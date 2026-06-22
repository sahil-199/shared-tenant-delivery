"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { Toast } from "@/components/ui/Toast";
import { useCartStore } from "@/store/cart";
import { useAuthStore } from "@/store/auth";

// ponytail: update this to the real WhatsApp number
const WHATSAPP = "919999999999";

export default function StoreLayout({ children }: { children: React.ReactNode }) {
  const [cartOpen, setCartOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const router = useRouter();
  const itemCount = useCartStore((s) => s.itemCount);
  const { isLoggedIn, isOwner, logout } = useAuthStore();

  function handleLogout() {
    logout();
    setMenuOpen(false);
    router.push("/login");
  }

  const navLinks = [
    { href: "/products", label: "Products", always: true },
    { href: "/orders", label: "Orders", always: false },
    { href: "/account", label: "Account", always: false },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-30 bg-slate-900 shadow-lg">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 shrink-0">
            <div className="w-9 h-9 bg-orange-500 rounded-xl flex items-center justify-center overflow-hidden">
              <svg className="w-5 h-5 text-white wrench-animate" fill="currentColor" viewBox="0 0 24 24">
                <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z" />
              </svg>
            </div>
            <span className="font-bold text-lg text-white tracking-tight" style={{fontFamily:"'Rubik',sans-serif"}}>Sanjay Hardware</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map(({ href, label, always }) =>
              (always || isLoggedIn) ? (
                <Link key={href} href={href} className="text-sm font-medium text-slate-300 hover:text-orange-400 transition-colors relative after:absolute after:bottom-[-2px] after:left-0 after:w-0 after:h-[2px] after:bg-orange-500 hover:after:w-full after:transition-all after:duration-200">{label}</Link>
              ) : null
            )}
            {isOwner && (
              <Link href="/admin/orders" className="text-sm font-medium text-orange-400 hover:text-orange-300 transition-colors relative after:absolute after:bottom-[-2px] after:left-0 after:w-0 after:h-[2px] after:bg-orange-400 hover:after:w-full after:transition-all after:duration-200">Admin</Link>
            )}
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
                <button onClick={handleLogout} className="hidden md:block px-3 py-2 text-sm text-slate-400 hover:text-white transition-colors cursor-pointer">Logout</button>
              </>
            ) : (
              <Link href="/login" className="hidden md:block px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold rounded-lg transition-colors">
                Sign in
              </Link>
            )}

            {/* Hamburger */}
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="md:hidden p-2.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              aria-label="Menu"
            >
              {menuOpen ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden bg-slate-800 border-t border-slate-700 px-4 py-3 flex flex-col gap-1">
            {navLinks.map(({ href, label, always }) =>
              (always || isLoggedIn) ? (
                <Link key={href} href={href} onClick={() => setMenuOpen(false)} className="px-3 py-2.5 text-sm font-medium text-slate-200 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">{label}</Link>
              ) : null
            )}
            {isOwner && (
              <Link href="/admin/orders" onClick={() => setMenuOpen(false)} className="px-3 py-2.5 text-sm font-medium text-orange-400 hover:bg-slate-700 rounded-lg transition-colors">Admin</Link>
            )}
            {isLoggedIn ? (
              <button onClick={handleLogout} className="text-left px-3 py-2.5 text-sm text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors cursor-pointer">Logout</button>
            ) : (
              <Link href="/login" onClick={() => setMenuOpen(false)} className="px-3 py-2.5 text-sm font-semibold text-white bg-orange-500 hover:bg-orange-600 rounded-lg transition-colors text-center mt-1">Sign in</Link>
            )}
          </div>
        )}
      </header>

      <main>{children}</main>

      <footer className="bg-slate-900 text-slate-400 text-sm py-8 mt-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p>© 2026 Sanjay Hardware · Quality hardware & sanitary products</p>
        </div>
      </footer>

      {/* WhatsApp float */}
      <a
        href={`https://wa.me/${WHATSAPP}?text=Hi, I have a query about your products`}
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-6 right-6 z-40 w-14 h-14 bg-green-500 hover:bg-green-600 rounded-full shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-110"
        aria-label="Chat on WhatsApp"
      >
        <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
      </a>

      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)} />
      <Toast />
    </div>
  );
}
