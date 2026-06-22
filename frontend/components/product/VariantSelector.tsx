"use client";
import { useState } from "react";
import { ProductVariant } from "@/lib/api";
import { useCartStore } from "@/store/cart";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";

export function VariantSelector({ variants }: { variants: ProductVariant[] }) {
  const [selected, setSelected] = useState(variants[0]?.id ?? null);
  const [adding, setAdding] = useState(false);
  const addItem = useCartStore((s) => s.addItem);
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const router = useRouter();
  const variant = variants.find((v) => v.id === selected);

  async function handleAdd() {
    if (!isLoggedIn) { router.push("/login"); return; }
    if (!selected) return;
    setAdding(true);
    try { await addItem(selected, 1); } finally { setAdding(false); }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        {variants.map((v) => (
          <button key={v.id} onClick={() => setSelected(v.id)}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${selected === v.id ? "border-blue-600 bg-blue-50 text-blue-700" : "border-gray-300 text-gray-700 hover:border-gray-400"}`}>
            {v.name}
          </button>
        ))}
      </div>
      {variant && (
        <div>
          <p className="text-2xl font-bold text-gray-900">
            ₹{variant.effective_price}
            {variant.sale_price && <span className="ml-2 text-base text-gray-400 line-through font-normal">₹{variant.price}</span>}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">SKU: {variant.sku}</p>
        </div>
      )}
      <Button onClick={handleAdd} loading={adding} className="w-full md:w-auto">
        Add to Cart
      </Button>
    </div>
  );
}
