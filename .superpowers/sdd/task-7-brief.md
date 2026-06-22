# Task 7: Product Listing Frontend Page

## Context

This is Task 7 of 9 in Plan 2 (Catalog). Tasks 1-6 are complete:
- Backend APIs for categories, brands, products, inventory are all live at `http://localhost:8000/api/v1/`
- Docker is running: `docker-compose up` already started

## Files to Create / Modify

- **Create:** `frontend/lib/types.ts`
- **Create:** `frontend/components/product/ProductCard.tsx`
- **Create:** `frontend/components/product/ProductGrid.tsx`
- **Create:** `frontend/app/(store)/products/page.tsx`
- **Modify:** `frontend/app/(store)/page.tsx`

## Global Constraints

- **No git in this project** — skip all commit steps
- Frontend: Next.js 14 App Router, TailwindCSS v4 (`@theme inline` in globals.css — no `tailwind.config.ts`)
- Fonts: Bodoni Moda headings (`font-['Bodoni_Moda']`), Jost body (`font-['Jost']`) — already loaded in globals.css
- Color palette: slate-50 background, orange-500 CTA, white cards, slate-900 headings
- Minimum touch target: 48px height on all interactive elements
- `searchParams` prop is available in Next.js 14 server components (page.tsx)
- **AGENTS.md says**: "This version has breaking changes — read `node_modules/next/dist/docs/` before writing any code." Honor this: check the Next.js docs before writing page files.

## Existing Frontend Structure

```
frontend/
  app/
    layout.tsx         ← root layout (exists)
    (store)/
      page.tsx         ← home page placeholder (MODIFY this)
    (auth)/            ← login pages (exists, don't touch)
  lib/
    api.ts             ← apiFetch() with auth + token refresh (exists)
    auth.ts            ← token storage helpers (exists)
  store/
    auth.ts            ← Zustand auth store (exists)
  components/
    ui/                ← existing UI components (don't touch)
```

## Step-by-Step Implementation

### Step 1: Check Next.js docs (per AGENTS.md)

Read the relevant Next.js 14 guide before writing code:
```
frontend/node_modules/next/dist/docs/
```

Look for notes on App Router, server components, searchParams, and page.tsx conventions.

### Step 2: Create `frontend/lib/types.ts`

```typescript
export interface Category {
  id: number;
  name: string;
  slug: string;
  image: string;
  parent: number | null;
  is_active: boolean;
  created_at: string;
}

export interface ProductVariant {
  id: number;
  name: string;
  sku: string;
  price: string;
  sale_price: string | null;
  effective_price: string;
  is_active: boolean;
}

export interface ProductImage {
  id: number;
  variant: number | null;
  image_url: string;
  sort_order: number;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  specifications: Record<string, string>;
  category: number;
  category_name: string;
  brand: number | null;
  brand_name: string | null;
  is_active: boolean;
  created_at: string;
  variants: ProductVariant[];
  images: ProductImage[];
}

export interface Brand {
  id: number;
  name: string;
  slug: string;
  logo: string;
  is_active: boolean;
  created_at: string;
}
```

### Step 3: Create component directories

```bash
mkdir -p frontend/components/product
mkdir -p frontend/components/admin
mkdir -p "frontend/app/(store)/products"
```

Run from the project root: `/Users/sahil/src/my_idea/shared_tenant_home_delivery_interface`

### Step 4: Create `frontend/components/product/ProductCard.tsx`

```tsx
import Link from 'next/link';
import type { Product } from '@/lib/types';

export default function ProductCard({ product }: { product: Product }) {
  const lowestPrice = product.variants.reduce<string | null>((min, v) => {
    const price = v.effective_price;
    return min === null || parseFloat(price) < parseFloat(min) ? price : min;
  }, null);

  const image = product.images[0]?.image_url;

  return (
    <Link
      href={`/products/${product.slug}`}
      className="group block bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-100 hover:shadow-md transition-shadow duration-200 cursor-pointer"
    >
      <div className="aspect-square bg-slate-50 flex items-center justify-center overflow-hidden">
        {image ? (
          <img
            src={image}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <svg className="w-16 h-16 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0v10l-8 4m0-10L4 7m8 10V7" />
          </svg>
        )}
      </div>
      <div className="p-4">
        <p className="text-xs text-orange-500 font-medium mb-1 font-['Jost'] uppercase tracking-wide">
          {product.category_name}
        </p>
        <h3 className="text-slate-900 font-medium leading-snug mb-2 font-['Jost'] line-clamp-2 text-sm">
          {product.name}
        </h3>
        {lowestPrice && (
          <p className="text-base font-semibold text-slate-800 font-['Jost']">
            ₹{parseFloat(lowestPrice).toFixed(0)}
            {product.variants.length > 1 && (
              <span className="text-xs font-normal text-slate-500"> onwards</span>
            )}
          </p>
        )}
        {!lowestPrice && (
          <p className="text-sm text-slate-400 font-['Jost']">Price on request</p>
        )}
      </div>
    </Link>
  );
}
```

