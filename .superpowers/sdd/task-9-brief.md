# Task 9: Admin Products Management Page

## Context

Final task of Plan 2. Tasks 7 and 8 complete — frontend types, ProductCard, ProductGrid, product listing page, and product detail page all exist.

## Files to Create

- **Create:** `frontend/app/admin/layout.tsx`
- **Create:** `frontend/app/admin/products/page.tsx`
- **Create:** `frontend/components/admin/ProductForm.tsx`
- **Create:** `frontend/app/admin/products/new/page.tsx`

## Global Constraints

- **No git in this project**
- Next.js **16.2.9** — read `node_modules/next/dist/docs/` before writing (AGENTS.md)
- TailwindCSS v4 (no `tailwind.config.ts`)
- Fonts: `font-['Bodoni_Moda']` headings, `font-['Jost']` body
- Color palette: slate-50 background, orange-500 CTA, white cards, slate-900 headings
- Minimum touch target: 48px on all interactive elements
- All 4 files are `'use client'` components (admin is fully client-side — reads auth from Zustand)

## Existing Interfaces

**`frontend/lib/api.ts`** — `apiFetch<T>(path, options?)` — authenticated fetch with auto token refresh. Throws the parsed error response on non-2xx.

**`frontend/store/auth.ts`** — `useAuthStore()` returns `{ user, isAuthenticated }` where `user: { phone: string; isStoreOwner: boolean } | null`.

**`frontend/lib/types.ts`** — `Category`, `Product`, `ProductVariant` interfaces are defined.

## Step-by-Step Implementation

### Step 1: Check Next.js docs

Read `frontend/node_modules/next/dist/docs/` — confirm client component conventions in App Router for this version.

### Step 2: Create `frontend/app/admin/layout.tsx`

Owner guard — redirects to `/login` if not authenticated or not store owner.

```tsx
'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated || !user?.isStoreOwner) {
      router.replace('/login');
    }
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated || !user?.isStoreOwner) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-400 font-['Jost'] text-sm">Checking permissions...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-6">
          <span className="font-['Bodoni_Moda'] text-lg font-bold text-slate-900">Admin</span>
          <nav className="flex gap-4">
            <Link
              href="/admin/products"
              className="text-sm text-slate-600 hover:text-orange-500 font-['Jost'] transition-colors min-h-[44px] flex items-center"
            >
              Products
            </Link>
          </nav>
          <div className="ml-auto">
            <Link
              href="/"
              className="text-sm text-slate-500 hover:text-slate-700 font-['Jost'] transition-colors min-h-[44px] flex items-center"
            >
              ← Store
            </Link>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
```

### Step 3: Create `frontend/app/admin/products/page.tsx`

Products list with Add Product button. Uses `apiFetch` (sends owner JWT automatically).

