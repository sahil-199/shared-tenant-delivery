# Task 1 Brief: Phase 6 — Product Search & Filters (Backend)

## Context
Multi-tenant hardware/sanitary commerce platform. Backend is Django 5.1 + DRF 3.15 + PostgreSQL 16. Plans 1 & 2 are fully complete. This is Task 1 of Plan 3.

## What to build
Extend the existing `ProductViewSet.get_queryset()` in `backend/apps/catalog/views.py` to support additional filter/sort query params.

## Exact changes required

### 1. Add to imports at top of `backend/apps/catalog/views.py`
```python
from django.db.models import Min, Q
```

### 2. Replace `get_queryset` method of `ProductViewSet` with:
```python
def get_queryset(self):
    store = get_store_for_request(self.request)
    if not store:
        return Product.objects.none()
    qs = (
        Product.objects.filter(tenant=store, is_active=True)
        .select_related('category', 'brand')
        .prefetch_related('variants', 'images')
        .annotate(min_price=Min('variants__price'))
    )
    params = self.request.query_params

    category_slug = params.get('category')
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    brand_slug = params.get('brand')
    if brand_slug:
        qs = qs.filter(brand__slug=brand_slug)

    search = params.get('search')
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

    min_price = params.get('min_price')
    if min_price:
        qs = qs.filter(min_price__gte=min_price)

    max_price = params.get('max_price')
    if max_price:
        qs = qs.filter(min_price__lte=max_price)

    if params.get('in_stock') == 'true':
        qs = qs.filter(variants__inventory__available_qty__gt=0).distinct()

    sort = params.get('sort')
    if sort == 'price_asc':
        qs = qs.order_by('min_price')
    elif sort == 'price_desc':
        qs = qs.order_by('-min_price')
    else:
        qs = qs.order_by('-created_at')

    return qs
```

### 3. Create `backend/tests/catalog/test_product_filters.py`:
```python
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import Inventory


@pytest.mark.django_db
def test_search_by_name(store, category):
    Product.objects.create(tenant=store, category=category, name='Ball Valve', slug='ball-valve')
    Product.objects.create(tenant=store, category=category, name='Gate Valve', slug='gate-valve')
    res = APIClient().get('/api/v1/products/?search=ball')
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]['slug'] == 'ball-valve'


@pytest.mark.django_db
def test_search_by_description(store, category):
    Product.objects.create(
        tenant=store, category=category, name='Pipe', slug='pipe-desc',
        description='high pressure industrial fitting'
    )
    Product.objects.create(tenant=store, category=category, name='Valve', slug='valve-desc')
    res = APIClient().get('/api/v1/products/?search=industrial')
    assert len(res.json()) == 1


@pytest.mark.django_db
def test_filter_in_stock(store, category):
    p_in = Product.objects.create(tenant=store, category=category, name='In Stock', slug='in-stock')
    v_in = ProductVariant.objects.create(product=p_in, name='A', sku='IN-A', price=Decimal('10'))
    Inventory.objects.create(tenant=store, variant=v_in, available_qty=5, reserved_qty=0)

    p_out = Product.objects.create(tenant=store, category=category, name='Out Stock', slug='out-stock')
    v_out = ProductVariant.objects.create(product=p_out, name='B', sku='OUT-B', price=Decimal('10'))
    Inventory.objects.create(tenant=store, variant=v_out, available_qty=0, reserved_qty=0)

    res = APIClient().get('/api/v1/products/?in_stock=true')
    slugs = [d['slug'] for d in res.json()]
    assert 'in-stock' in slugs
    assert 'out-stock' not in slugs


@pytest.mark.django_db
def test_sort_price_asc(store, category):
    p1 = Product.objects.create(tenant=store, category=category, name='Cheap', slug='cheap')
    ProductVariant.objects.create(product=p1, name='A', sku='CH-A', price=Decimal('10'))
    p2 = Product.objects.create(tenant=store, category=category, name='Expensive', slug='expensive')
    ProductVariant.objects.create(product=p2, name='B', sku='EX-B', price=Decimal('100'))

    res = APIClient().get('/api/v1/products/?sort=price_asc')
    slugs = [d['slug'] for d in res.json()]
    assert slugs.index('cheap') < slugs.index('expensive')


@pytest.mark.django_db
def test_sort_price_desc(store, category):
    p1 = Product.objects.create(tenant=store, category=category, name='Cheap2', slug='cheap2')
    ProductVariant.objects.create(product=p1, name='A', sku='CH2-A', price=Decimal('10'))
    p2 = Product.objects.create(tenant=store, category=category, name='Pricey2', slug='pricey2')
    ProductVariant.objects.create(product=p2, name='B', sku='PR2-B', price=Decimal('200'))

    res = APIClient().get('/api/v1/products/?sort=price_desc')
    slugs = [d['slug'] for d in res.json()]
    assert slugs.index('pricey2') < slugs.index('cheap2')
```

## Test command (requires Docker running)
```bash
docker-compose exec backend pytest tests/catalog/test_product_filters.py -v
```

## Global constraints
- No git commits in this project
- API prefix: /api/v1/
- All DRF serializers use explicit fields (no __all__)
- No unrequested abstractions

## Report file
Write your report to: .superpowers/sdd/plan3/task-1-report.md

## Report format
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Files changed: list
Tests: command run + outcome (PASS/FAIL/SKIP if Docker not available)
Concerns: any (or none)
