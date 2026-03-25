import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import type { ChampionStat } from '@/lib/types';

type Mode = 'ranked' | 'aram' | 'arena';
type SortKey = 'games' | 'win_rate' | 'avg_kills' | 'avg_damage' | 'avg_placement' | 'top4_rate';

interface Props {
  data: Record<string, ChampionStat>;
  mode?: Mode;
}

export function ChampionTable({ data, mode = 'ranked' }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>(mode === 'arena' ? 'avg_placement' : 'games');
  const [sortAsc, setSortAsc] = useState(mode === 'arena');

  const rows = Object.entries(data).sort(([, a], [, b]) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
  });

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(key === 'avg_placement'); }
  }

  function SortIcon({ k }: { k: SortKey }) {
    if (sortKey !== k) return <ChevronDown className="w-3 h-3 opacity-20" />;
    return sortAsc
      ? <ChevronUp className="w-3 h-3 text-blue-400" />
      : <ChevronDown className="w-3 h-3 text-blue-400" />;
  }

  function TH({ label, k }: { label: string; k: SortKey }) {
    return (
      <TableHead
        className="text-white/40 text-xs uppercase cursor-pointer hover:text-white/70 transition-colors select-none"
        onClick={() => toggleSort(k)}
      >
        <div className="flex items-center gap-1">{label}<SortIcon k={k} /></div>
      </TableHead>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="border-white/8 hover:bg-transparent">
            <TableHead className="text-white/40 text-xs uppercase">Champion</TableHead>
            <TH label="Games" k="games" />
            {mode === 'arena' ? (
              <>
                <TH label="Avg Place" k="avg_placement" />
                <TH label="Top 4%" k="top4_rate" />
              </>
            ) : (
              <TH label="Win Rate" k="win_rate" />
            )}
            <TableHead className="text-white/40 text-xs uppercase">KDA</TableHead>
            <TH label="Avg Dmg" k="avg_damage" />
            {mode === 'ranked' && <TableHead className="text-white/40 text-xs uppercase">CS/m</TableHead>}
            {mode === 'aram' && <TableHead className="text-white/40 text-xs uppercase">Dmg/m</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map(([champ, s]) => (
            <TableRow key={champ} className="border-white/5 hover:bg-white/4">
              <TableCell className="font-medium text-white">{champ}</TableCell>
              <TableCell className="text-white/70">{s.games}</TableCell>
              {mode === 'arena' ? (
                <>
                  <TableCell className={`font-semibold ${(s.avg_placement ?? 8) <= 3 ? 'text-emerald-400' : (s.avg_placement ?? 8) >= 6 ? 'text-red-400' : 'text-white/70'}`}>
                    {s.avg_placement?.toFixed(1) ?? '—'}
                  </TableCell>
                  <TableCell className="text-white/70">{s.top4_rate?.toFixed(0) ?? '—'}%</TableCell>
                </>
              ) : (
                <TableCell className={`font-semibold ${(s.win_rate ?? 0) >= 55 ? 'text-emerald-400' : (s.win_rate ?? 0) < 45 ? 'text-red-400' : 'text-white/70'}`}>
                  {s.win_rate?.toFixed(0) ?? '—'}%
                </TableCell>
              )}
              <TableCell className="text-white/70 font-mono text-xs">
                {s.avg_kills}/{s.avg_deaths}/{s.avg_assists}
              </TableCell>
              <TableCell className="text-white/70">{s.avg_damage.toLocaleString()}</TableCell>
              {mode === 'ranked' && (
                <TableCell className="text-white/70">{s.avg_cs_per_min?.toFixed(1) ?? '—'}</TableCell>
              )}
              {mode === 'aram' && (
                <TableCell className="text-white/70">{s.avg_damage_per_min?.toFixed(0) ?? '—'}</TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
