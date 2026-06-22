# Task 8: Product Detail Frontend Page

## Context

Task 8 of 9 in Plan 2. Task 7 complete — `frontend/lib/types.ts`, `ProductCard`, `ProductGrid`, and `/products` listing page all exist.

## Files to Create

- **Create:** `frontend/components/product/VariantSelector.tsx`
- **Create:** `frontend/app/(store)/products/[slug]/page.tsx`

## Global Constraints

- **No git in this project**
- Next.js **16.2.9** is installed (NOT 14) — `params` in dynamic routes is also a `Promise` in this version; must be awaited
- TailwindCSS v4 (no `tailwind.config.ts`)
- Fonts: `font-['Bodoni_Moda']` headings, `font-['Jost']` body
- Color palette: slate-50 background, orange-500 CTA, white cards, slate-900 headings
- Minimum touch target: 48px on all interactive elements
- `VariantSelector` must be `'use client'`
- **AGENTS.md says**: Read `node_modules/next/dist/docs/` before writing page files — dynamic route `params` is a Promise in Next.js 15+

## Auth Store Interface

`frontend/store/auth.ts` exports `useAuthStore` (Zustand):
```ts
interface AuthState {
  user: AuthUser | null;      // { phone: string; isStoreOwner: boolean }
  isAuthenticated: boolean;
  setAuth: (user, accessToken, refreshToken) => void;
  logout: () => void;
}
```

## Login-on-Demand Requirement

The user must NOT be prompted to log in just to browse. Login is required only when they try to add to cart. Implement as:

- If `isAuthenticated` is false → redirect to `/login?next=/products/{slug}`
- If `isAuthenticated` is true → show "Cart coming in Phase 7" toast/message (placeholder)
- No modal, no inline prompt — just a `router.push` redirect

## Types Available

From `frontend/lib/types.ts`:
```ts
interface ProductVariant { id, name, sku, price, sale_price, effective_price, is_active }
interface ProductImage    { id, variant, image_url, sort_order }
interface Product         { id, name, slug, description, specifications, category, category_name, brand, brand_name, is_active, created_at, variants, images }
```

## Step-by-Step Implementation

### Step 1: Check Next.js docs (per AGENTS.md)

Read `frontend/node_modules/next/dist/docs/` — confirm how `params` works in dynamic routes for this version.

### Step 2: Create `frontend/components/product/VariantSelector.tsx`

`'use client'` component. Uses `useAuthStore` to check auth before "Add to Cart".

```tsx
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import type { ProductVariant } from '@/lib/types';

interface Props {
  variants: ProductVariant[];
  productSlug: string;
}

export default function VariantSelector({ variants, productSlug }: Props) {
  const [selected, setSelected] = useState<ProductVariant>(variants[0]);
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  if (variants.length === 0) return null;

  const handleAddToCart = () => {
    if (!isAuthenticated) {
      router.push(`/login?next=/products/${productSlug}`);
      return;
    }
    // Cart coming in Phase 7
    alert('Cart coming in Phase 7');
  };

  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 font-['Jost']">
        Select Size / Variant
      </p>
      <div className="flex flex-wrap gap-2 mb-5">
        {variants.map((v) => (
          <button
            key={v.id}
            onClick={() => setSelected(v)}
            className={`px-4 py-2.5 rounded-xl border text-sm font-['Jost'] transition-all duration-150 cursor-pointer min-h-[48px] ${
              selected.id === v.id
                ? 'border-orange-500 bg-orange-50 text-orange-700 font-semibold'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
            }`}
          >
            {v.name}
          </button>
        ))}
      </div>

      <div className="flex items-baseline gap-3 mb-6">
        <span className="text-3xl font-bold text-slate-900 font-['Jost']">
          ₹{parseFloat(selected.effective_price).toFixed(0)}
        </span>
        {selected.sale_price && (
          <span className="text-slate-400 line-through text-base font-['Jost']">
            ₹{parseFloat(selected.price).toFixed(0)}
          </span>
        )}
        {selected.sale_price && (
          <span className="text-green-600 text-sm font-medium font-['Jost']">
            {Math.round((1 - parseFloat(selected.sale_price) / parseFloat(selected.price)) * 100)}% off
          </span>
        )}
      </div>

      <button
        onClick={handleAddToCart}
        className="w-full bg-orange-500 hover:bg-orange-600 active:bg-orange-700 text-white font-semibold py-4 rounded-xl font-['Jost'] text-base transition-colors cursor-pointer min-h-[52px]"
      >
        Add to Cart
      </button>
    </div>
  );
}
```

