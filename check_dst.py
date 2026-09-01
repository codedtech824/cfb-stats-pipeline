"""Check DST data availability."""
import requests, json

base = 'https://api.nfldata.org/v1'

print('=== /stats/team for 2024 ===')
resp = requests.get(f'{base}/stats/team', params={'season': 2024, 'limit': 3})
data = resp.json()
records = data.get('data', [])
print(f'Total: {data.get("total")}, status: {resp.status_code}, got: {len(records)}')
if records:
    print('Keys:', list(records[0].keys()))
    print('Sample:', json.dumps(records[0], indent=2)[:800])

print()
print('=== /games regular season sample ===')
resp = requests.get(f'{base}/games', params={'season': 2024, 'limit': 3})
data = resp.json()
records = data.get('data', [])
if records:
    g = records[0]
    print('Game keys:', list(g.keys()))
    print('Sample:', json.dumps(g, indent=2)[:500])

print()
print('=== /stats/advanced/defense for 2024 ===')
resp = requests.get(f'{base}/stats/advanced/defense', params={'season': 2024, 'limit': 3})
data = resp.json()
records = data.get('data', [])
print(f'Total: {data.get("total")}, got: {len(records)}')
if records:
    print('Keys:', list(records[0].keys()))
    print('Sample:', json.dumps(records[0], indent=2)[:500])
