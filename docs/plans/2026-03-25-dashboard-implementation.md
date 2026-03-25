# LoL Dashboard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an interactive web dashboard for visualizing LoL match data across all queue types with player comparison.

**Architecture:** FastAPI backend wrapping existing `lol_analysis` package, React + Vite frontend with Tailwind/shadcn/Recharts. Two local processes: backend on :8000, frontend on :5173.

**Tech Stack:** Python/FastAPI, React/TypeScript, Vite, Tailwind CSS, shadcn/ui, Recharts

---

### Task 1: Arena Analyzer

Add Arena analysis to the existing Python package so the backend can serve it.

**Files:**
- Modify: `lol_analysis/analyzer.py` (add `analyze_arena` method)
- Modify: `lol_analysis/riot_api.py` (no changes needed, `get_recent_matches` already accepts `queue` param)

**Step 1: Add `analyze_arena` method to `MatchAnalyzer`**

Add after the `analyze_aram` method in `lol_analysis/analyzer.py`:

```python
def analyze_arena(
    self,
    puuid: str,
    match_count: int = 30,
    display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Run analysis for Arena (2v2v2v2) games."""
    matches = self.api_client.get_recent_matches(puuid, match_count, queue=1700)

    games_parsed = 0
    placements = []
    all_kills, all_deaths, all_assists = [], [], []
    all_damage = []
    champion_stats: Dict[str, Dict] = defaultdict(lambda: {
        'games': 0, 'placements': [],
        'kills': [], 'deaths': [], 'assists': [],
        'damage': [],
    })
    recent_performance = []

    for match in matches:
        player = self._find_player(match, puuid)
        if not player:
            continue

        info = match['info']
        duration_min = info['gameDuration'] / 60
        if duration_min < 2:
            continue

        games_parsed += 1
        placement = player.get('placement', player.get('subteamPlacement', 8))
        kills = player['kills']
        deaths = player['deaths']
        assists = player['assists']
        damage = player['totalDamageDealtToChampions']
        champion = player['championName']

        placements.append(placement)
        all_kills.append(kills)
        all_deaths.append(deaths)
        all_assists.append(assists)
        all_damage.append(damage)

        cs_entry = champion_stats[champion]
        cs_entry['games'] += 1
        cs_entry['placements'].append(placement)
        cs_entry['kills'].append(kills)
        cs_entry['deaths'].append(deaths)
        cs_entry['assists'].append(assists)
        cs_entry['damage'].append(damage)

        recent_performance.append({
            'champion': champion,
            'placement': placement,
            'kda': f"{kills}/{deaths}/{assists}",
            'damage': damage,
            'duration_minutes': round(duration_min, 1),
        })

    def avg(lst):
        return round(statistics.mean(lst), 1) if lst else 0

    avg_placement = avg(placements)
    top4_count = sum(1 for p in placements if p <= 4)
    top4_rate = round((top4_count / games_parsed) * 100, 1) if games_parsed else 0
    first_count = sum(1 for p in placements if p == 1)
    first_rate = round((first_count / games_parsed) * 100, 1) if games_parsed else 0

    champion_summary = {}
    for champ, st in champion_stats.items():
        g = st['games']
        champion_summary[champ] = {
            'games': g,
            'avg_placement': avg(st['placements']),
            'top4_rate': round(sum(1 for p in st['placements'] if p <= 4) / g * 100, 1) if g else 0,
            'avg_kills': avg(st['kills']),
            'avg_deaths': avg(st['deaths']),
            'avg_assists': avg(st['assists']),
            'avg_damage': round(statistics.mean(st['damage'])) if st['damage'] else 0,
        }

    # Strengths/weaknesses
    strengths, weaknesses = [], []
    if avg_placement <= 3.5 and games_parsed >= 5:
        strengths.append(f"Strong avg placement ({avg_placement}) - consistently finishing high")
    elif avg_placement >= 5.5 and games_parsed >= 5:
        weaknesses.append(f"Avg placement is {avg_placement} - finishing in bottom half too often")

    if top4_rate >= 60:
        strengths.append(f"Top 4 in {top4_rate}% of games - solid consistency")
    elif top4_rate < 40 and games_parsed >= 5:
        weaknesses.append(f"Only top 4 in {top4_rate}% of games")

    if first_count >= 2:
        strengths.append(f"{first_count} first-place finishes")

    if champion_summary:
        qualified = {c: s for c, s in champion_summary.items() if s['games'] >= 2}
        if qualified:
            best = min(qualified.items(), key=lambda x: x[1]['avg_placement'])
            if best[1]['avg_placement'] <= 3.0:
                strengths.append(f"Strong on {best[0]} (avg {best[1]['avg_placement']} placement, {best[1]['games']} games)")

    avg_deaths_val = avg(all_deaths)
    if avg_deaths_val >= 8:
        weaknesses.append(f"Averaging {avg_deaths_val} deaths/game - dying too much in rounds")
    elif avg_deaths_val <= 3:
        strengths.append(f"Low deaths ({avg_deaths_val}/game) - great round survival")

    return {
        'mode': 'Arena',
        'display_name': display_name or 'Unknown',
        'total_matches': games_parsed,
        'avg_placement': avg_placement,
        'top4_rate': top4_rate,
        'top4_count': top4_count,
        'first_count': first_count,
        'first_rate': first_rate,
        'average_kda': {
            'kills': avg(all_kills),
            'deaths': avg_deaths_val,
            'assists': avg(all_assists),
            'ratio': round((avg(all_kills) + avg(all_assists)) / max(avg_deaths_val, 0.1), 2),
        },
        'avg_damage': round(statistics.mean(all_damage)) if all_damage else 0,
        'champion_stats': champion_summary,
        'recent_performance': recent_performance[:15],
        'strengths': strengths,
        'weaknesses': weaknesses,
    }
```

