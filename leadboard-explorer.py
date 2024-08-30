import pandas as pd

# Read in Tournament info data from data folder
df = pd.read_csv("data/tournament_info.csv")

# Find rows with non-unique Tournament IDs
non_unique_ids = df[df.duplicated("Tournament ID", keep=False)]

# Group by Tournament ID and count occurrences
id_counts = non_unique_ids["Tournament ID"].value_counts()

print(f"Non-unique Tournament ID count: {id_counts}")

print("\nDetailed information for non-unique Tournament IDs:")
for tournament_id in id_counts.index:
    print(f"\nTournament ID: {tournament_id}")
    print(
        non_unique_ids[non_unique_ids["Tournament ID"] == tournament_id][
            ["Year", "Tournament name", "Date", "Location"]
        ].to_string(index=False)
    )
