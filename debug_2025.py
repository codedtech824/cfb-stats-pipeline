"""Check what 2025 data looks like in the working endpoints."""
import requests

base = 'https://api.nfldata.org/v1'

# Check /stats/season for 2025
print('=== /stats/season for 2025 ===')
resp = requests.get(f'{base}/stats/season', params={'season': 2025}, timeout=10)
data = resp.json()
records = data.get('data', [])
print(f'Total: {data.get("total")}, Got: {len(records)}')
if records:
    r = records[0]
    print(f'All keys: {list(r.keys())}')
    name = r.get("player_name") or r.get("player_display_name")
    fp = r.get("fantasy_points")
    team = r.get("team") or r.get("recent_team")
    print(f'Sample: player={name}, season={r.get("season")}, team={team}, fp={fp}')

# Check /stats/ngs/passing (has week-level data)
print()
print('=== /stats/ngs/passing for 2025 ===')
resp = requests.get(f'{base}/stats/ngs/passing', params={'season': 2025}, timeout=10)
data = resp.json()
records = data.get('data', [])
print(f'Total: {data.get("total")}, Got: {len(records)}')
if records:
    r = records[0]
    print(f'All keys: {list(r.keys())}')
    name = r.get("player_display_name")
    week = r.get("week")
    team = r.get("team_abbr")
    print(f'Sample: player={name}, season={r.get("season")}, week={week}, team={team}')
    print(f'  Has fantasy_points: {"fantasy_points" in r}')
    print(f'  Has attempts/yards/tds: {"attempts" in r}, {"passing_yards" in r or "pass_yards" in r}, {"pass_touchdowns" in r}')

# Check nflverse play-by-play - can we derive player stats from it?
print()
print('=== nflverse play_by_play_2025.csv (checking size) ===')
import urllib.request
url = 'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2025.csv'
try:
    req = urllib.request.Request(url, method='HEAD')
    with urllib.request.urlopen(req) as resp2:
        size_mb = int(resp2.headers.get('Content-Length', 0)) / 1024 / 1024
        print(f'File exists: YES, size={size_mb:.1f} MB')
except Exception as e:
    print(f'Error: {e}')


