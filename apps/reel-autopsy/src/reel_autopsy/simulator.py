"""Deterministic spot long/flat simulator, next-bar-open fills (reel 3)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, localcontext

from .bars import Bar

START_EQUITY = Decimal("10000")


@dataclass(frozen=True, slots=True)
class CostModel:
    fee_bps: Decimal
    slippage_bps: Decimal


@dataclass(frozen=True, slots=True)
class Fill:
    bar_index: int
    side: str
    price: Decimal
    units: Decimal
    fee: Decimal


@dataclass(frozen=True, slots=True)
class MarkRow:
    bar_index: int
    cash: Decimal
    units: Decimal
    close: Decimal
    equity: Decimal


@dataclass(frozen=True, slots=True)
class SimResult:
    start_equity: Decimal
    marks: tuple[MarkRow, ...]
    fills: tuple[Fill, ...]


def simulate(
    bars: tuple[Bar, ...],
    targets: tuple[int, ...],
    costs: CostModel,
    position_fraction: Decimal,
    start_equity: Decimal = START_EQUITY,
) -> SimResult:
    """Fill target[t] on bar t+1 open; mark cash+units*close every bar."""
    if len(targets) != len(bars) or any(t not in (0, 1) for t in targets):
        raise ValueError("targets must be one 0/1 position per bar")
    if not position_fraction.is_finite() or not (0 < position_fraction <= 1):
        raise ValueError("position_fraction must be in (0,1]")
    if not start_equity.is_finite() or start_equity <= 0:
        raise ValueError("start_equity must be positive")
    if any(not x.is_finite() or x < 0 for x in (costs.fee_bps, costs.slippage_bps)):
        raise ValueError("costs must be finite and nonnegative")
    if costs.slippage_bps >= 10000:
        raise ValueError("slippage must be below 10000 bps")

    with localcontext() as ctx:
        ctx.prec = 110
        cash = +start_equity
        units = Decimal(0)
        state = 0
        marks: list[MarkRow] = []
        fills: list[Fill] = []
        fee_rate = costs.fee_bps / 10000
        slip_rate = costs.slippage_bps / 10000

        for i, bar in enumerate(bars):
            if bar.open <= 0 or bar.close <= 0:
                raise ValueError("prices must be strictly positive")
            if i:
                desired = targets[i - 1]
                if desired != state:
                    if desired == 1:
                        fill_price = bar.open * (1 + slip_rate)
                        equity_at_open = cash + units * bar.open
                        spend = position_fraction * equity_at_open
                        if spend > cash:
                            spend = cash
                        # Quantize to current significant digit budget, always downward.
                        with localcontext() as down:
                            down.prec = 100
                            down.rounding = ROUND_DOWN
                            buy_units = +(spend / (fill_price * (1 + fee_rate)))
                        fee = buy_units * fill_price * fee_rate
                        debit = buy_units * fill_price + fee
                        cash -= debit
                        if cash < 0:
                            if cash >= -(Decimal("1e-30") * max(spend, Decimal(1))):
                                cash = Decimal(0)
                            else:
                                raise ArithmeticError("negative cash after buy")
                        units += buy_units
                        fills.append(Fill(i, "BUY", +fill_price, +buy_units, +fee))
                    else:
                        fill_price = bar.open * (1 - slip_rate)
                        sold_units = units
                        fee = sold_units * fill_price * fee_rate
                        cash += sold_units * fill_price - fee
                        units = Decimal(0)
                        fills.append(Fill(i, "SELL", +fill_price, +sold_units, +fee))
                    state = desired
            equity = cash + units * bar.close
            marks.append(MarkRow(i, +cash, +units, +bar.close, +equity))
        return SimResult(+start_equity, tuple(marks), tuple(fills))
