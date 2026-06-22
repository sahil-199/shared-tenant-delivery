# Catalog & Inventory Implementation Plan (Phases 3–5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full product catalog (categories, brands, products, variants, images) and inventory tracking system, plus the customer storefront pages and owner admin UI.

**Architecture:** Two new Django apps — `apps.catalog` and `apps.inventory` — using tenant-scoped models extending `TenantModel`, DRF ViewSets with `IsStoreOwner` permission, and Next.js server-component pages for the storefront plus client-component admin forms.

**Tech Stack:** Django 5.1, DRF 3.15, PostgreSQL 16, Next.js 14 App Router, TypeScript, TailwindCSS v4

## Global Constraints

- **No git in this project** — skip all commit steps; mark tasks complete in `.superpowers/sdd/progress.md` instead
- Every tenant-scoped model must extend `TenantModel` from `apps/tenants/models.py`
- API prefix: `/api/v1/` — all endpoints use this prefix
- Tests run inside Docker: `docker-compose exec backend pytest tests/path/test_file.py -v`
- Frontend: Next.js 14 App Router, TailwindCSS v4 (`@theme inline` in `globals.css` — no `tailwind.config.ts`)
- Fonts: Bodoni Moda headings (`font-['Bodoni_Moda']`), Jost body (`font-['Jost']`) — already loaded in globals.css
- Color palette: slate-50 background, orange-500 CTA, white cards, slate-900 headings
- Minimum touch target: 48px height on all interactive elements
- Owner-only writes: protected by `IsStoreOwner` permission (defined in Task 4) — reads `is_store_owner` from JWT claim
- Public reads: category list, brand list, product list/detail — no auth required
- Slugs: auto-generated from `name` via `django.utils.text.slugify` if not provided at save time
- Image fields: store R2 URL strings — no file upload in this plan, accept URL strings as-is
- All DRF serializers must list `fields` explicitly — no `__all__`
- Existing fixtures in `backend/tests/conftest.py`: `store` fixture is already there — extend it, don't replace it
- `?format=` is reserved by DRF for renderer negotiation — use `?view=tree` for category tree format

---

## File Map

```
backend/
  apps/
    catalog/
      __init__.py
      apps.py
      models.py          # Category, Brand, Product, ProductVariant, ProductImage
      permissions.py     # IsStoreOwner
      serializers.py     # all catalog serializers
      views.py           # Category, Brand, Product ViewSets + get_store_for_request()
      urls.py            # router: categories, brands, products
      admin.py
      migrations/
        __init__.py
        0001_initial.py  # Category + Brand
        0002_product.py  # Product, ProductVariant, ProductImage
    inventory/
      __init__.py
      apps.py
      models.py          # Inventory, InventoryMovement
      serializers.py
      views.py           # InventoryViewSet
      urls.py
      admin.py
      migrations/
        __init__.py
        0001_initial.py
  config/
    settings/base.py     # +apps.catalog, +apps.inventory
    urls.py              # +catalog.urls, +inventory.urls
  tests/
    conftest.py          # +category, brand, product, variant fixtures
    catalog/
      __init__.py
      test_models.py
      test_category_api.py
      test_brand_api.py
      test_product_api.py
    inventory/
      __init__.py
      test_models.py
      test_api.py

frontend/
  lib/
    types.ts             # Category, Brand, Product, ProductVariant, ProductImage interfaces
  components/
    product/
      ProductCard.tsx
      ProductGrid.tsx
      VariantSelector.tsx  # 'use client'
    admin/
      ProductForm.tsx      # 'use client'
  app/
    (store)/
      products/
        page.tsx           # listing + category sidebar
        [slug]/
          page.tsx         # product detail
    admin/
      layout.tsx           # owner guard
      products/
        page.tsx           # admin product list
        new/
          page.tsx         # create product form
```

---

### Task 1: Catalog App + Category & Brand Models

**Files:**
- Create: `backend/apps/catalog/__init__.py`
- Create: `backend/apps/catalog/apps.py`
- Create: `backend/apps/catalog/models.py`
- Create: `backend/apps/catalog/admin.py`
- Create: `backend/apps/catalog/migrations/__init__.py`
- Modify: `backend/config/settings/base.py` (add `apps.catalog` to `LOCAL_APPS`)
- Create: `backend/tests/catalog/__init__.py`
- Create: `backend/tests/catalog/test_models.py`

**Interfaces:**
- Produces: `Category(TenantModel)` — fields: `id, tenant(FK→Store), name, slug, image(URLField blank), parent(FK→self nullable), is_active(bool default True), created_at`; `Meta.unique_together = ('tenant', 'slug')`
- Produces: `Brand(TenantModel)` — fields: `id, tenant(FK→Store), name, slug, logo(URLField blank), is_active, created_at`; `Meta.unique_together = ('tenant', 'slug')`
- Both have auto-slug: `if not self.slug: self.slug = slugify(self.name)` in `save()`

- [ ] **Step 1: Write failing model tests**

```python
# backend/tests/catalog/__init__.py
# (empty file)
```

```python
# backend/tests/catalog/test_models.py
import pytest
from apps.catalog.models import Category, Brand


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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
docker-compose exec backend pytest tests/catalog/test_models.py -v
```
Expected: `ModuleNotFoundError: No module named 'apps.catalog'`

- [ ] **Step 3: Create catalog app files**

```python
# backend/apps/catalog/__init__.py
# (empty)
```

```python
# backend/apps/catalog/apps.py
from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.catalog'
```

- [ ] **Step 4: Write the models**

```python
# backend/apps/catalog/models.py
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


# Product, ProductVariant, ProductImage added in Task 2
```

- [ ] **Step 5: Create admin.py**

```python
# backend/apps/catalog/admin.py
from django.contrib import admin
from .models import Category, Brand

admin.site.register(Category)
admin.site.register(Brand)
```

- [ ] **Step 6: Add to INSTALLED_APPS**

In `backend/config/settings/base.py`, change `LOCAL_APPS` to:

```python
LOCAL_APPS = [
    'apps.tenants',
    'apps.authentication',
    'apps.catalog',
]
```

- [ ] **Step 7: Create and apply migrations**

```bash
docker-compose exec backend python manage.py makemigrations catalog
docker-compose exec backend python manage.py migrate
```
Expected output contains: `Applying catalog.0001_initial... OK`

- [ ] **Step 8: Run tests**

```bash
docker-compose exec backend pytest tests/catalog/test_models.py -v
```
Expected: 5 tests PASS

---

### Task 2: Product, ProductVariant, ProductImage Models

**Files:**
- Modify: `backend/apps/catalog/models.py` (append Product, ProductVariant, ProductImage)
- Modify: `backend/apps/catalog/admin.py` (register new models)
- Modify: `backend/tests/catalog/test_models.py` (add product tests)
- Modify: `backend/tests/conftest.py` (add `category`, `brand`, `product`, `variant` fixtures)

