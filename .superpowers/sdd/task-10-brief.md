### Task 10: Next.js Frontend Scaffold

**Files:**
- Create: `frontend/` (via create-next-app)
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/auth.ts`
- Create: `frontend/store/auth.ts`
- Create: `frontend/components/ui/Button.tsx`
- Create: `frontend/components/ui/Input.tsx`

**Interfaces:**
- Produces:
  - `apiFetch(path, options)` — typed fetch wrapper with auto token refresh
  - `getAccessToken() / setTokens() / clearTokens()` — token storage helpers
  - `useAuthStore` — Zustand store with `{ user, isAuthenticated, setAuth, logout }`

- [ ] **Step 1: Scaffold Next.js app**

Run from the repo root:
```bash
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --src-dir=no \
  --import-alias="@/*" \
  --no-git
```
When prompted, select: TypeScript ✓, ESLint ✓, Tailwind ✓, App Router ✓

- [ ] **Step 2: Install Zustand**

```bash
cd frontend && npm install zustand
```

- [ ] **Step 3: Write lib/auth.ts — token storage**

`frontend/lib/auth.ts`:
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

- [ ] **Step 4: Write lib/api.ts — typed fetch wrapper**

`frontend/lib/api.ts`:
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
  return data.access;
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

- [ ] **Step 5: Write store/auth.ts — Zustand auth store**

`frontend/store/auth.ts`:
```typescript
'use client';
import { create } from 'zustand';
import { setTokens, clearTokens } from '@/lib/auth';

interface AuthUser {
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

- [ ] **Step 6: Write UI primitives**

`frontend/components/ui/Button.tsx`:
```typescript
import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
}

export function Button({ variant = 'primary', loading, children, className = '', disabled, ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center rounded-xl font-semibold text-base transition-colors min-h-[48px] px-6 disabled:opacity-50 disabled:cursor-not-allowed';
  const variants = {
    primary: 'bg-orange-500 text-white hover:bg-orange-600 active:bg-orange-700',
    secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
    ghost: 'bg-transparent text-orange-500 hover:bg-orange-50',
  };
  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <span className="animate-spin mr-2">⏳</span> : null}
      {children}
    </button>
  );
}
```

`frontend/components/ui/Input.tsx`:
```typescript
import { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <input
        className={`
          w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3
          text-base text-gray-900 placeholder-gray-400
          focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-200
          disabled:opacity-50 min-h-[48px]
          ${error ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''}
          ${className}
        `}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 7: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

---

