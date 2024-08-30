import re
import time
from io import StringIO

import pandas as pd
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import setup_driver


def extract_tournament_id(url):
    match = re.search(r"/tournamentId/(\d+)", url)
    if match:
        tournament_id = match.group(1)
        print(f"Extracted Tournament ID: {tournament_id}")
        return tournament_id
    else:
        print("Tournament ID not found in URL")
        return None


def scrape_leaderboard(url):
    driver = setup_driver()
    try:
        print(f"Loading URL: {url}")
        driver.get(url)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".Table__TBODY"))
            )
        except TimeoutException:
            print(f"Timeout waiting for table to load for URL: {url}")
            return None

        # Add a small delay to ensure the page is fully loaded
        time.sleep(2)

        html = driver.page_source

        tables = pd.read_html(StringIO(html))

        if not tables:
            print(f"No tables found in the HTML for URL: {url}")
            return None

        # Function to check if a table is a playoff table
        def is_playoff_table(df):
            return any("Playoff Results" in str(col) for col in df.columns)

        # Find the main leaderboard table
        leaderboard_df = None
        for table in tables:
            if not is_playoff_table(table):
                leaderboard_df = table
                break

        if leaderboard_df is None:
            print("No main leaderboard table found")
            return None

        print(f"Raw leaderboard data shape: {leaderboard_df.shape}")
        print(f"Raw leaderboard columns: {leaderboard_df.columns.tolist()}")

        # If the leaderboard has multi-index columns, flatten them
        if isinstance(leaderboard_df.columns, pd.MultiIndex):
            leaderboard_df.columns = [
                " ".join(col).strip() for col in leaderboard_df.columns.values
            ]

        # Standardize column names
        leaderboard_df.columns = leaderboard_df.columns.str.upper()
        leaderboard_df = leaderboard_df.loc[
            :, ~leaderboard_df.columns.str.contains("^UNNAMED")
        ]

        if "POS" in leaderboard_df.columns:
            pos_column = leaderboard_df["POS"]
            leaderboard_df = leaderboard_df.drop("POS", axis=1)
            leaderboard_df.insert(0, "POS", pos_column)

        tournament_id = extract_tournament_id(url)
        leaderboard_df["TOURNAMENT_ID"] = tournament_id

        print(f"Final leaderboard data shape: {leaderboard_df.shape}")
        print(f"Final leaderboard columns: {leaderboard_df.columns.tolist()}")

        return leaderboard_df

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

    finally:
        driver.quit()


def clean_leaderboard_data(df, tournament_id):
    if df is None:
        return None, None

    print("Available columns:", df.columns.tolist())

    # Detect TEAM and numbered columns
    extra_columns = [col for col in df.columns if col == "TEAM" or col.isdigit()]

    # If extra columns are found, return their information
    extra_column_info = (
        {"tournament_id": tournament_id, "extra_columns": ", ".join(extra_columns)}
        if extra_columns
        else None
    )

    # The rest of the cleaning process remains the same, but we don't remove any columns
    if "SCORE" in df.columns:
        df["SCORE"] = df["SCORE"].replace({"E": "0", "CUT": None, "WD": None})
        df["SCORE"] = pd.to_numeric(df["SCORE"], errors="coerce")

    for round in ["R1", "R2", "R3", "R4"]:
        if round in df.columns:
            df[round] = pd.to_numeric(df[round], errors="coerce")

    if "EARNINGS" in df.columns:
        df["EARNINGS"] = df["EARNINGS"].replace("--", "0")
        df["EARNINGS"] = (
            df["EARNINGS"].str.replace("$", "").str.replace(",", "").astype(float)
        )

    if "FEDEX PTS" in df.columns:
        df["FEDEX PTS"] = pd.to_numeric(df["FEDEX PTS"], errors="coerce")

    return df, extra_column_info


def load_tournament_info(csv_file):
    df = pd.read_csv(csv_file)
    print(f"Original DataFrame shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Data types: \n{df.dtypes}")

    # Remove rows with missing Tournament ID
    df = df.dropna(subset=["Tournament ID"])

    # Convert Tournament ID to integer
    df["Tournament ID"] = df["Tournament ID"].astype(int)

    print(f"Cleaned DataFrame shape: {df.shape}")

    unique_ids = df["Tournament ID"].nunique()
    total_ids = len(df["Tournament ID"])
    print(f"Unique Tournament IDs: {unique_ids} out of {total_ids} total")

    return df


def generate_urls(tournament_info):
    base_url = "https://www.espn.com/golf/leaderboard/_/tournamentId/"
    return [f"{base_url}{int(tid)}" for tid in tournament_info["Tournament ID"]]


def main():
    tournament_info = load_tournament_info("data/tournament_info.csv")

    tournament_urls = generate_urls(tournament_info)

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


if __name__ == "__main__":
    main()
