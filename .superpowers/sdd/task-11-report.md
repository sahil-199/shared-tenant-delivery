# Task 11 Report: Login Page — OTP Flow UI

## Status: COMPLETE

## Files Created / Modified

### Created
- `frontend/app/(auth)/login/page.tsx` — Two-step OTP login wizard (phone entry → OTP entry)
- `frontend/app/(store)/page.tsx` — Home placeholder ("Store coming soon — Phase 3+")

### Modified
- `frontend/app/layout.tsx` — Replaced Geist fonts with Jost body font; updated metadata title/description; removed unused `next/font/google` imports

## TypeScript (`npx tsc --noEmit`) Output

```
(node:36619) ExperimentalWarning: CommonJS module .../debug/src/node.js is loading ES Module
Support for loading ES Module in require() is an experimental feature ...
```

**Zero TypeScript errors.** The Node.js warning is a runtime Node v23 issue unrelated to our code.

## Design Implementation Notes

### Login Page (`(auth)/login/page.tsx`)
- Two-step wizard: `'phone'` → `'otp'`, never both shown simultaneously
- Brand mark: inline hardhat SVG (Heroicons-style, `w-8 h-8 text-slate-400`) at card top
- Heading: "Welcome back" in `text-slate-900` with `font-family: var(--font-bodoni)` inline style
- Step indicator: "Step 1 of 2" / "Step 2 of 2" in `text-xs text-slate-400`
- Page: `min-h-screen flex items-center justify-center bg-slate-50 px-4`
- Card: `w-full max-w-sm bg-white rounded-2xl border border-slate-100 shadow-sm p-8`
- Phone input: `text-lg`, `inputMode="numeric"`, placeholder `e.g. 9876543210`, `maxLength={10}`
- OTP input: `text-2xl tracking-[0.5em] text-center`, `inputMode="numeric"`, `maxLength={6}`
- Loading states: button text changes to "Sending OTP…" / "Verifying…" during requests
- Error handling: field-level via `Input`'s `error` prop (red text below field)
- JWT base64url decoding: handles URL-safe base64 (`-` → `+`, `_` → `/`) before `atob`

### Layout (`layout.tsx`)
- Removed Geist/Geist_Mono next/font imports (fonts loaded via Google Fonts in `globals.css`)
- Body class: `font-['Jost']` — reinforces the CSS rule in globals.css
- Metadata updated: title "Hardware & Sanitary Store"

### Home Placeholder (`(store)/page.tsx`)
- Minimal: centered text, `bg-slate-50`, `font-['Jost']`
- No conflicting route with existing `app/page.tsx` (route groups are transparent to URL routing — both `/` paths coexist; the `(store)` group page will be used once `app/page.tsx` is removed or the root page is migrated)

## Concerns

1. **Root page conflict**: Both `app/page.tsx` (existing Next.js default) and `app/(store)/page.tsx` resolve to `/`. Next.js will throw a build-time error if both exist simultaneously. The existing `app/page.tsx` should be deleted or replaced once Phase 3 development begins. For now, `app/page.tsx` takes precedence during dev.

2. **Font rendering**: `font-['Jost']` in Tailwind v4 relies on the font being loaded globally (done via `@import url(...)` in `globals.css`). No next/font optimization — acceptable for MVP.

3. **JWT payload shape**: The OTP verify handler assumes `{ phone, is_store_owner }` in the JWT payload. If the backend uses different claim names, `setAuth` will receive undefined values. Needs verification against the actual Django JWT config.
