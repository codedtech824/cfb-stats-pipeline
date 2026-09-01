"""
NFL Matchup Analyzer - Identifies standout games and problem opponents.
Works with game-level NFL data (2022-2025) to predict 2026 matchup difficulty.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from schedule_matcher import ScheduleMatcher


class NFLMatchupAnalyzer:
    """
    Analyze NFL player performance vs opponents using game-level stats.
    Identifies which opponents give players problems and flags 2026 matchups.
    """
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.silver_dir = self.data_dir / "silver"
        self.bronze_dir = self.data_dir / "bronze"
        self.matcher = ScheduleMatcher(data_dir=data_dir)
        
    def create_game_level_template(self):
        """
        Create a template CSV for game-level player stats (2022-2025).
        Users should populate this with their data source.
        
        Expected columns:
        - season (2022-2025)
        - week
        - game_date
        - player_name
        - position
        - team (player's team)
        - opponent (team they played against)
        - is_home (True/False)
        - fantasy_points (calculated based on stats)
        - passing_yds, passing_td, interceptions (QB)
        - rushing_yds, rushing_td (RB/WR)
        - receiving_yds, receptions, receiving_td (WR/TE)
        - etc.
        """
        template = pd.DataFrame({
            'season': [2022, 2022, 2022],
            'week': [1, 1, 2],
            'game_date': ['2022-09-09', '2022-09-09', '2022-09-15'],
            'player_name': ['Patrick Mahomes', 'Travis Kelce', 'Patrick Mahomes'],
            'position': ['QB', 'TE', 'QB'],
            'team': ['KC', 'KC', 'KC'],
            'opponent': ['ARI', 'ARI', 'LAC'],
            'is_home': [True, True, False],
            'fantasy_points': [25.3, 12.5, 31.2],
            'passing_yds': [250, np.nan, 280],
            'passing_td': [2, np.nan, 2],
            'interceptions': [0, np.nan, 1],
            'rushing_yds': [np.nan, np.nan, np.nan],
            'receiving_yds': [np.nan, 85, np.nan],
            'receptions': [np.nan, 7, np.nan],
        })
        
        template_path = self.silver_dir / "game_level_stats_template.csv"
        template.to_csv(template_path, index=False)
        print(f"✓ Created template: {template_path}")
        print("\nTemplate columns:")
        print(template.dtypes)
        return template
    
    def load_game_level_stats(self):
        """Load game-level player stats from silver layer."""
        stats_file = self.silver_dir / "game_level_stats.csv"
        
        if not stats_file.exists():
            print(f"\n⚠ {stats_file} not found")
            print("Creating template for you to populate with 2022-2025 NFL data...")
            self.create_game_level_template()
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(stats_file) if stats_file.suffix == '.parquet' else pd.read_csv(stats_file)
            print(f"✓ Loaded {len(df)} game records from {stats_file}")
            return df
        except Exception as e:
            print(f"Error loading stats: {e}")
            return pd.DataFrame()
    
    def calculate_vs_opponent_stats(self, game_stats_df):
        """
        Calculate performance vs each opponent using historical game data.
        
        Args:
            game_stats_df: DataFrame with columns:
                - player_name, team, opponent, season, week, fantasy_points, is_home
        
        Returns:
            DataFrame with per-player, per-opponent statistics
        """
        if len(game_stats_df) == 0:
            return pd.DataFrame()
        
        # Group by player and opponent
        vs_opponent = game_stats_df.groupby(['player_name', 'opponent']).agg({
            'fantasy_points': ['mean', 'count', 'min', 'max', 'std'],
            'season': lambda x: f"{x.min()}-{x.max()}",
            'is_home': lambda x: (x.sum() / len(x)) * 100  # % home games
        }).reset_index()
        
        vs_opponent.columns = ['player_name', 'opponent', 'avg_points', 'games_played', 
                              'min_points', 'max_points', 'std_dev', 'seasons', 'pct_home']
        
        # Mark consistency
        vs_opponent['consistency'] = 100 - vs_opponent['std_dev'].fillna(0).clip(0, 100)
        
        return vs_opponent.sort_values('avg_points')
    
    def identify_problem_opponents(self, vs_opponent_df, threshold_percentile=25):
        """
        Identify opponents where player historically underperforms.
        Uses percentile-based approach to find relative problem matchups.
        
        Args:
            vs_opponent_df: Output from calculate_vs_opponent_stats()
            threshold_percentile: Players with performance in bottom X% vs opponent
        
        Returns:
            DataFrame of problem matchups with severity ratings
        """
        if len(vs_opponent_df) == 0:
            return pd.DataFrame()
        
        # For each player, find opponents in bottom quartile
        problem_matchups = []
        
        for player in vs_opponent_df['player_name'].unique():
            player_data = vs_opponent_df[vs_opponent_df['player_name'] == player]
            
            if len(player_data) < 2:
                continue
            
            # Calculate percentile for this player
            threshold = player_data['avg_points'].quantile(threshold_percentile / 100)
            
            problems = player_data[player_data['avg_points'] <= threshold].copy()
            
            for _, row in problems.iterrows():
                problem_matchups.append({
                    'player_name': row['player_name'],
                    'opponent': row['opponent'],
                    'avg_points': row['avg_points'],
                    'games_played': row['games_played'],
                    'min_points': row['min_points'],
                    'max_points': row['max_points'],
                    'std_dev': row['std_dev'],
                    'consistency': row['consistency'],
                    'seasons': row['seasons'],
                    'pct_home': row['pct_home'],
                    'severity': self._classify_severity(row['avg_points'], row['consistency'])
                })
        
        result = pd.DataFrame(problem_matchups)
        return result.sort_values(['player_name', 'avg_points'])
    
    def _classify_severity(self, avg_points, consistency):
        """Classify how severe a problem matchup is."""
        if consistency < 30:  # Highly inconsistent
            return "ERRATIC (🔴) - Unpredictable"
        elif avg_points < 5 and consistency > 70:
            return "SEVERE (🔴) - Consistently struggles"
        elif avg_points < 10:
            return "MODERATE (⚠️) - Underperforms"
        else:
            return "MINOR (🟡) - Slight disadvantage"
    
    def match_2026_against_history(self, vs_opponent_df, schedule_df):
        """
        Match 2026 schedule against historical performance.
        Returns schedule with expected points based on opponent matchup history.
        
        Args:
            vs_opponent_df: Historical performance vs opponents
            schedule_df: 2026 schedule from matcher
        
        Returns:
            Schedule with expected_points and matchup_quality columns
        """
        if len(schedule_df) == 0 or len(vs_opponent_df) == 0:
            return schedule_df
        
        # Note: schedule_df needs player info - this requires integration with player roster
        # For now, show the structure
        result = schedule_df.merge(
            vs_opponent_df[['opponent', 'avg_points', 'consistency', 'games_played']],
            left_on='away_team',
            right_on='opponent',
            how='left'
        )
        
        result.rename(columns={'avg_points': 'expected_points_by_opponent'}, inplace=True)
        
        return result
    
    def generate_player_report(self, player_name, vs_opponent_df, schedule_df):
        """
        Generate detailed report for one player showing:
        - Problem opponents and when they play in 2026
        - Best matchups in 2026
        - Bye week analysis
        
        Args:
            player_name: Name of player
            vs_opponent_df: Historical vs opponent stats
            schedule_df: 2026 schedule
        
        Returns:
            Dictionary with analysis
        """
        print("\n" + "="*70)
        print(f"2026 MATCHUP ANALYSIS: {player_name}")
        print("="*70)
        
        # Get player's opponent stats
        player_opp = vs_opponent_df[vs_opponent_df['player_name'] == player_name].copy()
        
        if len(player_opp) == 0:
            print(f"No historical data found for {player_name}")
            return {}
        
        # Sort by performance
        player_opp_sorted = player_opp.sort_values('avg_points')
        
        print("\n📊 CAREER PERFORMANCE VS OPPONENTS")
        print("-" * 70)
        print(f"{'Opponent':<10} {'Avg Pts':<10} {'Games':<8} {'Range':<15} {'Consistency':<12}")
        print("-" * 70)
        
        for _, row in player_opp_sorted.iterrows():
            range_str = f"{row['min_points']:.1f}-{row['max_points']:.1f}"
            print(f"{row['opponent']:<10} {row['avg_points']:>7.1f}    {row['games_played']:>6.0f}   "
                  f"{range_str:<15} {row['consistency']:>10.0f}%")
        
        # Identify problem opponents
        print("\n\n🔴 PROBLEM OPPONENTS (Historical struggles)")
        print("-" * 70)
        problems = player_opp_sorted[player_opp_sorted['avg_points'] < player_opp['avg_points'].median()]
        
        for _, row in problems.iterrows():
            print(f"\n{row['opponent'].upper()} - {self._classify_severity(row['avg_points'], row['consistency'])}")
            print(f"  Avg Points: {row['avg_points']:.1f} (Range: {row['min_points']:.1f}-{row['max_points']:.1f})")
            print(f"  Games Played: {row['games_played']:.0f}")
            print(f"  Consistency: {row['consistency']:.0f}% {'(stable struggles)' if row['consistency'] > 70 else '(unpredictable)'}")
            print(f"  Data: {row['seasons']}")
        
        # Best matchups
        print("\n\n⭐ BEST MATCHUPS (Historical dominance)")
        print("-" * 70)
        best = player_opp_sorted.tail(3)
        
        for _, row in best.iterrows():
            print(f"\n{row['opponent'].upper()}")
            print(f"  Avg Points: {row['avg_points']:.1f} (Range: {row['min_points']:.1f}-{row['max_points']:.1f})")
            print(f"  Games Played: {row['games_played']:.0f}")
        
        return {
            'player_name': player_name,
            'all_opponents': player_opp,
            'problem_opponents': problems,
            'best_opponents': best
        }
    
    def generate_full_report(self, game_stats_df=None, schedule_df=None):
        """Generate comprehensive analysis across all players."""
        
        if game_stats_df is None or len(game_stats_df) == 0:
            game_stats_df = self.load_game_level_stats()
        
        if len(game_stats_df) == 0:
            print("No game-level stats available. Populate game_level_stats.csv first.")
            return {}
        
        if schedule_df is None or len(schedule_df) == 0:
            schedule_df = self.matcher.load_or_fetch_schedule(2026)
        
        print("\n" + "="*70)
        print("NFL 2026 MATCHUP ANALYSIS")
        print("="*70)
        
        # Calculate vs opponent stats
        vs_opp = self.calculate_vs_opponent_stats(game_stats_df)
        
        print(f"\n✓ Analyzed {vs_opp['player_name'].nunique()} players")
        print(f"✓ {len(vs_opp)} total opponent matchups in history")
        
        # Find problem opponents
        problem_opps = self.identify_problem_opponents(vs_opp)
        
        if len(problem_opps) > 0:
            print(f"\n🔴 IDENTIFIED PROBLEM MATCHUPS ({len(problem_opps)} total)")
            print("-" * 70)
            
            # Show worst matchups
            worst = problem_opps.nsmallest(10, 'avg_points')
            for _, row in worst.iterrows():
                print(f"\n{row['player_name']} vs {row['opponent'].upper()}")
                print(f"  Avg: {row['avg_points']:.1f}pts | Severity: {row['severity']}")
        
        # Save results
        vs_opp.to_csv(self.silver_dir / 'vs_opponent_history.csv', index=False)
        if len(problem_opps) > 0:
            problem_opps.to_csv(self.silver_dir / 'problem_matchups.csv', index=False)
        
        print(f"\n✓ Results saved to {self.silver_dir}")
        
        return {
            'vs_opponent_stats': vs_opp,
            'problem_matchups': problem_opps,
            'schedule_2026': schedule_df
        }


def main():
    """Run the full analysis."""
    analyzer = NFLMatchupAnalyzer(data_dir="data")
    report = analyzer.generate_full_report()


if __name__ == "__main__":
    main()