```tsx
'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import type { Product } from '@/lib/types';

export default function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch<Product[]>('/api/v1/products/')
      .then(setProducts)
      .catch(() => setError('Failed to load products'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-slate-400 font-['Jost'] text-sm">Loading...</p>;
  }

  if (error) {
    return <p className="text-red-500 font-['Jost'] text-sm">{error}</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900">Products</h1>
        <Link
          href="/admin/products/new"
          className="bg-orange-500 text-white px-5 py-2.5 rounded-xl text-sm font-semibold font-['Jost'] hover:bg-orange-600 transition-colors cursor-pointer min-h-[48px] flex items-center gap-1.5"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Product
        </Link>
      </div>

      {products.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-100">
          <p className="text-slate-400 font-['Jost'] text-sm mb-4">No products yet.</p>
          <Link
            href="/admin/products/new"
            className="text-orange-500 font-medium font-['Jost'] text-sm hover:text-orange-600 transition-colors"
          >
            Create your first product →
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost']">Product</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost'] hidden md:table-cell">Category</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost']">Variants</th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider font-['Jost'] hidden sm:table-cell">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-900 font-['Jost'] text-sm">{p.name}</p>
                      <p className="text-xs text-slate-400 font-['Jost']">{p.slug}</p>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 font-['Jost'] hidden md:table-cell">{p.category_name}</td>
                    <td className="px-6 py-4 text-sm text-slate-600 font-['Jost']">{p.variants.length}</td>
                    <td className="px-6 py-4 hidden sm:table-cell">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium font-['Jost'] ${
                        p.is_active ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'
                      }`}>
                        {p.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Step 4: Create `frontend/components/admin/ProductForm.tsx`

Form for creating a product. `apiFetch` sends the owner JWT. Redirects to `/admin/products` on success.

```tsx
'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import type { Category } from '@/lib/types';

interface VariantRow {
  name: string;
  sku: string;
  price: string;
}

const INPUT = 'w-full border border-slate-200 rounded-xl px-4 py-3 text-slate-900 font-["Jost"] text-sm focus:outline-none focus:ring-2 focus:ring-orange-200 focus:border-orange-400 bg-white min-h-[48px] transition-colors';
const LABEL = 'block text-sm font-medium text-slate-700 font-["Jost"] mb-1.5';

export default function ProductForm() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ name: '', slug: '', category: '', description: '', specifications: '' });
  const [variants, setVariants] = useState<VariantRow[]>([{ name: '', sku: '', price: '' }]);

  useEffect(() => {
    apiFetch<Category[]>('/api/v1/categories/').then(setCategories).catch(console.error);
  }, []);

  const handleNameChange = (name: string) => {
    const slug = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    setForm((f) => ({ ...f, name, slug }));
  };

  const parseSpecs = (text: string): Record<string, string> => {
    const specs: Record<string, string> = {};
    text.split('\n').forEach((line) => {
      const colonIdx = line.indexOf(':');
      if (colonIdx > 0) {
        const key = line.slice(0, colonIdx).trim();
        const value = line.slice(colonIdx + 1).trim();
        if (key && value) specs[key] = value;
      }
    });
    return specs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await apiFetch('/api/v1/products/', {
        method: 'POST',
        body: JSON.stringify({
          name: form.name,
          slug: form.slug,
          category: parseInt(form.category),
          description: form.description,
          specifications: parseSpecs(form.specifications),
          variants: variants.filter((v) => v.name && v.sku && v.price),
        }),
      });
      router.push('/admin/products');
    } catch (err: unknown) {
      const msg =
        typeof err === 'object' && err !== null && !Array.isArray(err)
          ? Object.entries(err as Record<string, unknown>)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
              .join(' | ')
          : 'Failed to create product';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const addVariant = () => setVariants((vs) => [...vs, { name: '', sku: '', price: '' }]);
  const removeVariant = (i: number) => setVariants((vs) => vs.filter((_, idx) => idx !== i));
  const updateVariant = (i: number, field: keyof VariantRow, value: string) =>
    setVariants((vs) => vs.map((v, idx) => (idx === i ? { ...v, [field]: value } : v)));

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-2xl">
      {error && (
        <div className="bg-red-50 border border-red-100 text-red-700 rounded-xl px-4 py-3 text-sm font-['Jost']">
          {error}
        </div>
      )}

      <div className="bg-white rounded-2xl p-6 border border-slate-100 space-y-4">
        <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 text-lg">Product Details</h2>

        <div>
          <label className={LABEL}>Name *</label>
          <input className={INPUT} value={form.name} onChange={(e) => handleNameChange(e.target.value)} required placeholder="e.g. PVC Pipe 2 inch" />
        </div>

        <div>
          <label className={LABEL}>Slug * <span className="text-slate-400 font-normal text-xs">(auto-generated)</span></label>
          <input className={INPUT} value={form.slug} onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))} required pattern="[a-z0-9-]+" title="Lowercase letters, numbers, hyphens only" />
        </div>

        <div>
          <label className={LABEL}>Category *</label>
          <select className={INPUT} value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))} required>
            <option value="">Select a category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className={LABEL}>Description</label>
          <textarea className={`${INPUT} min-h-[90px] resize-y`} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Brief product description" />
        </div>

        <div>
          <label className={LABEL}>Specifications <span className="text-slate-400 font-normal text-xs">(one per line: key: value)</span></label>
          <textarea className={`${INPUT} min-h-[80px] resize-y font-mono text-xs`} value={form.specifications} onChange={(e) => setForm((f) => ({ ...f, specifications: e.target.value }))} placeholder={'material: PVC\ndiameter: 2 inch'} />
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 border border-slate-100">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-['Bodoni_Moda'] font-bold text-slate-900 text-lg">Variants</h2>
          <button type="button" onClick={addVariant} className="text-orange-500 text-sm font-medium font-['Jost'] hover:text-orange-600 transition-colors cursor-pointer min-h-[48px] flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Variant
          </button>
        </div>

        <div className="space-y-3">
          {variants.map((v, i) => (
            <div key={i} className="grid grid-cols-3 gap-3 items-end">
              <div>
                {i === 0 && <label className={LABEL}>Name *</label>}
                <input className={INPUT} value={v.name} onChange={(e) => updateVariant(i, 'name', e.target.value)} placeholder="e.g. 1 inch" required />
              </div>
              <div>
                {i === 0 && <label className={LABEL}>SKU *</label>}
                <input className={INPUT} value={v.sku} onChange={(e) => updateVariant(i, 'sku', e.target.value.toUpperCase())} placeholder="e.g. PVC-1IN" required />
              </div>
              <div className="relative">
                {i === 0 && <label className={LABEL}>Price (₹) *</label>}
                <input className={INPUT} type="number" min="0" step="0.01" value={v.price} onChange={(e) => updateVariant(i, 'price', e.target.value)} placeholder="0.00" required />
                {variants.length > 1 && (
                  <button type="button" onClick={() => removeVariant(i)} className="absolute -top-5 right-0 text-xs text-slate-400 hover:text-red-500 transition-colors cursor-pointer font-['Jost']">
                    remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <button type="submit" disabled={submitting} className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-orange-300 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl font-['Jost'] text-base transition-colors cursor-pointer min-h-[52px]">
        {submitting ? 'Creating...' : 'Create Product'}
      </button>
    </form>
  );
}
```

### Step 5: Create `frontend/app/admin/products/new/page.tsx`

```tsx
import Link from 'next/link';
import ProductForm from '@/components/admin/ProductForm';

export default function NewProductPage() {
  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/admin/products"
          className="text-slate-500 hover:text-slate-700 transition-colors cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center -ml-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900">New Product</h1>
      </div>
      <ProductForm />
    </div>
  );
}
```

### Step 6: Verify TypeScript

```bash
cd /Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/frontend && npx tsc --noEmit
```

Zero errors in new files (the pre-existing `.next/types/validator.ts` stale cache error is known and can be ignored).

## Report

Write full report to:
`/Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/.superpowers/sdd/task-9-report.md`

Return: Status (DONE/DONE_WITH_CONCERNS/BLOCKED), one-line summary, any concerns.
