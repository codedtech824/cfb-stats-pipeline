"""
Matchup Analyzer - Identifies standout games and difficult opponents.
Uses historical performance (2022-2025) against opponents to flag games in 2026 schedule.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from schedule_matcher import ScheduleMatcher


class MatchupAnalyzer:
    """Analyze player performance vs opponents and flag standout 2026 matchups."""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.silver_dir = self.data_dir / "silver"
        self.matcher = ScheduleMatcher(data_dir=data_dir)
        
    def load_historical_stats(self):
        """Load historical player stats from silver layer."""
        stats_file = self.silver_dir / "player_stats_wide.parquet"
        
        if not stats_file.exists():
            print(f"Warning: {stats_file} not found")
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(stats_file)
            print(f"✓ Loaded {len(df)} player-season records from {stats_file}")
            return df
        except Exception as e:
            print(f"Error loading stats: {e}")
            return pd.DataFrame()
    
    def calculate_vs_opponent_performance(self, player_stats_df, seasons=[2022, 2023, 2024, 2025]):
        """
        Calculate average fantasy points per player vs each opponent.
        
        Args:
            player_stats_df: DataFrame with columns: player_name, team, opponent, season, points (or similar)
            seasons: Historical seasons to analyze
        
        Returns:
            DataFrame: player_name, opponent, avg_points, games_played, min_points, max_points, consistency
        """
        if len(player_stats_df) == 0:
            print("No player stats available")
            return pd.DataFrame()
        
        # Filter to historical seasons
        historical = player_stats_df[
            player_stats_df['season'].isin(seasons)
        ].copy() if 'season' in player_stats_df.columns else player_stats_df.copy()
        
        if len(historical) == 0:
            print(f"No data found for seasons {seasons}")
            return pd.DataFrame()
        
        # Check what columns we have
        print(f"Available columns: {list(historical.columns)}")
        
        # Try to identify opponent and points columns
        opponent_col = None
        for col in ['opponent', 'opp', 'opp_team', 'against']:
            if col in historical.columns:
                opponent_col = col
                break
        
        if opponent_col is None:
            print("Warning: Could not find opponent column. Available: " + ", ".join(historical.columns))
            return pd.DataFrame()
        
        # Group by player and opponent
        vs_opp = historical.groupby(['player_name', opponent_col]).agg({
            'points': ['mean', 'count', 'min', 'max', 'std'],
            'season': lambda x: list(x.unique()) if 'season' in historical.columns else []
        }).reset_index()
        
        vs_opp.columns = ['player_name', 'opponent', 'avg_points', 'games_played', 'min_points', 'max_points', 'std_dev', 'seasons']
        
        # Calculate consistency score (lower std = more consistent)
        vs_opp['consistency'] = 100 - vs_opp['std_dev'].fillna(0).clip(0, 100)
        
        return vs_opp
    
    def flag_standout_matchups(self, player_schedule_df, vs_opponent_stats_df, top_n=3):
        """
        Flag each player's standout matchups (best and worst) for 2026.
        
        Args:
            player_schedule_df: DataFrame from matcher.create_opponent_matchups()
                                Columns: player_name, position, current_team, week, opponent, game_date, is_home
            vs_opponent_stats_df: DataFrame from calculate_vs_opponent_performance()
                                  Columns: player_name, opponent, avg_points, games_played, ...
            top_n: Number of best/worst matchups to identify
        
        Returns:
            DataFrame with standout matchups flagged
        """
        if len(player_schedule_df) == 0 or len(vs_opponent_stats_df) == 0:
            print("Missing schedule or stats data")
            return pd.DataFrame()
        
        # Merge schedule with historical performance
        matchups = player_schedule_df.merge(
            vs_opponent_stats_df,
            left_on=['player_name', 'opponent'],
            right_on=['player_name', 'opponent'],
            how='left'
        )
        
        # Fill NaN for players with no historical data vs opponent
        matchups['avg_points'] = matchups['avg_points'].fillna(0)
        matchups['games_played'] = matchups['games_played'].fillna(0)
        matchups['consistency'] = matchups['consistency'].fillna(50)  # Neutral default
        
        # Classify matchups
        matchups['matchup_quality'] = matchups['avg_points'].apply(self._classify_matchup)
        
        # Add player-level summary
        player_best = matchups.nsmallest(top_n, 'avg_points')[['player_name', 'opponent', 'avg_points']]
        player_worst = matchups.nlargest(top_n, 'avg_points')[['player_name', 'opponent', 'avg_points']]
        
        return matchups.sort_values(['player_name', 'week'])
    
    def _classify_matchup(self, avg_points):
        """Classify matchup difficulty based on historical performance."""
        if avg_points >= 20:
            return "Elite Matchup ⭐⭐⭐"
        elif avg_points >= 15:
            return "Good Matchup ⭐⭐"
        elif avg_points >= 10:
            return "Neutral Matchup ⭐"
        elif avg_points >= 5:
            return "Tough Matchup ⚠️"
        else:
            return "Nightmare Matchup 🔴"
    
    def identify_problem_teams(self, vs_opponent_stats_df, problem_threshold=10):
        """
        Identify teams that a player consistently struggles against.
        
        Args:
            vs_opponent_stats_df: Historical performance vs opponents
            problem_threshold: Avg points below this = problem opponent
        
        Returns:
            DataFrame: player_name, opponent, avg_points, games_played, consistency, problem_level
        """
        problem_teams = vs_opponent_stats_df[
            (vs_opponent_stats_df['avg_points'] < problem_threshold) &
            (vs_opponent_stats_df['games_played'] >= 2)  # Need at least 2 games
        ].copy()
        
        problem_teams['problem_level'] = problem_teams['avg_points'].apply(
            lambda x: "SEVERE" if x < 5 else "MODERATE" if x < 10 else "MINOR"
        )
        
        return problem_teams.sort_values(['player_name', 'avg_points'])
    
    def create_2026_matchup_report(self, player_list=None, top_n=5):
        """
        Generate full 2026 matchup analysis report.
        
        Args:
            player_list: List of player names to analyze (None = all players)
            top_n: Number of best/worst matchups to highlight per player
        
        Returns:
            Dictionary with analysis results
        """
        print("\n" + "="*70)
        print("2026 MATCHUP ANALYSIS REPORT")
        print("="*70)
        
        # Load data
        stats = self.load_historical_stats()
        schedule = self.matcher.load_or_fetch_schedule(season=2026)
        
        if len(stats) == 0 or len(schedule) == 0:
            print("Insufficient data for analysis")
            return {}
        
        # Filter to players of interest
        if player_list:
            stats = stats[stats['player_name'].isin(player_list)]
        
        # Calculate performance vs opponents
        print("\nCalculating historical performance vs opponents...")
        vs_opp = self.calculate_vs_opponent_performance(stats)
        
        if len(vs_opp) == 0:
            print("Could not calculate opponent performance")
            return {}
        
        # Create sample player schedule (need more context on your data structure)
        # For now, show what data we have
        print(f"\n✓ Analyzed {vs_opp['player_name'].nunique()} players")
        print(f"✓ Found historical data vs {vs_opp['opponent'].nunique()} opponents")
        
        # Identify problem teams
        print("\n" + "-"*70)
        print("IDENTIFIED PROBLEM OPPONENTS (avg < 10 points)")
        print("-"*70)
        
        problem_teams = self.identify_problem_teams(vs_opp)
        if len(problem_teams) > 0:
            for idx, row in problem_teams.head(20).iterrows():
                print(f"\n{row['player_name']} vs {row['opponent']}")
                print(f"  History: {row['games_played']:.0f} games")
                print(f"  Avg Points: {row['avg_points']:.1f}")
                print(f"  Range: {row['min_points']:.1f} - {row['max_points']:.1f}")
                print(f"  Consistency: {row['consistency']:.0f}% (σ={row['std_dev']:.2f})")
                print(f"  Problem Level: {row['problem_level']}")
        else:
            print("No major problem opponents found in historical data")
        
        # Best matchups
        print("\n" + "-"*70)
        print("BEST MATCHUPS (avg > 15 points)")
        print("-"*70)
        
        best_matchups = vs_opp[vs_opp['avg_points'] >= 15].sort_values('avg_points', ascending=False)
        if len(best_matchups) > 0:
            for idx, row in best_matchups.head(15).iterrows():
                print(f"\n{row['player_name']} vs {row['opponent']} ⭐⭐⭐")
                print(f"  History: {row['games_played']:.0f} games averaging {row['avg_points']:.1f} pts")
                print(f"  Range: {row['min_points']:.1f} - {row['max_points']:.1f}")
        
        return {
            'vs_opponent_stats': vs_opp,
            'problem_opponents': problem_teams,
            'best_matchups': best_matchups,
            'schedule': schedule
        }


def example_report():
    """Generate example matchup report."""
    analyzer = MatchupAnalyzer(data_dir="data")
    
    # You can specify players or leave None for all
    # For now, we'll analyze all available players
    report = analyzer.create_2026_matchup_report(player_list=None, top_n=5)
    
    if report:
        # Save results
        if len(report['problem_opponents']) > 0:
            report['problem_opponents'].to_csv(
                'data/silver/problem_opponents.csv',
                index=False
            )
            print("\n✓ Problem opponents saved to data/silver/problem_opponents.csv")
        
        if len(report['best_matchups']) > 0:
            report['best_matchups'].to_csv(
                'data/silver/best_matchups.csv',
                index=False
            )
            print("✓ Best matchups saved to data/silver/best_matchups.csv")


if __name__ == "__main__":
    example_report()
