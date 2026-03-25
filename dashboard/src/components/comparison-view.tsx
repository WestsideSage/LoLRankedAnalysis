import { useState } from 'react';
import { X, Plus, Trophy } from 'lucide-react';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip, Legend,
} from 'recharts';
import { Layout } from './layout';
import { useRankedAnalysis, useAramAnalysis, useArenaAnalysis } from '@/hooks/use-api';
import { Input } from '@/components/ui/input';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import type { RankedAnalysis, AramAnalysis, ArenaAnalysis } from '@/lib/types';

type QueueMode = 'ranked' | 'aram' | 'arena';

const PLAYER_COLORS = ['#3b82f6', '#a855f7', '#f97316'];

const REGIONS = [
  { value: 'na1', label: 'NA' }, { value: 'euw1', label: 'EUW' },
  { value: 'eun1', label: 'EUNE' }, { value: 'kr', label: 'KR' },
  { value: 'jp1', label: 'JP' }, { value: 'br1', label: 'BR' },
];

interface PlayerEntry {
  input: string;
  name: string;
  tag: string;
  region: string;
}

function parseRiotId(input: string): { name: string; tag: string } | null {
  const parts = input.split('#');
  if (parts.length !== 2 || !parts[0].trim() || !parts[1].trim()) return null;
  return { name: parts[0].trim(), tag: parts[1].trim() };
}

function buildRankedRadar(d: RankedAnalysis) {
  return [
    { subject: 'Win Rate', value: d.win_rate },
    { subject: 'KDA', value: Math.min(100, Math.round((d.average_kda.ratio / 5) * 100)) },
    { subject: 'Damage', value: Math.min(100, Math.round((d.avg_damage / 25000) * 100)) },
    { subject: 'CS/min', value: Math.min(100, Math.round((d.avg_cs_per_min / 8) * 100)) },
    { subject: 'Kill Part.', value: Math.min(100, d.avg_kill_participation) },
    { subject: 'Vision', value: Math.min(100, Math.round((d.avg_vision_per_min / 1.5) * 100)) },
  ];
}

function buildAramRadar(d: AramAnalysis) {
  return [
    { subject: 'Win Rate', value: d.win_rate },
    { subject: 'KDA', value: Math.min(100, Math.round((d.average_kda.ratio / 6) * 100)) },
    { subject: 'Dmg/min', value: Math.min(100, Math.round((d.avg_damage_per_min / 1500) * 100)) },
    { subject: 'Kill Part.', value: Math.min(100, d.avg_kill_participation) },
    { subject: 'Dmg Share', value: Math.min(100, Math.round(d.avg_damage_share * 1.5)) },
  ];
}

function buildArenaRadar(d: ArenaAnalysis) {
  return [
    { subject: 'Avg Place', value: Math.round(((8 - d.avg_placement) / 7) * 100) },
    { subject: 'Top 4%', value: Math.round(d.top4_rate) },
    { subject: '1st Place%', value: Math.min(100, Math.round(d.first_rate)) },
    { subject: 'KDA', value: Math.min(100, Math.round((d.average_kda.ratio / 6) * 100)) },
    { subject: 'Damage', value: Math.min(100, Math.round((d.avg_damage / 25000) * 100)) },
  ];
}

