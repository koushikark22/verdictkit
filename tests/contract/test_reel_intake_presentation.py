"""Reel paste intake privacy (correction 8) and key-record roles (correction 6)."""
from decimal import Decimal

import pytest

from reel_autopsy.bars import Bar
from reel_autopsy.intake_text import MAX_CHARS, extract, privacy_violations
from reel_autopsy.presentation import key_records
from reel_autopsy.simulator import CostModel, simulate


@pytest.mark.parametrize(
    "text,reason",
    [
        ("see https://example.com/post for proof", "url"),
        ("follow @trader_x for more", "handle"),
        ("email me at a.b@example.com", "email"),
        ("call +1 415 555 0100", "phone"),
        ("x" * (MAX_CHARS + 1), "too_long"),
    ],
)
def test_privacy_rejections(text, reason):
    assert reason in privacy_violations(text)
    with pytest.raises(ValueError):
        extract(text)


def test_spans_point_into_text():
    text = "SMA cross 10/30 on BTC daily from 2025-01-01 to 2026-01-01 made +340%"
    assert privacy_violations(text) == ()
    ex = extract(text)
    assert ex.fields, "expected at least one extracted field"
    for f in ex.fields:
        assert 0 <= f.start < f.end <= len(text)
    names = {f.name for f in ex.fields}
    assert {"template", "total_return_pct"} <= names
    tr = next(f for f in ex.fields if f.name == "total_return_pct")
    assert tr.value == "340" and "340" in text[tr.start:tr.end]


def _sim():
    d = Decimal
    bars = tuple(Bar(i * 3600, d(100 + i), d(102 + i), d(99 + i), d(101 + i), d(1)) for i in range(10))
    return simulate(bars, (1, 1, 0, 0, 1, 1, 0, 1, 0, 0), CostModel(d(10), d(5)), d(1))


@pytest.mark.parametrize("status", ["REFUTED", "CONDITIONAL", "IMPOSSIBLE", "SUPPORTED"])
def test_trades_are_always_illustrative(status):
    recs = key_records(finding_id="total_return", finding_status=status,
                       counterexample_points=[{"fee_bps_per_side": "50"}], sim_at_worst_point=_sim())
    for r in recs:
        if r["recordKind"] in ("TRADE", "EQUITY_SERIES"):
            assert r["recordRole"] == "ILLUSTRATIVE"
        if r["recordRole"] == "COUNTEREXAMPLE":
            assert r["recordKind"] == "GRID_POINT" and status != "SUPPORTED"
    assert any(r["recordKind"] == "TRADE" for r in recs)
