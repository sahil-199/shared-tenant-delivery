import pytest
from django.contrib.postgres.fields import ArrayField


@pytest.fixture
def store(db):
    from apps.tenants.models import Store
    return Store.objects.create(
        name='Test Hardware Store',
        slug='test-hardware-store',
        phone='9876543210',
        address='123 Main St, Mumbai',
        delivery_pin_codes=['400001', '400002'],
    )


@pytest.fixture
def category(store):
    from apps.catalog.models import Category
    return Category.objects.create(tenant=store, name='Plumbing', slug='plumbing')


@pytest.fixture
def brand(store):
    from apps.catalog.models import Brand
    return Brand.objects.create(tenant=store, name='Supreme', slug='supreme')


@pytest.fixture
def product(store, category):
    from apps.catalog.models import Product
    return Product.objects.create(
        tenant=store,
        category=category,
        name='PVC Pipe 2 inch',
        slug='pvc-pipe-2-inch',
        description='Standard PVC pipe',
        specifications={'material': 'PVC', 'diameter': '2 inch'},
    )


@pytest.fixture
def variant(product):
    from apps.catalog.models import ProductVariant
    from decimal import Decimal
    return ProductVariant.objects.create(
        product=product,
        name='2 inch',
        sku='PVC-PIPE-2IN',
        price=Decimal('45.00'),
    )
