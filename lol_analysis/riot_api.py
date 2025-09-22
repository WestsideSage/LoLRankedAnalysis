"""
Riot Games API client for League of Legends data
"""
import requests
import time
from typing import List, Optional, Dict, Any
from .models import Summoner, Match, RankEntry


class RiotAPIError(Exception):
    """Custom exception for Riot API errors"""
    pass


class RiotAPIClient:
    """Client for interacting with the Riot Games API"""
    
    BASE_URLS = {
        'br1': 'https://br1.api.riotgames.com',
        'eun1': 'https://eun1.api.riotgames.com',
        'euw1': 'https://euw1.api.riotgames.com',
        'jp1': 'https://jp1.api.riotgames.com',
        'kr': 'https://kr.api.riotgames.com',
        'la1': 'https://la1.api.riotgames.com',
        'la2': 'https://la2.api.riotgames.com',
        'na1': 'https://na1.api.riotgames.com',
        'oc1': 'https://oc1.api.riotgames.com',
        'tr1': 'https://tr1.api.riotgames.com',
        'ru': 'https://ru.api.riotgames.com'
    }
    
    REGIONAL_URLS = {
        'americas': 'https://americas.api.riotgames.com',
        'asia': 'https://asia.api.riotgames.com',
        'europe': 'https://europe.api.riotgames.com'
    }
    
    REGION_MAPPING = {
        'br1': 'americas',
        'la1': 'americas',
        'la2': 'americas',
        'na1': 'americas',
        'oc1': 'americas',
        'eun1': 'europe',
        'euw1': 'europe',
        'tr1': 'europe',
        'ru': 'europe',
        'jp1': 'asia',
        'kr': 'asia'
    }
    
    def __init__(self, api_key: str, region: str = 'na1'):
        self.api_key = api_key
        self.region = region.lower()
        self.base_url = self.BASE_URLS.get(self.region)
        self.regional_url = self.REGIONAL_URLS.get(self.REGION_MAPPING.get(self.region))
        
        if not self.base_url:
            raise ValueError(f"Invalid region: {region}")
        
        self.session = requests.Session()
        self.session.headers.update({'X-Riot-Token': self.api_key})
        
        # Rate limiting
        self.last_request_time = 0
        self.request_delay = 1.2  # seconds between requests
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
        """Make a rate-limited request to the API"""
        # Simple rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        try:
            response = self.session.get(url, params=params)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise RiotAPIError(f"Resource not found: {url}")
            elif response.status_code == 429:
                # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
                return self._make_request(url, params)
            else:
                raise RiotAPIError(f"API request failed: {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            raise RiotAPIError(f"Network error: {str(e)}")
    
    def get_summoner_by_name(self, summoner_name: str) -> Summoner:
        """Get summoner information by summoner name"""
        url = f"{self.base_url}/lol/summoner/v4/summoners/by-name/{summoner_name}"
        data = self._make_request(url)
        return Summoner.from_dict(data)
    
    def get_summoner_by_puuid(self, puuid: str) -> Summoner:
        """Get summoner information by PUUID"""
        url = f"{self.base_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        data = self._make_request(url)
        return Summoner.from_dict(data)
    
    def get_match_ids(self, puuid: str, count: int = 20, start: int = 0) -> List[str]:
        """Get match IDs for a summoner"""
        url = f"{self.regional_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {
            'start': start,
            'count': count,
            'queue': 420  # Solo/Duo Ranked queue
        }
        return self._make_request(url, params)
    
    def get_match(self, match_id: str) -> Dict[Any, Any]:
        """Get detailed match information"""
        url = f"{self.regional_url}/lol/match/v5/matches/{match_id}"
        return self._make_request(url)
    
    def get_rank_entries(self, summoner_id: str) -> List[RankEntry]:
        """Get ranked information for a summoner"""
        url = f"{self.base_url}/lol/league/v4/entries/by-summoner/{summoner_id}"
        data = self._make_request(url)
        return [RankEntry.from_dict(entry) for entry in data]
    
    def get_recent_matches(self, summoner_name: str, count: int = 20) -> List[Dict[Any, Any]]:
        """Get recent matches for a summoner"""
        summoner = self.get_summoner_by_name(summoner_name)
        match_ids = self.get_match_ids(summoner.puuid, count)
        
        matches = []
        for match_id in match_ids:
            match_data = self.get_match(match_id)
            matches.append(match_data)
        
        return matches