import Link from "next/link";
import { products } from "@/lib/api";
import { ProductCard } from "@/components/product/ProductCard";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const items = await products.list().catch(() => []);
  const featured = items.slice(0, 8);

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white py-20 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-10">
          <div className="flex-1">
            <span className="inline-block px-3 py-1 bg-orange-500/20 text-orange-400 text-xs font-semibold rounded-full mb-4 uppercase tracking-wider">Free delivery · 500+ products</span>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-4" style={{fontFamily:"'Rubik',sans-serif"}}>
              Hardware &<br />
              <span className="text-orange-500">Sanitary</span> Supplies
            </h1>
            <p className="text-slate-300 text-lg mb-8 max-w-md">
              Pipes, fittings, taps, tiles, and more — delivered to your door.
            </p>
            <div className="flex gap-3 flex-wrap">
              <Link href="/products" className="px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors text-sm">
                Browse Products
              </Link>
            </div>
          </div>
          <div className="hidden md:flex gap-4">
            {[
              { icon: "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16", label: "Pipes & Fittings" },
              { icon: "M13 10V3L4 14h7v7l9-11h-7z", label: "Electrical" },
              { icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6", label: "Sanitary Ware" },
            ].map((item) => (
              <div key={item.label} className="w-28 h-28 bg-slate-800 border border-slate-700 rounded-2xl flex flex-col items-center justify-center gap-2 hover:border-orange-500/50 transition-colors cursor-pointer">
                <svg className="w-8 h-8 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={item.icon} />
                </svg>
                <span className="text-xs text-slate-400 text-center px-2">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust bar */}
      <section className="bg-orange-500 text-white py-3">
        <div className="max-w-6xl mx-auto px-4 flex flex-wrap justify-center gap-8 text-sm font-medium">
          {["Same-day dispatch", "Genuine brands", "Bulk pricing available", "Easy returns"].map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              {t}
            </span>
          ))}
        </div>
      </section>

      {/* Products */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900" style={{fontFamily:"'Rubik',sans-serif"}}>Featured Products</h2>
          <Link href="/products" className="text-sm text-orange-500 hover:text-orange-600 font-semibold">View all →</Link>
        </div>
        {featured.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-slate-200">
            <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p className="text-slate-500 font-medium">No products yet</p>
            <p className="text-slate-400 text-sm mt-1">Products added via the admin panel will appear here.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {featured.map((p) => <ProductCard key={p.id} product={p} />)}
          </div>
        )}
      </section>
    </div>
  );
}
