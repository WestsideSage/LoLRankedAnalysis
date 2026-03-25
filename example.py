#!/usr/bin/env python3
"""
Example: using the LoL Analysis library programmatically.
"""
import os
from dotenv import load_dotenv
from lol_analysis.riot_api import RiotAPIClient, RiotAPIError
from lol_analysis.analyzer import MatchAnalyzer


def main():
    load_dotenv()

    api_key = os.getenv('RIOT_API_KEY')
    if not api_key:
        print("Set RIOT_API_KEY in your .env file first.")
        return

    # ── Configuration ─────────────────────────────────────────────
    game_name = "YourName"     # Replace with your Riot ID name
    tag_line = "NA1"           # Replace with your tag
    region = "na1"             # Platform region

    try:
        client = RiotAPIClient(api_key, region)
        analyzer = MatchAnalyzer(client)

        # Look up account
        account = client.get_account_by_riot_id(game_name, tag_line)
        print(f"Account: {account.game_name}#{account.tag_line}")

        # Get rank
        for entry in client.get_rank_entries(account.puuid):
            if entry.queue_type == 'RANKED_SOLO_5x5':
                print(f"Rank: {entry.tier} {entry.rank} ({entry.league_points} LP)")

        # Analyze recent ranked matches
        print("\nAnalyzing last 10 ranked games...")
        analysis = analyzer.analyze_matches(
            puuid=account.puuid,
            match_count=10,
            display_name=f"{account.game_name}#{account.tag_line}",
        )

        print(f"Win Rate: {analysis['win_rate']}%")
        kda = analysis['average_kda']
        print(f"KDA: {kda['kills']}/{kda['deaths']}/{kda['assists']} ({kda['ratio']})")

        if analysis['strengths']:
            print("\nStrengths:")
            for s in analysis['strengths']:
                print(f"  + {s}")

        if analysis['weaknesses']:
            print("\nWeaknesses:")
            for w in analysis['weaknesses']:
                print(f"  - {w}")

    except RiotAPIError as e:
        print(f"API Error: {e}")


if __name__ == "__main__":
    main()
