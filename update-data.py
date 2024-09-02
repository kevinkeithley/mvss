import os

import pandas as pd

from utils.date_utils import extract_and_format_end_date
from utils.tournament_utils import (
    clean_leaderboard_data,
    extract_tournament_id,
    generate_urls,
    scrape_leaderboard,
    scrape_tournament_info,
    setup_driver,
)


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
    df["End Date"] = pd.to_datetime(df["End Date"], errors="coerce")
    df = df.sort_values("End Date", ascending=False)

    # Save the updated DataFrame to CSV
    df.to_csv(output_file, index=False)

    print(f"Added {len(new_tournaments)} new tournaments to {output_file}")


if __name__ == "__main__":

    # Tournament IDs to add
    tournament_ids_to_update = ["401580365"]

    # Add tournament metadata to tournament_info.csv
    update_tournament_info(tournament_ids_to_update)

    # Add leaderboard data
    tournament_urls = generate_urls(tournament_ids_to_update)

    all_leaderboards = []
    failed_tournament_ids = []
    extra_column_data = []  # List to store information about extra columns

    for url in tournament_urls:
        print(f"Scraping tournament: {url}")
        tournament_id = extract_tournament_id(url)
        leaderboard_df = scrape_leaderboard(url)
        if leaderboard_df is not None:
            leaderboard_df, extra_info = clean_leaderboard_data(
                leaderboard_df, tournament_id
            )
            if extra_info:
                extra_column_data.append(extra_info)
            if leaderboard_df is not None:
                all_leaderboards.append(leaderboard_df)
            else:
                failed_tournament_ids.append(tournament_id)
                print(f"Failed to clean data for tournament ID: {tournament_id}")
        else:
            failed_tournament_ids.append(tournament_id)
            print(f"Failed to scrape data for tournament ID: {tournament_id}")

    if all_leaderboards:
        combined_leaderboard = pd.concat(all_leaderboards, ignore_index=True)

        print(combined_leaderboard.head())
        print(combined_leaderboard.info())

        db_name = "leaderboards_data.csv"
        combined_leaderboard.to_csv(f"data/{db_name}", index=False)
        print(f"Combined leaderboard data saved to {db_name}")
    else:
        print("No leaderboard data was successfully scraped.")

    # Save failed tournament IDs to a CSV file
    if failed_tournament_ids:
        failed_df = pd.DataFrame({"Failed_Tournament_ID": failed_tournament_ids})
        failed_df.to_csv("data/failed_tournament_ids.csv", index=False)
        print(
            f"Failed tournament IDs saved to failed_tournament_ids.csv. Total failed: {len(failed_tournament_ids)}"
        )
    else:
        print("All tournaments were successfully scraped.")

    # Save information about tournaments with extra columns
    if extra_column_data:
        extra_column_df = pd.DataFrame(extra_column_data)
        extra_column_df.to_csv("data/extra_column_tournaments.csv", index=False)
        print(
            f"Information about tournaments with extra columns saved to extra_column_tournaments.csv. Total: {len(extra_column_data)}"
        )
    else:
        print("No tournaments with extra columns detected.")