### Step 5: Create `frontend/components/product/ProductGrid.tsx`

```tsx
import ProductCard from './ProductCard';
import type { Product } from '@/lib/types';

export default function ProductGrid({ products }: { products: Product[] }) {
  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <svg className="w-16 h-16 text-slate-200 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p className="text-slate-400 font-['Jost'] text-sm">No products found in this category.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
```

### Step 6: Create `frontend/app/(store)/products/page.tsx`

Server component — use `fetch()` directly (not `apiFetch`; no auth needed for public endpoints).

```tsx
import Link from 'next/link';
import ProductGrid from '@/components/product/ProductGrid';
import type { Product, Category } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function getProducts(categorySlug?: string): Promise<Product[]> {
  const url = categorySlug
    ? `${BASE_URL}/api/v1/products/?category=${encodeURIComponent(categorySlug)}`
    : `${BASE_URL}/api/v1/products/`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) return [];
  return res.json();
}

async function getCategories(): Promise<Category[]> {
  const res = await fetch(`${BASE_URL}/api/v1/categories/`, { next: { revalidate: 300 } });
  if (!res.ok) return [];
  return res.json();
}

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: { category?: string };
}) {
  const [products, categories] = await Promise.all([
    getProducts(searchParams.category),
    getCategories(),
  ]);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="font-['Bodoni_Moda'] text-xl font-bold text-slate-900">
            Hardware Store
          </Link>
          <Link
            href="/login"
            className="text-sm text-slate-600 font-['Jost'] hover:text-orange-500 transition-colors min-h-[44px] flex items-center"
          >
            Login
          </Link>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <h1 className="font-['Bodoni_Moda'] text-2xl font-bold text-slate-900 mb-6">Products</h1>

        <div className="md:flex md:gap-6">
          {/* Desktop category sidebar */}
          <aside className="hidden md:block w-48 shrink-0">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 font-['Jost']">
              Categories
            </h2>
            <nav className="space-y-0.5">
              <Link
                href="/products"
                className={`block px-3 py-2.5 rounded-xl text-sm font-['Jost'] transition-colors ${
                  !searchParams.category
                    ? 'bg-orange-50 text-orange-600 font-semibold'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                All Products
              </Link>
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  href={`/products?category=${cat.slug}`}
                  className={`block px-3 py-2.5 rounded-xl text-sm font-['Jost'] transition-colors ${
                    searchParams.category === cat.slug
                      ? 'bg-orange-50 text-orange-600 font-semibold'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {cat.name}
                </Link>
              ))}
            </nav>
          </aside>

          <div className="flex-1 min-w-0">
            {/* Mobile category chip strip */}
            <div className="md:hidden overflow-x-auto -mx-4 px-4 mb-4">
              <div className="flex gap-2 pb-2 w-max">
                <Link
                  href="/products"
                  className={`shrink-0 px-4 py-2 rounded-full text-sm font-['Jost'] transition-colors min-h-[44px] flex items-center ${
                    !searchParams.category
                      ? 'bg-orange-500 text-white font-medium'
                      : 'bg-white text-slate-600 border border-slate-200'
                  }`}
                >
                  All
                </Link>
                {categories.map((cat) => (
                  <Link
                    key={cat.id}
                    href={`/products?category=${cat.slug}`}
                    className={`shrink-0 px-4 py-2 rounded-full text-sm font-['Jost'] transition-colors min-h-[44px] flex items-center ${
                      searchParams.category === cat.slug
                        ? 'bg-orange-500 text-white font-medium'
                        : 'bg-white text-slate-600 border border-slate-200'
                    }`}
                  >
                    {cat.name}
                  </Link>
                ))}
              </div>
            </div>

            <ProductGrid products={products} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

### Step 7: Replace `frontend/app/(store)/page.tsx`

```tsx
import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-slate-50 gap-8 px-4">
      <div className="text-center">
        <h1 className="font-['Bodoni_Moda'] text-4xl font-bold text-slate-900 mb-2">
          Hardware Store
        </h1>
        <p className="text-slate-500 font-['Jost']">
          Quality hardware & sanitary delivered to your door
        </p>
      </div>
      <Link
        href="/products"
        className="bg-orange-500 text-white px-8 py-4 rounded-xl font-['Jost'] font-semibold text-lg hover:bg-orange-600 transition-colors min-h-[52px] flex items-center"
      >
        Browse Products
      </Link>
    </main>
  );
}
```

### Step 8: Verify the pages compile

```bash
docker-compose logs frontend --tail=30
```

Confirm no compile errors in the Next.js dev server output.

## Report

Write your full report to:
`/Users/sahil/src/my_idea/shared_tenant_home_delivery_interface/.superpowers/sdd/task-7-report.md`

Return only:
- Status: DONE / DONE_WITH_CONCERNS / BLOCKED
- One-line summary of what was built
- Any TypeScript errors, Next.js version quirks, or concerns
