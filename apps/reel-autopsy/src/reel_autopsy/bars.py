"""OHLCV bars and coverage. Requirements: reel 5.3, 5.4."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum


class Timeframe(str, Enum):
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    @property
    def seconds(self) -> int:
        return {"1h": 3600, "4h": 14400, "1d": 86400}[self.value]


@dataclass(frozen=True, slots=True)
class Bar:
    ts: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


def expected_timestamps(start_ts: int, end_ts: int, timeframe: Timeframe) -> tuple[int, ...]:
    """Aligned bar-open timestamps in the half-open interval [start_ts, end_ts)."""
    step = timeframe.seconds
    if not isinstance(start_ts, int) or not isinstance(end_ts, int):
        raise ValueError("timestamps must be integer UTC epoch seconds")
    if start_ts > end_ts or start_ts % step or end_ts % step:
        raise ValueError("start/end must be ordered and timeframe-aligned")
    return tuple(range(start_ts, end_ts, step))


def find_gaps(bars: tuple[Bar, ...], start_ts: int, end_ts: int, timeframe: Timeframe) -> tuple[int, ...]:
    """Return missing aligned bars without synthesizing or interpolating data."""
    expected = expected_timestamps(start_ts, end_ts, timeframe)
    observed = {bar.ts for bar in bars}
    return tuple(ts for ts in expected if ts not in observed)


def parse_decimal(text: str) -> Decimal:
    """Parse finite, nonnegative decimal text without floating-point conversion."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("decimal value must be a nonempty string")
    try:
        value = Decimal(text.strip())
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    if not value.is_finite() or value < 0:
        raise ValueError("decimal value must be finite and nonnegative")
    return value
