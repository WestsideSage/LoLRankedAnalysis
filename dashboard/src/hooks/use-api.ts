import { useState, useEffect } from 'react';
import type { OverviewData, RankedAnalysis, AramAnalysis, ArenaAnalysis } from '@/lib/types';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function buildUrl(path: string, params: Record<string, string | number | boolean>): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    search.set(k, String(v));
  }
  return `${path}?${search.toString()}`;
}

function useApiCall<T>(url: string | null): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({ data: null, loading: false, error: null });

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    setState({ data: null, loading: true, error: null });
    fetch(url)
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? `HTTP ${res.status}`);
        }
        return res.json() as Promise<T>;
      })
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null });
      })
      .catch((err: Error) => {
        if (!cancelled) setState({ data: null, loading: false, error: err.message });
      });
    return () => { cancelled = true; };
  }, [url]);

  return state;
}

export function useOverview(gameName: string, tagLine: string, region: string) {
  const url = gameName && tagLine
    ? buildUrl('/api/overview', { game_name: gameName, tag_line: tagLine, region })
    : null;
  return useApiCall<OverviewData>(url);
}

export function useRankedAnalysis(
  gameName: string, tagLine: string, region: string, matches: number
) {
  const url = gameName && tagLine
    ? buildUrl('/api/ranked', { game_name: gameName, tag_line: tagLine, region, matches })
    : null;
  return useApiCall<RankedAnalysis>(url);
}

export function useAramAnalysis(
  gameName: string, tagLine: string, region: string, matches: number, mayhem: boolean
) {
  const url = gameName && tagLine
    ? buildUrl('/api/aram', { game_name: gameName, tag_line: tagLine, region, matches, mayhem })
    : null;
  return useApiCall<AramAnalysis>(url);
}

export function useArenaAnalysis(
  gameName: string, tagLine: string, region: string, matches: number
) {
  const url = gameName && tagLine
    ? buildUrl('/api/arena', { game_name: gameName, tag_line: tagLine, region, matches })
    : null;
  return useApiCall<ArenaAnalysis>(url);
}
