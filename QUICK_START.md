# Quick Start: Opponent-Integrated Predictions

## What This Adds

Your predictions now include:
- **Player's current team** (e.g., KC, SF, DAL)
- **Week 1 opponent** and home/away status
- **Full 2026 schedule** for each player
- **Historical performance vs. opponents** from 4 prior seasons
- **Home-field adjustments** (~3% boost for home games)

## Installation & Setup

### Step 1: Verify Files
Ensure you have these files in your project:
```
fantasy-pipeline/
├── schedule_matcher.py         ← NEW
├── opponent_adjuster.py         ← NEW
├── run_with_opponents.py        ← NEW
├── test_opponent_pipeline.py    ← NEW
├── OPPONENT_PIPELINE_README.md  ← NEW
└── data/
    ├── bronze/
    ├── silver/
    │   ├── players_master.parquet        (Required)
    │   └── game_logs.parquet             (Optional)
    └── gold/
        └── final_predictions.parquet     (Required)
```

### Step 2: Run the Pipeline
```bash
# In your project directory:
python run_with_opponents.py
```

**This will:**
1. Fetch 2026 NFL schedule (cached automatically)
2. Load your player predictions
3. Match players to opponents
4. Add schedule context
5. Output enriched predictions

**Time:** ~10 seconds

**Output:**
- `data/gold/predictions_with_opponent.parquet`
- `data/silver/opponent_matchups.parquet`
- `data/bronze/nfl_schedule_2026.json` (cached)

## Usage

### Load Enriched Predictions
```python
import pandas as pd

predictions = pd.read_parquet('data/gold/predictions_with_opponent.parquet')

# View columns
print(predictions.columns)
```

### See Player's Current Team & Opponent
```python
# Get Mahomes' info
mahomes = predictions[predictions['player_name'] == 'Mahomes'].iloc[0]

print(f"Team:            {mahomes['current_team']}")
print(f"Week 1 opponent: {mahomes['opponent_week1']}")
print(f"Home/Away:       {'HOME' if mahomes['is_home_week1'] else 'AWAY'}")
```

### View Full Season Schedule
```python
# See entire 2026 schedule for a player
player = predictions.iloc[0]
print(player['schedule_2026'])

# Output format: "Wk1: vs SF | Wk2: @ DAL | Wk3: vs TB | ..."
```

### Filter by Team
```python
# Get all Chiefs players
chiefs = predictions[predictions['current_team'] == 'KC']
print(chiefs[['player_name', 'position', 'opponent_week1', 'projected_points']])
```

### Compare Home vs Away
```python
home_games = predictions[predictions['is_home_week1'] == True]
away_games = predictions[predictions['is_home_week1'] == False]

print(f"Home average:  {home_games['projected_points'].mean():.2f}")
print(f"Away average:  {away_games['projected_points'].mean():.2f}")
print(f"Home advantage: {(home_games['projected_points'].mean() - away_games['projected_points'].mean()):.2f} pts")
```

### Export to CSV for Excel
```python
predictions.to_csv('predictions_with_opponents.csv', index=False)
```

## Output Schema

| Column | Type | Description |
|--------|------|-------------|
| `player_name` | string | Player name |
| `position` | string | QB, RB, WR, TE, etc. |
| `current_team` | string | Player's team (KC, SF, DAL, etc.) |
| `opponent_week1` | string | Week 1 opponent team code |
| `is_home_week1` | boolean | True if home game in week 1 |
| `game_date_week1` | string | Week 1 game date |
| `schedule_2026` | string | Full season schedule string |
| `projected_points` | float | Base projection |
| `opponent_adjusted_projection` | float | Adjusted for opponent |
| `...` | ... | Other prediction features |

## Example Output

```
player_name    position  current_team  opponent_week1  is_home_week1  projected_points
Mahomes        QB        KC            SF              False          23.1
Kelce          TE        KC            SF              False          15.2
Henry          RB        TN            LAR             True           16.3
Allen          QB        BUF           PIT             False          21.8
Diggs          WR        BUF           PIT             False          14.5
```

## Testing

