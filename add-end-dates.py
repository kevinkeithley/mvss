import pandas as pd

from utils import extract_and_format_end_date

# Load the CSV data
df = pd.read_csv("data/tournament_info.csv")

# Apply the function to create the new 'End Date' column
df["End Date"] = df["Date"].apply(extract_and_format_end_date)

# Display the first few rows of the updated dataframe
print(df[["Tournament name", "Date", "End Date"]].head(10))

# Print rows where 'End Date' is None (if any)
null_end_dates = df[df["End Date"].isnull()]
if not null_end_dates.empty:
    print("\nRows where 'End Date' is None:")
    print(null_end_dates[["Tournament name", "Date", "End Date"]])
else:
    print("\nAll dates were successfully parsed.")

# Save the updated dataframe to a new CSV file
df.to_csv("data/tournament_info.csv", index=False)

print("\nUpdated CSV has been saved as 'data/tournament_info.csv'")

# Print unique date formats for manual verification
print("\nUnique date formats in the dataset:")
print(df["Date"].unique())
