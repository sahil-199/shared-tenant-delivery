"use client";
import { useEffect } from "react";
import Link from "next/link";
import { useCartStore } from "@/store/cart";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";

export function CartDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { cart, loading, loadCart, updateItem, removeItem } = useCartStore();
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);

  useEffect(() => {
    if (open && isLoggedIn) loadCart();
  }, [open, isLoggedIn]);

  return (
    <>
      {open && <div className="fixed inset-0 bg-black/30 z-40" onClick={onClose} />}
      <div className={`fixed right-0 top-0 h-full w-full max-w-sm bg-white z-50 shadow-xl transition-transform duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}>
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold text-gray-900">Cart</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
        </div>
        <div className="flex flex-col h-[calc(100%-130px)] overflow-y-auto p-4 gap-4">
          {loading && <div className="flex justify-center py-8"><Spinner /></div>}
          {!loading && !cart?.items.length && (
            <p className="text-gray-500 text-sm text-center py-8">Your cart is empty.</p>
          )}
          {cart?.items.map((item) => (
            <div key={item.id} className="flex gap-3">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{item.product_name}</p>
                <p className="text-xs text-gray-500">{item.variant_name}</p>
                <p className="text-sm font-semibold mt-1">₹{item.subtotal}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => item.qty > 1 ? updateItem(item.id, item.qty - 1) : removeItem(item.id)}
                  className="w-7 h-7 rounded-full border border-gray-300 text-gray-600 hover:bg-gray-50 flex items-center justify-center text-sm">−</button>
                <span className="w-6 text-center text-sm">{item.qty}</span>
                <button onClick={() => updateItem(item.id, item.qty + 1)}
                  className="w-7 h-7 rounded-full border border-gray-300 text-gray-600 hover:bg-gray-50 flex items-center justify-center text-sm">+</button>
              </div>
            </div>
          ))}
        </div>
        {cart && cart.items.length > 0 && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-white">
            <div className="flex justify-between text-sm font-semibold mb-3">
              <span>Total</span><span>₹{cart.total}</span>
            </div>
            <Link href="/checkout" onClick={onClose}>
              <Button className="w-full">Proceed to Checkout</Button>
            </Link>
          </div>
        )}
      </div>
    </>
  );
}
