"""
Draft Round Picker - Ranks players by position using historical fantasy data
and 2026 matchup analysis. Outputs projected draft rounds for each player.

Roster structure (12-team, 15-round draft):
  Starters (9): QB x1, RB x2, WR x2, TE x1, FLEX (RB/WR/TE) x1, K x1, DST x1
  Bench (6-7):  reserve spots for bye weeks and injuries
  Total:        15-16 players per team, 180 picks across the draft

Position demand in a 12-team league:
  RB:  ~60 drafted  (2 starters + 1 shared flex + 2 bench = 5 per team)
  WR:  ~60 drafted  (2 starters + 1 shared flex + 2 bench = 5 per team)
  QB:  ~18-24       (1 starter + 1 backup = 1.5 per team)
  TE:  ~18-24       (1 starter + 1 bench  = 1.5 per team)
  K:   ~12-15       (1 starter, always drafted last 2 rounds)
  DST: ~12-15      (1 starter, rounds 13-15, ranked by historical avg DST fantasy pts)
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ---------------------------------------------------------------------------
# Draft round cutoffs by position rank in a 12-team, 15-round PPR draft.
# Reflects real ADP patterns:
#   - RBs go earliest due to injury risk + limited elite depth
#   - WRs go throughout the draft (more depth at position)
#   - QBs: "wait on QB" strategy is common — top QB goes rounds 4-5
#   - TEs: top 1-2 are premium picks; rest go mid-to-late
#   - Ks: always last 2 rounds regardless of quality
#
# Format: (round_number, max_pos_rank_for_this_round)
# ---------------------------------------------------------------------------
LEAGUE_SIZE = 12
ROSTER_SPOTS = {
    'RB': 5,   # 2 starters + 1 flex + 2 bench = 60 RBs total drafted
    'WR': 5,   # 2 starters + 1 flex + 2 bench = 60 WRs total drafted
    'QB': 1.5, # 1 starter + backup share  = ~18 QBs total drafted
    'TE': 1.5, # 1 starter + backup share  = ~18 TEs total drafted
    'K':  1,   # 1 starter, last rounds     = ~12 Ks total drafted
    'DST': 1,  # 1 starter, last rounds     = ~12 DSTs total drafted
}

ROUND_CUTOFFS = {
    # RBs: high demand, go heavily in rounds 1-6, with handcuffs in 7-12
    'RB': [
        (1,  6),   # elite RB1 — top-3 picks territory
        (2, 12),   # RB1 — solid every-week starter
        (3, 18),   # RB2 — reliable second starter
        (4, 24),   # low-end RB2 / flex starter
        (5, 36),   # flex RB — borderline starter
        (6, 48),   # bench RB / handcuff
        (7, 60),   # depth RB
        (8, 72),   # late bench / bye-week fill
        (9, 85),
    ],
    # WRs: more depth than RB, can wait a round; elite still go rounds 1-3
    'WR': [
        (1,  6),   # elite WR1 — top-10 picks territory
        (2, 12),   # WR1
        (3, 24),   # WR2 — solid starter
        (4, 36),   # low-end WR2 / flex
        (5, 48),   # flex WR
        (6, 60),   # bench WR
        (7, 72),   # depth WR
        (8, 90),
        (9, 110),
    ],
    # QBs: "wait on QB" — only 1 starter needed; top QBs rounds 4-6
    # (Jalen Hurts/Josh Allen dual-threat types go earlier due to rushing bonus)
    'QB': [
        (4,  2),   # elite dual-threat QB (Allen/Hurts/Jackson/Daniels)
        (5,  4),   # top QB1
        (6,  7),   # solid QB1
        (7, 10),   # QB1 fringe
        (8, 13),   # streaming QB / QB2
        (9, 16),
        (10, 20),
        (11, 28),
    ],
    # TEs: top 1-2 are premium (similar value to WR1); everyone else waits
    'TE': [
        (2,  1),   # elite TE (Kittle/McBride tier) — round 2-3
        (3,  2),   # second elite TE
        (5,  4),   # TE1 — reliable starter
        (6,  6),   # solid TE1
        (7,  9),   # borderline TE1
        (8, 12),   # streaming TE
        (9, 15),
        (10, 24),
    ],
    # Ks: always rounds 13-15, nobody drafts K before that
    'K': [
        (13, 12),
        (14, 24),
        (15, 40),
    ],
    # DST: 1 starter, goes alongside Ks in rounds 13-15
    'DST': [
        (13,  4),  # elite DST (top-4, dominant units)
        (14, 12),  # solid DST
        (15, 24),  # streamable DST
    ],
}

MIN_GAMES = 5  # minimum games played to be included


def get_position_rank_to_round(position, pos_rank):
    """Map a position rank to a draft round based on ROUND_CUTOFFS."""
    cutoffs = ROUND_CUTOFFS.get(position, [(15, 9999)])
    for round_num, max_rank in cutoffs:
        if pos_rank <= max_rank:
            return round_num
    return 'Undrafted'


def normalize_position(row_position, player_name, position_lookup):
    """
    Map raw position labels to canonical fantasy positions.
    NGS records (WR/RB/TE/QB/K) are accurate and used directly.
    Standard API records (QB/RECEIVING/RUSHING) are unreliable for non-QB players;
    the position_lookup from NGS data overrides them where possible.
    """
    p = str(row_position).upper()
    
    # Clean NGS labels — accurate, use directly
    if p in ('WR', 'RB', 'TE', 'QB', 'K'):
        return p
    if p == 'FB':
        return 'RB'
    
    # Standard endpoint labels (QB/RECEIVING/RUSHING) — use NGS lookup if available
    if player_name in position_lookup:
        return position_lookup[player_name]
    
    # No NGS data for this player — fall back to raw label
    if p == 'QB':
        return 'QB'
    
    return None  # RECEIVING/RUSHING without lookup — handled in ambiguous loop


def build_player_position_lookup(gl):
    """
    Build a {player_name: canonical_position} lookup from NGS records
    (2025 data has WR/RB/TE labels directly on each record).
    """
    ngs_positions = gl[gl['position'].isin(['WR', 'RB', 'TE', 'FB', 'QB', 'K'])]
    if ngs_positions.empty:
        return {}
    
    # For each player, take the most common clean position
    lookup = (
        ngs_positions.groupby('player_name')['position']
        .agg(lambda x: x.value_counts().index[0])
        .to_dict()
    )
    # Map FB -> RB
    return {k: ('RB' if v == 'FB' else v) for k, v in lookup.items()}


def _fetch_2026_rosters():
    """
    Fetch the nflverse 2026 season roster CSV.
    Returns a DataFrame with full_name and team columns (2,800 active players).
    Returns empty DataFrame on failure.
    """
    import requests, io
    url = 'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2026.csv'
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            # Keep one row per player (some appear multiple times for different weeks)
            df = df[['full_name', 'team', 'position']].dropna(subset=['full_name', 'team'])
            df = df.drop_duplicates(subset=['full_name'], keep='last')
            print(f"  ✓ 2026 roster: {len(df):,} players from nflverse")
            return df
    except Exception as e:
        print(f"  ⚠ Could not fetch 2026 roster: {str(e)[:40]}")
    return pd.DataFrame()


def load_and_consolidate(gl):
    """
    Consolidate game_level_stats into one row per player with:
    - canonical position
    - overall avg fantasy points
    - games played
    - consistency (std dev / mean)
    """
    position_lookup = build_player_position_lookup(gl)

    # Assign canonical position to every row
    def assign_pos(row):
        return normalize_position(row['position'], row['player_name'], position_lookup)

    gl = gl.copy()
    gl['canon_pos'] = gl.apply(assign_pos, axis=1)

    # For RECEIVING/RUSHING rows without a clean position, try to infer:
    # - If a player appears as both RECEIVING and RUSHING, they're a skill player
    #   (likely RB for dual-entry, WR/TE for receiving-only)
    ambiguous = gl[gl['canon_pos'].isna()]['player_name'].unique()
    for player in ambiguous:
        rows = gl[gl['player_name'] == player]
        pos_labels = set(rows['position'].unique())
        # Only assign QB if there's an actual QB row, not just RUSHING/RECEIVING
        if 'RUSHING' in pos_labels and 'RECEIVING' in pos_labels:
            gl.loc[gl['player_name'] == player, 'canon_pos'] = 'RB'
        elif 'RUSHING' in pos_labels:
            gl.loc[gl['player_name'] == player, 'canon_pos'] = 'RB'
        elif 'RECEIVING' in pos_labels:
            gl.loc[gl['player_name'] == player, 'canon_pos'] = 'WR'

    # Enforce QB purity: players who appear in 2025 NGS passing records are
    # confirmed QBs. Players with QB-labeled rows who are NOT in that set are
    # false positives from the standard API returning all players in the passing
    # endpoint. Remove them from the QB bucket.
    ngs_qbs = set(gl[(gl['season'] == 2025) & (gl['position'] == 'QB')]['player_name'].unique())
    # Also keep any player who ONLY has QB rows (retired QBs pre-2025)
    qb_only_players = set(
        gl.groupby('player_name')['canon_pos']
        .apply(lambda x: set(x.dropna()))
        .pipe(lambda s: s[s.apply(lambda pos_set: pos_set == {'QB'})].index)
    )
    confirmed_qbs = ngs_qbs | qb_only_players
    gl.loc[(gl['canon_pos'] == 'QB') & (~gl['player_name'].isin(confirmed_qbs)), 'canon_pos'] = None
    
    # Drop rows still unresolved
    gl = gl[gl['canon_pos'].notna()]

    # For players with duplicate rows per game (appears in both RUSHING and RECEIVING),
    # deduplicate by taking the max fantasy points per player/season/week
    player_game = (
        gl.groupby(['player_name', 'canon_pos', 'season', 'week'])['fantasy_points']
        .max()
        .reset_index()
    )

    # Most recent team per player — fetch from nflverse 2026 season roster
    # (the definitive source for current team assignments as of the 2026 season).
    # Falls back to 2025 season data for players not on a 2026 roster.
    roster_2026 = _fetch_2026_rosters()

    # Build lookup: full_name -> team from 2026 roster
    if not roster_2026.empty:
        roster_lookup = roster_2026.set_index('full_name')['team'].to_dict()
    else:
        roster_lookup = {}

    # Fallback: most recent game-level team per player (2025 season → oldest)
    fallback_team = (
        gl.sort_values(['season', 'week'])
        .groupby('player_name')['team']
        .last()
        .reset_index()
        .rename(columns={'team': 'team_fallback'})
    )

    # Aggregate to player level
    player_stats = (
        player_game.groupby(['player_name', 'canon_pos'])
        .agg(
            avg_fp=('fantasy_points', 'mean'),
            games=('fantasy_points', 'count'),
            std_fp=('fantasy_points', 'std'),
            seasons_played=('season', lambda x: f"{x.min()}-{x.max()}")
        )
        .reset_index()
    )
    player_stats.rename(columns={'canon_pos': 'position'}, inplace=True)
    player_stats = player_stats.merge(fallback_team, on='player_name', how='left')
    # Apply 2026 roster lookup first, fall back to 2025 game data
    player_stats['team'] = player_stats['player_name'].map(roster_lookup).fillna(player_stats['team_fallback'])
    player_stats.drop(columns=['team_fallback'], inplace=True)
    player_stats['consistency'] = (player_stats['std_fp'] / player_stats['avg_fp'].abs().clip(lower=0.1)).round(2)

    # Minimum games filter
    player_stats = player_stats[player_stats['games'] >= MIN_GAMES]

    return player_stats


def apply_matchup_adjustment(player_stats):
    """
    Load problem_matchups.csv and apply a small penalty to avg_fp
    for players with SEVERE or MODERATE problem matchups in 2026.
    This nudges their ranking down to reflect schedule difficulty.
    """
    pm_path = Path('data/silver/problem_matchups.csv')
    if not pm_path.exists():
        player_stats['matchup_adj'] = 0.0
        player_stats['problem_matchup_count'] = 0
        return player_stats

    pm = pd.read_csv(pm_path)

    # Count problem matchups per player by severity
    severity_penalty = {'SEVERE': -1.5, 'MODERATE': -0.75, 'MINOR': -0.25}
    
    def calc_adj(player_name):
        player_pm = pm[pm['player_name'] == player_name]
        if player_pm.empty:
            return 0.0, 0
        total_pen = 0.0
        for _, row in player_pm.iterrows():
            total_pen += severity_penalty.get(row.get('severity', 'MINOR'), -0.25)
        return round(total_pen, 2), len(player_pm)

    adjs = player_stats['player_name'].apply(lambda n: pd.Series(calc_adj(n), index=['matchup_adj', 'problem_matchup_count']))
    player_stats = pd.concat([player_stats, adjs], axis=1)
    player_stats['adjusted_fp'] = (player_stats['avg_fp'] + player_stats['matchup_adj']).round(2)

    return player_stats


def assign_draft_rounds(player_stats):
    """Rank within position and assign draft rounds."""
    results = []

    for pos in ['RB', 'WR', 'QB', 'TE']:
        pos_players = player_stats[player_stats['position'] == pos].copy()
        if pos_players.empty:
            continue

        # Rank by adjusted_fp descending
        pos_players = pos_players.sort_values('adjusted_fp', ascending=False).reset_index(drop=True)
        pos_players['pos_rank'] = pos_players.index + 1
        pos_players['draft_round'] = pos_players['pos_rank'].apply(
            lambda r: get_position_rank_to_round(pos, r)
        )

        results.append(pos_players)

    if not results:
        return pd.DataFrame()

    return pd.concat(results, ignore_index=True)


# ---------------------------------------------------------------------------
# DST Fantasy Points Scoring
# Standard league scoring for Defense/Special Teams unit
# ---------------------------------------------------------------------------
def pa_to_fantasy_pts(points_allowed):
    """Convert points allowed to fantasy points using standard DST scoring."""
    if points_allowed == 0:       return 10
    elif points_allowed <= 6:     return 7
    elif points_allowed <= 13:    return 4
    elif points_allowed <= 20:    return 1
    elif points_allowed <= 27:    return 0
    elif points_allowed <= 34:    return -1
    else:                         return -4


def fetch_dst_rankings(seasons=(2022, 2023, 2024, 2025)):
    """
    Fetch DST data from nfldata.org and rank all 32 NFL teams.

    DST fantasy score per game (standard):
      - Points Allowed:  0=10, 1-6=7, 7-13=4, 14-20=1, 21-27=0, 28-34=-1, 35+=-4
      - Sacks:           +1 pt each
      - Interceptions:   +2 pts each
      - Fumble recovery: +2 pts each
      - Defensive TD:    +6 pts each
      - Safety:          +2 pts each

    Strategy:
      1. Get per-game points allowed from /games (home_score / away_score)
      2. Get season totals for sacks, turnovers, def TDs from /stats/team
      3. Convert season stats to per-game rates, then compute game-level approx DST fp
    """
    import requests

    BASE_URL = "https://api.nfldata.org/v1"
    session = requests.Session()
    session.headers['User-Agent'] = 'NFL-Fantasy-Pipeline/1.0'

    game_records = []   # per-game DST rows
    team_rates = {}     # {(team, season): per-game sack/turnover/td rates}

    print("  Fetching games for points-allowed...")
    for season in seasons:
        # Get all regular season games
        resp = session.get(f"{BASE_URL}/games", params={'season': season, 'limit': 500}, timeout=30)
        if resp.status_code != 200:
            continue
        games = resp.json().get('data', [])
        reg = [g for g in games if g.get('game_type') == 'REG']

        for game in reg:
            home = game.get('home_team')
            away = game.get('away_team')
            week = game.get('week')
            home_score = game.get('home_score') or 0
            away_score = game.get('away_score') or 0

            if not home or not away or week is None:
                continue

            # Home DST faces away offense → points allowed = away_score
            game_records.append({'season': season, 'week': week, 'team': home,
                                  'opponent': away, 'is_home': True, 'points_allowed': away_score})
            # Away DST faces home offense → points allowed = home_score
            game_records.append({'season': season, 'week': week, 'team': away,
                                  'opponent': home, 'is_home': False, 'points_allowed': home_score})

        # Get team season stats for supplementary stats
        resp2 = session.get(f"{BASE_URL}/stats/team",
                            params={'season': season, 'season_type': 'REG', 'limit': 50}, timeout=30)
        if resp2.status_code == 200:
            for ts in resp2.json().get('data', []):
                team = ts.get('team')
                games_played = ts.get('games') or 17
                if not team or games_played == 0:
                    continue
                team_rates[(team, season)] = {
                    'sacks_pg':   (ts.get('def_sacks') or 0) / games_played,
                    'ints_pg':    (ts.get('def_interceptions') or 0) / games_played,
                    'fum_rec_pg': (ts.get('fumble_recovery_opp') or 0) / games_played,
                    'def_td_pg':  (ts.get('def_tds') or 0) / games_played,
                    'safety_pg':  (ts.get('def_safeties') or 0) / games_played,
                }

    if not game_records:
        print("  ⚠ No DST game data available")
        return pd.DataFrame()

    df = pd.DataFrame(game_records)

    # Compute DST fantasy points per game
    def dst_fp(row):
        pa_pts = pa_to_fantasy_pts(row['points_allowed'])
        rates = team_rates.get((row['team'], row['season']), {})
        other = (
            rates.get('sacks_pg',   0) * 1 +
            rates.get('ints_pg',    0) * 2 +
            rates.get('fum_rec_pg', 0) * 2 +
            rates.get('def_td_pg',  0) * 6 +
            rates.get('safety_pg',  0) * 2
        )
        return round(pa_pts + other, 2)

    df['fantasy_points'] = df.apply(dst_fp, axis=1)

    # Aggregate to team level across all seasons
    dst_stats = (
        df.groupby('team')
        .agg(
            avg_fp=('fantasy_points', 'mean'),
            games=('fantasy_points', 'count'),
            std_fp=('fantasy_points', 'std'),
            seasons_played=('season', lambda x: f"{int(x.min())}-{int(x.max())}")
        )
        .reset_index()
    )
    dst_stats['position'] = 'DST'
    dst_stats['player_name'] = dst_stats['team']
    dst_stats['adjusted_fp'] = dst_stats['avg_fp'].round(2)
    dst_stats['matchup_adj'] = 0.0
    dst_stats['problem_matchup_count'] = 0
    dst_stats['consistency'] = (dst_stats['std_fp'] / dst_stats['avg_fp'].abs().clip(lower=0.1)).round(2)

    # Rank by adjusted_fp descending
    dst_stats = dst_stats.sort_values('adjusted_fp', ascending=False).reset_index(drop=True)
    dst_stats['pos_rank'] = dst_stats.index + 1
    dst_stats['draft_round'] = dst_stats['pos_rank'].apply(
        lambda r: get_position_rank_to_round('DST', r)
    )

    print(f"  ✓ {len(dst_stats)} DST units ranked  ({len(df):,} game records)")
    return dst_stats


def main():
    print("=" * 70)
    print("🏈 FANTASY DRAFT ROUND PICKER")
    print("=" * 70)

    # Load data
    gl_path = Path('data/silver/game_level_stats.csv')
    if not gl_path.exists():
        print("ERROR: game_level_stats.csv not found. Run fetch_from_nfldata_api.py first.")
        return

    gl = pd.read_csv(gl_path)
    print(f"✓ Loaded {len(gl):,} game records")

    # Consolidate to player level with canonical positions
    print("  Consolidating player stats...")
    player_stats = load_and_consolidate(gl)
    print(f"  ✓ {len(player_stats):,} eligible players (min {MIN_GAMES} games)")

    # Apply matchup difficulty adjustment
    print("  Applying 2026 matchup adjustments...")
    player_stats = apply_matchup_adjustment(player_stats)

    # Rank and assign draft rounds
    ranked = assign_draft_rounds(player_stats)

    # Fetch and rank DSTs
    print("  Fetching DST rankings...")
    dst_ranked = fetch_dst_rankings()

    if ranked.empty:
        print("No rankings generated.")
        return

    # Save full rankings (players + DSTs)
    output_path = Path('data/gold/draft_rankings.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    out_cols = ['pos_rank', 'player_name', 'team', 'position', 'avg_fp', 'matchup_adj',
                'adjusted_fp', 'games', 'consistency', 'seasons_played',
                'problem_matchup_count', 'draft_round']

    all_ranked = pd.concat(
        [ranked[[c for c in out_cols if c in ranked.columns]],
         dst_ranked[[c for c in out_cols if c in dst_ranked.columns]]],
        ignore_index=True
    )
    all_ranked.to_csv(output_path, index=False)

    # Print roster context header
    print(f"\n{'='*70}")
    print("📋 ROSTER STRUCTURE  (12-team, 15-round PPR draft)")
    print(f"{'='*70}")
    print("  Starters (9):  QB×1  RB×2  WR×2  TE×1  FLEX(RB/WR/TE)×1  K×1  DST×1")
    print("  Bench   (6-7): reserves for injuries, bye weeks")
    print("  Total   (15):  ~60 RBs · ~60 WRs · ~18-24 QBs · ~18-24 TEs · ~12 Ks · ~12 DSTs drafted")
    print(f"  Note: FLEX spot means RBs and WRs have +1 extra starting slot each")

    print(f"\n✅ Draft rankings saved to {output_path}")
    print(f"   {len(all_ranked):,} total ranked entries\n")

    for pos in ['RB', 'WR', 'QB', 'TE', 'DST']:
        pos_df = ranked[ranked['position'] == pos] if pos != 'DST' else dst_ranked
        if pos_df.empty:
            continue
        show = 20 if pos != 'DST' else 32
        print(f"\n{'='*74}")
        print(f"  {pos} RANKINGS  ({'top 20 shown' if pos != 'DST' else 'all 32 teams'})")
        print(f"{'='*74}")
        print(f"{'Rank':<5} {'Team':<5} {'Player':<26} {'Avg FP':>7} {'Adj FP':>7} {'Round':<10} {'Info'}")
        print("-" * 74)
        for _, row in pos_df.head(show).iterrows():
            team = str(row.get('team', '---') or '---')
            problems = f"⚠️ {int(row['problem_matchup_count'])}" if row.get('problem_matchup_count', 0) > 0 else ""
            print(f"{int(row['pos_rank']):<5} {team:<5} {row['player_name']:<26} {row['avg_fp']:>7.1f} {row['adjusted_fp']:>7.1f}   Rd {str(row['draft_round']):<7} {problems}")

    print(f"\n{'='*70}")
    print("Round distribution (across all positions):")
    round_dist = all_ranked[all_ranked['draft_round'] != 'Undrafted']['draft_round'].value_counts().sort_index()
    for round_num, count in round_dist.items():
        bar = '█' * min(count, 40)
        print(f"  Rd {round_num:>2}: {count:>3} players  {bar}")
    undrafted = (all_ranked['draft_round'] == 'Undrafted').sum()
    print(f"\n  Undrafted: {undrafted} players (depth chart, waiver wire)")
    print(f"\n  💡 K: always rounds 13-15 (not ranked here — no player-level kicker data)")
    print(f"  💡 FLEX: consider RBs rd 3-5 or WRs rd 3-4 for your flex slot")


if __name__ == "__main__":
    main()
