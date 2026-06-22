import pytest
from django.urls import reverse


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def active_store(db):
    from apps.tenants.models import Store
    return Store.objects.create(
        name='Test Store', slug='test-store',
        phone='9999999999', address='Test Address',
        delivery_pin_codes=['400001'],
        is_active=True,
    )


@pytest.mark.django_db
def test_otp_request_success(api_client, active_store):
    response = api_client.post('/api/v1/auth/otp/request/', {'phone': '9876543210'})
    assert response.status_code == 200
    assert 'message' in response.data


@pytest.mark.django_db
def test_otp_request_invalid_phone(api_client, active_store):
    response = api_client.post('/api/v1/auth/otp/request/', {'phone': '123'})
    assert response.status_code == 400


@pytest.mark.django_db
def test_otp_verify_creates_new_user(api_client, active_store):
    from apps.authentication.models import OTPVerification
    from apps.authentication.services import hash_otp
    from django.utils import timezone
    from datetime import timedelta

    OTPVerification.objects.create(
        phone='9876543210',
        otp_hash=hash_otp('123456'),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    response = api_client.post('/api/v1/auth/otp/verify/', {
        'phone': '9876543210', 'otp': '123456'
    })
    assert response.status_code == 200
    assert 'access_token' in response.data
    assert 'refresh_token' in response.data
    assert response.data['is_new_user'] is True


@pytest.mark.django_db
def test_otp_verify_wrong_otp(api_client, active_store):
    from apps.authentication.models import OTPVerification
    from apps.authentication.services import hash_otp
    from django.utils import timezone
    from datetime import timedelta

    OTPVerification.objects.create(
        phone='9876543210',
        otp_hash=hash_otp('123456'),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    response = api_client.post('/api/v1/auth/otp/verify/', {
        'phone': '9876543210', 'otp': '999999'
    })
    assert response.status_code == 400


@pytest.mark.django_db
def test_otp_verify_expired_otp(api_client, active_store):
    from apps.authentication.models import OTPVerification
    from apps.authentication.services import hash_otp
    from django.utils import timezone
    from datetime import timedelta

    OTPVerification.objects.create(
        phone='9876543210',
        otp_hash=hash_otp('123456'),
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    response = api_client.post('/api/v1/auth/otp/verify/', {
        'phone': '9876543210', 'otp': '123456'
    })
    assert response.status_code == 400


@pytest.mark.django_db
def test_otp_verify_lockout_after_5_failures(api_client, active_store):
    from apps.authentication.models import OTPVerification
    from apps.authentication.services import hash_otp
    from django.utils import timezone
    from datetime import timedelta

    for _ in range(5):
        OTPVerification.objects.create(
            phone='9876543210',
            otp_hash=hash_otp('123456'),
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        api_client.post('/api/v1/auth/otp/verify/', {
            'phone': '9876543210', 'otp': '999999'
        })

    # 6th attempt should be locked out
    OTPVerification.objects.create(
        phone='9876543210',
        otp_hash=hash_otp('123456'),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    response = api_client.post('/api/v1/auth/otp/verify/', {
        'phone': '9876543210', 'otp': '999999'
    })
    assert response.status_code == 429
