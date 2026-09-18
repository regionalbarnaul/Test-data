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


def warm_up(session):
    """Прогреваем сессию: заходим на главную DNS, получаем cookies."""
    try:
        session.get("https://www.dns-shop.ru/", impersonate="chrome120", timeout=30)
    except Exception as e:
        print(f"[warmup] error: {e}")


def get_price(session, article, debug=False):
    url = f"https://www.dns-shop.ru/search/?q={article}"
    headers = {
        "Referer": "https://www.dns-shop.ru/",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        r = session.get(url, impersonate="chrome120", timeout=30, headers=headers)
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
            if r.status_code != 200:
                print(f"[DEBUG] body-head={html[:500]!r}")
        return None
    except Exception as e:
        print(f"[{article}] error: {e}")
        return None


def main():
    articles = load_articles()
    print(f"Articles: {len(articles)}")
    articles = articles[:3]

    session = cffi_requests.Session()
    warm_up(session)

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
