# Task 2 Report — Search Bar & Sort Controls

**Status:** Complete

## Files Changed

| File | Action |
|------|--------|
| `frontend/components/product/SearchBar.tsx` | Created |
| `frontend/components/product/SortSelector.tsx` | Created |
| `frontend/app/(store)/products/page.tsx` | Updated |

## What Was Done

1. **SearchBar** — client component using `useSearchParams` + `useTransition` from `react`. Updates `search` URL param on input change via `router.replace`. `flex-1` added to wrapper div so it expands within the flex row. Touch target: `min-h-[48px]` (upgraded from spec's `44px` to match existing sidebar standard).

2. **SortSelector** — client component with a `<select>` for Newest / Price: Low to High / Price: High to Low. Updates `sort` URL param. Single `useTransition` import from `react` only (removed the erroneous duplicate import from the task brief). Touch target: `min-h-[48px]`.

3. **page.tsx** — Replaced `getProducts` to accept `{ category, search, sort }` params and build a proper query string. Both `SearchBar` and `SortSelector` wrapped in `<Suspense fallback={null}>` (required because they call `useSearchParams`). Header row restructured: `h1` + `div.flex` containing the two controls.

## TypeScript Corrections Applied

- **Next.js 16 `searchParams` API preserved:** The task brief used a Next.js 14-style synchronous `searchParams` prop. The existing codebase already had the correct Next.js 15+/16 pattern (`searchParams: Promise<...>` that is `await`ed). This was kept intact and extended to extract `search` and `sort` from the resolved params using the same `typeof ... === 'string'` guard pattern already in use for `category`.

- **`SortSelector` duplicate import removed:** The task brief contained a broken import (`import { useTransition } from 'next/navigation'` — which does not exist). Only the correct `import { useTransition } from 'react'` is present.

- **`SearchBar` wrapper `flex-1`:** Added so the input grows to fill available space within the `flex gap-3 flex-1 max-w-lg` row alongside `SortSelector`.

## No TypeScript Concerns

- `Product` and `Category` types in `@/lib/types` match usage.
- `ProductGrid` prop signature (`{ products: Product[] }`) matches what is passed.
- All Next.js navigation hooks (`useRouter`, `usePathname`, `useSearchParams`) are from `next/navigation` — correct for App Router.
- `Suspense` boundary around client components that use `useSearchParams` is required by Next.js for static rendering — correctly applied.
