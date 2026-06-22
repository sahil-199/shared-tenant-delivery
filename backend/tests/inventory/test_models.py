import pytest
from decimal import Decimal
from apps.inventory.models import Inventory, InventoryMovement


@pytest.mark.django_db
def test_inventory_creation(store, variant):
    inv = Inventory.objects.create(
        tenant=store, variant=variant, available_qty=100, reserved_qty=0
    )
    assert inv.available_qty == 100


@pytest.mark.django_db
def test_inventory_adjust_restock(store, variant):
    inv = Inventory.objects.create(
        tenant=store, variant=variant, available_qty=50, reserved_qty=0
    )
    movement = inv.adjust(delta=20, reason=InventoryMovement.RESTOCK)
    inv.refresh_from_db()
    assert inv.available_qty == 70
    assert movement.delta == 20
    assert movement.reason == InventoryMovement.RESTOCK
    assert InventoryMovement.objects.filter(inventory=inv).count() == 1


@pytest.mark.django_db
def test_inventory_adjust_sell(store, variant):
    inv = Inventory.objects.create(
        tenant=store, variant=variant, available_qty=10, reserved_qty=0
    )
    inv.adjust(delta=-3, reason=InventoryMovement.SELL)
    inv.refresh_from_db()
    assert inv.available_qty == 7


@pytest.mark.django_db
def test_inventory_tenant_isolation(db):
    from apps.tenants.models import Store
    from apps.catalog.models import Category, Product, ProductVariant
    store_a = Store.objects.create(
        name='Inv Store A', slug='inv-store-a', phone='3333333333',
        address='A', delivery_pin_codes=[]
    )
    store_b = Store.objects.create(
        name='Inv Store B', slug='inv-store-b', phone='4444444444',
        address='B', delivery_pin_codes=[]
    )
    cat_a = Category.objects.create(tenant=store_a, name='Cat', slug='cat-inv-a')
    prod_a = Product.objects.create(
        tenant=store_a, category=cat_a, name='Prod A', slug='prod-inv-a'
    )
    var_a = ProductVariant.objects.create(
        product=prod_a, name='X', sku='SKU-INV-A', price=Decimal('10')
    )
    Inventory.objects.create(
        tenant=store_a, variant=var_a, available_qty=5, reserved_qty=0
    )
    assert Inventory.objects.filter(tenant=store_a).count() == 1
    assert Inventory.objects.filter(tenant=store_b).count() == 0
