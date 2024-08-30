import csv
import os
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
                print(f"Scraped: {info.get('Tournament name', 'Unknown tournament')}")
            else:
                print(f"Skipping tournament {tournament['id']}: Unable to scrape data")

            time.sleep(1)  # Add a delay to avoid overloading the server

    driver.quit()


if __name__ == "__main__":
    data_directory = "data"
    output_file = f"{data_directory}/tournament_info.csv"

    tournaments = load_tournament_ids_by_year(data_directory)
    process_tournaments(tournaments, output_file)
