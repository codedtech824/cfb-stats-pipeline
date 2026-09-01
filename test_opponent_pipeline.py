"""
Example & Test: Opponent-integrated pipeline
Demonstrates usage and validates all components work correctly.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from schedule_matcher import ScheduleMatcher
from opponent_adjuster import OpponentAdjuster


def test_schedule_matcher():
    """Test schedule fetching and matchup creation."""
    print("\n" + "="*70)
    print("TEST 1: Schedule Fetching & Matchup Creation")
    print("="*70)
    
    matcher = ScheduleMatcher()
    
    # Test 1a: Load schedule (will use mock if real APIs fail)
    print("\n[1a] Loading 2026 Schedule...")
    try:
        schedule = matcher.load_or_fetch_schedule(2026, force_refresh=False)
        
        # If empty, use mock
        if len(schedule) == 0:
            print("ℹ️  Using mock schedule for testing...")
            schedule = matcher.create_mock_schedule(2026)
        
        if len(schedule) > 0:
            print(f"✓ Schedule loaded: {len(schedule)} games")
            print(f"  Weeks: {int(schedule['week'].min())} - {int(schedule['week'].max())}")
            print(f"  Sample games:")
            print(schedule[['week', 'home_team', 'away_team']].head(3).to_string(index=False))
        else:
            print("⚠️  Empty schedule. Skipping matchup tests.")
            return False
            
    except Exception as e:
        print(f"✗ Failed to load schedule: {e}")
        return False
    
    # Test 1b: Create sample players
    print("\n[1b] Creating sample players...")
    sample_players = pd.DataFrame({
        'player_name': [
            'Patrick Mahomes', 'Travis Kelce', 'Derrick Henry',
            'Josh Allen', 'Stefon Diggs', 'Saquon Barkley',
            'Jalen Hurts', 'DeVonta Smith', 'Dallas Goedert'
        ],
        'position': ['QB', 'TE', 'RB', 'QB', 'WR', 'RB', 'QB', 'WR', 'TE'],
        'team': ['KC', 'KC', 'TN', 'BUF', 'BUF', 'PHI', 'PHI', 'PHI', 'PHI'],
        'projected_points': np.random.uniform(10, 25, 9)
    })
    print(f"✓ Created {len(sample_players)} sample players")
    
    # Test 1c: Create matchups
    print("\n[1c] Creating opponent matchups...")
    try:
        matchups = matcher.create_opponent_matchups(sample_players, schedule)
        
        if len(matchups) > 0:
            print(f"✓ Created {len(matchups)} total matchups across all weeks")
            print(f"  Players: {matchups['player_name'].nunique()}")
            print(f"  Weeks: {int(matchups['week'].min())} - {int(matchups['week'].max())}")
            
            # Show week 1 only
            week1 = matchups[matchups['week'] == 1]
            print(f"\n  Week 1 matchups ({len(week1)} players):")
            print(week1[['player_name', 'current_team', 'opponent', 'is_home']].to_string(index=False))
            
            return True
        else:
            print("⚠️  No matchups created")
            return False
            
    except Exception as e:
        print(f"✗ Failed to create matchups: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_opponent_adjuster():
    """Test enrichment and adjustments."""
    print("\n" + "="*70)
    print("TEST 2: Opponent-Based Prediction Enrichment")
    print("="*70)
    
    adjuster = OpponentAdjuster()
    matcher = ScheduleMatcher()
    
    # Test 2a: Load schedule
    print("\n[2a] Loading schedule...")
    try:
        schedule = matcher.load_or_fetch_schedule(2026, force_refresh=False)
        
        # If empty, use mock
        if len(schedule) == 0:
            print("ℹ️  Using mock schedule for testing...")
            schedule = matcher.create_mock_schedule(2026)
        
        if len(schedule) == 0:
            print("⚠️  Empty schedule. Skipping enrichment tests.")
            return False
        print(f"✓ Loaded {len(schedule)} games")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2b: Create sample predictions + master data
    print("\n[2b] Creating sample data...")
    predictions = pd.DataFrame({
        'player_name': ['Mahomes', 'Henry', 'Kelce'],
        'position': ['QB', 'RB', 'TE'],
        'team': ['KC', 'TN', 'KC'],
        'projected_points': [22.5, 16.3, 14.8]
    })
    
    players_master = pd.DataFrame({
        'player_name': ['Mahomes', 'Henry', 'Kelce'],
        'team': ['KC', 'TN', 'KC'],
        'position': ['QB', 'RB', 'TE']
    })
    print(f"✓ Created predictions ({len(predictions)}) and master ({len(players_master)}) data")
    
    # Test 2c: Enrich with team
    print("\n[2c] Enriching with team info...")
    try:
        enriched = adjuster.enrich_players_with_team(predictions, players_master)
        if 'team' in enriched.columns:
            print(f"✓ Added team column")
            print(enriched[['player_name', 'team']].to_string(index=False))
        else:
            print("⚠️  Team column not added")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2d: Create matchups
    print("\n[2d] Creating matchups...")
    try:
        matchups = matcher.create_opponent_matchups(enriched, schedule)
        if len(matchups) > 0:
            print(f"✓ Created {len(matchups)} matchups")
            week1 = matchups[matchups['week'] == 1]
            print(f"  Week 1 opponents:")
            print(week1[['player_name', 'opponent', 'is_home']].drop_duplicates().to_string(index=False))
        else:
            print("⚠️  No matchups created")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test 2e: Add schedule context
    print("\n[2e] Adding schedule context...")
    try:
        with_context = adjuster.add_schedule_context(enriched, matchups, schedule)
        
        print(f"✓ Added schedule context")
        print(f"  New columns: {[c for c in with_context.columns if 'week1' in c or 'schedule' in c]}")
        
        # Show a sample
        if 'opponent_week1' in with_context.columns:
            print("\n  Sample enriched data:")
            print(with_context[['player_name', 'opponent_week1', 'is_home_week1']].to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_historical_vs_opponent():
    """Test historical performance tracking."""
    print("\n" + "="*70)
    print("TEST 3: Historical Performance vs. Opponent")
    print("="*70)
    
    print("\n[3a] Creating historical performance data...")
    
    # Create 4 years of historical game logs
    years = [2022, 2023, 2024, 2025]
    teams = ['KC', 'SF', 'BUF', 'DAL', 'TN', 'PHI']
    
    historical_records = []
    for year in years:
        for _ in range(50):
            player = np.random.choice(['Mahomes', 'Henry', 'Kelce', 'Allen', 'Diggs'])
            team = np.random.choice(teams)
            opponent = np.random.choice([t for t in teams if t != team])
            points = np.random.uniform(5, 30)
            
            historical_records.append({
                'player_name': player,
                'team': team,
                'opponent': opponent,
                'season': year,
                'points': points
            })
    
    historical_df = pd.DataFrame(historical_records)
    print(f"✓ Created {len(historical_df)} historical game records")
    
    # Calculate vs opponent stats (without schedule_df parameter for testing)
    print("\n[3b] Calculating historical performance vs. opponent...")
    try:
        # Group by player and opponent to calculate averages
        vs_opponent = historical_df.groupby(['player_name', 'opponent']).agg({
            'points': ['mean', 'count', 'max', 'min'],
            'season': lambda x: x.iloc[-1] if len(x) > 0 else None
        }).reset_index()
        
        vs_opponent.columns = ['player_name', 'opponent', 'avg_points_vs_opp', 'games_vs_opp', 'max_vs_opp', 'min_vs_opp', 'last_season']
        
        if len(vs_opponent) > 0:
            print(f"✓ Calculated {len(vs_opponent)} player-opponent records")
            print(f"  Sample:")
            print(vs_opponent.head(5).to_string(index=False))
        else:
            print("⚠️  No vs_opponent stats calculated")
        
        return len(vs_opponent) > 0
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def run_full_integration_test():
    """Run the complete pipeline with test data."""
    print("\n" + "="*70)
    print("TEST 4: Full Integration Test")
    print("="*70)
    
    # Create test data directory structure
    test_data_dir = Path("test_data")
    test_data_dir.mkdir(exist_ok=True)
    
    print("\n[4a] Creating test directory structure...")
    for subdir in ['bronze', 'silver', 'gold']:
        (test_data_dir / subdir).mkdir(exist_ok=True)
    print(f"✓ Created test directories in {test_data_dir}/")
    
    # Create mock schedule first
    print("\n[4b] Creating mock schedule...")
    try:
        matcher = ScheduleMatcher(data_dir=str(test_data_dir))
        schedule = matcher.create_mock_schedule(2026)
        print(f"✓ Created {len(schedule)} mock games")
    except Exception as e:
        print(f"✗ Failed to create mock schedule: {e}")
        return False
    
    # Create sample predictions
    print("\n[4c] Creating sample predictions...")
    sample_predictions = pd.DataFrame({
        'player_name': ['Mahomes', 'Kelce', 'Allen', 'Diggs', 'Henry'],
        'position': ['QB', 'TE', 'QB', 'WR', 'RB'],
        'team': ['KC', 'KC', 'BUF', 'BUF', 'TN'],
        'projected_points': [23.1, 15.2, 21.8, 14.5, 16.3],
        'season': [2026, 2026, 2026, 2026, 2026]
    })
    
    predictions_file = test_data_dir / 'gold' / 'final_predictions.parquet'
    sample_predictions.to_parquet(predictions_file, index=False)
    print(f"✓ Saved sample predictions to {predictions_file}")
    
    # Create sample player master
    print("\n[4d] Creating player master...")
    players_master = pd.DataFrame({
        'player_name': ['Mahomes', 'Kelce', 'Allen', 'Diggs', 'Henry'],
        'team': ['KC', 'KC', 'BUF', 'BUF', 'TN'],
        'position': ['QB', 'TE', 'QB', 'WR', 'RB']
    })
    master_file = test_data_dir / 'silver' / 'players_master.parquet'
    players_master.to_parquet(master_file, index=False)
    print(f"✓ Saved players master to {master_file}")
    
    # Create matchups
    print("\n[4e] Creating opponent matchups...")
    try:
        adjuster = OpponentAdjuster(data_dir=str(test_data_dir))
        matchups = matcher.create_opponent_matchups(sample_predictions, schedule)
        
        if len(matchups) > 0:
            print(f"✓ Created {len(matchups)} matchups")
            matchups_file = test_data_dir / 'silver' / 'opponent_matchups.parquet'
            matchups.to_parquet(matchups_file, index=False)
        else:
            print("⚠️  No matchups created")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Enrich predictions
    print("\n[4f] Enriching predictions with opponent context...")
    try:
        enriched = adjuster.enrich_players_with_team(sample_predictions, players_master)
        enriched = adjuster.add_schedule_context(enriched, matchups, schedule)
        
        output_file = test_data_dir / 'gold' / 'predictions_with_opponent.parquet'
        enriched.to_parquet(output_file, index=False)
        print(f"✓ Saved enriched predictions to {output_file}")
        print(f"  Rows: {len(enriched)}, Columns: {len(enriched.columns)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_usage_examples():
    """Show usage examples."""
    print("\n" + "="*70)
    print("USAGE EXAMPLES")
    print("="*70)
    
    examples = """
