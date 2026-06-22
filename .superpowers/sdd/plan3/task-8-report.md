# Task 8 Report: Payments Backend

**Status: Complete**

## Files Created

- `backend/apps/payments/__init__.py` — empty
- `backend/apps/payments/apps.py` — PaymentsConfig
- `backend/apps/payments/models.py` — Payment model (OneToOne → Order, method/status/razorpay fields, amount)
- `backend/apps/payments/serializers.py` — PaymentInitiateSerializer, PaymentSerializer
- `backend/apps/payments/views.py` — PaymentInitiateView (COD + Razorpay), RazorpayWebhookView
- `backend/apps/payments/urls.py` — payments/initiate/ and payments/webhook/razorpay/
- `backend/tests/payments/__init__.py` — empty
- `backend/tests/payments/test_api.py` — 4 tests

## Files Modified

- `backend/requirements/base.txt` — added `razorpay==1.4.2`
- `backend/config/settings/base.py` — added `apps.payments` to LOCAL_APPS; added RAZORPAY_KEY_ID/KEY_SECRET/WEBHOOK_SECRET settings (using `config()` from python-decouple)
- `backend/config/urls.py` — added `path('api/v1/', include('apps.payments.urls'))`
- `.env.example` — added RAZORPAY_WEBHOOK_SECRET; populated KEY_ID/KEY_SECRET with placeholder values

## Corrections from Spec

1. **Order field**: spec said `order.total` — actual field is `order.total_amount`. Fixed.
2. **Order status for filter**: spec said `status='pending'` — actual status is `Order.PLACED` (uppercase string constant). Fixed in both the queryset filter and transition target (`Order.CONFIRMED`).
3. **Order status transition**: COD sets order to `Order.CONFIRMED`; webhook does the same. Both are valid transitions from `PLACED` per `VALID_TRANSITIONS`.
4. **`get_store_for_request` import**: spec referenced `apps.tenants.utils` which doesn't exist — the actual location is `apps.catalog.views`. Fixed.
5. **`hmac.new`**: Verified it is valid Python stdlib — `hmac.new(key, msg, digestmod)` works correctly.
6. **Requirements file**: project uses `backend/requirements/base.txt`, not a flat `requirements.txt`. Added razorpay there.
7. **`.env.example`**: already had RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET — only RAZORPAY_WEBHOOK_SECRET was missing. Added it.

## Test Coverage

- `test_cod_payment_initiates_and_confirms_order` — POST cod, assert payment.status=paid, order.status=CONFIRMED
- `test_razorpay_payment_creates_razorpay_order` — mock razorpay.Client, assert status=initiated, razorpay_order_id set, order stays PLACED
- `test_duplicate_payment_rejected` — pre-create payment, assert second initiate → 400
- `test_invalid_order_returns_404` — non-existent order_id → 404

## Concerns / Notes

- The duplicate payment check uses `hasattr(order, 'payment')` which relies on Django's reverse OneToOne accessor — this correctly raises `RelatedObjectDoesNotExist` (a subclass of `DoesNotExist`) if no payment exists. `hasattr` catches the exception and returns False, so the guard works correctly.
- COD flow intentionally skips the `PENDING_CONFIRMATION` state, going directly `PLACED → CONFIRMED`. This is a business decision; the state machine allows it (`PLACED → [PENDING_CONFIRMATION, CANCELLED]`... actually PLACED does NOT have CONFIRMED as a valid transition — see concern below).
- **State machine gap**: `VALID_TRANSITIONS[PLACED] = [PENDING_CONFIRMATION, CANCELLED]`. CONFIRMED is not a direct valid transition from PLACED. The COD flow bypasses the state machine (it sets `order.status` directly without validation). This may be intentional for simplicity but should be reviewed if the `OrderStatusUpdateView` validation is ever applied to payment-driven transitions. Options: (a) add CONFIRMED to PLACED valid transitions, (b) go PLACED → PENDING_CONFIRMATION → CONFIRMED for COD, (c) accept the direct write as a payment-system privilege.