**Step 2: Verify it imports cleanly**

Run: `python -c "from lol_analysis.analyzer import MatchAnalyzer; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add lol_analysis/analyzer.py
git commit -m "feat: add Arena analysis mode"
```

---

### Task 2: FastAPI Backend

Create the API server that wraps the existing Python package.

**Files:**
- Create: `server/__init__.py`
- Create: `server/app.py`

**Step 1: Create `server/__init__.py`**

Empty file.

**Step 2: Create `server/app.py`**

```python
"""
FastAPI backend for the LoL Analysis Dashboard.
Wraps the existing lol_analysis package and exposes REST endpoints.
"""
import sys
import os
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
```

**Step 3: Verify the server starts**

Run: `cd /c/LoLRankedAnalysis && python -m uvicorn server.app:app --port 8000`
Expected: Server starts, `http://localhost:8000/docs` shows Swagger UI

**Step 4: Commit**

```bash
git add server/
git commit -m "feat: add FastAPI backend for dashboard"
```

---

### Task 3: Scaffold React Frontend

Set up the Vite + React + TypeScript project with Tailwind and shadcn/ui.

**Files:**
- Create: `dashboard/` (entire Vite project)

**Step 1: Create Vite project**

```bash
cd /c/LoLRankedAnalysis
npm create vite@latest dashboard -- --template react-ts
cd dashboard
npm install
```

**Step 2: Install Tailwind CSS v4**

```bash
npm install tailwindcss @tailwindcss/vite
```

Add Tailwind plugin to `vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

Replace `src/index.css` with:
```css
@import "tailwindcss";
```

**Step 3: Install shadcn/ui**

Follow shadcn init for Vite: `npx shadcn@latest init`
- Style: Default
- Color: Slate
- CSS variables: Yes

Then install components we need:
```bash
npx shadcn@latest add button card input select tabs table badge
```

**Step 4: Install Recharts and other deps**

```bash
npm install recharts lucide-react
```

**Step 5: Set up path aliases in tsconfig**

Ensure `tsconfig.json` has:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  }
}
```

**Step 6: Clean up default Vite files**

Remove default `App.css`, clean `App.tsx` to a minimal shell:
```tsx
function App() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <h1 className="text-2xl p-8">LoL Dashboard</h1>
    </div>
  )
}
export default App
```

**Step 7: Verify it runs**

```bash
npm run dev
```

Expected: `http://localhost:5173` shows "LoL Dashboard" on dark background.

**Step 8: Commit**

```bash
cd /c/LoLRankedAnalysis
git add dashboard/
git commit -m "feat: scaffold React frontend with Tailwind and shadcn/ui"
```

---

### Task 4: API Hooks and Types

Create TypeScript types matching the backend responses and React hooks for data fetching.

