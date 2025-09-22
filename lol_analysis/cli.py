#!/usr/bin/env python3
"""
League of Legends Ranked Analysis CLI
"""
import click
from typing import Optional
from tabulate import tabulate
import sys

from .config import Config
from .riot_api import RiotAPIClient, RiotAPIError
from .analyzer import MatchAnalyzer


def print_error(message: str):
    """Print error message in red"""
    click.echo(click.style(f"Error: {message}", fg='red'), err=True)


def print_success(message: str):
    """Print success message in green"""
    click.echo(click.style(message, fg='green'))


def print_info(message: str):
    """Print info message in blue"""
    click.echo(click.style(message, fg='blue'))


def format_rank_info(rank_info: dict) -> str:
    """Format rank information for display"""
    if not rank_info:
        return "Unranked"
    return f"{rank_info['tier']} {rank_info['rank']} ({rank_info['lp']} LP) - {rank_info['win_rate']}% WR"


def display_analysis(analysis: dict):
    """Display the complete analysis results"""
    print("\n" + "="*60)
    print_info(f"ANALYSIS FOR {analysis['summoner_info']['name'].upper()}")
    print("="*60)
    
    # Summoner info
    print(f"Level: {analysis['summoner_info']['level']}")
    print(f"Rank: {format_rank_info(analysis.get('rank_info', {}))}")
    print(f"Recent Matches Analyzed: {analysis['total_matches']}")
    print()
    
    # Overall stats
    print_info("OVERALL PERFORMANCE:")
    print(f"Win Rate: {analysis['win_rate']}% ({analysis['wins']}W / {analysis['losses']}L)")
    kda = analysis['average_kda']
    kda_ratio = round((kda['kills'] + kda['assists']) / max(kda['deaths'], 1), 2)
    print(f"Average KDA: {kda['kills']}/{kda['deaths']}/{kda['assists']} ({kda_ratio})")
    print(f"Average Damage: {analysis['total_damage_avg']:,}")
    print(f"CS per Minute: {analysis['cs_per_minute_avg']}")
    print(f"Average Vision Score: {analysis['vision_score_avg']}")
    print()
    
    # Champion stats
    if analysis['champion_stats']:
        print_info("CHAMPION PERFORMANCE:")
        champion_data = []
        for champion, stats in sorted(analysis['champion_stats'].items(), 
                                    key=lambda x: x[1]['games'], reverse=True):
            champion_data.append([
                champion,
                stats['games'],
                f"{stats['win_rate']}%",
                f"{stats['avg_kills']}/{stats['avg_deaths']}/{stats['avg_assists']}"
            ])
        
        headers = ['Champion', 'Games', 'Win Rate', 'Avg KDA']
        print(tabulate(champion_data, headers=headers, tablefmt='grid'))
        print()
    
    # Recent performance
    if analysis['recent_performance']:
        print_info("RECENT MATCHES:")
        recent_data = []
        for i, match in enumerate(analysis['recent_performance'], 1):
            result = "✓ Win" if match['win'] else "✗ Loss"
            recent_data.append([
                i,
                match['champion'],
                result,
                match['kda'],
                f"{match['damage']:,}",
                f"{match['cs']} ({match['duration_minutes']}min)"
            ])
        
        headers = ['#', 'Champion', 'Result', 'KDA', 'Damage', 'CS (Duration)']
        print(tabulate(recent_data, headers=headers, tablefmt='grid'))


@click.group()
def cli():
    """League of Legends Ranked Analysis Tool"""
    pass


@cli.command()
@click.option('--summoner', '-s', help='Summoner name to analyze')
@click.option('--region', '-r', default='na1', help='Region (default: na1)')
@click.option('--matches', '-m', default=20, help='Number of recent matches to analyze (default: 20)')
def analyze(summoner: Optional[str], region: str, matches: int):
    """Analyze match history for a summoner"""
    try:
        config = Config()
        
        if not config.is_configured():
            print_error("API key not configured. Please set RIOT_API_KEY in your .env file")
            print_info("Copy .env.example to .env and fill in your API key")
            sys.exit(1)
        
        # Use provided summoner or default from config
        summoner_name = summoner or config.default_summoner_name
        if not summoner_name:
            print_error("No summoner name provided. Use --summoner option or set SUMMONER_NAME in .env")
            sys.exit(1)
        
        print_info(f"Analyzing {summoner_name} on {region.upper()}...")
        
        # Initialize API client and analyzer
        api_client = RiotAPIClient(config.riot_api_key, region)
        analyzer = MatchAnalyzer(api_client)
        
        # Perform analysis
        analysis = analyzer.analyze_matches(summoner_name, matches)
        
        # Display results
        display_analysis(analysis)
        
        # Show recommendations
        recommendations = analyzer.get_champion_recommendations(analysis)
        if recommendations:
            print()
            print_info("TOP CHAMPION RECOMMENDATIONS:")
            rec_data = []
            for rec in recommendations:
                rec_data.append([
                    rec['champion'],
                    rec['games'],
                    f"{rec['win_rate']}%",
                    rec['avg_kda']
                ])
            
            headers = ['Champion', 'Games', 'Win Rate', 'Avg KDA']
            print(tabulate(rec_data, headers=headers, tablefmt='grid'))
        
        print_success(f"\nAnalysis complete for {analysis['total_matches']} matches!")
        
    except RiotAPIError as e:
        print_error(f"API Error: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)


@cli.command()
def setup():
    """Show setup instructions"""
    print_info("LoL Ranked Analysis Setup Instructions:")
    print("\n1. Get a Riot API key:")
    print("   - Go to https://developer.riotgames.com/")
    print("   - Sign in with your Riot account")
    print("   - Generate a personal API key")
    print()
    print("2. Configure the application:")
    print("   - Copy .env.example to .env")
    print("   - Add your API key to the .env file")
    print("   - Optionally set your default summoner name and region")
    print()
    print("3. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("4. Run analysis:")
    print("   python -m lol_analysis.cli analyze --summoner YourSummonerName")


if __name__ == '__main__':
    cli()