import os

import pandas as pd

from utils.date_utils import extract_and_format_end_date
from utils.tournament_utils import scrape_tournament_info, setup_driver


def update_tournament_info(tournament_ids, data_directory="data"):
    output_file = f"{data_directory}/tournament_info.csv"
    existing_tournaments = set()

    # Read existing tournaments if file exists
    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
        existing_tournaments = set(df["Tournament ID"].astype(str))
    else:
        df = pd.DataFrame()

    driver = setup_driver()

    new_tournaments = []
    for tournament_id in tournament_ids:
        if str(tournament_id) in existing_tournaments:
            print(f"Tournament ID {tournament_id} already exists. Skipping.")
            continue

        url = f"https://www.espn.com/golf/leaderboard/_/tournamentId/{tournament_id}"
        print(f"Scraping: {url}")

        info = scrape_tournament_info(driver, url)
        info["Tournament ID"] = tournament_id
        info["Year"] = info.get("Date", "").split()[-1]  # Extract year from date
        info["End Date"] = extract_and_format_end_date(info.get("Date", ""))

        new_tournaments.append(info)
        print(f"Scraped: {info.get('Tournament name', 'Unknown tournament')}")

    driver.quit()

    # Convert new tournaments to DataFrame
    new_df = pd.DataFrame(new_tournaments)

    # Combine existing and new data
    df = pd.concat([df, new_df], ignore_index=True)

    # Ensure all columns are present
    columns = [
        "Tournament ID",
        "Year",
        "Tournament name",
        "Date",
        "End Date",
        "Location",
        "Par",
        "Yards",
        "Purse",
    ]
    for col in columns:
        if col not in df.columns:
            df[col] = None

    # Sort the DataFrame by Date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values("Date", ascending=False)

    # Save the updated DataFrame to CSV
    df.to_csv(output_file, index=False)

    print(f"Added {len(new_tournaments)} new tournaments to {output_file}")

    # Print unique date formats for manual verification
    print("\nUnique date formats in the dataset:")
    print(df["Date"].unique())


# Example usage
if __name__ == "__main__":
    tournament_ids_to_update = ["401580365"]
    update_tournament_info(tournament_ids_to_update)
