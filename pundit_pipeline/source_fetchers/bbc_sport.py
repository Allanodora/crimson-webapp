"""
BBC Sport Fetcher
Uses Selenium to scrape football news, VAR drama, match reactions
"""

import sys
from pathlib import Path

# Add pipeline root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

try:
    import config as CONFIG
except Exception:

    class _C:
        CHROME_PATH = ""
        DRIVER_PATH = ""

    CONFIG = _C()


def get_driver():
    """Create headless Chrome driver."""
    if not CONFIG.CHROME_PATH:
        return None

    options = webdriver.ChromeOptions()
    options.binary_location = CONFIG.CHROME_PATH
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        service = Service(CONFIG.DRIVER_PATH)
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"[BBC Sport] Driver error: {e}")
        return None


def fetch_premier_league_news() -> list:
    """Fetch latest PL news headlines from BBC Sport."""
    stories = []
    driver = get_driver()

    if not driver:
        print("[BBC Sport] Driver not available, skipping")
        return stories

    try:
        driver.get("https://www.bbc.com/sport/football/premier-league")
        wait = WebDriverWait(driver, 10)

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))

        articles = driver.find_elements(By.TAG_NAME, "article")

        for article in articles[:15]:
            try:
                headline = article.find_element(By.CSS_SELECTOR, "h3, h2").text.strip()
                if not headline or len(headline) < 10:
                    continue

                link = ""
                try:
                    link_el = article.find_element(By.TAG_NAME, "a")
                    link = link_el.get_attribute("href") or ""
                except:
                    pass

                stories.append(
                    {
                        "title": headline,
                        "description": headline,
                        "source": "bbc_sport",
                        "category": "football",
                        "timestamp": datetime.now().isoformat(),
                        "url": link,
                        "has_graph": False,
                        "is_trending": True,
                    }
                )

            except Exception:
                continue

    except Exception as e:
        print(f"[BBC Sport] Error: {e}")

    finally:
        driver.quit()

    return stories


def fetch_standings() -> dict:
    """Fetch current PL standings."""
    driver = get_driver()
    standings = {"teams": [], "timestamp": datetime.now().isoformat()}

    if not driver:
        return standings

    try:
        driver.get("https://www.bbc.com/sport/football/premier-league/table")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        rows = driver.find_elements(By.XPATH, "//table//tbody//tr")

        for row in rows[:20]:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 8:
                    standings["teams"].append(
                        {
                            "position": cells[0].text.strip(),
                            "team": cells[1].text.strip(),
                            "played": cells[2].text.strip(),
                            "won": cells[3].text.strip(),
                            "drawn": cells[4].text.strip(),
                            "lost": cells[5].text.strip(),
                            "gf": cells[6].text.strip(),
                            "ga": cells[7].text.strip(),
                            "points": cells[-1].text.strip(),
                        }
                    )
            except:
                continue

    except Exception as e:
        print(f"[BBC Sport] Standings error: {e}")

    finally:
        driver.quit()

    return standings


def fetch_chelsea_news() -> list:
    """Fetch Chelsea-specific news."""
    stories = []
    driver = get_driver()

    if not driver:
        return stories

    try:
        driver.get("https://www.bbc.com/sport/football/teams/chelsea")
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))

        articles = driver.find_elements(By.TAG_NAME, "article")

        for article in articles[:10]:
            try:
                headline = article.find_element(By.CSS_SELECTOR, "h3, h2").text.strip()
                if not headline:
                    continue

                link = ""
                try:
                    link_el = article.find_element(By.TAG_NAME, "a")
                    link = link_el.get_attribute("href") or ""
                except:
                    pass

                stories.append(
                    {
                        "title": headline,
                        "description": headline,
                        "source": "bbc_sport",
                        "category": "football",
                        "core_relevant": True,
                        "timestamp": datetime.now().isoformat(),
                        "url": link,
                        "has_graph": False,
                        "is_trending": True,
                    }
                )

            except:
                continue

    except Exception as e:
        print(f"[BBC Sport] Chelsea news error: {e}")

    finally:
        driver.quit()

    return stories


if __name__ == "__main__":
    print("Fetching BBC Sport PL news...")
    news = fetch_premier_league_news()
    print(f"Found {len(news)} headlines")
    for n in news[:5]:
        print(f"  - {n['title']}")
