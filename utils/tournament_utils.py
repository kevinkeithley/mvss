# utils/tournament_utils.py

import re

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_tournament_info(driver, url):
    driver.get(url)
    tournament_info = {}
    selectors = {
        "Tournament name": ("Leaderboard__Event__Title", "class"),
        "Date": ("Leaderboard__Event__Date", "class"),
        "Location": ("Leaderboard__Course__Location", "class"),
        "Details": ("Leaderboard__Course__Location__Detail", "class"),
        "Purse": ("//div[@class='Leaderboard__Courses']/div[2]", "xpath"),
    }

    selector_types = {
        "css": By.CSS_SELECTOR,
        "xpath": By.XPATH,
        "id": By.ID,
        "class": By.CLASS_NAME,
        "name": By.NAME,
        "tag": By.TAG_NAME,
    }

    def check_selector(selector, selector_type="class", timeout=10):
        if selector_type not in selector_types:
            raise ValueError(
                f"Invalid selector type. Choose from: {', '.join(selector_types.keys())}"
            )

        by_type = selector_types[selector_type]
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by_type, selector))
            )
            return element.text.strip()
        except (TimeoutException, NoSuchElementException):
            return "Not found"

    for key, (selector, selector_type) in selectors.items():
        tournament_info[key] = check_selector(selector, selector_type)

    # Process Details
    if "Details" in tournament_info and tournament_info["Details"] != "Not found":
        details = tournament_info["Details"]
        par_match = re.search(r"Par(\d+)", details)
        yards_match = re.search(r"Yards(\d+)", details)
        if par_match:
            tournament_info["Par"] = par_match.group(1)
        if yards_match:
            tournament_info["Yards"] = yards_match.group(1)
        del tournament_info["Details"]

    # Process Purse
    if "Purse" in tournament_info and tournament_info["Purse"] != "Not found":
        purse = tournament_info["Purse"]
        if "Purse" in purse:
            purse_match = re.search(r"Purse\$([0-9,]+)", purse)
            if purse_match:
                tournament_info["Purse"] = purse_match.group(1).replace(",", "")
        else:
            del tournament_info["Purse"]

    return tournament_info
