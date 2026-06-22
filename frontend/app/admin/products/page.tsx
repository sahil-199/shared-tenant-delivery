"use client";
import { useEffect, useState } from "react";
import { products } from "@/lib/api";
import type { Product } from "@/lib/api";
import { Spinner } from "@/components/ui/Spinner";
import { Badge } from "@/components/ui/Badge";

export default function AdminProductsPage() {
  const [list, setList] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    products.list().then(setList).finally(() => setLoading(false));
  }, []);

  const filtered = list.filter((p) =>
    !search || p.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="flex justify-center py-16"><Spinner /></div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-900">Products</h1>
        <input
          type="search"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="text-sm border border-gray-300 rounded-lg px-3 py-2 outline-none w-56"
        />
      </div>
      <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 border-b border-gray-200">
            <tr>
              {["Product", "Category", "Brand", "Variants", "Status"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id} className="border-b border-gray-100 last:border-0 hover:bg-zinc-50">
                <td className="px-4 py-3 font-medium">{p.name}</td>
                <td className="px-4 py-3 text-gray-500">{p.category_name}</td>
                <td className="px-4 py-3 text-gray-500">{p.brand_name ?? "—"}</td>
                <td className="px-4 py-3 text-gray-500">{p.variants.length}</td>
                <td className="px-4 py-3">
                  <Badge status={p.is_active ? "active" : "inactive"} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && <p className="text-center py-12 text-gray-400">No products found.</p>}
      </div>
    </div>
  );
}
