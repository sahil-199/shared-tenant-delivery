import { products, categories, brands } from "@/lib/api";
import { ProductCard } from "@/components/product/ProductCard";
import { SortSelect } from "@/components/product/SortSelect";

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; category?: string; sort?: string }>;
}) {
  const params = await searchParams;
  const [items, cats, brs] = await Promise.all([
    products.list({
      search: params.search,
      category: params.category ? Number(params.category) : undefined,
      sort: params.sort,
    }).catch(() => []),
    categories.list().catch(() => []),
    brands.list().catch(() => []),
  ]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row gap-6">
        {/* Filters sidebar */}
        <aside className="w-full md:w-48 shrink-0">
          <h2 className="font-semibold text-gray-900 mb-3">Categories</h2>
          <div className="flex flex-col gap-1">
            <a href="/products" className="text-sm text-gray-600 hover:text-blue-600 py-1">All products</a>
            {cats.map((c) => (
              <a key={c.id} href={`/products?category=${c.id}`} className="text-sm text-gray-600 hover:text-blue-600 py-1">{c.name}</a>
            ))}
          </div>
        </aside>
        {/* Grid */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">{items.length} products</p>
            <SortSelect current={params.sort} category={params.category} />
          </div>
          {items.length === 0 ? (
            <p className="text-gray-400 text-center py-16">No products found.</p>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {items.map((p) => <ProductCard key={p.id} product={p} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
