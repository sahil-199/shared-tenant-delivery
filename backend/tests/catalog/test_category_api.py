import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.catalog.models import Category


@pytest.fixture
def owner(store, db):
    user = User.objects.create(phone='9100000001', is_store_owner=True, is_staff=True)
    CustomerProfile.objects.create(user=user, tenant=store)
    return user


@pytest.fixture
def customer(store, db):
    user = User.objects.create(phone='9100000002')
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


@pytest.fixture
def customer_client(customer, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(customer, store)}')
    return c


@pytest.mark.django_db
def test_list_categories_public(store, category):
    res = APIClient().get('/api/v1/categories/')
    assert res.status_code == 200
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_create_category_owner(owner_client, store):
    res = owner_client.post(
        '/api/v1/categories/', {'name': 'Electrical', 'slug': 'electrical'}, format='json'
    )
    assert res.status_code == 201
    assert Category.objects.filter(tenant=store, slug='electrical').exists()


@pytest.mark.django_db
def test_create_category_customer_forbidden(customer_client):
    res = customer_client.post(
        '/api/v1/categories/', {'name': 'X', 'slug': 'x'}, format='json'
    )
    assert res.status_code == 403


@pytest.mark.django_db
def test_create_category_unauthenticated_forbidden():
    res = APIClient().post(
        '/api/v1/categories/', {'name': 'X', 'slug': 'x'}, format='json'
    )
    assert res.status_code == 403


@pytest.mark.django_db
def test_category_tree_format(owner_client, store):
    parent = Category.objects.create(tenant=store, name='Plumbing', slug='plumbing-tree')
    Category.objects.create(
        tenant=store, name='PVC Pipes', slug='pvc-pipes-tree', parent=parent
    )
    res = owner_client.get('/api/v1/categories/?view=tree')
    data = res.json()
    root_slugs = [d['slug'] for d in data]
    assert 'plumbing-tree' in root_slugs
    assert 'pvc-pipes-tree' not in root_slugs
    plumbing = next(d for d in data if d['slug'] == 'plumbing-tree')
    assert len(plumbing['children']) == 1
    assert plumbing['children'][0]['slug'] == 'pvc-pipes-tree'
