import { Badge } from '@/components/ui/badge';
import type { RecentMatch } from '@/lib/types';

type Mode = 'ranked' | 'aram' | 'arena';

interface Props {
  matches: RecentMatch[];
  mode?: Mode;
}

const ROLE_LABELS: Record<string, string> = {
  TOP: 'Top', JUNGLE: 'JG', MIDDLE: 'Mid', BOTTOM: 'Bot', UTILITY: 'Sup',
};

export function MatchList({ matches, mode = 'ranked' }: Props) {
  return (
    <div className="flex flex-col gap-1.5">
      {matches.slice(0, 15).map((m, i) => (
        <div
          key={i}
          className={`flex items-center gap-4 px-4 py-3 rounded-xl border text-sm
            ${mode !== 'arena'
              ? m.win
                ? 'bg-emerald-500/5 border-emerald-500/15'
                : 'bg-red-500/5 border-red-500/15'
              : (m.placement ?? 9) <= 4
                ? 'bg-emerald-500/5 border-emerald-500/15'
                : 'bg-red-500/5 border-red-500/15'
            }`}
        >
          {/* Result */}
          <div className="w-10 shrink-0">
            {mode === 'arena' ? (
              <span className={`font-bold text-base ${(m.placement ?? 9) <= 4 ? 'text-emerald-400' : 'text-red-400'}`}>
                #{m.placement}
              </span>
            ) : (
              <Badge
                variant="outline"
                className={`text-xs font-bold border-0 px-1.5 ${
                  m.win ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                }`}
              >
                {m.win ? 'W' : 'L'}
              </Badge>
            )}
          </div>

          {/* Champion + role */}
          <div className="min-w-0 flex-1">
            <span className="font-medium text-white">{m.champion}</span>
            {m.role && (
              <span className="text-white/30 text-xs ml-2">{ROLE_LABELS[m.role] ?? m.role}</span>
            )}
          </div>

          {/* KDA */}
          <span className="text-white/60 font-mono text-xs shrink-0">{m.kda}</span>

          {/* Damage */}
          <span className="text-white/40 text-xs shrink-0 w-20 text-right">
            {m.damage.toLocaleString()}
          </span>

          {/* Mode-specific */}
          {mode === 'ranked' && m.cs !== undefined && (
            <span className="text-white/40 text-xs shrink-0 w-20 text-right">
              {m.cs} cs ({m.cs_per_min}/m)
            </span>
          )}
          {mode !== 'ranked' && mode !== 'arena' && m.damage_per_min !== undefined && (
            <span className="text-white/40 text-xs shrink-0 w-20 text-right">
              {m.damage_per_min} d/m
            </span>
          )}
          {mode !== 'arena' && m.kill_participation !== undefined && (
            <span className="text-white/40 text-xs shrink-0 w-12 text-right">{m.kill_participation}%</span>
          )}
        </div>
      ))}
    </div>
  );
}
