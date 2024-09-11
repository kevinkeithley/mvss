import csv
import os
import time
from datetime import datetime
from io import StringIO

import pandas as pd
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import (
    extract_tournament_id,
    generate_urls,
    identify_csv_files_for_rescrape,
    setup_driver,
)


def wait_for_table_data(driver, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        table = driver.find_elements(By.TAG_NAME, "table")
        if table:
            rows = table[0].find_elements(By.TAG_NAME, "tr")
            if len(rows) > 1:  # Check if there's more than just the header row
                return True
        time.sleep(0.5)  # Short sleep to prevent excessive CPU usage
    return False


def scrape_player_stats(urls, headless=True, additional_options=None):
    """
    Scrape player stats from given URLs.
    Args:
    urls (list): List of URLs to scrape.
    headless (bool): Whether to run the browser in headless mode.
    additional_options (list): Additional Chrome options.
    Returns:
    dict: A dictionary with tournament IDs as keys and DataFrames of player stats as values.
    """
    driver = setup_driver(headless=headless, additional_options=additional_options)
    tournaments_without_stats = []
    all_tournament_stats = {}

    try:
        for url in urls:
            try:
                print(f"Loading URL: {url}")
                driver.get(url)
                tournament_id = extract_tournament_id(url)
                print(f"Processing tournament ID: {tournament_id}")

                try:
                    # Wait for and click the Player Stats button
                    player_stats_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Player Stats')]")
                        )
                    )
                    player_stats_button.click()
                    print("Clicked Player Stats button")

                    # Wait for the table data to load
                    if wait_for_table_data(driver):
                        print("Player Stats data loaded successfully")
                        html = driver.page_source
                        tables = pd.read_html(StringIO(html))

                        if tables:
                            stats_df = tables[
                                -1
                            ]  # Assuming the main stats table is the last one
                            all_tournament_stats[tournament_id] = stats_df
                            print(
                                f"Successfully scraped Player Stats data for tournament ID: {tournament_id}"
                            )
                        else:
                            raise Exception("No tables found in Player Stats")
                    else:
                        raise TimeoutException(
                            "Timed out waiting for Player Stats data to load"
                        )

                except TimeoutException as e:
                    print(f"Timeout error for tournament {tournament_id}: {str(e)}")
                    tournaments_without_stats.append(
                        {
                            "url": url,
                            "tournament_id": tournament_id,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "reason": str(e),
                        }
                    )

            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                tournaments_without_stats.append(
                    {
                        "url": url,
                        "tournament_id": tournament_id,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": str(e),
                    }
                )

    finally:
        driver.quit()

    # Save information about tournaments without player stats
    save_tournaments_without_stats(tournaments_without_stats)

    return all_tournament_stats


def save_tournaments_without_stats(
    tournaments_without_stats, filename="tournaments_without_player_stats.csv"
):
    """
    Save information about tournaments without player stats to a CSV file.
    Args:
    tournaments_without_stats (list): List of dictionaries containing tournament information.
    filename (str): Name of the CSV file to save.
    """
    if tournaments_without_stats:
        with open(filename, "w", newline="") as csvfile:
            fieldnames = ["url", "tournament_id", "timestamp", "reason"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for tournament in tournaments_without_stats:
                writer.writerow(tournament)
        print(f"Information about tournaments without player stats saved to {filename}")
    else:
        print("All tournaments had player stats available.")


# def main():
#     # Path to the tournament info CSV file
#     tournament_info_path = os.path.join("data", "tournament_info.csv")

#     # Read the CSV file
#     df = pd.read_csv(tournament_info_path)

#     # Extract tournament IDs from the DataFrame
#     # Assuming the column name is 'Tournament ID'. Adjust if it's different.
#     tournament_ids = df["Tournament ID"].tolist()

#     print(f"Loaded {len(tournament_ids)} tournament IDs from {tournament_info_path}")

#     # Generate URLs for all tournament IDs
#     tournament_ids = "401353214"
#     tournament_urls = generate_urls(tournament_ids)

#     # Run in non-headless mode with a maximized window for debugging
#     all_tournament_stats = scrape_player_stats(
#         tournament_urls, headless=True, additional_options=["--start-maximized"]
#     )

#     # Define the base directory and create the folder structure for saving results
#     base_dir = "data"
#     player_stats_dir = os.path.join(base_dir, "player-stats")
#     os.makedirs(player_stats_dir, exist_ok=True)

#     # Process and save the scraped data
#     for tournament_id, stats_df in all_tournament_stats.items():
#         print(f"Saving data for tournament ID: {tournament_id}")
#         file_path = os.path.join(player_stats_dir, f"player_stats_{tournament_id}.csv")
#         stats_df.to_csv(file_path, index=False)
#         print(f"Saved to: {file_path}")


# if __name__ == "__main__":
#     main()


def main():
    # Path to the player stats directory
    player_stats_dir = os.path.join("data", "player-stats")

    # Identify CSV files that need to be rescraped
    files_to_rescrape = identify_csv_files_for_rescrape(player_stats_dir)

    if not files_to_rescrape:
        print("No files need to be rescraped. All data appears to be valid.")
        return

    # Extract tournament IDs from the files that need to be rescraped
    tournament_ids_to_rescrape = [
        extract_tournament_id(filename) for filename, _ in files_to_rescrape
    ]

    print(
        f"Found {len(tournament_ids_to_rescrape)} tournaments that need to be rescraped."
    )

    # Generate URLs for the tournaments that need to be rescraped
    tournament_urls = generate_urls(tournament_ids_to_rescrape)

    # Run the scraper for these specific tournaments
    all_tournament_stats = scrape_player_stats(
        tournament_urls, headless=True, additional_options=["--start-maximized"]
    )

    # Process and save the rescraped data
    for tournament_id, stats_df in all_tournament_stats.items():
        print(f"Saving rescraped data for tournament ID: {tournament_id}")
        file_path = os.path.join(player_stats_dir, f"player_stats_{tournament_id}.csv")
        stats_df.to_csv(file_path, index=False)
        print(f"Saved to: {file_path}")

    print("Rescraping process completed.")


if __name__ == "__main__":
    main()
