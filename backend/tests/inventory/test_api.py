import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.inventory.models import Inventory, InventoryMovement


@pytest.fixture
def owner(store, db):
    user = User.objects.create(phone='9100000005', is_store_owner=True, is_staff=True)
    CustomerProfile.objects.create(user=user, tenant=store)
    return user


@pytest.fixture
def customer(store, db):
    user = User.objects.create(phone='9100000006')
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


@pytest.fixture
def inventory(store, variant):
    return Inventory.objects.create(
        tenant=store, variant=variant, available_qty=50, reserved_qty=0
    )


@pytest.mark.django_db
def test_list_inventory_owner(owner_client, inventory):
    res = owner_client.get('/api/v1/inventory/')
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]['available_qty'] == 50
    assert data[0]['sku'] == 'PVC-PIPE-2IN'


@pytest.mark.django_db
def test_list_inventory_customer_forbidden(customer_client, inventory):
    res = customer_client.get('/api/v1/inventory/')
    assert res.status_code == 403


@pytest.mark.django_db
def test_list_inventory_unauthenticated_forbidden(inventory):
    res = APIClient().get('/api/v1/inventory/')
    assert res.status_code == 403


@pytest.mark.django_db
def test_adjust_inventory_restock(owner_client, inventory, variant):
    res = owner_client.patch(
        f'/api/v1/inventory/{variant.id}/',
        {'delta': 20, 'reason': 'RESTOCK'},
        format='json',
    )
    assert res.status_code == 200
    assert res.json()['available_qty'] == 70
    assert InventoryMovement.objects.filter(inventory=inventory).count() == 1


@pytest.mark.django_db
def test_adjust_creates_inventory_if_missing(owner_client, store, variant):
    # No Inventory record yet — should be auto-created
    res = owner_client.patch(
        f'/api/v1/inventory/{variant.id}/',
        {'delta': 100, 'reason': 'RESTOCK'},
        format='json',
    )
    assert res.status_code == 200
    assert res.json()['available_qty'] == 100


@pytest.mark.django_db
def test_list_movements_owner(owner_client, inventory):
    inventory.adjust(delta=10, reason=InventoryMovement.RESTOCK)
    res = owner_client.get('/api/v1/inventory/movements/')
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]['delta'] == 10
