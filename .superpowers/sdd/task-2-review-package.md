# Review Package — Task 2: Product, ProductVariant, ProductImage Models

## Files Modified
- backend/apps/catalog/models.py (modified — appended Product, ProductVariant, ProductImage)
- backend/apps/catalog/admin.py (modified — added 3 new registrations)
- backend/apps/catalog/migrations/0002_*.py (new)
- backend/tests/catalog/test_models.py (modified — appended 6 new tests)
- backend/tests/conftest.py (modified — added category/brand/product/variant fixtures)


### backend/apps/catalog/models.py
```
from django.db import models
from django.utils.text import slugify
from apps.tenants.models import TenantModel


class Category(TenantModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    image = models.URLField(blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'
        unique_together = ('tenant', 'slug')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(TenantModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    logo = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'slug')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TenantModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products'
    )
    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name='products'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'slug')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    @property
    def effective_price(self):
        return self.sale_price if self.sale_price is not None else self.price

    def __str__(self):
        return f"{self.product.name} — {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(
        ProductVariant, null=True, blank=True, on_delete=models.SET_NULL, related_name='images'
    )
    image_url = models.URLField()
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']
```

### backend/apps/catalog/admin.py
```
from django.contrib import admin
from .models import Category, Brand, Product, ProductVariant, ProductImage

admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)
```

### backend/tests/catalog/test_models.py
```
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
```

### backend/tests/conftest.py
```
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
```

### backend/apps/catalog/migrations/0002_product_productvariant_productimage.py
```
# Generated by Django 5.1 on 2026-06-19 20:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('specifications', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='catalog.brand')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='catalog.category')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='tenants.store')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('tenant', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sale_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='catalog.product')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.URLField()),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='catalog.product')),
                ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='images', to='catalog.productvariant')),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
    ]
```
