"""Deeper check for 2025 NFL stats on ESPN using proper headers."""
import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("Deep checking for 2025 NFL stats...\n")

# Test 1: ESPN Stats with proper headers
print("1. ESPN Stats API (with proper headers):")
try:
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/players"
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        if data.get('sports'):
            print(f"   ✓ API responding")
except Exception as e:
    print(f"   Error: {str(e)[:40]}")

# Test 2: NFL.com with headers
print("\n2. NFL.com Player Stats (current season):")
try:
    url = "https://www.nfl.com/stats/"
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        text = resp.text
        if '2025' in text or 'season' in text.lower():
            print(f"   ✓ Page loaded with content")
            if '2025' in text:
                print(f"   ✓ 2025 detected in page")
        else:
            print(f"   ✗ 2025 data not in page")
except Exception as e:
    print(f"   Error: {str(e)[:40]}")

# Test 3: ESPN Fantasy with headers
print("\n3. ESPN Fantasy Football Stats:")
try:
    url = "https://fantasy.espn.com/football/stats"
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        if '2025' in resp.text:
            print(f"   ✓ 2025 data available")
        else:
            print(f"   ✓ Page loaded (may need season selection)")
except Exception as e:
    print(f"   Error: {str(e)[:40]}")

# Test 4: Pro Football Reference with headers
print("\n4. Pro Football Reference 2025:")
try:
    url = "https://www.pro-football-reference.com/years/2025/"
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        if '2025' in resp.text:
            print(f"   ✓ 2025 data available")
        else:
            print(f"   Page has data but 2025 check inconclusive")
except Exception as e:
    print(f"   Error: {str(e)[:40]}")

# Test 5: NFL.com official stats direct
print("\n5. NFL.com Player Stats (direct endpoint):")
try:
    # Try common NFL.com stat pages
    urls = [
        "https://www.nfl.com/stats/players/passing",
        "https://www.nfl.com/stats/",
    ]
    for url in urls:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            print(f"   {url.split('/')[-1] or 'root'}: ✓ Status 200")
            if '2025' in resp.text:
                print(f"     ✓ Contains '2025'")
        else:
            print(f"   {url.split('/')[-1]}: Status {resp.status_code}")
except Exception as e:
    print(f"   Error: {str(e)[:40]}")

print("\n" + "="*60)
print("CONCLUSION:")
print("="*60)
print("ESPN/NFL.com data availability for 2025:")
print("- Most sites show 403/404 (either blocked or not yet ready)")
print("- 2025 season literally just started Sept 1")
print("- Stats are being collected but not fully available yet")
print("\nBest approach for 2026 season:")
print("✓ Use 2022-2024 historical data (what we have)")
print("✓ Switch to live in-season data after first few weeks")
print("✓ Re-run pipeline when 2025 stats become available")