function StatBar({ label, values, colors, names }: {
  label: string;
  values: number[];
  colors: string[];
  names: string[];
}) {
  const max = Math.max(...values, 1);
  const winnerIdx = values.indexOf(Math.max(...values));
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-white/50 text-xs uppercase tracking-wider">{label}</span>
        <span className="text-xs" style={{ color: colors[winnerIdx] }}>
          {names[winnerIdx]} wins
        </span>
      </div>
      {values.map((v, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="w-20 text-xs truncate" style={{ color: colors[i] }}>{names[i]}</span>
          <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${(v / max) * 100}%`, background: colors[i] }}
            />
          </div>
          <span className="text-white/50 text-xs w-12 text-right">{typeof v === 'number' && v > 100 ? v.toLocaleString() : `${v}%` }</span>
        </div>
      ))}
    </div>
  );
}

function PlayerDataLoader({
  player, mode, color, onData,
}: {
  player: PlayerEntry;
  mode: QueueMode;
  color: string;
  onData: (name: string, data: RankedAnalysis | AramAnalysis | ArenaAnalysis | null) => void;
}) {
  const ranked = useRankedAnalysis(player.name, player.tag, player.region, 20);
  const aram = useAramAnalysis(player.name, player.tag, player.region, 30, false);
  const arena = useArenaAnalysis(player.name, player.tag, player.region, 30);

  const active = mode === 'ranked' ? ranked : mode === 'aram' ? aram : arena;

  if (active.error) {
    return (
      <div className="text-red-400 text-xs bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
        {player.input}: {active.error}
      </div>
    );
  }

  if (active.loading) {
    return (
      <div className="flex items-center gap-2 text-xs" style={{ color }}>
        <div className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
        Loading {player.input}...
      </div>
    );
  }

  if (active.data && !active.loading) {
    onData(player.input, active.data);
  }

  return null;
}

export function ComparisonView() {
  const [players, setPlayers] = useState<PlayerEntry[]>([]);
  const [inputDraft, setInputDraft] = useState('');
  const [regionDraft, setRegionDraft] = useState('na1');
  const [mode, setMode] = useState<QueueMode>('aram');
  const [inputError, setInputError] = useState('');
  const [playerData, setPlayerData] = useState<Record<string, RankedAnalysis | AramAnalysis | ArenaAnalysis>>({});

  function addPlayer() {
    const parsed = parseRiotId(inputDraft);
    if (!parsed) { setInputError('Enter a Riot ID in "Name#TAG" format'); return; }
    if (players.length >= 3) { setInputError('Max 3 players'); return; }
    if (players.some((p) => p.input.toLowerCase() === inputDraft.toLowerCase())) {
      setInputError('Already added'); return;
    }
    setInputError('');
    setPlayers([...players, { input: inputDraft.trim(), ...parsed, region: regionDraft }]);
    setInputDraft('');
  }

  function removePlayer(input: string) {
    setPlayers(players.filter((p) => p.input !== input));
    setPlayerData((prev) => { const n = { ...prev }; delete n[input]; return n; });
  }

  function handleData(name: string, data: RankedAnalysis | AramAnalysis | ArenaAnalysis | null) {
    if (data) setPlayerData((prev) => ({ ...prev, [name]: data }));
  }

  // Build combined radar data
  const radarSubjects: string[] = (() => {
    if (mode === 'ranked') return ['Win Rate', 'KDA', 'Damage', 'CS/min', 'Kill Part.', 'Vision'];
    if (mode === 'aram') return ['Win Rate', 'KDA', 'Dmg/min', 'Kill Part.', 'Dmg Share'];
    return ['Avg Place', 'Top 4%', '1st Place%', 'KDA', 'Damage'];
  })();

  const radarData = radarSubjects.map((subject) => {
    const point: Record<string, number | string> = { subject };
    players.forEach((p) => {
      const d = playerData[p.input];
      if (!d) return;
      const arr = mode === 'ranked'
        ? buildRankedRadar(d as RankedAnalysis)
        : mode === 'aram'
          ? buildAramRadar(d as AramAnalysis)
          : buildArenaRadar(d as ArenaAnalysis);
      const found = arr.find((r) => r.subject === subject);
      if (found) point[p.input] = found.value;
    });
    return point;
  });

  // Summary scores for "winner" badge
  const scores: Record<string, number> = {};
  players.forEach((p) => {
    const d = playerData[p.input];
    if (!d) return;
    const arr = mode === 'ranked'
      ? buildRankedRadar(d as RankedAnalysis)
      : mode === 'aram'
        ? buildAramRadar(d as AramAnalysis)
        : buildArenaRadar(d as ArenaAnalysis);
    scores[p.input] = arr.reduce((s, r) => s + r.value, 0) / arr.length;
  });
  const winner = players.reduce<string | null>((best, p) => {
    if (!playerData[p.input]) return best;
    if (!best || (scores[p.input] ?? 0) > (scores[best] ?? 0)) return p.input;
    return best;
  }, null);

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">
        <div>
          <h1 className="text-2xl font-bold">Player Comparison</h1>
          <p className="text-white/40 text-sm mt-1">Roast your friends with data-backed statistics</p>
        </div>

        {/* Controls */}
        <div className="bg-white/4 border border-white/8 rounded-2xl p-5 flex flex-col gap-4">
          <div className="flex gap-3">
            <Select value={mode} onValueChange={(v) => v && setMode(v as QueueMode)}>
              <SelectTrigger className="w-36 bg-white/5 border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#0f0f1a] border-white/10">
                <SelectItem value="ranked" className="text-white focus:bg-white/10">Ranked</SelectItem>
                <SelectItem value="aram" className="text-white focus:bg-white/10">ARAM</SelectItem>
                <SelectItem value="arena" className="text-white focus:bg-white/10">Arena</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="GameName#TAG"
              value={inputDraft}
              onChange={(e) => { setInputDraft(e.target.value); setInputError(''); }}
              onKeyDown={(e) => e.key === 'Enter' && addPlayer()}
              className="flex-1 bg-white/5 border-white/10 text-white placeholder:text-white/30"
              disabled={players.length >= 3}
            />
            <Select value={regionDraft} onValueChange={(v) => v && setRegionDraft(v)}>
              <SelectTrigger className="w-20 bg-white/5 border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#0f0f1a] border-white/10">
                {REGIONS.map((r) => (
                  <SelectItem key={r.value} value={r.value} className="text-white focus:bg-white/10">{r.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              onClick={addPlayer}
              disabled={players.length >= 3}
              className="bg-blue-600 hover:bg-blue-500 text-white"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
          {inputError && <p className="text-red-400 text-xs">{inputError}</p>}

          {/* Player tags */}
          {players.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {players.map((p, i) => (
                <div
                  key={p.input}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm"
                  style={{ borderColor: PLAYER_COLORS[i] + '40', background: PLAYER_COLORS[i] + '15' }}
                >
                  <span style={{ color: PLAYER_COLORS[i] }}>{p.input}</span>
                  <span className="text-white/30 text-xs">{p.region.toUpperCase()}</span>
                  <button onClick={() => removePlayer(p.input)} className="text-white/30 hover:text-white/60 ml-1">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Data loaders (invisible) */}
        {players.map((p, i) => (
          <div key={p.input} className="hidden">
            <PlayerDataLoader
              player={p}
              mode={mode}
              color={PLAYER_COLORS[i]}
              onData={handleData}
            />
          </div>
        ))}

        {/* Loading/error messages */}
        <div className="flex flex-col gap-2">
          {players.map((p, i) => {
            const d = playerData[p.input];
            if (d) return null;
            return (
              <div key={p.input} className="flex items-center gap-2 text-xs" style={{ color: PLAYER_COLORS[i] }}>
                <div className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
                Loading {p.input}...
              </div>
            );
          })}
        </div>

        {/* Results */}
        {players.length >= 2 && Object.keys(playerData).length >= 2 && (
          <>
            {/* Winner badge */}
            {winner && (
              <div className="flex items-center gap-3 bg-yellow-500/10 border border-yellow-500/20 rounded-2xl px-5 py-4">
                <Trophy className="w-6 h-6 text-yellow-400" />
                <div>
                  <p className="text-yellow-300 font-bold text-lg">{winner}</p>
                  <p className="text-yellow-300/60 text-xs">Overall better in {mode === 'arena' ? 'Arena' : mode === 'aram' ? 'ARAM' : 'Ranked'}</p>
                </div>
              </div>
            )}

            {/* Overlay radar */}
            <div className="bg-white/4 border border-white/8 rounded-2xl p-5">
              <h2 className="text-white/60 text-xs uppercase tracking-widest mb-4 font-semibold">Radar Comparison</h2>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                  {players.map((p, i) => playerData[p.input] && (
                    <Radar
                      key={p.input}
                      name={p.input}
                      dataKey={p.input}
                      stroke={PLAYER_COLORS[i]}
                      fill={PLAYER_COLORS[i]}
                      fillOpacity={0.15}
                      strokeWidth={2}
                    />
                  ))}
                  <Legend wrapperStyle={{ fontSize: 12, color: 'rgba(255,255,255,0.6)' }} />
                  <Tooltip
                    contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'white', fontSize: 12 }}
                    formatter={(v) => [`${v}%`, '']}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Stat bars */}
            {(() => {
              const activePlayers = players.filter((p) => playerData[p.input]);
              const names = activePlayers.map((p) => p.input);
              const colors = activePlayers.map((_, i) => PLAYER_COLORS[i]);

              const stats: Array<{ label: string; key: string }> = mode === 'ranked'
                ? [
                    { label: 'Win Rate %', key: 'win_rate' },
                    { label: 'KDA Ratio', key: 'average_kda' },
                    { label: 'Avg Damage', key: 'avg_damage' },
                    { label: 'Kill Part. %', key: 'avg_kill_participation' },
                  ]
                : mode === 'aram'
                  ? [
                      { label: 'Win Rate %', key: 'win_rate' },
                      { label: 'KDA Ratio', key: 'average_kda' },
                      { label: 'Dmg/min', key: 'avg_damage_per_min' },
                      { label: 'Kill Part. %', key: 'avg_kill_participation' },
                    ]
                  : [
                      { label: 'Top 4 Rate %', key: 'top4_rate' },
                      { label: 'KDA Ratio', key: 'average_kda' },
                      { label: 'Avg Damage', key: 'avg_damage' },
                      { label: '1st Place %', key: 'first_rate' },
                    ];

              return (
                <div className="bg-white/4 border border-white/8 rounded-2xl p-5 flex flex-col gap-5">
                  <h2 className="text-white/60 text-xs uppercase tracking-widest font-semibold">Head-to-Head</h2>
                  {stats.map(({ label, key }) => {
                    const values = activePlayers.map((p) => {
                      const d = playerData[p.input] as unknown as Record<string, unknown>;
                      const v = d?.[key];
                      if (v === null || v === undefined) return 0;
                      if (typeof v === 'object' && v !== null && 'ratio' in v) return (v as { ratio: number }).ratio;
                      return typeof v === 'number' ? v : 0;
                    });
                    return <StatBar key={label} label={label} values={values} colors={colors} names={names} />;
                  })}
                </div>
              );
            })()}
          </>
        )}

        {players.length < 2 && (
          <p className="text-white/20 text-sm text-center py-8">Add at least 2 players to compare</p>
        )}
      </div>
    </Layout>
  );
}
