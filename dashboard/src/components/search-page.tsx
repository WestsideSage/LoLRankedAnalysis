import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Clock, X, Swords } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const REGIONS = [
  { value: 'na1', label: 'NA' },
  { value: 'euw1', label: 'EUW' },
  { value: 'eun1', label: 'EUNE' },
  { value: 'kr', label: 'KR' },
  { value: 'jp1', label: 'JP' },
  { value: 'br1', label: 'BR' },
  { value: 'la1', label: 'LAN' },
  { value: 'la2', label: 'LAS' },
  { value: 'oc1', label: 'OCE' },
  { value: 'tr1', label: 'TR' },
  { value: 'ru', label: 'RU' },
];

interface RecentSearch {
  riotId: string;
  region: string;
}

const STORAGE_KEY = 'lol-recent-searches';

function loadRecent(): RecentSearch[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]');
  } catch {
    return [];
  }
}

function saveRecent(entry: RecentSearch) {
  const existing = loadRecent().filter(
    (r) => !(r.riotId === entry.riotId && r.region === entry.region)
  );
  localStorage.setItem(STORAGE_KEY, JSON.stringify([entry, ...existing].slice(0, 5)));
}

function removeRecent(entry: RecentSearch) {
  const updated = loadRecent().filter(
    (r) => !(r.riotId === entry.riotId && r.region === entry.region)
  );
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}

export function SearchPage() {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [region, setRegion] = useState('na1');
  const [recent, setRecent] = useState<RecentSearch[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    setRecent(loadRecent());
  }, []);

  function submit(riotId: string, reg: string) {
    const parts = riotId.split('#');
    if (parts.length !== 2 || !parts[0].trim() || !parts[1].trim()) {
      setError('Enter a Riot ID in "Name#TAG" format');
      return;
    }
    setError('');
    const entry = { riotId: riotId.trim(), region: reg };
    saveRecent(entry);
    setRecent(loadRecent());
    const [name, tag] = parts;
    navigate(`/player/${encodeURIComponent(name.trim())}/${encodeURIComponent(tag.trim())}?region=${reg}`);
  }

  function handleRemove(e: React.MouseEvent, entry: RecentSearch) {
    e.stopPropagation();
    removeRecent(entry);
    setRecent(loadRecent());
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/4 w-[300px] h-[300px] bg-purple-600/8 rounded-full blur-[100px] pointer-events-none" />

      <div className="relative z-10 w-full max-w-xl flex flex-col items-center gap-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 backdrop-blur-sm">
            <Swords className="w-10 h-10 text-blue-400" />
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-400 via-purple-400 to-blue-300 bg-clip-text text-transparent">
              LoL Stats
            </h1>
            <p className="text-white/40 text-sm mt-1">Analyze your League of Legends performance</p>
          </div>
        </div>

        {/* Search card */}
        <div className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md shadow-2xl">
          <div className="flex gap-2 mb-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
              <Input
                placeholder="GameName#TAG"
                value={input}
                onChange={(e) => { setInput(e.target.value); setError(''); }}
                onKeyDown={(e) => e.key === 'Enter' && submit(input, region)}
                className="pl-9 bg-white/5 border-white/10 text-white placeholder:text-white/30 focus:border-blue-500/50 focus:ring-blue-500/20"
              />
            </div>
            <Select value={region} onValueChange={(v) => v && setRegion(v)}>
              <SelectTrigger className="w-24 bg-white/5 border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#0f0f1a] border-white/10">
                {REGIONS.map((r) => (
                  <SelectItem key={r.value} value={r.value} className="text-white hover:bg-white/10 focus:bg-white/10">
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {error && <p className="text-red-400 text-xs mb-3">{error}</p>}

          <Button
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all duration-200 shadow-lg shadow-blue-600/20"
            onClick={() => submit(input, region)}
          >
            Search
          </Button>
        </div>

        {/* Recent searches */}
        {recent.length > 0 && (
          <div className="w-full">
            <p className="text-white/30 text-xs uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Clock className="w-3 h-3" /> Recent
            </p>
            <div className="flex flex-col gap-1.5">
              {recent.map((r) => (
                <button
                  key={`${r.riotId}-${r.region}`}
                  onClick={() => submit(r.riotId, r.region)}
                  className="flex items-center justify-between px-4 py-2.5 rounded-xl bg-white/4 border border-white/6 hover:bg-white/8 hover:border-white/12 transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-white/80 text-sm">{r.riotId}</span>
                    <span className="text-white/30 text-xs uppercase">{REGIONS.find(reg => reg.value === r.region)?.label ?? r.region}</span>
                  </div>
                  <X
                    className="w-3.5 h-3.5 text-white/20 group-hover:text-white/50 transition-colors"
                    onClick={(e) => handleRemove(e, r)}
                  />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
