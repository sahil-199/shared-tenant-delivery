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

