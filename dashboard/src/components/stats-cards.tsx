interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}

export function StatCard({ label, value, sub, accent = 'text-white' }: StatCardProps) {
  return (
    <div className="bg-white/5 border border-white/8 rounded-xl p-4 flex flex-col gap-1">
      <span className="text-white/40 text-xs uppercase tracking-wider">{label}</span>
      <span className={`text-2xl font-bold ${accent}`}>{value}</span>
      {sub && <span className="text-white/40 text-xs">{sub}</span>}
    </div>
  );
}
