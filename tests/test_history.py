"""History / diff tests."""

from pathlib import Path

from pricehawk.history import (
    diff,
    diff_history,
    format_diff,
    load_history,
    save_snapshot,
)
from pricehawk.models import Product


def test_diff_detects_price_drop():
    old = {"Widget": 50.0, "Gadget": 20.0}
    new = {"Widget": 40.0, "Gadget": 20.0}
    d = diff(old, new)
    assert len(d.changed) == 1
    change = d.changed[0]
    assert change.name == "Widget"
    assert change.delta == -10.0
    assert change.delta_pct == -20.0


def test_diff_added_and_removed():
    d = diff({"A": 1.0}, {"B": 2.0})
    assert d.added == ["B"]
    assert d.removed == ["A"]
    assert d.has_changes


def test_diff_no_change():
    d = diff({"A": 1.0}, {"A": 1.0})
    assert not d.has_changes
    assert "No changes" in format_diff(d)


def test_snapshot_roundtrip(tmp_path: Path):
    path = tmp_path / "history.json"
    p1 = [Product(name="Widget", price=50.0, scraped_at="t1")]
    p2 = [Product(name="Widget", price=45.0, scraped_at="t2")]
    save_snapshot(p1, path)
    save_snapshot(p2, path)

    history = load_history(path)
    assert len(history) == 2
    d = diff_history(history)
    assert d.changed[0].new_price == 45.0
    assert "PRICE CHANGES" in format_diff(d)
