import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.orders.models import Order, Address


@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='7000000002')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


@pytest.fixture
def owner(store, db):
    u = User.objects.create(phone='7000000003', is_store_owner=True, is_staff=True)
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


def _jwt(user, store):
    from apps.authentication.tokens import TenantRefreshToken
    return str(TenantRefreshToken.for_user_and_store(user, store).access_token)


@pytest.fixture
def user_client(user, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(user, store)}')
    return c


@pytest.fixture
def owner_client(owner, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(owner, store)}')
    return c


@pytest.mark.django_db
def test_create_address(user_client):
    res = user_client.post('/api/v1/addresses/', {
        'line1': '10 Park St', 'city': 'Mumbai', 'state': 'MH', 'pin_code': '400001'
    }, format='json')
    assert res.status_code == 201


@pytest.mark.django_db
def test_checkout_invalid_pin(user_client, store, variant):
    from apps.authentication.models import User
    store.delivery_pin_codes = ['999999']
    store.save()
    u = User.objects.get(phone='7000000002')
    addr = Address.objects.create(
        tenant=store, user=u,
        line1='X', city='Y', state='Z', pin_code='400001'
    )
    # Need a cart with items
    from apps.cart.models import Cart, CartItem
    cart = Cart.objects.create(tenant=store, user=u)
    CartItem.objects.create(cart=cart, variant=variant, qty=1)
    res = user_client.post('/api/v1/orders/', {
        'address': addr.id,
    }, format='json')
    assert res.status_code == 400
    assert 'pin' in str(res.json()).lower() or 'delivery' in str(res.json()).lower()


@pytest.mark.django_db
def test_checkout_success(user_client, store, variant):
    from apps.inventory.models import Inventory
    from apps.authentication.models import User
    from apps.cart.models import Cart, CartItem
    store.delivery_pin_codes = ['400001']
    store.save()
    Inventory.objects.create(tenant=store, variant=variant, available_qty=10, reserved_qty=0)
    u = User.objects.get(phone='7000000002')
    addr = Address.objects.create(
        tenant=store, user=u,
        line1='10 Park', city='Mumbai', state='MH', pin_code='400001'
    )
    cart = Cart.objects.create(tenant=store, user=u)
    CartItem.objects.create(cart=cart, variant=variant, qty=2)
    res = user_client.post('/api/v1/orders/', {'address': addr.id}, format='json')
    assert res.status_code == 201
    assert Order.objects.filter(user=u).exists()


@pytest.mark.django_db
def test_list_orders(user_client):
    res = user_client.get('/api/v1/orders/list/')
    assert res.status_code == 200


@pytest.mark.django_db
def test_owner_update_order_status(owner_client, user, store, variant):
    from apps.authentication.models import User
    u = User.objects.get(phone='7000000002')
    addr = Address.objects.create(
        tenant=store, user=u,
        line1='X', city='Y', state='Z', pin_code='400001'
    )
    order = Order.objects.create(
        tenant=store, user=u, address=addr,
        status=Order.PLACED, total_amount=Decimal('45')
    )
    res = owner_client.patch(
        f'/api/v1/orders/{order.id}/status/',
        {'status': Order.PENDING_CONFIRMATION},
        format='json'
    )
    assert res.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.PENDING_CONFIRMATION


@pytest.mark.django_db
def test_invalid_status_transition(owner_client, user, store, variant):
    from apps.authentication.models import User
    u = User.objects.get(phone='7000000002')
    addr = Address.objects.create(
        tenant=store, user=u,
        line1='X', city='Y', state='Z', pin_code='400001'
    )
    order = Order.objects.create(
        tenant=store, user=u, address=addr,
        status=Order.PLACED, total_amount=Decimal('0')
    )
    res = owner_client.patch(
        f'/api/v1/orders/{order.id}/status/',
        {'status': Order.DELIVERED},
        format='json'
    )
    assert res.status_code == 400
