#!/usr/bin/env python3
"""
League of Legends Ranked Analysis CLI
"""
import click
import sys
from typing import Optional
from tabulate import tabulate

from .config import Config
from .riot_api import RiotAPIClient, RiotAPIError
from .analyzer import MatchAnalyzer


# ── Helpers ───────────────────────────────────────────────────────────

ROLE_DISPLAY = {
    'TOP': 'Top',
    'JUNGLE': 'Jungle',
    'MIDDLE': 'Mid',
    'BOTTOM': 'Bot/ADC',
    'UTILITY': 'Support',
}


def print_error(msg: str):
    click.echo(click.style(f"Error: {msg}", fg='red'), err=True)


def print_success(msg: str):
    click.echo(click.style(msg, fg='green'))


def print_info(msg: str):
    click.echo(click.style(msg, fg='blue'))


def print_warn(msg: str):
    click.echo(click.style(msg, fg='yellow'))


def format_rank(rank_info: dict) -> str:
    if not rank_info:
        return "Unranked"
    streak = " (on a hot streak!)" if rank_info.get('hot_streak') else ""
    return (
        f"{rank_info['tier']} {rank_info['rank']} "
        f"({rank_info['lp']} LP) - "
        f"{rank_info['win_rate']}% WR "
        f"({rank_info['wins']}W/{rank_info['losses']}L){streak}"
    )


def parse_riot_id(riot_id: str):
    """Parse 'GameName#TAG' into (game_name, tag_line).

    If no # is present, returns (riot_id, None) so the caller can
    fall back to a default tag.
    """
    if '#' in riot_id:
        parts = riot_id.rsplit('#', 1)
        return parts[0].strip(), parts[1].strip()
    return riot_id.strip(), None


# ── Display ───────────────────────────────────────────────────────────

def display_analysis(analysis: dict):
    """Display the complete analysis results."""
    name = analysis['display_name']
    print("\n" + "=" * 64)
    print_info(f"  RANKED ANALYSIS FOR {name.upper()}")
    print("=" * 64)

    # Rank
    print(f"  Rank: {format_rank(analysis.get('rank_info', {}))}")
    print(f"  Games Analyzed: {analysis['total_matches']}")
    print()

    # ── Overall stats ─────────────────────────────────────────────
    print_info("OVERALL PERFORMANCE")
    print("-" * 40)
    wr = analysis['win_rate']
    w, l = analysis['wins'], analysis['losses']
    kda = analysis['average_kda']
    print(f"  Win Rate:             {wr}% ({w}W / {l}L)")
    print(f"  KDA:                  {kda['kills']}/{kda['deaths']}/{kda['assists']}  ({kda['ratio']} ratio)")
    print(f"  Avg Damage:           {analysis['avg_damage']:,}")
    print(f"  Avg Gold:             {analysis['avg_gold']:,}")
    print(f"  CS/min:               {analysis['avg_cs_per_min']}")
    print(f"  Vision Score/min:     {analysis['avg_vision_per_min']}")
    print(f"  Kill Participation:   {analysis['avg_kill_participation']}%")
    print(f"  Damage Share:         {analysis['avg_damage_share']}%")
    print()

    # ── Champion stats ────────────────────────────────────────────
    if analysis['champion_stats']:
        print_info("CHAMPION PERFORMANCE")
        print("-" * 40)
        rows = []
        for champ, s in sorted(
            analysis['champion_stats'].items(),
            key=lambda x: x[1]['games'],
            reverse=True,
        ):
            rows.append([
                champ,
                s['games'],
                f"{s['win_rate']}%",
                f"{s['avg_kills']}/{s['avg_deaths']}/{s['avg_assists']}",
                s['avg_cs_per_min'],
                f"{s['avg_damage']:,}",
            ])
        print(tabulate(
            rows,
            headers=['Champion', 'Games', 'WR', 'Avg KDA', 'CS/m', 'Avg Dmg'],
            tablefmt='grid',
        ))
        print()

    # ── Role stats ────────────────────────────────────────────────
    if analysis['role_stats']:
        print_info("ROLE PERFORMANCE")
        print("-" * 40)
        rows = []
        for role, s in sorted(
            analysis['role_stats'].items(),
            key=lambda x: x[1]['games'],
            reverse=True,
        ):
            rows.append([
                ROLE_DISPLAY.get(role, role),
                s['games'],
                f"{s['win_rate']}%",
                f"{s['avg_kills']}/{s['avg_deaths']}/{s['avg_assists']}",
                s['avg_cs_per_min'],
                s['avg_vision_per_min'],
            ])
        print(tabulate(
            rows,
            headers=['Role', 'Games', 'WR', 'Avg KDA', 'CS/m', 'Vis/m'],
            tablefmt='grid',
        ))
        print()

    # ── Recent matches ────────────────────────────────────────────
    if analysis['recent_performance']:
        print_info("RECENT MATCHES")
        print("-" * 40)
        rows = []
        for i, m in enumerate(analysis['recent_performance'][:15], 1):
            result = "Win" if m['win'] else "Loss"
            rows.append([
                i,
                m['champion'],
                ROLE_DISPLAY.get(m['role'], m['role']),
                result,
                m['kda'],
                f"{m['damage']:,}",
                f"{m['cs']} ({m['cs_per_min']}/m)",
                f"{m['kill_participation']}%",
            ])
        print(tabulate(
            rows,
            headers=['#', 'Champ', 'Role', 'Result', 'KDA', 'Damage', 'CS', 'KP%'],
            tablefmt='grid',
        ))
        print()

    # ── Strengths & Weaknesses ────────────────────────────────────
    if analysis['strengths']:
        print_success("STRENGTHS")
        print("-" * 40)
        for s in analysis['strengths']:
            print(f"  + {s}")
        print()

    if analysis['weaknesses']:
        print_warn("WEAKNESSES")
        print("-" * 40)
        for w in analysis['weaknesses']:
            print(f"  - {w}")
        print()


