"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { addresses, orders, payments } from "@/lib/api";
import type { Address } from "@/lib/api";
import { useCartStore } from "@/store/cart";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, clearCart } = useCartStore();
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const [addressList, setAddressList] = useState<Address[]>([]);
  const [selectedAddress, setSelectedAddress] = useState<number | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<"cod" | "razorpay">("cod");
  const [newAddr, setNewAddr] = useState({ line1: "", line2: "", city: "", state: "", pin_code: "" });
  const [showNewAddr, setShowNewAddr] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn) { router.push("/login"); return; }
    addresses.list().then((list) => {
      setAddressList(list);
      const def = list.find((a) => a.is_default) ?? list[0];
      if (def) setSelectedAddress(def.id);
      else setShowNewAddr(true);
    });
  }, [isLoggedIn]);

  async function saveNewAddress() {
    const addr = await addresses.create(newAddr);
    setAddressList((prev) => [...prev, addr]);
    setSelectedAddress(addr.id);
    setShowNewAddr(false);
  }

  async function placeOrder() {
    if (!selectedAddress) { setError("Select a delivery address."); return; }
    setLoading(true); setError("");
    try {
      const order = await orders.create(selectedAddress);
      await payments.initiate(order.id, paymentMethod);
      clearCart();
      router.push(`/orders/${order.id}`);
    } catch (err: unknown) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Failed to place order.");
    } finally {
      setLoading(false);
    }
  }

  if (!cart?.items.length) return (
    <div className="max-w-lg mx-auto px-4 py-16 text-center">
      <p className="text-gray-500">Your cart is empty.</p>
      <a href="/products" className="text-blue-600 text-sm hover:underline mt-2 block">Browse products</a>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Checkout</h1>
      {/* Order summary */}
      <section className="bg-zinc-50 rounded-xl p-4 mb-6">
        <h2 className="font-semibold text-gray-900 mb-3">Order Summary</h2>
        {cart.items.map((item) => (
          <div key={item.id} className="flex justify-between text-sm py-1">
            <span className="text-gray-700">{item.product_name} — {item.variant_name} × {item.qty}</span>
            <span className="font-medium">₹{item.subtotal}</span>
          </div>
        ))}
        <div className="flex justify-between font-semibold pt-2 border-t border-gray-200 mt-2">
          <span>Total</span><span>₹{cart.total}</span>
        </div>
      </section>
      {/* Delivery address */}
      <section className="mb-6">
        <h2 className="font-semibold text-gray-900 mb-3">Delivery Address</h2>
        {addressList.map((addr) => (
          <label key={addr.id} className={`flex gap-3 p-3 rounded-xl border cursor-pointer mb-2 transition-colors ${selectedAddress === addr.id ? "border-blue-600 bg-blue-50" : "border-gray-200 hover:border-gray-300"}`}>
            <input type="radio" name="address" value={addr.id} checked={selectedAddress === addr.id} onChange={() => setSelectedAddress(addr.id)} className="mt-0.5" />
            <span className="text-sm text-gray-700">{addr.line1}, {addr.city}, {addr.state} — {addr.pin_code}</span>
          </label>
        ))}
        {showNewAddr ? (
          <div className="border border-gray-200 rounded-xl p-4 flex flex-col gap-3">
            <Input label="Address line 1" value={newAddr.line1} onChange={(e) => setNewAddr((p) => ({ ...p, line1: e.target.value }))} required />
            <Input label="Address line 2 (optional)" value={newAddr.line2} onChange={(e) => setNewAddr((p) => ({ ...p, line2: e.target.value }))} />
            <div className="grid grid-cols-2 gap-3">
              <Input label="City" value={newAddr.city} onChange={(e) => setNewAddr((p) => ({ ...p, city: e.target.value }))} required />
              <Input label="State" value={newAddr.state} onChange={(e) => setNewAddr((p) => ({ ...p, state: e.target.value }))} required />
            </div>
            <Input label="Pin code" value={newAddr.pin_code} onChange={(e) => setNewAddr((p) => ({ ...p, pin_code: e.target.value }))} required />
            <Button variant="secondary" onClick={saveNewAddress} type="button">Save Address</Button>
          </div>
        ) : (
          <button onClick={() => setShowNewAddr(true)} className="text-sm text-blue-600 hover:underline mt-1">+ Add new address</button>
        )}
      </section>
      {/* Payment method */}
      <section className="mb-6">
        <h2 className="font-semibold text-gray-900 mb-3">Payment Method</h2>
        {(["cod", "razorpay"] as const).map((m) => (
          <label key={m} className={`flex gap-3 p-3 rounded-xl border cursor-pointer mb-2 ${paymentMethod === m ? "border-blue-600 bg-blue-50" : "border-gray-200"}`}>
            <input type="radio" name="payment" value={m} checked={paymentMethod === m} onChange={() => setPaymentMethod(m)} />
            <span className="text-sm text-gray-700">{m === "cod" ? "Cash on Delivery" : "Razorpay (UPI / Card)"}</span>
          </label>
        ))}
      </section>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      <Button onClick={placeOrder} loading={loading} className="w-full py-3 text-base">Place Order</Button>
    </div>
  );
}
