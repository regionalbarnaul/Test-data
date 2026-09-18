import json
import csv
import io
import time
import urllib.request
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CSV_URL = "https://raw.githubusercontent.com/regionalbarnaul/Test-data/main/Test.csv"


def load_articles():
    req = urllib.request.Request(CSV_URL)
    text = urllib.request.urlopen(req).read().decode("utf-8")
    reader = csv.reader(io.StringIO(text))
    articles = []
    for row in reader:
        if row and row[0].strip().isdigit():
            articles.append(row[0].strip())
    return articles


def get_price(driver, article, debug=False):
    url = f"https://www.dns-shop.ru/search/?q={article}"
    try:
        driver.get(url)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            pass
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        selectors = [
            "div.product-buy__price",
            "[class*='product-buy__price']",
            "[class*='product-mini-card__price-current']",
            "[class*='product-mini-card__price']",
            "[class*='product-card__price']",
        ]
        for sel in selectors:
            for tag in soup.select(sel):
                text = tag.get_text(" ", strip=True)
                digits = "".join(c for c in text if c.isdigit())
                if digits and len(digits) >= 3:
                    return int(digits)

        if debug:
            classes = set()
            for tag in soup.find_all(True):
                for c in (tag.get("class") or []):
                    if "price" in c.lower():
                        classes.add(c)
            print(f"[DEBUG] title='{(driver.title or '')[:80]}'")
            print(f"[DEBUG] price-classes={sorted(classes)[:30]}")
            print(f"[DEBUG] html-length={len(driver.page_source)}")
        return None
    except Exception as e:
        print(f"[{article}] error: {e}")
        return None


def main():
    articles = load_articles()
    print(f"Articles: {len(articles)}")
    articles = articles[:3]  # ВРЕМЕННО: тестируем только на 3 товарах

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options, version_main=152)

    prices = {}
    for i, art in enumerate(articles, 1):
        price = get_price(driver, art, debug=(i == 1))
        prices[art] = price
        print(f"[{i}/{len(articles)}] {art} -> {price}")

    driver.quit()

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    print(f"Saved: {len(prices)}")


if __name__ == "__main__":
    main()
