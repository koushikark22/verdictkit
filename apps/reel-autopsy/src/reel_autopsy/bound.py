"""Cost-free SPOT_LONG_FLAT perfect-foresight upper bound (reel 7)."""
from __future__ import annotations

from decimal import Decimal, localcontext

from .bars import Bar


def interval_returns(bars: tuple[Bar, ...]) -> tuple[Decimal, ...]:
    """Achievable open-to-open changes, with a final open-to-close interval."""
    if len(bars) < 2:
        return ()
    with localcontext() as ctx:
        ctx.prec = 110
        result = []
        for k in range(1, len(bars)):
            entry = bars[k].open
            exit_price = bars[k + 1].open if k + 1 < len(bars) else bars[k].close
            if entry <= 0:
                raise ValueError("open prices must be strictly positive")
            result.append(+(exit_price / entry - 1))
        return tuple(result)


def perfect_foresight_bound_pct(bars: tuple[Bar, ...]) -> Decimal:
    """Compounded product of nonnegative holdable interval returns."""
    with localcontext() as ctx:
        ctx.prec = 110
        product = Decimal(1)
        for r in interval_returns(bars):
            product *= Decimal(1) + max(Decimal(0), r)
        return +((product - 1) * 100)


def oracle_targets(bars: tuple[Bar, ...]) -> tuple[int, ...]:
    """Future-looking oracle, *never* a strategy template or backtest signal."""
    if not bars:
        return ()
    returns = interval_returns(bars)
    return tuple(int(r > 0) for r in returns) + (0,)
