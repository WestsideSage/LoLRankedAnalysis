import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import type { ChampionStat } from '@/lib/types';

interface Props {
  data: Record<string, ChampionStat>;
  mode?: 'winrate' | 'placement';
}

export function ChampionBarChart({ data, mode = 'winrate' }: Props) {
  const entries = Object.entries(data)
    .filter(([, s]) => s.games >= 2)
    .sort(([, a], [, b]) =>
      mode === 'placement'
        ? (a.avg_placement ?? 8) - (b.avg_placement ?? 8)
        : (b.win_rate ?? 0) - (a.win_rate ?? 0)
    )
    .slice(0, 10)
    .map(([champ, s]) => ({
      name: champ,
      value: mode === 'placement' ? (s.avg_placement ?? 8) : (s.win_rate ?? 0),
    }));

  if (entries.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, entries.length * 32)}>
      <BarChart data={entries} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
        <XAxis
          type="number"
          domain={mode === 'placement' ? [1, 8] : [0, 100]}
          tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }}
          tickFormatter={(v) => mode === 'placement' ? `#${v}` : `${v}%`}
        />
        <YAxis type="category" dataKey="name" width={90} tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }} />
        <Tooltip
          contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'white', fontSize: 12 }}
          formatter={(v) => [mode === 'placement' ? `#${Number(v).toFixed(1)}` : `${v}%`, mode === 'placement' ? 'Avg Place' : 'Win Rate']}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {entries.map((e, i) => {
            const good = mode === 'placement' ? e.value <= 3.5 : e.value >= 55;
            const bad = mode === 'placement' ? e.value >= 6 : e.value < 45;
            return (
              <Cell
                key={i}
                fill={good ? '#10b981' : bad ? '#ef4444' : '#3b82f6'}
                fillOpacity={0.7}
              />
            );
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
