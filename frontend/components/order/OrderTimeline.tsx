const STEPS = ["placed", "pending_confirmation", "confirmed", "processing", "out_for_delivery", "delivered"];

export function OrderTimeline({ status }: { status: string }) {
  const current = STEPS.indexOf(status.toLowerCase());
  if (status === "cancelled") return <p className="text-sm text-red-600 font-medium">Order Cancelled</p>;
  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step, i) => (
        <div key={step} className="flex items-center">
          <div className={`w-3 h-3 rounded-full border-2 transition-colors ${i <= current ? "bg-blue-600 border-blue-600" : "bg-white border-gray-300"}`} />
          {i < STEPS.length - 1 && <div className={`h-0.5 w-8 md:w-12 ${i < current ? "bg-blue-600" : "bg-gray-200"}`} />}
        </div>
      ))}
      <p className="ml-3 text-xs text-gray-500 capitalize">{status.replace(/_/g, " ")}</p>
    </div>
  );
}
