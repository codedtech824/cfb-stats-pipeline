"""Test nfldata.org API to see response format."""
import requests
import json

base_url = 'https://api.nfldata.org/v1'

print('Testing nfldata.org API endpoints...\n')

# Test /games endpoint
print('1. Testing /games endpoint:')
try:
    resp = requests.get(f'{base_url}/games?season=2022&limit=5', timeout=10)
    print(f'   Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   Response type: {type(data).__name__}')
        if isinstance(data, dict):
            print(f'   Keys: {list(data.keys())}')
        elif isinstance(data, list):
            print(f'   List length: {len(data)}')
            if data:
                print(f'   First item keys: {list(data[0].keys())[:10]}')
        print(f'   Full response (first 500 chars):\n{str(data)[:500]}')
except Exception as e:
    print(f'   Error: {e}')

# Test /stats/passing endpoint
print('\n2. Testing /stats/passing endpoint:')
try:
    resp = requests.get(f'{base_url}/stats/passing?season=2022&limit=3', timeout=10)
    print(f'   Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'   Response type: {type(data).__name__}')
        if isinstance(data, dict):
            print(f'   Keys: {list(data.keys())}')
        elif isinstance(data, list):
            print(f'   List length: {len(data)}')
            if data:
                print(f'   First item:\n{json.dumps(data[0], indent=2)[:400]}')
        print(f'   Full response (first 500 chars):\n{str(data)[:500]}')
except Exception as e:
    print(f'   Error: {e}')

# Test /meta endpoint
print('\n3. Testing /meta endpoint:')
try:
    resp = requests.get(f'{base_url}/meta', timeout=10)
    print(f'   Status: {resp.status_code}')
    data = resp.json()
    print(f'   Response:\n{json.dumps(data, indent=2)[:500]}')
except Exception as e:
    print(f'   Error: {e}')

# Test /health endpoint
print('\n4. Testing /health endpoint:')
try:
    resp = requests.get(f'{base_url}/health', timeout=10)
    print(f'   Status: {resp.status_code}')
    data = resp.json()
    print(f'   Response:\n{json.dumps(data, indent=2)}')
except Exception as e:
    print(f'   Error: {e}')