def display_aram_analysis(analysis: dict):
    """Display ARAM analysis results."""
    name = analysis['display_name']
    mode = analysis.get('mode', 'ARAM')
    print("\n" + "=" * 64)
    print_info(f"  {mode.upper()} ANALYSIS FOR {name.upper()}")
    print("=" * 64)
    print(f"  Games Analyzed: {analysis['total_matches']}")
    print()

    # ── Overall stats ─────────────────────────────────────────────
    print_info("OVERALL PERFORMANCE")
    print("-" * 40)
    wr = analysis['win_rate']
    w, l = analysis['wins'], analysis['losses']
    kda = analysis['average_kda']
    print(f"  Win Rate:             {wr}% ({w}W / {l}L)")
    print(f"  KDA:                  {kda['kills']}/{kda['deaths']}/{kda['assists']}  ({kda['ratio']} ratio)")
    print(f"  Avg Damage:           {analysis['avg_damage']:,}")
    print(f"  Damage/min:           {analysis['avg_damage_per_min']}")
    print(f"  Gold/min:             {analysis['avg_gold_per_min']}")
    print(f"  Kill Participation:   {analysis['avg_kill_participation']}%")
    print(f"  Damage Share:         {analysis['avg_damage_share']}%")
    print(f"  Avg Damage Taken:     {analysis['avg_damage_taken']:,}")
    print(f"  Avg Healing Done:     {analysis['avg_healing']:,}")
    if analysis['pentakills']:
        print(f"  Pentakills:           {analysis['pentakills']}")
    if analysis['quadrakills']:
        print(f"  Quadrakills:          {analysis['quadrakills']}")
    print()

    # ── Champion stats ────────────────────────────────────────────
    if analysis['champion_stats']:
        print_info("CHAMPION PERFORMANCE")
        print("-" * 40)
        rows = []
        for champ, s in sorted(
            analysis['champion_stats'].items(),
            key=lambda x: x[1]['games'],
            reverse=True,
        ):
            rows.append([
                champ,
                s['games'],
                f"{s['win_rate']}%",
                f"{s['avg_kills']}/{s['avg_deaths']}/{s['avg_assists']}",
                f"{s['avg_damage']:,}",
                round(s['avg_damage_per_min']),
            ])
        print(tabulate(
            rows,
            headers=['Champion', 'Games', 'WR', 'Avg KDA', 'Avg Dmg', 'Dmg/m'],
            tablefmt='grid',
        ))
        print()

    # ── Recent matches ────────────────────────────────────────────
    if analysis['recent_performance']:
        print_info("RECENT MATCHES")
        print("-" * 40)
        rows = []
        for i, m in enumerate(analysis['recent_performance'][:15], 1):
            result = "Win" if m['win'] else "Loss"
            rows.append([
                i,
                m['champion'],
                result,
                m['kda'],
                f"{m['damage']:,}",
                m['damage_per_min'],
                f"{m['kill_participation']}%",
                f"{m['damage_share']}%",
            ])
        print(tabulate(
            rows,
            headers=['#', 'Champ', 'Result', 'KDA', 'Damage', 'Dmg/m', 'KP%', 'Dmg%'],
            tablefmt='grid',
        ))
        print()

    # ── Strengths & Weaknesses ────────────────────────────────────
    if analysis['strengths']:
        print_success("STRENGTHS")
        print("-" * 40)
        for s in analysis['strengths']:
            print(f"  + {s}")
        print()

    if analysis['weaknesses']:
        print_warn("WEAKNESSES")
        print("-" * 40)
        for w in analysis['weaknesses']:
            print(f"  - {w}")
        print()


