"use client";

export function SortSelect({ current, category }: { current?: string; category?: string }) {
  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (e.target.value) params.set("sort", e.target.value);
    window.location.href = `/products${params.toString() ? "?" + params : ""}`;
  }

  return (
    <select
      defaultValue={current ?? ""}
      onChange={handleChange}
      className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 outline-none"
    >
      <option value="">Sort: Default</option>
      <option value="price_asc">Price: Low to High</option>
      <option value="price_desc">Price: High to Low</option>
      <option value="newest">Newest</option>
    </select>
  );
}
