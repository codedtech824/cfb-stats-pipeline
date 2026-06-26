import pandas as pd


def top_players_by_stat(category, stat, n=10):
    """Return the top N players in a category, ranked by a given stat.
    Reads the silver artifact; returns a DataFrame."""
    silver = pd.read_parquet("data/silver/player_stats_wide.parquet")

    # Guard: is the requested stat actually a column?
    if stat not in silver.columns:
        print(f"'{stat}' is not a valid stat. Available stats: {sorted(silver.columns)}")
        return None

    # Guard: does the category exist?
    if category not in silver["category"].unique():
        print(f"'{category}' is not a valid category. Available: {sorted(silver['category'].unique())}")
        return None

    # Filter to one category so we compare like with like
    subset = silver[silver["category"] == category]

    # Rank by the chosen stat, descending, take top N
    ranked = subset.sort_values(stat, ascending=False).head(n)

    # Return identity columns + the ranked stat
    return ranked[["player", "team", "position", stat]]

# Test it on a few different questions
print("--- Top 5 Rushers by YDS ---")
print(top_players_by_stat("rushing", "YDS", 5))

print("\n--- Top 5 Receivers by TD ---")
print(top_players_by_stat("receiving", "TD", 5))

print("\n--- Top 5 Passers by YDS ---")
print(top_players_by_stat("passing", "YDS", 5))

print("\n--- Testing a bad stat name ---")
result = top_players_by_stat("rushing", "TOUCHDOWNS", 5)
print("Returned:", result)

