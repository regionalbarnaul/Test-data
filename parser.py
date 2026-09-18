import json
import csv
import io
import time
import urllib.request
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

CSV_URL = "https://raw.githubusercontent.com/regionalbarnaul/Test-data/main/Test.csv"

def load_articles():
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    articles = []
    for i, row in enumerate(reader):
        if i == 0:
            continue
        if row and row[0].strip().isdigit():
            articles.append(row[0].strip())
    return articles

def get_price(driver, article):
    url = f"https://www.dns-shop.ru/search/?q={article}"
    try:
        driver.get(url)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for sel in ["div.product-buy__price", "div.product-buy__price-active", "span.product-buy__price"]:
            tag = soup.select_one(sel)
            if tag:
                digits = "".join(c for c in tag.get_text() if c.isdigit())
                if digits:
                    return int(digits)
        return None
    except Exception as e:
        print(f"[{article}] error: {e}")
        return None

def main():
    articles = load_articles()
    print(f"Articles: {len(articles)}")

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options)

    prices = {}
    for i, art in enumerate(articles, 1):
        price = get_price(driver, art)
        prices[art] = price
        print(f"[{i}/{len(articles)}] {art} -> {price}")

    driver.quit()

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    print(f"Saved: {len(prices)}")

if __name__ == "__main__":
    main()
