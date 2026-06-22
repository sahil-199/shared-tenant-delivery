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

