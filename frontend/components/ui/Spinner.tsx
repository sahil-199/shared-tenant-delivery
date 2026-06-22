export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div className={`w-6 h-6 border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin ${className}`} />
  );
}
