# Commerce Implementation Plan (Phases 6–10)

> **For agentic workers:** Use superpowers:subagent-driven-development to implement task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build product discovery, cart, checkout, orders, and payments on top of the existing catalog/inventory foundation.

**Architecture:** Three new Django apps — `apps.cart`, `apps.orders`, `apps.payments` — plus a `apps.notifications` stub. Frontend adds cart drawer (Zustand), checkout flow, and order history pages.

**Tech Stack:** Django 5.1, DRF 3.15, PostgreSQL 16, Next.js 14 App Router, TypeScript, TailwindCSS v4

---

## Global Constraints

- **No git in this project**
- Every tenant-scoped model extends `TenantModel` from `apps/tenants/models.py`
- API prefix: `/api/v1/` — all endpoints use this prefix
- Tests run inside Docker: `docker-compose exec backend pytest tests/path/test_file.py -v`
- Frontend: Next.js 14 App Router, TailwindCSS v4 (`@theme inline` in `globals.css`)
- Fonts: `font-['Bodoni_Moda']` headings, `font-['Jost']` body — already loaded
- Color palette: slate-50 background, orange-500 CTA, white cards, slate-900 headings
- Minimum touch target: 48px height on all interactive elements
- `IsStoreOwner` permission already in `apps/catalog/permissions.py`
- `get_store_for_request()` already in `apps/catalog/views.py`
- Existing conftest fixtures: `store`, `category`, `brand`, `product`, `variant`

---

## File Map

```
backend/
  apps/
    cart/
      __init__.py, apps.py, models.py, serializers.py, views.py, urls.py, admin.py
      migrations/__init__.py, 0001_initial.py
    orders/
      __init__.py, apps.py, models.py, serializers.py, views.py, urls.py, admin.py
      migrations/__init__.py, 0001_initial.py
    payments/
      __init__.py, apps.py, models.py, serializers.py, views.py, urls.py, admin.py
      migrations/__init__.py, 0001_initial.py
    notifications/
      __init__.py, apps.py, services.py
  tests/
    cart/__init__.py, test_models.py, test_api.py
    orders/__init__.py, test_models.py, test_api.py
    payments/__init__.py, test_models.py, test_api.py

frontend/
  store/cart.ts
  components/cart/CartDrawer.tsx, CartItem.tsx
  components/checkout/AddressForm.tsx, PaymentSelector.tsx
  components/order/OrderCard.tsx, OrderTimeline.tsx
  app/(store)/
    cart/page.tsx
    checkout/page.tsx
    orders/page.tsx, [id]/page.tsx
  app/admin/
    orders/page.tsx
    inventory/page.tsx
```

---

### Task 1: Phase 6 — Product Search & Filters (Backend)

**Files:**
- Modify: `backend/apps/catalog/views.py` — extend `ProductViewSet.get_queryset()`
- Create: `backend/tests/catalog/test_product_filters.py`

**Interfaces:**
- Extends existing `GET /api/v1/products/` with:
  - `?search=<text>` — icontains on `name` + `description`
  - `?min_price=<n>` and `?max_price=<n>` — filter by min variant price (annotated)
  - `?in_stock=true` — only products with `inventory.available_qty > 0`
  - `?sort=price_asc|price_desc|newest` — order results

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/catalog/test_product_filters.py
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

- [ ] **Step 2: Run to confirm failure**

```bash
docker-compose exec backend pytest tests/catalog/test_product_filters.py -v
```

- [ ] **Step 3: Extend `ProductViewSet.get_queryset()` in views.py**

At the top of `backend/apps/catalog/views.py`, add to existing imports:
```python
from django.db.models import Min, Q
```

Replace the `get_queryset` method in `ProductViewSet` with:

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

- [ ] **Step 4: Run tests**

```bash
docker-compose exec backend pytest tests/catalog/test_product_filters.py -v
```
Expected: 5 tests PASS

---

### Task 2: Phase 6 — Product Search & Filters (Frontend)

**Files:**
- Create: `frontend/components/product/SearchBar.tsx`
- Modify: `frontend/app/(store)/products/page.tsx` — add search bar + sort dropdown

**Interfaces:**
- `SearchBar` — `'use client'`; updates URL `?search=` param with `useRouter`; debounced 300ms
- Products page adds `?sort=` dropdown; search + sort params passed server-side to API

- [ ] **Step 1: Create SearchBar component**

```tsx
// frontend/components/product/SearchBar.tsx
'use client';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useCallback, useTransition } from 'react';

export default function SearchBar({ defaultValue = '' }: { defaultValue?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  const handleChange = useCallback(
    (value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set('search', value);
      } else {
        params.delete('search');
      }
      startTransition(() => {
        router.replace(`${pathname}?${params.toString()}`);
      });
    },
    [router, pathname, searchParams]
  );

  return (
    <div className="relative">
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
        fill="none" viewBox="0 0 24 24" stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
      </svg>
      <input
        type="search"
        defaultValue={defaultValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="Search products..."
        className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm font-['Jost'] text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-200 focus:border-orange-400 min-h-[44px]"
      />
    </div>
  );
}
```

- [ ] **Step 2: Update products page to include search + sort**

Replace `frontend/app/(store)/products/page.tsx` search params handling. Add `search` and `sort` to the existing page:

At the top of the server component, update `getProducts` and add `sort` to `searchParams`:

