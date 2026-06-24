import os
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
api_key = os.getenv("CFBD_API_KEY")


def get_team_stats(team, year):
    """Fetch season player stats for one team/year. Returns a list of dicts, or None on failure."""
    url = "https://api.collegefootballdata.com/stats/player/season"
    params = {"year": year, "team": team}
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {team} {year}: {e}")
        return None

    if response.status_code != 200:
        print(f"Server error for {team} {year}: {response.status_code}")
        return None

    data = response.json()

    if len(data) == 0:
        print(f"No records for {team} {year} — check filters.")
        return None

    return data

# Pull several teams, stack them into one dataset
teams = ["USC", "Oregon", "Michigan", "Alabama", "Georgia"]
all_data = []

for team in teams:
    data = get_team_stats(team, 2023)
    if data is None:          # failure signal — skip this team, keep going
        continue
    all_data.extend(data)     # add this team's records to the pile

print(f"\nTotal records across {len(teams)} teams: {len(all_data)}")

df = pd.DataFrame(all_data)
print("Teams actually pulled:", df["team"].unique())