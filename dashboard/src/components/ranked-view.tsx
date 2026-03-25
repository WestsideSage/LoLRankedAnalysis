import { useSearchParams, useParams } from 'react-router-dom';
import { useRankedAnalysis } from '@/hooks/use-api';
import { Layout } from './layout';
import { StatCard } from './stats-cards';
import { ChampionTable } from './champion-table';
import { MatchList } from './match-list';
import { StrengthsWeaknesses } from './strengths-weaknesses';
import { PlayerRadarChart } from './charts/radar-chart';
import { WinRateChart } from './charts/winrate-chart';
import { ChampionBarChart } from './charts/champion-bar-chart';
import type { RankedAnalysis } from '@/lib/types';

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-white/8 rounded-xl ${className}`} />;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-white/60 text-xs uppercase tracking-widest mb-3 font-semibold">{children}</h2>
  );
}

function buildRadarData(data: RankedAnalysis) {
  // Normalize to 0-100 relative to reasonable ranges
  const wrScore = data.win_rate;
  const kdaScore = Math.min(100, (data.average_kda.ratio / 5) * 100);
  const dmgScore = Math.min(100, (data.avg_damage / 25000) * 100);
  const csScore = Math.min(100, (data.avg_cs_per_min / 8) * 100);
  const visScore = Math.min(100, (data.avg_vision_per_min / 1.5) * 100);
  const kpScore = Math.min(100, data.avg_kill_participation);
  return [
    { subject: 'Win Rate', value: Math.round(wrScore), fullMark: 100 },
    { subject: 'KDA', value: Math.round(kdaScore), fullMark: 100 },
    { subject: 'Damage', value: Math.round(dmgScore), fullMark: 100 },
    { subject: 'CS/min', value: Math.round(csScore), fullMark: 100 },
    { subject: 'Vision', value: Math.round(visScore), fullMark: 100 },
    { subject: 'Kill Part.', value: Math.round(kpScore), fullMark: 100 },
  ];
}

export function RankedView() {
  const { name = '', tag = '' } = useParams();
  const [searchParams] = useSearchParams();
  const region = searchParams.get('region') ?? 'na1';

  const { data, loading, error } = useRankedAnalysis(
    decodeURIComponent(name),
    decodeURIComponent(tag),
    region,
    20,
  );

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">
        <div>
          <p className="text-white/30 text-sm mb-1">
            {decodeURIComponent(name)}#{decodeURIComponent(tag)} &bull; Ranked Solo/Duo
          </p>
          <h1 className="text-2xl font-bold">Performance Analysis</h1>
        </div>

        {loading && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
            </div>
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
          </div>
        )}

        {error && (
          <div className="text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl p-6">
            <p className="font-semibold">Failed to load ranked data</p>
            <p className="text-sm mt-1 text-red-400/70">{error}</p>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Stat cards */}
            <div>
              <SectionTitle>Overview — {data.total_matches} games</SectionTitle>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <StatCard
                  label="Win Rate"
                  value={`${data.win_rate}%`}
                  sub={`${data.wins}W / ${data.losses}L`}
                  accent={data.win_rate >= 55 ? 'text-emerald-400' : data.win_rate < 45 ? 'text-red-400' : 'text-white'}
                />
                <StatCard
                  label="KDA"
                  value={`${data.average_kda.ratio}`}
                  sub={`${data.average_kda.kills}/${data.average_kda.deaths}/${data.average_kda.assists}`}
                />
                <StatCard label="Avg Damage" value={data.avg_damage.toLocaleString()} />
                <StatCard label="CS/min" value={String(data.avg_cs_per_min)} />
                <StatCard label="Vision/min" value={String(data.avg_vision_per_min)} />
                <StatCard label="Kill Part." value={`${data.avg_kill_participation}%`} />
              </div>
            </div>

            {/* Charts row */}
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Performance Radar</SectionTitle>
                <PlayerRadarChart data={buildRadarData(data)} />
              </div>
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Win Rate Trend</SectionTitle>
                <WinRateChart matches={data.recent_performance} />
              </div>
            </div>

            {/* Champion win rate bar */}
            {Object.keys(data.champion_stats).length > 0 && (
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Champion Win Rate (2+ games)</SectionTitle>
                <ChampionBarChart data={data.champion_stats} />
              </div>
            )}

            {/* Strengths / Weaknesses */}
            <StrengthsWeaknesses strengths={data.strengths} weaknesses={data.weaknesses} />

            {/* Champion table */}
            <div className="bg-white/4 border border-white/8 rounded-2xl overflow-hidden">
              <div className="px-4 pt-4 pb-2">
                <SectionTitle>Champion Performance</SectionTitle>
              </div>
              <ChampionTable data={data.champion_stats} mode="ranked" />
            </div>

            {/* Recent matches */}
            <div>
              <SectionTitle>Recent Matches</SectionTitle>
              <MatchList matches={data.recent_performance} mode="ranked" />
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
