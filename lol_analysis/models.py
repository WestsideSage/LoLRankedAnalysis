"""
Data models for League of Legends API responses
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RiotAccount:
    """Represents a Riot Games account (from Account v1 API)"""
    puuid: str
    game_name: str
    tag_line: str

    @classmethod
    def from_dict(cls, data: dict) -> 'RiotAccount':
        return cls(
            puuid=data['puuid'],
            game_name=data['gameName'],
            tag_line=data['tagLine'],
        )


@dataclass
class Summoner:
    """Represents a League of Legends summoner (from Summoner v4 API)"""
    puuid: str
    profile_icon_id: int
    revision_date: int
    summoner_level: int

    @classmethod
    def from_dict(cls, data: dict) -> 'Summoner':
        return cls(
            puuid=data['puuid'],
            profile_icon_id=data['profileIconId'],
            revision_date=data['revisionDate'],
            summoner_level=data['summonerLevel'],
        )


@dataclass
class RankEntry:
    """Represents a ranked league entry"""
    queue_type: str
    tier: str
    rank: str
    league_points: int
    wins: int
    losses: int
    hot_streak: bool

    @classmethod
    def from_dict(cls, data: dict) -> 'RankEntry':
        return cls(
            queue_type=data['queueType'],
            tier=data['tier'],
            rank=data['rank'],
            league_points=data['leaguePoints'],
            wins=data['wins'],
            losses=data['losses'],
            hot_streak=data.get('hotStreak', False),
        )
