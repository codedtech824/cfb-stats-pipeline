"""
NFL Data API Fetcher v2 - Smart opponent mapping
Fetches player game-level stats from nfldata.org and maps opponent data from games.
"""

import requests
import pandas as pd
from pathlib import Path
import time


class SmartNFLDataFetcher:
    """Fetch NFL stats with intelligent opponent mapping."""
    
    BASE_URL = "https://api.nfldata.org/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NFL-Fantasy-Pipeline/1.0'
        })
    
    def fetch_games_for_season(self, season):
        """Fetch all games for a season to build opponent mappings."""
        print(f"    Fetching {season} games...", end=" ", flush=True)
        try:
            url = f"{self.BASE_URL}/games"
            params = {'season': season, 'limit': 500}
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                games = data.get('data', [])
                print(f"✓ {len(games)} games")
                return games
        except Exception as e:
            print(f"✗ {str(e)[:30]}")
        
        return []
    
    def build_opponent_map(self, games):
        """
        Build a mapping of team -> opponent for each week from games data.
        Returns dict like: {(team, week): opponent_team, ...}
        """
        opponent_map = {}
        for game in games:
            try:
                week = game.get('week')
                home_team = game.get('home_team')
                away_team = game.get('away_team')
                
                if home_team and away_team and week:
                    # Home team plays against away team
                    opponent_map[(home_team, week)] = away_team
                    # Away team plays against home team
                    opponent_map[(away_team, week)] = home_team
            except:
                pass
        
        return opponent_map
    
    def fetch_stats_for_position(self, position, season):
        """
        Fetch stats for a position (passing, receiving, rushing) with full pagination.
        For 2025+, falls back to NGS endpoints since regular stat endpoints are empty.
        """
        endpoint_map = {
            'passing': '/stats/passing',
            'receiving': '/stats/receiving',
            'rushing': '/stats/rushing'
        }
        ngs_map = {
            'passing': '/stats/ngs/passing',
            'receiving': '/stats/ngs/receiving',
            'rushing': '/stats/ngs/rushing'
        }
        
        endpoint = endpoint_map.get(position, '/stats/passing')
        
        # Try standard endpoint with full pagination
        all_records = []
        offset = 0
        limit = 500
        
        try:
            while True:
                url = f"{self.BASE_URL}{endpoint}"
                params = {'season': season, 'limit': limit, 'offset': offset}
                response = self.session.get(url, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get('data', [])
                    total = data.get('total', 0)
                    all_records.extend(records)
                    
                    if len(all_records) >= total or len(records) < limit:
                        break
                    offset += limit
                else:
                    print(f"        (status {response.status_code})")
                    break
            
            if all_records:
                return all_records, 'standard'
            else:
                # Fall back to NGS endpoint (has 2025 data)
                ngs_endpoint = ngs_map.get(position)
                if ngs_endpoint:
                    return self._fetch_ngs_all_pages(ngs_endpoint, season), 'ngs'
        except Exception as e:
            print(f"      Error fetching {position}: {str(e)}")
        
        return [], 'standard'
    
    def _fetch_ngs_all_pages(self, endpoint, season):
        """Fetch all pages from an NGS endpoint."""
        all_records = []
        offset = 0
        limit = 500
        
        while True:
            try:
                url = f"{self.BASE_URL}{endpoint}"
                params = {'season': season, 'limit': limit, 'offset': offset}
                response = self.session.get(url, params=params, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get('data', [])
                    total = data.get('total', 0)
                    all_records.extend(records)
                    
                    if len(all_records) >= total or len(records) < limit:
                        break
                    offset += limit
                else:
                    break
            except Exception as e:
                break
        
        return all_records
    
    @staticmethod
    def calc_fantasy_points_from_ngs(stat, position):
        """
        Compute standard fantasy points from NGS raw stats.
        Standard scoring: pass_yd/25, pass_td*4, int*-2, rush_yd/10, rush_td*6, rec_yd/10, rec_td*6
        """
        fp = 0.0
        if position == 'passing':
            fp += stat.get('pass_yards', 0) / 25
            fp += stat.get('pass_touchdowns', 0) * 4
            fp -= stat.get('interceptions', 0) * 2
        elif position == 'rushing':
            fp += stat.get('rush_yards', 0) / 10
            fp += stat.get('rush_touchdowns', 0) * 6
        elif position == 'receiving':
            fp += stat.get('rec_yards', 0) / 10
            fp += stat.get('rec_touchdowns', 0) * 6
            fp += stat.get('receptions', 0) * 0.5  # half-PPR
        return fp
    
    def build_game_level_stats(self, seasons=[2022, 2023, 2024, 2025]):
        """
        Fetch stats and map opponent information.
        """
        print("\n" + "="*70)
        print("🏈 FETCHING FROM NFL DATA API (nfldata.org)")
        print("="*70)
        
        all_records = []
        total_processed = 0
        
        print("\n📊 Processing player stats...")
        for season in seasons:
            print(f"\nSeason {season}:")
            
            # First fetch all games to build opponent map
            games = self.fetch_games_for_season(season)
            if not games:
                print(f"  ⚠ No games found, skipping")
                continue
            
            opponent_map = self.build_opponent_map(games)
            
            # Build home_away map: (team, week) -> True if home, False if away
            home_away_map = {}
            for game in games:
                try:
                    week = game.get('week')
                    home_team = game.get('home_team')
                    away_team = game.get('away_team')
                    
                    if home_team and away_team and week:
                        home_away_map[(home_team, week)] = True   # home
                        home_away_map[(away_team, week)] = False  # away
                except:
                    pass
            
            print(f"    Built opponent map for {len(opponent_map)} team-weeks")
            
            # Now fetch stats for each position
            positions = ['passing', 'receiving', 'rushing']
            season_total = 0
            
            for pos in positions:
                print(f"    Fetching {pos}...", end=" ", flush=True)
                stats, source = self.fetch_stats_for_position(pos, season)
                print(f"✓ {len(stats)} records {'(NGS)' if source == 'ngs' else ''}")
                
                if not stats:
                    continue
                
                pos_label = {'passing': 'QB', 'receiving': 'RECEIVING', 'rushing': 'RUSHING'}[pos]
                
                # Process each stat record
                for stat in stats:
                    try:
                        if source == 'ngs':
                            # NGS format: different field names
                            player_name = stat.get('player_display_name', '')
                            team = stat.get('team_abbr', '')
                            week = stat.get('week')
                            # Compute fantasy points from raw NGS stats
                            fantasy_points = self.calc_fantasy_points_from_ngs(stat, pos)
                            position = 'QB' if pos == 'passing' else stat.get('player_position', pos_label)
                        else:
                            # Standard format
                            player_name = stat.get('player_name', '')
                            team = stat.get('recent_team', '')
                            week = stat.get('week')
                            fantasy_points = stat.get('fantasy_points', 0)
                            position = 'QB' if pos == 'passing' else stat.get('position', pos_label)
                        
                        # Skip if missing key fields
                        if not player_name or not team or week is None or fantasy_points is None:
                            continue
                        
                        # Look up opponent and home/away status
                        opponent = opponent_map.get((team, week), '')
                        is_home = home_away_map.get((team, week), False)
                        
                        record = {
                            'season': season,
                            'week': week,
                            'player_name': player_name,
                            'position': position,
                            'team': team,
                            'opponent': opponent,
                            'is_home': is_home,
                            'fantasy_points': fantasy_points,
                        }
                        all_records.append(record)
                        season_total += 1
                    except Exception as e:
                        print(f"      Processing error: {str(e)[:30]}")
                
                time.sleep(0.3)  # Rate limiting
            
            print(f"  ✓ Season {season}: {season_total} records")
            total_processed += season_total
        
        if all_records:
            df = pd.DataFrame(all_records)
            
            # Clean: remove records without opponents (edge cases)
            df = df[df['opponent'].notna() & (df['opponent'] != '')]
            
            # Generate approximate game date from season and week
            def get_game_date(row):
                season = row['season']
                week = row['week']
                start_date = pd.Timestamp(f"{season}-09-01")
                return start_date + pd.Timedelta(weeks=int(week) - 1)
            
            df['game_date'] = df.apply(get_game_date, axis=1)
            
            # Reorder columns
            cols = ['season', 'week', 'game_date', 'player_name', 'position', 'team', 'opponent', 'is_home', 'fantasy_points']
            df = df[[c for c in cols if c in df.columns]]
            
            print(f"\n✅ SUCCESS - Fetched {len(df):,} player-game records")
            print(f"   Seasons: {sorted(df['season'].unique())}")
            print(f"   Unique players: {df['player_name'].nunique():,}")
            print(f"   Unique opponents: {df['opponent'].nunique()}")
            
            return df
        
        print(f"\n❌ No data found")
        return None


def main():
    """Fetch NFL stats from nfldata.org API."""
    
    print("\n" + "="*70)
    print("🏈 NFL DATA API FETCHER (with Opponent Mapping)")
    print("Using: nfldata.org Official API")
    print("="*70)
    
    fetcher = SmartNFLDataFetcher()
    
    # Fetch data
    df = fetcher.build_game_level_stats([2022, 2023, 2024, 2025])
    
    if df is not None and len(df) > 0:
        # Save
        output_path = Path('data/silver/game_level_stats.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print("\n" + "="*70)
        print("✅ DATA SAVED TO CSV")
        print("="*70)
        print(f"File: {output_path}")
        print(f"Total Records: {len(df):,}")
        
        print("\n📊 Sample Data:")
        print("-" * 70)
        print(df.head(15).to_string())
        
        print("\n✓ Ready for analysis!")
        print("   python nfl_matchup_analyzer.py")
        
        return df
    else:
        print("\n❌ Failed to fetch data from API")
        return None


if __name__ == "__main__":
    df = main()
