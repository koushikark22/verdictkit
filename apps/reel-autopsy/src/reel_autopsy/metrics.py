"""Deterministic backtest summary metrics (reel 4)."""
from __future__ import annotations

from decimal import Decimal, localcontext

from .simulator import SimResult


def total_return_pct(sim: SimResult) -> Decimal:
    if not sim.marks:
        return Decimal(0)
    with localcontext() as ctx:
        ctx.prec = 110
        return +((sim.marks[-1].equity / sim.start_equity - 1) * 100)


def max_drawdown_pct(sim: SimResult) -> Decimal:
    """Largest peak-to-trough close-marked equity decline, in percent."""
    with localcontext() as ctx:
        ctx.prec = 110
        peak = sim.start_equity
        worst = Decimal(0)
        for mark in sim.marks:
            peak = max(peak, mark.equity)
            if peak > 0:
                worst = max(worst, (peak - mark.equity) / peak * 100)
        return +worst


def trade_count(sim: SimResult) -> int:
    return sum(fill.side == "BUY" for fill in sim.fills)


def win_rate_pct(sim: SimResult) -> Decimal | None:
    """Percentage of closed BUY/SELL round trips with positive net realized P&L."""
    with localcontext() as ctx:
        ctx.prec = 110
        cost_basis = None
        wins = 0
        closed = 0
        for fill in sim.fills:
            if fill.side == "BUY":
                cost_basis = fill.units * fill.price + fill.fee
            elif fill.side == "SELL" and cost_basis is not None:
                proceeds = fill.units * fill.price - fill.fee
                wins += int(proceeds > cost_basis)
                closed += 1
                cost_basis = None
        return +(Decimal(wins) / Decimal(closed) * 100) if closed else None
