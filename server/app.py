"""
FastAPI backend for the LoL Analysis Dashboard.
Wraps the existing lol_analysis package and exposes REST endpoints.
"""
import sys
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Ensure the project root is on sys.path so lol_analysis can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lol_analysis.config import Config
from lol_analysis.riot_api import RiotAPIClient, RiotAPIError
from lol_analysis.analyzer import MatchAnalyzer

app = FastAPI(title="LoL Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client_and_analyzer(region: str):
    config = Config()
    if not config.is_configured():
        raise HTTPException(status_code=500, detail="RIOT_API_KEY not configured in .env")
    client = RiotAPIClient(config.riot_api_key, region)
    analyzer = MatchAnalyzer(client)
    return client, analyzer


@app.get("/api/account")
def account_lookup(
    game_name: str = Query(...),
    tag_line: str = Query(...),
    region: str = Query("na1"),
):
    try:
        client, _ = get_client_and_analyzer(region)
        account = client.get_account_by_riot_id(game_name, tag_line)
        return {"puuid": account.puuid, "game_name": account.game_name, "tag_line": account.tag_line}
    except RiotAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/overview")
def overview(
    game_name: str = Query(...),
    tag_line: str = Query(...),
    region: str = Query("na1"),
):
    """Quick per-queue summary for the overview page."""
    try:
        client, analyzer = get_client_and_analyzer(region)
        account = client.get_account_by_riot_id(game_name, tag_line)
        puuid = account.puuid
        display = f"{account.game_name}#{account.tag_line}"

        # Rank info
        rank_info = {}
        entries = client.get_rank_entries(puuid)
        for e in entries:
            if e.queue_type == 'RANKED_SOLO_5x5':
                total = e.wins + e.losses
                rank_info = {
                    "tier": e.tier, "rank": e.rank, "lp": e.league_points,
                    "wins": e.wins, "losses": e.losses,
                    "win_rate": round((e.wins / total) * 100, 1) if total else 0,
                }

        # Per-queue game counts (fast - only fetches IDs, not full match data)
        queue_counts = {}
        for qid, name in [(420, "ranked"), (450, "aram"), (1700, "arena")]:
            ids = client.get_match_ids(puuid, count=100, queue=qid)
            queue_counts[name] = len(ids)

        return {
            "display_name": display,
            "puuid": puuid,
            "rank_info": rank_info,
            "queue_counts": queue_counts,
        }
    except RiotAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/ranked")
def ranked_analysis(
    game_name: str = Query(...),
    tag_line: str = Query(...),
    region: str = Query("na1"),
    matches: int = Query(20, ge=1, le=100),
):
    try:
        client, analyzer = get_client_and_analyzer(region)
        account = client.get_account_by_riot_id(game_name, tag_line)
        display = f"{account.game_name}#{account.tag_line}"
        result = analyzer.analyze_matches(
            puuid=account.puuid, match_count=matches, display_name=display,
        )
        return result
    except RiotAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/aram")
def aram_analysis(
    game_name: str = Query(...),
    tag_line: str = Query(...),
    region: str = Query("na1"),
    matches: int = Query(30, ge=1, le=100),
    mayhem: bool = Query(False),
):
    try:
        client, analyzer = get_client_and_analyzer(region)
        account = client.get_account_by_riot_id(game_name, tag_line)
        display = f"{account.game_name}#{account.tag_line}"
        mayhem_filter = "mayhem" if mayhem else None
        result = analyzer.analyze_aram(
            puuid=account.puuid, match_count=matches,
            display_name=display, mayhem_filter=mayhem_filter,
        )
        return result
    except RiotAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/arena")
def arena_analysis(
    game_name: str = Query(...),
    tag_line: str = Query(...),
    region: str = Query("na1"),
    matches: int = Query(30, ge=1, le=100),
):
    try:
        client, analyzer = get_client_and_analyzer(region)
        account = client.get_account_by_riot_id(game_name, tag_line)
        display = f"{account.game_name}#{account.tag_line}"
        result = analyzer.analyze_arena(
            puuid=account.puuid, match_count=matches, display_name=display,
        )
        return result
    except RiotAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
