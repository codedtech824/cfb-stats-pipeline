"""
Automatically fetch NFL game-level stats from free APIs/endpoints (2022-2025)
No manual download needed - just run this script!
"""

import requests
import pandas as pd
from pathlib import Path
import json


def fetch_from_github_raw():
    """Fetch NFL player stats from GitHub raw data repository."""
    print("\n" + "="*70)
    print("FETCHING NFL STATS FROM GITHUB (cooperdff/nfl_data_py)")
    print("="*70)
    
    try:
        # This repo has cleaned NFL data as CSV files
        base_url = "https://raw.githubusercontent.com/cooperdff/nfl_data_py/main/data"
        
        print("Downloading player_stats.csv...", end=" ", flush=True)
        url = f"{base_url}/player_stats.csv"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            print(f"✓ Downloaded {len(df):,} records")
            
            # Filter to 2022-2025
            if 'season' in df.columns:
                df = df[df['season'].isin([2022, 2023, 2024, 2025])]
                print(f"  Filtered to 2022-2025: {len(df):,} records")
            
            return df
        else:
            print(f"✗ Status {response.status_code}")
            return None
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def fetch_from_espn_api():
    """Fetch game scores and opponent info from ESPN API."""
    print("\n" + "="*70)
    print("FETCHING GAMES FROM ESPN API")
    print("="*70)
    
    all_games = []
    
    for season in [2022, 2023, 2024, 2025]:
        print(f"\nFetching {season}...", end=" ", flush=True)
        try:
            # ESPN scoreboard API has game data
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            params = {'season': season, 'week': 1}  # Will get all weeks via pagination
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                
                for event in events:
                    try:
                        game_info = {
                            'game_id': event.get('id'),
                            'game_date': event.get('date'),
                            'season': season,
                            'week': event.get('competitions', [{}])[0].get('week')
                        }
                        
                        # Get matchup info
                        comp = event.get('competitions', [{}])[0]
                        competitors = comp.get('competitors', [])
                        
                        if len(competitors) >= 2:
                            home = competitors[0].get('team', {}).get('abbreviation')
                            away = competitors[1].get('team', {}).get('abbreviation')
                            
                            if home and away:
                                game_info['home_team'] = home
                                game_info['away_team'] = away
                                all_games.append(game_info)
                    except:
                        pass
                
                print(f"✓ {len(events)} games")
            else:
                print(f"✗ Status {response.status_code}")
        
        except Exception as e:
            print(f"✗ Error: {str(e)[:40]}")
    
    if all_games:
        return pd.DataFrame(all_games)
    return None


def fetch_nfl_data_py_api():
    """Use nfl_data_py library's built-in data fetching."""
    print("\n" + "="*70)
    print("FETCHING FROM NFL DATA PY LIBRARY")
    print("="*70)
    
    try:
        import nfl_data_py as nfl
        print("Importing nfl_data_py library...", end=" ", flush=True)
        
        all_stats = []
        for season in [2022, 2023, 2024, 2025]:
            print(f"\nLoading {season}...", end=" ", flush=True)
            try:
                # Load seasonal player stats
                stats = nfl.import_seasonal_data(season)
                if stats is not None and len(stats) > 0:
                    all_stats.append(stats)
                    print(f"✓ {len(stats):,} records")
            except Exception as e:
                print(f"✗ {str(e)[:30]}")
        
        if all_stats:
            df = pd.concat(all_stats, ignore_index=True)
            return df
        
    except ImportError:
        print("nfl_data_py not installed, trying alternative...")
    
    return None


def auto_fetch_nfl_stats():
    """Automatically fetch NFL stats from the best available source."""
    
    print("\n" + "="*70)
    print("🏈 AUTO-FETCHING 2022-2025 NFL PLAYER STATS")
    print("="*70)
    
    output_path = Path('data/silver/game_level_stats.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try multiple sources in order of preference
    df = None
    
    # Option 1: GitHub raw CSV (fastest, no dependencies)
    print("\n1. Trying GitHub repository...")
    df = fetch_from_github_raw()
    
    # Option 2: nfl_data_py library
    if df is None or len(df) == 0:
        print("\n2. Trying nfl_data_py library...")
        df = fetch_nfl_data_py_api()
    
    # Option 3: ESPN API (limited)
    if df is None or len(df) == 0:
        print("\n3. Trying ESPN API...")
        df = fetch_from_espn_api()
    
    # Save results
    if df is not None and len(df) > 0:
        # Clean up data
        df = df.dropna(subset=['season'])
        df = df[df['season'].isin([2022, 2023, 2024, 2025])]
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        print("\n" + "="*70)
        print("✅ SUCCESS - DATA SAVED")
        print("="*70)
        print(f"File: {output_path}")
        print(f"Total Records: {len(df):,}")
        
        if 'player_name' in df.columns:
            print(f"Unique Players: {df['player_name'].nunique():,}")
        if 'season' in df.columns:
            print(f"Seasons: {sorted(df['season'].unique())}")
        if 'game_date' in df.columns:
            print(f"Date Range: {df['game_date'].min()} to {df['game_date'].max()}")
        
        print("\n📊 Sample Data:")
        print("-" * 70)
        print(df.head(10).to_string())
        
        print("\n✓ Ready to analyze!")
        print("   python nfl_matchup_analyzer.py")
        
        return df
    
    else:
        print("\n" + "="*70)
        print("❌ FAILED TO FETCH DATA")
        print("="*70)
        print("\nAll API sources failed. This might be due to:")
        print("• Network connectivity issues")
        print("• APIs being temporarily down")
        print("• Rate limiting")
        
        print("\n📝 Manual Fallback:")
        print("Download from: https://www.kaggle.com/datasets")
        print("Search: 'NFL player game stats'")
        print("Save to: data/silver/game_level_stats.csv")
        
        return None


if __name__ == "__main__":
    df = auto_fetch_nfl_stats()
