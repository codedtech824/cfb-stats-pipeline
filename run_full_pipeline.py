"""
Complete fantasy football pipeline orchestrator.
Fetches 2026 schedule, player stats from nfldata.org API, and analyzes matchups.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\n❌ FAILED: {description}")
        return False
    
    print(f"\n✅ COMPLETED: {description}")
    return True


def main():
    """Run the complete pipeline."""
    print("\n" + "="*70)
    print("🏈 FANTASY FOOTBALL PIPELINE - ORCHESTRATOR")
    print("="*70)
    print("\nSequence:")
    print("  1. Fetch 2026 NFL Schedule")
    print("  2. Fetch Player Stats from nfldata.org API (2022-2025)")
    print("  3. Analyze Matchups & Identify Problem Opponents")
    print("  4. Generate Draft Round Rankings")
    print()
    
    # Step 1: Fetch schedule
    if not run_command(
        [sys.executable, 'test_schedule_integration.py'],
        "Step 1/4: Fetch 2026 NFL Schedule"
    ):
        return False
    
    # Step 2: Fetch stats from nfldata.org API
    if not run_command(
        [sys.executable, 'fetch_from_nfldata_api.py'],
        "Step 2/4: Fetch Player Stats from nfldata.org API"
    ):
        print("\n⚠️ Warning: Could not fetch from API, data may not be available")
        # Don't fail here - API might have rate limits or 2025 data not ready
    
    # Step 3: Analyze matchups
    if not run_command(
        [sys.executable, 'nfl_matchup_analyzer.py'],
        "Step 3/4: Analyze Matchups & Identify Problem Opponents"
    ):
        return False
    
    # Step 4: Generate draft rankings
    if not run_command(
        [sys.executable, 'draft_ranker.py'],
        "Step 4/4: Generate Draft Round Rankings"
    ):
        return False
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE")
    print("="*70)
    print("\nOutput Files:")
    print("  📊 data/silver/game_level_stats.csv - Player game-level stats")
    print("  📊 data/silver/vs_opponent_history.csv - Matchup history")
    print("  🎯 data/silver/problem_matchups.csv - Problem opponents")
    print("  🏆 data/gold/draft_rankings.csv - Draft round picks by position")
    print("\nReady for 2026 matchup predictions!")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