```tsx
// frontend/app/(store)/products/page.tsx
import { Suspense } from 'react';
import Link from 'next/link';
import ProductGrid from '@/components/product/ProductGrid';
import SearchBar from '@/components/product/SearchBar';
import type { Product, Category } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function getProducts(params: { category?: string; search?: string; sort?: string }): Promise<Product[]> {
  const qs = new URLSearchParams();
  if (params.category) qs.set('category', params.category);
  if (params.search) qs.set('search', params.search);
  if (params.sort) qs.set('sort', params.sort);
  const res = await fetch(`${BASE_URL}/api/v1/products/?${qs}`, { next: { revalidate: 60 } });
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
  searchParams: { category?: string; search?: string; sort?: string };
}) {
  const [products, categories] = await Promise.all([
    getProducts(searchParams),
    getCategories(),
  ]);

  return (
    <div className="min-h-screen bg-slate-50">
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
        <div className="flex items-center justify-between mb-6 gap-4">
          <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900 shrink-0">Products</h1>
          <div className="flex gap-3 flex-1 max-w-lg">
            <Suspense fallback={null}>
              <SearchBar defaultValue={searchParams.search} />
            </Suspense>
            <select
              defaultValue={searchParams.sort ?? ''}
              className="border border-slate-200 rounded-xl px-3 py-2 text-sm font-['Jost'] text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-orange-200 min-h-[44px] shrink-0"
              onChange={(e) => {
                // handled client-side via form/link — server renders with URL param
              }}
            >
              <option value="">Newest</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
            </select>
          </div>
        </div>

        <div className="md:flex md:gap-6">
          <aside className="hidden md:block w-48 shrink-0">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 font-['Jost']">
              Categories
            </h2>
            <nav className="space-y-0.5">
              <Link
                href="/products"
                className={`block px-3 py-2.5 rounded-xl text-sm font-['Jost'] transition-colors ${
                  !searchParams.category ? 'bg-orange-50 text-orange-600 font-semibold' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                All Products
              </Link>
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/products?category=${cat.slug}`}
                  className={`block px-3 py-2.5 rounded-xl text-sm font-['Jost'] transition-colors ${
                    searchParams.category === cat.slug ? 'bg-orange-50 text-orange-600 font-semibold' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {cat.name}
                </Link>
              ))}
            </nav>
          </aside>

          <div className="flex-1 min-w-0">
            <div className="md:hidden overflow-x-auto -mx-4 px-4 mb-4">
              <div className="flex gap-2 pb-2 w-max">
                <Link
                  href="/products"
                  className={`shrink-0 px-4 py-2 rounded-full text-sm font-['Jost'] transition-colors min-h-[44px] flex items-center ${
                    !searchParams.category ? 'bg-orange-500 text-white font-medium' : 'bg-white text-slate-600 border border-slate-200'
                  }`}
                >
                  All
                </Link>
                {categories.map((cat) => (
                  <Link
                    key={cat.id}
                    href={`/products?category=${cat.slug}`}
                    className={`shrink-0 px-4 py-2 rounded-full text-sm font-['Jost'] transition-colors min-h-[44px] flex items-center ${
                      searchParams.category === cat.slug ? 'bg-orange-500 text-white font-medium' : 'bg-white text-slate-600 border border-slate-200'
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

Note: The `<select>` onChange for sort needs a SortSelector client component for full reactivity. For now, sort is applied only if the URL is navigated with `?sort=`. Add `SortSelector` as a follow-up if needed.

- [ ] **Step 3: Verify frontend compiles**

```bash
docker-compose logs frontend --tail=20
```

---

### Task 3: Phase 7 — Cart App (Backend)

**Files:**
- Create: `backend/apps/cart/__init__.py`, `apps.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`
- Create: `backend/apps/cart/migrations/__init__.py`
- Modify: `backend/config/settings/base.py` — add `apps.cart`
- Modify: `backend/config/urls.py` — add cart urls
- Create: `backend/tests/cart/__init__.py`, `test_models.py`, `test_api.py`

**Interfaces:**
- Produces: `Cart(TenantModel)` — `user(FK→User unique_together with tenant)`, `created_at`
- Produces: `CartItem(models.Model)` — `cart(FK→Cart)`, `variant(FK→ProductVariant)`, `qty(int)`, unique_together `(cart, variant)`; property `subtotal` = `variant.effective_price * qty`
- Produces: `GET /api/v1/cart/` — returns cart with nested items; creates cart if not exists
- Produces: `POST /api/v1/cart/items/` — add/update item; if variant already in cart, add qty
- Produces: `PATCH /api/v1/cart/items/{id}/` — update qty (qty=0 removes)
- Produces: `DELETE /api/v1/cart/items/{id}/` — remove item
- All cart endpoints require authentication (IsAuthenticated)

- [ ] **Step 1: Write failing model tests**

```python
# backend/tests/cart/__init__.py
```

```python
# backend/tests/cart/test_models.py
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
docker-compose exec backend pytest tests/cart/test_models.py -v
```

- [ ] **Step 3: Create cart app**

```python
# backend/apps/cart/__init__.py
```

```python
# backend/apps/cart/apps.py
from django.apps import AppConfig

class CartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cart'
```

```python
# backend/apps/cart/models.py
from decimal import Decimal
from django.db import models
from apps.tenants.models import TenantModel


class Cart(TenantModel):
    user = models.ForeignKey(
        'authentication.User', on_delete=models.CASCADE, related_name='carts'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'user')

    def __str__(self):
        return f"Cart({self.user}, {self.tenant})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(
        'catalog.ProductVariant', on_delete=models.CASCADE, related_name='cart_items'
    )
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'variant')

    @property
    def subtotal(self) -> Decimal:
        return self.variant.effective_price * self.qty

    def __str__(self):
        return f"{self.variant} x{self.qty}"
```

```python
# backend/apps/cart/admin.py
from django.contrib import admin
from .models import Cart, CartItem

admin.site.register(Cart)
admin.site.register(CartItem)
```

- [ ] **Step 4: Add to INSTALLED_APPS and migrate**

In `backend/config/settings/base.py`, add `'apps.cart'` to `LOCAL_APPS`.

```bash
docker-compose exec backend python manage.py makemigrations cart
docker-compose exec backend python manage.py migrate
```

- [ ] **Step 5: Run model tests**

```bash
docker-compose exec backend pytest tests/cart/test_models.py -v
```
Expected: 3 tests PASS

- [ ] **Step 6: Write failing API tests**

```python
# backend/tests/cart/test_api.py
import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.cart.models import Cart, CartItem


@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='8000000002')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


def _jwt(user, store):
    from apps.authentication.tokens import TenantRefreshToken
    return str(TenantRefreshToken.for_user_and_store(user, store).access_token)


@pytest.fixture
def auth_client(user, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(user, store)}')
    return c


@pytest.mark.django_db
def test_get_cart_creates_if_missing(auth_client, store, user):
    res = auth_client.get('/api/v1/cart/')
    assert res.status_code == 200
    assert Cart.objects.filter(user=user, tenant=store).exists()


@pytest.mark.django_db
def test_add_item_to_cart(auth_client, variant):
    res = auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 2}, format='json')
    assert res.status_code == 201
    assert CartItem.objects.filter(variant=variant).exists()


@pytest.mark.django_db
def test_add_same_variant_increases_qty(auth_client, variant):
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 2}, format='json')
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 3}, format='json')
    item = CartItem.objects.get(variant=variant)
    assert item.qty == 5


@pytest.mark.django_db
def test_update_cart_item_qty(auth_client, variant):
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 2}, format='json')
    item = CartItem.objects.get(variant=variant)
    res = auth_client.patch(f'/api/v1/cart/items/{item.id}/', {'qty': 10}, format='json')
    assert res.status_code == 200
    item.refresh_from_db()
    assert item.qty == 10


@pytest.mark.django_db
def test_delete_cart_item(auth_client, variant):
    auth_client.post('/api/v1/cart/items/', {'variant': variant.id, 'qty': 1}, format='json')
    item = CartItem.objects.get(variant=variant)
    res = auth_client.delete(f'/api/v1/cart/items/{item.id}/')
    assert res.status_code == 204


@pytest.mark.django_db
def test_cart_requires_auth(variant):
    res = APIClient().get('/api/v1/cart/')
    assert res.status_code == 401
