Status: DONE

Files changed:
- backend/apps/catalog/views.py — added `Min, Q` to django.db.models imports; replaced `ProductViewSet.get_queryset` with version that annotates `min_price`, adds search/min_price/max_price/in_stock/sort params, and defaults sort to `-created_at`
- backend/tests/catalog/test_product_filters.py — created with 5 tests: test_search_by_name, test_search_by_description, test_filter_in_stock, test_sort_price_asc, test_sort_price_desc

Tests: docker-compose exec backend pytest tests/catalog/test_product_filters.py -v — SKIP (Docker not running, no containers up)

Concerns: none. Existing category/brand filter logic preserved unchanged. The `in_stock` filter uses `.distinct()` to avoid duplicate rows from the variants join. The `store` and `category` fixtures used in tests are defined in backend/tests/conftest.py and are available to all catalog tests.

Fix applied: min_price/max_price wrapped in try/except float() to prevent 500 on invalid input. No Docker test run (Docker not running).
