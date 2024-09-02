from selenium import webdriver
from selenium.common.exceptions import InvalidSelectorException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def check_selector(driver, selector, selector_type="css", timeout=10, element_name=""):
    selector_types = {
        "css": By.CSS_SELECTOR,
        "xpath": By.XPATH,
        "id": By.ID,
        "class": By.CLASS_NAME,
        "name": By.NAME,
        "tag": By.TAG_NAME,
    }
    if selector_type not in selector_types:
        raise ValueError(
            f"Invalid selector type. Choose from: {', '.join(selector_types.keys())}"
        )

    by_type = selector_types[selector_type]
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by_type, selector))
        )
        elements = driver.find_elements(by_type, selector)

        if len(elements) == 1:
            element = elements[0]
            text = element.text.strip()
            return "Unique", f"Text: {text}"
        else:
            element_info = []
            for i, element in enumerate(elements, 1):
                tag_name = element.tag_name
                classes = element.get_attribute("class")
                id_attr = element.get_attribute("id")
                text = element.text.strip()
                text = text[:50] + "..." if len(text) > 50 else text
                xpath = driver.execute_script(
                    """
                    function getXPath(element) {
                        if (element.id !== '')
                            return 'id("' + element.id + '")';
                        if (element === document.body)
                            return element.tagName;
                        var ix = 0;
                        var siblings = element.parentNode.childNodes;
                        for (var i = 0; i < siblings.length; i++) {
                            var sibling = siblings[i];
                            if (sibling === element)
                                return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                ix++;
                        }
                    }
                    return getXPath(arguments[0]);
                """,
                    element,
                )
                element_info.append(
                    f"Element {i}:\n  Tag: {tag_name}\n  Classes: {classes}\n  ID: {id_attr}\n  Text: {text}\n  XPath: {xpath}"
                )
            return f"Not Unique ({len(elements)} elements found)", "\n\n".join(
                element_info
            )
    except (TimeoutException, InvalidSelectorException):
        return "Not Found", None


def check_selectors(url, selectors):
    driver = setup_driver()
    driver.get(url)
    print(f"Checking selectors on {url}")
    print("-" * 100)

    for selector, selector_type, element_name in selectors:
        result, details = check_selector(
            driver, selector, selector_type, element_name=element_name
        )
        print(f"Element: {element_name}")
        print(f"{selector_type.upper():<6} | {selector:<30} | {result}")
        if details:
            print("\nDetails:")
            print(details)
        print("-" * 100)

    driver.quit()


# Usage
if __name__ == "__main__":
    url = "https://www.espn.com/golf/leaderboard"
    selectors_to_check = [
        ("Leaderboard__Event__Title", "class", "Tournament name"),
        ("Leaderboard__Event__Date", "class", "Date"),
        ("Leaderboard__Course__Location", "class", "Location"),
        ("Leaderboard__Course__Location__Detail", "class", "Details"),
        ("//div[@class='Leaderboard__Courses']/div[2]", "xpath", "Purse"),
        ("leaderboard__content", "class", "Data"),
        ("competitors", "class", "table"),
    ]
    check_selectors(url, selectors_to_check)
