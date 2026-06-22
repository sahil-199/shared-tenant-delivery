import pytest
from decimal import Decimal
from apps.authentication.models import User, CustomerProfile
from apps.cart.models import Cart, CartItem


@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='8000000001')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


@pytest.mark.django_db
def test_cart_creation(store, user):
    cart = Cart.objects.create(tenant=store, user=user)
    assert cart.id is not None


@pytest.mark.django_db
def test_cart_item_subtotal(store, user, variant):
    cart = Cart.objects.create(tenant=store, user=user)
    item = CartItem.objects.create(cart=cart, variant=variant, qty=3)
    assert item.subtotal == Decimal('45.00') * 3


@pytest.mark.django_db
def test_cart_item_unique_per_variant(store, user, variant):
    cart = Cart.objects.create(tenant=store, user=user)
    CartItem.objects.create(cart=cart, variant=variant, qty=1)
    from django.db import IntegrityError
    with pytest.raises(IntegrityError):
        CartItem.objects.create(cart=cart, variant=variant, qty=2)
