import { create } from "zustand";
import { cart as cartApi, CartData } from "@/lib/api";

interface CartState {
  cart: CartData | null;
  loading: boolean;
  itemCount: number;
  loadCart: () => Promise<void>;
  addItem: (variantId: number, qty: number) => Promise<void>;
  updateItem: (itemId: number, qty: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
  clearCart: () => void;
}

export const useCartStore = create<CartState>((set, get) => ({
  cart: null,
  loading: false,
  itemCount: 0,
  loadCart: async () => {
    set({ loading: true });
    try {
      const data = await cartApi.get();
      set({ cart: data, itemCount: data.items.reduce((s, i) => s + i.qty, 0) });
    } finally {
      set({ loading: false });
    }
  },
  addItem: async (variantId, qty) => {
    set((s) => ({ itemCount: s.itemCount + qty })); // optimistic
    const data = await cartApi.addItem(variantId, qty);
    set({ cart: data, itemCount: data.items.reduce((s, i) => s + i.qty, 0) });
  },
  updateItem: async (itemId, qty) => {
    const data = await cartApi.updateItem(itemId, qty);
    set({ cart: data, itemCount: data.items.reduce((s, i) => s + i.qty, 0) });
  },
  removeItem: async (itemId) => {
    set((s) => {
      if (!s.cart) return {};
      const items = s.cart.items.filter((i) => i.id !== itemId);
      const total = items.reduce((sum, i) => sum + parseFloat(i.subtotal), 0).toFixed(2);
      return { cart: { ...s.cart, items, total }, itemCount: items.reduce((sum, i) => sum + i.qty, 0) };
    });
    await cartApi.removeItem(itemId);
  },
  clearCart: () => set({ cart: null, itemCount: 0 }),
}));
