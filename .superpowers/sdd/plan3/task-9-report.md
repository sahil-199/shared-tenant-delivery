# Task 9 Report: Payment Selector Frontend

**Status:** DONE

## Files Modified

- `frontend/app/(store)/checkout/page.tsx`

## What Was Done

1. **Added `PaymentMethod` type** (`'cod' | 'razorpay'`) and `PaymentInitiateResponse` interface for the `/api/v1/payments/initiate/` response shape.

2. **Added `paymentMethod` state** (defaults to `'cod'`).

3. **Loaded Razorpay checkout.js dynamically** via `useEffect` — appends `<script src="https://checkout.razorpay.com/v1/checkout.js">` to `document.body` on mount, removes it on unmount.

4. **Added payment method selector section** between Order Summary and the Place Order button. Two radio cards:
   - "Cash on Delivery" — "Pay when your order arrives"
   - "Pay Online" — "Credit/debit card, UPI, netbanking"
   - Each card: `min-h-[48px]`, `border-2`, orange border + orange-50 background when selected.

5. **Rewrote `handlePlaceOrder`** to two-step flow:
   - Step 1: `POST /api/v1/orders/` with `{ address: selectedAddr }` → `{ id }`
   - Step 2: `POST /api/v1/payments/initiate/` with `{ order_id: id, method: paymentMethod }`
   - COD path: `fetchCart()` then `router.push('/orders/{id}')` — identical to old behavior
   - Razorpay path: opens `window.Razorpay` modal; `handler` calls `fetchCart()` then redirects; `modal.ondismiss` resets `placing` to `false`

6. **Button label** changes dynamically:
   - COD: "Place Order" (idle) / "Placing Order..." (in-flight)
   - Razorpay: "Proceed to Payment" (idle) / "Opening Payment..." (in-flight)

## Self-Review

- **COD path end-to-end**: Creates order → initiates payment → fetchCart → redirect to `/orders/{id}`. Identical redirect to previous behavior. `setPlacing(false)` runs in `finally` for COD.
- **Razorpay path order**: Order created first (`POST /api/v1/orders/`), then payment initiated (`POST /api/v1/payments/initiate/`), then Razorpay modal opens. Correct sequence.
- **Radio cards 48px**: Both cards have `min-h-[48px]`. The Place Order button retains `min-h-[52px]`.
- **`placing` state for Razorpay**: The `finally` block has a guard (`if (paymentMethod === 'cod')`) so it doesn't prematurely reset `placing` for the Razorpay path. The `ondismiss` callback resets it when the modal is closed without payment.

## Concerns

None blocking. One minor note: the `finally` block approach for managing `placing` across async branching is slightly asymmetric — Razorpay leaves `placing=true` while the modal is open (intentional, prevents double-click). If the Razorpay `handler` callback encounters a navigation error, `placing` would stay `true` permanently. This is edge-case enough to leave as-is for now.
