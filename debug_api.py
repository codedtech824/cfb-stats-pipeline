"""Debug nfldata.org API responses in detail."""
import requests
import json
import pandas as pd

base_url = 'https://api.nfldata.org/v1'

# Test passing stats
print('Fetching passing stats for 2022...')
resp = requests.get(f'{base_url}/stats/passing?season=2022&limit=10')
print(f'Status: {resp.status_code}')
data = resp.json()

print(f'Response keys: {data.keys()}')
print(f'Total records: {data.get("total")}')
print(f'Data length: {len(data.get("data", []))}')

if data.get('data'):
    print(f'\nFirst record:')
    print(json.dumps(data['data'][0], indent=2))
    
    # Try to build DataFrame
    df = pd.DataFrame(data['data'])
    print(f'\nDataFrame shape: {df.shape}')
    print(f'Columns: {list(df.columns)}')
    print(f'\nFirst few rows:')
    print(df.head(3))
    
    # Check key fields
    print(f'\nSample data:')
    print(df[['player_name', 'season', 'week', 'recent_team', 'fantasy_points']].head(5))
