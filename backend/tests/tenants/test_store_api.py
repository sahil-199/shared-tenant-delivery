import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def store_with_owner(db):
    from apps.tenants.models import Store
    from apps.authentication.models import User, CustomerProfile
    from apps.authentication.tokens import TenantRefreshToken

    store = Store.objects.create(
        name='Test Store', slug='test-store',
        phone='9999999999', address='Test Address',
        delivery_pin_codes=['400001'],
    )
    owner = User.objects.create_user(phone='9000000000', is_store_owner=True)
    CustomerProfile.objects.create(user=owner, tenant=store)
    refresh = TenantRefreshToken.for_user_and_store(owner, store)
    return store, owner, str(refresh.access_token)


@pytest.mark.django_db
def test_get_store_public(api_client, store_with_owner):
    store, _, _ = store_with_owner
    response = api_client.get('/api/v1/store/')
    assert response.status_code == 200
    assert response.data['name'] == 'Test Store'
    assert 'delivery_pin_codes' in response.data


@pytest.mark.django_db
def test_patch_store_requires_owner(api_client, store_with_owner):
    _, _, token = store_with_owner
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = api_client.patch('/api/v1/store/', {'name': 'Updated Store'}, format='json')
    assert response.status_code == 200
    assert response.data['name'] == 'Updated Store'


@pytest.mark.django_db
def test_patch_store_rejects_non_owner(api_client, store_with_owner):
    store, _, _ = store_with_owner
    from apps.authentication.models import User, CustomerProfile
    from apps.authentication.tokens import TenantRefreshToken

    customer = User.objects.create_user(phone='8000000000')
    CustomerProfile.objects.create(user=customer, tenant=store)
    refresh = TenantRefreshToken.for_user_and_store(customer, store)
    token = str(refresh.access_token)

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = api_client.patch('/api/v1/store/', {'name': 'Hacked'}, format='json')
    assert response.status_code == 403
