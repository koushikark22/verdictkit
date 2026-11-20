"""P11 bounded, ordered sweep with explicit missing-assumption handling. Core requirement 7."""
import itertools
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from verdictkit.model import Assumption, AssumptionKind, Origin
from verdictkit.sweep import (
    AggregateKind,
    GridTooLargeError,
    PointOutcome,
    aggregate,
    expand_grid,
    findings_blocked_by_missing,
)

NAMES = ["alpha", "beta", "fee_bps", "slip_bps", "zeta"]


@st.composite
def assumption(draw, name):
    kind = draw(st.sampled_from(list(AssumptionKind)))
    origin = draw(st.sampled_from(list(Origin)))
    if kind is AssumptionKind.FIXED:
        return Assumption(name, kind, origin, value=Decimal(draw(st.integers(0, 50))))
    if kind is AssumptionKind.RANGE:
        lo = draw(st.integers(0, 5))
        step = draw(st.integers(1, 3))
        hi = draw(st.integers(lo, lo + 10))
        return Assumption(name, kind, origin, minimum=Decimal(lo), maximum=Decimal(hi), step=Decimal(step))
    if kind is AssumptionKind.SET:
        vals = draw(st.lists(st.integers(0, 99), min_size=1, max_size=4, unique=True))
        return Assumption(name, kind, origin, values=tuple(Decimal(v) for v in vals))
    return Assumption(name, kind, origin)


@st.composite
def assumption_lists(draw):
    names = draw(st.lists(st.sampled_from(NAMES), min_size=0, max_size=4, unique=True))
    items = [draw(assumption(n)) for n in names]
    return draw(st.permutations(items))


def axis_values(a: Assumption):
    if a.kind is AssumptionKind.FIXED:
        return [a.value]
    if a.kind is AssumptionKind.SET:
        return sorted(a.values)
    if a.kind is AssumptionKind.RANGE:
        out, v = [], a.minimum
        while v <= a.maximum:
            out.append(v)
            v += a.step
        return out
    return None


def reference_points(assumptions):
    axes = sorted((a for a in assumptions if a.kind is not AssumptionKind.MISSING), key=lambda a: a.name)
    names = [a.name for a in axes]
    combos = itertools.product(*[axis_values(a) for a in axes])
    return [dict(zip(names, (format(v, "f") for v in c), strict=False)) for c in combos]


@given(assumption_lists())
def test_grid_matches_reference_order_and_size(assumptions):
    """P11: size = product of axis sizes; order is name-sorted, values ascending;
    grids above the cap are rejected, never subsampled."""
    expected = reference_points(assumptions)
    if len(expected) > 1000:
        with pytest.raises(GridTooLargeError) as e:
            expand_grid(assumptions, cap=1000)
        assert e.value.size == len(expected)
        return
    g = expand_grid(assumptions, cap=1000)
    assert [dict(p) for p in g.points] == expected
    assert sorted(g.missing) == sorted(a.name for a in assumptions if a.kind is AssumptionKind.MISSING)


def test_over_cap_rejected_never_subsampled():
    axes = [
        Assumption(n, AssumptionKind.RANGE, Origin.DEFAULT_POLICY,
                   minimum=Decimal(0), maximum=Decimal(10), step=Decimal(1))
        for n in ("a", "b", "c")
    ]  # 11^3 = 1331 points
    with pytest.raises(GridTooLargeError) as e:
        expand_grid(axes, cap=1000)
    assert e.value.size == 1331


@pytest.mark.parametrize("cap", [0, 1001, 5000])
def test_cap_cannot_exceed_max(cap):
    with pytest.raises(ValueError):
        expand_grid([], cap=cap)


@given(st.lists(st.tuples(st.booleans(), st.integers(-50, 50)), min_size=1, max_size=20))
def test_aggregate_selection(rows):
    """Req 7.6: kind, first fail, first pass, worst margin (ties -> earliest)."""
    outs = [PointOutcome(point={"i": str(i)}, passed=p, margin=Decimal(m)) for i, (p, m) in enumerate(rows)]
    agg = aggregate(outs)
    passed = [o for o in outs if o.passed]
    failed = [o for o in outs if not o.passed]
    if not failed:
        assert agg.kind is AggregateKind.ALL_PASS
    elif not passed:
        assert agg.kind is AggregateKind.NONE_PASS
    else:
        assert agg.kind is AggregateKind.MIXED
    assert agg.first_fail == (failed[0] if failed else None)
    assert agg.first_pass == (passed[0] if passed else None)
    min_margin = min(o.margin for o in outs)
    assert agg.worst == next(o for o in outs if o.margin == min_margin)


def test_aggregate_empty_rejected():
    with pytest.raises(ValueError):
        aggregate([])


@given(
    st.lists(st.sampled_from(NAMES), unique=True),
    st.dictionaries(st.sampled_from(["f1", "f2", "f3"]), st.lists(st.sampled_from(NAMES), unique=True)),
)
def test_missing_blocks_only_dependent_findings(missing, deps):
    """Req 7.3: only findings that depend on a missing assumption are blocked."""
    blocked = findings_blocked_by_missing(missing, deps)
    assert blocked == frozenset(f for f, d in deps.items() if set(d) & set(missing))
