"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useEffect } from "react";

const navItems = [
  { href: "/admin/orders", label: "Orders" },
  { href: "/admin/products", label: "Products" },
  { href: "/admin/inventory", label: "Inventory" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, isOwner } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoggedIn) router.push("/login");
    else if (!isOwner) router.push("/");
  }, [isLoggedIn, isOwner]);

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="bg-white border-b border-gray-200 h-14 flex items-center px-6 sticky top-0 z-10">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-900 mr-6">← Store</Link>
        <span className="font-semibold text-gray-900">Admin</span>
      </header>
      <div className="flex">
        <nav className="w-48 shrink-0 min-h-[calc(100vh-56px)] bg-white border-r border-gray-200 p-4 flex flex-col gap-1">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href}
              className={`px-3 py-2 rounded-lg text-sm transition-colors ${pathname === item.href ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-600 hover:bg-gray-50"}`}>
              {item.label}
            </Link>
          ))}
        </nav>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
