"""
Data models for League of Legends API responses
"""
from dataclasses import dataclass
from typing import List, Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Summoner:
    """Represents a League of Legends summoner"""
    id: str
    accountId: str
    puuid: str
    name: str
    profileIconId: int
    revisionDate: int
    summonerLevel: int


@dataclass_json
@dataclass
class MatchParticipant:
    """Represents a participant in a match"""
    championName: str
    championId: int
    summonerId: str
    summonerName: str
    teamId: int
    win: bool
    kills: int
    deaths: int
    assists: int
    totalDamageDealtToChampions: int
    totalMinionsKilled: int
    goldEarned: int
    visionScore: int
    item0: int
    item1: int
    item2: int
    item3: int
    item4: int
    item5: int
    item6: int


@dataclass_json
@dataclass
class MatchTeam:
    """Represents a team in a match"""
    teamId: int
    win: bool
    firstBlood: bool
    firstTower: bool
    firstInhibitor: bool
    firstRiftHerald: bool
    firstBaron: bool
    firstDragon: bool
    dragonKills: int
    baronKills: int
    riftHeraldKills: int
    inhibitorKills: int
    towerKills: int


@dataclass_json
@dataclass
class MatchInfo:
    """Represents match information"""
    gameId: int
    gameCreation: int
    gameDuration: int
    gameMode: str
    gameType: str
    gameVersion: str
    mapId: int
    platformId: str
    queueId: int
    seasonId: int
    participants: List[MatchParticipant]
    teams: List[MatchTeam]


@dataclass_json
@dataclass
class Match:
    """Represents a complete match"""
    metadata: dict
    info: MatchInfo


@dataclass_json
@dataclass
class RankEntry:
    """Represents a ranked league entry"""
    leagueId: str
    summonerId: str
    summonerName: str
    queueType: str
    tier: str
    rank: str
    leaguePoints: int
    wins: int
    losses: int
    hotStreak: bool
    veteran: bool
    freshBlood: bool
    inactive: bool