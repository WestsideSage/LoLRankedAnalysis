# LoL Ranked Analysis

A Python tool for analyzing your League of Legends ranked match history using the Riot Games API. Get detailed insights into your performance, champion statistics, and improvement opportunities.

## Features

- **Match Analysis**: Analyze your recent ranked matches with detailed statistics
- **Champion Performance**: See win rates and KDA for each champion you play
- **Rank Information**: Display current rank and overall performance
- **Performance Metrics**: Track damage, CS, vision score, and more
- **Champion Recommendations**: Get suggestions for champions you perform well with
- **Recent Match History**: View detailed results from your most recent games

## Setup

### 1. Get a Riot API Key

1. Go to [Riot Developer Portal](https://developer.riotgames.com/)
2. Sign in with your Riot Games account
3. Generate a personal API key (valid for 24 hours for development)
4. For production use, you'll need to apply for a production key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Application

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your configuration:
   ```
   RIOT_API_KEY=RGAPI-your-api-key-here
   SUMMONER_NAME=YourSummonerName
   REGION=na1
   ```

### Supported Regions

- `na1` - North America
- `euw1` - Europe West
- `eun1` - Europe Nordic & East
- `kr` - Korea
- `jp1` - Japan
- `br1` - Brazil
- `la1` - Latin America North
- `la2` - Latin America South
- `oc1` - Oceania
- `tr1` - Turkey
- `ru` - Russia

## Usage

### Basic Analysis

Analyze your recent matches (uses summoner name from .env):
```bash
python main.py analyze
```

### Analyze Specific Summoner

```bash
python main.py analyze --summoner "Summoner Name" --region na1
```

### Analyze More Matches

```bash
python main.py analyze --summoner "Summoner Name" --matches 50
```

### Show Setup Instructions

```bash
python main.py setup
```

## Example Output

```
============================================================
ANALYSIS FOR SUMMONER NAME
============================================================
Level: 150
Rank: Gold II (75 LP) - 65.2% WR
Recent Matches Analyzed: 20

OVERALL PERFORMANCE:
Win Rate: 60.0% (12W / 8L)
Average KDA: 8.2/5.1/9.3 (3.43)
Average Damage: 18,456
CS per Minute: 6.8
Average Vision Score: 15.2

CHAMPION PERFORMANCE:
┌────────────┬───────┬──────────┬───────────┐
│ Champion   │ Games │ Win Rate │ Avg KDA   │
├────────────┼───────┼──────────┼───────────┤
│ Jinx       │ 8     │ 75.0%    │ 9.1/4.2/8.5 │
│ Caitlyn    │ 6     │ 50.0%    │ 7.3/5.8/10.1│
│ Ezreal     │ 4     │ 50.0%    │ 8.0/5.0/9.0 │
│ Vayne      │ 2     │ 100.0%   │ 10.5/3.5/7.5│
└────────────┴───────┴──────────┴───────────┘

TOP CHAMPION RECOMMENDATIONS:
┌────────────┬───────┬──────────┬───────────┐
│ Champion   │ Games │ Win Rate │ Avg KDA   │
├────────────┼───────┼──────────┼───────────┤
│ Vayne      │ 2     │ 100.0%   │ 10.5/3.5/7.5│
│ Jinx       │ 8     │ 75.0%    │ 9.1/4.2/8.5 │
└────────────┴───────┴──────────┴───────────┘
```

## API Rate Limiting

The tool implements basic rate limiting to respect Riot's API limits:
- Personal API Key: 100 requests every 2 minutes
- Production API Key: Higher limits based on your approved rate

## Project Structure

```
LoLRankedAnalysis/
├── lol_analysis/
│   ├── __init__.py       # Package initialization
│   ├── models.py         # Data models for API responses
│   ├── riot_api.py       # Riot Games API client
│   ├── analyzer.py       # Match analysis logic
│   ├── config.py         # Configuration management
│   └── cli.py           # Command-line interface
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
├── .env.example        # Example configuration file
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Contributing

This is a personal project, but suggestions and improvements are welcome! Please feel free to open issues or submit pull requests.

## License

This project is for educational and personal use. Please respect Riot Games' API Terms of Service when using this tool.

## Disclaimer

This project is not affiliated with Riot Games. League of Legends is a trademark of Riot Games, Inc.