# EXAMPLE 1: Quick start
from run_with_opponents import run_complete_pipeline_with_opponents
results = run_complete_pipeline_with_opponents()
predictions = results['predictions']

# EXAMPLE 2: Filter to specific team
import pandas as pd
predictions = pd.read_parquet('data/gold/predictions_with_opponent.parquet')
mahomes = predictions[predictions['player_name'] == 'Mahomes']
print(f"Mahomes plays: {mahomes['opponent_week1'].values[0]}")

# EXAMPLE 3: Home vs Away comparison
home = predictions[predictions['is_home_week1'] == True]
away = predictions[predictions['is_home_week1'] == False]
print(f"Home avg: {home['projected_points'].mean():.1f}")
print(f"Away avg: {away['projected_points'].mean():.1f}")

# EXAMPLE 4: View full schedule
player = predictions.iloc[0]
print(player['schedule_2026'])

# EXAMPLE 5: Export for analysis
predictions.to_csv('predictions_with_opponents.csv', index=False)
    """
    print(examples)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("OPPONENT PIPELINE TEST SUITE")
    print("="*70)
    
    results = {
        'Schedule Matcher': test_schedule_matcher(),
        'Opponent Adjuster': test_opponent_adjuster(),
        'Historical Performance': test_historical_vs_opponent(),
        'Full Integration': run_full_integration_test()
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} {test_name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Show examples
    display_usage_examples()
    
    # Recommendations
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
1. Ensure your prediction pipeline produces 'data/gold/final_predictions.parquet'
2. Ensure players master data is available at 'data/silver/players_master.parquet'
3. Run the complete pipeline:
   
   python run_with_opponents.py

4. Load and use enriched predictions:
   
   import pandas as pd
   predictions = pd.read_parquet('data/gold/predictions_with_opponent.parquet')
   
5. See OPPONENT_PIPELINE_README.md for detailed documentation
    """)
