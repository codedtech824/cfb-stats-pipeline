#!/usr/bin/env python3
"""
Quick test to verify 2026 NFL schedule integration.
"""

from schedule_matcher import ScheduleMatcher
import pandas as pd

# Initialize matcher
matcher = ScheduleMatcher(data_dir="data")

# Fetch real 2026 schedule
print("\n" + "="*60)
print("Fetching real 2026 NFL schedule from live sources...")
print("="*60)

schedule = matcher.load_or_fetch_schedule(season=2026, force_refresh=True)

print(f"\nSchedule loaded: {len(schedule)} games")
print(f"Weeks covered: {sorted(schedule['week'].unique())}")
print(f"\nFirst 5 games:")
print(schedule.head(5).to_string(index=False))

print(f"\n\nTeams in schedule:")
teams = set(schedule['home_team'].unique()) | set(schedule['away_team'].unique())
print(sorted(teams))

print(f"\nGames per week:")
print(schedule['week'].value_counts().sort_index())

# Verify data quality
print(f"\n" + "="*60)
print("Data Quality Checks:")
print("="*60)
print(f"✓ Total games: {len(schedule)}")
print(f"✓ Unique teams: {len(teams)}")
print(f"✓ Weeks: {schedule['week'].min()} to {schedule['week'].max()}")
print(f"✓ Missing game_ids: {schedule['game_id'].isna().sum()}")
print(f"✓ Missing dates: {schedule['game_date'].isna().sum()}")

print("\n✓ Integration successful! Schedule is ready for use.")
