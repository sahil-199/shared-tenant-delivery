import pytest
from decimal import Decimal
from apps.catalog.models import Category, Brand, Product, ProductVariant, ProductImage


@pytest.mark.django_db
def test_category_creation(store):
    cat = Category.objects.create(
        tenant=store, name='Pipes & Fittings', slug='pipes-fittings'
    )
    assert cat.id is not None
    assert cat.parent is None
    assert cat.is_active is True


@pytest.mark.django_db
def test_category_auto_slug(store):
    cat = Category.objects.create(tenant=store, name='Electrical Wires')
    assert cat.slug == 'electrical-wires'


@pytest.mark.django_db
def test_category_nesting(store):
    parent = Category.objects.create(tenant=store, name='Plumbing', slug='plumbing')
    child = Category.objects.create(
        tenant=store, name='PVC Pipes', slug='pvc-pipes', parent=parent
    )
    assert child.parent_id == parent.id
    assert list(parent.children.values_list('slug', flat=True)) == ['pvc-pipes']


@pytest.mark.django_db
def test_brand_creation(store):
    brand = Brand.objects.create(tenant=store, name='Supreme', slug='supreme')
    assert brand.is_active is True


@pytest.mark.django_db
def test_category_tenant_isolation(db):
    from apps.tenants.models import Store
    store_a = Store.objects.create(
        name='Store A', slug='store-a', phone='1111111111', address='A', delivery_pin_codes=[]
    )
    store_b = Store.objects.create(
        name='Store B', slug='store-b', phone='2222222222', address='B', delivery_pin_codes=[]
    )
    Category.objects.create(tenant=store_a, name='Cat A', slug='cat-a')
    Category.objects.create(tenant=store_b, name='Cat B', slug='cat-b')
    assert Category.objects.filter(tenant=store_a).count() == 1
    assert Category.objects.filter(tenant=store_b).count() == 1


@pytest.mark.django_db
def test_product_creation(store):
    cat = Category.objects.create(tenant=store, name='Pipes', slug='pipes')
    brand = Brand.objects.create(tenant=store, name='Supreme', slug='supreme')
    product = Product.objects.create(
        tenant=store, category=cat, brand=brand,
        name='PVC Pipe 2 inch', slug='pvc-pipe-2-inch',
        description='Standard PVC pipe',
        specifications={'material': 'PVC', 'diameter': '2 inch'},
    )
    assert product.is_active is True
    assert product.specifications['material'] == 'PVC'


@pytest.mark.django_db
def test_product_auto_slug(store):
    cat = Category.objects.create(tenant=store, name='Pipes', slug='pipes-auto')
    product = Product.objects.create(tenant=store, category=cat, name='Ball Valve')
    assert product.slug == 'ball-valve'


@pytest.mark.django_db
def test_variant_effective_price_with_sale(store):
    cat = Category.objects.create(tenant=store, name='Pipes', slug='pipes-eff')
    product = Product.objects.create(tenant=store, category=cat, name='Pipe', slug='pipe-eff')
    variant = ProductVariant.objects.create(
        product=product, name='1 inch', sku='PIPE-1IN-EFF',
        price=Decimal('100.00'), sale_price=Decimal('80.00')
    )
    assert variant.effective_price == Decimal('80.00')


@pytest.mark.django_db
def test_variant_effective_price_without_sale(store):
    cat = Category.objects.create(tenant=store, name='Pipes', slug='pipes-no-sale')
    product = Product.objects.create(tenant=store, category=cat, name='Pipe2', slug='pipe-no-sale')
    variant = ProductVariant.objects.create(
        product=product, name='1 inch', sku='PIPE-1IN-NS', price=Decimal('100.00')
    )
    assert variant.effective_price == Decimal('100.00')


@pytest.mark.django_db
def test_variant_sku_uniqueness(store):
    cat = Category.objects.create(tenant=store, name='Pipes', slug='pipes-sku')
    p1 = Product.objects.create(tenant=store, category=cat, name='P1', slug='p1-sku')
    ProductVariant.objects.create(product=p1, name='A', sku='DUPE-SKU', price=Decimal('10.00'))
    p2 = Product.objects.create(tenant=store, category=cat, name='P2', slug='p2-sku')
    from django.db import IntegrityError
    with pytest.raises(IntegrityError):
        ProductVariant.objects.create(product=p2, name='A', sku='DUPE-SKU', price=Decimal('10.00'))


@pytest.mark.django_db
def test_product_image_variant_nullable(store):
    cat = Category.objects.create(tenant=store, name='Pipes', slug='pipes-img')
    product = Product.objects.create(tenant=store, category=cat, name='Pipe3', slug='pipe-img')
    img = ProductImage.objects.create(
        product=product, image_url='https://r2.example.com/pipe.jpg', sort_order=0
    )
    assert img.variant is None
