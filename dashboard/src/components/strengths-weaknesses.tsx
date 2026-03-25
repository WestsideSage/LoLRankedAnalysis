import { TrendingUp, TrendingDown } from 'lucide-react';

interface Props {
  strengths: string[];
  weaknesses: string[];
}

export function StrengthsWeaknesses({ strengths, weaknesses }: Props) {
  if (strengths.length === 0 && weaknesses.length === 0) return null;
  return (
    <div className="grid sm:grid-cols-2 gap-4">
      {strengths.length > 0 && (
        <div className="bg-emerald-500/8 border border-emerald-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400 text-sm font-semibold uppercase tracking-wider">Strengths</span>
          </div>
          <ul className="flex flex-col gap-2">
            {strengths.map((s, i) => (
              <li key={i} className="text-white/70 text-sm flex items-start gap-2">
                <span className="text-emerald-400 mt-0.5">+</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
      {weaknesses.length > 0 && (
        <div className="bg-amber-500/8 border border-amber-500/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="w-4 h-4 text-amber-400" />
            <span className="text-amber-400 text-sm font-semibold uppercase tracking-wider">Weaknesses</span>
          </div>
          <ul className="flex flex-col gap-2">
            {weaknesses.map((w, i) => (
              <li key={i} className="text-white/70 text-sm flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">-</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
