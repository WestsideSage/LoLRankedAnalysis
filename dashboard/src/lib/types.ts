export interface KDA {
  kills: number;
  deaths: number;
  assists: number;
  ratio: number;
}

export interface RankInfo {
  tier: string;
  rank: string;
  lp: number;
  wins: number;
  losses: number;
  win_rate: number;
  hot_streak?: boolean;
}

export interface ChampionStat {
  games: number;
  wins?: number;
  win_rate?: number;
  avg_kills: number;
  avg_deaths: number;
  avg_assists: number;
  avg_damage: number;
  avg_cs_per_min?: number;
  avg_damage_per_min?: number;
  avg_placement?: number;
  top4_rate?: number;
}

export interface RoleStat {
  games: number;
  win_rate: number;
  avg_kills: number;
  avg_deaths: number;
  avg_assists: number;
  avg_cs_per_min: number;
  avg_vision_per_min: number;
}

export interface RecentMatch {
  champion: string;
  role?: string;
  win?: boolean;
  placement?: number;
  kda: string;
  damage: number;
  cs?: number;
  cs_per_min?: number;
  kill_participation?: number;
  damage_per_min?: number;
  damage_share?: number;
  duration_minutes?: number;
}

export interface OverviewData {
  display_name: string;
  puuid: string;
  rank_info: RankInfo | Record<string, never>;
  queue_counts: { ranked: number; aram: number; arena: number };
}

export interface RankedAnalysis {
  display_name: string;
  rank_info: RankInfo;
  total_matches: number;
  wins: number;
  losses: number;
  win_rate: number;
  average_kda: KDA;
  avg_damage: number;
  avg_gold: number;
  avg_cs_per_min: number;
  avg_vision_per_min: number;
  avg_kill_participation: number;
  avg_damage_share: number;
  champion_stats: Record<string, ChampionStat>;
  role_stats: Record<string, RoleStat>;
  recent_performance: RecentMatch[];
  strengths: string[];
  weaknesses: string[];
}

export interface AramAnalysis {
  display_name: string;
  mode: string;
  total_matches: number;
  wins: number;
  losses: number;
  win_rate: number;
  average_kda: KDA;
  avg_damage: number;
  avg_damage_per_min: number;
  avg_gold_per_min: number;
  avg_kill_participation: number;
  avg_damage_share: number;
  avg_damage_taken: number;
  avg_healing: number;
  pentakills: number;
  quadrakills: number;
  champion_stats: Record<string, ChampionStat>;
  recent_performance: RecentMatch[];
  strengths: string[];
  weaknesses: string[];
}

export interface ArenaAnalysis {
  display_name: string;
  mode: string;
  total_matches: number;
  avg_placement: number;
  top4_rate: number;
  top4_count: number;
  first_count: number;
  first_rate: number;
  average_kda: KDA;
  avg_damage: number;
  champion_stats: Record<string, ChampionStat>;
  recent_performance: RecentMatch[];
  strengths: string[];
  weaknesses: string[];
}

export type QueueType = 'ranked' | 'aram' | 'mayhem' | 'arena';
