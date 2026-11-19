"""Bounded sensitivity analysis. Requirement: core 7. Property: P11.

Grid enumeration order (normative): axes sorted by assumption name; within an axis,
values ascending (Decimal order; str tokens in code-point order); the grid is the
Cartesian product in that axis order (first axis varies slowest, like itertools.product).
RANGE axis values: minimum, minimum+step, ... while <= maximum.
MISSING axes are excluded from the grid and listed in ``missing``.
Point values are rendered as canonical strings (Decimal via format(d, "f")).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping, Sequence

from .model import GRID_CAP_MAX, Assumption, AssumptionKind


class GridTooLargeError(ValueError):
    def __init__(self, size: int, cap: int) -> None:
        super().__init__(f"assumption grid has {size} points; cap is {cap}")
        self.size = size
        self.cap = cap


@dataclass(frozen=True, slots=True)
class GridExpansion:
    points: tuple[Mapping[str, str], ...]
    missing: tuple[str, ...]


def _axis_values(a: Assumption) -> list[str]:
    """Return the ordered string values for a non-MISSING axis."""
    if a.kind is AssumptionKind.FIXED:
        v = a.value
        if isinstance(v, Decimal):
            return [format(v, "f")]
        return [str(v)]
    if a.kind is AssumptionKind.SET:
        sorted_vals = sorted(a.values, key=lambda x: (Decimal(x) if isinstance(x, Decimal) else x))
        return [format(v, "f") if isinstance(v, Decimal) else str(v) for v in sorted_vals]
    if a.kind is AssumptionKind.RANGE:
        result = []
        v = a.minimum
        while v <= a.maximum:
            result.append(format(v, "f"))
            v += a.step
        return result
    raise ValueError(f"unexpected kind {a.kind}")  # MISSING handled before this call


def _grid_size(axes: list[Assumption]) -> int:
    """Compute the product of axis sizes without materialising the grid."""
    size = 1
    for a in axes:
        if a.kind is AssumptionKind.FIXED:
            size *= 1
        elif a.kind is AssumptionKind.SET:
            size *= len(a.values)
        elif a.kind is AssumptionKind.RANGE:
            vals = []
            v = a.minimum
            while v <= a.maximum:
                vals.append(v)
                v += a.step
            size *= len(vals)
    return size


def expand_grid(assumptions: Sequence[Assumption], cap: int = GRID_CAP_MAX) -> GridExpansion:
    """Raise ValueError if cap > GRID_CAP_MAX or cap < 1; GridTooLargeError if over cap.

    Never subsamples.
    """
    if cap < 1 or cap > GRID_CAP_MAX:
        raise ValueError(f"cap must be between 1 and {GRID_CAP_MAX}, got {cap}")

    missing_names: list[str] = []
    active_axes: list[Assumption] = []

    for a in assumptions:
        if a.kind is AssumptionKind.MISSING:
            missing_names.append(a.name)
        else:
            active_axes.append(a)

    # Sort axes by name (normative order)
    active_axes.sort(key=lambda a: a.name)

    # Compute grid size first so we can reject before materialising
    size = _grid_size(active_axes)
    if size > cap:
        raise GridTooLargeError(size, cap)

    if not active_axes:
        # Zero non-missing axes → one empty point
        points: list[Mapping[str, str]] = [{}]
    else:
        axis_names = [a.name for a in active_axes]
        axis_value_lists = [_axis_values(a) for a in active_axes]
        points = [
            dict(zip(axis_names, combo))
            for combo in itertools.product(*axis_value_lists)
        ]

    return GridExpansion(
        points=tuple(points),
        missing=tuple(sorted(missing_names)),
    )


class AggregateKind(str, Enum):
    ALL_PASS = "ALL_PASS"
    NONE_PASS = "NONE_PASS"
    MIXED = "MIXED"


@dataclass(frozen=True, slots=True)
class PointOutcome:
    point: Mapping[str, str]
    passed: bool
    margin: Decimal  # tolerance - |difference|; negative means failing


@dataclass(frozen=True, slots=True)
class Aggregate:
    kind: AggregateKind
    first_fail: PointOutcome | None
    first_pass: PointOutcome | None
    worst: PointOutcome  # smallest margin; ties -> earliest in order


def aggregate(outcomes: Sequence[PointOutcome]) -> Aggregate:
    """``outcomes`` are in grid order. Empty input raises ValueError."""
    if not outcomes:
        raise ValueError("aggregate requires at least one outcome")

    passed = [o for o in outcomes if o.passed]
    failed = [o for o in outcomes if not o.passed]

    if not failed:
        kind = AggregateKind.ALL_PASS
    elif not passed:
        kind = AggregateKind.NONE_PASS
    else:
        kind = AggregateKind.MIXED

    # Worst = smallest margin; ties → earliest in order (first occurrence)
    min_margin = min(o.margin for o in outcomes)
    worst = next(o for o in outcomes if o.margin == min_margin)

    return Aggregate(
        kind=kind,
        first_fail=failed[0] if failed else None,
        first_pass=passed[0] if passed else None,
        worst=worst,
    )


def findings_blocked_by_missing(
    missing: Sequence[str], dependencies: Mapping[str, Sequence[str]]
) -> frozenset[str]:
    """Finding ids whose declared dependencies intersect ``missing`` (Req 7.3)."""
    missing_set = set(missing)
    return frozenset(
        fid for fid, deps in dependencies.items() if set(deps) & missing_set
    )
