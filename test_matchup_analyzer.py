"""
Test the NFL Matchup Analyzer with sample data.
Demonstrates how the system identifies problem opponents (e.g., Packers).
"""

import pandas as pd
from nfl_matchup_analyzer import NFLMatchupAnalyzer


def create_sample_data():
    """Create sample game-level stats to demonstrate analysis."""
    
    # Sample data: Patrick Mahomes performance over 2022-2025 vs various teams
    data = [
        # 2022 Season
        {'season': 2022, 'week': 1, 'game_date': '2022-09-09', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'ARI', 'is_home': True, 'fantasy_points': 25.3},
        {'season': 2022, 'week': 2, 'game_date': '2022-09-15', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'LAC', 'is_home': False, 'fantasy_points': 22.1},
        {'season': 2022, 'week': 3, 'game_date': '2022-09-22', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'GB', 'is_home': True, 'fantasy_points': 8.5},  # STRUGGLES
        {'season': 2022, 'week': 4, 'game_date': '2022-09-29', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'TB', 'is_home': False, 'fantasy_points': 28.0},
        
        # 2023 Season
        {'season': 2023, 'week': 1, 'game_date': '2023-09-08', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'DET', 'is_home': False, 'fantasy_points': 24.2},
        {'season': 2023, 'week': 5, 'game_date': '2023-10-05', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'GB', 'is_home': False, 'fantasy_points': 9.2},  # STRUGGLES AGAIN
        {'season': 2023, 'week': 12, 'game_date': '2023-11-26', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'LAC', 'is_home': True, 'fantasy_points': 26.5},
        
        # 2024 Season
        {'season': 2024, 'week': 2, 'game_date': '2024-09-15', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'GB', 'is_home': True, 'fantasy_points': 7.8},  # STRUGGLES YET AGAIN
        {'season': 2024, 'week': 6, 'game_date': '2024-10-13', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'NO', 'is_home': False, 'fantasy_points': 29.4},
        {'season': 2024, 'week': 13, 'game_date': '2024-12-01', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'BUF', 'is_home': True, 'fantasy_points': 20.1},
        
        # 2025 Season
        {'season': 2025, 'week': 1, 'game_date': '2025-09-04', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'ARI', 'is_home': False, 'fantasy_points': 23.7},
        {'season': 2025, 'week': 9, 'game_date': '2025-11-02', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'GB', 'is_home': False, 'fantasy_points': 6.2},  # CONSISTENT PROBLEM
        {'season': 2025, 'week': 17, 'game_date': '2025-12-28', 'player_name': 'Patrick Mahomes', 
         'position': 'QB', 'team': 'KC', 'opponent': 'PIT', 'is_home': True, 'fantasy_points': 27.8},
        
        # Travis Kelce data (for comparison)
        {'season': 2022, 'week': 1, 'game_date': '2022-09-09', 'player_name': 'Travis Kelce', 
         'position': 'TE', 'team': 'KC', 'opponent': 'ARI', 'is_home': True, 'fantasy_points': 18.2},
        {'season': 2022, 'week': 3, 'game_date': '2022-09-22', 'player_name': 'Travis Kelce', 
         'position': 'TE', 'team': 'KC', 'opponent': 'GB', 'is_home': True, 'fantasy_points': 22.5},
        {'season': 2023, 'week': 5, 'game_date': '2023-10-05', 'player_name': 'Travis Kelce', 
         'position': 'TE', 'team': 'KC', 'opponent': 'GB', 'is_home': False, 'fantasy_points': 19.8},
        {'season': 2024, 'week': 2, 'game_date': '2024-09-15', 'player_name': 'Travis Kelce', 
         'position': 'TE', 'team': 'KC', 'opponent': 'GB', 'is_home': True, 'fantasy_points': 24.1},
    ]
    
    return pd.DataFrame(data)


def demo_matchup_analysis():
    """Demonstrate the matchup analyzer."""
    
    print("\n" + "="*70)
    print("NFL MATCHUP ANALYZER - SAMPLE DATA DEMO")
    print("="*70)
    
    analyzer = NFLMatchupAnalyzer(data_dir="data")
    
    # Create and save sample data
    sample_stats = create_sample_data()
    sample_stats.to_csv('data/silver/game_level_stats.csv', index=False)
    print("\n✓ Created sample game-level stats (2022-2025)")
    print(f"  {len(sample_stats)} game records for {sample_stats['player_name'].nunique()} players")
    
    # Run the full analysis
    report = analyzer.generate_full_report(game_stats_df=sample_stats)
    
    # Show individual player analysis
    print("\n\n" + "="*70)
    print("INDIVIDUAL PLAYER REPORTS")
    print("="*70)
    
    # Analyze Mahomes
    mahomes_report = analyzer.generate_player_report(
        'Patrick Mahomes',
        report['vs_opponent_stats'],
        report['schedule_2026']
    )
    
    # Show the problem: Packers
    print("\n" + "="*70)
    print("⚠️  KEY FINDING: PATRICK MAHOMES VS GREEN BAY PACKERS")
    print("="*70)
    mahomes_vs_gb = report['vs_opponent_stats'][
        (report['vs_opponent_stats']['player_name'] == 'Patrick Mahomes') &
        (report['vs_opponent_stats']['opponent'] == 'GB')
    ]
    
    if len(mahomes_vs_gb) > 0:
        row = mahomes_vs_gb.iloc[0]
        print(f"\nHistorical Performance (2022-2025):")
        print(f"  Games vs Packers: {int(row['games_played'])}")
        print(f"  Average Fantasy Points: {row['avg_points']:.1f}")
        print(f"  Range: {row['min_points']:.1f} - {row['max_points']:.1f}")
        print(f"  Std Dev: {row['std_dev']:.2f} (Consistency: {row['consistency']:.0f}%)")
        print(f"  Data Years: {row['seasons']}")
        print(f"\n  → Mahomes has CONSISTENTLY struggled against GB (all 4 years)")
        print(f"  → Average only {row['avg_points']:.1f} pts vs his typical 20+ pts")
        print(f"  → This is a SEVERE MATCHUP to avoid in 2026 drafting/fantasy planning")
    
    # Compare to Kelce vs Packers
    print("\n" + "="*70)
    print("COMPARISON: Travis Kelce vs Packers")
    print("="*70)
    kelce_vs_gb = report['vs_opponent_stats'][
        (report['vs_opponent_stats']['player_name'] == 'Travis Kelce') &
        (report['vs_opponent_stats']['opponent'] == 'GB')
    ]
    
    if len(kelce_vs_gb) > 0:
        row = kelce_vs_gb.iloc[0]
        print(f"\nHistorical Performance (2022-2025):")
        print(f"  Games vs Packers: {int(row['games_played'])}")
        print(f"  Average Fantasy Points: {row['avg_points']:.1f}")
        print(f"  → Kelce actually THRIVES vs GB ({row['avg_points']:.1f} pts)")
        print(f"  → Different matchup dynamics for different positions")


if __name__ == "__main__":
    demo_matchup_analysis()
