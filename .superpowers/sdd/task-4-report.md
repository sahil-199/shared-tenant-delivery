# Task 4 Report: Category & Brand APIs

## Status: COMPLETE

## Test Summary
8/8 tests pass (`tests/catalog/test_category_api.py` + `tests/catalog/test_brand_api.py`)

## Files Created
- `backend/apps/catalog/permissions.py` — `IsStoreOwner` permission
- `backend/apps/catalog/serializers.py` — all catalog serializers (Category, Brand, Product, variants, images)
- `backend/apps/catalog/views.py` — `CategoryViewSet`, `BrandViewSet`, `get_store_for_request()`
- `backend/apps/catalog/urls.py` — DRF router registration
- `backend/tests/catalog/test_category_api.py`
- `backend/tests/catalog/test_brand_api.py`

## Files Modified
- `backend/config/urls.py` — added `path('api/v1/', include('apps.catalog.urls'))`

## Concerns
1. **Coverage gate**: Overall project coverage is 69% (gate requires 80%). This is pre-existing — `apps/tenants/views.py` (44%), `apps/authentication/views.py` (31%), and `apps/tenants/management/commands/create_store.py` (0%) are the main offenders. Task 4 code itself has 91-100% coverage.

2. **IsStoreOwner raises PermissionDenied**: The spec says `return False` for unauthenticated unsafe requests, but DRF converts `False` to 401 (not 403) when no auth credentials are supplied. Changed to `raise PermissionDenied()` to force 403. This matches the test expectations and the spec's intent.

3. **`get_store_for_request` fallback**: When unauthenticated, it returns `Store.objects.filter(is_active=True).first()` — deterministic only if there's exactly one active store. Fine for current single-tenant-per-deployment usage; multi-store deployments will need host-based resolution later.
