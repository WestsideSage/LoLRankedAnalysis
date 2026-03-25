"""
Riot Games API client for League of Legends data.

Uses the modern Account v1 API (Riot IDs) and Match v5 API.
"""
import requests
import time
from typing import List, Optional, Dict, Any
from .models import RiotAccount, Summoner, RankEntry


class RiotAPIError(Exception):
    pass


class RiotAPIClient:
    """Client for interacting with the Riot Games API"""

    # Platform-specific URLs (for summoner, league, spectator endpoints)
    PLATFORM_URLS = {
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
        'ru': 'https://ru.api.riotgames.com',
        'ph2': 'https://ph2.api.riotgames.com',
        'sg2': 'https://sg2.api.riotgames.com',
        'th2': 'https://th2.api.riotgames.com',
        'tw2': 'https://tw2.api.riotgames.com',
        'vn2': 'https://vn2.api.riotgames.com',
    }

    # Regional URLs (for account, match, and tournament endpoints)
    REGIONAL_URLS = {
        'americas': 'https://americas.api.riotgames.com',
        'asia': 'https://asia.api.riotgames.com',
        'europe': 'https://europe.api.riotgames.com',
        'sea': 'https://sea.api.riotgames.com',
    }

    # Platform -> Regional routing
    REGION_MAPPING = {
        'br1': 'americas',
        'la1': 'americas',
        'la2': 'americas',
        'na1': 'americas',
        'oc1': 'sea',
        'eun1': 'europe',
        'euw1': 'europe',
        'tr1': 'europe',
        'ru': 'europe',
        'jp1': 'asia',
        'kr': 'asia',
        'ph2': 'sea',
        'sg2': 'sea',
        'th2': 'sea',
        'tw2': 'sea',
        'vn2': 'sea',
    }

    def __init__(self, api_key: str, region: str = 'na1'):
        self.api_key = api_key
        self.region = region.lower()
        self.platform_url = self.PLATFORM_URLS.get(self.region)
        self.regional_url = self.REGIONAL_URLS.get(
            self.REGION_MAPPING.get(self.region, ''), ''
        )

        if not self.platform_url:
            raise ValueError(
                f"Invalid region: {region}. "
                f"Valid regions: {', '.join(sorted(self.PLATFORM_URLS.keys()))}"
            )

        self.session = requests.Session()
        self.session.headers.update({'X-Riot-Token': self.api_key})

        # Rate limiting
        self._last_request_time = 0.0
        self._request_delay = 1.2  # seconds between requests

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Any:
        """Make a rate-limited request to the API"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._request_delay:
            time.sleep(self._request_delay - elapsed)

        response = self.session.get(url, params=params, timeout=15)
        self._last_request_time = time.time()

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise RiotAPIError(f"Not found (404). Check that the name/tag/region is correct.")
        elif response.status_code == 403:
            raise RiotAPIError("Forbidden (403). Your API key may be expired or invalid.")
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 30))
            print(f"  Rate limited - waiting {retry_after}s...")
            time.sleep(retry_after)
            return self._make_request(url, params)
        else:
            raise RiotAPIError(
                f"API error {response.status_code}: {response.text[:200]}"
            )

    # ── Account v1 (Riot ID lookups) ──────────────────────────────────

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> RiotAccount:
        """Look up a Riot account by Riot ID (GameName#TagLine).

        Uses the regional routing (americas/europe/asia/sea).
        """
        url = (
            f"{self.regional_url}"
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        data = self._make_request(url)
        return RiotAccount.from_dict(data)

    def get_account_by_puuid(self, puuid: str) -> RiotAccount:
        """Look up a Riot account by PUUID."""
        url = f"{self.regional_url}/riot/account/v1/accounts/by-puuid/{puuid}"
        data = self._make_request(url)
        return RiotAccount.from_dict(data)

    # ── Summoner v4 ───────────────────────────────────────────────────

    def get_summoner_by_puuid(self, puuid: str) -> Summoner:
        """Get summoner data (level, icon, etc.) by PUUID."""
        url = f"{self.platform_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        data = self._make_request(url)
        return Summoner.from_dict(data)

    # ── League v4 (rank info) ─────────────────────────────────────────

    def get_rank_entries(self, puuid: str) -> List[RankEntry]:
        """Get ranked entries by PUUID."""
        url = f"{self.platform_url}/lol/league/v4/entries/by-puuid/{puuid}"
        data = self._make_request(url)
        return [RankEntry.from_dict(entry) for entry in data]

    # ── Match v5 ──────────────────────────────────────────────────────

    def get_match_ids(
        self,
        puuid: str,
        count: int = 20,
        start: int = 0,
        queue: Optional[int] = 420,
    ) -> List[str]:
        """Get match IDs for a player.

        queue=420 is Solo/Duo Ranked. Pass None for all queues.
        """
        url = f"{self.regional_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params: Dict[str, Any] = {'start': start, 'count': min(count, 100)}
        if queue is not None:
            params['queue'] = queue
        return self._make_request(url, params)

    def get_match(self, match_id: str) -> Dict[str, Any]:
        """Get full match data by match ID."""
        url = f"{self.regional_url}/lol/match/v5/matches/{match_id}"
        return self._make_request(url)

    # ── Convenience ───────────────────────────────────────────────────

    def get_recent_matches(
        self,
        puuid: str,
        count: int = 20,
        queue: Optional[int] = 420,
    ) -> List[Dict[str, Any]]:
        """Fetch full match data for a player's recent games."""
        match_ids = self.get_match_ids(puuid, count, queue=queue)
        matches = []
        for i, match_id in enumerate(match_ids):
            print(f"  Fetching match {i + 1}/{len(match_ids)}...", end='\r')
            matches.append(self.get_match(match_id))
        print()  # clear the \r line
        return matches
