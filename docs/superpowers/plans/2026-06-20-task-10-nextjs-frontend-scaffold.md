# Task 10: Next.js Frontend Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the Next.js 14 frontend with the design system, typed API client, Zustand auth store, and UI primitives (Button, Input).

**Architecture:** Run create-next-app into the existing `frontend/` directory (which only has a Dockerfile.dev), then layer in the design system (fonts, Tailwind config, globals.css), the auth/API library files, the Zustand store, and the two UI primitives — all following the orange/slate color palette and Bodoni Moda + Jost typography.

**Tech Stack:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand 4, Google Fonts (Bodoni Moda + Jost)

## Global Constraints

- Working directory root: `/Users/sahil/src/my_idea/shared_tenant_home_delivery_interface`
- Next.js app lives at: `frontend/` (relative to root)
- No git commits at any step (NO GIT)
- Minimum touch target: `min-h-[48px]` on ALL interactive elements
- Primary color: `#F97316` (`bg-orange-500`), hover `bg-orange-600`
- Background: `#F8FAFC` (`bg-slate-50`), Text: `#334155` (`text-slate-700`)
- Headings font: `Bodoni Moda` (serif), Body/UI font: `Jost` (geometric sans)
- `transition-colors duration-200` on all interactive elements
- TypeScript must compile with zero errors (`npx tsc --noEmit`)
- Backend API base URL env var: `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000`)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `frontend/` (via create-next-app) | Create | Next.js app scaffold with TS + Tailwind + App Router |
| `frontend/app/globals.css` | Modify | Add Google Fonts @import, apply Jost as default body font |
| `frontend/tailwind.config.ts` | Modify | Add `fontFamily` entries for `bodoni` and `jost` |
| `frontend/lib/auth.ts` | Create | Token storage helpers (localStorage, SSR-safe) |
| `frontend/lib/api.ts` | Create | Typed `apiFetch` wrapper with auto 401 token refresh |
| `frontend/store/auth.ts` | Create | Zustand `useAuthStore` with `setAuth` / `logout` |
| `frontend/components/ui/Button.tsx` | Create | Button UI primitive (primary / secondary / ghost variants) |
| `frontend/components/ui/Input.tsx` | Create | Input UI primitive with label and error state |
| `frontend/.env.local` | Create | `NEXT_PUBLIC_API_URL=http://localhost:8000` placeholder |

---

### Task 1: Scaffold Next.js App

**Files:**
- Create: `frontend/` (populated by create-next-app)

**Interfaces:**
- Produces: `frontend/package.json`, `frontend/app/`, `frontend/tailwind.config.ts`, `frontend/tsconfig.json`

- [ ] **Step 1: Run create-next-app from repo root**

```bash
cd /Users/sahil/src/my_idea/shared_tenant_home_delivery_interface
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias="@/*" --no-git --yes 2>&1 | tail -10
```

Expected: Lines ending with `Success! Created frontend at ...` or similar. The command uses `--yes` to skip all prompts. The existing `Dockerfile.dev` in `frontend/` will be preserved.

- [ ] **Step 2: Verify the scaffold exists**

```bash
ls /Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/frontend/
```

Expected output includes: `app/  node_modules/  package.json  tailwind.config.ts  tsconfig.json  next.config.ts` (or `.mjs`/`.js`)

- [ ] **Step 3: Install Zustand**

```bash
cd /Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/frontend && npm install zustand
```

Expected: `added N packages` with no errors.

- [ ] **Step 4: Create .env.local with API base URL**

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### Task 2: Design System — Fonts and Tailwind Config

**Files:**
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tailwind.config.ts`

**Interfaces:**
- Consumes: `frontend/tailwind.config.ts` and `frontend/app/globals.css` from Task 1
- Produces: Tailwind utility classes `font-bodoni` and `font-jost` available project-wide; Jost applied as default body font

- [ ] **Step 1: Read the current globals.css to see what's there**

```bash
cat /Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/frontend/app/globals.css
```

- [ ] **Step 2: Prepend Google Fonts import and set body font in globals.css**

Replace the entire contents of `frontend/app/globals.css` with:

```css
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,700&family=Jost:wght@300;400;500;600;700&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #F8FAFC;
  --foreground: #334155;
}

