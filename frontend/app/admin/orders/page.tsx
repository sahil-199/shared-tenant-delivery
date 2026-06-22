"use client";
import { useEffect, useState } from "react";
import { orders } from "@/lib/api";
import type { Order } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

const ORDER_STATUSES = ["placed", "pending_confirmation", "confirmed", "processing", "out_for_delivery", "delivered", "cancelled"];

export default function AdminOrdersPage() {
  const [list, setList] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<number | null>(null);

  useEffect(() => {
    orders.list().then(setList).finally(() => setLoading(false));
  }, []);

  async function changeStatus(id: number, status: string) {
    setUpdating(id);
    try {
      const updated = await orders.updateStatus(id, status);
      setList((prev) => prev.map((o) => (o.id === id ? updated : o)));
    } finally {
      setUpdating(null);
    }
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner /></div>;

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 mb-4">Orders</h1>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-zinc-50 border-b border-gray-200">
            <tr>
              {["Order", "Customer", "Items", "Total", "Status", "Action"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {list.map((order) => (
              <tr key={order.id} className="border-b border-gray-100 last:border-0 hover:bg-zinc-50">
                <td className="px-4 py-3 font-medium">#{order.id}</td>
                <td className="px-4 py-3 text-gray-600">{order.address.city}</td>
                <td className="px-4 py-3 text-gray-600">{order.items.length} item(s)</td>
                <td className="px-4 py-3 font-semibold">₹{order.total_amount}</td>
                <td className="px-4 py-3"><Badge status={order.status} /></td>
                <td className="px-4 py-3">
                  <select
                    value={order.status}
                    disabled={updating === order.id}
                    onChange={(e) => changeStatus(order.id, e.target.value)}
                    className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 outline-none disabled:opacity-50"
                  >
                    {ORDER_STATUSES.map((s) => (
                      <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {list.length === 0 && <p className="text-center py-12 text-gray-400">No orders yet.</p>}
      </div>
    </div>
  );
}
