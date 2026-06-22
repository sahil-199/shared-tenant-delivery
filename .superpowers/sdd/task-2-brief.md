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

