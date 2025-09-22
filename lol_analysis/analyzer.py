"""
Analysis functions for League of Legends match data
"""
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import statistics
from .riot_api import RiotAPIClient
from .models import RankEntry


class MatchAnalyzer:
    """Analyzes League of Legends match data"""
    
    def __init__(self, api_client: RiotAPIClient):
        self.api_client = api_client
    
    def find_player_data(self, match_data: Dict[Any, Any], puuid: str) -> Dict[Any, Any]:
        """Find the specific player's data in a match"""
        for participant in match_data['info']['participants']:
            if participant['puuid'] == puuid:
                return participant
        return {}
    
    def analyze_matches(self, summoner_name: str, match_count: int = 20) -> Dict[str, Any]:
        """Analyze recent matches for a summoner"""
        summoner = self.api_client.get_summoner_by_name(summoner_name)
        matches = self.api_client.get_recent_matches(summoner_name, match_count)
        rank_entries = self.api_client.get_rank_entries(summoner.id)
        
        # Initialize analysis data
        analysis = {
            'summoner_info': {
                'name': summoner.name,
                'level': summoner.summonerLevel,
                'puuid': summoner.puuid
            },
            'rank_info': {},
            'total_matches': len(matches),
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'champion_stats': defaultdict(lambda: {'games': 0, 'wins': 0, 'kills': [], 'deaths': [], 'assists': []}),
            'average_kda': {'kills': 0, 'deaths': 0, 'assists': 0},
            'total_damage_avg': 0,
            'cs_per_minute_avg': 0,
            'vision_score_avg': 0,
            'recent_performance': []
        }
        
        # Add rank information
        for entry in rank_entries:
            if entry.queueType == 'RANKED_SOLO_5x5':
                analysis['rank_info'] = {
                    'tier': entry.tier,
                    'rank': entry.rank,
                    'lp': entry.leaguePoints,
                    'wins': entry.wins,
                    'losses': entry.losses,
                    'win_rate': round((entry.wins / (entry.wins + entry.losses)) * 100, 1) if entry.wins + entry.losses > 0 else 0
                }
        
        total_kills = []
        total_deaths = []
        total_assists = []
        total_damage = []
        total_cs = []
        total_duration = []
        vision_scores = []
        
        for match in matches:
            player_data = self.find_player_data(match, summoner.puuid)
            if not player_data:
                continue
            
            # Basic match info
            won = player_data['win']
            champion = player_data['championName']
            kills = player_data['kills']
            deaths = player_data['deaths']
            assists = player_data['assists']
            damage = player_data['totalDamageDealtToChampions']
            cs = player_data['totalMinionsKilled']
            duration_minutes = match['info']['gameDuration'] / 60
            vision_score = player_data['visionScore']
            
            # Update overall stats
            if won:
                analysis['wins'] += 1
            else:
                analysis['losses'] += 1
            
            # Champion-specific stats
            analysis['champion_stats'][champion]['games'] += 1
            if won:
                analysis['champion_stats'][champion]['wins'] += 1
            analysis['champion_stats'][champion]['kills'].append(kills)
            analysis['champion_stats'][champion]['deaths'].append(deaths)
            analysis['champion_stats'][champion]['assists'].append(assists)
            
            # Aggregate stats
            total_kills.append(kills)
            total_deaths.append(deaths)
            total_assists.append(assists)
            total_damage.append(damage)
            total_cs.append(cs)
            total_duration.append(duration_minutes)
            vision_scores.append(vision_score)
            
            # Recent performance (last 10 games)
            if len(analysis['recent_performance']) < 10:
                analysis['recent_performance'].append({
                    'champion': champion,
                    'win': won,
                    'kda': f"{kills}/{deaths}/{assists}",
                    'damage': damage,
                    'cs': cs,
                    'duration_minutes': round(duration_minutes, 1)
                })
        
        # Calculate averages
        if total_kills:
            analysis['win_rate'] = round((analysis['wins'] / analysis['total_matches']) * 100, 1)
            analysis['average_kda']['kills'] = round(statistics.mean(total_kills), 1)
            analysis['average_kda']['deaths'] = round(statistics.mean(total_deaths), 1)
            analysis['average_kda']['assists'] = round(statistics.mean(total_assists), 1)
            analysis['total_damage_avg'] = round(statistics.mean(total_damage))
            analysis['cs_per_minute_avg'] = round(statistics.mean([cs / duration for cs, duration in zip(total_cs, total_duration)]), 1)
            analysis['vision_score_avg'] = round(statistics.mean(vision_scores), 1)
        
        # Calculate champion win rates
        for champion, stats in analysis['champion_stats'].items():
            stats['win_rate'] = round((stats['wins'] / stats['games']) * 100, 1) if stats['games'] > 0 else 0
            stats['avg_kills'] = round(statistics.mean(stats['kills']), 1) if stats['kills'] else 0
            stats['avg_deaths'] = round(statistics.mean(stats['deaths']), 1) if stats['deaths'] else 0
            stats['avg_assists'] = round(statistics.mean(stats['assists']), 1) if stats['assists'] else 0
        
        return analysis
    
    def get_champion_recommendations(self, analysis: Dict[str, Any], min_games: int = 3) -> List[Dict[str, Any]]:
        """Get champion recommendations based on performance"""
        recommendations = []
        
        for champion, stats in analysis['champion_stats'].items():
            if stats['games'] >= min_games:
                recommendations.append({
                    'champion': champion,
                    'games': stats['games'],
                    'win_rate': stats['win_rate'],
                    'avg_kda': f"{stats['avg_kills']}/{stats['avg_deaths']}/{stats['avg_assists']}"
                })
        
        # Sort by win rate, then by games played
        recommendations.sort(key=lambda x: (x['win_rate'], x['games']), reverse=True)
        return recommendations[:5]  # Top 5 recommendations