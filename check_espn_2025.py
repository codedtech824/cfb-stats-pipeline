"""Test ESPN for 2025 NFL player stats availability."""
import requests
import json
from urllib.parse import quote

print("Testing ESPN data sources for 2025 stats...\n")

# Test 1: ESPN API for NFL stats
print("1. ESPN NFL Stats API:")
try:
    # Try ESPN's stats endpoint
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/statistics"
    resp = requests.get(url, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Available: Yes")
except Exception as e:
    print(f"   Error: {str(e)[:50]}")

# Test 2: ESPN Fantasy API (has player stats)
print("\n2. ESPN Fantasy Football Player Stats:")
try:
    # Fantasy API typically has current season data
    url = "https://lm-api-reads.espn.com/lm-api-reads/v1/nfl?seasonId=2025"
    resp = requests.get(url, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   Available: Yes (2025 found)")
    elif resp.status_code == 404:
        print(f"   Available: No (404 - not found)")
except Exception as e:
    print(f"   Error: {str(e)[:50]}")

# Test 3: ESPN player stats pages (public)
print("\n3. ESPN Public Player Stats Pages:")
players = [
    "Patrick Mahomes",
    "Travis Kelce",
    "Josh Allen"
]

for player in players:
    try:
        # Try searching ESPN for player
        search_url = f"https://www.espn.com/search?query={quote(player)} nfl stats"
        resp = requests.head(search_url, timeout=10, allow_redirects=True)
        print(f"   {player}: Status {resp.status_code}")
    except Exception as e:
        print(f"   {player}: Error {str(e)[:20]}")

# Test 4: ProFootballReference (often has up-to-date stats)
print("\n4. Pro Football Reference (PFR) 2025:")
try:
    url = "https://www.pro-football-reference.com/years/2025/passing.htm"
    resp = requests.head(url, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   Available: Yes")
    elif resp.status_code == 404:
        print(f"   Available: No (404)")
except Exception as e:
    print(f"   Error: {str(e)[:50]}")

# Test 5: NFL.com official stats
print("\n5. NFL.com Official Stats 2025:")
try:
    url = "https://www.nfl.com/stats/player-stats/offense/passing/2025/regular"
    resp = requests.head(url, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   Available: Yes")
    elif resp.status_code == 404:
        print(f"   Available: No")
except Exception as e:
    print(f"   Error: {str(e)[:50]}")

# Test 6: Check if there's a sports-reference API
print("\n6. Sports Data APIs:")
apis = [
    ("SportsData.io", "https://api.sportsdata.io/v3/nfl/stats/json/Player2025"),
    ("Rapid API", "https://api-football.p.rapidapi.com/fixtures"),
]

for name, url in apis:
    try:
        resp = requests.head(url, timeout=10)
        print(f"   {name}: Status {resp.status_code}")
    except Exception as e:
        print(f"   {name}: Error")

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
print("✓ ESPN Fantasy API - Check if seasonId=2025 works")
print("✓ Pro Football Reference - Likely has current season")
print("✓ NFL.com - Official source, should have 2025")
print("✓ nfldata.org - May update as season progresses")
print("\nNote: 2025 season just started (Sept 1, 2026)")
print("Stats are being updated in real-time but may be incomplete")
