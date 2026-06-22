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