body {
  font-family: 'Jost', sans-serif;
  background-color: var(--background);
  color: var(--foreground);
}
```

(If the existing globals.css has additional CSS variables or dark-mode blocks you want to keep, append them after the `body {}` block — but do not remove the lines above.)

- [ ] **Step 3: Read the current tailwind.config.ts**

```bash
cat /Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/frontend/tailwind.config.ts
```

- [ ] **Step 4: Add custom fontFamily to tailwind.config.ts**

In `frontend/tailwind.config.ts`, extend the `theme` with custom fonts. The final file should look like:

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        bodoni: ['"Bodoni Moda"', 'Georgia', 'serif'],
        jost: ['Jost', 'system-ui', 'sans-serif'],
      },
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
      },
    },
  },
  plugins: [],
};

export default config;
```

> Note: `create-next-app` may generate a slightly different skeleton. Preserve the existing `content` array if it already has entries; just add the `fontFamily` and `colors` under `theme.extend`.

---

### Task 3: Token Storage Helpers — lib/auth.ts

**Files:**
- Create: `frontend/lib/auth.ts`

**Interfaces:**
- Produces:
  - `getAccessToken(): string | null` — reads from localStorage (SSR-safe)
  - `getRefreshToken(): string | null` — reads from localStorage (SSR-safe)
  - `setTokens(access: string, refresh: string): void`
  - `clearTokens(): void`

- [ ] **Step 1: Create the lib directory and auth.ts**

Create `frontend/lib/auth.ts` with this exact content:

```typescript
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}
```

> The `typeof window === 'undefined'` guard prevents crashes during Next.js server-side rendering where `localStorage` is not available.

---

### Task 4: Typed API Fetch Wrapper — lib/api.ts

**Files:**
- Create: `frontend/lib/api.ts`

**Interfaces:**
- Consumes: `getAccessToken`, `getRefreshToken`, `setTokens`, `clearTokens` from `@/lib/auth`
- Produces:
  - `apiFetch<T>(path: string, options?: RequestInit): Promise<T>` — auto-attaches Bearer token, retries once on 401 after refreshing, throws the parsed JSON error body on failure

- [ ] **Step 1: Create frontend/lib/api.ts**

```typescript
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  const res = await fetch(`${BASE_URL}/api/v1/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    clearTokens();
    return null;
  }
  const data = await res.json();
  setTokens(data.access, refresh);
  return data.access as string;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const token = getAccessToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers ?? {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let res = await fetch(url, { ...options, headers });

  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await fetch(url, {
        ...options,
        headers: { ...headers, Authorization: `Bearer ${newToken}` },
      });
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: res.statusText }));
    throw error;
  }

  return res.json() as Promise<T>;
}
```

---

### Task 5: Zustand Auth Store — store/auth.ts

**Files:**
- Create: `frontend/store/auth.ts`

**Interfaces:**
- Consumes: `setTokens`, `clearTokens` from `@/lib/auth`
- Produces:
  - `useAuthStore` — Zustand hook exposing `{ user: AuthUser | null, isAuthenticated: boolean, setAuth(user, accessToken, refreshToken): void, logout(): void }`
  - `AuthUser` — `{ phone: string, isStoreOwner: boolean }`

- [ ] **Step 1: Create frontend/store/auth.ts**

```typescript
'use client';
import { create } from 'zustand';
import { setTokens, clearTokens } from '@/lib/auth';

export interface AuthUser {
  phone: string;
  isStoreOwner: boolean;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setAuth: (user, accessToken, refreshToken) => {
    setTokens(accessToken, refreshToken);
    set({ user, isAuthenticated: true });
  },
  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false });
  },
}));
```

> `'use client'` is required because Zustand stores use browser state (`localStorage` via `setTokens`/`clearTokens`). Any component that imports `useAuthStore` must also be a Client Component.

---

### Task 6: Button UI Primitive

**Files:**
- Create: `frontend/components/ui/Button.tsx`

**Interfaces:**
- Produces:
  - `Button({ variant?, loading?, children, className?, disabled?, ...HTMLButtonAttributes })` — React component

- [ ] **Step 1: Create frontend/components/ui/Button.tsx**

```tsx
import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
}

