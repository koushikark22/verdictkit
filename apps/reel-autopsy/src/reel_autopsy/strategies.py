"""Mechanical templates using only data observable at or before bar t."""
from __future__ import annotations

from decimal import Decimal, localcontext
from enum import Enum
from typing import Mapping

from .bars import Bar


class Template(str, Enum):
    BUY_AND_HOLD = "BUY_AND_HOLD"
    SMA_CROSS = "SMA_CROSS"
    DONCHIAN_BREAKOUT = "DONCHIAN_BREAKOUT"
    RSI_REVERSION = "RSI_REVERSION"


PARAM_NAMES: Mapping[Template, tuple[str, ...]] = {
    Template.BUY_AND_HOLD: (),
    Template.SMA_CROSS: ("fast", "slow"),
    Template.DONCHIAN_BREAKOUT: ("lookback",),
    Template.RSI_REVERSION: ("period", "lower", "upper"),
}


def validate_params(template: Template, params: Mapping[str, int]) -> None:
    if template not in PARAM_NAMES:
        raise ValueError("unknown strategy")
    expected = set(PARAM_NAMES[template])
    if set(params) != expected:
        raise ValueError("strategy parameters do not match template")
    for key, value in params.items():
        if type(value) is not int:
            raise ValueError(f"{key} must be an integer")
    periods = [params[k] for k in ("fast", "slow", "lookback", "period") if k in params]
    if any(not (2 <= p <= 400) for p in periods):
        raise ValueError("periods must be between 2 and 400")
    if template is Template.SMA_CROSS and params["fast"] >= params["slow"]:
        raise ValueError("fast must be less than slow")
    if template is Template.RSI_REVERSION and not (0 < params["lower"] < params["upper"] < 100):
        raise ValueError("RSI bands must satisfy 0 < lower < upper < 100")


def target_positions(template: Template, params: Mapping[str, int], bars: tuple[Bar, ...]) -> tuple[int, ...]:
    validate_params(template, params)
    if template is Template.BUY_AND_HOLD:
        return tuple(1 for _ in bars)
    targets: list[int] = []
    with localcontext() as ctx:
        ctx.prec = 80
        closes = [bar.close for bar in bars]
        for i, close in enumerate(closes):
            previous = targets[-1] if targets else 0
            if template is Template.SMA_CROSS:
                fast, slow = params["fast"], params["slow"]
                if i + 1 < slow:
                    targets.append(0)
                else:
                    fast_sma = sum(closes[i + 1 - fast:i + 1]) / fast
                    slow_sma = sum(closes[i + 1 - slow:i + 1]) / slow
                    targets.append(int(fast_sma > slow_sma))
            elif template is Template.DONCHIAN_BREAKOUT:
                lookback = params["lookback"]
                if i < lookback:
                    targets.append(0)
                else:
                    previous_high = max(bar.high for bar in bars[i - lookback:i])
                    previous_low = min(bar.low for bar in bars[i - lookback:i])
                    if close > previous_high:
                        targets.append(1)
                    elif close < previous_low:
                        targets.append(0)
                    else:
                        targets.append(previous)
            elif template is Template.RSI_REVERSION:
                period = params["period"]
                if i < period:
                    targets.append(0)
                    continue
                changes = [closes[j] - closes[j - 1] for j in range(i - period + 1, i + 1)]
                gain = sum((max(d, Decimal(0)) for d in changes), Decimal(0))
                loss = sum((max(-d, Decimal(0)) for d in changes), Decimal(0))
                rsi = Decimal(100) if loss == 0 else Decimal(100) * gain / (gain + loss)
                if rsi < params["lower"]:
                    targets.append(1)
                elif rsi > params["upper"]:
                    targets.append(0)
                else:
                    targets.append(previous)
    return tuple(targets)
