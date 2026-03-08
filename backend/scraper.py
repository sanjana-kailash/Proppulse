"""
scraper.py — Web scraping logic for PropPulse

Scrapes 4 Melbourne property market sources and saves to:
  backend/data/raw_articles.json  — list of {source, url, scraped_date, content}

Run directly:  python scraper.py
"""

import json
import os
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "name": "propertyupdate.com.au",
        "url": "https://propertyupdate.com.au/australian-property-market/",
    },
    {
        "name": "metropole.com.au",
        "url": "https://metropole.com.au/melbourne-housing-market-update/",
    },
    {
        "name": "whichrealestateagent.com.au",
        "url": "https://whichrealestateagent.com.au/property-market-update/melbourne-vic/",
    },
    {
        "name": "reiv.com.au",
        "url": "https://reiv.com.au/market-insights/victorian-insights",
    },
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_ARTICLES_PATH = os.path.join(DATA_DIR, "raw_articles.json")

# Tags to strip before content extraction — boilerplate, ads, navigation
STRIP_TAGS = ["script", "style", "nav", "footer", "header",
              "aside", "form", "noscript", "iframe", "figure"]

# Content containers searched in priority order
CONTENT_SELECTORS = [
    {"tag": "article"},
    {"class_": re.compile(r"entry-content|post-content|article-body|article-content", re.I)},
    {"tag": "main"},
]


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def get_headers() -> dict:
    """Realistic browser headers to reduce bot-detection risk."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
    }


def safe_get(url: str, delay: float = 2.0) -> requests.Response | None:
    """
    Fetch a URL with a polite delay. Returns None on any error.
    Sets response.encoding to apparent_encoding so non-ASCII characters
    (curly quotes, em-dashes, etc.) are decoded correctly before parsing.
    """
    time.sleep(delay)
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        # Override the charset declared in headers with what chardet detects.
        # This fixes garbled text when sites declare iso-8859-1 but serve utf-8.
        response.encoding = response.apparent_encoding
        return response
    except requests.exceptions.HTTPError as e:
        print(f"  [HTTP error] {url} → {e}")
    except requests.exceptions.ConnectionError:
        print(f"  [Connection error] Could not reach {url}")
    except requests.exceptions.Timeout:
        print(f"  [Timeout] Request to {url} timed out")
    except requests.exceptions.RequestException as e:
        print(f"  [Request error] {url} → {e}")
    return None


def find_main_content(soup: BeautifulSoup):
    """
    Find the primary content container using a priority-ordered selector list.
    Falls back to <body> if nothing else matches.
    """
    for selector in CONTENT_SELECTORS:
        if "tag" in selector:
            el = soup.find(selector["tag"])
        else:
            el = soup.find(class_=selector["class_"])
        if el:
            return el
    return soup.body or soup


def extract_content_blocks(soup: BeautifulSoup) -> list[str]:
    """
    From a parsed page, strip boilerplate and return all meaningful
    text blocks (headers + paragraphs + list items) over 20 characters.
    """
    # Decompose noise tags in-place
    for tag in soup(STRIP_TAGS):
        tag.decompose()

    main_body = find_main_content(soup)
    blocks = []

    for el in main_body.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = el.get_text(separator=" ", strip=True)
        if not text or len(text) < 20:
            continue
        blocks.append(text)

    return blocks


# ---------------------------------------------------------------------------
# Core scraper
# ---------------------------------------------------------------------------

def scrape_source(source: dict) -> dict:
    """
    Scrape a single source and return a structured result dict.

    Returns:
      {
        "source": str,
        "url": str,
        "scraped_date": "YYYY-MM-DD",
        "content": [str, ...],
        "success": bool,
      }
    """
    name = source["name"]
    url = source["url"]

    result = {
        "source": name,
        "url": url,
        "scraped_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "content": [],
        "success": False,
    }

    print(f"\n[{name}] Fetching {url} ...")
    response = safe_get(url, delay=2.0)

    if not response:
        print(f"  [{name}] Skipping — request failed.")
        return result

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        blocks = extract_content_blocks(soup)
        result["content"] = blocks
        result["success"] = True

        # Print a preview of stat-containing lines for visibility
        stat_pattern = re.compile(r"[\d]+\.?\d*\s*%|\$[\d]|[\d]{1,3},[\d]{3}")
        stat_count = 0
        for block in blocks:
            if stat_pattern.search(block) and stat_count < 5:
                print(f"  [stat] {block[:100]}...")
                stat_count += 1

        print(f"  [{name}] Extracted {len(blocks)} content blocks.")

    except Exception as e:
        print(f"  [{name}] Parse error: {e}")

    return result


def scrape_all_sources() -> list[dict]:
    """
    Scrape all 4 configured sources sequentially.
    Returns a list of result dicts (one per source).
    """
    results = []
    for source in SOURCES:
        result = scrape_source(source)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("PropPulse Scraper")
    print(f"Started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Sources: {len(SOURCES)}")
    print("=" * 60)

    os.makedirs(DATA_DIR, exist_ok=True)

    results = scrape_all_sources()

    successful = [r for r in results if r["success"]]
    print(f"\n[scraper] {len(successful)}/{len(SOURCES)} sources scraped successfully.")

    with open(RAW_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"[scraper] Saved to {RAW_ARTICLES_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
