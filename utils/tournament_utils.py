# utils/tournament_utils.py

import re
import time
from io import StringIO

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver(headless=True, additional_options=None):
    """
    Set up and return a Chrome WebDriver instance.

    This function creates a Chrome WebDriver with specified options. It allows
    for easy switching between headless and non-headless modes, and provides
    the ability to add custom Chrome options.

    Args:
        headless (bool, optional): Whether to run Chrome in headless mode.
            Defaults to True.
        additional_options (list, optional): A list of additional Chrome options
            to be added. Each option should be a string. Defaults to None.

    Returns:
        webdriver.Chrome: An instance of Chrome WebDriver.

    Example:
        # Create a headless driver with no additional options
        driver = setup_driver()

        # Create a non-headless driver with additional options
        driver = setup_driver(headless=False, additional_options=["--start-maximized", "--disable-extensions"])
    """
    chrome_options = Options()

    if headless:
        chrome_options.add_argument("--headless")

    if additional_options:
        for option in additional_options:
            chrome_options.add_argument(option)

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


def extract_tournament_id(input_string):
    """
    Extract tournament ID from a URL or a CSV filename.

    Args:
    input_string (str): Either a URL or a CSV filename containing the tournament ID.

    Returns:
    str: The extracted tournament ID, or None if not found.

    Examples:
    >>> extract_tournament_id("https://www.espn.com/golf/leaderboard/_/tournamentId/401353214")
    '401353214'
    >>> extract_tournament_id("player_stats_401353214.csv")
    '401353214'
    """
    # Try to match URL pattern
    url_match = re.search(r"/tournamentId/(\d+)", input_string)
    if url_match:
        tournament_id = url_match.group(1)
        print(f"Extracted Tournament ID from URL: {tournament_id}")
        return tournament_id

    # Try to match CSV filename pattern
    csv_match = re.search(r"player_stats_(\d+)\.csv", input_string)
    if csv_match:
        tournament_id = csv_match.group(1)
        print(f"Extracted Tournament ID from filename: {tournament_id}")
        return tournament_id

    print("Tournament ID not found in input string")
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
    """
    Generate ESPN golf leaderboard URLs based on tournament IDs.

    This function creates URLs for ESPN golf tournament leaderboards. It can handle
    different input formats for flexibility in various use cases.

    Args:
        tournament_info (Union[dict, str, list]): The tournament information in one of three formats:
            - dict: A dictionary with a key "Tournament ID" containing a list of tournament IDs.
            - str: A single tournament ID as a string.
            - list: A list of tournament IDs as strings.

    Returns:
        list: A list of URLs for ESPN golf leaderboards. Each URL is formed by
              concatenating the base URL with a tournament ID.

    Raises:
        TypeError: If the input is not a dictionary, string, or list of strings.

    Examples:
        >>> generate_urls({"Tournament ID": ["401353308", "401353310"]})
        ['https://www.espn.com/golf/leaderboard/_/tournamentId/401353308',
         'https://www.espn.com/golf/leaderboard/_/tournamentId/401353310']

        >>> generate_urls("401353308")
        ['https://www.espn.com/golf/leaderboard/_/tournamentId/401353308']

        >>> generate_urls(["401353308", "401353310"])
        ['https://www.espn.com/golf/leaderboard/_/tournamentId/401353308',
         'https://www.espn.com/golf/leaderboard/_/tournamentId/401353310']
    """
    base_url = "https://www.espn.com/golf/leaderboard/_/tournamentId/"

    if isinstance(tournament_info, dict):
        # Original functionality: dictionary with "Tournament ID" key
        return [f"{base_url}{tid}" for tid in tournament_info["Tournament ID"]]

    elif isinstance(tournament_info, str):
        # Single tournament ID as a string
        return [f"{base_url}{tournament_info}"]

    elif isinstance(tournament_info, list):
        # List of tournament IDs as strings
        return [f"{base_url}{tid}" for tid in tournament_info]

    else:
        raise TypeError("Input must be a dictionary, a string, or a list of strings")


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
