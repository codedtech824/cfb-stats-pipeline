"""
Integrated pipeline: predictions + opponent matchups + schedule context.
Produces final dataset with player team, opponent, and schedule-adjusted predictions.
"""

import pandas as pd
from pathlib import Path
from schedule_matcher import ScheduleMatcher
from opponent_adjuster import OpponentAdjuster


def run_complete_pipeline_with_opponents():
    """
    Full pipeline:
    1. Fetch 2026 schedule
    2. Load player predictions
    3. Create opponent matchups
    4. Calculate historical vs-opponent performance
    5. Apply adjustments to predictions
    6. Save enriched output
    """
    
    print("=" * 70)
    print("OPPONENT-INTEGRATED PREDICTION PIPELINE")
    print("=" * 70)
    
    # Initialize components
    matcher = ScheduleMatcher()
    adjuster = OpponentAdjuster()
    
    # ========================================
    # STAGE 1: Fetch 2026 Schedule
    # ========================================
    print("\n[1/5] Fetching 2026 NFL Schedule...")
    try:
        schedule = matcher.load_or_fetch_schedule(2026, force_refresh=False)
        if len(schedule) == 0:
            print("⚠️  Schedule is empty. Creating placeholder...")
            # Create minimal placeholder for testing
            schedule = pd.DataFrame({
                'game_id': [],
                'week': [],
                'home_team': [],
                'away_team': [],
                'game_date': [],
                'season': [2026]
            })
        else:
            print(f"✓ Loaded {len(schedule)} games")
            print(f"  Teams: {len(set(schedule['home_team'].unique()) | set(schedule['away_team'].unique()))} unique")
            print(f"  Weeks: {schedule['week'].min():.0f} - {schedule['week'].max():.0f}")
    except Exception as e:
        print(f"✗ Error fetching schedule: {e}")
        schedule = pd.DataFrame()
    
    # ========================================
    # STAGE 2: Load Predictions
    # ========================================
    print("\n[2/5] Loading Player Predictions...")
    predictions_path = Path("data/gold/final_predictions.parquet")
    
    if predictions_path.exists():
        predictions = pd.read_parquet(predictions_path)
        print(f"✓ Loaded {len(predictions)} player predictions")
        print(f"  Columns: {list(predictions.columns)}")
    else:
        print(f"✗ Predictions file not found: {predictions_path}")
        print("  Ensure you've run the prediction pipeline first.")
        return
    
    # ========================================
    # STAGE 3: Load Player Master Data
    # ========================================
    print("\n[3/5] Loading Player Master Data...")
    master_path = Path("data/silver/players_master.parquet")
    
    if master_path.exists():
        players_master = pd.read_parquet(master_path)
        print(f"✓ Loaded {len(players_master)} players from master")
        
        # Enrich predictions with team info
        predictions = adjuster.enrich_players_with_team(predictions, players_master)
        print(f"✓ Added team information")
    else:
        print(f"⚠️  Master file not found: {master_path}")
        print("  Some enrichment features may be limited.")
    
    # ========================================
    # STAGE 4: Create Opponent Matchups
    # ========================================
    print("\n[4/5] Creating Opponent Matchups...")
    try:
        matchups = matcher.create_opponent_matchups(predictions, schedule)
        if len(matchups) > 0:
            print(f"✓ Created {len(matchups)} player-opponent matchups")
            print(f"  Players with schedules: {matchups['player_name'].nunique()}")
            print(f"  Weeks covered: {matchups['week'].min():.0f} - {matchups['week'].max():.0f}")
            
            # Save matchups
            matchups_path = Path("data/silver/opponent_matchups.parquet")
            matchups.to_parquet(matchups_path, index=False)
            print(f"✓ Saved matchups to {matchups_path}")
        else:
            print("⚠️  No matchups created. This may be due to empty schedule or missing team info.")
            matchups = pd.DataFrame()
    except Exception as e:
        print(f"✗ Error creating matchups: {e}")
        matchups = pd.DataFrame()
    
    # ========================================
    # STAGE 5: Add Schedule Context
    # ========================================
    print("\n[5/5] Adding Schedule Context to Predictions...")
    try:
        enriched = adjuster.add_schedule_context(predictions, matchups, schedule)
        print(f"✓ Enriched predictions with schedule context")
        
        # Display sample
        sample_display_cols = [
            'player_name', 
            'position',
            'current_team',
            'opponent_week1',
            'is_home_week1'
        ]
        available_cols = [c for c in sample_display_cols if c in enriched.columns]
        
        if available_cols:
            print("\n  Sample enriched data:")
            print(enriched[available_cols].head(10).to_string(index=False))
        
        # Save enriched output
        adjuster.save_enriched_projections(enriched)
        
    except Exception as e:
        print(f"✗ Error enriching predictions: {e}")
        enriched = predictions
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"\n📊 Final Output Columns ({len(enriched.columns)} total):")
    for i, col in enumerate(enriched.columns, 1):
        print(f"   {i:2d}. {col}")
    
    print(f"\n📁 Output Files:")
    print(f"   • Predictions:        data/gold/predictions_with_opponent.parquet")
    print(f"   • Matchups:           data/silver/opponent_matchups.parquet")
    print(f"   • Schedule (cached):  data/bronze/nfl_schedule_2026.json")
    
    return {
        'predictions': enriched,
        'matchups': matchups,
        'schedule': schedule,
        'players_master': players_master if 'players_master' in locals() else None
    }


if __name__ == "__main__":
    results = run_complete_pipeline_with_opponents()
    
    print("\n" + "=" * 70)
    print("USAGE EXAMPLES")
    print("=" * 70)
    print("""
# Load the enriched predictions in your code:
import pandas as pd

predictions = pd.read_parquet('data/gold/predictions_with_opponent.parquet')

# Filter to specific team:
chiefs_players = predictions[predictions['current_team'] == 'KC']

# See week 1 opponents:
print(predictions[['player_name', 'opponent_week1', 'is_home_week1']])

# See full schedule:
print(predictions['schedule_2026'].iloc[0])

# Filter to home games:
home_games = predictions[predictions['is_home_week1'] == True]
    """)
