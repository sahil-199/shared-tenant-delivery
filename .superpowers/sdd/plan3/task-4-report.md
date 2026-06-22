# Task 4 Report: Cart Frontend

## Status: COMPLETE

## Files Created

- `frontend/store/cart.ts` — Zustand store with `useCartStore`. State: `items`, `total`, `open`, `loading`. Actions: `setOpen`, `fetchCart`, `addItem`, `updateQty`, `removeItem`. Follows exact same pattern as `frontend/store/auth.ts`.
- `frontend/components/cart/CartItemRow.tsx` — Row component with qty increment/decrement (decrement to 0 removes the item), product link, variant name, subtotal display.
- `frontend/components/cart/CartDrawer.tsx` — Slide-in drawer with backdrop, empty state, items list, total, and Proceed to Checkout link. Fetches cart on mount when authenticated. Returns null when closed (no SSR issue).

## Files Modified

- `frontend/components/product/VariantSelector.tsx` — Replaced placeholder `alert('Cart coming in Phase 7')` with real `handleAddToCart` (async, sets `adding` state, redirects to login if unauthenticated). Added `useCartStore` import and `adding` state. All existing variant selector UI unchanged.
- `frontend/app/layout.tsx` — Added `import CartDrawer` and `<CartDrawer />` after `{children}` in body.

## Self-Review

- `zustand: ^5.0.14` confirmed in `frontend/package.json` — no new dependency needed.
- All client components marked `'use client'`.
- `CartDrawer` returns `null` when `open` is false — safe for server rendering of root layout (Next.js 16 App Router).
- `useEffect` dependency array in `CartDrawer` only includes `isAuthenticated` (fetchCart is stable from Zustand, omitting it is intentional to avoid infinite loops).
- TypeScript: all imports resolve — `CartItem` is exported from `cart.ts`, `useAuthStore` from `auth.ts`, `apiFetch` from `lib/api.ts`.
- No concerns.

## Follow-up Fixes Applied

Fixes applied: touch targets enlarged (+/- to 40px, close to 48px), updateQty/removeItem wrapped in try/catch.
