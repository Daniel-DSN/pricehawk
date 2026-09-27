"""Parser unit tests — offline, using samples/listing.html."""

from pathlib import Path

import pytest

from pricehawk.scraper import BOOKS_DEFAULT, SelectorConfig, parse_listing, parse_price, next_page

SAMPLES = Path(__file__).parent.parent / "samples"
HTML = (SAMPLES / "listing.html").read_text(encoding="utf-8")
BASE = "https://books.toscrape.com/catalogue/page-1.html"


def test_parse_price_gbp():
    assert parse_price("£51.77") == 51.77


def test_parse_price_brl_thousands():
    assert parse_price("R$ 1.299,90") == 1299.90


def test_parse_price_missing():
    assert parse_price("n/a") is None


def test_parse_listing_finds_all_cards():
    products = parse_listing(HTML, BASE, BOOKS_DEFAULT)
    assert len(products) == 5
    assert products[0].name == "A Light in the Attic"
    assert products[0].price == 51.77
    assert products[0].rating == "3/5"
    assert "In stock" in products[0].availability
    assert products[0].url.startswith("https://books.toscrape.com/")


def test_parse_listing_skips_cards_without_name():
    html = '<div class="p"><span class="p">no name</span><p class="price_color">£1.00</p></div>'
    cfg = SelectorConfig(card="div.p", name="h3", price=".price_color")
    assert parse_listing(html, BASE, cfg) == []


def test_next_page_follows_rel():
    products_html = HTML  # sample contains <a class="next">
    nxt = next_page(products_html, BASE, BOOKS_DEFAULT)
    assert nxt and nxt.endswith("page-2.html")


def test_next_page_absent_returns_none():
    assert next_page("<html><body>end</body></html>", BASE, BOOKS_DEFAULT) is None
