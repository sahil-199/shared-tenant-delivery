"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { orders } from "@/lib/api";
import type { Order } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Badge } from "@/components/ui/Badge";
import { OrderTimeline } from "@/components/order/OrderTimeline";
import { Spinner } from "@/components/ui/Spinner";

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoggedIn) { router.push("/login"); return; }
    orders.get(Number(id)).then(setOrder).finally(() => setLoading(false));
  }, [id, isLoggedIn]);

  if (loading) return <div className="flex justify-center py-16"><Spinner /></div>;
  if (!order) return <p className="text-center py-16 text-gray-400">Order not found.</p>;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Order #{order.id}</h1>
          <p className="text-sm text-gray-400">{new Date(order.created_at).toLocaleString()}</p>
        </div>
        <Badge status={order.status} />
      </div>
      <div className="mb-6">
        <OrderTimeline status={order.status} />
      </div>
      <section className="bg-zinc-50 rounded-xl p-4 mb-4">
        <h2 className="font-semibold text-gray-900 mb-3">Items</h2>
        {order.items.map((item) => (
          <div key={item.id} className="flex justify-between text-sm py-1.5 border-b border-gray-100 last:border-0">
            <span className="text-gray-700">{item.variant_name} × {item.qty}</span>
            <span className="font-medium">₹{(parseFloat(item.unit_price) * item.qty).toFixed(2)}</span>
          </div>
        ))}
        <div className="flex justify-between font-bold pt-2 mt-1">
          <span>Total</span><span>₹{order.total_amount}</span>
        </div>
      </section>
      <section className="border border-gray-200 rounded-xl p-4">
        <h2 className="font-semibold text-gray-900 mb-2">Delivery Address</h2>
        <p className="text-sm text-gray-600">
          {order.address.line1}<br />
          {order.address.line2 && <>{order.address.line2}<br /></>}
          {order.address.city}, {order.address.state} — {order.address.pin_code}
        </p>
      </section>
    </div>
  );
}
