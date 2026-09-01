import pandas as pd
gl = pd.read_csv('data/silver/game_level_stats.csv')
print('Seasons in data:', sorted(gl['season'].unique()))
print('Max season:', gl['season'].max())
print()
for player in ['Derrick Henry', 'Josh Allen', 'Christian McCaffrey', 'Saquon Barkley', 'Patrick Mahomes']:
    rows = gl[gl['player_name'] == player][['season','week','team']].sort_values(['season','week'])
    seasons = rows.drop_duplicates(['season','team'])[['season','team']].to_dict('records')
    latest = rows.iloc[-1] if len(rows) > 0 else None
    print(f'{player}: seasons={seasons}  -> latest entry: season={latest["season"] if latest is not None else "N/A"} team={latest["team"] if latest is not None else "N/A"}')
