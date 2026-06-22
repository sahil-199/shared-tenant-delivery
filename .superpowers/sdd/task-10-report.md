# Task 10 Report: Next.js Frontend Scaffold

## Status
COMPLETE

## Adaptation Notes
create-next-app v16.2.9 generated a **Tailwind CSS v4** project (not v3). Key differences:
- No `tailwind.config.ts` — Tailwind v4 uses `@theme inline {}` in CSS for custom tokens
- Custom fonts registered via `--font-*` CSS custom properties inside `@theme inline`
- `@import "tailwindcss"` replaces the three `@tailwind` directives
- This is handled correctly in globals.css

## Files Created
- `frontend/` — Next.js 16.2.9 app scaffold (create-next-app, App Router, TypeScript)
- `frontend/.env.local` — `NEXT_PUBLIC_API_URL=http://localhost:8000` placeholder
- `frontend/lib/auth.ts` — SSR-safe localStorage token helpers (getAccessToken, getRefreshToken, setTokens, clearTokens)
- `frontend/lib/api.ts` — typed apiFetch<T> with Bearer auth and auto 401 refresh
- `frontend/store/auth.ts` — Zustand 5 useAuthStore (user, isAuthenticated, setAuth, logout)
- `frontend/components/ui/Button.tsx` — Button primitive (primary/secondary/ghost, min-h-[48px], loading spinner)
- `frontend/components/ui/Input.tsx` — Input primitive with label, error state, min-h-[48px]

## Files Modified
- `frontend/app/globals.css` — Google Fonts @import (Bodoni Moda + Jost), @theme inline with --font-bodoni/--font-jost, CSS vars (#F8FAFC background, #334155 text), Jost default body font

## tsc Output
Zero errors. Only Node.js experimental ESM/CJS interop warnings (unrelated to TypeScript).

## Design System Applied
- Background: #F8FAFC (--background CSS var)
- Text: #334155 (--foreground CSS var)
- Primary CTA: bg-orange-500, hover:bg-orange-600, active:bg-orange-700
- Fonts: Bodoni Moda (headings via font-bodoni), Jost (body default + font-jost)
- All interactive elements: min-h-[48px], transition-colors duration-200

## Concerns
- Google Fonts loaded via @import. For production, consider Next.js `next/font/google` for zero-layout-shift and self-hosting. Fine for scaffold stage.
- Zustand store state is ephemeral (not persisted to localStorage). On page refresh, `isAuthenticated` resets to false even though tokens survive in localStorage. A future task should add a hydration step (e.g., an `AuthProvider` that reads tokens on mount and calls `setAuth` to rehydrate state).
- `NEXT_PUBLIC_API_URL` must be set in all deployment environments (Vercel env vars, Docker compose, etc.).
- Tailwind v4 font utilities are `font-bodoni` and `font-jost` (matching `--font-bodoni`/`--font-jost` token names), not `font-['Bodoni_Moda']`. Components in later tasks should use these utility classes.
