"""PriceHawk command-line interface.

Commands
--------
    pricehawk scrape URL [-o out.csv] [--pages N] [--format csv|json|xlsx]
    pricehawk diff   [--history history.json]

Exit codes: 0 = success, 1 = error, 2 = changes found (for CI/alerting).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .export import export
from .history import diff_history, format_diff, load_history, save_snapshot
from .scraper import BOOKS_DEFAULT, SelectorConfig, scrape


def _load_config(path: Path | None) -> SelectorConfig:
    if path is None:
        return BOOKS_DEFAULT
    data = json.loads(path.read_text(encoding="utf-8"))
    return SelectorConfig(**data)


def cmd_scrape(args: argparse.Namespace) -> int:
    cfg = _load_config(Path(args.config) if args.config else None)
    suffix = {"csv": ".csv", "json": ".json", "xlsx": ".xlsx"}[args.format]
    out = Path(args.output) if args.output else Path(f"products{suffix}")

    print(f"PriceHawk {__version__} — scraping {args.url}")
    products = scrape(args.url, cfg, pages=args.pages, delay=args.delay, ua=args.ua)

    if not products:
        print("[warn] no items found — check your selectors", file=sys.stderr)
        return 1

    # price stats
    prices = [p.price for p in products if p.price is not None]
    if prices:
        print(
            f"[stats] {len(products)} items · "
            f"price min {min(prices):.2f} · max {max(prices):.2f} · "
            f"avg {sum(prices) / len(prices):.2f}"
        )

    export(products, out)
    print(f"[ok] exported {len(products)} rows → {out}")

    if args.history:
        stamp = save_snapshot(products, Path(args.history))
        print(f"[ok] snapshot saved → {args.history} ({stamp})")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    history = load_history(Path(args.history))
    if len(history) < 2:
        print(
            f"[warn] need ≥2 snapshots in {args.history} (found {len(history)})",
            file=sys.stderr,
        )
        return 1
    result = diff_history(history)
    print(format_diff(result))
    return 2 if result.has_changes else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pricehawk",
        description="Polite multi-page product scraper with price history.",
    )
    parser.add_argument("--version", action="version", version=f"pricehawk {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scrape", help="scrape a listing page and export")
    s.add_argument("url", help="listing URL")
    s.add_argument("-o", "--output", help="output file (.csv / .json / .xlsx)")
    s.add_argument("-f", "--format", choices=["csv", "json", "xlsx"], default="csv")
    s.add_argument("--pages", type=int, default=1, help="max pages to crawl")
    s.add_argument("--delay", type=float, default=1.0, help="seconds between pages")
    s.add_argument("--config", help="JSON file with CSS selectors")
    s.add_argument("--ua", help="override User-Agent")
    s.add_argument("--history", help="append price snapshot to this JSON file")
    s.set_defaults(func=cmd_scrape)

    d = sub.add_parser("diff", help="compare the last two price snapshots")
    d.add_argument("--history", default="history.json")
    d.set_defaults(func=cmd_diff)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n[abort] interrupted", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
