import json
import csv
import io
import time
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

CSV_URL = "https://raw.githubusercontent.com/regionalbarnaul/Test-data/main/Test.csv"


def load_articles():
    r = cffi_requests.get(CSV_URL, impersonate="chrome120", timeout=30)
    r.encoding = "utf-8"
    reader = csv.reader(io.StringIO(r.text))
    articles = []
    for row in reader:
        if row and row[0].strip().isdigit():
            articles.append(row[0].strip())
    return articles


def get_price(session, article, debug=False):
    url = f"https://www.dns-shop.ru/search/?q={article}"
    try:
        r = session.get(url, impersonate="chrome120", timeout=30)
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

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
            print(f"[DEBUG] status={r.status_code}")
            print(f"[DEBUG] html-length={len(html)}")
            print(f"[DEBUG] title={(soup.title.get_text() if soup.title else '')[:80]}")
            print(f"[DEBUG] price-classes={sorted(classes)[:30]}")
        return None
    except Exception as e:
        print(f"[{article}] error: {e}")
        return None


def main():
    articles = load_articles()
    print(f"Articles: {len(articles)}")
    articles = articles[:3]

    session = cffi_requests.Session()

    prices = {}
    for i, art in enumerate(articles, 1):
        price = get_price(session, art, debug=(i == 1))
        prices[art] = price
        print(f"[{i}/{len(articles)}] {art} -> {price}")
        time.sleep(2)

    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    print(f"Saved: {len(prices)}")


if __name__ == "__main__":
    main()
