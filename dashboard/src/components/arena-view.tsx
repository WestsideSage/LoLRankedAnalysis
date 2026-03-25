import { useSearchParams, useParams } from 'react-router-dom';
import { useArenaAnalysis } from '@/hooks/use-api';
import { Layout } from './layout';
import { StatCard } from './stats-cards';
import { ChampionTable } from './champion-table';
import { MatchList } from './match-list';
import { StrengthsWeaknesses } from './strengths-weaknesses';
import { PlayerRadarChart } from './charts/radar-chart';
import { PlacementChart } from './charts/placement-chart';
import { ChampionBarChart } from './charts/champion-bar-chart';
import type { ArenaAnalysis } from '@/lib/types';

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-white/8 rounded-xl ${className}`} />;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-white/60 text-xs uppercase tracking-widest mb-3 font-semibold">{children}</h2>
  );
}

function buildRadarData(data: ArenaAnalysis) {
  // Invert placement: placement 1 = 100%, placement 8 = 0%
  const placementScore = Math.round(((8 - data.avg_placement) / 7) * 100);
  return [
    { subject: 'Avg Place', value: placementScore, fullMark: 100 },
    { subject: 'Top 4%', value: Math.round(data.top4_rate), fullMark: 100 },
    { subject: '1st Place%', value: Math.round(data.first_rate), fullMark: 100 },
    { subject: 'KDA', value: Math.min(100, Math.round((data.average_kda.ratio / 6) * 100)), fullMark: 100 },
    { subject: 'Damage', value: Math.min(100, Math.round((data.avg_damage / 25000) * 100)), fullMark: 100 },
  ];
}

export function ArenaView() {
  const { name = '', tag = '' } = useParams();
  const [searchParams] = useSearchParams();
  const region = searchParams.get('region') ?? 'na1';

  const { data, loading, error } = useArenaAnalysis(
    decodeURIComponent(name),
    decodeURIComponent(tag),
    region,
    30,
  );

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">
        <div>
          <p className="text-white/30 text-sm mb-1">
            {decodeURIComponent(name)}#{decodeURIComponent(tag)} &bull; Arena
          </p>
          <h1 className="text-2xl font-bold">Performance Analysis</h1>
        </div>

        {loading && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
            </div>
            <Skeleton className="h-64" />
          </div>
        )}

        {error && (
          <div className="text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl p-6">
            <p className="font-semibold">Failed to load Arena data</p>
            <p className="text-sm mt-1 text-red-400/70">{error}</p>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Stat cards */}
            <div>
              <SectionTitle>Overview — {data.total_matches} games</SectionTitle>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <StatCard
                  label="Avg Placement"
                  value={`#${data.avg_placement}`}
                  accent={data.avg_placement <= 3.5 ? 'text-emerald-400' : data.avg_placement >= 5.5 ? 'text-red-400' : 'text-white'}
                />
                <StatCard
                  label="Top 4 Rate"
                  value={`${data.top4_rate}%`}
                  sub={`${data.top4_count} games`}
                  accent={data.top4_rate >= 60 ? 'text-emerald-400' : data.top4_rate < 40 ? 'text-red-400' : 'text-white'}
                />
                <StatCard label="1st Place" value={String(data.first_count)} sub={`${data.first_rate}%`} />
                <StatCard label="KDA" value={`${data.average_kda.ratio}`} sub={`${data.average_kda.kills}/${data.average_kda.deaths}/${data.average_kda.assists}`} />
                <StatCard label="Avg Damage" value={data.avg_damage.toLocaleString()} />
              </div>
            </div>

            {/* Charts */}
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Performance Radar</SectionTitle>
                <PlayerRadarChart data={buildRadarData(data)} color="#f97316" />
              </div>
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Placement Distribution</SectionTitle>
                <PlacementChart matches={data.recent_performance} />
              </div>
            </div>

            {Object.keys(data.champion_stats).length > 0 && (
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Champion Avg Placement (2+ games, lower is better)</SectionTitle>
                <ChampionBarChart data={data.champion_stats} mode="placement" />
              </div>
            )}

            <StrengthsWeaknesses strengths={data.strengths} weaknesses={data.weaknesses} />

            <div className="bg-white/4 border border-white/8 rounded-2xl overflow-hidden">
              <div className="px-4 pt-4 pb-2">
                <SectionTitle>Champion Performance</SectionTitle>
              </div>
              <ChampionTable data={data.champion_stats} mode="arena" />
            </div>

            <div>
              <SectionTitle>Recent Matches</SectionTitle>
              <MatchList matches={data.recent_performance} mode="arena" />
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
