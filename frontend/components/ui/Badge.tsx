const statusColors: Record<string, string> = {
  placed: "bg-yellow-100 text-yellow-800",
  pending_confirmation: "bg-yellow-100 text-yellow-800",
  confirmed: "bg-blue-100 text-blue-800",
  processing: "bg-blue-100 text-blue-800",
  out_for_delivery: "bg-purple-100 text-purple-800",
  delivered: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  refunded: "bg-gray-100 text-gray-800",
  active: "bg-green-100 text-green-800",
  inactive: "bg-gray-100 text-gray-600",
};

export function Badge({ status }: { status: string }) {
  const color = statusColors[status.toLowerCase()] ?? "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize ${color}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
