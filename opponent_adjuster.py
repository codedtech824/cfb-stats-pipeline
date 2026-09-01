"""
Integrate opponent matchups and schedule into player predictions.
Adds team context and opponent-specific adjustments to projections.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


class OpponentAdjuster:
    """Adjust player projections based on opponent and historical performance."""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.silver_dir = self.data_dir / "silver"
        self.gold_dir = self.data_dir / "gold"
        self.gold_dir.mkdir(parents=True, exist_ok=True)
    
    def load_schedule(self, season=2026):
        """Load 2026 NFL schedule."""
        try:
            schedule_file = self.data_dir / "bronze" / f"nfl_schedule_{season}.json"
            if schedule_file.exists():
                import json
                with open(schedule_file) as f:
                    return pd.read_json(f)
        except Exception as e:
            print(f"Could not load schedule: {e}")
        
        return pd.DataFrame()
    
    def enrich_players_with_team(self, players_df, players_master_df):
        """
        Add team information to player DataFrame.
        
        Args:
            players_df: Main player DataFrame
            players_master_df: Master reference with team info
        
        Returns:
            players_df with 'current_team' column added
        """
        result = players_df.copy()
        
        if 'team' in players_master_df.columns:
            # Create mapping from player name to team
            name_to_team = players_master_df[['player_name', 'team']].drop_duplicates()
            
            # Check if we need to merge
            if 'team' not in result.columns:
                # Merge team info
                result = result.merge(
                    name_to_team.rename(columns={'team': 'current_team'}),
                    on='player_name',
                    how='left'
                )
            else:
                # Rename existing team column to current_team
                result = result.rename(columns={'team': 'current_team'})
            
            # Fallback: extract team from conformed_id if available
            if result['current_team'].isna().any() and 'conformed_id' in result.columns:
                print("Note: Some players missing team info. Consider enriching from another source.")
        
        return result
    
    def add_schedule_context(self, predictions_df, matchups_df, schedule_df):
        """
        Add schedule information to predictions.
        
        Args:
            predictions_df: Player predictions
            matchups_df: Player-opponent matchups
            schedule_df: Full schedule
        
        Returns:
            DataFrame with schedule context added
        """
        enriched = predictions_df.copy()
        
        # For current week (week 1), add opponent info
        if len(matchups_df) > 0:
            # Filter to week 1 (current week)
            week1_matchups = matchups_df[matchups_df['week'] == 1].copy()
            
            # Merge opponent for current week
            current_opponent = week1_matchups[['player_name', 'opponent', 'is_home', 'game_date']].drop_duplicates()
            current_opponent.columns = ['player_name', 'opponent_week1', 'is_home_week1', 'game_date_week1']
            
            enriched = enriched.merge(
                current_opponent,
                on='player_name',
                how='left'
            )
        
        # Add full season schedule (weeks 2-18)
        if len(schedule_df) > 0:
            enriched['schedule_2026'] = enriched.apply(
                lambda row: self._get_team_schedule(row, schedule_df),
                axis=1
            )
        
        return enriched
    
    def _get_team_schedule(self, row, schedule_df):
        """Get the full 2026 schedule for a player's team."""
        team = row.get('current_team') or row.get('team')
        
        if pd.isna(team):
            return None
        
        # Get all games for this team
        team_games = schedule_df[
            (schedule_df['home_team'] == team) | 
            (schedule_df['away_team'] == team)
        ].copy()
        
        if len(team_games) == 0:
            return None
        
        # Determine opponent for each game
        team_games['opponent'] = team_games.apply(
            lambda row: row['away_team'] if row['home_team'] == team else row['home_team'],
            axis=1
        )
        
        # Create list of (week, opponent, location) tuples
        schedule_list = team_games.sort_values('week').apply(
            lambda row: f"Wk{row['week']}: vs {row['opponent']}",
            axis=1
        ).tolist()
        
        return " | ".join(schedule_list) if schedule_list else None
    
    def calculate_opponent_adjustments(self, predictions_df, historical_vs_opponent_df, matchups_df):
        """
        Calculate adjustments to predictions based on historical performance vs. opponent.
        
        Args:
            predictions_df: Base predictions
            historical_vs_opponent_df: Historical performance vs. each opponent
            matchups_df: Player-opponent matchups
        
        Returns:
            DataFrame with adjustment factors (opp_adjustment, confidence, reason)
        """
        adjustments = []
        
        for _, prediction in predictions_df.iterrows():
            player_name = prediction.get('player_name')
            
            # Find upcoming opponent (week 1)
            player_matchups = matchups_df[
                (matchups_df['player_name'] == player_name) &
                (matchups_df['week'] == 1)
            ]
            
            if len(player_matchups) == 0:
                # No scheduled opponent found
                adjustments.append({
                    'player_name': player_name,
                    'opponent_adjustment': 1.0,  # No adjustment
                    'adjustment_confidence': 'none',
                    'adjustment_reason': 'No opponent found for week 1'
                })
                continue
            
            opponent = player_matchups.iloc[0]['opponent']
            is_home = player_matchups.iloc[0]['is_home']
            
            # Look up historical vs. this opponent
            hist = historical_vs_opponent_df[
                (historical_vs_opponent_df['player_name'] == player_name) &
                (historical_vs_opponent_df['opponent'] == opponent)
            ]
            
            if len(hist) == 0:
                # No historical data
                adjustments.append({
                    'player_name': player_name,
                    'opponent': opponent,
                    'is_home': is_home,
                    'opponent_adjustment': 1.0,
                    'adjustment_confidence': 'low',
                    'adjustment_reason': f'No historical data vs {opponent}',
                    'avg_points_vs_opp': None,
                    'games_vs_opp': 0
                })
                continue
            
            hist_row = hist.iloc[0]
            avg_points_vs_opp = hist_row['avg_points_vs_opp']
            games_vs_opp = hist_row['games_vs_opp']
            
            # Calculate adjustment multiplier
            # Assume base projection is average over all opponents
            base_avg = prediction.get('projected_points', 15)  # Adjust default as needed
            
            if base_avg > 0:
                adjustment = avg_points_vs_opp / base_avg
            else:
                adjustment = 1.0
            
            # Confidence based on number of games
            if games_vs_opp >= 4:
                confidence = 'high'
            elif games_vs_opp >= 2:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            # Home/away modifier (historically ~3-5% bonus for home teams)
            location_mod = 1.03 if is_home else 0.97
            
            adjustments.append({
                'player_name': player_name,
                'opponent': opponent,
                'is_home': is_home,
                'opponent_adjustment': adjustment * location_mod,
                'adjustment_confidence': confidence,
                'adjustment_reason': f'{games_vs_opp} games vs {opponent}, {("home" if is_home else "away")}',
                'avg_points_vs_opp': avg_points_vs_opp,
                'games_vs_opp': games_vs_opp
            })
        
        return pd.DataFrame(adjustments)
    
    def apply_adjustments(self, predictions_df, adjustments_df, projection_column='projected_points'):
        """
        Apply opponent adjustments to predictions.
        
        Args:
            predictions_df: Base predictions
            adjustments_df: Opponent adjustments
            projection_column: Column name to adjust
        
        Returns:
            DataFrame with adjusted projections and adjustment metadata
        """
        result = predictions_df.merge(adjustments_df, on='player_name', how='left')
        
        # Apply adjustment
        result['opponent_adjusted_projection'] = result.apply(
            lambda row: (
                row[projection_column] * row['opponent_adjustment']
                if pd.notna(row['opponent_adjustment']) and pd.notna(row[projection_column])
                else row[projection_column]
            ),
            axis=1
        )
        
        # Mark which projections were adjusted
        result['was_opponent_adjusted'] = result['opponent_adjustment'] != 1.0
        
        return result
    
    def save_enriched_projections(self, enriched_df):
        """Save enriched predictions with team and opponent info."""
        output_path = self.gold_dir / "predictions_with_opponent.parquet"
        enriched_df.to_parquet(output_path, index=False)
        print(f"✓ Enriched predictions saved to {output_path}")
        print(f"  Columns: {list(enriched_df.columns)}")
        return output_path


