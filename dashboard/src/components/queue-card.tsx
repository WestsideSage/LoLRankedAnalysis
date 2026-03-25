import { useNavigate, useLocation } from 'react-router-dom';
import type { QueueType } from '@/lib/types';

interface QueueCardProps {
  queue: QueueType;
  label: string;
  gameCount: number;
  winRate?: number;
  top4Rate?: number;
  kda?: string;
  name: string;
  tag: string;
}

const QUEUE_COLORS: Record<QueueType, string> = {
  ranked: 'from-blue-600/20 to-blue-800/5 border-blue-500/20 hover:border-blue-500/40',
  aram: 'from-purple-600/20 to-purple-800/5 border-purple-500/20 hover:border-purple-500/40',
  mayhem: 'from-pink-600/20 to-pink-800/5 border-pink-500/20 hover:border-pink-500/40',
  arena: 'from-orange-600/20 to-orange-800/5 border-orange-500/20 hover:border-orange-500/40',
};

const QUEUE_ACCENT: Record<QueueType, string> = {
  ranked: 'text-blue-400',
  aram: 'text-purple-400',
  mayhem: 'text-pink-400',
  arena: 'text-orange-400',
};

export function QueueCard({ queue, label, gameCount, winRate, top4Rate, kda, name, tag }: QueueCardProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const region = new URLSearchParams(location.search).get('region') ?? 'na1';

  const rate = queue === 'arena' ? top4Rate : winRate;
  const rateLabel = queue === 'arena' ? 'Top 4' : 'Win Rate';
  const accent = QUEUE_ACCENT[queue];

  function handleClick() {
    if (gameCount === 0) return;
    navigate(`/player/${encodeURIComponent(name)}/${encodeURIComponent(tag)}/${queue}?region=${region}`);
  }

  return (
    <button
      onClick={handleClick}
      disabled={gameCount === 0}
      className={`
        relative flex flex-col p-5 rounded-2xl border bg-gradient-to-br
        ${QUEUE_COLORS[queue]}
        transition-all duration-200
        ${gameCount > 0 ? 'hover:scale-[1.02] hover:shadow-lg cursor-pointer' : 'opacity-40 cursor-not-allowed'}
        text-left w-full
      `}
    >
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-semibold uppercase tracking-wider ${accent}`}>{label}</span>
        <span className="text-white/30 text-xs">{gameCount} games</span>
      </div>

      {gameCount > 0 ? (
        <>
          <div className={`text-3xl font-bold ${accent} leading-none`}>
            {rate !== undefined ? `${rate}%` : '—'}
          </div>
          <div className="text-white/40 text-xs mt-1">{rateLabel}</div>
          {kda && <div className="text-white/50 text-xs mt-2">KDA {kda}</div>}
        </>
      ) : (
        <div className="text-white/30 text-sm">No games</div>
      )}
    </button>
  );
}
