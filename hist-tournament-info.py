import csv
import json
import os
import sys
import time

from utils import scrape_tournament_info, setup_driver


def load_tournament_ids_by_year(directory):
    tournaments = []
    seen_ids = set()
    for filename in os.listdir(directory):
        if filename.endswith(".csv") and filename.startswith("golf_tournaments"):
            with open(os.path.join(directory, filename), "r") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["id"] not in seen_ids:
                        tournaments.append(row)
                        seen_ids.add(row["id"])
    return tournaments


def process_tournaments(tournaments, output_file):
    driver = setup_driver()

    try:
        with open(output_file, "w", newline="") as csvfile:
            fieldnames = [
                "Tournament ID",
                "Year",
                "Tournament name",
                "Date",
                "Location",
                "Par",
                "Yards",
                "Purse",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for tournament in tournaments:
                # Skip tournaments without an ID
                if not tournament["id"]:
                    print(
                        f"Skipping tournament without ID: {tournament.get('name', 'Unknown')}"
                    )
                    continue

                url = f"https://www.espn.com/golf/leaderboard/_/tournamentId/{tournament['id']}"
                print(f"Scraping: {url}")

                info = scrape_tournament_info(driver, url)

                # Only write the row if we successfully scraped the tournament name
                if info.get("Tournament name", "") != "Not found":
                    info["Tournament ID"] = tournament["id"]
                    info["Year"] = tournament["year"]
                    writer.writerow(info)
                    csvfile.flush()  # Flush after each write

                    # Print the row data to stdout
                    print(f"Row written: {json.dumps(info, indent=2)}")

                    print(
                        f"Scraped: {info.get('Tournament name', 'Unknown tournament')}"
                    )
                else:
                    print(
                        f"Skipping tournament {tournament['id']}: Unable to scrape data"
                    )

                time.sleep(1)  # Add a delay to avoid overloading the server

        print(f"CSV file has been successfully saved to: {output_file}")

    except IOError as e:
        print(f"Error writing to CSV file: {e}", file=sys.stderr)
    finally:
        driver.quit()


if __name__ == "__main__":
    data_directory = "data"
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
    output_file = os.path.join(data_directory, "tournament_info.csv")

    tournaments = load_tournament_ids_by_year(data_directory)
    process_tournaments(tournaments, output_file)
