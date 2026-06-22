import { create } from "zustand";

interface ToastState {
  message: string;
  visible: boolean;
  show: (message: string) => void;
}

let timer: ReturnType<typeof setTimeout>;

export const useToastStore = create<ToastState>((set) => ({
  message: "",
  visible: false,
  show: (message) => {
    clearTimeout(timer);
    set({ message, visible: true });
    timer = setTimeout(() => set({ visible: false }), 2500);
  },
}));
