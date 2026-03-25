import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip,
} from 'recharts';

interface RadarPoint {
  subject: string;
  value: number;
  fullMark: number;
}

interface Props {
  data: RadarPoint[];
  color?: string;
}

export function PlayerRadarChart({ data, color = '#3b82f6' }: Props) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
        <PolarGrid stroke="rgba(255,255,255,0.1)" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
        />
        <Radar
          name="You"
          dataKey="value"
          stroke={color}
          fill={color}
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Tooltip
          contentStyle={{
            background: '#0f0f1a', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px', color: 'white', fontSize: 12,
          }}
          formatter={(v) => [`${v}%`, '']}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