export function Button({
  variant = 'primary',
  loading,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const base =
    'inline-flex items-center justify-center rounded-xl font-semibold text-base transition-colors duration-200 min-h-[48px] px-6 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer';
  const variants = {
    primary: 'bg-orange-500 text-white hover:bg-orange-600 active:bg-orange-700',
    secondary: 'bg-slate-100 text-slate-700 hover:bg-slate-200',
    ghost: 'bg-transparent text-orange-500 hover:bg-orange-50',
  };
  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 22 6.477 22 12h-4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
```

---

### Task 7: Input UI Primitive

**Files:**
- Create: `frontend/components/ui/Input.tsx`

**Interfaces:**
- Produces:
  - `Input({ label?, error?, className?, ...HTMLInputAttributes })` — React component

- [ ] **Step 1: Create frontend/components/ui/Input.tsx**

```tsx
import { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label className="text-sm font-medium text-slate-700">{label}</label>
      )}
      <input
        className={`w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-base text-slate-700 placeholder-slate-400 min-h-[48px] focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-200 disabled:opacity-50 transition-colors duration-200 ${
          error ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''
        } ${className}`}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
```

---

### Task 8: TypeScript Verification

**Files:**
- No new files — verification step only

**Interfaces:**
- Consumes: All files from Tasks 1–7

- [ ] **Step 1: Run tsc --noEmit**

```bash
cd /Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/frontend && npx tsc --noEmit 2>&1
```

Expected: No output (zero errors). If errors appear, fix them before proceeding.

**Common fixes:**
- If tsc complains about `zustand` types: ensure `npm install zustand` completed in Task 1 Step 3.
- If tsc complains about missing `@types/*`: run `npm install --save-dev @types/node` (usually pre-installed by create-next-app).
- If tsc complains about `'use client'` in store/auth.ts: this is a Next.js directive, not a TS issue — ensure tsconfig.json has `"lib": ["dom", "esnext"]` or similar (create-next-app sets this by default).

- [ ] **Step 2: Write the task-10 report**

Create `/Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/.superpowers/sdd/task-10-report.md` with:

```markdown
# Task 10 Report: Next.js Frontend Scaffold

## Status
COMPLETE

## Files Created
- `frontend/` — Next.js 14 app scaffold (create-next-app)
- `frontend/.env.local` — NEXT_PUBLIC_API_URL placeholder
- `frontend/app/globals.css` — Google Fonts import, Jost default body font, CSS vars
- `frontend/tailwind.config.ts` — fontFamily extended with `bodoni` and `jost`
- `frontend/lib/auth.ts` — SSR-safe localStorage token helpers
- `frontend/lib/api.ts` — typed apiFetch with auto 401 refresh
- `frontend/store/auth.ts` — Zustand useAuthStore
- `frontend/components/ui/Button.tsx` — Button primitive (primary/secondary/ghost)
- `frontend/components/ui/Input.tsx` — Input primitive with label/error

## Files Modified
- `frontend/app/globals.css`
- `frontend/tailwind.config.ts`

## tsc Output
[paste output of `npx tsc --noEmit` here — empty = zero errors]

## Concerns
- Google Fonts are loaded via @import in CSS. In production, consider using next/font for better performance and no layout shift. This is fine for the scaffold stage.
- The Zustand store uses localStorage directly; SSR pages that try to read auth state server-side will get null (by design — guarded by typeof window check).
- NEXT_PUBLIC_API_URL must be set in deployment environments (Vercel, Docker, etc.).
```

---

## Self-Review

**Spec coverage:**
- [x] create-next-app scaffold → Task 1
- [x] Zustand install → Task 1 Step 3
- [x] Google Fonts @import → Task 2
- [x] Tailwind fontFamily config → Task 2
- [x] `getAccessToken / setTokens / clearTokens` → Task 3
- [x] `apiFetch` with auto token refresh → Task 4
- [x] `useAuthStore` with `setAuth / logout` → Task 5
- [x] Button with mandatory design system colors and `cursor-pointer` → Task 6
- [x] Input with mandatory design system colors → Task 7
- [x] `npx tsc --noEmit` verification → Task 8
- [x] Report file at `.superpowers/sdd/task-10-report.md` → Task 8 Step 2
- [x] NO GIT constraint → noted in Global Constraints, no commit steps present

**Placeholder scan:** No TBDs, no "implement later", no "similar to Task N" — each step has full code.

**Type consistency:**
- `getAccessToken`, `getRefreshToken`, `setTokens`, `clearTokens` defined in Task 3, imported in Task 4 and Task 5 using exact same names.
- `AuthUser` exported from `store/auth.ts` (Task 5) with `{ phone: string, isStoreOwner: boolean }`.
- `apiFetch<T>` signature matches brief exactly.
- `useAuthStore` exposes `{ user, isAuthenticated, setAuth, logout }` matching brief spec.
