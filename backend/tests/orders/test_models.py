import pytest
from decimal import Decimal
from apps.authentication.models import User, CustomerProfile
from apps.orders.models import Address, Order, OrderItem


@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='7000000001')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


@pytest.fixture
def address(store, user):
    return Address.objects.create(
        tenant=store, user=user,
        line1='123 Main St', city='Mumbai', state='Maharashtra',
        pin_code='400001', is_default=True
    )


@pytest.mark.django_db
def test_address_creation(address):
    assert address.id is not None
    assert address.pin_code == '400001'


@pytest.mark.django_db
def test_order_creation(store, user, address, product, variant):
    order = Order.objects.create(
        tenant=store, user=user, address=address,
        status=Order.PLACED, total_amount=Decimal('45.00')
    )
    OrderItem.objects.create(
        order=order, variant=variant, qty=1,
        unit_price=Decimal('45.00'), variant_name=variant.name
    )
    assert order.status == Order.PLACED
    assert order.items.count() == 1


@pytest.mark.django_db
def test_order_status_choices(store, user, address):
    order = Order.objects.create(
        tenant=store, user=user, address=address,
        status=Order.PLACED, total_amount=Decimal('0')
    )
    order.status = Order.CONFIRMED
    order.save()
    order.refresh_from_db()
    assert order.status == Order.CONFIRMED


@pytest.mark.django_db
def test_valid_transitions_defined():
    assert Order.CANCELLED in Order.VALID_TRANSITIONS[Order.PLACED]
    assert Order.DELIVERED not in Order.VALID_TRANSITIONS[Order.PLACED]
