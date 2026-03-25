# LoL Analysis Dashboard - Design Document

## Overview

Interactive web dashboard for visualizing League of Legends match data across all queue types (Ranked, ARAM, ARAM: Mayhem, Arena) with side-by-side player comparison.

## Architecture

Two-process local setup:

- **Backend**: Python FastAPI server wrapping existing `riot_api.py` and `analyzer.py`. Runs on `localhost:8000`. Handles all Riot API calls, rate limiting, and data shaping. API key stays server-side.
- **Frontend**: React + Vite app on `localhost:5173`. Calls backend REST endpoints.

```
Browser (localhost:5173)
  -> React Frontend (Vite + Tailwind + shadcn/ui + Recharts)
  -> FastAPI Backend (localhost:8000)
  -> Riot Games API
```

### Project Structure

```
LoLRankedAnalysis/
  lol_analysis/          # existing Python package (unchanged)
  server/
    app.py               # FastAPI app with endpoints
  dashboard/
    src/
      components/        # React components
      hooks/             # data fetching hooks
      lib/               # utilities
    package.json
    vite.config.ts
    tailwind.config.ts
```

## Tech Stack

- **Frontend**: React, Vite, TypeScript, Tailwind CSS, shadcn/ui, Recharts
- **Backend**: FastAPI, existing lol_analysis package
- **Data**: Live fetch from Riot API (no caching/persistence)

## Backend API Endpoints

All endpoints accept `game_name`, `tag_line`, and `region` as query params.

| Endpoint | Description |
|---|---|
| `GET /api/account` | Riot account lookup (PUUID, display name) |
| `GET /api/overview` | Quick stats per queue (win rate, games, KDA) for landing page |
| `GET /api/ranked` | Full ranked analysis (reuses `analyze_matches`) |
| `GET /api/aram` | ARAM analysis, optional `?mayhem=true` filter (reuses `analyze_aram`) |
| `GET /api/arena` | Arena analysis (new, placement-based) |

No auth - local only. API key read from `.env` server-side.

## Frontend Views

### 1. Player Search (landing page)
- Centered search bar with Riot ID input (`Name#TAG`)
- Region dropdown selector
- Recent searches stored in localStorage

### 2. Player Overview
- Header card: player name, rank emblem, overall stats
- Row of queue cards (Ranked, ARAM, Mayhem, Arena) showing game count + win rate
- Click a queue card to drill into full analysis

### 3. Queue Detail View (tabbed)
- **Stats cards row**: Win rate (W/L), KDA ratio, Damage, CS/min or Dmg/min depending on mode
- **Champion performance table**: Sortable by games, WR, KDA, damage
- **Recent matches list**: Expandable rows with per-game details
- **Charts**:
  - Win rate over time (line chart)
  - Champion win rate breakdown (horizontal bar chart)
  - Radar chart: KDA / Damage / Vision / KP / CS vs tier benchmarks (ranked) or averages (ARAM)
- **Strengths & Weaknesses**: Styled cards with green/yellow accents

### 4. Player Comparison
- Add 2-3 players side by side
- Select which queue to compare
- Overlay radar charts showing where each player excels
- Side-by-side stat bars for key metrics (WR, KDA, damage, KP%)

## Arena-Specific Design

Arena (queue 1700) is 2v2v2v2 with placement-based results:
- `placement` field (1-8) replaces win/loss
- Key metrics: avg placement, top-4 rate, kills, deaths, damage
- Top 4 = "top half" (analogous to a win)
- Radar chart axes: Avg Placement / Kills / Damage / Top-4 Rate

## Visual Style

- Dark background (#0a0a0f), subtle gradient accents
- Glassmorphism stat cards with slight blur/transparency
- Blue/purple accent palette (League aesthetic)
- Smooth animations on chart renders and page transitions
- Gaming dashboard feel (op.gg / u.gg vibes)
