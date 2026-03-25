import type { RankInfo } from '@/lib/types';

const TIER_COLORS: Record<string, string> = {
  IRON: 'text-gray-400',
  BRONZE: 'text-amber-700',
  SILVER: 'text-slate-300',
  GOLD: 'text-yellow-400',
  PLATINUM: 'text-teal-400',
  EMERALD: 'text-emerald-400',
  DIAMOND: 'text-blue-300',
  MASTER: 'text-purple-400',
  GRANDMASTER: 'text-red-400',
  CHALLENGER: 'text-yellow-300',
};

const TIER_BG: Record<string, string> = {
  IRON: 'bg-gray-500/10 border-gray-500/20',
  BRONZE: 'bg-amber-700/10 border-amber-700/20',
  SILVER: 'bg-slate-300/10 border-slate-300/20',
  GOLD: 'bg-yellow-400/10 border-yellow-400/20',
  PLATINUM: 'bg-teal-400/10 border-teal-400/20',
  EMERALD: 'bg-emerald-400/10 border-emerald-400/20',
  DIAMOND: 'bg-blue-300/10 border-blue-300/20',
  MASTER: 'bg-purple-400/10 border-purple-400/20',
  GRANDMASTER: 'bg-red-400/10 border-red-400/20',
  CHALLENGER: 'bg-yellow-300/10 border-yellow-300/20',
};

export function RankBadge({ rank }: { rank: RankInfo }) {
  const color = TIER_COLORS[rank.tier] ?? 'text-white';
  const bg = TIER_BG[rank.tier] ?? 'bg-white/10 border-white/20';
  return (
    <div className={`inline-flex flex-col items-center px-4 py-2 rounded-xl border ${bg}`}>
      <span className={`font-bold text-lg leading-none ${color}`}>
        {rank.tier} {rank.rank}
      </span>
      <span className="text-white/50 text-xs mt-0.5">{rank.lp} LP</span>
    </div>
  );
}

export function UnrankedBadge() {
  return (
    <div className="inline-flex flex-col items-center px-4 py-2 rounded-xl border bg-white/5 border-white/10">
      <span className="font-bold text-lg leading-none text-white/50">Unranked</span>
    </div>
  );
}