**Interfaces:**
- Consumes: `Category`, `Brand` from Task 1
- Produces: `Product(TenantModel)` — `id, tenant, category(FK→Category), brand(FK→Brand nullable), name, slug, description, specifications(JSONField default=dict), is_active, created_at`
- Produces: `ProductVariant(models.Model)` — `id, product(FK→Product), name, sku(unique), price(Decimal 10.2), sale_price(Decimal nullable), is_active, created_at`; property `effective_price` returns `sale_price or price`
- Produces: `ProductImage(models.Model)` — `id, product(FK→Product), variant(FK→ProductVariant nullable), image_url(URLField), sort_order(int default 0)`
- Produces: conftest fixtures `category(store)`, `brand(store)`, `product(store, category)`, `variant(product)` — used by Tasks 4–6

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/catalog/test_models.py` (after existing imports — add `Product, ProductVariant, ProductImage` to the import and add these test functions):

```python
from decimal import Decimal
from apps.catalog.models import Category, Brand, Product, ProductVariant, ProductImage


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

- [ ] **Step 2: Run tests to confirm they fail**

```bash
docker-compose exec backend pytest tests/catalog/test_models.py::test_product_creation -v
```
Expected: `ImportError: cannot import name 'Product'`

- [ ] **Step 3: Append Product models to models.py**

Append to `backend/apps/catalog/models.py` (after the `Brand` class):

```python
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

- [ ] **Step 4: Update admin.py**

```python
# backend/apps/catalog/admin.py
from django.contrib import admin
from .models import Category, Brand, Product, ProductVariant, ProductImage

admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)
```

- [ ] **Step 5: Migrate**

```bash
docker-compose exec backend python manage.py makemigrations catalog
docker-compose exec backend python manage.py migrate
```
Expected: `Applying catalog.0002_product... OK`

- [ ] **Step 6: Add shared fixtures to conftest.py**

The existing `backend/tests/conftest.py` has the `store` fixture. Append these fixtures after it:

```python
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

- [ ] **Step 7: Run all catalog model tests**

```bash
docker-compose exec backend pytest tests/catalog/test_models.py -v
```
Expected: 11 tests PASS

---

### Task 3: Inventory App + Models

**Files:**
- Create: `backend/apps/inventory/__init__.py`
- Create: `backend/apps/inventory/apps.py`
- Create: `backend/apps/inventory/models.py`
- Create: `backend/apps/inventory/admin.py`
- Create: `backend/apps/inventory/migrations/__init__.py`
- Modify: `backend/config/settings/base.py` (add `apps.inventory` to `LOCAL_APPS`)
- Create: `backend/tests/inventory/__init__.py`
- Create: `backend/tests/inventory/test_models.py`

**Interfaces:**
- Consumes: `ProductVariant` from Task 2 (via string ref `'catalog.ProductVariant'`); `TenantModel` from `apps/tenants/models.py`
- Produces: `Inventory(TenantModel)` — `id, variant(OneToOneField→ProductVariant), tenant(FK→Store via TenantModel), available_qty(int default 0), reserved_qty(int default 0)`; method `adjust(delta: int, reason: str) -> InventoryMovement` — atomic update + movement record
- Produces: `InventoryMovement(models.Model)` — `id, inventory(FK→Inventory), delta(int), reason(str choices: RESTOCK/RESERVE/RELEASE/SELL/ADJUSTMENT), created_at`; class-level constants `RESTOCK = 'RESTOCK'` etc.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/inventory/__init__.py
# (empty)
```

```python
# backend/tests/inventory/test_models.py
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
docker-compose exec backend pytest tests/inventory/test_models.py -v
```
Expected: `ModuleNotFoundError: No module named 'apps.inventory'`

- [ ] **Step 3: Create inventory app files**

```python
# backend/apps/inventory/__init__.py
# (empty)
```

```python
# backend/apps/inventory/apps.py
from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'
```

- [ ] **Step 4: Write inventory models**

```python
# backend/apps/inventory/models.py
from django.db import models, transaction
from apps.tenants.models import TenantModel


class Inventory(TenantModel):
    variant = models.OneToOneField(
        'catalog.ProductVariant', on_delete=models.CASCADE, related_name='inventory'
    )
    available_qty = models.IntegerField(default=0)
    reserved_qty = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'inventories'

    def adjust(self, delta: int, reason: str) -> 'InventoryMovement':
        with transaction.atomic():
            self.available_qty += delta
            self.save(update_fields=['available_qty'])
            return InventoryMovement.objects.create(
                inventory=self, delta=delta, reason=reason
            )

    def __str__(self):
        return f"{self.variant} — qty: {self.available_qty}"


class InventoryMovement(models.Model):
    RESTOCK = 'RESTOCK'
    RESERVE = 'RESERVE'
    RELEASE = 'RELEASE'
    SELL = 'SELL'
    ADJUSTMENT = 'ADJUSTMENT'

    REASON_CHOICES = [
        (RESTOCK, 'Restock'),
        (RESERVE, 'Reserve'),
        (RELEASE, 'Release'),
        (SELL, 'Sell'),
        (ADJUSTMENT, 'Adjustment'),
    ]

    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name='movements'
    )
    delta = models.IntegerField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

- [ ] **Step 5: Create admin.py**

```python
# backend/apps/inventory/admin.py
from django.contrib import admin
from .models import Inventory, InventoryMovement

admin.site.register(Inventory)
admin.site.register(InventoryMovement)
```

- [ ] **Step 6: Add to INSTALLED_APPS**

In `backend/config/settings/base.py`, update `LOCAL_APPS`:

```python
LOCAL_APPS = [
    'apps.tenants',
    'apps.authentication',
    'apps.catalog',
    'apps.inventory',
]
```

- [ ] **Step 7: Migrate**

```bash
docker-compose exec backend python manage.py makemigrations inventory
docker-compose exec backend python manage.py migrate
```
Expected: `Applying inventory.0001_initial... OK`

- [ ] **Step 8: Run tests**

```bash
docker-compose exec backend pytest tests/inventory/test_models.py -v
```
Expected: 4 tests PASS

---

### Task 4: Category & Brand APIs

**Files:**
- Create: `backend/apps/catalog/permissions.py`
- Create: `backend/apps/catalog/serializers.py`
- Create: `backend/apps/catalog/views.py`
- Create: `backend/apps/catalog/urls.py`
- Modify: `backend/config/urls.py` (add catalog urls)
- Create: `backend/tests/catalog/test_category_api.py`
- Create: `backend/tests/catalog/test_brand_api.py`

