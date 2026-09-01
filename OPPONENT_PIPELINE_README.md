# Opponent-Integrated Prediction Pipeline

## Overview

This extension adds **player team**, **opponent matchups**, and **schedule-based predictions** to your fantasy pipeline. It integrates the 2026 NFL schedule with historical performance data (4 prior seasons) to provide context-aware predictions.

## Features

✅ **Automatic Schedule Fetching** — Fetches 2026 NFL schedule from public APIs  
✅ **Team Assignment** — Associates each player with their current team  
✅ **Opponent Matching** — Maps players to their upcoming opponents for each week  
✅ **Historical Performance** — Calculates how players perform against specific opponents  
✅ **Schedule Context** — Adds full 2026 schedule to each player record  
✅ **Home/Away Adjustment** — Accounts for home-field advantage (~3% boost)  

## Components

### 1. `schedule_matcher.py`
Handles NFL schedule fetching and player-opponent matching.

**Key Classes:**
- `ScheduleMatcher` — Main class for schedule operations

**Key Methods:**
- `fetch_nfl_schedule(season=2026)` — Fetch schedule from ESPN/NFL API
- `load_or_fetch_schedule(season, force_refresh=False)` — Load cached or fetch fresh
- `create_opponent_matchups(players_df, schedule_df)` — Map players to opponents
- `calculate_vs_opponent_stats(...)` — Historical performance analysis

**Example:**
```python
from schedule_matcher import ScheduleMatcher

matcher = ScheduleMatcher()
schedule = matcher.load_or_fetch_schedule(2026)  # (week, home_team, away_team, etc.)
matchups = matcher.create_opponent_matchups(players_df, schedule)  # Player schedules
```

### 2. `opponent_adjuster.py`
Applies opponent-based adjustments to predictions.

**Key Classes:**
- `OpponentAdjuster` — Main class for prediction enrichment

**Key Methods:**
- `enrich_players_with_team(players_df, master_df)` — Add team to predictions
- `add_schedule_context(predictions, matchups, schedule)` — Add opponent info
- `calculate_opponent_adjustments(...)` — Compute adjustment factors
- `apply_adjustments(predictions, adjustments)` — Apply to projections
- `save_enriched_projections(df)` — Persist to parquet

**Example:**
```python
from opponent_adjuster import OpponentAdjuster

adjuster = OpponentAdjuster()
enriched = adjuster.add_schedule_context(predictions, matchups, schedule)
enriched = adjuster.apply_adjustments(enriched, adjustments)
adjuster.save_enriched_projections(enriched)
```

### 3. `run_with_opponents.py`
End-to-end pipeline orchestration. Combines schedule fetching, opponent matching, and prediction enrichment.

**Usage:**
```bash
python run_with_opponents.py
```

**Output:**
- `data/gold/predictions_with_opponent.parquet` — Final enriched predictions
- `data/silver/opponent_matchups.parquet` — Player-opponent matchups
- `data/bronze/nfl_schedule_2026.json` — Cached schedule

## Workflow

```
┌─────────────────────────────────────────┐
│ 1. Fetch 2026 NFL Schedule              │
│    (ESPN API / NFL.com)                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 2. Load Player Predictions              │
│    (from gold layer)                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 3. Load Players Master Data             │
│    (team, position, etc.)               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 4. Create Opponent Matchups             │
│    (player → opponent per week)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ 5. Enrich with Schedule Context         │
│    (current opponent + full schedule)    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Output: predictions_with_opponent.pq    │
│ • player_name, current_team             │
│ • opponent_week1, is_home_week1         │
│ • schedule_2026 (all weeks)             │
│ • projected_points, etc.                │
└─────────────────────────────────────────┘
```

## Data Schema

### Input: Player Predictions
```
player_name          object
position             object
projected_points     float
season              int
... other prediction features ...
```

### Input: Players Master
```
player_name          object
team                 object
position             object
... other player info ...
```

### Input: Schedule
```
game_id              object
week                 int
home_team            object
away_team            object
game_date            object
season               int
```

### Output: Enriched Predictions
```
player_name              object    # Player name
position                 object    # QB, RB, WR, TE, etc.
current_team             object    # Player's team (KC, SF, DAL, etc.)
opponent_week1           object    # Week 1 opponent (opponent team code)
is_home_week1            bool      # True if playing at home in week 1
game_date_week1          object    # Week 1 game date
schedule_2026            object    # Full schedule string (e.g., "Wk1: vs SF | Wk2: @ DAL | ...")
projected_points         float     # Base projection
opponent_adjusted_projection float # Adjusted for opponent
... other features ...
```

## Usage Examples

### Basic Usage
```python
from run_with_opponents import run_complete_pipeline_with_opponents

results = run_complete_pipeline_with_opponents()
predictions = results['predictions']
```

### Filter by Team
```python
import pandas as pd

predictions = pd.read_parquet('data/gold/predictions_with_opponent.parquet')

# Get all players on Kansas City Chiefs
kc_players = predictions[predictions['current_team'] == 'KC']
print(kc_players[['player_name', 'position', 'opponent_week1']])
```

