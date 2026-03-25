"""
Analysis engine for League of Legends match data.

Produces overall stats, per-champion stats, per-role stats,
and identifies concrete strengths and weaknesses.
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
import statistics

from .riot_api import RiotAPIClient


# ── Rank-tier benchmarks (approximate per-game averages) ─────────────
# Sources: leagueofgraphs / op.gg aggregate data.
# Keys: cs_per_min, vision_per_min, kda_ratio, kill_participation, damage_share
TIER_BENCHMARKS = {
    'IRON':       {'cs_per_min': 4.0, 'vision_per_min': 0.30, 'kda_ratio': 1.5, 'kill_part': 0.45, 'dmg_share': 0.20},
    'BRONZE':     {'cs_per_min': 4.5, 'vision_per_min': 0.35, 'kda_ratio': 1.8, 'kill_part': 0.48, 'dmg_share': 0.20},
    'SILVER':     {'cs_per_min': 5.2, 'vision_per_min': 0.40, 'kda_ratio': 2.0, 'kill_part': 0.50, 'dmg_share': 0.20},
    'GOLD':       {'cs_per_min': 5.8, 'vision_per_min': 0.45, 'kda_ratio': 2.3, 'kill_part': 0.52, 'dmg_share': 0.20},
    'PLATINUM':   {'cs_per_min': 6.3, 'vision_per_min': 0.50, 'kda_ratio': 2.5, 'kill_part': 0.54, 'dmg_share': 0.20},
    'EMERALD':    {'cs_per_min': 6.6, 'vision_per_min': 0.55, 'kda_ratio': 2.7, 'kill_part': 0.55, 'dmg_share': 0.20},
    'DIAMOND':    {'cs_per_min': 7.0, 'vision_per_min': 0.60, 'kda_ratio': 2.9, 'kill_part': 0.56, 'dmg_share': 0.20},
    'MASTER':     {'cs_per_min': 7.5, 'vision_per_min': 0.65, 'kda_ratio': 3.2, 'kill_part': 0.58, 'dmg_share': 0.20},
    'GRANDMASTER':{'cs_per_min': 7.8, 'vision_per_min': 0.68, 'kda_ratio': 3.4, 'kill_part': 0.59, 'dmg_share': 0.20},
    'CHALLENGER': {'cs_per_min': 8.0, 'vision_per_min': 0.70, 'kda_ratio': 3.6, 'kill_part': 0.60, 'dmg_share': 0.20},
}

# Role-specific CS expectations (multiplier on the tier benchmark)
ROLE_CS_MULTIPLIER = {
    'TOP': 1.0,
    'JUNGLE': 0.85,   # jungle CS counted differently
    'MIDDLE': 1.0,
    'BOTTOM': 1.05,
    'UTILITY': 0.30,   # supports don't farm
}


class MatchAnalyzer:
    """Analyzes League of Legends match data and identifies strengths/weaknesses."""

    def __init__(self, api_client: RiotAPIClient):
        self.api_client = api_client

    # ── Core analysis ─────────────────────────────────────────────────

    def analyze_matches(
        self,
        puuid: str,
        match_count: int = 20,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the full analysis pipeline for a player's recent ranked games."""

        matches = self.api_client.get_recent_matches(puuid, match_count)

        rank_info = {}
        if puuid:
            entries = self.api_client.get_rank_entries(puuid)
            for e in entries:
                if e.queue_type == 'RANKED_SOLO_5x5':
                    total = e.wins + e.losses
                    rank_info = {
                        'tier': e.tier,
                        'rank': e.rank,
                        'lp': e.league_points,
                        'wins': e.wins,
                        'losses': e.losses,
                        'win_rate': round((e.wins / total) * 100, 1) if total else 0,
                        'hot_streak': e.hot_streak,
                    }

        # ── Accumulate per-game stats ─────────────────────────────────
        games_parsed = 0
        wins = 0
        all_kills, all_deaths, all_assists = [], [], []
        all_damage, all_cs_per_min, all_vision_per_min = [], [], []
        all_gold, all_kill_participation = [], []
        all_damage_share = []
        champion_stats: Dict[str, Dict] = defaultdict(lambda: {
            'games': 0, 'wins': 0,
            'kills': [], 'deaths': [], 'assists': [],
            'cs_per_min': [], 'damage': [],
        })
        role_stats: Dict[str, Dict] = defaultdict(lambda: {
            'games': 0, 'wins': 0,
            'kills': [], 'deaths': [], 'assists': [],
            'cs_per_min': [], 'damage': [], 'vision_per_min': [],
        })
        recent_performance = []
        first_blood_kills = 0
        first_blood_deaths = 0
        early_deaths = []  # deaths at < 15 min indicator
        games_with_high_deaths = 0

        for match in matches:
            player = self._find_player(match, puuid)
            if not player:
                continue

            games_parsed += 1
            info = match['info']
            duration_min = info['gameDuration'] / 60
            if duration_min < 5:
                # Remake / early surrender -skip
                games_parsed -= 1
                continue

            won = player['win']
            if won:
                wins += 1

            kills = player['kills']
            deaths = player['deaths']
            assists = player['assists']
            damage = player['totalDamageDealtToChampions']
            # Total CS = lane minions + jungle monsters
            cs = player['totalMinionsKilled'] + player.get('neutralMinionsKilled', 0)
            cs_per_min = cs / duration_min
            vision = player['visionScore']
            vision_per_min = vision / duration_min
            gold = player['goldEarned']
            role = player.get('teamPosition', player.get('individualPosition', 'UNKNOWN'))
            champion = player['championName']

            # Kill participation: (kills+assists) / team_total_kills
            team_id = player['teamId']
            team_kills = sum(
                p['kills'] for p in info['participants'] if p['teamId'] == team_id
            )
            kp = (kills + assists) / max(team_kills, 1)

            # Damage share within team
            team_damage = sum(
                p['totalDamageDealtToChampions']
                for p in info['participants']
                if p['teamId'] == team_id
            )
            dmg_share = damage / max(team_damage, 1)

            # First blood tracking
            if player.get('firstBloodKill'):
                first_blood_kills += 1
            if player.get('firstBloodAssist'):
                pass  # not penalized
            # Approximate "first blood death" -Riot doesn't expose this directly,
            # but we can check if the player has 0 kills and died within ~3 min
            # via timeline. We'll skip this for now and use deaths > 5 as a proxy.

            if deaths >= 6:
                games_with_high_deaths += 1

            # Accumulate
            all_kills.append(kills)
            all_deaths.append(deaths)
            all_assists.append(assists)
            all_damage.append(damage)
            all_cs_per_min.append(cs_per_min)
            all_vision_per_min.append(vision_per_min)
            all_gold.append(gold)
            all_kill_participation.append(kp)
            all_damage_share.append(dmg_share)

            # Champion stats
            cs_entry = champion_stats[champion]
            cs_entry['games'] += 1
            if won:
                cs_entry['wins'] += 1
            cs_entry['kills'].append(kills)
            cs_entry['deaths'].append(deaths)
            cs_entry['assists'].append(assists)
            cs_entry['cs_per_min'].append(cs_per_min)
            cs_entry['damage'].append(damage)

            # Role stats
            if role and role != 'UNKNOWN':
                rs = role_stats[role]
                rs['games'] += 1
                if won:
                    rs['wins'] += 1
                rs['kills'].append(kills)
                rs['deaths'].append(deaths)
                rs['assists'].append(assists)
                rs['cs_per_min'].append(cs_per_min)
                rs['damage'].append(damage)
                rs['vision_per_min'].append(vision_per_min)

            # Recent matches list (keep all for display, limit later)
            recent_performance.append({
                'champion': champion,
                'role': role,
                'win': won,
                'kda': f"{kills}/{deaths}/{assists}",
                'damage': damage,
                'cs': cs,
                'cs_per_min': round(cs_per_min, 1),
                'vision': vision,
                'duration_minutes': round(duration_min, 1),
                'kill_participation': round(kp * 100, 1),
            })

        # ── Compute aggregates ────────────────────────────────────────
        losses = games_parsed - wins
        win_rate = round((wins / games_parsed) * 100, 1) if games_parsed else 0

        def avg(lst):
            return round(statistics.mean(lst), 1) if lst else 0

        avg_kills = avg(all_kills)
        avg_deaths = avg(all_deaths)
        avg_assists = avg(all_assists)
        kda_ratio = round((avg_kills + avg_assists) / max(avg_deaths, 0.1), 2)
        avg_cs_per_min = avg(all_cs_per_min)
        avg_vision_per_min = avg(all_vision_per_min)
        avg_damage = round(statistics.mean(all_damage)) if all_damage else 0
        avg_gold = round(statistics.mean(all_gold)) if all_gold else 0
        avg_kp = avg([x * 100 for x in all_kill_participation])
        avg_dmg_share = avg([x * 100 for x in all_damage_share])

        # Finalize champion stats
        champion_summary = {}
        for champ, st in champion_stats.items():
            g = st['games']
            champion_summary[champ] = {
                'games': g,
                'wins': st['wins'],
                'win_rate': round((st['wins'] / g) * 100, 1) if g else 0,
                'avg_kills': avg(st['kills']),
                'avg_deaths': avg(st['deaths']),
                'avg_assists': avg(st['assists']),
                'avg_cs_per_min': avg(st['cs_per_min']),
                'avg_damage': round(statistics.mean(st['damage'])) if st['damage'] else 0,
            }

        # Finalize role stats
        role_summary = {}
        for role, st in role_stats.items():
            g = st['games']
            role_summary[role] = {
                'games': g,
                'wins': st['wins'],
                'win_rate': round((st['wins'] / g) * 100, 1) if g else 0,
                'avg_kills': avg(st['kills']),
                'avg_deaths': avg(st['deaths']),
                'avg_assists': avg(st['assists']),
                'avg_cs_per_min': avg(st['cs_per_min']),
                'avg_damage': round(statistics.mean(st['damage'])) if st['damage'] else 0,
                'avg_vision_per_min': avg(st['vision_per_min']),
            }

        # ── Strengths & Weaknesses ────────────────────────────────────
        tier = rank_info.get('tier', 'SILVER')  # default benchmark
        strengths, weaknesses = self._evaluate(
            tier=tier,
            win_rate=win_rate,
            kda_ratio=kda_ratio,
            avg_kills=avg_kills,
            avg_deaths=avg_deaths,
            avg_assists=avg_assists,
            avg_cs_per_min=avg_cs_per_min,
            avg_vision_per_min=avg_vision_per_min,
            avg_kp=avg_kp,
            avg_dmg_share=avg_dmg_share,
            games_with_high_deaths=games_with_high_deaths,
            games_parsed=games_parsed,
            first_blood_kills=first_blood_kills,
            role_summary=role_summary,
            champion_summary=champion_summary,
        )

        return {
            'display_name': display_name or 'Unknown',
            'rank_info': rank_info,
            'total_matches': games_parsed,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'average_kda': {
                'kills': avg_kills,
                'deaths': avg_deaths,
                'assists': avg_assists,
                'ratio': kda_ratio,
            },
            'avg_damage': avg_damage,
            'avg_gold': avg_gold,
            'avg_cs_per_min': avg_cs_per_min,
            'avg_vision_per_min': avg_vision_per_min,
            'avg_kill_participation': avg_kp,
            'avg_damage_share': avg_dmg_share,
            'champion_stats': champion_summary,
            'role_stats': role_summary,
            'recent_performance': recent_performance[:15],
            'strengths': strengths,
            'weaknesses': weaknesses,
        }

    # ── Strength/weakness evaluation ──────────────────────────────────

    def _evaluate(
        self, *, tier, win_rate, kda_ratio, avg_kills, avg_deaths, avg_assists,
        avg_cs_per_min, avg_vision_per_min, avg_kp, avg_dmg_share,
        games_with_high_deaths, games_parsed, first_blood_kills,
        role_summary, champion_summary,
    ):
        strengths: List[str] = []
        weaknesses: List[str] = []
        bench = TIER_BENCHMARKS.get(tier, TIER_BENCHMARKS['SILVER'])

        # Determine primary role for role-aware benchmarks
        primary_role = None
        if role_summary:
            primary_role_entry = max(role_summary.items(), key=lambda x: x[1]['games'])
            primary_role = primary_role_entry[0]

        # ── Win rate ──────────────────────────────────────────────────
        if win_rate >= 55:
            strengths.append(f"Strong win rate ({win_rate}%) - you're climbing")
        elif win_rate < 48 and games_parsed >= 10:
            weaknesses.append(
                f"Win rate is {win_rate}% over {games_parsed} games - "
                "consider focusing on fewer champions or reviewing losses"
            )

        # ── KDA / Deaths ─────────────────────────────────────────────
        if kda_ratio >= bench['kda_ratio'] * 1.2:
            strengths.append(
                f"Excellent KDA ratio ({kda_ratio}) - well above {tier} average "
                f"({bench['kda_ratio']})"
            )
        elif kda_ratio < bench['kda_ratio'] * 0.75:
            weaknesses.append(
                f"KDA ratio ({kda_ratio}) is below {tier} average ({bench['kda_ratio']})"
            )

        if avg_deaths >= 6:
            weaknesses.append(
                f"Averaging {avg_deaths} deaths/game - dying too often. "
                "Focus on positioning and knowing when to disengage"
            )
        elif avg_deaths <= 3.5:
            strengths.append(f"Low death average ({avg_deaths}) - good survivability")

        if games_parsed >= 5:
            death_pct = games_with_high_deaths / games_parsed
            if death_pct >= 0.4:
                weaknesses.append(
                    f"You had 6+ deaths in {games_with_high_deaths}/{games_parsed} "
                    "games - inconsistent survival"
                )

        # ── CS (role-aware) ───────────────────────────────────────────
        # Adjust the CS benchmark based on primary role so supports
        # aren't penalized for not farming
        cs_multiplier = ROLE_CS_MULTIPLIER.get(primary_role, 1.0) if primary_role else 1.0
        cs_bench = round(bench['cs_per_min'] * cs_multiplier, 1)

        if cs_multiplier >= 0.5:  # only evaluate CS for farming roles
            if avg_cs_per_min >= cs_bench * 1.1:
                strengths.append(
                    f"Great CS/min ({avg_cs_per_min}) - above {tier} average "
                    f"for your role ({cs_bench})"
                )
            elif avg_cs_per_min < cs_bench * 0.85:
                weaknesses.append(
                    f"CS/min ({avg_cs_per_min}) is below {tier} average "
                    f"for your role ({cs_bench}) - practice last-hitting and wave management"
                )

        # ── Vision ────────────────────────────────────────────────────
        if avg_vision_per_min >= bench['vision_per_min'] * 1.2:
            strengths.append(
                f"Strong vision score ({avg_vision_per_min}/min) - good map awareness"
            )
        elif avg_vision_per_min < bench['vision_per_min'] * 0.7:
            weaknesses.append(
                f"Low vision score ({avg_vision_per_min}/min) - "
                "place more wards and use control wards"
            )

        # ── Kill participation ────────────────────────────────────────
        if avg_kp >= bench['kill_part'] * 100 * 1.1:
            strengths.append(
                f"High kill participation ({avg_kp}%) - you're involved in team fights"
            )
        elif avg_kp < bench['kill_part'] * 100 * 0.8:
            weaknesses.append(
                f"Low kill participation ({avg_kp}%) - "
                "try to group with your team more and look for plays"
            )

        # ── Role diversity / one-tricking ─────────────────────────────
        if role_summary and primary_role:
            role_name = primary_role
            role_data = role_summary[role_name]
            role_pct = role_data['games'] / games_parsed * 100 if games_parsed else 0
            if role_pct >= 70:
                if role_data['win_rate'] >= 55:
                    strengths.append(
                        f"Consistent {role_name} player ({role_data['games']} games, "
                        f"{role_data['win_rate']}% WR) - role focus is paying off"
                    )
                elif role_data['win_rate'] < 48:
                    weaknesses.append(
                        f"Primary role {role_name} has only {role_data['win_rate']}% WR "
                        f"over {role_data['games']} games - consider reviewing your "
                        "role-specific fundamentals"
                    )

        # ── Champion pool insights ────────────────────────────────────
        if champion_summary:
            # Best / worst champions (min 2 games)
            qualified = {c: s for c, s in champion_summary.items() if s['games'] >= 2}
            if qualified:
                best = max(qualified.items(), key=lambda x: x[1]['win_rate'])
                worst = min(qualified.items(), key=lambda x: x[1]['win_rate'])
                if best[1]['win_rate'] >= 60:
                    strengths.append(
                        f"Strong on {best[0]} ({best[1]['win_rate']}% WR "
                        f"over {best[1]['games']} games)"
                    )
                if worst[1]['win_rate'] <= 40 and worst[1]['games'] >= 3:
                    weaknesses.append(
                        f"Struggling on {worst[0]} ({worst[1]['win_rate']}% WR "
                        f"over {worst[1]['games']} games) - consider dropping this pick"
                    )

            # Too many champions?
            unique_champs = len(champion_summary)
            if games_parsed >= 10 and unique_champs >= games_parsed * 0.7:
                weaknesses.append(
                    f"Playing {unique_champs} different champions in {games_parsed} "
                    "games - narrowing your pool will help you improve faster"
                )

        return strengths, weaknesses

    # ── ARAM Analysis ─────────────────────────────────────────────────

    # ARAM benchmarks (not rank-dependent since ARAM has no visible rank)
    # These are approximate averages for an "average" ARAM player.
    ARAM_BENCHMARKS = {
        'kda_ratio': 2.5,
        'kill_part': 65,       # % - ARAM has much higher KP than SR
        'dmg_per_min': 900,
        'deaths_per_game': 7,  # ARAM has more deaths than SR
        'gold_per_min': 400,
    }

    def analyze_aram(
        self,
        puuid: str,
        match_count: int = 30,
        display_name: Optional[str] = None,
        mayhem_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run analysis for ARAM games.

        mayhem_filter: None = all ARAM, 'mayhem' = only Mayhem, 'classic' = only classic ARAM
        """

        matches = self.api_client.get_recent_matches(puuid, match_count, queue=450)

        # Filter by Mayhem vs classic ARAM
        if mayhem_filter == 'mayhem':
            matches = [m for m in matches if m['info'].get('gameModeMutators')]
        elif mayhem_filter == 'classic':
            matches = [m for m in matches if not m['info'].get('gameModeMutators')]

        games_parsed = 0
        wins = 0
        all_kills, all_deaths, all_assists = [], [], []
        all_damage, all_damage_per_min = [], []
        all_gold_per_min = []
        all_kill_participation = []
        all_damage_share = []
        all_damage_taken, all_healing = [], []
        all_multikills = []  # pentakills, quadras, triples
        champion_stats: Dict[str, Dict] = defaultdict(lambda: {
            'games': 0, 'wins': 0,
            'kills': [], 'deaths': [], 'assists': [],
            'damage': [], 'damage_per_min': [],
        })
        recent_performance = []
        pentakills_total = 0
        quadrakills_total = 0
        games_with_high_deaths = 0

        for match in matches:
            player = self._find_player(match, puuid)
            if not player:
                continue

            info = match['info']
            duration_min = info['gameDuration'] / 60
            if duration_min < 3:
                continue

            games_parsed += 1
            won = player['win']
            if won:
                wins += 1

            kills = player['kills']
            deaths = player['deaths']
            assists = player['assists']
            damage = player['totalDamageDealtToChampions']
            damage_per_min = damage / duration_min
            gold = player['goldEarned']
            gold_per_min = gold / duration_min
            champion = player['championName']
            damage_taken = player.get('totalDamageTaken', 0)
            healing = player.get('totalHeal', 0) + player.get('totalHealsOnTeammates', 0)

            # Kill participation
            team_id = player['teamId']
            team_kills = sum(
                p['kills'] for p in info['participants'] if p['teamId'] == team_id
            )
            kp = (kills + assists) / max(team_kills, 1)

            # Damage share
            team_damage = sum(
                p['totalDamageDealtToChampions']
                for p in info['participants']
                if p['teamId'] == team_id
            )
            dmg_share = damage / max(team_damage, 1)

            # Multikills
            pentakills_total += player.get('pentaKills', 0)
            quadrakills_total += player.get('quadraKills', 0)

            if deaths >= 10:
                games_with_high_deaths += 1

            # Accumulate
            all_kills.append(kills)
            all_deaths.append(deaths)
            all_assists.append(assists)
            all_damage.append(damage)
            all_damage_per_min.append(damage_per_min)
            all_gold_per_min.append(gold_per_min)
            all_kill_participation.append(kp)
            all_damage_share.append(dmg_share)
            all_damage_taken.append(damage_taken)
            all_healing.append(healing)

            # Champion stats
            cs_entry = champion_stats[champion]
            cs_entry['games'] += 1
            if won:
                cs_entry['wins'] += 1
            cs_entry['kills'].append(kills)
            cs_entry['deaths'].append(deaths)
            cs_entry['assists'].append(assists)
            cs_entry['damage'].append(damage)
            cs_entry['damage_per_min'].append(damage_per_min)

            recent_performance.append({
                'champion': champion,
                'win': won,
                'kda': f"{kills}/{deaths}/{assists}",
                'damage': damage,
                'damage_per_min': round(damage_per_min),
                'kill_participation': round(kp * 100, 1),
                'damage_share': round(dmg_share * 100, 1),
                'duration_minutes': round(duration_min, 1),
            })

        # ── Aggregates ────────────────────────────────────────────────
        def avg(lst):
            return round(statistics.mean(lst), 1) if lst else 0

        losses = games_parsed - wins
        win_rate = round((wins / games_parsed) * 100, 1) if games_parsed else 0
        avg_kills = avg(all_kills)
        avg_deaths = avg(all_deaths)
        avg_assists = avg(all_assists)
        kda_ratio = round((avg_kills + avg_assists) / max(avg_deaths, 0.1), 2)
        avg_damage = round(statistics.mean(all_damage)) if all_damage else 0
        avg_dmg_per_min = avg(all_damage_per_min)
        avg_gold_per_min = avg(all_gold_per_min)
        avg_kp = avg([x * 100 for x in all_kill_participation])
        avg_dmg_share = avg([x * 100 for x in all_damage_share])
        avg_damage_taken_val = round(statistics.mean(all_damage_taken)) if all_damage_taken else 0
        avg_healing_val = round(statistics.mean(all_healing)) if all_healing else 0

        # Finalize champion stats
        champion_summary = {}
        for champ, st in champion_stats.items():
            g = st['games']
            champion_summary[champ] = {
                'games': g,
                'wins': st['wins'],
                'win_rate': round((st['wins'] / g) * 100, 1) if g else 0,
                'avg_kills': avg(st['kills']),
                'avg_deaths': avg(st['deaths']),
                'avg_assists': avg(st['assists']),
                'avg_damage': round(statistics.mean(st['damage'])) if st['damage'] else 0,
                'avg_damage_per_min': avg(st['damage_per_min']),
            }

        # ── ARAM Strengths & Weaknesses ───────────────────────────────
        strengths, weaknesses = self._evaluate_aram(
            win_rate=win_rate,
            kda_ratio=kda_ratio,
            avg_kills=avg_kills,
            avg_deaths=avg_deaths,
            avg_assists=avg_assists,
            avg_dmg_per_min=avg_dmg_per_min,
            avg_kp=avg_kp,
            avg_dmg_share=avg_dmg_share,
            games_with_high_deaths=games_with_high_deaths,
            games_parsed=games_parsed,
            pentakills=pentakills_total,
            quadrakills=quadrakills_total,
            champion_summary=champion_summary,
        )

        return {
            'mode': 'ARAM: Mayhem' if mayhem_filter == 'mayhem' else 'ARAM',
            'display_name': display_name or 'Unknown',
            'total_matches': games_parsed,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'average_kda': {
                'kills': avg_kills,
                'deaths': avg_deaths,
                'assists': avg_assists,
                'ratio': kda_ratio,
            },
            'avg_damage': avg_damage,
            'avg_damage_per_min': avg_dmg_per_min,
            'avg_gold_per_min': avg_gold_per_min,
            'avg_kill_participation': avg_kp,
            'avg_damage_share': avg_dmg_share,
            'avg_damage_taken': avg_damage_taken_val,
            'avg_healing': avg_healing_val,
            'pentakills': pentakills_total,
            'quadrakills': quadrakills_total,
            'champion_stats': champion_summary,
            'recent_performance': recent_performance[:15],
            'strengths': strengths,
            'weaknesses': weaknesses,
        }

    def _evaluate_aram(
        self, *, win_rate, kda_ratio, avg_kills, avg_deaths, avg_assists,
        avg_dmg_per_min, avg_kp, avg_dmg_share, games_with_high_deaths,
        games_parsed, pentakills, quadrakills, champion_summary,
    ):
        strengths: List[str] = []
        weaknesses: List[str] = []
        bench = self.ARAM_BENCHMARKS

        # ── Win rate ──────────────────────────────────────────────────
        if win_rate >= 55:
            strengths.append(f"Strong ARAM win rate ({win_rate}%) - you're an ARAM beast")
        elif win_rate < 45 and games_parsed >= 10:
            weaknesses.append(
                f"ARAM win rate is {win_rate}% over {games_parsed} games"
            )

        # ── KDA ───────────────────────────────────────────────────────
        if kda_ratio >= bench['kda_ratio'] * 1.3:
            strengths.append(
                f"Excellent ARAM KDA ({kda_ratio}) - well above average ({bench['kda_ratio']})"
            )
        elif kda_ratio < bench['kda_ratio'] * 0.7:
            weaknesses.append(
                f"KDA ratio ({kda_ratio}) is below ARAM average ({bench['kda_ratio']}) - "
                "try to avoid getting caught out and play around your team"
            )

        # ── Deaths ────────────────────────────────────────────────────
        if avg_deaths >= 9:
            weaknesses.append(
                f"Averaging {avg_deaths} deaths/game in ARAM - dying too often even "
                "for ARAM. Position more carefully in teamfights"
            )
        elif avg_deaths <= 5:
            strengths.append(
                f"Low death average for ARAM ({avg_deaths}) - great positioning"
            )

        if games_parsed >= 5:
            death_pct = games_with_high_deaths / games_parsed
            if death_pct >= 0.5:
                weaknesses.append(
                    f"10+ deaths in {games_with_high_deaths}/{games_parsed} games - "
                    "consider playing safer in extended fights"
                )

        # ── Damage ────────────────────────────────────────────────────
        if avg_dmg_per_min >= bench['dmg_per_min'] * 1.2:
            strengths.append(
                f"High damage output ({round(avg_dmg_per_min)}/min) - "
                f"above average ({bench['dmg_per_min']}/min)"
            )
        elif avg_dmg_per_min < bench['dmg_per_min'] * 0.7:
            weaknesses.append(
                f"Low damage output ({round(avg_dmg_per_min)}/min) - "
                f"below average ({bench['dmg_per_min']}/min). "
                "Look for more opportunities to poke and fight"
            )

        # ── Kill participation ────────────────────────────────────────
        if avg_kp >= bench['kill_part'] * 1.1:
            strengths.append(
                f"High kill participation ({avg_kp}%) - always in the action"
            )
        elif avg_kp < bench['kill_part'] * 0.8:
            weaknesses.append(
                f"Low kill participation ({avg_kp}%) for ARAM - "
                "you should be involved in nearly every fight"
            )

        # ── Multikills ────────────────────────────────────────────────
        if pentakills >= 1:
            strengths.append(
                f"{pentakills} pentakill{'s' if pentakills > 1 else ''} - clutch performer"
            )
        if quadrakills >= 2:
            strengths.append(
                f"{quadrakills} quadrakills - strong teamfight cleanup"
            )

        # ── Champion insights ─────────────────────────────────────────
        if champion_summary:
            qualified = {c: s for c, s in champion_summary.items() if s['games'] >= 2}
            if qualified:
                best = max(qualified.items(), key=lambda x: x[1]['win_rate'])
                worst = min(qualified.items(), key=lambda x: x[1]['win_rate'])
                if best[1]['win_rate'] >= 65:
                    strengths.append(
                        f"Dominant on {best[0]} in ARAM ({best[1]['win_rate']}% WR, "
                        f"{best[1]['games']} games)"
                    )
                if worst[1]['win_rate'] <= 35 and worst[1]['games'] >= 3:
                    weaknesses.append(
                        f"Struggling on {worst[0]} in ARAM ({worst[1]['win_rate']}% WR, "
                        f"{worst[1]['games']} games)"
                    )

        return strengths, weaknesses

    # ── Arena Analysis ─────────────────────────────────────────────────

    def analyze_arena(
        self,
        puuid: str,
        match_count: int = 30,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run analysis for Arena (2v2v2v2) games."""
        matches = self.api_client.get_recent_matches(puuid, match_count, queue=1700)

        games_parsed = 0
        placements = []
        all_kills, all_deaths, all_assists = [], [], []
        all_damage = []
        champion_stats: Dict[str, Dict] = defaultdict(lambda: {
            'games': 0, 'placements': [],
            'kills': [], 'deaths': [], 'assists': [],
            'damage': [],
        })
        recent_performance = []

        for match in matches:
            player = self._find_player(match, puuid)
            if not player:
                continue

            info = match['info']
            duration_min = info['gameDuration'] / 60
            if duration_min < 2:
                continue

            games_parsed += 1
            placement = player.get('placement', player.get('subteamPlacement', 8))
            kills = player['kills']
            deaths = player['deaths']
            assists = player['assists']
            damage = player['totalDamageDealtToChampions']
            champion = player['championName']

            placements.append(placement)
            all_kills.append(kills)
            all_deaths.append(deaths)
            all_assists.append(assists)
            all_damage.append(damage)

            cs_entry = champion_stats[champion]
            cs_entry['games'] += 1
            cs_entry['placements'].append(placement)
            cs_entry['kills'].append(kills)
            cs_entry['deaths'].append(deaths)
            cs_entry['assists'].append(assists)
            cs_entry['damage'].append(damage)

            recent_performance.append({
                'champion': champion,
                'placement': placement,
                'kda': f"{kills}/{deaths}/{assists}",
                'damage': damage,
                'duration_minutes': round(duration_min, 1),
            })

        def avg(lst):
            return round(statistics.mean(lst), 1) if lst else 0

        avg_placement = avg(placements)
        top4_count = sum(1 for p in placements if p <= 4)
        top4_rate = round((top4_count / games_parsed) * 100, 1) if games_parsed else 0
        first_count = sum(1 for p in placements if p == 1)
        first_rate = round((first_count / games_parsed) * 100, 1) if games_parsed else 0

        champion_summary = {}
        for champ, st in champion_stats.items():
            g = st['games']
            champion_summary[champ] = {
                'games': g,
                'avg_placement': avg(st['placements']),
                'top4_rate': round(sum(1 for p in st['placements'] if p <= 4) / g * 100, 1) if g else 0,
                'avg_kills': avg(st['kills']),
                'avg_deaths': avg(st['deaths']),
                'avg_assists': avg(st['assists']),
                'avg_damage': round(statistics.mean(st['damage'])) if st['damage'] else 0,
            }

        # Strengths/weaknesses
        strengths, weaknesses = [], []
        if avg_placement <= 3.5 and games_parsed >= 5:
            strengths.append(f"Strong avg placement ({avg_placement}) - consistently finishing high")
        elif avg_placement >= 5.5 and games_parsed >= 5:
            weaknesses.append(f"Avg placement is {avg_placement} - finishing in bottom half too often")

        if top4_rate >= 60:
            strengths.append(f"Top 4 in {top4_rate}% of games - solid consistency")
        elif top4_rate < 40 and games_parsed >= 5:
            weaknesses.append(f"Only top 4 in {top4_rate}% of games")

        if first_count >= 2:
            strengths.append(f"{first_count} first-place finishes")

        if champion_summary:
            qualified = {c: s for c, s in champion_summary.items() if s['games'] >= 2}
            if qualified:
                best = min(qualified.items(), key=lambda x: x[1]['avg_placement'])
                if best[1]['avg_placement'] <= 3.0:
                    strengths.append(f"Strong on {best[0]} (avg {best[1]['avg_placement']} placement, {best[1]['games']} games)")

        avg_deaths_val = avg(all_deaths)
        if avg_deaths_val >= 8:
            weaknesses.append(f"Averaging {avg_deaths_val} deaths/game - dying too much in rounds")
        elif avg_deaths_val <= 3:
            strengths.append(f"Low deaths ({avg_deaths_val}/game) - great round survival")

        return {
            'mode': 'Arena',
            'display_name': display_name or 'Unknown',
            'total_matches': games_parsed,
            'avg_placement': avg_placement,
            'top4_rate': top4_rate,
            'top4_count': top4_count,
            'first_count': first_count,
            'first_rate': first_rate,
            'average_kda': {
                'kills': avg(all_kills),
                'deaths': avg_deaths_val,
                'assists': avg(all_assists),
                'ratio': round((avg(all_kills) + avg(all_assists)) / max(avg_deaths_val, 0.1), 2),
            },
            'avg_damage': round(statistics.mean(all_damage)) if all_damage else 0,
            'champion_stats': champion_summary,
            'recent_performance': recent_performance[:15],
            'strengths': strengths,
            'weaknesses': weaknesses,
        }

    # ── Champion recommendations ──────────────────────────────────────

    def get_champion_recommendations(
        self, analysis: Dict[str, Any], min_games: int = 2
    ) -> List[Dict[str, Any]]:
        """Return top champions sorted by win rate (min games threshold)."""
        recs = []
        for champ, stats in analysis['champion_stats'].items():
            if stats['games'] >= min_games:
                recs.append({
                    'champion': champ,
                    'games': stats['games'],
                    'win_rate': stats['win_rate'],
                    'avg_kda': f"{stats['avg_kills']}/{stats['avg_deaths']}/{stats['avg_assists']}",
                    'avg_cs_per_min': stats['avg_cs_per_min'],
                })
        recs.sort(key=lambda x: (x['win_rate'], x['games']), reverse=True)
        return recs[:5]

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _find_player(match: Dict, puuid: str) -> Optional[Dict]:
        for p in match['info']['participants']:
            if p['puuid'] == puuid:
                return p
        return None
