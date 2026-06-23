import os
import requests
from dotenv import load_dotenv
import pandas as pd

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
    

# --- silver work starts here ---
df = pd.DataFrame(data)
# Cast the stat column from string to numeric
df["stat"] = pd.to_numeric(df["stat"])
print(df.head())
print("\nShape (rows, columns):", df.shape)
print("\nColumn types:\n", df.dtypes)

# Profiling pass 1 — what stat categories exist, and how common?
# SQL: SELECT category, COUNT(*) FROM t GROUP BY category ORDER BY 2 DESC
print("\n--- categories ---")
print(df["category"].value_counts())

# Profiling pass 2 — what statTypes exist?
# SQL: SELECT statType, COUNT(*) FROM t GROUP BY statType
print("\n--- statTypes ---")
print(df["statType"].value_counts())

# Profiling pass 3 — numeric summary of the stat column
# SQL-ish: MIN, MAX, AVG, plus quartiles — all at once
print("\n--- stat distribution ---")
print(df["stat"].describe())

# Pivot long → wide
# index = row identity (your "in a row" columns)
# columns = statType (becomes the new column headers)
# values = stat (fills the cells)
wide = df.pivot_table(
    index=["season", "playerId", "player", "position", "team", "conference", "category"],
    columns="statType",
    values="stat"
)

print(wide.head())
print("\nShape:", wide.shape)