#!/usr/bin/env python3
"""
Example script demonstrating programmatic use of the LoL Analysis library
"""
import os
from dotenv import load_dotenv
from lol_analysis.riot_api import RiotAPIClient, RiotAPIError
from lol_analysis.analyzer import MatchAnalyzer


def main():
    """Example of using the library programmatically"""
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv('RIOT_API_KEY')
    if not api_key:
        print("Please set RIOT_API_KEY in your .env file")
        return
    
    summoner_name = "YourSummonerName"  # Replace with actual summoner name
    region = "na1"  # Replace with your region
    
    try:
        # Initialize API client and analyzer
        api_client = RiotAPIClient(api_key, region)
        analyzer = MatchAnalyzer(api_client)
        
        # Get basic summoner info
        summoner = api_client.get_summoner_by_name(summoner_name)
        print(f"Summoner: {summoner.name} (Level {summoner.summonerLevel})")
        
        # Get rank information
        rank_entries = api_client.get_rank_entries(summoner.id)
        for entry in rank_entries:
            if entry.queueType == 'RANKED_SOLO_5x5':
                print(f"Rank: {entry.tier} {entry.rank} ({entry.leaguePoints} LP)")
                break
        
        # Analyze recent matches
        print("\nAnalyzing recent matches...")
        analysis = analyzer.analyze_matches(summoner_name, 10)
        
        # Display key stats
        print(f"Win Rate: {analysis['win_rate']}%")
        print(f"Average KDA: {analysis['average_kda']['kills']}/{analysis['average_kda']['deaths']}/{analysis['average_kda']['assists']}")
        
        # Show champion stats
        print("\nTop Champions:")
        for champion, stats in list(analysis['champion_stats'].items())[:3]:
            print(f"  {champion}: {stats['games']} games, {stats['win_rate']}% WR")
        
    except RiotAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()