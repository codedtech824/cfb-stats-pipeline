"""
Automatically fetch NFL game-level stats from nflverse (2022-2025)
"""

import pandas as pd
from pathlib import Path


def fetch_nfl_stats():
    """Fetch game-level stats from nfl-data-py for 2022-2025."""
    
    try:
        import nfl_data_py as nfl
    except ImportError:
        print("Installing nfl-data-py package...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'nfl-data-py', '-q'])
        import nfl_data_py as nfl
    
    print("\n" + "="*70)
    print("FETCHING NFL GAME-LEVEL STATS (2022-2025)")
    print("="*70)
    print("Source: nfl-data-py (https://github.com/cooperdff/nfl_data_py)")
    print("This may take 2-5 minutes on first run...\n")
    
    all_stats = []
    
    for season in [2022, 2023, 2024, 2025]:
        print(f"Loading {season}...", end=" ", flush=True)
        try:
            # Load player stats for the season
            stats = nfl.import_seasonal_data(season)
            
            if stats is not None and len(stats) > 0:
                # Keep essential columns (exact names vary by dataset)
                relevant_cols = [col for col in ['season', 'player', 'team', 'fantasy_points'] if col in stats.columns]
                
                if len(relevant_cols) > 0:
                    game_stats = stats[relevant_cols].copy()
                    all_stats.append(game_stats)
                    print(f"✓ {len(game_stats):,} records")
                else:
                    print(f"✗ No matching columns. Available: {list(stats.columns[:5])}")
            else:
                print("✗ No data")
        
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
    
    if not all_stats:
        print("\n✗ Failed to fetch any data")
        return None
    
    # Combine all seasons
    df = pd.concat(all_stats, ignore_index=True)
    
    # Clean up
    df = df.dropna(subset=['player_name', 'opponent', 'fantasy_points'])
    df = df[df['fantasy_points'] > 0]  # Only games with actual points
    
    # Save
    output_path = Path('data/silver/game_level_stats.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print("\n" + "="*70)
    print("✓ DATA SAVED SUCCESSFULLY")
    print("="*70)
    print(f"File: {output_path}")
    print(f"Total Records: {len(df):,}")
    print(f"Players: {df['player_name'].nunique():,}")
    print(f"Teams: {df['team'].nunique()}")
    print(f"Opponents: {df['opponent'].nunique()}")
    print(f"Seasons: {sorted(df['season'].unique())}")
    print(f"Date Range: {df['game_date'].min()} to {df['game_date'].max()}")
    
    print("\n" + "-"*70)
    print("SAMPLE DATA:")
    print("-"*70)
    print(df.head(10).to_string())
    
    return df


if __name__ == "__main__":
    df = fetch_nfl_stats()
    
    if df is not None:
        print("\n✓ Ready to run matchup analysis!")
        print("   python nfl_matchup_analyzer.py")
