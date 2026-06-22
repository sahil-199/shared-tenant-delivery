import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.catalog.models import Category, Brand, Product, ProductVariant


@pytest.fixture
def owner(store, db):
    user = User.objects.create(phone='9100000004', is_store_owner=True, is_staff=True)
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
def test_list_products_public(store, product, variant):
    res = APIClient().get('/api/v1/products/')
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]['slug'] == 'pvc-pipe-2-inch'
    assert len(data[0]['variants']) == 1
    assert data[0]['variants'][0]['sku'] == 'PVC-PIPE-2IN'


@pytest.mark.django_db
def test_get_product_by_slug(store, product, variant):
    res = APIClient().get('/api/v1/products/pvc-pipe-2-inch/')
    assert res.status_code == 200
    data = res.json()
    assert data['name'] == 'PVC Pipe 2 inch'
    assert data['category_name'] == 'Plumbing'


@pytest.mark.django_db
def test_get_product_not_found():
    res = APIClient().get('/api/v1/products/does-not-exist/')
    assert res.status_code == 404


@pytest.mark.django_db
def test_create_product_owner(owner_client, store, category):
    payload = {
        'name': 'Ball Valve',
        'slug': 'ball-valve',
        'category': category.id,
        'description': 'Brass ball valve for plumbing',
        'specifications': {'material': 'brass', 'size': '1/2 inch'},
        'variants': [
            {'name': '1/2 inch', 'sku': 'VALVE-HALF', 'price': '120.00'},
            {'name': '1 inch', 'sku': 'VALVE-ONE', 'price': '180.00'},
        ],
    }
    res = owner_client.post('/api/v1/products/', payload, format='json')
    assert res.status_code == 201
    assert Product.objects.filter(tenant=store, slug='ball-valve').exists()
    assert ProductVariant.objects.filter(sku='VALVE-HALF').exists()
    assert ProductVariant.objects.filter(sku='VALVE-ONE').exists()


@pytest.mark.django_db
def test_create_product_unauthenticated_forbidden(store, category):
    payload = {'name': 'X', 'slug': 'x', 'category': category.id}
    res = APIClient().post('/api/v1/products/', payload, format='json')
    assert res.status_code == 403


@pytest.mark.django_db
def test_filter_by_category(store, product, variant, category):
    res = APIClient().get(f'/api/v1/products/?category={category.slug}')
    assert res.status_code == 200
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_filter_by_nonexistent_category(store, product):
    res = APIClient().get('/api/v1/products/?category=nonexistent')
    assert res.status_code == 200
    assert len(res.json()) == 0


@pytest.mark.django_db
def test_list_variants_for_product(store, product, variant):
    res = APIClient().get(f'/api/v1/products/{product.slug}/variants/')
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]['sku'] == 'PVC-PIPE-2IN'
