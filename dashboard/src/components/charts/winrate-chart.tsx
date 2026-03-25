import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { RecentMatch } from '@/lib/types';

interface Props {
  matches: RecentMatch[];
}

export function WinRateChart({ matches }: Props) {
  // Build cumulative win rate over the last N games (oldest first)
  const reversed = [...matches].reverse();
  let wins = 0;
  const data = reversed.map((m, i) => {
    if (m.win) wins++;
    return { game: i + 1, wr: Math.round((wins / (i + 1)) * 100) };
  });

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="game" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} label={{ value: 'Games (oldest→newest)', position: 'insideBottom', offset: -3, fill: 'rgba(255,255,255,0.2)', fontSize: 10 }} />
        <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
        <ReferenceLine y={50} stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" />
        <Tooltip
          contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'white', fontSize: 12 }}
          formatter={(v) => [`${v}%`, 'Win Rate']}
          labelFormatter={(l) => `After ${l} game${l === 1 ? '' : 's'}`}
        />
        <Line type="monotone" dataKey="wr" stroke="#3b82f6" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
