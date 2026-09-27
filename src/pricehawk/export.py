"""Export products to CSV, JSON or Excel."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Product

FIELDS = ["name", "price", "availability", "rating", "url", "scraped_at"]


def to_csv(products: list[Product], path: Path) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for p in products:
            writer.writerow(p.to_dict())
    return path


def to_json(products: list[Product], path: Path) -> Path:
    payload = [p.to_dict() for p in products]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def to_xlsx(products: list[Product], path: Path) -> Path:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "products"
    ws.append(FIELDS)
    for p in products:
        ws.append([p.to_dict()[f] for f in FIELDS])
    # light styling: bold header + frozen first row
    from openpyxl.styles import Font

    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"
    wb.save(path)
    return path


def export(products: list[Product], path: Path) -> Path:
    """Dispatch on file suffix (.csv / .json / .xlsx)."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return to_csv(products, path)
    if suffix == ".json":
        return to_json(products, path)
    if suffix in {".xlsx", ".xlsm"}:
        return to_xlsx(products, path)
    raise ValueError(f"unsupported format: {suffix!r} (use .csv, .json or .xlsx)")