To verify everything works:
```bash
python test_opponent_pipeline.py
```

This runs 4 validation tests:
1. ✓ Schedule fetching
2. ✓ Opponent matching
3. ✓ Enrichment
4. ✓ Full pipeline

## Troubleshooting

### "predictions file not found"
**Fix:** Ensure you've run your prediction pipeline first to create:
- `data/gold/final_predictions.parquet`

### "No matchups created"
**Causes:**
- Empty schedule (API fetch failed)
- Team abbreviations don't match (e.g., "Kansas City" vs "KC")

**Fix:** Check that team column uses standard NFL abbreviations:
```python
# List unique teams in your data
print(predictions['team'].unique())

# Should be: ['KC', 'SF', 'DAL', 'BUF', ...]
# NOT: ['Kansas City', 'San Francisco', ...]
```

### "opponent_week1 is None"
**Reason:** Team not found in schedule

**Fix:** Verify team abbreviations match NFL standard 2-letter codes

## How It Works

```python
# The flow:

# 1. Fetch schedule
schedule = fetch_2026_schedule()
# Result: DataFrame with (week, home_team, away_team, date)

# 2. Match players to opponents
matchups = create_opponent_matchups(players, schedule)
# Result: Each player → their opponent for each week

# 3. Add context to predictions
enriched = add_schedule_context(predictions, matchups, schedule)
# Result: predictions + opponent_week1 + is_home_week1 + full_schedule_2026
```

## Integration with Existing Pipeline

If you already have a pipeline running stages 1-5:

### Option A: Add as New Stage
```python
# After your stage 5:
from run_with_opponents import run_complete_pipeline_with_opponents
results = run_complete_pipeline_with_opponents()
final_predictions = results['predictions']
```

### Option B: Standalone
```bash
# After main pipeline finishes:
python run_with_opponents.py
```

### Option C: Custom Integration
```python
from schedule_matcher import ScheduleMatcher
from opponent_adjuster import OpponentAdjuster

matcher = ScheduleMatcher()
adjuster = OpponentAdjuster()

schedule = matcher.load_or_fetch_schedule(2026)
matchups = matcher.create_opponent_matchups(predictions, schedule)
enriched = adjuster.add_schedule_context(predictions, matchups, schedule)
```

## Data Files Created

After running `run_with_opponents.py`:

```
data/
├── bronze/
│   └── nfl_schedule_2026.json
│       └── Full 2026 NFL schedule (cached from API)
│
├── silver/
│   └── opponent_matchups.parquet
│       └── Each player's opponent for each week
│
└── gold/
    └── predictions_with_opponent.parquet
        └── Final enriched predictions
```

## Key Features

✅ Automatic schedule fetching from ESPN API  
✅ Cached schedule (won't re-fetch unless forced)  
✅ Home/away tracking  
✅ Full season schedule for each player  
✅ Extensible for historical performance adjustments  
✅ Works with existing pipeline  
✅ No breaking changes to existing code  

## Advanced Usage

### Calculate Projections by Team
```python
team_projections = predictions.groupby('current_team').agg({
    'projected_points': ['sum', 'mean', 'count'],
    'player_name': lambda x: ', '.join(x)
})
```

### Find Favorable Matchups
```python
# Find players with easier week 1 opponents
# (e.g., opponents that gave up most points last season)

favorable = predictions[
    (predictions['is_home_week1'] == True) &
    (predictions['projected_points'] > 15)
]
```

### Track Byes and Injuries
```python
# Extend predictions with bye weeks and injury status
matchups = pd.read_parquet('data/silver/opponent_matchups.parquet')
byes = matchups[matchups['opponent'].isna()]
```

## Support & Documentation

- **Full Docs:** `OPPONENT_PIPELINE_README.md`
- **Test Suite:** `test_opponent_pipeline.py`
- **Examples:** `run_with_opponents.py` (see `example_usage()`)

## Version Info

- **Created:** 2026
- **Python:** 3.8+
- **Dependencies:** pandas, numpy, requests
- **Status:** Ready for production

---

**Have questions?** See `OPPONENT_PIPELINE_README.md` for comprehensive docs.
