"use client";
import Link from "next/link";
import { Product } from "@/lib/api";
import { useCartStore } from "@/store/cart";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useToastStore } from "@/store/toast";

export function ProductCard({ product }: { product: Product }) {
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const addItem = useCartStore((s) => s.addItem);
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const showToast = useToastStore((s) => s.show);
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
      showToast(`${product.name} added to cart`);
      setTimeout(() => setAdded(false), 1500);
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="group bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-slate-100 hover:border-orange-200 flex flex-col">
      <Link href={`/products/${product.id}`} className="block">
        <div className="relative overflow-hidden bg-slate-50" style={{ aspectRatio: "4/3" }}>
          {image ? (
            <img
              src={image}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center gap-2">
              <svg className="w-12 h-12 text-slate-200" fill="currentColor" viewBox="0 0 24 24">
                <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z" />
              </svg>
            </div>
          )}
          {hasDiscount && (
            <span className="absolute top-2 left-2 bg-orange-500 text-white text-[10px] font-bold px-2 py-1 rounded-lg tracking-wide">SALE</span>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </div>
        <div className="p-4 pb-2">
          <p className="text-[10px] font-bold text-orange-500 uppercase tracking-widest mb-1">{product.category_name}</p>
          <h3 className="text-sm font-semibold text-slate-800 line-clamp-2 leading-snug min-h-[2.5rem]">{product.name}</h3>
          {variant && (
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-lg font-extrabold text-slate-900">₹{variant.effective_price}</span>
              {variant.sale_price && (
                <span className="text-xs text-slate-400 line-through font-medium">₹{variant.price}</span>
              )}
            </div>
          )}
        </div>
      </Link>
      {variant && (
        <div className="px-4 pb-4 mt-auto">
          <button
            onClick={handleAdd}
            disabled={adding || added}
            className={`w-full py-2.5 text-sm font-bold rounded-xl transition-all duration-200 cursor-pointer disabled:cursor-not-allowed tracking-wide
              ${added
                ? "bg-green-500 text-white scale-95"
                : "bg-orange-500 hover:bg-orange-600 active:scale-95 text-white disabled:opacity-60"
              }`}
          >
            {added ? "✓ Added to cart" : adding ? "Adding…" : "Add to Cart"}
          </button>
        </div>
      )}
    </div>
  );
}
