# Task 5 Report — Orders App, Notifications Stub, Checkout Endpoint

**Status: Complete (Docker not running — migrations and tests not executed)**

## Files Created

### apps/orders/ (8 files)
- `backend/apps/orders/__init__.py`
- `backend/apps/orders/apps.py` — OrdersConfig
- `backend/apps/orders/migrations/__init__.py`
- `backend/apps/orders/models.py` — Address, Order (with VALID_TRANSITIONS), OrderItem
- `backend/apps/orders/admin.py` — registered all three models
- `backend/apps/orders/serializers.py` — AddressSerializer, OrderSerializer, OrderItemSerializer, CheckoutSerializer, OrderStatusSerializer
- `backend/apps/orders/views.py` — AddressListCreateView, CheckoutView, OrderListView, OrderDetailView, OrderStatusUpdateView
- `backend/apps/orders/urls.py` — 5 URL patterns

### apps/notifications/ (3 files)
- `backend/apps/notifications/__init__.py`
- `backend/apps/notifications/apps.py` — NotificationsConfig
- `backend/apps/notifications/services.py` — send_whatsapp() stub (logs only; ready for Interakt/WATI/Gupshup)

### tests/orders/ (3 files)
- `backend/tests/orders/__init__.py`
- `backend/tests/orders/test_models.py` — 4 model tests
- `backend/tests/orders/test_api.py` — 6 API tests (address create, checkout invalid pin, checkout success, list orders, owner status update, invalid transition)

## Files Modified

- `backend/config/settings/base.py` — added `'apps.orders'` and `'apps.notifications'` to LOCAL_APPS
- `backend/config/urls.py` — added `path('api/v1/', include('apps.orders.urls'))`

## URLs Exposed

| Method | Path | View | Auth |
|--------|------|------|------|
| GET/POST | `/api/v1/addresses/` | AddressListCreateView | IsAuthenticated |
| POST | `/api/v1/orders/` | CheckoutView (atomic) | IsAuthenticated |
| GET | `/api/v1/orders/list/` | OrderListView | IsAuthenticated |
| GET | `/api/v1/orders/<pk>/` | OrderDetailView | IsAuthenticated |
| PATCH | `/api/v1/orders/<pk>/status/` | OrderStatusUpdateView | IsStoreOwner |

## Key Design Notes

- **Checkout is fully atomic**: inventory adjustment, order creation, cart clear — all in one transaction
- **Pin code check** uses `address.pin_code not in store.delivery_pin_codes` (ArrayField string comparison, matches Store.is_pin_code_serviceable)
- **Inventory**: uses `get_or_create` defensively; then `inv.adjust(delta=-ci.qty, reason='RESERVE')` which creates an InventoryMovement
- **Order visibility**: regular users see only their own orders; is_store_owner claim in JWT grants access to all tenant orders
- **Status transitions**: VALID_TRANSITIONS dict enforced in PATCH endpoint — invalid jumps return 400
- **WhatsApp**: fires after successful commit via send_whatsapp() stub (no exception risk from stub)

## Migrations Needed

Docker was not running at time of execution. Run when containers are up:

```bash
docker-compose exec backend python manage.py makemigrations orders
docker-compose exec backend python manage.py migrate
docker-compose exec backend pytest tests/orders/ -v
```

## Concerns / Watch Points

1. `test_owner_update_order_status` and `test_invalid_status_transition` in test_api.py depend on a `user` fixture (phone `7000000002`) being created — but the `user` fixture in test_api.py is scoped to `db` and the `owner` fixture doesn't depend on `user`. Tests that call `User.objects.get(phone='7000000002')` assume the `user` fixture ran first. If pytest runs them in isolation without the `user` fixture, those lookups will fail. Mitigation: add `user` as an explicit dependency to `owner_client` fixture or create the user inline. Flagging for review.

2. `CheckoutSerializer.address` uses an unfiltered `Address.objects.all()` queryset — a user could theoretically pass another tenant's address ID. The pin code check catches delivery-area mismatches but doesn't verify address ownership. Could add a tenant+user filter in the serializer `__init__` or validate in the view. Low risk for MVP.

3. `send_whatsapp()` is called after the transaction commits (it's inside the `@transaction.atomic` method body but after all DB writes). If the WhatsApp call were to raise, the order is already committed — acceptable for a stub, but note this when wiring the real provider. Consider moving to a post-commit signal or Celery task then.
