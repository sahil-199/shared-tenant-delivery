# Task 2: Product, ProductVariant, ProductImage Models — Implementation Report

**Date:** 2026-06-20  
**Status:** DONE

## Summary
All 11 tests pass (5 existing Category/Brand + 6 new Product tests). Product models fully implemented with migrations applied and fixtures ready for downstream tasks.

## Files Created/Modified

### Models
- **backend/apps/catalog/models.py**
  - Added `Product(TenantModel)` with category FK, brand FK, slug auto-generation, JSON specifications, is_active, created_at
  - Added `ProductVariant(models.Model)` with unique SKU (global), effective_price property, price/sale_price
  - Added `ProductImage(models.Model)` with nullable variant FK, sort_order

### Admin
- **backend/apps/catalog/admin.py**
  - Registered Product, ProductVariant, ProductImage

### Tests
- **backend/tests/catalog/test_models.py**
  - Updated import to include: `Product, ProductVariant, ProductImage, Decimal`
  - Added 6 new tests:
    - `test_product_creation` — creates product with category, brand, specs
    - `test_product_auto_slug` — verifies slug auto-generation from name
    - `test_variant_effective_price_with_sale` — sale_price takes precedence
    - `test_variant_effective_price_without_sale` — falls back to price
    - `test_variant_sku_uniqueness` — enforces unique SKU globally (IntegrityError on duplicate)
    - `test_product_image_variant_nullable` — variant FK is optional

### Fixtures
- **backend/tests/conftest.py**
  - Preserved existing `store(db)` fixture
  - Added `category(store)` fixture — creates 'Plumbing' category
  - Added `brand(store)` fixture — creates 'Supreme' brand
  - Added `product(store, category)` fixture — creates PVC Pipe with specs
  - Added `variant(product)` fixture — creates 2 inch variant with SKU 'PVC-PIPE-2IN', price 45.00

### Migrations
- **backend/apps/catalog/migrations/0002_product_productvariant_productimage.py**
  - Created and applied successfully

## Test Results

```bash
$ docker-compose exec backend pytest tests/catalog/test_models.py -v
```

**Output:**
```
tests/catalog/test_models.py::test_category_creation PASSED              [  9%]
tests/catalog/test_models.py::test_category_auto_slug PASSED             [ 18%]
tests/catalog/test_models.py::test_category_nesting PASSED               [ 27%]
tests/catalog/test_models.py::test_brand_creation PASSED                 [ 36%]
tests/catalog/test_models.py::test_category_tenant_isolation PASSED      [ 45%]
tests/catalog/test_models.py::test_product_creation PASSED               [ 54%]
tests/catalog/test_models.py::test_product_auto_slug PASSED              [ 63%]
tests/catalog/test_models.py::test_variant_effective_price_with_sale PASSED [ 72%]
tests/catalog/test_models.py::test_variant_effective_price_without_sale PASSED [ 81%]
tests/catalog/test_models.py::test_variant_sku_uniqueness PASSED         [ 90%]
tests/catalog/test_models.py::test_product_image_variant_nullable PASSED [100%]

============================== 11 passed in 0.62s ==============================
```

## Key Implementation Details

1. **Product extends TenantModel** — row-level tenant isolation via FK to Store
2. **ProductVariant is plain Model** — not tenant-scoped (as per spec)
3. **SKU is globally unique** — `unique=True` on CharField (not per-tenant)
4. **effective_price is @property** — not a database field; returns sale_price if set else price
5. **Slug auto-generation** — Product.save() calls slugify(name) if slug is blank
6. **Nullable brand** — Products can exist without a brand
7. **ProductImage.variant is nullable** — images can be product-level or variant-level
8. **Admin registration** — All three models registered for Django admin

## Self-Review Findings

✅ No issues identified:
- All model fields match specification
- Migrations created and applied cleanly
- Test coverage includes all business logic (auto-slug, effective_price, SKU uniqueness, nullable fields)
- Fixtures are properly parameterized and ready for Tasks 4–6
- No breaking changes to existing Category/Brand tests
- Database state is clean (11 tests isolated via `@pytest.mark.django_db`)

---

Task 2 complete. Fixtures ready for Task 4 (Product creation API) and downstream tasks.
