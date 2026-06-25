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

# Cast and pivot — same silver moves, now on 5 teams
df["stat"] = pd.to_numeric(df["stat"])

wide = df.pivot_table(
    index=["season", "playerId", "player", "position", "team", "conference", "category"],
    columns="statType",
    values="stat"
)

print("Wide shape:", wide.shape)

# Reset index so position and category become regular columns we can group on
flat = wide.reset_index()

# For each category, how many rows, and how many have a TD value vs NaN?
print("\n--- TD presence by category ---")
print(flat.groupby("category")["TD"].agg(["count", "size"]))

# Create a silver output folder if it doesn't exist
os.makedirs("data/silver", exist_ok=True)

# Persist the clean wide DataFrame — flatten the index first so it saves cleanly
flat = wide.reset_index()
output_path = "data/silver/player_stats_wide.parquet"
flat.to_parquet(output_path, index=False)

print(f"\nSilver artifact written: {output_path}")
print(f"Rows: {len(flat)}, Columns: {len(flat.columns)}")

# Round-trip verification — read it back as a fresh consumer would
print("\n--- Round-trip check ---")
reloaded = pd.read_parquet("data/silver/player_stats_wide.parquet")
print("Reloaded shape:", reloaded.shape)
print("\nStat column dtype (should be float64):", reloaded["TD"].dtype)
print("\nNaN still present?", reloaded["TD"].isna().sum(), "NaN values in TD")