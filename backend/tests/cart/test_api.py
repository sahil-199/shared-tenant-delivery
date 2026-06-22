import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.cart.models import Cart, CartItem


@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='8000000002')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


def _jwt(user, store):
    from apps.authentication.tokens import TenantRefreshToken
    return str(TenantRefreshToken.for_user_and_store(user, store).access_token)


@pytest.fixture
def auth_client(user, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(user, store)}')
    return c


@pytest.mark.django_db
def test_get_cart_creates_if_missing(auth_client, store, user):
    res = auth_client.get('/api/v1/cart/')
    assert res.status_code == 200
    assert Cart.objects.filter(user=user, tenant=store).exists()


@pytest.mark.django_db
def test_add_item_to_cart(auth_client, variant):
    res = auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 2}, format='json')
    assert res.status_code == 201
    assert CartItem.objects.filter(variant=variant).exists()


@pytest.mark.django_db
def test_add_same_variant_increases_qty(auth_client, variant):
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 2}, format='json')
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 3}, format='json')
    item = CartItem.objects.get(variant=variant)
    assert item.qty == 5


@pytest.mark.django_db
def test_update_cart_item_qty(auth_client, variant):
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 2}, format='json')
    item = CartItem.objects.get(variant=variant)
    res = auth_client.patch(f'/api/v1/cart/items/{item.id}/', {'qty': 10}, format='json')
    assert res.status_code == 200
    item.refresh_from_db()
    assert item.qty == 10


@pytest.mark.django_db
def test_delete_cart_item(auth_client, variant):
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 1}, format='json')
    item = CartItem.objects.get(variant=variant)
    res = auth_client.delete(f'/api/v1/cart/items/{item.id}/delete/')
    assert res.status_code == 204


@pytest.mark.django_db
def test_cart_requires_auth(variant):
    res = APIClient().get('/api/v1/cart/')
    assert res.status_code == 401
