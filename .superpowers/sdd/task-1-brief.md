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