# ── CLI Commands ──────────────────────────────────────────────────────

@click.group()
def cli():
    """League of Legends Ranked Analysis Tool

    Analyzes your ranked match history and identifies strengths and weaknesses.

    Usage:  python main.py analyze --name "GameName#TAG"
    """
    pass


@cli.command()
@click.option('--name', '-n', help='Riot ID in "GameName#TAG" format (e.g. "Doublelift#NA1")')
@click.option('--region', '-r', default=None, help='Platform region (default: from .env or na1)')
@click.option('--matches', '-m', default=20, help='Number of recent matches (default: 20, max 100)')
@click.option('--mode', type=click.Choice(['ranked', 'aram', 'mayhem'], case_sensitive=False),
              default='ranked', help='Game mode: ranked, aram, or mayhem (default: ranked)')
def analyze(name: Optional[str], region: Optional[str], matches: int, mode: str):
    """Analyze match history and show strengths/weaknesses."""
    try:
        config = Config()

        if not config.is_configured():
            print_error("API key not configured. Set RIOT_API_KEY in your .env file.")
            print_info("  cp .env.example .env   # then add your key")
            sys.exit(1)

        region = region or config.default_region or 'na1'

        # Resolve Riot ID
        riot_id = name or config.default_summoner_name
        if not riot_id:
            print_error(
                'No Riot ID provided. Use --name "GameName#TAG" '
                'or set SUMMONER_NAME in .env'
            )
            sys.exit(1)

        game_name, tag_line = parse_riot_id(riot_id)
        tag_line = tag_line or config.default_tag_line or region.upper()

        display_name = f"{game_name}#{tag_line}"
        mode_labels = {'ranked': 'Ranked', 'aram': 'ARAM', 'mayhem': 'ARAM: Mayhem'}
        mode_label = mode_labels[mode]
        print_info(f"Analyzing {display_name} on {region.upper()} ({mode_label})...")
        print()

        # Initialize
        api_client = RiotAPIClient(config.riot_api_key, region)
        analyzer = MatchAnalyzer(api_client)

        # Look up account by Riot ID
        account = api_client.get_account_by_riot_id(game_name, tag_line)

        if mode in ('aram', 'mayhem'):
            # ARAM / Mayhem analysis
            mayhem_filter = 'mayhem' if mode == 'mayhem' else None
            analysis = analyzer.analyze_aram(
                puuid=account.puuid,
                match_count=min(matches, 100),
                display_name=display_name,
                mayhem_filter=mayhem_filter,
            )
            display_aram_analysis(analysis)
        else:
            # Ranked analysis
            analysis = analyzer.analyze_matches(
                puuid=account.puuid,
                match_count=min(matches, 100),
                display_name=display_name,
            )
            display_analysis(analysis)

            # Champion recommendations (ranked only)
            recs = analyzer.get_champion_recommendations(analysis)
            if recs:
                print_info("RECOMMENDED CHAMPIONS (best win rate, 2+ games)")
                print("-" * 40)
                rows = [[r['champion'], r['games'], f"{r['win_rate']}%", r['avg_kda'], r['avg_cs_per_min']]
                        for r in recs]
                print(tabulate(
                    rows,
                    headers=['Champion', 'Games', 'WR', 'Avg KDA', 'CS/m'],
                    tablefmt='grid',
                ))
                print()

        print_success(f"Analysis complete - {analysis['total_matches']} {mode_label} games analyzed.")

    except RiotAPIError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise


@cli.command()
def setup():
    """Show setup instructions."""
    print_info("LoL Ranked Analysis - Setup")
    print()
    print("1. Get a Riot API key:")
    print("   https://developer.riotgames.com/")
    print("   Sign in -> generate a Development API key (valid 24 hours)")
    print()
    print("2. Configure:")
    print("   cp .env.example .env")
    print("   Then edit .env:")
    print('     RIOT_API_KEY=RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
    print('     SUMMONER_NAME=YourName')
    print('     TAG_LINE=NA1')
    print('     REGION=na1')
    print()
    print("3. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("4. Run:")
    print('   python main.py analyze --name "YourName#NA1"')
    print('   python main.py analyze --name "YourName#NA1" --matches 50')
    print('   python main.py analyze --name "YourName#NA1" --mode aram')
    print()


if __name__ == '__main__':
    cli()
