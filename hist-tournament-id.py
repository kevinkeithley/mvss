import csv
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def extract_tournament_id(url):
    match = re.search(r"/tournamentId/(\d+)", url)
    return match.group(1) if match else None


def scrape_tournaments(driver, year):
    # XPath selectors
    year_xpath = "//*[contains(@class, 'mt4')][1]//*[contains(@class, 'mr4')]//*[contains(@class, 'dropdown__select')][1]"
    tournament_xpath = "//*[contains(@class, 'mt4')][1]//*[contains(@class, 'mr3')]//*[contains(@class, 'dropdown__select')][1]"

    # Wait for the year dropdown to be present and visible
    wait = WebDriverWait(driver, 10)
    year_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, year_xpath)))

    # Select the year
    select = Select(year_dropdown)
    select.select_by_visible_text(str(year))

    # Wait for the page to update
    time.sleep(2)

    # Get the tournament dropdown
    tournament_dropdown = wait.until(
        EC.presence_of_element_located((By.XPATH, tournament_xpath))
    )
    select = Select(tournament_dropdown)

    # Get all tournament options
    tournament_options = select.options

    # List to store tournament information
    tournaments = []

    # Iterate through each tournament option
    for option in tournament_options:
        tournament_name = option.text
        select.select_by_visible_text(tournament_name)
        time.sleep(1)  # Wait for URL to update
        current_url = driver.current_url
        tournament_id = extract_tournament_id(current_url)
        tournaments.append({"name": tournament_name, "id": tournament_id, "year": year})

    return tournaments


def save_to_csv(tournaments, year):
    # Create a 'data' directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")

    csv_filename = f"data/golf_tournaments_{year}.csv"
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "id", "year"])
        writer.writeheader()
        for tournament in tournaments:
            writer.writerow(tournament)
    print(f"Tournament data for {year} has been saved to {csv_filename}")


def save_years_csv(years):
    csv_filename = "golf_tournament_years.csv"
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["year"])
        for year in years:
            writer.writerow([year])
    print(f"Years data has been saved to {csv_filename}")


def main():
    # Setup the Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # Navigate to the ESPN golf leaderboard
    driver.get("https://www.espn.com/golf/leaderboard")

    # Get all available years from the dropdown
    year_xpath = "//*[contains(@class, 'mt4')][1]//*[contains(@class, 'mr4')]//*[contains(@class, 'dropdown__select')][1]"
    wait = WebDriverWait(driver, 10)
    year_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, year_xpath)))
    select = Select(year_dropdown)
    available_years = [option.text for option in select.options]

    # Save years to CSV
    save_years_csv(available_years)

    for year in available_years:
        print(f"Scraping data for year {year}")
        tournaments = scrape_tournaments(driver, year)
        save_to_csv(tournaments, year)

    # Close the browser
    driver.quit()


if __name__ == "__main__":
    main()
