"""
Fetch NFL schedule and match players to opponents.
Provides team information and opponent-based predictions.
"""

import os
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime
from pathlib import Path


class ScheduleMatcher:
    """Fetch NFL schedule, enrich players with team and opponent info."""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.bronze_dir = self.data_dir / "bronze"
        self.bronze_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_nfl_schedule(self, season=2026):
        """
        Fetch 2026 NFL schedule from public API.
        Returns DataFrame with: game_id, week, home_team, away_team, game_date, season.
        
        Uses GitHub gist with complete 2026 schedule as primary source,
        falls back to ESPN scoreboard API by week.
        """
        schedule_file = self.bronze_dir / f"nfl_schedule_{season}.json"
        
        # Try multiple sources for NFL schedule
        apis = [
            # GitHub gist with complete 2026 schedule
            ("gist", "https://gist.githubusercontent.com/brucehart/8a4cc2c1d169321892552b4a4b212744/raw/nfl-2026-regular-season-schedule.json"),
            # ESPN scoreboard API (will need to fetch by week)
            ("espn", f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&dates={season}"),
        ]
        
        schedule_data = None
        source_type = None
        
        for api_type, api_url in apis:
            try:
                print(f"Attempting to fetch schedule from: {api_url}")
                response = requests.get(api_url, timeout=15)
                
                if response.status_code == 200:
                    schedule_data = response.json()
                    source_type = api_type
                    print(f"✓ Schedule fetched successfully from {api_type}")
                    
                    # Save raw JSON
                    with open(schedule_file, 'w') as f:
                        json.dump(schedule_data, f, indent=2)
                    break
                    
            except Exception as e:
                print(f"✗ Failed to fetch from {api_type}: {e}")
                continue
        
        if schedule_data is None:
            print(f"Warning: Could not fetch 2026 schedule from any source.")
            print(f"Returning empty DataFrame. You may need to manually provide schedule data.")
            return pd.DataFrame(columns=['game_id', 'week', 'home_team', 'away_team', 'game_date', 'season'])
        
        # Parse schedule into standardized format
        return self._parse_schedule(schedule_data, season, source_type)
    
    def _parse_schedule(self, schedule_data, season, source_type="espn"):
        """Parse ESPN or GitHub gist 2026 schedule into standardized DataFrame."""
        games = []
        
        # Handle GitHub gist format (complete 2026 schedule)
        if source_type == "gist" or "weeks" in schedule_data:
            try:
                weeks_data = schedule_data.get("weeks", [])
                for week_info in weeks_data:
                    week_num = week_info.get("week")
                    games_list = week_info.get("games", [])
                    
                    for game in games_list:
                        try:
                            # Navigate the matchup structure
                            matchup = game.get("matchup", {})
                            home_team = matchup.get("home", {}).get("abbreviation")
                            away_team = matchup.get("away", {}).get("abbreviation")
                            game_date = game.get("startTimeUTC", game.get("date", ""))
                            
                            if home_team and away_team:
                                games.append({
                                    'game_id': game.get('id', ''),
                                    'week': week_num,
                                    'home_team': home_team,
                                    'away_team': away_team,
                                    'game_date': game_date,
                                    'season': season
                                })
                        except Exception as e:
                            print(f"  Error parsing game: {e}")
                            continue
            except Exception as e:
                print(f"Error parsing gist format: {e}")
        
        # Handle ESPN format (current week scoreboard)
        elif source_type == "espn" or "events" in schedule_data:
            try:
                events = schedule_data.get("events", [])
                for event in events:
                    try:
                        competitions = event.get('competitions', [])
                        if not competitions:
                            continue
                        
                        comp = competitions[0]
                        week = comp.get('week', None)
                        game_date = event.get('date', '')
                        
                        competitors = comp.get('competitors', [])
                        if len(competitors) >= 2:
                            home = competitors[0].get('team', {}).get('abbreviation', '')
                            away = competitors[1].get('team', {}).get('abbreviation', '')
                            
                            if home and away:
                                games.append({
                                    'game_id': event.get('id', ''),
                                    'week': week,
                                    'home_team': home,
                                    'away_team': away,
                                    'game_date': game_date,
                                    'season': season
                                })
                    except Exception as e:
                        print(f"  Error parsing event: {e}")
                        continue
            except Exception as e:
                print(f"Error parsing ESPN format: {e}")
        
        # Handle NFL API format (list of games)
        elif isinstance(schedule_data, list):
            for game in schedule_data:
                try:
                    games.append({
                        'game_id': game.get('id', ''),
                        'week': game.get('week', None),
                        'home_team': game.get('homeTeam', {}).get('abbreviation', ''),
                        'away_team': game.get('awayTeam', {}).get('abbreviation', ''),
                        'game_date': game.get('gameDate', ''),
                        'season': season
                    })
                except Exception as e:
                    print(f"  Error parsing game: {e}")
                    continue
        
        df = pd.DataFrame(games)
        if len(df) > 0:
            print(f"✓ Parsed {len(df)} games from schedule")
        else:
            print(f"⚠ No games parsed from schedule data")
        return df
    
    def load_or_fetch_schedule(self, season=2026, force_refresh=False):
        """Load schedule from cache, or fetch fresh if not available."""
        schedule_file = self.bronze_dir / f"nfl_schedule_{season}.json"
        
        if schedule_file.exists() and not force_refresh:
            print(f"Loading cached schedule from {schedule_file}")
            with open(schedule_file) as f:
                schedule_data = json.load(f)
            return self._parse_schedule(schedule_data, season)
        
        schedule = self.fetch_nfl_schedule(season)
        
        # If fetch failed, try mock schedule for development
        if len(schedule) == 0:
            print(f"\n💡 Tip: For development/testing without live API, use mock schedule:")
            print(f"   schedule = matcher.create_mock_schedule({season})")
        
        return schedule
    
    def create_mock_schedule(self, season=2026):
        """
        Create a mock 2026 NFL schedule for testing/development.
        Useful when live APIs don't have future season data yet.
        """
        print(f"Creating mock {season} NFL schedule for testing...")
        
        teams = ['KC', 'SF', 'BUF', 'DAL', 'PHI', 'LAR', 'TB', 'NE', 'MIA', 'NYJ',
                 'PIT', 'BAL', 'CLE', 'CIN', 'HOU', 'TEN', 'IND', 'JAX', 'CAR', 'ATL',
                 'NO', 'GB', 'MIN', 'DET', 'CHI', 'ARI', 'LAC', 'DEN', 'LV', 'SEA', 'WSH']
        
        games = []
        game_id = 1
        
        # Create 18-week schedule with each team playing ~17 games
        for week in range(1, 19):
            # Randomly pair teams for this week
            week_teams = teams.copy()
            np.random.shuffle(week_teams)
            
            for i in range(0, len(week_teams) - 1, 2):
                home = week_teams[i]
                away = week_teams[i + 1]
                
                games.append({
                    'game_id': f"game_{game_id}",
                    'week': week,
                    'home_team': home,
                    'away_team': away,
                    'game_date': f"2026-{9 + week//9:02d}-{(week % 7) * 3:02d}",
                    'season': season
                })
                game_id += 1
        
        schedule = pd.DataFrame(games)
        print(f"✓ Generated {len(schedule)} mock games across 18 weeks")
        return schedule
    
    def get_player_team_and_schedule(self, players_df, schedule_df):
        """
        Enrich player DataFrame with team and upcoming opponent info.
        
        Args:
            players_df: DataFrame with player info (should have 'player_name', 'position', etc.)
            schedule_df: DataFrame with schedule (week, home_team, away_team, etc.)
        
        Returns:
            DataFrame with columns: player_name, position, current_team, opponent, opponent_week
        """
        # Get unique teams from schedule
        schedule_df['game_info'] = schedule_df.apply(
            lambda row: {
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'week': row['week'],
                'game_date': row['game_date']
            },
            axis=1
        )
        
        # This would be populated from players_master or LeagueLogs
        # For now, we create a template
        
        enriched = players_df.copy()
        
        # Try to extract team from player data or conformed_id
        if 'team' in enriched.columns:
            enriched['current_team'] = enriched['team']
        else:
            print("Warning: 'team' column not found in players_df. Team assignment will be incomplete.")
            enriched['current_team'] = None
        
        return enriched, schedule_df
    
    def create_opponent_matchups(self, players_df, schedule_df):
        """
        Create a DataFrame mapping each player to their opponent for each week.
        
        Returns:
            DataFrame: player_name, position, current_team, week, opponent, game_date, is_home
        """
        if len(schedule_df) == 0:
            print("Schedule is empty. Cannot create opponent matchups.")
            return pd.DataFrame()
        
        # Determine team column name
        team_column = 'current_team' if 'current_team' in players_df.columns else 'team'
        
        # Ensure we have the team column
        if team_column not in players_df.columns:
            print(f"Warning: No team column found. Expected 'current_team' or 'team'.")
            return pd.DataFrame()
        
        matchups = []
        
        # For each team in the schedule, find matching players
        all_teams = set(schedule_df['home_team'].unique()) | set(schedule_df['away_team'].unique())
        
        for team in all_teams:
            # Find players on this team
            team_players = players_df[
                (players_df[team_column] == team)
            ].copy()
            
            if len(team_players) == 0:
                continue
            
            # Add current_team column if it doesn't exist
            if 'current_team' not in team_players.columns:
                team_players['current_team'] = team
            
            # Find games for this team
            home_games = schedule_df[schedule_df['home_team'] == team].copy()
            home_games['is_home'] = True
            home_games['opponent'] = home_games['away_team']
            
            away_games = schedule_df[schedule_df['away_team'] == team].copy()
            away_games['is_home'] = False
            away_games['opponent'] = away_games['home_team']
            
            team_games = pd.concat([home_games, away_games], ignore_index=True)
            
            # Cross-join players with their schedule
            team_players['_join_key'] = 1
            team_games['_join_key'] = 1
            
            player_schedule = team_players.merge(team_games, on='_join_key').drop('_join_key', axis=1)
            matchups.append(player_schedule)
        
        if matchups:
            result = pd.concat(matchups, ignore_index=True)
            # Select and order desired columns
            cols = ['player_name', 'position', 'current_team', 'week', 'opponent', 'game_date', 'is_home']
            # Only include columns that exist
            cols = [c for c in cols if c in result.columns]
            return result[cols]
        
        return pd.DataFrame(columns=['player_name', 'position', 'current_team', 'week', 'opponent', 'game_date', 'is_home'])
    
    def calculate_vs_opponent_stats(self, player_stats_df, schedule_df, historical_seasons=[2022, 2023, 2024, 2025]):
        """
        Calculate historical performance vs. each opponent.
        
        Args:
            player_stats_df: Historical player stats (should include player_name, team, opponent, season, points)
            schedule_df: 2026 schedule
            historical_seasons: List of seasons to analyze
        
        Returns:
            DataFrame: player_name, opponent, avg_points_vs_opp, games_vs_opp, last_game_result
        """
        # Filter to historical seasons only
        historical = player_stats_df[
            player_stats_df['season'].isin(historical_seasons)
        ].copy()
        
        if len(historical) == 0:
            print(f"Warning: No historical data found for seasons {historical_seasons}")
            return pd.DataFrame()
        
        # Group by player and opponent
        vs_opponent = historical.groupby(['player_name', 'opponent']).agg({
            'points': ['mean', 'count', 'max', 'min'],
            'season': lambda x: x.iloc[-1] if len(x) > 0 else None  # most recent season
        }).reset_index()
        
        vs_opponent.columns = ['player_name', 'opponent', 'avg_points_vs_opp', 'games_vs_opp', 'max_vs_opp', 'min_vs_opp', 'last_season']
        
        return vs_opponent


def example_usage():
    """Example of how to use ScheduleMatcher."""
    matcher = ScheduleMatcher()
    
    # Fetch 2026 schedule
    print("=== Fetching 2026 Schedule ===")
    schedule = matcher.load_or_fetch_schedule(2026)
    print(f"\nSchedule preview:\n{schedule.head()}\n")
    
    # Create sample players DataFrame (in real usage, this comes from your pipeline)
    sample_players = pd.DataFrame({
        'player_name': ['Patrick Mahomes', 'Travis Kelce', 'Derrick Henry'],
        'position': ['QB', 'TE', 'RB'],
        'team': ['KC', 'KC', 'TN'],
    })
    
    # Create opponent matchups
    print("=== Creating Opponent Matchups ===")
    matchups = matcher.create_opponent_matchups(sample_players, schedule)
    print(f"\nMatchups preview (showing first 5 weeks):\n{matchups.head(10)}\n")
    
    # Save results
    matchups.to_parquet('data/silver/opponent_matchups.parquet', index=False)
    print(f"Matchups saved to data/silver/opponent_matchups.parquet")


if __name__ == "__main__":
    example_usage()
