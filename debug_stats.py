"""Debug stats endpoints."""
import requests
import json

base_url = 'https://api.nfldata.org/v1'

for season in [2022, 2023, 2024]:
    print(f'\nSeason {season}:')
    
    for endpoint in ['/stats/passing', '/stats/receiving', '/stats/rushing']:
        url = f"{base_url}{endpoint}"
        params = {'season': season, 'limit': 5}
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            print(f'  {endpoint}: status={resp.status_code}, total={data.get("total")}, got {len(data.get("data", []))} records')
            
            if data.get('data'):
                # Check fields
                first = data['data'][0]
                has_team = 'recent_team' in first or 'team' in first
                has_week = 'week' in first
                has_fp = 'fantasy_points' in first
                print(f'    Has team: {has_team}, week: {has_week}, fantasy_points: {has_fp}')
        except Exception as e:
            print(f'  {endpoint}: ERROR - {e}')