### Step 3: Create `frontend/app/(store)/products/[slug]/page.tsx`

Server component. In Next.js 16, `params` is a Promise — await it.

```tsx
import Link from 'next/link';
import { notFound } from 'next/navigation';
import VariantSelector from '@/components/product/VariantSelector';
import type { Product } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function getProduct(slug: string): Promise<Product | null> {
  const res = await fetch(`${BASE_URL}/api/v1/products/${slug}/`, {
    next: { revalidate: 60 },
  });
  if (res.status === 404) return null;
  if (!res.ok) return null;
  return res.json();
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) notFound();

  const activeVariants = product.variants.filter((v) => v.is_active);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header with back nav */}
      <header className="bg-white border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <Link
            href="/products"
            className="text-slate-500 hover:text-slate-700 transition-colors cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center -ml-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <nav className="flex items-center gap-2 text-sm text-slate-500 font-['Jost']">
            <Link href="/products" className="hover:text-orange-500 transition-colors">
              Products
            </Link>
            <span>/</span>
            <span className="text-slate-700">{product.category_name}</span>
          </nav>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100">
          <div className="md:grid md:grid-cols-2">
            {/* Image */}
            <div className="aspect-square bg-slate-50 flex items-center justify-center overflow-hidden">
              {product.images[0] ? (
                <img
                  src={product.images[0].image_url}
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <svg className="w-24 h-24 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0v10l-8 4m0-10L4 7m8 10V7" />
                </svg>
              )}
            </div>

            {/* Details */}
            <div className="p-6 flex flex-col gap-3">
              <div>
                <p className="text-xs text-orange-500 font-semibold uppercase tracking-wider mb-1 font-['Jost']">
                  {product.category_name}
                </p>
                <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900 leading-tight">
                  {product.name}
                </h1>
                {product.brand_name && (
                  <p className="text-sm text-slate-500 font-['Jost'] mt-1">by {product.brand_name}</p>
                )}
              </div>

              {product.description && (
                <p className="text-slate-600 font-['Jost'] text-sm leading-relaxed">
                  {product.description}
                </p>
              )}

              {activeVariants.length > 0 ? (
                <VariantSelector variants={activeVariants} productSlug={product.slug} />
              ) : (
                <p className="text-slate-400 font-['Jost'] text-sm">No variants available.</p>
              )}
            </div>
          </div>

          {/* Specifications */}
          {Object.keys(product.specifications).length > 0 && (
            <div className="border-t border-slate-100 p-6">
              <h2 className="font-['Bodoni_Moda'] text-lg font-bold text-slate-900 mb-4">
                Specifications
              </h2>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                {Object.entries(product.specifications).map(([key, value]) => (
                  <div key={key} className="bg-slate-50 rounded-xl p-3">
                    <p className="text-xs text-slate-400 font-['Jost'] mb-0.5 capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-slate-900 font-semibold font-['Jost'] text-sm">
                      {String(value)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

### Step 4: Verify compile

```bash
docker-compose logs frontend --tail=20
```

or if Docker isn't running:

```bash
cd frontend && npx tsc --noEmit
```

Confirm zero TypeScript errors.

## Report

Write full report to:
`/Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/.superpowers/sdd/task-8-report.md`

Return: Status (DONE/DONE_WITH_CONCERNS/BLOCKED), one-line summary, any concerns.
