# PriceHawk

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](#testing)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Style](https://img.shields.io/badge/code-polite-orange)](#politeness-policy)

**Polite multi-page product scraper with price history and diff reports.**

Turn any listing page into clean CSV / JSON / Excel — then track price changes over time.

```
URL in → products.csv + history.json → pricehawk diff → "£51.77 → £47.82 (-7.6%)"
```

---

## Why this exists

Manual price checks, copy-paste catalog exports and "who changed this page?" emails
steal hours every week. PriceHawk does the boring half:

- **Scrape** product name, price, availability, rating and URL
- **Export** CSV, JSON or styled Excel (frozen header, bold columns)
- **Track** every run as a timestamped snapshot
- **Diff** two snapshots → price drops, new items, removals
- **Exit code 2 when prices changed** — drop it into cron/CI and you get alerts

## Quick start

```bash
pip install -r requirements.txt          # requests, beautifulsoup4, openpyxl
PYTHONPATH=src python -m pricehawk.cli --help
```

Run the bundled demo against the public practice site:

```bash
# 1) scrape page 1 → CSV + first snapshot
python -m pricehawk.cli scrape "http://books.toscrape.com/" \
    -o products.csv --history history.json

# 2) later — scrape again and compare
python -m pricehawk.cli scrape "http://books.toscrape.com/" \
    -o products2.csv --history history.json
python -m pricehawk.cli diff --history history.json
```

Typical output:

```
PriceHawk 1.0.0 — scraping http://books.toscrape.com/
  [page 1]  20 items  http://books.toscrape.com/
[stats] 20 items · price min 33.34 · max 58.85 · avg 46.33
[ok] exported 20 rows → products.csv
[ok] snapshot saved → history.json (2026-09-25T14:02:11+00:00)
```

## Full CLI

| Command | Purpose |
|---------|---------|
| `pricehawk scrape URL -o out.csv` | crawl listing → export |
| `--pages N` | follow "next" pagination up to N pages |
| `--format csv\|json\|xlsx` | output format (or use `-o file.xlsx`) |
| `--config selectors.json` | CSS selectors for a different site |
| `--history history.json` | append price snapshot each run |
| `--delay 1.5` | polite delay between pages (seconds) |
| `--ua "..."` | custom User-Agent |
| `pricehawk diff --history history.json` | compare last 2 snapshots (exit 2 = changes) |

### Configuring a new site

Save a JSON file with the site's CSS selectors:

```json
{
  "card": ".product-card",
  "name": ".title",
  "price": ".price",
  "availability": ".stock",
  "rating": ".stars",
  "next_page": "a[rel=next]"
}
```

```bash
pricehawk scrape "https://shop.example.com/products" --config myshop.json -o shop.xlsx
```

No code changes needed — selectors are data.

## Architecture

```
src/pricehawk/
├── cli.py       argparse + commands (scrape / diff)
├── scraper.py   fetch (retry/backoff) + pure parsers + pagination
├── models.py    Product dataclass
├── export.py    CSV / JSON / XLSX writers
└── history.py   snapshots + diff + human report
```

- **Parsing is pure** (HTML in → products out) → unit-tested without network
- **Fetching is isolated** with retries, timeout and backoff
- **Selectors live in config** → adapt to a new shop in seconds

## Politeness policy

- Custom User-Agent identifying the bot
- Configurable delay between pages (default 1s)
- Retries with backoff — no tight loops on failure
- Public data only; respects each site's Terms of Service
- Never used for login-walled or private/personal data

## Testing

```bash
pip install pytest
python -m pytest -q
```

```
16 passed in 1.71s
```

Coverage: price parsing (GBP/BR formats), listing parser, pagination,
CSV/JSON/XLSX export, snapshot round-trip, diff math.

## Use cases

| Who | Uses PriceHawk for |
|-----|--------------------|
| E-commerce | competitor price monitoring → weekly CSV |
| Agencies | catalog export / migration (Shopify, WooCommerce) |
| Analysts | price history + % change reports |
| Ops | scheduled scrape → alert when prices change |

## License

MIT — see [LICENSE](LICENSE).