```

- [ ] **Step 7: Write cart serializers**

```python
# backend/apps/cart/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    product_slug = serializers.CharField(source='variant.product.slug', read_only=True)
    price = serializers.DecimalField(source='variant.effective_price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'variant_name', 'product_name', 'product_slug', 'qty', 'price', 'subtotal']
        read_only_fields = ['id', 'variant_name', 'product_name', 'product_slug', 'price', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total']
        read_only_fields = ['id']

    def get_total(self, obj):
        return sum(item.subtotal for item in obj.items.all())
```

- [ ] **Step 8: Write cart views**

```python
# backend/apps/cart/views.py
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView, DestroyAPIView
from django.shortcuts import get_object_or_404
from apps.catalog.views import get_store_for_request
from apps.catalog.models import ProductVariant
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store = get_store_for_request(request)
        cart, _ = Cart.objects.get_or_create(
            user=request.user, tenant=store,
        )
        return Response(CartSerializer(cart).data)


class CartItemAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        store = get_store_for_request(request)
        variant_id = request.data.get('variant')
        qty = int(request.data.get('qty', 1))
        variant = get_object_or_404(ProductVariant, pk=variant_id, product__tenant=store)
        cart, _ = Cart.objects.get_or_create(user=request.user, tenant=store)
        item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={'qty': 0})
        item.qty += qty
        item.save()
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartItemUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        store = get_store_for_request(self.request)
        return CartItem.objects.filter(cart__user=self.request.user, cart__tenant=store)


class CartItemDeleteView(DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        store = get_store_for_request(self.request)
        return CartItem.objects.filter(cart__user=self.request.user, cart__tenant=store)
```

- [ ] **Step 9: Create cart URLs**

```python
# backend/apps/cart/urls.py
from django.urls import path
from .views import CartView, CartItemAddView, CartItemUpdateView, CartItemDeleteView

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/', CartItemAddView.as_view(), name='cart-item-add'),
    path('cart/items/<int:pk>/', CartItemUpdateView.as_view(), name='cart-item-update'),
    path('cart/items/<int:pk>/delete/', CartItemDeleteView.as_view(), name='cart-item-delete'),
]
```

Add to `backend/config/urls.py`:
```python
path('api/v1/', include('apps.cart.urls')),
```

- [ ] **Step 10: Run API tests**

```bash
docker-compose exec backend pytest tests/cart/test_api.py -v
```
Expected: 6 tests PASS

---

### Task 4: Phase 7 — Cart Frontend

**Files:**
- Create: `frontend/store/cart.ts`
- Create: `frontend/components/cart/CartDrawer.tsx`
- Create: `frontend/components/cart/CartItemRow.tsx`
- Modify: `frontend/components/product/VariantSelector.tsx` — wire "Add to Cart"
- Create: `frontend/app/(store)/cart/page.tsx`

**Interfaces:**
- Cart Zustand store: `items`, `total`, `fetchCart()`, `addItem(variantId, qty)`, `removeItem(itemId)`, `updateQty(itemId, qty)`
- `CartDrawer` — slide-in from right; shows items, subtotals, total, checkout CTA
- Product detail "Add to Cart" button calls `addItem` and opens drawer

- [ ] **Step 1: Create cart Zustand store**

```typescript
// frontend/store/cart.ts
'use client';
import { create } from 'zustand';
import { apiFetch } from '@/lib/api';

export interface CartItem {
  id: number;
  variant: number;
  variant_name: string;
  product_name: string;
  product_slug: string;
  qty: number;
  price: string;
  subtotal: string;
}

interface CartState {
  items: CartItem[];
  total: string;
  open: boolean;
  loading: boolean;
  setOpen: (open: boolean) => void;
  fetchCart: () => Promise<void>;
  addItem: (variantId: number, qty?: number) => Promise<void>;
  updateQty: (itemId: number, qty: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  total: '0',
  open: false,
  loading: false,

  setOpen: (open) => set({ open }),

  fetchCart: async () => {
    try {
      const data = await apiFetch<{ items: CartItem[]; total: string }>('/api/v1/cart/');
      set({ items: data.items, total: data.total });
    } catch {
      // not authenticated — clear cart
      set({ items: [], total: '0' });
    }
  },

  addItem: async (variantId, qty = 1) => {
    await apiFetch('/api/v1/cart/items/', {
      method: 'POST',
      body: JSON.stringify({ variant: variantId, qty }),
    });
    await get().fetchCart();
    set({ open: true });
  },

  updateQty: async (itemId, qty) => {
    await apiFetch(`/api/v1/cart/items/${itemId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ qty }),
    });
    await get().fetchCart();
  },

  removeItem: async (itemId) => {
    await apiFetch(`/api/v1/cart/items/${itemId}/delete/`, { method: 'DELETE' });
    await get().fetchCart();
  },
}));
```

- [ ] **Step 2: Create CartItemRow**

```tsx
// frontend/components/cart/CartItemRow.tsx
'use client';
import Link from 'next/link';
import { useCartStore, CartItem } from '@/store/cart';

export default function CartItemRow({ item }: { item: CartItem }) {
  const { updateQty, removeItem } = useCartStore();

  return (
    <div className="flex items-center gap-3 py-3 border-b border-slate-100 last:border-0">
      <div className="flex-1 min-w-0">
        <Link href={`/products/${item.product_slug}`} className="text-sm font-medium text-slate-900 font-['Jost'] hover:text-orange-500 transition-colors line-clamp-1">
          {item.product_name}
        </Link>
        <p className="text-xs text-slate-400 font-['Jost']">{item.variant_name}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => item.qty > 1 ? updateQty(item.id, item.qty - 1) : removeItem(item.id)}
          className="w-7 h-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:border-orange-300 hover:text-orange-500 transition-colors text-sm cursor-pointer"
        >
          −
        </button>
        <span className="w-6 text-center text-sm font-medium text-slate-900 font-['Jost']">{item.qty}</span>
        <button
          onClick={() => updateQty(item.id, item.qty + 1)}
          className="w-7 h-7 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:border-orange-300 hover:text-orange-500 transition-colors text-sm cursor-pointer"
        >
          +
        </button>
      </div>
      <p className="text-sm font-semibold text-slate-900 font-['Jost'] w-16 text-right shrink-0">
        ₹{parseFloat(item.subtotal).toFixed(0)}
      </p>
    </div>
  );
}
```

- [ ] **Step 3: Create CartDrawer**

```tsx
// frontend/components/cart/CartDrawer.tsx
'use client';
import { useEffect } from 'react';
import Link from 'next/link';
import { useCartStore } from '@/store/cart';
import CartItemRow from './CartItemRow';
import { useAuthStore } from '@/store/auth';

export default function CartDrawer() {
  const { items, total, open, setOpen, fetchCart } = useCartStore();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) fetchCart();
  }, [isAuthenticated]);

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/30 z-40" onClick={() => setOpen(false)} />
      <div className="fixed right-0 top-0 h-full w-full max-w-sm bg-white z-50 shadow-xl flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 className="font-['Bodoni_Moda'] text-lg font-bold text-slate-900">Cart</h2>
          <button
            onClick={() => setOpen(false)}
            className="w-9 h-9 flex items-center justify-center rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-2">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3">
              <p className="text-slate-400 font-['Jost'] text-sm">Your cart is empty.</p>
              <button onClick={() => setOpen(false)} className="text-orange-500 font-medium font-['Jost'] text-sm hover:text-orange-600 transition-colors cursor-pointer">
                Browse Products →
              </button>
            </div>
          ) : (
            items.map((item) => <CartItemRow key={item.id} item={item} />)
          )}
        </div>

        {items.length > 0 && (
          <div className="px-5 py-4 border-t border-slate-100">
            <div className="flex justify-between mb-4">
              <span className="font-['Jost'] text-slate-600 text-sm">Total</span>
              <span className="font-['Jost'] font-bold text-slate-900">₹{parseFloat(total).toFixed(0)}</span>
            </div>
            <Link
              href="/checkout"
              onClick={() => setOpen(false)}
              className="block w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold py-4 rounded-xl font-['Jost'] text-base transition-colors text-center min-h-[52px] flex items-center justify-center"
            >
              Proceed to Checkout
            </Link>
          </div>
        )}
      </div>
    </>
  );
}
```

- [ ] **Step 4: Update VariantSelector to wire Add to Cart**

Replace the `onClick` handler in `frontend/components/product/VariantSelector.tsx`:

```tsx
// Add at the top of the file:
import { useCartStore } from '@/store/cart';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';

// Inside the component, replace the placeholder button:
const { addItem } = useCartStore();
const { isAuthenticated } = useAuthStore();
const router = useRouter();
const [adding, setAdding] = useState(false);

const handleAddToCart = async () => {
  if (!isAuthenticated) { router.push('/login'); return; }
  setAdding(true);
  try { await addItem(selected.id, 1); } finally { setAdding(false); }
};

// Replace button:
<button
  onClick={handleAddToCart}
  disabled={adding}
  className="w-full bg-orange-500 hover:bg-orange-600 active:bg-orange-700 disabled:bg-orange-300 text-white font-semibold py-4 rounded-xl font-['Jost'] text-base transition-colors cursor-pointer min-h-[52px]"
>
  {adding ? 'Adding...' : 'Add to Cart'}
</button>
```

- [ ] **Step 5: Add CartDrawer to root layout**

In `frontend/app/layout.tsx`, import and render `<CartDrawer />` inside the body.

- [ ] **Step 6: Verify cart flow**

```bash
docker-compose logs frontend --tail=20
```
Login → go to product detail → click "Add to Cart" → drawer slides in with item.

---

### Task 5: Phase 8 — Orders App + Address + Checkout (Backend)

**Files:**
- Create: `backend/apps/orders/` — full app (models, serializers, views, urls, admin, migrations)
- Create: `backend/apps/notifications/__init__.py`, `apps.py`, `services.py`
- Modify: `backend/config/settings/base.py`, `backend/config/urls.py`
- Create: `backend/tests/orders/__init__.py`, `test_models.py`, `test_api.py`

**Interfaces:**
- Produces: `Address(TenantModel)` — `user(FK)`, `line1`, `line2(blank)`, `city`, `state`, `pin_code(CharField 6)`, `lat(nullable)`, `lng(nullable)`, `is_default(bool)`
- Produces: `Order(TenantModel)` — `user(FK)`, `address(FK→Address)`, `status(CharField choices)`, `total_amount(Decimal)`, `notes(blank)`, `created_at`; statuses: `PLACED PENDING_CONFIRMATION CONFIRMED PROCESSING OUT_FOR_DELIVERY DELIVERED CANCELLED`
- Produces: `OrderItem(models.Model)` — `order(FK)`, `variant(FK→ProductVariant)`, `qty`, `unit_price(Decimal)`, `variant_name(CharField)` (snapshot)
- Produces: `GET/POST/PATCH/DELETE /api/v1/addresses/` — user's own addresses
- Produces: `POST /api/v1/orders/` — checkout: validates pin code, reserves inventory, creates Order + OrderItems, clears cart; fires `notify_order_placed`
- Produces: `GET /api/v1/orders/` — customer sees own; owner sees all
- Produces: `GET /api/v1/orders/{id}/`
- Produces: `PATCH /api/v1/orders/{id}/status/` — owner only; valid transitions enforced
- Produces: `send_whatsapp(phone, template, params)` in notifications/services.py — logs in dev, stubbed for prod

- [ ] **Step 1: Write failing model tests**

```python
# backend/tests/orders/__init__.py
```

```python
# backend/tests/orders/test_models.py
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
```

- [ ] **Step 2: Create the orders app**

```python
# backend/apps/orders/__init__.py
```

```python
# backend/apps/orders/apps.py
from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
```

```python
# backend/apps/orders/models.py
from django.db import models
from apps.tenants.models import TenantModel


class Address(TenantModel):
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='addresses')
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=6)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.line1}, {self.city} - {self.pin_code}"


class Order(TenantModel):
    PLACED = 'PLACED'
    PENDING_CONFIRMATION = 'PENDING_CONFIRMATION'
    CONFIRMED = 'CONFIRMED'
    PROCESSING = 'PROCESSING'
    OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (PLACED, 'Placed'),
        (PENDING_CONFIRMATION, 'Pending Confirmation'),
        (CONFIRMED, 'Confirmed'),
        (PROCESSING, 'Processing'),
        (OUT_FOR_DELIVERY, 'Out for Delivery'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]

    # ponytail: simple forward-only transitions; add full state machine if edge cases arise
    VALID_TRANSITIONS = {
        PLACED: [PENDING_CONFIRMATION, CANCELLED],
        PENDING_CONFIRMATION: [CONFIRMED, CANCELLED],
        CONFIRMED: [PROCESSING, CANCELLED],
        PROCESSING: [OUT_FOR_DELIVERY, CANCELLED],
        OUT_FOR_DELIVERY: [DELIVERED],
        DELIVERED: [],
        CANCELLED: [],
    }

    user = models.ForeignKey('authentication.User', on_delete=models.PROTECT, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=PLACED)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey('catalog.ProductVariant', on_delete=models.PROTECT, related_name='order_items')
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    variant_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.variant_name} x{self.qty}"
```

```python
# backend/apps/orders/admin.py
from django.contrib import admin
from .models import Address, Order, OrderItem

admin.site.register(Address)
admin.site.register(Order)
admin.site.register(OrderItem)
```

- [ ] **Step 3: Create notifications stub**

```python
# backend/apps/notifications/__init__.py
```

```python
# backend/apps/notifications/apps.py
from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
```

```python
# backend/apps/notifications/services.py
import logging

logger = logging.getLogger(__name__)


def send_whatsapp(phone: str, template: str, params: dict) -> None:
    # ponytail: dev stub — swap body to call Interakt/WATI/Gupshup when ready
    logger.info(f"[WhatsApp] TO:{phone} TEMPLATE:{template} PARAMS:{params}")
```

- [ ] **Step 4: Add to INSTALLED_APPS and migrate**

Add `'apps.orders'` and `'apps.notifications'` to `LOCAL_APPS`.

```bash
docker-compose exec backend python manage.py makemigrations orders
docker-compose exec backend python manage.py migrate
```

- [ ] **Step 5: Run model tests**

```bash
docker-compose exec backend pytest tests/orders/test_models.py -v
```
Expected: 4 tests PASS

- [ ] **Step 6: Write order API tests**

```python
# backend/tests/orders/test_api.py
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.orders.models import Order
from apps.tenants.models import Store


@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='7000000002')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


@pytest.fixture
def owner(store, db):
    u = User.objects.create(phone='7000000003', is_store_owner=True, is_staff=True)
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


def _jwt(user, store):
    from apps.authentication.tokens import TenantRefreshToken
    return str(TenantRefreshToken.for_user_and_store(user, store).access_token)


@pytest.fixture
def user_client(user, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(user, store)}')
    return c


@pytest.fixture
def owner_client(owner, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(owner, store)}')
    return c


@pytest.fixture
def delivery_store(db):
    """Store with 400001 in delivery_pin_codes."""
    return Store.objects.filter(is_active=True).first()


@pytest.mark.django_db
def test_create_address(user_client):
    res = user_client.post('/api/v1/addresses/', {
        'line1': '10 Park St', 'city': 'Mumbai', 'state': 'MH', 'pin_code': '400001'
    }, format='json')
    assert res.status_code == 201


@pytest.mark.django_db
def test_checkout_invalid_pin(user_client, store, variant):
    # Set store to not deliver to pin
    store.delivery_pin_codes = ['999999']
    store.save()
    from apps.orders.models import Address
    addr = Address.objects.create(
        tenant=store, user=user_client.handler._force_user if hasattr(user_client, 'handler') else None,
        line1='X', city='Y', state='Z', pin_code='400001'
    )
    # Use a fresh user lookup
    from apps.authentication.models import User
    u = User.objects.get(phone='7000000002')
    addr.user = u
    addr.save()
    res = user_client.post('/api/v1/orders/', {
        'address': addr.id,
        'items': [{'variant': variant.id, 'qty': 1}],
    }, format='json')
    assert res.status_code == 400
    assert 'pin' in str(res.json()).lower() or 'delivery' in str(res.json()).lower()


@pytest.mark.django_db
def test_checkout_success(user_client, store, variant):
    from apps.inventory.models import Inventory
    from apps.orders.models import Address
    from apps.authentication.models import User
    store.delivery_pin_codes = ['400001']
    store.save()
    Inventory.objects.create(tenant=store, variant=variant, available_qty=10, reserved_qty=0)
    u = User.objects.get(phone='7000000002')
    addr = Address.objects.create(
        tenant=store, user=u,
        line1='10 Park', city='Mumbai', state='MH', pin_code='400001'
    )
    from apps.cart.models import Cart, CartItem
    cart = Cart.objects.create(tenant=store, user=u)
    CartItem.objects.create(cart=cart, variant=variant, qty=2)

    res = user_client.post('/api/v1/orders/', {'address': addr.id}, format='json')
    assert res.status_code == 201
    assert Order.objects.filter(user=u).exists()


@pytest.mark.django_db
def test_list_orders_customer_sees_own(user_client, store, owner_client):
    res = user_client.get('/api/v1/orders/')
    assert res.status_code == 200


@pytest.mark.django_db
def test_owner_update_order_status(owner_client, store, variant):
    from apps.orders.models import Address, Order, OrderItem
    from apps.authentication.models import User
    u = User.objects.get(phone='7000000002')
    addr = Address.objects.create(
        tenant=store, user=u,
        line1='X', city='Y', state='Z', pin_code='400001'
    )
    order = Order.objects.create(
        tenant=store, user=u, address=addr,
        status=Order.PLACED, total_amount=Decimal('45')
    )
    res = owner_client.patch(
        f'/api/v1/orders/{order.id}/status/',
        {'status': Order.PENDING_CONFIRMATION},
        format='json'
    )
    assert res.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.PENDING_CONFIRMATION


@pytest.mark.django_db
def test_invalid_status_transition(owner_client, store, variant):
    from apps.orders.models import Address, Order
    from apps.authentication.models import User
    u = User.objects.get(phone='7000000002')
    addr = Address.objects.create(
        tenant=store, user=u,
        line1='X', city='Y', state='Z', pin_code='400001'
    )
    order = Order.objects.create(
        tenant=store, user=u, address=addr,
        status=Order.PLACED, total_amount=Decimal('0')
    )
    res = owner_client.patch(
        f'/api/v1/orders/{order.id}/status/',
        {'status': Order.DELIVERED},
        format='json'
    )
    assert res.status_code == 400
```

- [ ] **Step 7: Write order serializers**

```python
# backend/apps/orders/serializers.py
from rest_framework import serializers
from .models import Address, Order, OrderItem


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'line1', 'line2', 'city', 'state', 'pin_code', 'lat', 'lng', 'is_default']
        read_only_fields = ['id']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'variant', 'variant_name', 'qty', 'unit_price']
        read_only_fields = ['id', 'variant_name', 'unit_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    address = AddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'notes', 'created_at', 'address', 'items']
        read_only_fields = ['id', 'status', 'total_amount', 'created_at']


class CheckoutSerializer(serializers.Serializer):
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
```

- [ ] **Step 8: Write order views**

```python
# backend/apps/orders/views.py
from decimal import Decimal
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.catalog.permissions import IsStoreOwner
from apps.catalog.views import get_store_for_request
from apps.cart.models import Cart, CartItem
from apps.inventory.models import Inventory
from apps.notifications.services import send_whatsapp
from .models import Address, Order, OrderItem
from .serializers import AddressSerializer, OrderSerializer, CheckoutSerializer, OrderStatusSerializer


class AddressListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        store = get_store_for_request(self.request)
        return Address.objects.filter(user=self.request.user, tenant=store)

    def perform_create(self, serializer):
        store = get_store_for_request(self.request)
        serializer.save(user=self.request.user, tenant=store)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        store = get_store_for_request(request)
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address = serializer.validated_data['address']
        if address.pin_code not in store.delivery_pin_codes:
            raise ValidationError({'detail': 'Delivery not available to this pin code.'})

        cart = get_object_or_404(Cart, user=request.user, tenant=store)
        items = list(CartItem.objects.filter(cart=cart).select_related('variant'))
        if not items:
            raise ValidationError({'detail': 'Cart is empty.'})

        total = Decimal('0')
        order_items = []
        for ci in items:
            variant = ci.variant
            inv, _ = Inventory.objects.get_or_create(
                variant=variant,
                defaults={'tenant': store, 'available_qty': 0, 'reserved_qty': 0}
            )
            if inv.available_qty < ci.qty:
                raise ValidationError({'detail': f'{variant.product.name} ({variant.name}) is out of stock.'})
            price = variant.effective_price
            total += price * ci.qty
            order_items.append((ci, variant, price))

        order = Order.objects.create(
            tenant=store, user=request.user, address=address,
            status=Order.PLACED, total_amount=total,
            notes=serializer.validated_data.get('notes', '')
        )

        for ci, variant, price in order_items:
            OrderItem.objects.create(
                order=order, variant=variant, qty=ci.qty,
                unit_price=price, variant_name=variant.name
            )
            inv = Inventory.objects.get(variant=variant, tenant=store)
            inv.adjust(delta=-ci.qty, reason='RESERVE')

        cart.items.all().delete()

        send_whatsapp(
            request.user.phone, 'order_placed',
            {'order_id': order.id, 'total': str(total)}
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store = get_store_for_request(request)
        if request.auth and request.auth.get('is_store_owner'):
            orders = Order.objects.filter(tenant=store).prefetch_related('items')
        else:
            orders = Order.objects.filter(tenant=store, user=request.user).prefetch_related('items')
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        store = get_store_for_request(self.request)
        if self.request.auth and self.request.auth.get('is_store_owner'):
            return Order.objects.filter(tenant=store)
        return Order.objects.filter(tenant=store, user=self.request.user)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsStoreOwner]

    def patch(self, request, pk):
        if not (request.auth and request.auth.get('is_store_owner')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        store = get_store_for_request(request)
        order = get_object_or_404(Order, pk=pk, tenant=store)
        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        if new_status not in Order.VALID_TRANSITIONS.get(order.status, []):
            raise ValidationError({'detail': f'Cannot transition from {order.status} to {new_status}.'})
        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data)
```

- [ ] **Step 9: Create order URLs**

```python
# backend/apps/orders/urls.py
from django.urls import path
from .views import AddressListCreateView, CheckoutView, OrderListView, OrderDetailView, OrderStatusUpdateView

urlpatterns = [
    path('addresses/', AddressListCreateView.as_view(), name='addresses'),
    path('orders/', CheckoutView.as_view(), name='checkout'),
    path('orders/list/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status'),
]
```

Add to `backend/config/urls.py`:
```python
path('api/v1/', include('apps.orders.urls')),
```

- [ ] **Step 10: Run order tests**

```bash
docker-compose exec backend pytest tests/orders/ -v
```
Expected: 7+ tests PASS

---

### Task 6: Phase 8 — Checkout Frontend

**Files:**
- Create: `frontend/app/(store)/checkout/page.tsx`
- Create: `frontend/components/checkout/AddressForm.tsx`

**Interfaces:**
- Checkout page — `'use client'`; loads addresses via API; address select/create; "Place Order" calls `POST /api/v1/orders/`; on success redirects to `/orders/{id}`
- `AddressForm` — inline form to add a new address (line1, city, state, pin_code)

- [ ] **Step 1: Create AddressForm**

```tsx
// frontend/components/checkout/AddressForm.tsx
'use client';
import { useState } from 'react';
import { apiFetch } from '@/lib/api';

interface Address {
  id: number;
  line1: string;
  line2: string;
  city: string;
  state: string;
  pin_code: string;
  is_default: boolean;
}

interface Props {
  onSaved: (addr: Address) => void;
}

const INPUT = 'w-full border border-slate-200 rounded-xl px-4 py-3 text-slate-900 font-["Jost"] text-sm focus:outline-none focus:ring-2 focus:ring-orange-200 focus:border-orange-400 bg-white min-h-[48px]';

export default function AddressForm({ onSaved }: Props) {
  const [form, setForm] = useState({ line1: '', line2: '', city: '', state: '', pin_code: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const addr = await apiFetch<Address>('/api/v1/addresses/', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      onSaved(addr);
    } catch (err: unknown) {
      setError(typeof err === 'object' ? JSON.stringify(err) : 'Failed to save address');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <p className="text-red-500 text-sm font-['Jost']">{error}</p>}
      <input className={INPUT} placeholder="Address line 1 *" value={form.line1} onChange={e => setForm(f => ({...f, line1: e.target.value}))} required />
      <input className={INPUT} placeholder="Address line 2" value={form.line2} onChange={e => setForm(f => ({...f, line2: e.target.value}))} />
      <div className="grid grid-cols-2 gap-3">
        <input className={INPUT} placeholder="City *" value={form.city} onChange={e => setForm(f => ({...f, city: e.target.value}))} required />
        <input className={INPUT} placeholder="State *" value={form.state} onChange={e => setForm(f => ({...f, state: e.target.value}))} required />
      </div>
      <input className={INPUT} placeholder="PIN Code *" value={form.pin_code} onChange={e => setForm(f => ({...f, pin_code: e.target.value}))} maxLength={6} pattern="\d{6}" required />
      <button type="submit" disabled={saving} className="w-full bg-slate-900 hover:bg-slate-700 disabled:bg-slate-300 text-white font-semibold py-3 rounded-xl font-['Jost'] text-sm transition-colors cursor-pointer min-h-[48px]">
        {saving ? 'Saving...' : 'Save Address'}
      </button>
    </form>
  );
}
```

- [ ] **Step 2: Create checkout page**

```tsx
// frontend/app/(store)/checkout/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { useCartStore } from '@/store/cart';
import { useAuthStore } from '@/store/auth';
import AddressForm from '@/components/checkout/AddressForm';
import Link from 'next/link';

interface Address {
  id: number;
  line1: string;
  line2: string;
  city: string;
  state: string;
  pin_code: string;
  is_default: boolean;
}

export default function CheckoutPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { items, total, fetchCart } = useCartStore();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddr, setSelectedAddr] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) { router.replace('/login'); return; }
    fetchCart();
    apiFetch<Address[]>('/api/v1/addresses/').then(a => {
      setAddresses(a);
      const def = a.find(x => x.is_default) ?? a[0];
      if (def) setSelectedAddr(def.id);
    });
  }, [isAuthenticated]);

  const handlePlaceOrder = async () => {
    if (!selectedAddr) { setError('Please select a delivery address.'); return; }
    setPlacing(true);
    setError('');
    try {
      const order = await apiFetch<{ id: number }>('/api/v1/orders/', {
        method: 'POST',
        body: JSON.stringify({ address: selectedAddr }),
      });
      await fetchCart();
      router.push(`/orders/${order.id}`);
    } catch (err: unknown) {
      const msg = typeof err === 'object' && err !== null ? (err as Record<string, string>).detail ?? JSON.stringify(err) : 'Failed to place order';
      setError(msg);
    } finally {
      setPlacing(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-100">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
          <Link href="/cart" className="text-slate-500 hover:text-slate-700 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center -ml-2 cursor-pointer">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="font-['Bodoni_Moda'] text-xl font-bold text-slate-900">Checkout</h1>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {error && <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl px-4 py-3 text-sm font-['Jost']">{error}</div>}

        {/* Delivery address */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100">
          <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 mb-4">Delivery Address</h2>
          {addresses.map(addr => (
            <label key={addr.id} className="flex items-start gap-3 p-3 rounded-xl cursor-pointer hover:bg-slate-50 transition-colors mb-2">
              <input
                type="radio"
                name="address"
                value={addr.id}
                checked={selectedAddr === addr.id}
                onChange={() => setSelectedAddr(addr.id)}
                className="mt-1 accent-orange-500"
              />
              <div>
                <p className="text-sm font-medium text-slate-900 font-['Jost']">{addr.line1}{addr.line2 ? `, ${addr.line2}` : ''}</p>
                <p className="text-xs text-slate-500 font-['Jost']">{addr.city}, {addr.state} — {addr.pin_code}</p>
              </div>
            </label>
          ))}
          {showForm ? (
            <div className="mt-3">
              <AddressForm onSaved={addr => {
                setAddresses(a => [...a, addr]);
                setSelectedAddr(addr.id);
                setShowForm(false);
              }} />
            </div>
          ) : (
            <button onClick={() => setShowForm(true)} className="text-orange-500 text-sm font-medium font-['Jost'] hover:text-orange-600 transition-colors cursor-pointer mt-2 min-h-[44px] flex items-center">
              + Add new address
            </button>
          )}
        </div>

        {/* Order summary */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100">
          <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 mb-4">Order Summary</h2>
          {items.map(item => (
            <div key={item.id} className="flex justify-between py-1.5">
              <span className="text-sm text-slate-700 font-['Jost']">{item.product_name} ({item.variant_name}) ×{item.qty}</span>
              <span className="text-sm font-medium text-slate-900 font-['Jost']">₹{parseFloat(item.subtotal).toFixed(0)}</span>
            </div>
          ))}
          <div className="flex justify-between pt-3 mt-3 border-t border-slate-100">
            <span className="font-semibold text-slate-900 font-['Jost']">Total</span>
            <span className="font-bold text-slate-900 font-['Jost']">₹{parseFloat(total).toFixed(0)}</span>
          </div>
        </div>

        <button
          onClick={handlePlaceOrder}
          disabled={placing || items.length === 0}
          className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-orange-300 text-white font-semibold py-4 rounded-xl font-['Jost'] text-base transition-colors cursor-pointer min-h-[52px]"
        >
          {placing ? 'Placing Order...' : 'Place Order (COD)'}
        </button>
      </div>
    </div>
  );
}
```

---

### Task 7: Phase 9 — Orders Frontend

**Files:**
- Create: `frontend/app/(store)/orders/page.tsx`
- Create: `frontend/app/(store)/orders/[id]/page.tsx`
- Create: `frontend/app/admin/orders/page.tsx`

- [ ] **Step 1: Create customer orders list**

```tsx
// frontend/app/(store)/orders/page.tsx
'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'next/navigation';

interface Order {
  id: number;
  status: string;
  total_amount: string;
  created_at: string;
  items: { variant_name: string; qty: number }[];
}

const STATUS_COLOR: Record<string, string> = {
  PLACED: 'bg-blue-50 text-blue-700',
  PENDING_CONFIRMATION: 'bg-yellow-50 text-yellow-700',
  CONFIRMED: 'bg-green-50 text-green-700',
  PROCESSING: 'bg-orange-50 text-orange-700',
  OUT_FOR_DELIVERY: 'bg-purple-50 text-purple-700',
  DELIVERED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-50 text-red-700',
};

export default function OrdersPage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { router.replace('/login'); return; }
    apiFetch<Order[]>('/api/v1/orders/list/')
      .then(setOrders)
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-100 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
          <Link href="/" className="text-slate-500 hover:text-slate-700 min-h-[44px] min-w-[44px] flex items-center justify-center -ml-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="font-['Bodoni_Moda'] text-xl font-bold text-slate-900">My Orders</h1>
        </div>
      </header>
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-3">
        {loading && <p className="text-slate-400 font-['Jost'] text-sm text-center py-10">Loading...</p>}
        {!loading && orders.length === 0 && (
          <div className="bg-white rounded-2xl p-12 text-center border border-slate-100">
            <p className="text-slate-400 font-['Jost'] text-sm mb-4">No orders yet.</p>
            <Link href="/products" className="text-orange-500 font-medium font-['Jost'] text-sm hover:text-orange-600 transition-colors">Browse Products →</Link>
          </div>
        )}
        {orders.map(order => (
          <Link key={order.id} href={`/orders/${order.id}`} className="block bg-white rounded-2xl p-5 border border-slate-100 hover:shadow-sm transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-slate-900 font-['Jost']">Order #{order.id}</span>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium font-['Jost'] ${STATUS_COLOR[order.status] ?? 'bg-slate-100 text-slate-600'}`}>
                {order.status.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-['Jost'] mb-3">{new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
            <p className="text-xs text-slate-600 font-['Jost'] line-clamp-1">{order.items.map(i => `${i.variant_name} ×${i.qty}`).join(', ')}</p>
            <p className="text-base font-bold text-slate-900 font-['Jost'] mt-2">₹{parseFloat(order.total_amount).toFixed(0)}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create order detail page**

```tsx
// frontend/app/(store)/orders/[id]/page.tsx
'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { useRouter, useParams } from 'next/navigation';

interface OrderDetail {
  id: number;
  status: string;
  total_amount: string;
  notes: string;
  created_at: string;
  address: { line1: string; line2: string; city: string; state: string; pin_code: string };
  items: { id: number; variant_name: string; qty: number; unit_price: string }[];
}

const TIMELINE = ['PLACED', 'CONFIRMED', 'PROCESSING', 'OUT_FOR_DELIVERY', 'DELIVERED'];

export default function OrderDetailPage() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const [order, setOrder] = useState<OrderDetail | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { router.replace('/login'); return; }
    apiFetch<OrderDetail>(`/api/v1/orders/${params.id}/`).then(setOrder);
  }, [isAuthenticated, params.id]);

  if (!order) return <div className="min-h-screen bg-slate-50 flex items-center justify-center"><p className="text-slate-400 font-['Jost'] text-sm">Loading...</p></div>;

  const currentIdx = TIMELINE.indexOf(order.status);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-100">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
          <Link href="/orders" className="text-slate-500 hover:text-slate-700 min-h-[44px] min-w-[44px] flex items-center justify-center -ml-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="font-['Bodoni_Moda'] text-xl font-bold text-slate-900">Order #{order.id}</h1>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* Timeline */}
        {order.status !== 'CANCELLED' && (
          <div className="bg-white rounded-2xl p-5 border border-slate-100">
            <div className="flex items-center gap-0">
              {TIMELINE.map((s, i) => (
                <div key={s} className="flex items-center flex-1 last:flex-none">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold font-['Jost'] ${i <= currentIdx ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-400'}`}>
                    {i < currentIdx ? '✓' : i + 1}
                  </div>
                  {i < TIMELINE.length - 1 && (
                    <div className={`h-0.5 flex-1 ${i < currentIdx ? 'bg-orange-500' : 'bg-slate-100'}`} />
                  )}
                </div>
              ))}
            </div>
            <p className="text-center text-xs text-slate-500 font-['Jost'] mt-3">{order.status.replace(/_/g, ' ')}</p>
          </div>
        )}

        {/* Items */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100">
          <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 mb-4">Items</h2>
          {order.items.map(item => (
            <div key={item.id} className="flex justify-between py-2 border-b border-slate-50 last:border-0">
              <div>
                <p className="text-sm text-slate-900 font-['Jost']">{item.variant_name}</p>
                <p className="text-xs text-slate-400 font-['Jost']">×{item.qty} @ ₹{parseFloat(item.unit_price).toFixed(0)}</p>
              </div>
              <p className="text-sm font-semibold text-slate-900 font-['Jost']">₹{(parseFloat(item.unit_price) * item.qty).toFixed(0)}</p>
            </div>
          ))}
          <div className="flex justify-between pt-3 mt-2 border-t border-slate-100">
            <span className="font-semibold font-['Jost'] text-slate-900">Total</span>
            <span className="font-bold font-['Jost'] text-slate-900">₹{parseFloat(order.total_amount).toFixed(0)}</span>
          </div>
        </div>

        {/* Address */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100">
          <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 mb-2">Delivery Address</h2>
          <p className="text-sm text-slate-700 font-['Jost']">{order.address.line1}{order.address.line2 ? `, ${order.address.line2}` : ''}</p>
          <p className="text-sm text-slate-500 font-['Jost']">{order.address.city}, {order.address.state} — {order.address.pin_code}</p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create admin orders page**

```tsx
// frontend/app/admin/orders/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';

interface Order {
  id: number;
  status: string;
  total_amount: string;
  created_at: string;
  items: { variant_name: string; qty: number }[];
}

const STATUS_OPTIONS = ['PENDING_CONFIRMATION', 'CONFIRMED', 'PROCESSING', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'];

const STATUS_COLOR: Record<string, string> = {
  PLACED: 'bg-blue-50 text-blue-700',
  PENDING_CONFIRMATION: 'bg-yellow-50 text-yellow-700',
  CONFIRMED: 'bg-green-50 text-green-700',
  PROCESSING: 'bg-orange-50 text-orange-700',
  OUT_FOR_DELIVERY: 'bg-purple-50 text-purple-700',
  DELIVERED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-50 text-red-700',
};

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  const loadOrders = () => apiFetch<Order[]>('/api/v1/orders/list/').then(setOrders).finally(() => setLoading(false));

  useEffect(() => { loadOrders(); }, []);

  const updateStatus = async (id: number, status: string) => {
    try {
      await apiFetch(`/api/v1/orders/${id}/status/`, { method: 'PATCH', body: JSON.stringify({ status }) });
      await loadOrders();
    } catch (e) {
      alert('Invalid status transition');
    }
  };

  if (loading) return <p className="text-slate-400 font-['Jost'] text-sm">Loading...</p>;

  return (
    <div>
      <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900 mb-6">Orders</h1>
      {orders.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-100">
          <p className="text-slate-400 font-['Jost'] text-sm">No orders yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map(order => (
            <div key={order.id} className="bg-white rounded-2xl p-5 border border-slate-100">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-900 font-['Jost']">Order #{order.id}</span>
                <span className="font-bold text-slate-900 font-['Jost']">₹{parseFloat(order.total_amount).toFixed(0)}</span>
              </div>
              <p className="text-xs text-slate-400 font-['Jost'] mb-2">{new Date(order.created_at).toLocaleDateString('en-IN')}</p>
              <p className="text-xs text-slate-600 font-['Jost'] mb-3">{order.items.map(i => `${i.variant_name} ×${i.qty}`).join(', ')}</p>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium font-['Jost'] ${STATUS_COLOR[order.status] ?? ''}`}>
                  {order.status.replace(/_/g, ' ')}
                </span>
                <select
                  className="border border-slate-200 rounded-xl px-3 py-1.5 text-sm font-['Jost'] text-slate-700 bg-white focus:outline-none cursor-pointer min-h-[36px]"
                  defaultValue=""
                  onChange={e => { if (e.target.value) updateStatus(order.id, e.target.value); e.target.value = ''; }}
                >
                  <option value="">Update status...</option>
                  {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

Add `Orders` link to admin layout nav:
```tsx
<Link href="/admin/orders" className="text-sm text-slate-600 hover:text-orange-500 font-['Jost'] transition-colors min-h-[44px] flex items-center">
  Orders
</Link>
```

---

### Task 8: Phase 10 — Payments (Backend)

**Files:**
- Create: `backend/apps/payments/` — full app
- Modify: `backend/config/settings/base.py`, `backend/config/urls.py`
- Create: `backend/tests/payments/__init__.py`, `test_api.py`

**Interfaces:**
- Produces: `Payment(models.Model)` — `order(OneToOneField→Order)`, `method(COD|RAZORPAY)`, `status(PENDING|COMPLETED|FAILED|REFUNDED)`, `gateway_ref(blank)`, `amount`
- Produces: `POST /api/v1/payments/initiate/` — creates Payment record; for COD sets status=PENDING; for RAZORPAY creates Razorpay order via SDK, returns `razorpay_order_id`
- Produces: `POST /api/v1/payments/cod/confirm/` — owner only; sets payment status=COMPLETED, order status=DELIVERED
- Produces: `POST /api/v1/payments/webhook/` — Razorpay webhook; verifies HMAC signature; sets payment status=COMPLETED, order status=CONFIRMED
- Razorpay SDK: `razorpay` package (add to requirements.txt); reads `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` from env

- [ ] **Step 1: Create payments app**

```python
# backend/apps/payments/__init__.py
```

```python
# backend/apps/payments/apps.py
from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
```

```python
# backend/apps/payments/models.py
from django.db import models


class Payment(models.Model):
    COD = 'COD'
    RAZORPAY = 'RAZORPAY'
    METHOD_CHOICES = [(COD, 'Cash on Delivery'), (RAZORPAY, 'Razorpay')]

    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'
    STATUS_CHOICES = [(PENDING, 'Pending'), (COMPLETED, 'Completed'), (FAILED, 'Failed'), (REFUNDED, 'Refunded')]

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    gateway_ref = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} ({self.method} / {self.status})"
```

```python
# backend/apps/payments/admin.py
from django.contrib import admin
from .models import Payment

admin.site.register(Payment)
```

- [ ] **Step 2: Add razorpay to requirements**

```bash
docker-compose exec backend pip install razorpay
```

Also add `razorpay` to `backend/requirements.txt`.

- [ ] **Step 3: Add to INSTALLED_APPS and migrate**

Add `'apps.payments'` to `LOCAL_APPS`.

```bash
docker-compose exec backend python manage.py makemigrations payments
docker-compose exec backend python manage.py migrate
```

- [ ] **Step 4: Write payment views**

```python
# backend/apps/payments/serializers.py
from rest_framework import serializers
from .models import Payment


class InitiatePaymentSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'method', 'status', 'gateway_ref', 'amount', 'created_at']
        read_only_fields = ['id', 'status', 'gateway_ref', 'amount', 'created_at']
```

```python
# backend/apps/payments/views.py
import hashlib
import hmac
import os
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.catalog.permissions import IsStoreOwner
from apps.catalog.views import get_store_for_request
from apps.orders.models import Order
from apps.notifications.services import send_whatsapp
from .models import Payment
from .serializers import InitiatePaymentSerializer, PaymentSerializer


class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = get_store_for_request(request)
        order = get_object_or_404(
            Order, pk=serializer.validated_data['order'],
            tenant=store, user=request.user
        )
        method = serializer.validated_data['method']

        if hasattr(order, 'payment'):
            return Response(PaymentSerializer(order.payment).data)

        payment = Payment.objects.create(
            order=order, method=method,
            status=Payment.PENDING, amount=order.total_amount
        )

        if method == Payment.RAZORPAY:
            import razorpay
            client = razorpay.Client(
                auth=(os.environ['RAZORPAY_KEY_ID'], os.environ['RAZORPAY_KEY_SECRET'])
            )
            rp_order = client.order.create({
                'amount': int(order.total_amount * 100),
                'currency': 'INR',
                'receipt': f'order_{order.id}',
            })
            payment.gateway_ref = rp_order['id']
            payment.save()
            return Response({
                'payment_id': payment.id,
                'razorpay_order_id': rp_order['id'],
                'key': os.environ['RAZORPAY_KEY_ID'],
                'amount': int(order.total_amount * 100),
            })

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class CODConfirmView(APIView):
    permission_classes = [IsStoreOwner]

    def post(self, request):
        if not (request.auth and request.auth.get('is_store_owner')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        order_id = request.data.get('order')
        store = get_store_for_request(request)
        order = get_object_or_404(Order, pk=order_id, tenant=store)
        payment = get_object_or_404(Payment, order=order, method=Payment.COD)
        payment.status = Payment.COMPLETED
        payment.save()
        order.status = Order.DELIVERED
        order.save()
        send_whatsapp(order.user.phone, 'order_delivered', {'order_id': order.id})
        return Response({'status': 'confirmed'})


class RazorpayWebhookView(APIView):
    def post(self, request):
        secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
        sig = request.headers.get('X-Razorpay-Signature', '')
        body = request.body
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return Response({'error': 'invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        payload = request.data
        event = payload.get('event')
        if event == 'payment.captured':
            rp_order_id = payload['payload']['payment']['entity']['order_id']
            payment = Payment.objects.filter(gateway_ref=rp_order_id).first()
            if payment:
                payment.status = Payment.COMPLETED
                payment.save()
                order = payment.order
                order.status = Order.CONFIRMED
                order.save()
                send_whatsapp(order.user.phone, 'order_confirmed', {'order_id': order.id})
        return Response({'status': 'ok'})
```

- [ ] **Step 5: Create payment URLs**

```python
# backend/apps/payments/urls.py
from django.urls import path
from .views import InitiatePaymentView, CODConfirmView, RazorpayWebhookView

urlpatterns = [
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('payments/cod/confirm/', CODConfirmView.as_view(), name='cod-confirm'),
    path('payments/webhook/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
]
```

Add to `backend/config/urls.py`:
```python
path('api/v1/', include('apps.payments.urls')),
```

- [ ] **Step 6: Write basic payment tests**

```python
# backend/tests/payments/__init__.py
```

```python
# backend/tests/payments/test_api.py
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from apps.authentication.models import User, CustomerProfile
from apps.orders.models import Address, Order
from apps.payments.models import Payment


@pytest.fixture
def user(store, db):
    u = User.objects.create(phone='6000000001')
    CustomerProfile.objects.create(user=u, tenant=store)
    return u


@pytest.fixture
def owner(store, db):
    u = User.objects.create(phone='6000000002', is_store_owner=True, is_staff=True)
    CustomerProfile.objects.create(u, tenant=store)
    return u


def _jwt(user, store):
    from apps.authentication.tokens import TenantRefreshToken
    return str(TenantRefreshToken.for_user_and_store(user, store).access_token)


@pytest.fixture
def user_client(user, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(user, store)}')
    return c


@pytest.fixture
def owner_client(owner, store):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {_jwt(owner, store)}')
    return c


@pytest.fixture
def order(store, user):
    addr = Address.objects.create(
        tenant=store, user=user, line1='X', city='Y', state='Z', pin_code='400001'
    )
    return Order.objects.create(
        tenant=store, user=user, address=addr,
        status=Order.PLACED, total_amount=Decimal('100')
    )


@pytest.mark.django_db
def test_initiate_cod_payment(user_client, order):
    res = user_client.post('/api/v1/payments/initiate/', {'order': order.id, 'method': 'COD'}, format='json')
    assert res.status_code == 201
    assert Payment.objects.filter(order=order, method='COD').exists()


@pytest.mark.django_db
def test_initiate_payment_idempotent(user_client, order):
    user_client.post('/api/v1/payments/initiate/', {'order': order.id, 'method': 'COD'}, format='json')
    res = user_client.post('/api/v1/payments/initiate/', {'order': order.id, 'method': 'COD'}, format='json')
    assert res.status_code == 200
    assert Payment.objects.filter(order=order).count() == 1
```

```bash
docker-compose exec backend pytest tests/payments/test_api.py -v
```
Expected: 2 tests PASS

---

### Task 9: Phase 10 — Payment Selector Frontend

**Files:**
- Modify: `frontend/app/(store)/checkout/page.tsx` — add payment method selector before Place Order button

- [ ] **Step 1: Add payment method state + selector to checkout page**

Add `paymentMethod` state (`'COD' | 'RAZORPAY'`) to checkout page. Render two radio cards between the address section and the Place Order button:

```tsx
// Add near other useState calls:
const [paymentMethod, setPaymentMethod] = useState<'COD' | 'RAZORPAY'>('COD');

// Add between address block and Place Order button:
<div className="bg-white rounded-2xl p-5 border border-slate-100">
  <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 mb-4">Payment Method</h2>
  {(['COD', 'RAZORPAY'] as const).map(method => (
    <label key={method} className="flex items-center gap-3 p-3 rounded-xl cursor-pointer hover:bg-slate-50 transition-colors mb-2">
      <input
        type="radio"
        name="payment"
        value={method}
        checked={paymentMethod === method}
        onChange={() => setPaymentMethod(method)}
        className="accent-orange-500"
      />
      <div>
        <p className="text-sm font-medium text-slate-900 font-['Jost']">
          {method === 'COD' ? 'Cash on Delivery' : 'Pay Online (UPI / Card)'}
        </p>
        <p className="text-xs text-slate-400 font-['Jost']">
          {method === 'COD' ? 'Pay when your order arrives' : 'Secure payment via Razorpay'}
        </p>
      </div>
    </label>
  ))}
</div>
```

Update `handlePlaceOrder` to call `POST /api/v1/payments/initiate/` after order creation:

```tsx
const order = await apiFetch<{ id: number }>('/api/v1/orders/', {
  method: 'POST',
  body: JSON.stringify({ address: selectedAddr }),
});
await apiFetch('/api/v1/payments/initiate/', {
  method: 'POST',
  body: JSON.stringify({ order: order.id, method: paymentMethod }),
});
await fetchCart();
router.push(`/orders/${order.id}`);
```

---

### Task 10: Add Missing Nav Links + Final Wiring

**Files:**
- Modify: `frontend/app/(store)/products/page.tsx` — add cart icon in header
- Modify: `frontend/app/(store)/page.tsx` — add orders + cart links
- Modify: `frontend/app/admin/layout.tsx` — add Inventory link

- [ ] **Step 1: Add cart icon to storefront header**

In `frontend/app/(store)/products/page.tsx` and `frontend/app/(store)/products/[slug]/page.tsx`, add cart icon button in the header that calls `useCartStore().setOpen(true)`.

Since these are server components, move the header cart button to a shared `'use client'` component:

```tsx
// frontend/components/layout/CartButton.tsx
'use client';
import { useCartStore } from '@/store/cart';

export default function CartButton() {
  const { setOpen, items } = useCartStore();
  return (
    <button
      onClick={() => setOpen(true)}
      className="relative text-slate-600 hover:text-orange-500 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
    >
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13l-1.5 7H19M7 13h10m-5 7a1 1 0 100-2 1 1 0 000 2zm-5 0a1 1 0 100-2 1 1 0 000 2z" />
      </svg>
      {items.length > 0 && (
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-orange-500 text-white text-xs rounded-full flex items-center justify-center font-['Jost'] font-bold">
          {items.length}
        </span>
      )}
    </button>
  );
}
```

Import `CartButton` in headers of product pages alongside the Login link.

- [ ] **Step 2: Update home page links**

```tsx
// frontend/app/(store)/page.tsx
import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-slate-50 gap-8 px-4">
      <div className="text-center">
        <h1 className="font-['Bodoni_Moda'] text-4xl font-bold text-slate-900 mb-2">Hardware Store</h1>
        <p className="text-slate-500 font-['Jost']">Quality hardware & sanitary delivered to your door</p>
      </div>
      <div className="flex flex-col gap-3 w-full max-w-xs">
        <Link href="/products" className="bg-orange-500 text-white px-8 py-4 rounded-xl font-['Jost'] font-semibold text-lg hover:bg-orange-600 transition-colors min-h-[52px] flex items-center justify-center">
          Browse Products
        </Link>
        <Link href="/orders" className="bg-white border border-slate-200 text-slate-700 px-8 py-4 rounded-xl font-['Jost'] font-semibold hover:bg-slate-50 transition-colors min-h-[52px] flex items-center justify-center">
          My Orders
        </Link>
        <Link href="/login" className="text-slate-500 font-['Jost'] text-sm text-center hover:text-orange-500 transition-colors min-h-[44px] flex items-center justify-center">
          Login / Sign up
        </Link>
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Add Inventory link to admin layout**

In `frontend/app/admin/layout.tsx`, add:
```tsx
<Link href="/admin/inventory" className="text-sm text-slate-600 hover:text-orange-500 font-['Jost'] transition-colors min-h-[44px] flex items-center">
  Inventory
</Link>
```

- [ ] **Step 4: Create admin inventory page**

```tsx
// frontend/app/admin/inventory/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';

interface InventoryItem {
  id: number;
  variant: number;
  variant_name: string;
  product_name: string;
  sku: string;
  available_qty: number;
  reserved_qty: number;
}

export default function AdminInventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [adjusting, setAdjusting] = useState<Record<number, string>>({});

  const load = () => apiFetch<InventoryItem[]>('/api/v1/inventory/').then(setItems).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const adjust = async (variantId: number, delta: number) => {
    await apiFetch(`/api/v1/inventory/${variantId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ delta, reason: 'ADJUSTMENT' }),
    });
    await load();
  };

  if (loading) return <p className="text-slate-400 font-['Jost'] text-sm">Loading...</p>;

  return (
    <div>
      <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900 mb-6">Inventory</h1>
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-slate-100">
                {['Product', 'Variant / SKU', 'Available', 'Reserved', 'Adjust'].map(h => (
                  <th key={h} className="text-left px-5 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost']">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {items.map(item => (
                <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-4 text-sm font-medium text-slate-900 font-['Jost']">{item.product_name}</td>
                  <td className="px-5 py-4">
                    <p className="text-sm text-slate-700 font-['Jost']">{item.variant_name}</p>
                    <p className="text-xs text-slate-400 font-['Jost']">{item.sku}</p>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`text-sm font-semibold font-['Jost'] ${item.available_qty > 0 ? 'text-green-700' : 'text-red-500'}`}>
                      {item.available_qty}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-500 font-['Jost']">{item.reserved_qty}</td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        placeholder="±qty"
                        className="w-20 border border-slate-200 rounded-xl px-3 py-1.5 text-sm font-['Jost'] text-slate-900 focus:outline-none focus:ring-2 focus:ring-orange-200 min-h-[36px]"
                        id={`adj-${item.variant}`}
                      />
                      <button
                        onClick={() => {
                          const input = document.getElementById(`adj-${item.variant}`) as HTMLInputElement;
                          const delta = parseInt(input.value);
                          if (!isNaN(delta) && delta !== 0) { adjust(item.variant, delta); input.value = ''; }
                        }}
                        className="bg-slate-900 hover:bg-slate-700 text-white text-xs font-semibold px-3 py-1.5 rounded-xl font-['Jost'] transition-colors cursor-pointer min-h-[36px]"
                      >
                        Apply
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Full test suite**

```bash
docker-compose exec backend pytest tests/ -v
```

- [ ] **Step 6: Verify frontend end-to-end**

1. Login as customer → Browse products → Add to Cart → Cart drawer opens
2. Checkout → Select/add address → Place Order (COD) → Redirect to order detail with timeline
3. Go to `/orders` → see order list
4. Login as owner → `/admin/orders` → update order status
5. `/admin/inventory` → adjust stock

---

## Update CLAUDE.md after completion

When all tasks are done, update CLAUDE.md:

```markdown
## Current Plan
Plan 3 complete (all 10 tasks done).
Next: Production hardening — rate limits, error monitoring (Sentry), image uploads (R2), WhatsApp provider integration.
```

Update phase table:

| Phase | Description | Status |
|-------|-------------|--------|
| 6 | Product discovery | ✅ Complete |
| 7 | Cart | ✅ Complete |
| 8 | Checkout | ✅ Complete |
| 9 | Order management | ✅ Complete |
| 10 | Payments | ✅ Complete |
