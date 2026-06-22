"use client";
import Link from "next/link";
import { Product } from "@/lib/api";
import { useCartStore } from "@/store/cart";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function ProductCard({ product }: { product: Product }) {
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const addItem = useCartStore((s) => s.addItem);
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const router = useRouter();
  const variant = product.variants[0];
  const image = product.images[0]?.image_url;
  const hasDiscount = variant?.sale_price != null;

  async function handleAdd() {
    if (!isLoggedIn) { router.push("/login"); return; }
    if (!variant) return;
    setAdding(true);
    try {
      await addItem(variant.id, 1);
      setAdded(true);
      setTimeout(() => setAdded(false), 1500);
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="group bg-white border border-slate-200 rounded-2xl overflow-hidden hover:shadow-lg hover:border-orange-200 transition-all duration-200">
      <Link href={`/products/${product.id}`}>
        <div className="aspect-square bg-slate-50 overflow-hidden relative">
          {image ? (
            <img src={image} alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <svg className="w-16 h-16 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
          )}
          {hasDiscount && (
            <span className="absolute top-2 left-2 bg-orange-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-md">SALE</span>
          )}
        </div>
        <div className="p-3 pb-2">
          <p className="text-[11px] font-semibold text-orange-500 uppercase tracking-wide mb-0.5">{product.category_name}</p>
          <h3 className="text-sm font-semibold text-slate-800 line-clamp-2 leading-snug">{product.name}</h3>
          {variant && (
            <div className="flex items-baseline gap-1.5 mt-2">
              <span className="text-base font-bold text-slate-900">₹{variant.effective_price}</span>
              {variant.sale_price && (
                <span className="text-xs text-slate-400 line-through">₹{variant.price}</span>
              )}
            </div>
          )}
        </div>
      </Link>
      {variant && (
        <div className="px-3 pb-3">
          <button
            onClick={handleAdd}
            disabled={adding || added}
            className={`w-full py-2 text-sm font-semibold rounded-xl transition-all duration-200 cursor-pointer disabled:cursor-not-allowed
              ${added
                ? "bg-green-500 text-white"
                : "bg-orange-500 hover:bg-orange-600 text-white disabled:opacity-60"
              }`}
          >
            {added ? "✓ Added" : adding ? "Adding…" : "Add to Cart"}
          </button>
        </div>
      )}
    </div>
  );
}
