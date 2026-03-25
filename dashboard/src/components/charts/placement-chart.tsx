import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import type { RecentMatch } from '@/lib/types';

interface Props {
  matches: RecentMatch[];
}

export function PlacementChart({ matches }: Props) {
  const counts = Array.from({ length: 8 }, (_, i) => ({
    place: `#${i + 1}`,
    count: matches.filter((m) => m.placement === i + 1).length,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={counts} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
        <XAxis dataKey="place" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
        <YAxis allowDecimals={false} tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} />
        <Tooltip
          contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'white', fontSize: 12 }}
          formatter={(v) => [v, 'Games']}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {counts.map((_entry, i) => (
            <Cell
              key={i}
              fill={i <= 3 ? '#10b981' : i <= 5 ? '#3b82f6' : '#ef4444'}
              fillOpacity={0.7}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