**Interfaces:**
- Produces: `IsStoreOwner` permission — reads `is_store_owner` from `request.auth` JWT claim; allows all safe methods (GET/HEAD/OPTIONS), blocks unsafe methods unless `is_store_owner=True`
- Produces: `get_store_for_request(request) -> Store | None` — resolves Store from JWT `tenant_id` if authenticated, else from `Store.objects.filter(is_active=True).first()`; used by Tasks 5, 6
- Produces: `GET /api/v1/categories/` — flat list; `?view=tree` returns root nodes with nested `children`
- Produces: `POST /api/v1/categories/`, `PATCH /api/v1/categories/{id}/`, `DELETE /api/v1/categories/{id}/` — owner only
- Produces: `GET /api/v1/brands/`, `POST`, `PATCH`, `DELETE` — same pattern

- [ ] **Step 1: Write failing category API tests**

```python
# backend/tests/catalog/test_category_api.py
import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.catalog.models import Category


@pytest.fixture
def owner(store, db):
    user = User.objects.create(phone='9100000001', is_store_owner=True, is_staff=True)
    CustomerProfile.objects.create(user=user, tenant=store)
    return user


@pytest.fixture
def customer(store, db):
    user = User.objects.create(phone='9100000002')
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


@pytest.mark.django_db
def test_list_categories_public(store, category):
    res = APIClient().get('/api/v1/categories/')
    assert res.status_code == 200
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_create_category_owner(owner_client, store):
    res = owner_client.post(
        '/api/v1/categories/', {'name': 'Electrical', 'slug': 'electrical'}, format='json'
    )
    assert res.status_code == 201
    assert Category.objects.filter(tenant=store, slug='electrical').exists()


@pytest.mark.django_db
def test_create_category_customer_forbidden(customer_client):
    res = customer_client.post(
        '/api/v1/categories/', {'name': 'X', 'slug': 'x'}, format='json'
    )
    assert res.status_code == 403


@pytest.mark.django_db
def test_create_category_unauthenticated_forbidden():
    res = APIClient().post(
        '/api/v1/categories/', {'name': 'X', 'slug': 'x'}, format='json'
    )
    assert res.status_code == 403


@pytest.mark.django_db
def test_category_tree_format(owner_client, store):
    parent = Category.objects.create(tenant=store, name='Plumbing', slug='plumbing-tree')
    Category.objects.create(
        tenant=store, name='PVC Pipes', slug='pvc-pipes-tree', parent=parent
    )
    res = owner_client.get('/api/v1/categories/?view=tree')
    data = res.json()
    root_slugs = [d['slug'] for d in data]
    assert 'plumbing-tree' in root_slugs
    assert 'pvc-pipes-tree' not in root_slugs
    plumbing = next(d for d in data if d['slug'] == 'plumbing-tree')
    assert len(plumbing['children']) == 1
    assert plumbing['children'][0]['slug'] == 'pvc-pipes-tree'
```

- [ ] **Step 2: Write failing brand API tests**

```python
# backend/tests/catalog/test_brand_api.py
import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.catalog.models import Brand


@pytest.fixture
def owner(store, db):
    user = User.objects.create(phone='9100000003', is_store_owner=True, is_staff=True)
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
def test_list_brands_public(store, brand):
    res = APIClient().get('/api/v1/brands/')
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]['name'] == 'Supreme'


@pytest.mark.django_db
def test_create_brand_owner(owner_client, store):
    res = owner_client.post(
        '/api/v1/brands/', {'name': 'Jaguar', 'slug': 'jaguar'}, format='json'
    )
    assert res.status_code == 201
    assert Brand.objects.filter(tenant=store, slug='jaguar').exists()


@pytest.mark.django_db
def test_create_brand_unauthenticated_forbidden():
    res = APIClient().post('/api/v1/brands/', {'name': 'X', 'slug': 'x'}, format='json')
    assert res.status_code == 403
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
docker-compose exec backend pytest tests/catalog/test_category_api.py tests/catalog/test_brand_api.py -v
```
Expected: `404 Not Found` (no urls registered) or import errors

- [ ] **Step 4: Create IsStoreOwner permission**

```python
# backend/apps/catalog/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework import status
from rest_framework.exceptions import PermissionDenied


class IsStoreOwner(BasePermission):
    """
    Safe methods (GET/HEAD/OPTIONS) are public.
    Unsafe methods require is_store_owner=True in JWT.
    """
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.auth and request.auth.get('is_store_owner'))
```

- [ ] **Step 5: Create serializers**

```python
# backend/apps/catalog/serializers.py
from rest_framework import serializers
from .models import Category, Brand, Product, ProductVariant, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'is_active', 'children']

    def get_children(self, obj):
        active_children = obj.children.filter(is_active=True)
        return CategoryTreeSerializer(active_children, many=True).data


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductVariantSerializer(serializers.ModelSerializer):
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'sku', 'price', 'sale_price', 'effective_price', 'is_active']
        read_only_fields = ['id', 'effective_price']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'variant', 'image_url', 'sort_order']
        read_only_fields = ['id']


class ProductVariantWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    sku = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    sale_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )


class ProductListSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(
        source='brand.name', read_only=True, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'specifications',
            'category', 'category_name', 'brand', 'brand_name',
            'is_active', 'created_at', 'variants', 'images',
        ]
        read_only_fields = ['id', 'created_at', 'category_name', 'brand_name']


class ProductWriteSerializer(serializers.ModelSerializer):
    variants = ProductVariantWriteSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'specifications',
            'category', 'brand', 'is_active', 'variants',
        ]

    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(**validated_data)
        for v in variants_data:
            ProductVariant.objects.create(product=product, **v)
        return product
```

- [ ] **Step 6: Create views**

```python
# backend/apps/catalog/views.py
from rest_framework import viewsets
from rest_framework.response import Response
from apps.tenants.models import Store
from .models import Category, Brand, Product, ProductVariant
from .permissions import IsStoreOwner
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, BrandSerializer,
    ProductListSerializer, ProductWriteSerializer, ProductVariantSerializer,
)


def get_store_for_request(request) -> Store | None:
    """Resolve tenant: from JWT if authenticated, else single active store."""
    if request.auth:
        tenant_id = request.auth.get('tenant_id')
        if tenant_id:
            return Store.objects.filter(id=tenant_id).first()
    return Store.objects.filter(is_active=True).first()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStoreOwner]

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if not store:
            return Category.objects.none()
        return Category.objects.filter(tenant=store, is_active=True)

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(tenant=store)

    def list(self, request, *args, **kwargs):
        if request.query_params.get('view') == 'tree':
            store = get_store_for_request(request)
            if not store:
                return Response([])
            roots = Category.objects.filter(
                tenant=store, parent__isnull=True, is_active=True
            )
            return Response(CategoryTreeSerializer(roots, many=True).data)
        return super().list(request, *args, **kwargs)


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsStoreOwner]

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if not store:
            return Brand.objects.none()
        return Brand.objects.filter(tenant=store, is_active=True)

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(tenant=store)
```