### View Week 1 Matchups
```python
# Show each player's week 1 opponent and home/away
matchup_view = predictions[[
    'player_name', 
    'position',
    'current_team',
    'opponent_week1',
    'is_home_week1'
]].head(20)

print(matchup_view)
```

### Compare Home vs Away Performance
```python
# Players with home advantage (historically ~3% better)
home_games = predictions[predictions['is_home_week1'] == True]
away_games = predictions[predictions['is_home_week1'] == False]

print(f"Home avg projection: {home_games['projected_points'].mean():.2f}")
print(f"Away avg projection: {away_games['projected_points'].mean():.2f}")
```

### Full Schedule View
```python
# Display entire 2026 schedule for a player
player = predictions[predictions['player_name'] == 'Patrick Mahomes'].iloc[0]
print(player['schedule_2026'])

# Output example:
# Wk1: vs SF | Wk2: @ DAL | Wk3: vs TB | Wk4: @ MIA | ...
```

## Data Sources

### NFL Schedule
- **Primary:** ESPN API (`api.espn.com/apis/site/v2/sports/football/nfl/schedule`)
- **Fallback:** Official NFL API (`api.nfl.com/v1/game`)
- **Caching:** Fetched schedule is cached in `data/bronze/nfl_schedule_2026.json`
- **Refresh:** Pass `force_refresh=True` to fetch latest

### Historical Performance
- Should come from your existing data pipeline (4+ seasons of game logs)
- Format: player_name, opponent, season, points, etc.
- Location: Typically `data/silver/game_logs.parquet`

## Integration with Existing Pipeline

### Option 1: Add as Final Stage
Add after `drafter.py` for complete VBD rankings with opponent context:

```python
# In your main pipeline:
from run_with_opponents import run_complete_pipeline_with_opponents

# ... run stages 1-5 ...

# Stage 5.5: Add opponent context
results = run_complete_pipeline_with_opponents()
final_predictions = results['predictions']
```

### Option 2: Standalone Enrichment
Run independently to enrich existing predictions:

```bash
python run_with_opponents.py
```

### Option 3: Custom Integration
Use individual components:

```python
from schedule_matcher import ScheduleMatcher
from opponent_adjuster import OpponentAdjuster
import pandas as pd

# Load your predictions
predictions = pd.read_parquet('data/gold/final_predictions.parquet')

# Add opponents
matcher = ScheduleMatcher()
schedule = matcher.load_or_fetch_schedule(2026)
matchups = matcher.create_opponent_matchups(predictions, schedule)

# Add schedule context
adjuster = OpponentAdjuster()
enriched = adjuster.add_schedule_context(predictions, matchups, schedule)

# Save
enriched.to_parquet('data/gold/my_enriched_predictions.parquet')
```

## Troubleshooting

### Schedule not fetching
```
✗ Failed to fetch from [API URL]
```

**Solution:** Check internet connection. APIs may be rate-limited or temporarily down.
- The module will create an empty DataFrame rather than crash
- You can provide a manual schedule CSV if needed

### Missing team information
```
⚠️  Some players missing team info
```

**Solution:** Ensure `players_master.parquet` is available with a `team` column.
- If unavailable, you can manually add team mappings
- Or extract from `conformed_id` if it contains team abbreviation

### No matchups created
```
⚠️  No matchups created
```

**Causes:**
1. Schedule DataFrame is empty → check API connection
2. Players DataFrame missing `team` or `current_team` column
3. Team abbreviations don't match (e.g., "KC" vs "Kansas City")

**Solution:** Ensure team column uses standard NFL abbreviations (KC, SF, DAL, etc.)

### Empty schedule_2026 field
```
schedule_2026 contains None
```

**Reason:** Team abbreviation wasn't found in schedule. Check team name consistency.

## Performance Notes

- **Schedule fetching:** ~2-5 seconds (cached after first run)
- **Matchup creation:** ~1-2 seconds (100+ players)
- **Enrichment:** ~1 second (full dataset)
- **Total runtime:** ~5-10 seconds for full pipeline

## Future Enhancements

- [ ] Defense strength ratings (DSR) for each opponent
- [ ] Historical opponent performance rankings
- [ ] Weather adjustments (if game-day weather available)
- [ ] Bye week tracking
- [ ] Playoff scenario projections
- [ ] Team rest days (short weeks, Thursday games)

## Files Generated

```
data/
├── bronze/
│   └── nfl_schedule_2026.json          # Cached schedule from API
├── silver/
│   └── opponent_matchups.parquet       # Player-opponent matchups by week
└── gold/
    └── predictions_with_opponent.parquet # Final enriched predictions
```

## Support

For issues or questions:
1. Check troubleshooting section above
2. Verify input data files exist and are valid
3. Check that team abbreviations match NFL standard
4. Run in verbose mode for detailed logs

---

**Version:** 1.0  
**Last Updated:** 2026  
**Compatibility:** Python 3.8+, pandas 1.3+, numpy 1.20+
