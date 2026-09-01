"""
Data Sources for NFL Game-Level Player Stats (2022-2025)

This guide shows where to get the historical player performance data needed
for the matchup analyzer to identify problem opponents.
"""

# ============================================================================
# OPTION 1: Pro Football Reference (RECOMMENDED)
# ============================================================================
"""
Source: https://www.pro-football-reference.com
Data: Game-by-game stats for all NFL players (2022-2025)
Cost: Free
Difficulty: Moderate (requires web scraping or manual download)

Steps:
1. Go to: https://www.pro-football-reference.com/players/[FIRST_LETTER]/[LastNameFirst]##.htm
   Example: https://www.pro-football-reference.com/players/m/MahomPa00.htm
   
2. Find "Game Logs" section for each season (2022-2025)
   - Shows: Date, Week, Opponent, Fantasy Points, all stats
   
3. Export or scrape the data to CSV format with columns:
   season, week, game_date, player_name, team, opponent, fantasy_points, 
   passing_yds, passing_td, interceptions, rushing_yds, receiving_yds, etc.

Python Tool to Scrape:
   pip install beautifulsoup4 requests pandas
   
   Example Code:
   import requests
   from bs4 import BeautifulSoup
   import pandas as pd
   
   url = "https://www.pro-football-reference.com/players/m/MahomPa00.htm"
   response = requests.get(url)
   soup = BeautifulSoup(response.content, 'html.parser')
   # Parse game logs tables for 2022-2025
"""


# ============================================================================
# OPTION 2: nfl-data GitHub Repository (EASIEST)
# ============================================================================
"""
Source: https://github.com/nflverse/nfldata
Data: Complete game-level statistics (2022-2025)
Cost: Free
Difficulty: Easy (direct download or API)
Popular: Yes, well-maintained by the community

Key Datasets Available:
1. play_by_play data (every play in every game)
2. games (game results, scores, opponent info)
3. player game statistics (combine games + player stats)

Installation:
   pip install nflverse  # Python client
   
   # or download CSV directly
   https://github.com/nflverse/nfldata/blob/master/data/games.csv
   https://github.com/nflverse/nfldata/blob/master/data/player_stats.csv

Example Python Code to Load Data:
   import nflverse
   import pandas as pd
   
   # Load play-by-play and game data for 2022-2025
   pbp = nflverse.load_pbp(2022)  # Returns all plays from 2022
   games = nflverse.load_games(2022)
   stats = nflverse.load_player_stats(2022)
   
   # Combine to get player stats by opponent
   player_opponent_stats = stats.merge(
       games[['game_id', 'opponent']],
       on='game_id'
   )

GitHub Repo Links:
   - Player Stats: https://github.com/nflverse/nfldata/releases
   - Direct Downloads: https://github.com/nflverse/nfldata
   - Documentation: https://nflverse.nfldata.com/
"""


# ============================================================================
# OPTION 3: ESPN API (FREE, NO AUTH NEEDED)
# ============================================================================
"""
Source: ESPN Sports API
Data: Game scores, schedules, limited player stats
Cost: Free, No API key required
Difficulty: Medium (requires API calls)

Limitations:
   - Better for schedule/scores than detailed player stats
   - Some endpoints require parsing from HTML

Useful Endpoints:
   GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
   GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?week=1&season=2022
   
Example Python Code:
   import requests
   import pandas as pd
   
   for season in [2022, 2023, 2024, 2025]:
       for week in range(1, 19):
           url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
           params = {'season': season, 'week': week}
           response = requests.get(url, params=params)
           games = response.json()['events']
           
           # Extract game info and opponent data
           for game in games:
               # Parse competitors and scores

Note: May need to supplement with other sources for player-level stats
"""


# ============================================================================
# OPTION 4: Kaggle Datasets (EASY)
# ============================================================================
"""
Source: https://www.kaggle.com
Data: Multiple curated NFL datasets
Cost: Free (with Kaggle account)
Difficulty: Easy (download directly)

Recommended Datasets:
1. "NFL Game Statistics and Analytics" (up to 2022)
   https://www.kaggle.com/datasets/cviaxmiwnptr/nfl-game-data
   
2. "NFL Player Statistics (2022 Season)"
   https://www.kaggle.com/datasets/tobycrabtree/nfl-scores-and-elo-ratings
   
3. "NFL Scores and Statistics (1989-2022)"
   https://www.kaggle.com/datasets/toddstewart/nfl-scores

Steps:
1. Create Kaggle account (free)
2. Search for "NFL player stats" or "NFL game data"
3. Download CSV files
4. Import into your pipeline

Python to Load:
   import pandas as pd
   df = pd.read_csv('nfl_player_stats_2022_2025.csv')
"""


# ============================================================================
# OPTION 5: NFLDB (Database)
# ============================================================================
"""
Source: https://github.com/BurntSushi/nfldb
Data: Comprehensive NFL statistics database
Cost: Free
Difficulty: Hard (requires database setup)

Features:
   - Complete play-by-play data
   - Player game statistics
   - Opponent information
   - Query via Python or SQL

Installation:
   pip install nfldb
   python nfldb-update.py  # Download latest data
   
Example Query:
   import nfldb
   db = nfldb.connect()
   
   # Get Mahomes stats vs each team
   query = db.query(nfldb.PlayPlayer).filter_by(player_name='Patrick Mahomes')
   for play in query:
       print(f"{play.team} vs {play.opp}: {play.passing_yds} yards")
"""


