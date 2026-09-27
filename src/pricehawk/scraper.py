"""Fetching and parsing of listing pages.

Design notes
------------
* Parsing is **pure** (str in, list[Product] out) so it is unit-testable
  without network access.
* Fetching is polite: timeout, retries with backoff, custom User-Agent
  and a configurable delay between pages.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Product

DEFAULT_UA = "PriceHawk/1.0 (+https://example.com/pricehawk; polite scraper)"
PRICE_RE = re.compile(r"(\d[\d.,]*)")
RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


@dataclass(slots=True)
class SelectorConfig:
    """CSS selectors for one site — kept in YAML/JSON, not hard-coded."""

    card: str
    name: str
    price: str
    availability: str = ""
    rating: str = ""
    next_page: str = "li.next a"


# books.toscrape.com — the public scraping-practice site used in the demo
BOOKS_DEFAULT = SelectorConfig(
    card="article.product_pod",
    name="h3 a",
    price="p.price_color",
    availability="p.instock.availability",
    rating="p.star-rating",
)


class FetchError(RuntimeError):
    """Raised when a page cannot be fetched after all retries."""


def fetch(url: str, *, ua: str = DEFAULT_UA, timeout: int = 20, retries: int = 3) -> str:
    """GET *url* with retries/backoff. Returns raw HTML."""
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": ua, "Accept-Language": "en"},
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)
    raise FetchError(f"failed to fetch {url}: {last_exc}") from last_exc


def parse_price(raw: str) -> float | None:
    """Extract a float from strings like '£51.77', 'R$ 1.299,90', '$3.99'."""
    text = raw.replace("\xa0", " ").strip()
    m = PRICE_RE.search(text)
    if not m:
        return None
    number = m.group(1)
    if "," in number and "." in number:
        number = number.replace(",", "") if number.rfind(".") > number.rfind(",") else number.replace(".", "").replace(",", ".")
    elif "," in number:
        parts = number.split(",")
        number = number.replace(",", ".") if len(parts[-1]) != 3 else number.replace(",", "")
    elif number.count(".") > 1:
        number = number.replace(".", "")
    try:
        return float(number)
    except ValueError:
        return None


def parse_listing(html: str, base_url: str, cfg: SelectorConfig) -> list[Product]:
    """Pure parser: HTML → products. No I/O."""
    soup = BeautifulSoup(html, "html.parser")
    products: list[Product] = []
    for card in soup.select(cfg.card):
        name_el = card.select_one(cfg.name)
        price_el = card.select_one(cfg.price)
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        href = name_el.get("href", "")
        price = parse_price(price_el.get_text()) if price_el else None

        availability = ""
        if cfg.availability:
            avail_el = card.select_one(cfg.availability)
            availability = avail_el.get_text(" ", strip=True) if avail_el else ""

        rating = ""
        if cfg.rating:
            rating_el = card.select_one(cfg.rating)
            if rating_el:
                for word, value in RATING_MAP.items():
                    if word in (rating_el.get("class") or []):
                        rating = f"{value}/5"
                        break

        products.append(
            Product(
                name=name,
                price=price,
                availability=availability,
                rating=rating,
                url=urljoin(base_url, href),
            )
        )
    return products


def next_page(html: str, base_url: str, cfg: SelectorConfig) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one(cfg.next_page)
    if link and link.get("href"):
        return urljoin(base_url, link["href"])
    return None


def scrape(
    url: str,
    cfg: SelectorConfig = BOOKS_DEFAULT,
    *,
    pages: int = 1,
    delay: float = 1.0,
    ua: str = DEFAULT_UA,
) -> list[Product]:
    """Crawl up to *pages* listing pages and return all products."""
    results: list[Product] = []
    current: str | None = url
    seen: set[str] = set()

    for page_no in range(1, pages + 1):
        if current is None or current in seen:
            break
        seen.add(current)
        html = fetch(current, ua=ua)
        batch = parse_listing(html, current, cfg)
        results.extend(batch)
        print(f"  [page {page_no}] {len(batch):>3} items  {current}")
        current = next_page(html, current, cfg)
        if page_no < pages and delay > 0 and current:
            time.sleep(delay)
    return results
