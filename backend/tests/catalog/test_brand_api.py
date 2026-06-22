import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.catalog.models import Brand


@pytest.fixture
def owner(store, db):
    user = User.objects.create(phone='9100000003', is_store_owner=True, is_staff=True)
    CustomerProfile.objects.create(user=user, tenant=store)
    return user


def _jwt(user, store):
    from apps.authentication.tokens import TenantRefreshToken
    return str(TenantRefreshToken.for_user_and_store(user, store).access_token)


@pytest.fixture
def owner_client(owner, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(owner, store)}')
    return c


@pytest.mark.django_db
def test_list_brands_public(store, brand):
    res = APIClient().get('/api/v1/brands/')
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]['name'] == 'Supreme'


@pytest.mark.django_db
def test_create_brand_owner(owner_client, store):
    res = owner_client.post(
        '/api/v1/brands/', {'name': 'Jaguar', 'slug': 'jaguar'}, format='json'
    )
    assert res.status_code == 201
    assert Brand.objects.filter(tenant=store, slug='jaguar').exists()


@pytest.mark.django_db
def test_create_brand_unauthenticated_forbidden():
    res = APIClient().post('/api/v1/brands/', {'name': 'X', 'slug': 'x'}, format='json')
    assert res.status_code == 403