**Files:**
- Create: `dashboard/src/lib/types.ts`
- Create: `dashboard/src/hooks/use-api.ts`

**Step 1: Create types**

`dashboard/src/lib/types.ts` - define interfaces for `OverviewData`, `RankedAnalysis`, `AramAnalysis`, `ArenaAnalysis`, `ChampionStats`, `RecentMatch`, etc. matching the Python dicts returned by the API.

Key types:
```typescript
export interface KDA {
  kills: number; deaths: number; assists: number; ratio: number;
}

export interface ChampionStat {
  games: number; wins?: number; win_rate?: number;
  avg_kills: number; avg_deaths: number; avg_assists: number;
  avg_damage: number;
  avg_cs_per_min?: number; avg_damage_per_min?: number;
  avg_placement?: number; top4_rate?: number;
}

export interface OverviewData {
  display_name: string; puuid: string;
  rank_info: RankInfo | Record<string, never>;
  queue_counts: { ranked: number; aram: number; arena: number };
}

export interface RankedAnalysis {
  display_name: string; rank_info: RankInfo;
  total_matches: number; wins: number; losses: number; win_rate: number;
  average_kda: KDA; avg_damage: number; avg_gold: number;
  avg_cs_per_min: number; avg_vision_per_min: number;
  avg_kill_participation: number; avg_damage_share: number;
  champion_stats: Record<string, ChampionStat>;
  role_stats: Record<string, RoleStat>;
  recent_performance: RecentMatch[];
  strengths: string[]; weaknesses: string[];
}

// Similar for AramAnalysis, ArenaAnalysis
```

**Step 2: Create API hooks**

`dashboard/src/hooks/use-api.ts` - custom hooks using `fetch` + `useState`/`useEffect`:

```typescript
export function useOverview(gameName: string, tagLine: string, region: string)
export function useRankedAnalysis(gameName: string, tagLine: string, region: string, matches: number)
export function useAramAnalysis(gameName: string, tagLine: string, region: string, matches: number, mayhem: boolean)
export function useArenaAnalysis(gameName: string, tagLine: string, region: string, matches: number)
```

Each hook returns `{ data, loading, error }`.

**Step 3: Commit**

```bash
git add dashboard/src/lib/types.ts dashboard/src/hooks/use-api.ts
git commit -m "feat: add TypeScript types and API hooks"
```

---

### Task 5: Search Page and Layout Shell

Build the landing page with search bar and the app layout.

**Files:**
- Create: `dashboard/src/components/layout.tsx`
- Create: `dashboard/src/components/search-page.tsx`
- Modify: `dashboard/src/App.tsx`

**Implementation:**
- Dark background with centered content
- Animated title/logo area
- Search input for Riot ID (`Name#TAG`)
- Region dropdown (using shadcn Select)
- Recent searches from localStorage
- On search, transition to player overview

**Visual:** Dark gradient background, glassmorphism search card, blue/purple accent glow.

**Step: Commit**

```bash
git add dashboard/src/
git commit -m "feat: add search page with dark gaming theme"
```

---

### Task 6: Player Overview Page

Show the player header and queue cards.

**Files:**
- Create: `dashboard/src/components/player-overview.tsx`
- Create: `dashboard/src/components/queue-card.tsx`
- Create: `dashboard/src/components/rank-badge.tsx`

**Implementation:**
- Header: player name, rank emblem/badge, overall ranked stats
- Grid of queue cards: Ranked, ARAM, Mayhem, Arena
- Each card shows: game count, win rate (or top-4 rate for Arena), mini KDA
- Cards are clickable - navigate to queue detail view
- Loading skeletons while data fetches

**Step: Commit**

```bash
git add dashboard/src/components/
git commit -m "feat: add player overview page with queue cards"
```

---

### Task 7: Queue Detail View - Ranked

Build the full ranked analysis view with charts.

**Files:**
- Create: `dashboard/src/components/ranked-view.tsx`
- Create: `dashboard/src/components/stats-cards.tsx`
- Create: `dashboard/src/components/champion-table.tsx`
- Create: `dashboard/src/components/match-list.tsx`
- Create: `dashboard/src/components/charts/radar-chart.tsx`
- Create: `dashboard/src/components/charts/winrate-chart.tsx`
- Create: `dashboard/src/components/charts/champion-bar-chart.tsx`
- Create: `dashboard/src/components/strengths-weaknesses.tsx`

