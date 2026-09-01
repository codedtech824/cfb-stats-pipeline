"""Inspect nflverse 2026 roster CSV."""
import requests, io
import pandas as pd

url = 'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2026.csv'
resp = requests.get(url, timeout=30)
df = pd.read_csv(io.StringIO(resp.text))

print(f'Shape: {df.shape}')
print(f'Columns: {list(df.columns)}')
print()
print(df.head(3).to_string())
print()
name_cols = [c for c in df.columns if any(k in c.lower() for k in ['name', 'team', 'pos', 'abbr'])]
print(f'Key cols: {name_cols}')
print()
for player in ['Patrick Mahomes', 'Josh Allen', 'Derrick Henry', 'Saquon Barkley', 'Jayden Daniels']:
    rows = df[df.apply(lambda r: player.lower() in str(r.values).lower(), axis=1)]
    if not rows.empty:
        r = rows.iloc[0]
        team = r.get('team', r.get('team_abbr', '?'))
        pos = r.get('position', r.get('pos', '?'))
        full = r.get('full_name', r.get('player_name', r.get('display_name', '?')))
        print(f'{player}: full_name={full}, team={team}, pos={pos}')
    else:
        print(f'{player}: NOT FOUND')


print('=== nflverse GitHub rosters for 2026 ===')
urls = [
    'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2026.csv',
    'https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_week_1_2026.csv',
    'https://github.com/nflverse/nflverse-data/releases/download/rosters/rosters_2026.csv',
]
for url in urls:
    try:
        resp = requests.head(url, timeout=15, allow_redirects=True)
        size = int(resp.headers.get('Content-Length', 0))
        print(f'  {url.split("/")[-1]}: {resp.status_code} ({size/1024:.0f} KB)')
    except Exception as e:
        print(f'  Error: {str(e)[:40]}')

print()
print('=== ESPN roster API ===')
teams = ['KC', 'BUF', 'PHI']
for team in teams:
    try:
        url = f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team}/roster'
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            athletes = data.get('athletes', [])
            total = sum(len(g.get('items', [])) for g in athletes)
            print(f'  {team}: {total} players')
            if athletes and athletes[0].get('items'):
                p = athletes[0]['items'][0]
                print(f'    Sample: {p.get("displayName")} pos={p.get("position", {}).get("abbreviation")}')
        else:
            print(f'  {team}: {resp.status_code}')
    except Exception as e:
        print(f'  {team}: Error {str(e)[:40]}')

print()
print('=== nfldata.org /players/{gsis_id}/stats for 2026 ===')
base = 'https://api.nfldata.org/v1'
# Try a known player (Patrick Mahomes gsis_id)
try:
    resp = requests.get(f'{base}/players', params={'limit': 500}, timeout=30)
    data = resp.json()
    players = data.get('data', [])
    # Find Mahomes
    mahomes = next((p for p in players if 'Mahomes' in p.get('display_name', '')), None)
    if mahomes:
        print(f'  Found: {mahomes}')
except Exception as e:
    print(f'  Error: {str(e)[:40]}')