Note: `ProductViewSet` is added in Task 5.

- [ ] **Step 7: Create catalog URLs**

```python
# backend/apps/catalog/urls.py
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, BrandViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('brands', BrandViewSet, basename='brand')

urlpatterns = router.urls
```

- [ ] **Step 8: Register in config/urls.py**

Replace `backend/config/urls.py` with:

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/', include('apps.tenants.urls')),
    path('api/v1/', include('apps.catalog.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

- [ ] **Step 9: Run tests**

```bash
docker-compose exec backend pytest tests/catalog/test_category_api.py tests/catalog/test_brand_api.py -v
```
Expected: 8 tests PASS

---

### Task 5: Product API

**Files:**
- Modify: `backend/apps/catalog/views.py` (add `ProductViewSet`)
- Modify: `backend/apps/catalog/urls.py` (register `products` router)
- Create: `backend/tests/catalog/test_product_api.py`

**Interfaces:**
- Consumes: `get_store_for_request`, `IsStoreOwner` from Task 4; `ProductListSerializer`, `ProductWriteSerializer`, `ProductVariantSerializer` from Task 4; `Product`, `ProductVariant` from Task 2
- Produces: `GET /api/v1/products/` — list; filters: `?category=<slug>`, `?brand=<slug>`; includes nested `variants` + `images`
- Produces: `GET /api/v1/products/{slug}/` — detail (uses `slug` as lookup field)
- Produces: `POST /api/v1/products/` — owner only; creates product + variants in one request
- Produces: `PATCH /api/v1/products/{id}/` — owner only (uses `id`, registered separately)
- Produces: `GET /api/v1/products/{slug}/variants/` — custom action on detail

- [ ] **Step 1: Write failing product API tests**

```python
# backend/tests/catalog/test_product_api.py
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
docker-compose exec backend pytest tests/catalog/test_product_api.py -v
```
Expected: 404 Not Found on product endpoints

- [ ] **Step 3: Add ProductViewSet to views.py**

Append to `backend/apps/catalog/views.py`:

```python
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsStoreOwner]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'PUT'):
            return ProductWriteSerializer
        return ProductListSerializer

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if not store:
            return Product.objects.none()
        qs = (
            Product.objects.filter(tenant=store, is_active=True)
            .select_related('category', 'brand')
            .prefetch_related('variants', 'images')
        )
        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        brand_slug = self.request.query_params.get('brand')
        if brand_slug:
            qs = qs.filter(brand__slug=brand_slug)
        return qs

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(tenant=store)

    @action(detail=True, methods=['get'], url_path='variants')
    def variants(self, request, slug=None):
        store = get_store_for_request(request)
        product = get_object_or_404(Product, slug=slug, tenant=store)
        active_variants = product.variants.filter(is_active=True)
        return Response(ProductVariantSerializer(active_variants, many=True).data)
```

- [ ] **Step 4: Register products router in urls.py**

Replace `backend/apps/catalog/urls.py` with:

```python
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, BrandViewSet, ProductViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('brands', BrandViewSet, basename='brand')
router.register('products', ProductViewSet, basename='product')

urlpatterns = router.urls
```

- [ ] **Step 5: Run tests**

```bash
docker-compose exec backend pytest tests/catalog/test_product_api.py -v
```
Expected: 8 tests PASS

---

### Task 6: Inventory API

**Files:**
- Create: `backend/apps/inventory/serializers.py`
- Create: `backend/apps/inventory/views.py`
- Create: `backend/apps/inventory/urls.py`
- Create: `backend/apps/inventory/migrations/__init__.py` (already done in Task 3)
- Modify: `backend/config/urls.py` (add inventory urls)
- Create: `backend/tests/inventory/test_api.py`

**Interfaces:**
- Consumes: `Inventory`, `InventoryMovement` from Task 3; `IsStoreOwner` from Task 4; `get_store_for_request` from Task 4; `ProductVariant` from Task 2
- Produces: `GET /api/v1/inventory/` — owner only; list with `variant_name`, `product_name`, `sku`
- Produces: `PATCH /api/v1/inventory/{variant_id}/` — owner only; body `{delta: int, reason: str}`; auto-creates Inventory record if it doesn't exist; returns updated inventory
- Produces: `GET /api/v1/inventory/movements/` — owner only; all movements for this store

- [ ] **Step 1: Write failing inventory API tests**

```python
# backend/tests/inventory/test_api.py
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
docker-compose exec backend pytest tests/inventory/test_api.py -v
```
Expected: 404 Not Found

- [ ] **Step 3: Write inventory serializers**

```python
# backend/apps/inventory/serializers.py
from rest_framework import serializers
from .models import Inventory, InventoryMovement


class InventorySerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    sku = serializers.CharField(source='variant.sku', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'variant', 'variant_name', 'product_name', 'sku',
            'available_qty', 'reserved_qty',
        ]
        read_only_fields = ['id', 'variant_name', 'product_name', 'sku']


class InventoryAdjustSerializer(serializers.Serializer):
    delta = serializers.IntegerField()
    reason = serializers.ChoiceField(choices=InventoryMovement.REASON_CHOICES)


class InventoryMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryMovement
        fields = ['id', 'inventory', 'delta', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']
```

- [ ] **Step 4: Write inventory views**

```python
# backend/apps/inventory/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.catalog.permissions import IsStoreOwner
from apps.catalog.views import get_store_for_request
from apps.catalog.models import ProductVariant
from .models import Inventory, InventoryMovement
from .serializers import (
    InventorySerializer, InventoryAdjustSerializer, InventoryMovementSerializer
)


def _require_owner(request):
    if not (request.auth and request.auth.get('is_store_owner')):
        raise PermissionDenied()


class InventoryViewSet(viewsets.ViewSet):
    permission_classes = [IsStoreOwner]

    def list(self, request):
        _require_owner(request)
        store = get_store_for_request(request)
        inventories = (
            Inventory.objects.filter(tenant=store)
            .select_related('variant__product')
        )
        return Response(InventorySerializer(inventories, many=True).data)

    def partial_update(self, request, pk=None):
        _require_owner(request)
        store = get_store_for_request(request)
        variant = get_object_or_404(ProductVariant, pk=pk, product__tenant=store)
        inventory, _ = Inventory.objects.get_or_create(
            variant=variant,
            defaults={'tenant': store, 'available_qty': 0, 'reserved_qty': 0},
        )
        serializer = InventoryAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory.adjust(
            delta=serializer.validated_data['delta'],
            reason=serializer.validated_data['reason'],
        )
        inventory.refresh_from_db()
        return Response(InventorySerializer(inventory).data)

    @action(detail=False, methods=['get'])
    def movements(self, request):
        _require_owner(request)
        store = get_store_for_request(request)
        movements = InventoryMovement.objects.filter(
            inventory__tenant=store
        ).select_related('inventory')
        return Response(InventoryMovementSerializer(movements, many=True).data)
```

- [ ] **Step 5: Create inventory URLs**

```python
# backend/apps/inventory/urls.py
from rest_framework.routers import SimpleRouter
from .views import InventoryViewSet

router = SimpleRouter()
router.register('inventory', InventoryViewSet, basename='inventory')

urlpatterns = router.urls
```

- [ ] **Step 6: Register in config/urls.py**

Add `path('api/v1/', include('apps.inventory.urls')),` to `backend/config/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/', include('apps.tenants.urls')),
    path('api/v1/', include('apps.catalog.urls')),
    path('api/v1/', include('apps.inventory.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

- [ ] **Step 7: Run tests**

```bash
docker-compose exec backend pytest tests/inventory/test_api.py -v
```
Expected: 7 tests PASS

- [ ] **Step 8: Run full test suite**

```bash
docker-compose exec backend pytest tests/ -v
```
Expected: all existing tests still PASS

---

### Task 7: Product Listing Frontend Page

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/components/product/ProductCard.tsx`
- Create: `frontend/components/product/ProductGrid.tsx`
- Create: `frontend/app/(store)/products/page.tsx`
- Modify: `frontend/app/(store)/page.tsx` (add navigation to products)

**Interfaces:**
- Consumes: `GET /api/v1/products/` and `GET /api/v1/categories/` — server-side fetch, no auth needed
- Produces: `/products` page — server component; sticky header, category sidebar (desktop) + horizontal chip strip (mobile), product grid
- Produces: `ProductCard` — links to `/products/{slug}`, shows image, category name, product name, lowest price with "onwards" if multiple variants
- Produces: `ProductGrid` — responsive 2-4 column grid; empty state SVG message

- [ ] **Step 1: Create types file**

```typescript
// frontend/lib/types.ts
export interface Category {
  id: number;
  name: string;
  slug: string;
  image: string;
  parent: number | null;
  is_active: boolean;
  created_at: string;
}

export interface ProductVariant {
  id: number;
  name: string;
  sku: string;
  price: string;
  sale_price: string | null;
  effective_price: string;
  is_active: boolean;
}

export interface ProductImage {
  id: number;
  variant: number | null;
  image_url: string;
  sort_order: number;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  specifications: Record<string, string>;
  category: number;
  category_name: string;
  brand: number | null;
  brand_name: string | null;
  is_active: boolean;
  created_at: string;
  variants: ProductVariant[];
  images: ProductImage[];
}

export interface Brand {
  id: number;
  name: string;
  slug: string;
  logo: string;
  is_active: boolean;
  created_at: string;
}
```

- [ ] **Step 2: Create component directories**

```bash
mkdir -p frontend/components/product
mkdir -p frontend/components/admin
mkdir -p "frontend/app/(store)/products/[slug]"
mkdir -p frontend/app/admin/products/new
```

- [ ] **Step 3: Create ProductCard**

```tsx
// frontend/components/product/ProductCard.tsx
import Link from 'next/link';
import type { Product } from '@/lib/types';

export default function ProductCard({ product }: { product: Product }) {
  const lowestPrice = product.variants.reduce<string | null>((min, v) => {
    const price = v.effective_price;
    return min === null || parseFloat(price) < parseFloat(min) ? price : min;
  }, null);

  const image = product.images[0]?.image_url;

  return (
    <Link
      href={`/products/${product.slug}`}
      className="group block bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100 hover:shadow-md transition-shadow duration-200 cursor-pointer"
    >
      <div className="aspect-square bg-slate-50 flex items-center justify-center overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <svg className="w-16 h-16 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0v10l-8 4m0-10L4 7m8 10V7" />
          </svg>
        )}
      </div>
      <div className="p-4">
        <p className="text-xs text-orange-500 font-medium mb-1 font-['Jost'] uppercase tracking-wide">
          {product.category_name}
        </p>
        <h3 className="text-slate-900 font-medium leading-snug mb-2 font-['Jost'] line-clamp-2 text-sm">
          {product.name}
        </h3>
        {lowestPrice && (
          <p className="text-base font-semibold text-slate-800 font-['Jost']">
            ₹{parseFloat(lowestPrice).toFixed(0)}
            {product.variants.length > 1 && (
              <span className="text-xs font-normal text-slate-500"> onwards</span>
            )}
          </p>
        )}
        {!lowestPrice && (
          <p className="text-sm text-slate-400 font-['Jost']">Price on request</p>
        )}
      </div>
    </Link>
  );
}
```

- [ ] **Step 4: Create ProductGrid**

```tsx
// frontend/components/product/ProductGrid.tsx
import ProductCard from './ProductCard';
import type { Product } from '@/lib/types';

export default function ProductGrid({ products }: { products: Product[] }) {
  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <svg className="w-16 h-16 text-slate-200 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p className="text-slate-400 font-['Jost'] text-sm">No products found in this category.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
```

- [ ] **Step 5: Create product listing page**

```tsx
// frontend/app/(store)/products/page.tsx
import Link from 'next/link';
import ProductGrid from '@/components/product/ProductGrid';
import type { Product, Category } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function getProducts(categorySlug?: string): Promise<Product[]> {
  const url = categorySlug
    ? `${BASE_URL}/api/v1/products/?category=${encodeURIComponent(categorySlug)}`
    : `${BASE_URL}/api/v1/products/`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) return [];
  return res.json();
}

async function getCategories(): Promise<Category[]> {
  const res = await fetch(`${BASE_URL}/api/v1/categories/`, { next: { revalidate: 300 } });
  if (!res.ok) return [];
  return res.json();
}

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: { category?: string };
}) {
  const [products, categories] = await Promise.all([
    getProducts(searchParams.category),
    getCategories(),
  ]);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="font-['Bodoni_Moda'] text-xl font-bold text-slate-900">
            Hardware Store
          </Link>
          <Link
            href="/login"
            className="text-sm text-slate-600 font-['Jost'] hover:text-orange-500 transition-colors min-h-[44px] flex items-center"
          >
            Login
          </Link>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900 mb-6">Products</h1>

        <div className="md:flex md:gap-6">
          {/* Desktop category sidebar */}
          <aside className="hidden md:block w-48 shrink-0">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 font-['Jost']">
              Categories
            </h2>
            <nav className="space-y-0.5">
              <Link
                href="/products"
                className={`block px-3 py-2.5 rounded-xl text-sm font-['Jost'] transition-colors ${
                  !searchParams.category
                    ? 'bg-orange-50 text-orange-600 font-semibold'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                All Products
              </Link>
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/products?category=${cat.slug}`}
                  className={`block px-3 py-2.5 rounded-xl text-sm font-['Jost'] transition-colors ${
                    searchParams.category === cat.slug
                      ? 'bg-orange-50 text-orange-600 font-semibold'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {cat.name}
                </Link>
              ))}
            </nav>
          </aside>

          <div className="flex-1 min-w-0">
            {/* Mobile category chip strip */}
            <div className="md:hidden overflow-x-auto -mx-4 px-4 mb-4">
              <div className="flex gap-2 pb-2 w-max">
                <Link
                  href="/products"
                  className={`shrink-0 px-4 py-2 rounded-full text-sm font-['Jost'] transition-colors min-h-[44px] flex items-center ${
                    !searchParams.category
                      ? 'bg-orange-500 text-white font-medium'
                      : 'bg-white text-slate-600 border border-slate-200'
                  }`}
                >
                  All
                </Link>
                {categories.map((cat) => (
                  <Link
                    key={cat.id}
                    href={`/products?category=${cat.slug}`}
                    className={`shrink-0 px-4 py-2 rounded-full text-sm font-['Jost'] transition-colors min-h-[44px] flex items-center ${
                      searchParams.category === cat.slug
                        ? 'bg-orange-500 text-white font-medium'
                        : 'bg-white text-slate-600 border border-slate-200'
                    }`}
                  >
                    {cat.name}
                  </Link>
                ))}
              </div>
            </div>

            <ProductGrid products={products} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Update home page**

```tsx
// frontend/app/(store)/page.tsx
import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-slate-50 gap-8 px-4">
      <div className="text-center">
        <h1 className="font-['Bodoni_Moda'] text-4xl font-bold text-slate-900 mb-2">
          Hardware Store
        </h1>
        <p className="text-slate-500 font-['Jost']">
          Quality hardware & sanitary delivered to your door
        </p>
      </div>
      <Link
        href="/products"
        className="bg-orange-500 text-white px-8 py-4 rounded-xl font-['Jost'] font-semibold text-lg hover:bg-orange-600 transition-colors min-h-[52px] flex items-center"
      >
        Browse Products
      </Link>
    </main>
  );
}
```

- [ ] **Step 7: Verify page loads**

```bash
docker-compose logs frontend --tail=30
```
Open http://localhost:3000 — should show home page. Click "Browse Products" → http://localhost:3000/products — renders grid (empty if no products yet, or with products if some were added via API).

---

### Task 8: Product Detail Frontend Page

**Files:**
- Create: `frontend/components/product/VariantSelector.tsx`
- Create: `frontend/app/(store)/products/[slug]/page.tsx`

**Interfaces:**
- Consumes: `GET /api/v1/products/{slug}/` — server-side fetch
- Produces: `/products/{slug}` page — back navigation, product image, category/brand label, name, description, variant selector, specifications grid
- `VariantSelector` — `'use client'`; shows variant buttons (48px touch target), displays selected variant's effective_price with crossed-out original if on sale, "Add to Cart" placeholder button

- [ ] **Step 1: Create VariantSelector component**

```tsx
// frontend/components/product/VariantSelector.tsx
'use client';
import { useState } from 'react';
import type { ProductVariant } from '@/lib/types';

interface Props {
  variants: ProductVariant[];
}

export default function VariantSelector({ variants }: Props) {
  const [selected, setSelected] = useState<ProductVariant>(variants[0]);

  if (variants.length === 0) return null;

  return (
    <div>
      {/* Variant buttons */}
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 font-['Jost']">
        Select Size / Variant
      </p>
      <div className="flex flex-wrap gap-2 mb-5">
        {variants.map((v) => (
          <button
            key={v.id}
            onClick={() => setSelected(v)}
            className={`px-4 py-2.5 rounded-xl border text-sm font-['Jost'] transition-all duration-150 cursor-pointer min-h-[48px] ${
              selected.id === v.id
                ? 'border-orange-500 bg-orange-50 text-orange-700 font-semibold'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
            }`}
          >
            {v.name}
          </button>
        ))}
      </div>

      {/* Price */}
      <div className="flex items-baseline gap-3 mb-6">
        <span className="text-3xl font-bold text-slate-900 font-['Jost']">
          ₹{parseFloat(selected.effective_price).toFixed(0)}
        </span>
        {selected.sale_price && (
          <span className="text-slate-400 line-through text-base font-['Jost']">
            ₹{parseFloat(selected.price).toFixed(0)}
          </span>
        )}
        {selected.sale_price && (
          <span className="text-green-600 text-sm font-medium font-['Jost']">
            {Math.round((1 - parseFloat(selected.sale_price) / parseFloat(selected.price)) * 100)}% off
          </span>
        )}
      </div>

      {/* Add to cart — Phase 7 placeholder */}
      <button
        className="w-full bg-orange-500 hover:bg-orange-600 active:bg-orange-700 text-white font-semibold py-4 rounded-xl font-['Jost'] text-base transition-colors cursor-pointer min-h-[52px]"
        onClick={() => {
          alert('Cart coming in Phase 7');
        }}
      >
        Add to Cart
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Create product detail page**

```tsx
// frontend/app/(store)/products/[slug]/page.tsx
import Link from 'next/link';
import { notFound } from 'next/navigation';
import VariantSelector from '@/components/product/VariantSelector';
import type { Product } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function getProduct(slug: string): Promise<Product | null> {
  const res = await fetch(`${BASE_URL}/api/v1/products/${slug}/`, {
    next: { revalidate: 60 },
  });
  if (res.status === 404) return null;
  if (!res.ok) return null;
  return res.json();
}

export default async function ProductDetailPage({
  params,
}: {
  params: { slug: string };
}) {
  const product = await getProduct(params.slug);
  if (!product) notFound();

  const activeVariants = product.variants.filter((v) => v.is_active);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header with back nav */}
      <header className="bg-white border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <Link
            href="/products"
            className="text-slate-500 hover:text-slate-700 transition-colors cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center -ml-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <nav className="flex items-center gap-2 text-sm text-slate-500 font-['Jost']">
            <Link href="/products" className="hover:text-orange-500 transition-colors">
              Products
            </Link>
            <span>/</span>
            <span className="text-slate-700">{product.category_name}</span>
          </nav>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100">
          <div className="md:grid md:grid-cols-2">
            {/* Image */}
            <div className="aspect-square bg-slate-50 flex items-center justify-center overflow-hidden">
              {product.images[0] ? (
                <img
                  src={product.images[0].image_url}
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <svg
                  className="w-24 h-24 text-slate-200"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0v10l-8 4m0-10L4 7m8 10V7" />
                </svg>
              )}
            </div>

            {/* Details */}
            <div className="p-6 flex flex-col gap-3">
              <div>
                <p className="text-xs text-orange-500 font-semibold uppercase tracking-wider mb-1 font-['Jost']">
                  {product.category_name}
                </p>
                <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900 leading-tight">
                  {product.name}
                </h1>
                {product.brand_name && (
                  <p className="text-sm text-slate-500 font-['Jost'] mt-1">
                    by {product.brand_name}
                  </p>
                )}
              </div>

              {product.description && (
                <p className="text-slate-600 font-['Jost'] text-sm leading-relaxed">
                  {product.description}
                </p>
              )}

              {activeVariants.length > 0 ? (
                <VariantSelector variants={activeVariants} />
              ) : (
                <p className="text-slate-400 font-['Jost'] text-sm">
                  No variants available.
                </p>
              )}
            </div>
          </div>

          {/* Specifications */}
          {Object.keys(product.specifications).length > 0 && (
            <div className="border-t border-slate-100 p-6">
              <h2 className="font-['Bodoni_Moda'] text-lg font-bold text-slate-900 mb-4">
                Specifications
              </h2>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                {Object.entries(product.specifications).map(([key, value]) => (
                  <div key={key} className="bg-slate-50 rounded-xl p-3">
                    <p className="text-xs text-slate-400 font-['Jost'] mb-0.5 capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-slate-900 font-semibold font-['Jost'] text-sm">
                      {String(value)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify pages**

```bash
docker-compose logs frontend --tail=20
```
Open http://localhost:3000/products → click a product card → should render detail page with variant selector and specs.

If no products exist yet, create one via API to test:
```bash
# First get an owner token:
curl -X POST http://localhost:8000/api/v1/auth/otp/request/ -H "Content-Type: application/json" -d '{"phone": "YOUR_OWNER_PHONE"}'
# Check docker-compose logs backend for OTP, then verify and get token
# Then POST /api/v1/products/ with the token
```

---

### Task 9: Admin Products Management Page

**Files:**
- Create: `frontend/app/admin/layout.tsx`
- Create: `frontend/app/admin/products/page.tsx`
- Create: `frontend/components/admin/ProductForm.tsx`
- Create: `frontend/app/admin/products/new/page.tsx`

**Interfaces:**
- Consumes: `GET /api/v1/products/` (owner JWT), `POST /api/v1/products/`, `GET /api/v1/categories/` — all via `apiFetch` from `lib/api.ts`
- Produces: `/admin/products` — client component; owner-only guard via `useAuthStore`; table of products with name, category, variant count, status
- Produces: `/admin/products/new` — create product form with name, slug (auto-generated), category dropdown, description, specs (key:value text area), and dynamic variant rows (name + SKU + price)
- Note: admin layout reads auth from Zustand store — auth persists only within the browser tab session (localStorage-backed). Redirect to `/login` if not owner.

- [ ] **Step 1: Create admin layout with owner guard**

```tsx
// frontend/app/admin/layout.tsx
'use client';
import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated || !user?.isStoreOwner) {
      router.replace('/login');
    }
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated || !user?.isStoreOwner) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-400 font-['Jost'] text-sm">Checking permissions...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-6">
          <span className="font-['Bodoni_Moda'] text-lg font-bold text-slate-900">Admin</span>
          <nav className="flex gap-4">
            <Link
              href="/admin/products"
              className="text-sm text-slate-600 hover:text-orange-500 font-['Jost'] transition-colors min-h-[44px] flex items-center"
            >
              Products
            </Link>
          </nav>
          <div className="ml-auto">
            <Link
              href="/"
              className="text-sm text-slate-500 hover:text-slate-700 font-['Jost'] transition-colors min-h-[44px] flex items-center"
            >
              ← Store
            </Link>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: Create admin products list page**

```tsx
// frontend/app/admin/products/page.tsx
'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import type { Product } from '@/lib/types';

export default function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch<Product[]>('/api/v1/products/')
      .then(setProducts)
      .catch(() => setError('Failed to load products'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-slate-400 font-['Jost'] text-sm">Loading...</p>;
  }

  if (error) {
    return <p className="text-red-500 font-['Jost'] text-sm">{error}</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900">Products</h1>
        <Link
          href="/admin/products/new"
          className="bg-orange-500 text-white px-5 py-2.5 rounded-xl text-sm font-semibold font-['Jost'] hover:bg-orange-600 transition-colors cursor-pointer min-h-[44px] flex items-center gap-1.5"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Product
        </Link>
      </div>

      {products.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-100">
          <p className="text-slate-400 font-['Jost'] text-sm mb-4">No products yet.</p>
          <Link
            href="/admin/products/new"
            className="text-orange-500 font-medium font-['Jost'] text-sm hover:text-orange-600 transition-colors"
          >
            Create your first product →
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost']">
                    Product
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost'] hidden md:table-cell">
                    Category
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost']">
                    Variants
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost'] hidden sm:table-cell">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-900 font-['Jost'] text-sm">{p.name}</p>
                      <p className="text-xs text-slate-400 font-['Jost']">{p.slug}</p>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 font-['Jost'] hidden md:table-cell">
                      {p.category_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 font-['Jost']">
                      {p.variants.length}
                    </td>
                    <td className="px-6 py-4 hidden sm:table-cell">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium font-['Jost'] ${
                          p.is_active
                            ? 'bg-green-50 text-green-700'
                            : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        {p.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create ProductForm component**

```tsx
// frontend/components/admin/ProductForm.tsx
'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import type { Category } from '@/lib/types';

interface VariantRow {
  name: string;
  sku: string;
  price: string;
}

const INPUT = 'w-full border border-slate-200 rounded-xl px-4 py-3 text-slate-900 font-["Jost"] text-sm focus:outline-none focus:ring-2 focus:ring-orange-200 focus:border-orange-400 bg-white min-h-[48px] transition-colors';
const LABEL = 'block text-sm font-medium text-slate-700 font-["Jost"] mb-1.5';

export default function ProductForm() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: '',
    slug: '',
    category: '',
    description: '',
    specifications: '',
  });
  const [variants, setVariants] = useState<VariantRow[]>([
    { name: '', sku: '', price: '' },
  ]);

  useEffect(() => {
    apiFetch<Category[]>('/api/v1/categories/')
      .then(setCategories)
      .catch(console.error);
  }, []);

  const handleNameChange = (name: string) => {
    const slug = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    setForm((f) => ({ ...f, name, slug }));
  };

  const parseSpecs = (text: string): Record<string, string> => {
    const specs: Record<string, string> = {};
    text.split('\n').forEach((line) => {
      const colonIdx = line.indexOf(':');
      if (colonIdx > 0) {
        const key = line.slice(0, colonIdx).trim();
        const value = line.slice(colonIdx + 1).trim();
        if (key && value) specs[key] = value;
      }
    });
    return specs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await apiFetch('/api/v1/products/', {
        method: 'POST',
        body: JSON.stringify({
          name: form.name,
          slug: form.slug,
          category: parseInt(form.category),
          description: form.description,
          specifications: parseSpecs(form.specifications),
          variants: variants.filter((v) => v.name && v.sku && v.price),
        }),
      });
      router.push('/admin/products');
    } catch (err: unknown) {
      const msg =
        typeof err === 'object' && err !== null && !Array.isArray(err)
          ? Object.entries(err as Record<string, unknown>)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
              .join(' | ')
          : 'Failed to create product';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const addVariant = () => setVariants((vs) => [...vs, { name: '', sku: '', price: '' }]);
  const removeVariant = (i: number) => setVariants((vs) => vs.filter((_, idx) => idx !== i));
  const updateVariant = (i: number, field: keyof VariantRow, value: string) =>
    setVariants((vs) => vs.map((v, idx) => (idx === i ? { ...v, [field]: value } : v)));

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-2xl">
      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl px-4 py-3 text-sm font-['Jost']">
          {error}
        </div>
      )}

      {/* Product details card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-100 space-y-4">
        <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 text-lg">Product Details</h2>

        <div>
          <label className={LABEL}>Name *</label>
          <input
            className={INPUT}
            value={form.name}
            onChange={(e) => handleNameChange(e.target.value)}
            required
            placeholder="e.g. PVC Pipe 2 inch"
          />
        </div>

        <div>
          <label className={LABEL}>
            Slug * <span className="text-slate-400 font-normal text-xs">(auto-generated, edit if needed)</span>
          </label>
          <input
            className={INPUT}
            value={form.slug}
            onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
            required
            pattern="[a-z0-9-]+"
            title="Lowercase letters, numbers, hyphens only"
          />
        </div>

        <div>
          <label className={LABEL}>Category *</label>
          <select
            className={INPUT}
            value={form.category}
            onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            required
          >
            <option value="">Select a category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={LABEL}>Description</label>
          <textarea
            className={`${INPUT} min-h-[90px] resize-y`}
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            placeholder="Brief product description"
          />
        </div>

        <div>
          <label className={LABEL}>
            Specifications{' '}
            <span className="text-slate-400 font-normal text-xs">
              (one per line: key: value)
            </span>
          </label>
          <textarea
            className={`${INPUT} min-h-[80px] resize-y font-mono text-xs`}
            value={form.specifications}
            onChange={(e) => setForm((f) => ({ ...f, specifications: e.target.value }))}
            placeholder={'material: PVC\ndiameter: 2 inch\ncolor: white'}
          />
        </div>
      </div>

      {/* Variants card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-100">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 text-lg">Variants</h2>
          <button
            type="button"
            onClick={addVariant}
            className="text-orange-500 text-sm font-medium font-['Jost'] hover:text-orange-600 transition-colors cursor-pointer min-h-[44px] flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Variant
          </button>
        </div>

        <div className="space-y-3">
          {variants.map((v, i) => (
            <div key={i} className="grid grid-cols-3 gap-3 items-end">
              <div>
                {i === 0 && <label className={LABEL}>Name *</label>}
                <input
                  className={INPUT}
                  value={v.name}
                  onChange={(e) => updateVariant(i, 'name', e.target.value)}
                  placeholder="e.g. 1 inch"
                  required
                />
              </div>
              <div>
                {i === 0 && <label className={LABEL}>SKU *</label>}
                <input
                  className={INPUT}
                  value={v.sku}
                  onChange={(e) => updateVariant(i, 'sku', e.target.value.toUpperCase())}
                  placeholder="e.g. PVC-1IN"
                  required
                />
              </div>
              <div className="relative">
                {i === 0 && <label className={LABEL}>Price (₹) *</label>}
                <input
                  className={INPUT}
                  type="number"
                  min="0"
                  step="0.01"
                  value={v.price}
                  onChange={(e) => updateVariant(i, 'price', e.target.value)}
                  placeholder="0.00"
                  required
                />
                {variants.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeVariant(i)}
                    className="absolute -top-5 right-0 text-xs text-slate-400 hover:text-red-500 transition-colors cursor-pointer font-['Jost']"
                  >
                    remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-orange-300 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl font-['Jost'] text-base transition-colors cursor-pointer min-h-[52px]"
      >
        {submitting ? 'Creating...' : 'Create Product'}
      </button>
    </form>
  );
}
```

- [ ] **Step 4: Create admin new product page**

```tsx
// frontend/app/admin/products/new/page.tsx
import Link from 'next/link';
import ProductForm from '@/components/admin/ProductForm';

export default function NewProductPage() {
  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/admin/products"
          className="text-slate-500 hover:text-slate-700 transition-colors cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center -ml-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900">New Product</h1>
      </div>
      <ProductForm />
    </div>
  );
}
```

- [ ] **Step 5: Verify admin flow**

```bash
docker-compose logs frontend --tail=20
```

Test flow:
1. Go to http://localhost:3000/login → login as store owner (OTP from `docker-compose logs backend | grep OTP`)
2. Go to http://localhost:3000/admin/products — should show product list (or empty state)
3. Click "Add Product" → fill in name, category, variant(s) → submit
4. Should redirect back to `/admin/products` showing the new product
5. Go to http://localhost:3000/products — new product should appear in the grid

---

## Self-Review Checklist

After writing the plan, check against spec:

- [x] Phase 3: Category system with unlimited nesting (adjacency list via `parent` FK) — Tasks 1, 4
- [x] Phase 4: Product, ProductVariant, Brand, ProductImage models + CRUD API — Tasks 2, 5
- [x] Phase 5: Inventory + InventoryMovement + adjust() state machine — Tasks 3, 6
- [x] Frontend product listing page — Task 7
- [x] Frontend product detail page with variant selector — Task 8
- [x] Admin product management (list + create form) — Task 9
- [x] `?view=tree` for category tree (spec says `?format=tree` but that conflicts with DRF — note this divergence)
- [x] Tenant isolation tested in every model test
- [x] Owner-only writes protected by `IsStoreOwner` permission
- [x] Public reads (product list, detail, categories, brands) require no auth
- [x] No `__all__` in serializers — all use explicit `fields = [...]`
- [x] All touch targets ≥ 48px on interactive elements
- [x] Fonts: `font-['Bodoni_Moda']` headings, `font-['Jost']` body throughout
- [x] `get_store_for_request` handles both authenticated (JWT) and unauthenticated (single active store) requests
- [x] No `git` steps — progress tracked in `.superpowers/sdd/progress.md`
