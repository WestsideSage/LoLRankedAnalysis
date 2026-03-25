import { useSearchParams, useParams } from 'react-router-dom';
import { useOverview } from '@/hooks/use-api';
import { RankBadge, UnrankedBadge } from './rank-badge';
import { QueueCard } from './queue-card';
import { Layout } from './layout';

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-white/8 rounded-xl ${className}`} />;
}

export function PlayerOverview() {
  const { name = '', tag = '' } = useParams();
  const [searchParams] = useSearchParams();
  const region = searchParams.get('region') ?? 'na1';

  const { data, loading, error } = useOverview(
    decodeURIComponent(name),
    decodeURIComponent(tag),
    region
  );

  const rankInfo = data?.rank_info && 'tier' in data.rank_info ? data.rank_info : null;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-6 py-10">
        {/* Player header */}
        {loading ? (
          <div className="flex flex-col gap-4 mb-10">
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-16 w-40" />
          </div>
        ) : error ? (
          <div className="text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl p-6 mb-10">
            <p className="font-semibold">Failed to load player data</p>
            <p className="text-sm mt-1 text-red-400/70">{error}</p>
          </div>
        ) : data ? (
          <div className="mb-10">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white">{data.display_name}</h1>
                <p className="text-white/40 text-sm mt-1">{region.toUpperCase()}</p>
              </div>
              {rankInfo && 'tier' in rankInfo ? <RankBadge rank={rankInfo as import('@/lib/types').RankInfo} /> : <UnrankedBadge />}
              {rankInfo && 'tier' in rankInfo && (
                <div className="sm:ml-auto flex gap-6 text-sm">
                  <div className="text-center">
                    <div className="text-white font-semibold">{rankInfo.win_rate}%</div>
                    <div className="text-white/40 text-xs">Win Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-green-400 font-semibold">{rankInfo.wins}W</div>
                    <div className="text-white/40 text-xs">Wins</div>
                  </div>
                  <div className="text-center">
                    <div className="text-red-400 font-semibold">{rankInfo.losses}L</div>
                    <div className="text-white/40 text-xs">Losses</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : null}

        {/* Queue cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-36" />)
          ) : data ? (
            <>
              <QueueCard
                queue="ranked"
                label="Ranked Solo"
                gameCount={data.queue_counts.ranked}
                winRate={rankInfo?.win_rate}
                name={decodeURIComponent(name)}
                tag={decodeURIComponent(tag)}
              />
              <QueueCard
                queue="aram"
                label="ARAM"
                gameCount={data.queue_counts.aram}
                name={decodeURIComponent(name)}
                tag={decodeURIComponent(tag)}
              />
              <QueueCard
                queue="mayhem"
                label="ARAM: Mayhem"
                gameCount={data.queue_counts.aram}
                name={decodeURIComponent(name)}
                tag={decodeURIComponent(tag)}
              />
              <QueueCard
                queue="arena"
                label="Arena"
                gameCount={data.queue_counts.arena}
                name={decodeURIComponent(name)}
                tag={decodeURIComponent(tag)}
              />
            </>
          ) : null}
        </div>
      </div>
    </Layout>
  );
}