def example_usage():
    """Example workflow."""
    from schedule_matcher import ScheduleMatcher
    
    adjuster = OpponentAdjuster()
    matcher = ScheduleMatcher()
    
    # 1. Load schedule
    print("=== Loading 2026 Schedule ===")
    schedule = matcher.load_or_fetch_schedule(2026)
    print(f"Loaded {len(schedule)} games")
    
    # 2. Load predictions
    print("\n=== Loading Predictions ===")
    predictions_path = Path("data/gold/final_predictions.parquet")
    if predictions_path.exists():
        predictions = pd.read_parquet(predictions_path)
        print(f"Loaded {len(predictions)} player predictions")
    else:
        print("Note: predictions file not found. Run prediction stage first.")
        return
    
    # 3. Create matchups
    print("\n=== Creating Matchups ===")
    matchups = matcher.create_opponent_matchups(predictions, schedule)
    print(f"Created {len(matchups)} player-opponent matchups")
    
    # 4. Add team and schedule context
    print("\n=== Adding Schedule Context ===")
    enriched = adjuster.add_schedule_context(predictions, matchups, schedule)
    print(f"Enriched predictions with schedule info")
    
    # 5. Save results
    adjuster.save_enriched_projections(enriched)
    
    # Display sample
    print("\n=== Sample Enriched Predictions ===")
    sample_cols = ['player_name', 'opponent_week1', 'is_home_week1', 'schedule_2026']
    available_cols = [c for c in sample_cols if c in enriched.columns]
    print(enriched[available_cols].head(10).to_string())


if __name__ == "__main__":
    example_usage()
