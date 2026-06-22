"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { orders } from "@/lib/api";
import type { Order } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

export default function OrdersPage() {
  const router = useRouter();
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const [list, setList] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn) { router.push("/login"); return; }
    orders.list().then(setList).finally(() => setLoading(false));
  }, [isLoggedIn]);

  if (loading) return <div className="flex justify-center py-16"><Spinner /></div>;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Orders</h1>
      {list.length === 0 ? (
        <p className="text-gray-400 text-center py-16">No orders yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {list.map((order) => (
            <Link key={order.id} href={`/orders/${order.id}`}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-xl hover:border-gray-300 transition-colors">
              <div>
                <p className="text-sm font-semibold text-gray-900">Order #{order.id}</p>
                <p className="text-xs text-gray-400 mt-0.5">{new Date(order.created_at).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-gray-900">₹{order.total_amount}</span>
                <Badge status={order.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
