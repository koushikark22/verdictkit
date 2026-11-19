"""Exact decimal parsing and monetary rounding for Quote Autopsy."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")


def D(text: str) -> Decimal:
    """Parse a decimal string; reject floats and non-finite input."""
    if not isinstance(text, str):
        raise TypeError("decimal values must be supplied as strings")
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("invalid decimal string") from exc
    if not value.is_finite():
        raise ValueError("non-finite decimal value")
    return value


def cents(x: Decimal) -> Decimal:
    """Round to the nearest cent, ties away from zero (ROUND_HALF_UP)."""
    if not isinstance(x, Decimal):
        raise TypeError("cents() requires Decimal")
    if not x.is_finite():
        raise ValueError("non-finite decimal value")
    return x.quantize(CENT, rounding=ROUND_HALF_UP)
