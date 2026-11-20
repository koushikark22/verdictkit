"""Reel Autopsy contract: P13 no lookahead, P14 accounting, P15 bound, P15b costs.
Reel requirements 2, 3, 4, 6.2, 7."""
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from contract.oracles import F, bound_pct_oracle, buy_and_hold_return_pct_oracle, interval_returns_oracle
from reel_autopsy.bars import Bar
from reel_autopsy.bound import interval_returns, oracle_targets, perfect_foresight_bound_pct
from reel_autopsy.metrics import total_return_pct, trade_count
from reel_autopsy.simulator import START_EQUITY, CostModel, simulate
from reel_autopsy.strategies import Template, target_positions
from reel_autopsy.tolerance import precision_tolerance

ZERO = CostModel(Decimal(0), Decimal(0))
EPS = Decimal("1e-18")


@st.composite
def bar_at(draw, i):
    o = draw(st.integers(100, 100_000))
    c = draw(st.integers(100, 100_000))
    hi = max(o, c) + draw(st.integers(0, 500))
    lo = max(1, min(o, c) - draw(st.integers(0, 500)))
    d = lambda x: Decimal(x).scaleb(-2)  # noqa: E731
    return Bar(ts=i * 3600, open=d(o), high=d(hi), low=d(lo), close=d(c), volume=d(draw(st.integers(0, 10**6))))


@st.composite
def bar_series(draw, min_n=3, max_n=40):
    n = draw(st.integers(min_n, max_n))
    return tuple(draw(bar_at(i)) for i in range(n))


@st.composite
def template_and_params(draw):
    t = draw(st.sampled_from(list(Template)))
    if t is Template.SMA_CROSS:
        fast = draw(st.integers(2, 5))
        return t, {"fast": fast, "slow": draw(st.integers(fast + 1, 10))}
    if t is Template.DONCHIAN_BREAKOUT:
        return t, {"lookback": draw(st.integers(2, 8))}
    if t is Template.RSI_REVERSION:
        return t, {"period": draw(st.integers(2, 8)), "lower": draw(st.integers(10, 40)), "upper": draw(st.integers(60, 90))}
    return t, {}


costs_st = st.builds(
    CostModel,
    fee_bps=st.integers(0, 100).map(Decimal),
    slippage_bps=st.integers(0, 100).map(Decimal),
)
fraction_st = st.sampled_from([Decimal("0.25"), Decimal("0.5"), Decimal("0.75"), Decimal("1")])


@given(bar_series(), template_and_params(), st.data())
def test_no_lookahead(bars, tp, data):
    """P13 / Req 2.1: target[0..t] is unchanged when bars after t are replaced."""
    template, params = tp
    t = data.draw(st.integers(0, len(bars) - 1))
    tail = tuple(data.draw(bar_at(i)) for i in range(t + 1, len(bars)))
    a = target_positions(template, params, bars)
    b = target_positions(template, params, bars[: t + 1] + tail)
    assert len(a) == len(bars) and set(a) <= {0, 1}
    assert a[: t + 1] == b[: t + 1]


@given(bar_series(), st.data(), costs_st, fraction_st)
def test_accounting_identity(bars, data, costs, frac):
    """P14 / Req 3.4–3.5: equity = cash + units*close; cash, units never negative."""
    targets = tuple(data.draw(st.lists(st.sampled_from([0, 1]), min_size=len(bars), max_size=len(bars))))
    sim = simulate(bars, targets, costs, frac)
    assert len(sim.marks) == len(bars)
    with localcontext() as ctx:
        ctx.prec = 34
        for row in sim.marks:
            assert row.cash >= 0 and row.units >= 0
            assert abs(row.equity - (row.cash + row.units * row.close)) <= EPS * max(Decimal(1), row.equity)


@given(bar_series())
def test_flat_is_constant(bars):
    sim = simulate(bars, tuple(0 for _ in bars), ZERO, Decimal(1))
    assert all(r.equity == START_EQUITY for r in sim.marks) and trade_count(sim) == 0


@given(bar_series(min_n=2))
def test_bound_matches_exact_oracle(bars):
    """Req 7.1–7.2: implementation equals the Fraction oracle."""
    assert len(interval_returns(bars)) == len(bars) - 1
    for got, exp in zip(interval_returns(bars), interval_returns_oracle(bars), strict=False):
        assert abs(F(got) - exp) <= Fraction(1, 10**25)
    exp = bound_pct_oracle(bars)
    assert abs(F(perfect_foresight_bound_pct(bars)) - exp) <= Fraction(1, 10**20) * (1 + abs(exp))


@given(bar_series(), st.data(), fraction_st)
def test_bound_sound_and_tight(bars, data, frac):
    """P15: no zero-cost 0/1 strategy beats the bound; the oracle sequence attains it."""
    bound = perfect_foresight_bound_pct(bars)
    targets = tuple(data.draw(st.lists(st.sampled_from([0, 1]), min_size=len(bars), max_size=len(bars))))
    assert total_return_pct(simulate(bars, targets, ZERO, frac)) <= bound + EPS * (1 + abs(bound))
    best = total_return_pct(simulate(bars, oracle_targets(bars), ZERO, Decimal(1)))
    assert abs(best - bound) <= Decimal("1e-15") * (1 + abs(bound))


@given(bar_series(), st.data(), fraction_st, st.integers(0, 100), st.integers(0, 100))
def test_costs_never_help(bars, data, frac, fee_a, extra):
    """P15b: raising the fee (same slippage) never increases final equity."""
    targets = tuple(data.draw(st.lists(st.sampled_from([0, 1]), min_size=len(bars), max_size=len(bars))))
    slip = Decimal(data.draw(st.integers(0, 50)))
    lo = simulate(bars, targets, CostModel(Decimal(fee_a), slip), frac).marks[-1].equity
    hi = simulate(bars, targets, CostModel(Decimal(fee_a + extra), slip), frac).marks[-1].equity
    assert hi <= lo + EPS * lo


@given(bar_series())
def test_buy_and_hold_matches_oracle(bars):
    """Req 3.1, 4.1: zero-cost buy-and-hold fills at open[1] and marks at the last close."""
    sim = simulate(bars, target_positions(Template.BUY_AND_HOLD, {}, bars), ZERO, Decimal(1))
    exp = buy_and_hold_return_pct_oracle(bars)
    assert abs(F(total_return_pct(sim)) - exp) <= Fraction(1, 10**15) * (1 + abs(exp))
    assert trade_count(sim) == 1


@pytest.mark.parametrize(
    "claimed,tol",
    [("340", "0.5"), ("340.2", "0.05"), ("-12.50", "0.005"), ("0", "0.5"), ("1000", "0.5")],
)
def test_precision_tolerance(claimed, tol):
    """Req 6.2."""
    assert precision_tolerance(claimed) == Decimal(tol)


def test_no_fill_on_final_bar():
    """Req 3.1: a target change on the last bar does not fill."""
    d = Decimal
    bars = tuple(Bar(i, d(100), d(101), d(99), d(100), d(1)) for i in range(3))
    sim = simulate(bars, (0, 0, 1), ZERO, d(1))
    assert trade_count(sim) == 0
