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

