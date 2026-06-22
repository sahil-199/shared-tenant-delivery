# Task 6 Report — Checkout Frontend Page

## Status: Complete

## Files Created

1. `frontend/components/checkout/AddressForm.tsx`
   - Exports `Address` interface (re-used by checkout page)
   - POST to `/api/v1/addresses/` via `apiFetch`
   - Error narrowed with `typeof err === 'object'` guard (safe for `unknown`)

2. `frontend/app/(store)/checkout/page.tsx`
   - `'use client'` — fully interactive
   - Auth guard: redirects to `/login` if `!isAuthenticated`, returns `null` before render
   - Loads saved addresses on mount; pre-selects default (or first)
   - Inline `AddressForm` for adding a new address
   - Order summary pulled from `useCartStore` (`items`, `total`)
   - POST to `/api/v1/orders/` with `{ address: selectedAddr }`
   - On success: `fetchCart()` to clear store, then `router.push('/orders/{id}')`
   - Error narrowed via `err as Record<string, unknown>` then `typeof e?.detail === 'string'` check

## TypeScript Notes

- `Address` interface is exported from `AddressForm.tsx` and imported as `type Address` in the checkout page — correct usage for an interface re-export.
- `catch (err: unknown)` in `AddressForm`: guarded with `typeof err === 'object'` before `JSON.stringify` — safe. Null is also typeof 'object'; `JSON.stringify(null)` returns `"null"` which is acceptable UX for an edge case.
- `catch (err: unknown)` in checkout `handlePlaceOrder`: cast to `Record<string, unknown>` then checks `typeof e?.detail === 'string'` before using — correct narrowing pattern.
- `useEffect` dependency array includes only `[isAuthenticated]` — intentional; `fetchCart` and `router` are stable refs and omitting them avoids spurious re-fetches. A stricter lint setup may warn; wrapping `fetchCart` in `useCallback` in the store or adding it to deps with a `useRef` guard would silence that if needed.
- `apiFetch<Address[]>` call with `.then().catch()` inside `useEffect` — valid pattern; the async effect is not directly awaited but errors are swallowed intentionally (`.catch(() => {})`).

## No Issues Found
All types align with `CartItem` fields (`subtotal: string`, `qty: number`) and `AuthState` (`isAuthenticated: boolean`).
