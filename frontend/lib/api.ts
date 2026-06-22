import { authStorage } from "./auth";

const BASE = process.env.NEXT_PUBLIC_API_URL!;

// ---- Types ----

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  is_new_user: boolean;
}

export interface ProductVariant {
  id: number;
  name: string;
  sku: string;
  price: string;
  sale_price: string | null;
  effective_price: string;
}

export interface ProductImage {
  id: number;
  variant: number | null;
  image_url: string;
  sort_order: number;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  specifications: Record<string, string>;
  category: number;
  category_name: string;
  brand: number | null;
  brand_name: string | null;
  is_active: boolean;
  created_at: string;
  variants: ProductVariant[];
  images: ProductImage[];
}

export interface CartItem {
  id: number;
  variant: number;
  variant_name: string;
  product_name: string;
  product_slug: string;
  qty: number;
  price: string;
  subtotal: string;
}

export interface CartData {
  id: number;
  items: CartItem[];
  total: string;
}

export interface Address {
  id: number;
  line1: string;
  line2: string;
  city: string;
  state: string;
  pin_code: string;
  lat: number | null;
  lng: number | null;
  is_default: boolean;
}

export interface OrderItem {
  id: number;
  variant: number;
  variant_name: string;
  qty: number;
  unit_price: string;
}

export interface Order {
  id: number;
  status: string;
  total_amount: string;
  notes: string;
  created_at: string;
  address: Address;
  items: OrderItem[];
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  image: string | null;
  parent: number | null;
  is_active: boolean;
}

export interface Brand {
  id: number;
  name: string;
  slug: string;
  logo: string | null;
  is_active: boolean;
}

export interface InventoryItem {
  variant_id: number;
  available_qty: number;
  reserved_qty: number;
}

// ---- HTTP Core ----

async function refreshTokens(): Promise<string | null> {
  const refresh = authStorage.getRefresh();
  if (!refresh) return null;
  try {
    const res = await fetch(`${BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) { authStorage.clear(); return null; }
    const data = await res.json();
    authStorage.set(data.access, refresh);
    return data.access;
  } catch {
    return null;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const token = authStorage.getAccess();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401 && retry) {
    const newToken = await refreshTokens();
    if (newToken) return request<T>(path, options, false);
    authStorage.clear();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw Object.assign(new Error(res.statusText), { status: res.status, data: err });
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---- Auth ----

export const auth = {
  requestOtp: (phone: string) =>
    request<void>("/auth/otp/request/", {
      method: "POST",
      body: JSON.stringify({ phone }),
    }),
  verifyOtp: (phone: string, otp: string) =>
    request<AuthTokens>("/auth/otp/verify/", {
      method: "POST",
      body: JSON.stringify({ phone, otp }),
    }),
};

// ---- Products ----

export const products = {
  list: (params?: { search?: string; category?: string; brand?: number; in_stock?: boolean; sort?: string }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.category) q.set("category", String(params.category));
    if (params?.brand) q.set("brand", String(params.brand));
    if (params?.in_stock) q.set("in_stock", "true");
    if (params?.sort) q.set("sort", params.sort);
    return request<Product[]>(`/products/${q.toString() ? "?" + q : ""}`);
  },
  get: (id: number) => request<Product>(`/products/${id}/`),
};

// ---- Categories ----

export const categories = {
  list: () => request<Category[]>("/categories/"),
  create: (data: Partial<Category>) =>
    request<Category>("/categories/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Category>) =>
    request<Category>(`/categories/${id}/`, { method: "PUT", body: JSON.stringify(data) }),
  remove: (id: number) => request<void>(`/categories/${id}/`, { method: "DELETE" }),
};

// ---- Brands ----

export const brands = {
  list: () => request<Brand[]>("/brands/"),
};

// ---- Cart ----

export const cart = {
  get: () => request<CartData>("/cart/"),
  addItem: (variant: number, qty: number) =>
    request<CartData>("/cart/items/", { method: "POST", body: JSON.stringify({ variant, qty }) }),
  updateItem: (id: number, qty: number) =>
    request<CartData>(`/cart/items/${id}/`, { method: "PATCH", body: JSON.stringify({ qty }) }),
  removeItem: (id: number) =>
    request<void>(`/cart/items/${id}/delete/`, { method: "DELETE" }),
};

// ---- Addresses ----

export const addresses = {
  list: () => request<Address[]>("/addresses/"),
  create: (data: Omit<Address, "id" | "lat" | "lng" | "is_default">) =>
    request<Address>("/addresses/", { method: "POST", body: JSON.stringify(data) }),
  update: (id: number, data: Partial<Address>) =>
    request<Address>(`/addresses/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  remove: (id: number) => request<void>(`/addresses/${id}/`, { method: "DELETE" }),
};

// ---- Orders ----

export const orders = {
  list: () => request<Order[]>("/orders/list/"),
  get: (id: number) => request<Order>(`/orders/${id}/`),
  create: (address: number, notes?: string) =>
    request<Order>("/orders/", { method: "POST", body: JSON.stringify({ address, notes }) }),
  updateStatus: (id: number, status: string) =>
    request<Order>(`/orders/${id}/status/`, { method: "PATCH", body: JSON.stringify({ status }) }),
};

// ---- Payments ----

export const payments = {
  initiate: (order_id: number, method: "cod" | "razorpay") =>
    request<{ id: number; method: string; status: string; razorpay_order_id?: string; amount: string }>(
      "/payments/initiate/",
      { method: "POST", body: JSON.stringify({ order_id, method }) }
    ),
};

// ---- Inventory (admin) ----

export const inventory = {
  list: () => request<InventoryItem[]>("/inventory/"),
  update: (variant_id: number, available_qty: number) =>
    request<InventoryItem>(`/inventory/${variant_id}/`, {
      method: "PATCH",
      body: JSON.stringify({ available_qty }),
    }),
};
