import { useState } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import { useAramAnalysis } from '@/hooks/use-api';
import { Layout } from './layout';
import { StatCard } from './stats-cards';
import { ChampionTable } from './champion-table';
import { MatchList } from './match-list';
import { StrengthsWeaknesses } from './strengths-weaknesses';
import { PlayerRadarChart } from './charts/radar-chart';
import { WinRateChart } from './charts/winrate-chart';
import { ChampionBarChart } from './charts/champion-bar-chart';
import { Badge } from '@/components/ui/badge';
import type { AramAnalysis } from '@/lib/types';

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-white/8 rounded-xl ${className}`} />;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-white/60 text-xs uppercase tracking-widest mb-3 font-semibold">{children}</h2>
  );
}

function buildRadarData(data: AramAnalysis) {
  return [
    { subject: 'Win Rate', value: Math.round(data.win_rate), fullMark: 100 },
    { subject: 'KDA', value: Math.min(100, Math.round((data.average_kda.ratio / 6) * 100)), fullMark: 100 },
    { subject: 'Dmg/min', value: Math.min(100, Math.round((data.avg_damage_per_min / 1500) * 100)), fullMark: 100 },
    { subject: 'Kill Part.', value: Math.min(100, Math.round(data.avg_kill_participation)), fullMark: 100 },
    { subject: 'Dmg Share', value: Math.min(100, Math.round(data.avg_damage_share * 1.5)), fullMark: 100 },
    { subject: 'Gold/min', value: Math.min(100, Math.round((data.avg_gold_per_min / 500) * 100)), fullMark: 100 },
  ];
}

interface Props {
  isMayhem?: boolean;
}

export function AramView({ isMayhem = false }: Props) {
  const { name = '', tag = '' } = useParams();
  const [searchParams] = useSearchParams();
  const region = searchParams.get('region') ?? 'na1';
  const [mayhem, setMayhem] = useState(isMayhem);

  const { data, loading, error } = useAramAnalysis(
    decodeURIComponent(name),
    decodeURIComponent(tag),
    region,
    30,
    mayhem,
  );

  const modeLabel = mayhem ? 'ARAM: Mayhem' : 'ARAM';
  const accentColor = mayhem ? '#ec4899' : '#a855f7';

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-white/30 text-sm mb-1">
              {decodeURIComponent(name)}#{decodeURIComponent(tag)} &bull; {modeLabel}
            </p>
            <h1 className="text-2xl font-bold">Performance Analysis</h1>
          </div>
          <button
            onClick={() => setMayhem(!mayhem)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-all font-semibold ${
              mayhem
                ? 'bg-pink-500/20 border-pink-500/40 text-pink-300'
                : 'bg-white/5 border-white/10 text-white/50 hover:border-white/20'
            }`}
          >
            {mayhem ? 'Mayhem ON' : 'Show Mayhem'}
          </button>
        </div>

        {loading && (
          <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
            </div>
            <Skeleton className="h-64" />
          </div>
        )}

        {error && (
          <div className="text-red-400 bg-red-400/10 border border-red-400/20 rounded-xl p-6">
            <p className="font-semibold">Failed to load ARAM data</p>
            <p className="text-sm mt-1 text-red-400/70">{error}</p>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Multikill badges */}
            {(data.pentakills > 0 || data.quadrakills > 0) && (
              <div className="flex gap-2">
                {data.pentakills > 0 && (
                  <Badge className="bg-yellow-500/20 text-yellow-300 border-yellow-500/30">
                    {data.pentakills} Pentakill{data.pentakills > 1 ? 's' : ''}
                  </Badge>
                )}
                {data.quadrakills > 0 && (
                  <Badge className="bg-orange-500/20 text-orange-300 border-orange-500/30">
                    {data.quadrakills} Quadrakill{data.quadrakills > 1 ? 's' : ''}
                  </Badge>
                )}
              </div>
            )}

            {/* Stat cards */}
            <div>
              <SectionTitle>Overview — {data.total_matches} games</SectionTitle>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard
                  label="Win Rate"
                  value={`${data.win_rate}%`}
                  sub={`${data.wins}W / ${data.losses}L`}
                  accent={data.win_rate >= 55 ? 'text-emerald-400' : data.win_rate < 45 ? 'text-red-400' : 'text-white'}
                />
                <StatCard label="KDA" value={`${data.average_kda.ratio}`} sub={`${data.average_kda.kills}/${data.average_kda.deaths}/${data.average_kda.assists}`} />
                <StatCard label="Dmg/min" value={String(data.avg_damage_per_min)} />
                <StatCard label="Kill Part." value={`${data.avg_kill_participation}%`} />
                <StatCard label="Avg Damage" value={data.avg_damage.toLocaleString()} />
                <StatCard label="Dmg Taken" value={data.avg_damage_taken.toLocaleString()} />
                <StatCard label="Avg Healing" value={data.avg_healing.toLocaleString()} />
                <StatCard label="Gold/min" value={String(data.avg_gold_per_min)} />
              </div>
            </div>

            {/* Charts */}
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Performance Radar</SectionTitle>
                <PlayerRadarChart data={buildRadarData(data)} color={accentColor} />
              </div>
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Win Rate Trend</SectionTitle>
                <WinRateChart matches={data.recent_performance} />
              </div>
            </div>

            {Object.keys(data.champion_stats).length > 0 && (
              <div className="bg-white/4 border border-white/8 rounded-2xl p-4">
                <SectionTitle>Champion Win Rate (2+ games)</SectionTitle>
                <ChampionBarChart data={data.champion_stats} />
              </div>
            )}

            <StrengthsWeaknesses strengths={data.strengths} weaknesses={data.weaknesses} />

            <div className="bg-white/4 border border-white/8 rounded-2xl overflow-hidden">
              <div className="px-4 pt-4 pb-2">
                <SectionTitle>Champion Performance</SectionTitle>
              </div>
              <ChampionTable data={data.champion_stats} mode="aram" />
            </div>

            <div>
              <SectionTitle>Recent Matches</SectionTitle>
              <MatchList matches={data.recent_performance} mode="aram" />
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
