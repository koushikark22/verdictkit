"""Key forensic records: grid counterexamples; trades and equity are illustrative."""
from __future__ import annotations

from typing import Mapping, Sequence

from .simulator import SimResult


def key_records(
    *,
    finding_id: str,
    finding_status: str,
    counterexample_points: Sequence[Mapping[str, str]],
    sim_at_worst_point: SimResult | None,
    max_trades: int = 5,
) -> list[dict[str, object]]:
    if max_trades < 0:
        raise ValueError("max_trades must be nonnegative")
    records: list[dict[str, object]] = []
    refuted = finding_status in {"REFUTED", "CONDITIONAL", "IMPOSSIBLE"}
    for point in counterexample_points:
        records.append({
            "finding_id": finding_id,
            "kind": "GRID_POINT",
            "role": "COUNTEREXAMPLE" if refuted else "ILLUSTRATIVE",
            "point": dict(point),
        })
    if sim_at_worst_point is not None:
        for fill in sim_at_worst_point.fills[:max_trades]:
            records.append({
                "finding_id": finding_id,
                "kind": "TRADE",
                "role": "ILLUSTRATIVE",
                "bar_index": fill.bar_index,
                "side": fill.side,
                "price": str(fill.price),
                "units": str(fill.units),
                "fee": str(fill.fee),
            })
        records.append({
            "finding_id": finding_id,
            "kind": "EQUITY_SERIES",
            "role": "ILLUSTRATIVE",
            "equity": [str(row.equity) for row in sim_at_worst_point.marks],
        })
    for record in records:
        record["recordKind"] = record["kind"]
        record["recordRole"] = record["role"]
        record["dataLabel"] = "DEMONSTRATION ONLY"

    return records
