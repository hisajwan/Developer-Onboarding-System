export function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl bg-surface p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  );
}
