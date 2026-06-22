"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { useCartStore } from "@/store/cart";
import { useAuthStore } from "@/store/auth";

export default function StoreLayout({ children }: { children: React.ReactNode }) {
  const [cartOpen, setCartOpen] = useState(false);
  const router = useRouter();
  const itemCount = useCartStore((s) => s.itemCount);
  const { isLoggedIn, isOwner, logout } = useAuthStore();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-30 bg-slate-900 shadow-lg">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-orange-500 rounded-xl flex items-center justify-center overflow-hidden">
              <svg className="w-5 h-5 text-white wrench-animate" fill="currentColor" viewBox="0 0 24 24">
                <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z" />
              </svg>
            </div>
            <span className="font-bold text-lg text-white tracking-tight" style={{fontFamily:"'Rubik',sans-serif"}}>Sanjay Hardware</span>
          </Link>

          {/* Nav */}
          <nav className="hidden md:flex items-center gap-2">
            <Link href="/products" className="px-4 py-2 text-sm font-semibold text-white bg-slate-700/60 hover:bg-orange-500 rounded-lg transition-all duration-200">Products</Link>
            {isLoggedIn && <Link href="/orders" className="px-4 py-2 text-sm font-semibold text-white bg-slate-700/60 hover:bg-orange-500 rounded-lg transition-all duration-200">Orders</Link>}
            {isLoggedIn && <Link href="/account" className="px-4 py-2 text-sm font-semibold text-white bg-slate-700/60 hover:bg-orange-500 rounded-lg transition-all duration-200">Account</Link>}
            {isOwner && <Link href="/admin/orders" className="px-4 py-2 text-sm font-semibold text-orange-400 border border-orange-500/40 hover:bg-orange-500 hover:text-white rounded-lg transition-all duration-200">Admin</Link>}
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {isLoggedIn ? (
              <>
                <button
                  onClick={() => setCartOpen(true)}
                  className="relative p-2.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                  aria-label="Open cart"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  {itemCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-orange-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">{itemCount}</span>
                  )}
                </button>
                <button onClick={handleLogout} className="px-3 py-2 text-sm text-slate-400 hover:text-white transition-colors cursor-pointer">Logout</button>
              </>
            ) : (
              <Link href="/login" className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold rounded-lg transition-colors">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main>{children}</main>

      <footer className="bg-slate-900 text-slate-400 text-sm py-8 mt-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p>© 2026 Sanjay Hardware · Quality hardware & sanitary products</p>
        </div>
      </footer>

      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} />
    </div>
  );
}
