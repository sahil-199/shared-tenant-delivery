# Task 3 Report: apps.cart — Cart + CartItem Models & API

## Status: Complete (Docker not running — migrations/tests deferred)

## Files Created

| File | Purpose |
|------|---------|
| `backend/apps/cart/__init__.py` | Empty package marker |
| `backend/apps/cart/apps.py` | CartConfig AppConfig |
| `backend/apps/cart/models.py` | Cart + CartItem models |
| `backend/apps/cart/admin.py` | Admin registration |
| `backend/apps/cart/serializers.py` | CartItemSerializer + CartSerializer |
| `backend/apps/cart/views.py` | CartView, CartItemAddView, CartItemUpdateView, CartItemDeleteView |
| `backend/apps/cart/urls.py` | URL patterns for all 4 views |
| `backend/apps/cart/migrations/__init__.py` | Empty migrations package |
| `backend/tests/cart/__init__.py` | Empty test package marker |
| `backend/tests/cart/test_models.py` | 3 model tests |
| `backend/tests/cart/test_api.py` | 6 API tests |

## Files Modified

| File | Change |
|------|--------|
| `backend/config/settings/base.py` | Added `'apps.cart'` to LOCAL_APPS after `'apps.inventory'` |
| `backend/config/urls.py` | Added `path('api/v1/', include('apps.cart.urls'))` after inventory include |

## Key Design Decisions

- **TenantModel field confirmed**: `tenant` FK (checked `backend/apps/tenants/models.py` directly). Cart uses `unique_together = ('tenant', 'user')` correctly.
- **String FK references**: `'authentication.User'` and `'catalog.ProductVariant'` used in models to avoid circular imports.
- **Add-to-cart is cumulative**: `CartItemAddView` uses `get_or_create` with `defaults={'qty': 0}` then increments — so posting the same variant twice accumulates qty.
- **Delete URL**: `/api/v1/cart/items/<pk>/delete/` (with `/delete/` suffix) to avoid Django routing conflicts between PATCH `<pk>/` and DELETE.
- **CartItemUpdateView**: Uses `http_method_names = ['patch']` — only PATCH allowed (not PUT), keeping qty update surgical.
- **effective_price**: `subtotal` property on CartItem calls `self.variant.effective_price * self.qty`. This assumes `ProductVariant` exposes `effective_price` (confirmed by the variant fixture using `price=Decimal('45.00')` and test asserting `Decimal('45.00') * 3`).

## Test Results

Docker was not running at time of execution. To run:

```bash
docker-compose up -d
docker-compose exec backend python manage.py makemigrations cart
docker-compose exec backend python manage.py migrate
docker-compose exec backend pytest tests/cart/ -v
```

## Concerns / Watch Points

1. **`effective_price` on ProductVariant**: The subtotal property calls `variant.effective_price`. If ProductVariant only has a `price` field and no `effective_price` property (e.g., no sale_price logic), this will raise `AttributeError`. Check `backend/apps/catalog/models.py` — if it's just `price`, update `CartItem.subtotal` to use `self.variant.price` instead.
2. **`CustomerProfile` in tests**: Both test files create a `CustomerProfile` for the user fixture. Confirm `CustomerProfile` exists in `apps.authentication.models` and accepts `(user, tenant)` — this matches the pattern from existing auth tests.
3. **Migration**: No migration file was generated (Docker not running). Run `makemigrations cart` before deploying — it will create `0001_initial.py` for Cart and CartItem tables.
