"""
NFL PLAYER STATS DATA SOURCE GUIDE

For the matchup analyzer to identify problem opponents, you need game-level stats
showing how each player performed against each opponent (2022-2025).

This guide shows you the 3 easiest ways to get this data.
"""

print("""
================================================================================
EASIEST DATA SOURCES FOR 2022-2025 NFL PLAYER GAME-LEVEL STATS
================================================================================

OPTION 1: Pro Football Reference (RECOMMENDED - 30 min - Free)
────────────────────────────────────────────────────────────────────────────
URL:       https://www.pro-football-reference.com
Process:   Browse player → Copy game logs → Save to CSV
Cost:      Free
Difficulty: Easy (manual but straightforward)

Steps:
1. Go to Pro Football Reference: https://www.pro-football-reference.com
2. Search for a player (e.g., "Patrick Mahomes")
3. Click on their name
4. Scroll down to "Game Logs" section
5. For each season (2022, 2023, 2024, 2025):
   - Click on the year
   - You'll see a table with: Date, Week, Opponent, Fantasy Points, Passing Yds, etc.
   - Select all data (Ctrl+A)
   - Copy (Ctrl+C)
   - Paste into Excel or Google Sheets
   - Save as CSV

CSV Format Needed:
   game_date, week, opponent, player_name, position, team, fantasy_points, passing_yds, passing_td, ...

Example: https://www.pro-football-reference.com/players/m/MahomPa00.htm
         Click "2022 Game Logs" to see Mahomes vs each opponent that season

BEST FOR: Analyzing specific players (QB, top WRs, etc.)
TIME INVESTMENT: ~2-3 min per player × number of players you want


OPTION 2: Kaggle (EASIEST - 15 min - Free)
────────────────────────────────────────────────────────────────────────────
URL:       https://www.kaggle.com/datasets
Search:    "NFL player stats 2025"
Cost:      Free (need Kaggle account)
Difficulty: Very Easy (download CSV)

Steps:
1. Create free Kaggle account (https://www.kaggle.com)
2. Search: "NFL player game stats 2022 2023 2024 2025"
3. Find a dataset with game-level data
4. Download CSV file
5. Place in: fantasy-pipeline/data/silver/game_level_stats.csv

Recommended Datasets:
• "NFL Weekly Offensive Stats" - has opponent by week
• "NFL Player Performance Stats" - game-by-game
• "NFL 2024-2025 Season Data" - latest available

BEST FOR: Getting bulk data quickly without manual work
TIME INVESTMENT: 5-10 minutes


OPTION 3: GitHub NFL Data Repos (BEST - 10 min - Free)
────────────────────────────────────────────────────────────────────────────
URL:       https://github.com/topics/nfl-statistics
Popular:   - cooperdff/nfl_data_py
           - nflverse/nfldata (R package)
           - BurntSushi/nfldb (older)
Cost:      Free
Difficulty: Easy (download raw CSV files)

Steps:
1. Go to: https://github.com/cooperdff/nfl_data_py/releases
2. Find latest release with CSV files
3. Download: player_stats.csv or player_game_data.csv
4. OR use Python:
   
   import pandas as pd
   url = "https://raw.githubusercontent.com/cooperdff/nfl_data_py/main/data/player_stats.csv"
   df = pd.read_csv(url)
   df.to_csv('data/silver/game_level_stats.csv', index=False)

BEST FOR: Getting complete historical data programmatically
TIME INVESTMENT: 5-10 minutes


================================================================================
WHAT THE DATA SHOULD LOOK LIKE
================================================================================

Your CSV (game_level_stats.csv) should have columns:

    season, week, game_date, player_name, position, team, opponent, 
    is_home, fantasy_points, [position-specific stats]

Example rows:
    2022, 1, 2022-09-09, Patrick Mahomes, QB, KC, ARI, True, 25.3, ...
    2022, 2, 2022-09-15, Patrick Mahomes, QB, KC, LAC, False, 22.1, ...
    2022, 3, 2022-09-22, Patrick Mahomes, QB, KC, GB, True, 8.5, ...
    2023, 1, 2023-09-08, Patrick Mahomes, QB, KC, DET, False, 24.2, ...
    ...

Position-specific columns (if available):
    QB: passing_yds, passing_td, interceptions, rushing_yds
    RB: rushing_yds, rushing_td, receiving_yds, receptions, receiving_td
    WR/TE: receiving_yds, receiving_td, receptions, rushing_yds
    DEF: sacks, interceptions, touchdowns, fumble_recoveries


================================================================================
QUICK START: MANUAL APPROACH (FASTEST TO GET STARTED)
================================================================================

If you want to analyze specific players like "Does player X struggle against GB?":

1. Go to https://www.pro-football-reference.com
2. Search "Patrick Mahomes" (or your player)
3. Go to their page
4. Copy the 2022 Game Log table
5. Paste into Excel, add "opponent" column manually
6. Export as CSV

This takes ~5 minutes per player and gives you immediate results to test the system.

Once you're familiar with the pipeline, fetch bulk data from Kaggle or GitHub.


================================================================================
NEXT STEP: LOAD YOUR DATA
================================================================================

Once you have game_level_stats.csv in data/silver/:

    python nfl_matchup_analyzer.py

This will analyze your player data and identify problem opponents!


================================================================================
NEED HELP?
================================================================================

• Pro Football Reference page structure: Scroll to bottom for "Game Logs" link
• Kaggle dataset: Most recent dataset is usually in search results (sort by date)
• GitHub CSV: Look for "releases" tab or "data" folder
• Excel to CSV: Save As → CSV UTF-8 (.csv) file

The system works with ANY game-level data as long as it has:
    player_name, opponent, fantasy_points, season, week
    
Everything else is optional!
""")


# Quick Python script to read Pro Football Reference data if you paste it
def create_pfr_template():
    """Create template for data you copy/paste from Pro Football Reference."""
    import pandas as pd
    from pathlib import Path
    
    template = pd.DataFrame({
        'game_date': ['2022-09-09', '2022-09-15', '2022-09-22'],
        'week': [1, 2, 3],
        'player_name': ['Patrick Mahomes', 'Patrick Mahomes', 'Patrick Mahomes'],
        'position': ['QB', 'QB', 'QB'],
        'team': ['KC', 'KC', 'KC'],
        'opponent': ['ARI', 'LAC', 'GB'],
        'is_home': [True, False, True],
        'fantasy_points': [25.3, 22.1, 8.5],
        'season': [2022, 2022, 2022]
    })
    
    path = Path('data/silver/game_level_stats_example.csv')
    path.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(path, index=False)
    
    print(f"\n✓ Created example template: {path}")
    print("Fill this format with data from Pro Football Reference")
    

if __name__ == "__main__":
    create_pfr_template()
    print("\nData sources guide saved above!")
