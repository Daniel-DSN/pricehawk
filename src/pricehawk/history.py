"""Price history: snapshots + diff reports.

Workflow
--------
1. ``save_snapshot`` — after each scrape, store prices with a timestamp
2. ``load_history``  — read the JSON history file
3. ``diff``          — compare two snapshots → added/removed/price-changed
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Product


@dataclass(slots=True)
class PriceChange:
    name: str
    old_price: float | None
    new_price: float | None

    @property
    def delta(self) -> float | None:
        if self.old_price is None or self.new_price is None:
            return None
        return round(self.new_price - self.old_price, 2)

    @property
    def delta_pct(self) -> float | None:
        if not self.old_price or self.new_price is None:
            return None
        return round((self.new_price - self.old_price) / self.old_price * 100, 1)


@dataclass(slots=True)
class Diff:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[PriceChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def save_snapshot(products: list[Product], history_path: Path) -> str:
    """Append a timestamped snapshot {name: price} to the history file."""
    stamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    history: dict[str, Any] = {}
    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
    history[stamp] = {p.name: p.price for p in products}
    history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    return stamp


def load_history(history_path: Path) -> dict[str, Any]:
    if not history_path.exists():
        return {}
    return json.loads(history_path.read_text(encoding="utf-8"))


def diff(old: dict[str, float | None], new: dict[str, float | None]) -> Diff:
    """Compare two {name: price} maps."""
    result = Diff()
    for name in sorted(set(new) - set(old)):
        result.added.append(name)
    for name in sorted(set(old) - set(new)):
        result.removed.append(name)
    for name in sorted(set(old) & set(new)):
        old_p, new_p = old[name], new[name]
        if old_p != new_p:
            result.changed.append(PriceChange(name=name, old_price=old_p, new_price=new_p))
    return result


def diff_history(history: dict[str, Any]) -> Diff:
    """Diff the last two snapshots of a history file."""
    stamps = sorted(history)
    if len(stamps) < 2:
        return Diff()
    return diff(history[stamps[-2]], history[stamps[-1]])


def format_diff(diff_obj: Diff) -> str:
    if not diff_obj.has_changes:
        return "No changes between snapshots."
    lines: list[str] = []
    if diff_obj.changed:
        lines.append("PRICE CHANGES")
        for c in diff_obj.changed:
            pct = f" ({c.delta_pct:+.1f}%)" if c.delta_pct is not None else ""
            lines.append(f"  {c.old_price} → {c.new_price}{pct}  {c.name}")
    if diff_obj.added:
        lines.append("NEW ITEMS")
        lines.extend(f"  + {n}" for n in diff_obj.added)
    if diff_obj.removed:
        lines.append("REMOVED")
        lines.extend(f"  - {n}" for n in diff_obj.removed)
    return "\n".join(lines)