**Implementation:**
- Row of stat cards (win rate, KDA, damage, CS/min, vision/min, KP%)
- Champion performance table (sortable via shadcn Table)
- Recent matches list with expandable rows
- Radar chart: player stats vs tier benchmarks (Recharts RadarChart)
- Win rate over recent games (Recharts LineChart)
- Champion bar chart (Recharts BarChart, horizontal)
- Strengths in green cards, weaknesses in yellow/amber cards
- Role performance section

**Step: Commit**

```bash
git add dashboard/src/components/
git commit -m "feat: add ranked detail view with charts"
```

---

### Task 8: ARAM and Mayhem Detail Views

Adapt the ranked view for ARAM-specific metrics.

**Files:**
- Create: `dashboard/src/components/aram-view.tsx`

**Implementation:**
- Reuse stats-cards, champion-table, match-list, strengths-weaknesses components
- Different stat cards: Dmg/min, Gold/min, Damage Taken, Healing, KP% (no CS/vision)
- Pentakill/Quadrakill badges
- Radar chart axes: KDA / Dmg/min / KP / Damage Share / Gold/min
- Mayhem toggle switch (fetches with `?mayhem=true`)

**Step: Commit**

```bash
git add dashboard/src/components/aram-view.tsx
git commit -m "feat: add ARAM/Mayhem detail view"
```

---

### Task 9: Arena Detail View

Build the placement-based Arena view.

**Files:**
- Create: `dashboard/src/components/arena-view.tsx`
- Create: `dashboard/src/components/charts/placement-chart.tsx`

**Implementation:**
- Stat cards: Avg Placement, Top 4 Rate, 1st Place Count, KDA, Avg Damage
- Placement distribution chart (bar chart showing how many 1st, 2nd, ... 8th finishes)
- Champion table sorted by avg placement instead of win rate
- Radar chart: Placement / Kills / Damage / Top-4 Rate

**Step: Commit**

```bash
git add dashboard/src/components/
git commit -m "feat: add Arena detail view with placement stats"
```

---

### Task 10: Player Comparison View

Build the side-by-side comparison for roasting friends.

**Files:**
- Create: `dashboard/src/components/comparison-view.tsx`
- Create: `dashboard/src/components/comparison-bar.tsx`
- Create: `dashboard/src/components/charts/comparison-radar.tsx`

**Implementation:**
- Input fields to add 2-3 players (Riot IDs)
- Queue selector (which mode to compare)
- Overlaid radar chart with different colors per player
- Side-by-side horizontal bars for: WR, KDA, Damage, KP%, Deaths
- Color-coded highlights showing who's better at each stat
- "Winner" badge on the player with better overall stats

**Step: Commit**

```bash
git add dashboard/src/components/
git commit -m "feat: add player comparison view"
```

---

### Task 11: Navigation and Routing

Wire everything together with client-side routing.

**Files:**
- Modify: `dashboard/src/App.tsx`
- Install: `react-router-dom`

**Implementation:**
- Routes: `/` (search), `/player/:name/:tag` (overview), `/player/:name/:tag/:queue` (detail), `/compare` (comparison)
- Back navigation, tab switching between queues
- URL reflects current view so it's shareable/bookmarkable

**Step: Commit**

```bash
git add dashboard/src/
git commit -m "feat: add routing and navigation"
```

---

### Task 12: Polish and Final Integration

Final visual polish, loading states, error handling.

**Files:**
- Various component files
- Create: `dashboard/src/components/loading-skeleton.tsx`
- Create: `dashboard/src/components/error-display.tsx`

**Implementation:**
- Loading skeletons that match card layouts
- Error states with retry buttons
- Smooth page transitions
- Responsive layout (works on different screen sizes)
- Rate limit warning display when backend returns 429

**Step: Commit**

```bash
git add dashboard/
git commit -m "feat: add loading states, error handling, and visual polish"
```

---

### Running the Dashboard

**Terminal 1 (backend):**
```bash
cd /c/LoLRankedAnalysis
python -m uvicorn server.app:app --reload --port 8000
```

**Terminal 2 (frontend):**
```bash
cd /c/LoLRankedAnalysis/dashboard
npm run dev
```

Open `http://localhost:5173`
