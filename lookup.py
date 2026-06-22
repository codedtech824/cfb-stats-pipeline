import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("CFBD_API_KEY")

url = "https://api.collegefootballdata.com/stats/player/season"
params = {"year": 2023, "team": "USC"}
headers = {"Authorization": f"Bearer {api_key}"}

# LAYER 1: connection — wrap the call so a network failure doesn't crash us
try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
except requests.exceptions.RequestException as e:
    print("Request failed to complete:", e)
    exit()

# LAYER 2: HTTP status — did the server say yes?
if response.status_code != 200:
    print(f"Server returned an error: {response.status_code}")
    exit()

data = response.json()

# LAYER 3: data — did we actually get anything usable?
if len(data) == 0:
    print("Request succeeded but returned no records — check your filters.")
    exit()

# Happy path — filter to one player
player_name = "Justin Dedich"
player_rows = [row for row in data if row["player"] == player_name]

if len(player_rows) == 0:
    print(f"No rows found for {player_name} — name may be misspelled or not on this team.")
    exit()

print(f"Rows for {player_name}: {len(player_rows)}")
for row in player_rows:
    print(f"  {row['category']} / {row['statType']} = {row['stat']}")