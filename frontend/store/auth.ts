import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authStorage } from "@/lib/auth";

interface AuthState {
  phone: string | null;
  isLoggedIn: boolean;
  isOwner: boolean;
  login: (phone: string, access: string, refresh: string) => void;
  logout: () => void;
}

// ponytail: decodes JWT without a library — we only need phone + is_store_owner
function parseJwt(token: string): Record<string, unknown> {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch {
    return {};
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      phone: null,
      isLoggedIn: false,
      isOwner: false,
      login: (phone, access, refresh) => {
        authStorage.set(access, refresh);
        const payload = parseJwt(access);
        set({ phone, isLoggedIn: true, isOwner: Boolean(payload.is_store_owner) });
      },
      logout: () => {
        authStorage.clear();
        set({ phone: null, isLoggedIn: false, isOwner: false });
      },
    }),
    { name: "auth-store", partialize: (s) => ({ phone: s.phone, isLoggedIn: s.isLoggedIn, isOwner: s.isOwner }) }
  )
);
