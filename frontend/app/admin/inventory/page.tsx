"use client";
import { useEffect, useState } from "react";
import { products, inventory } from "@/lib/api";
import type { Product, InventoryItem } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";

export default function AdminInventoryPage() {
  const [productList, setProductList] = useState<Product[]>([]);
  const [inv, setInv] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [edits, setEdits] = useState<Record<number, number>>({});
  const [saving, setSaving] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([products.list(), inventory.list()])
      .then(([p, i]) => { setProductList(p); setInv(i); })
      .finally(() => setLoading(false));
  }, []);

  const invMap = Object.fromEntries(inv.map((i) => [i.variant_id, i]));

  async function saveQty(variantId: number) {
    const qty = edits[variantId];
    if (qty === undefined) return;
    setSaving(variantId);
    try {
      const updated = await inventory.update(variantId, qty);
      setInv((prev) => prev.map((i) => i.variant_id === variantId ? updated : i));
      setEdits((p) => { const n = { ...p }; delete n[variantId]; return n; });
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner /></div>;

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 mb-4">Inventory</h1>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 border-b border-gray-200">
            <tr>
              {["Product", "Variant", "Available", "Reserved", "Update"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {productList.flatMap((p) =>
              p.variants.map((v) => {
                const stock = invMap[v.id];
                return (
                  <tr key={v.id} className="border-b border-gray-100 last:border-0 hover:bg-zinc-50">
                    <td className="px-4 py-3 text-gray-700">{p.name}</td>
                    <td className="px-4 py-3 text-gray-500">{v.name}</td>
                    <td className="px-4 py-3">
                      <span className={`font-semibold ${(stock?.available_qty ?? 0) === 0 ? "text-red-600" : "text-green-700"}`}>
                        {stock?.available_qty ?? 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{stock?.reserved_qty ?? 0}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min={0}
                          value={edits[v.id] ?? stock?.available_qty ?? 0}
                          onChange={(e) => setEdits((p) => ({ ...p, [v.id]: Number(e.target.value) }))}
                          className="w-20 border border-gray-300 rounded-lg px-2 py-1 text-sm outline-none"
                        />
                        {edits[v.id] !== undefined && (
                          <Button variant="secondary" onClick={() => saveQty(v.id)} loading={saving === v.id} className="py-1 text-xs">
                            Save
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
