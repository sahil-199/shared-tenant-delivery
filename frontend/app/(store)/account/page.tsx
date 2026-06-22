"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { addresses } from "@/lib/api";
import type { Address } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";

export default function AccountPage() {
  const router = useRouter();
  const { phone, isLoggedIn, logout } = useAuthStore();
  const [list, setList] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newAddr, setNewAddr] = useState({ line1: "", line2: "", city: "", state: "", pin_code: "" });

  useEffect(() => {
    if (!isLoggedIn) { router.push("/login"); return; }
    addresses.list().then(setList).finally(() => setLoading(false));
  }, [isLoggedIn]);

  async function saveAddress() {
    const addr = await addresses.create(newAddr);
    setList((p) => [...p, addr]);
    setShowNew(false);
    setNewAddr({ line1: "", line2: "", city: "", state: "", pin_code: "" });
  }

  async function removeAddress(id: number) {
    await addresses.remove(id);
    setList((p) => p.filter((a) => a.id !== id));
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner /></div>;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Account</h1>
      <section className="bg-zinc-50 rounded-xl p-4 mb-6">
        <p className="text-sm text-gray-500">Logged in as</p>
        <p className="font-semibold text-gray-900 mt-0.5">{phone}</p>
        <button onClick={() => { logout(); router.push("/login"); }}
          className="text-sm text-red-600 hover:underline mt-2">Logout</button>
      </section>
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900">Saved Addresses</h2>
          <button onClick={() => setShowNew(true)} className="text-sm text-blue-600 hover:underline">+ Add</button>
        </div>
        {list.map((addr) => (
          <div key={addr.id} className="flex items-start justify-between p-3 border border-gray-200 rounded-xl mb-2">
            <p className="text-sm text-gray-700">{addr.line1}, {addr.city}, {addr.state} — {addr.pin_code}</p>
            <button onClick={() => removeAddress(addr.id)} className="text-xs text-red-500 hover:underline ml-4 shrink-0">Remove</button>
          </div>
        ))}
        {showNew && (
          <div className="border border-gray-200 rounded-xl p-4 flex flex-col gap-3 mt-2">
            <Input label="Address line 1" value={newAddr.line1} onChange={(e) => setNewAddr((p) => ({ ...p, line1: e.target.value }))} />
            <Input label="Address line 2" value={newAddr.line2} onChange={(e) => setNewAddr((p) => ({ ...p, line2: e.target.value }))} />
            <div className="grid grid-cols-2 gap-3">
              <Input label="City" value={newAddr.city} onChange={(e) => setNewAddr((p) => ({ ...p, city: e.target.value }))} />
              <Input label="State" value={newAddr.state} onChange={(e) => setNewAddr((p) => ({ ...p, state: e.target.value }))} />
            </div>
            <Input label="Pin code" value={newAddr.pin_code} onChange={(e) => setNewAddr((p) => ({ ...p, pin_code: e.target.value }))} />
            <div className="flex gap-2">
              <Button onClick={saveAddress}>Save</Button>
              <Button variant="ghost" onClick={() => setShowNew(false)}>Cancel</Button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