# ============================================================================
# QUICK START RECOMMENDATION
# ============================================================================
"""
BEST FOR THIS PROJECT:

1. FASTEST (1 hour): 
   → Use nflverse/nfldata GitHub repo
   → pip install nflverse
   → Load stats + games → merge on opponent
   
2. MANUAL (2-4 hours):
   → Pro Football Reference
   → Copy/paste game logs for key players (Mahomes, Kelce, etc.)
   → Format into CSV template
   
3. SCRIPT IT (3-5 hours):
   → Web scrape Pro Football Reference
   → Parse opponent from game results
   → Output to game_level_stats.csv

EXAMPLE DATA STRUCTURE (after processing):
   season | week | game_date  | player_name      | team | opponent | fantasy_points
   2022   | 1    | 2022-09-09 | Patrick Mahomes  | KC   | ARI      | 25.3
   2022   | 2    | 2022-09-15 | Patrick Mahomes  | KC   | LAC      | 22.1
   2022   | 3    | 2022-09-22 | Patrick Mahomes  | KC   | GB       | 8.5
   ...
"""


# ============================================================================
# PYTHON SCRIPT TO FETCH FROM NFLVERSE (RECOMMENDED)
# ============================================================================
"""
This is the easiest approach. Run this script to get data:
"""

def fetch_nfl_stats_from_nflverse():
    """Fetch game-level stats from nflverse for 2022-2025."""
    
    try:
        import nflverse
        import pandas as pd
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'nflverse', 'pandas'])
        import nflverse
        import pandas as pd
    
    print("Fetching NFL game-level stats (2022-2025)...")
    print("This may take a few minutes on first run...\n")
    
    all_stats = []
    
    for season in [2022, 2023, 2024, 2025]:
        print(f"Loading {season} stats...")
        try:
            # Load player stats for the season
            stats = nflverse.load_player_stats(season)
            
            # Load games to get opponent info
            games = nflverse.load_games(season)
            
            # Merge to add opponent
            if stats is not None and games is not None:
                # Merge on game_id
                merged = stats.merge(
                    games[['game_id', 'opponent', 'week']],
                    on='game_id',
                    how='left'
                )
                
                # Select relevant columns
                game_stats = merged[[
                    'season', 'week', 'game_date', 'player_name', 
                    'position', 'team', 'opponent', 'fantasy_points'
                ]].copy()
                
                all_stats.append(game_stats)
                print(f"  ✓ Loaded {len(game_stats)} player-game records")
        
        except Exception as e:
            print(f"  ✗ Error loading {season}: {e}")
    
    if all_stats:
        df = pd.concat(all_stats, ignore_index=True)
        df.to_csv('data/silver/game_level_stats.csv', index=False)
        print(f"\n✓ SUCCESS: Saved {len(df)} records to data/silver/game_level_stats.csv")
        return df
    else:
        print("\n✗ Failed to fetch any data")
        return None


# ============================================================================
# ALTERNATIVE: FETCH FROM PRO-FOOTBALL-REFERENCE (WEB SCRAPING)
# ============================================================================
"""
If nflverse doesn't have the format you need, scrape Pro Football Reference:
"""

def scrape_pfr_for_player(player_url):
    """
    Scrape Pro Football Reference for a player's game logs.
    
    Example URL: https://www.pro-football-reference.com/players/m/MahomPa00.htm
    
    Returns: DataFrame with game-by-game stats
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import pandas as pd
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'beautifulsoup4', 'requests', 'pandas'])
        import requests
        from bs4 import BeautifulSoup
        import pandas as pd
    
    print(f"Scraping: {player_url}")
    
    response = requests.get(player_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all game log tables (one per season)
    tables = soup.find_all('table', {'id': 'stats'})
    
    all_games = []
    
    for table in tables:
        # Parse table rows
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 0:
                try:
                    game_data = {
                        'date': cols[0].text,
                        'week': cols[1].text,
                        'opponent': cols[3].text,
                        'fantasy_points': float(cols[9].text) if cols[9].text else 0
                    }
                    all_games.append(game_data)
                except:
                    pass
    
    return pd.DataFrame(all_games)


# ============================================================================
# RUN THIS TO GET DATA
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NFL PLAYER STATS DATA FETCHER")
    print("="*70)
    print("\nOption 1: Fetch from nflverse (RECOMMENDED - Easiest)")
    print("Option 2: Manual download from Pro Football Reference")
    print("Option 3: Web scrape specific player URLs")
    print("\n" + "="*70)
    
    choice = input("\nEnter your choice (1/2/3) or 'help' for more info: ").strip()
    
    if choice == '1':
        print("\nAttempting to fetch from nflverse...")
        df = fetch_nfl_stats_from_nflverse()
        if df is not None:
            print(f"\nData loaded successfully!")
            print(f"Players: {df['player_name'].nunique()}")
            print(f"Seasons: {sorted(df['season'].unique())}")
            print(f"Opponents: {df['opponent'].nunique()}")
    
    elif choice == '2':
        print("\nManual Download Instructions:")
        print("1. Visit: https://www.pro-football-reference.com")
        print("2. Search for each player you want (e.g., 'Patrick Mahomes')")
        print("3. Click player name, scroll to 'Game Logs'")
        print("4. For each season (2022-2025), export or copy the table")
        print("5. Format into CSV and save to: data/silver/game_level_stats.csv")
    
    elif choice == '3':
        player_url = input("Enter Pro Football Reference player URL: ").strip()
        df = scrape_pfr_for_player(player_url)
        print(f"\nScraped {len(df)} games")
        print(df.head())
    
    else:
        print("\nData Sources Available:")
        print("• nflverse (https://github.com/nflverse/nfldata) - BEST")
        print("• Pro Football Reference (https://www.pro-football-reference.com) - Manual")
        print("• Kaggle (https://www.kaggle.com) - Datasets")
        print("• ESPN API (https://www.espn.com/apis) - Limited")
        print("• NFLDB (https://github.com/BurntSushi/nfldb) - Complex")
