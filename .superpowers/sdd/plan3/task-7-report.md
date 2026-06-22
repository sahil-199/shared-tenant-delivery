# Task 7 Report — Orders Frontend

**Status:** DONE

## Files Created

1. `frontend/app/(store)/orders/page.tsx`
   - Customer orders list page (`'use client'`)
   - Redirects to `/login` if not authenticated (useAuthStore + useRouter)
   - Fetches `GET /api/v1/orders/list/` via apiFetch
   - Renders order cards with id, date, status badge, items count, total
   - Each card links to `/orders/{id}` with min-h-[48px] touch target
   - Empty state with "Browse Products" CTA button
   - Status badge colors: pending→amber, confirmed→blue, shipped→purple, delivered→green, cancelled→red, refunded→gray

2. `frontend/app/(store)/orders/[id]/page.tsx`
   - Order detail page (`'use client'`)
   - Reads orderId from `useParams()`
   - Fetches `GET /api/v1/orders/{id}/` via apiFetch
   - Shows: status + date, status timeline, items list with unit price/qty/subtotal, delivery address, grand total
   - StatusTimeline: dots+lines for pending→confirmed→shipped→delivered; completed steps green, current step orange, future steps gray
   - Terminal states (cancelled, refunded) render a separate single-dot indicator instead of the timeline
   - Back link to `/orders` with min-h-[48px] min-w-[48px]

3. `frontend/app/admin/orders/page.tsx`
   - Admin orders list page (`'use client'`)
   - Auth guard is handled by the admin layout (already redirects non-owners to /login)
   - Fetches `GET /api/v1/orders/list/` via apiFetch
   - Table: Order#, Date, Status badge, Total, Update dropdown
   - Status dropdown only shows valid forward transitions: pending→confirmed, confirmed→shipped, shipped→delivered
   - Terminal states (delivered/cancelled/refunded) show "—" instead of a dropdown
   - PATCH `/api/v1/orders/{id}/status/` with `{ status: newStatus }` on selection
   - Local state updated optimistically after successful PATCH; per-row error display on failure
   - Dropdown has `min-h-[48px]`

## Files Modified

- `frontend/app/admin/layout.tsx` — added "Orders" nav link pointing to `/admin/orders` alongside existing Products link

## Self-Review Checklist

- All interactive elements >= 48px: back links use `min-h-[48px] min-w-[48px]`; order cards `min-h-[48px]`; status dropdown `min-h-[48px]`; empty-state CTA `min-h-[48px]` ✓
- No unused imports ✓
- TypeScript types defined for all API shapes ✓
- apiFetch used everywhere (no raw fetch) ✓
- useAuthStore for auth check ✓
- useRouter from next/navigation ✓
- font-['Bodoni_Moda'] headings, font-['Jost'] body ✓
- orange-500 primary actions ✓

## Notes

- Admin orders page relies on the existing admin layout for the auth/isStoreOwner redirect guard, consistent with how all admin pages work in this codebase (the layout handles it, pages don't duplicate it).
- `useParams()` is used in the `[id]` page rather than a prop, which is the Next.js 15+ pattern for client components.
- Status dropdown resets to the placeholder after each selection so the UI stays clean if the admin wants to make multiple updates.
