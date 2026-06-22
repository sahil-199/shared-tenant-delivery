import pytest
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
def test_user_creation_with_phone():
    from apps.authentication.models import User
    user = User.objects.create_user(phone='9876543210')
    assert user.phone == '9876543210'
    assert user.is_active is True
    assert user.is_store_owner is False
    assert user.email is None


@pytest.mark.django_db
def test_user_phone_is_unique():
    from apps.authentication.models import User
    from django.db import IntegrityError
    User.objects.create_user(phone='9876543210')
    with pytest.raises(IntegrityError):
        User.objects.create_user(phone='9876543210')


@pytest.mark.django_db
def test_customer_profile_created(store):
    from apps.authentication.models import User, CustomerProfile
    user = User.objects.create_user(phone='9876543210')
    profile = CustomerProfile.objects.create(user=user, tenant=store)
    assert profile.user == user
    assert profile.tenant == store


@pytest.mark.django_db
def test_otp_verification_model():
    from apps.authentication.models import OTPVerification
    otp = OTPVerification.objects.create(
        phone='9876543210',
        otp_hash='hashed_value',
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    assert otp.is_used is False
    assert otp.attempt_count == 0
