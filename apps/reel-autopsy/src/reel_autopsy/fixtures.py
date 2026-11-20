"""Trusted SYNTHETIC_DEMO fixture claims (reel task 8; API contract §3).

These are *constructed* claims about the labelled synthetic series ``SYNTH-USD``. Their
claimed values were chosen after running the engine so that each fixture demonstrates
one verdict status; the statuses themselves are always computed by the engine at run
time, and ``tests/integration/test_reel_synthetic_demo.py`` asserts them. A
SYNTHETIC_DEMO case can only be created from one of these ids; users cannot submit
their own claims against synthetic data.
"""
from __future__ import annotations

from types import MappingProxyType

from .sources.synthetic import INSTRUMENT


def _claim(template: str, template_params: dict, outcomes: dict) -> dict:
    return {
        "claim_type": "reel.mechanical.v1",
        "schema_version": 1,
        "params": {
            "instrument": INSTRUMENT, "timeframe": "1d", "start": "2025-01-01",
            "end": "2026-01-01", "template": template, "template_params": template_params,
            "instrument_mode": "SPOT_LONG_FLAT",
        },
        "outcomes": outcomes,
        "assumptions": {},
    }


FIXTURES = MappingProxyType({
    # Exact trade count holds at every cost grid point -> SUPPORTED.
    "fx_reel_supported_hold": _claim("BUY_AND_HOLD", {}, {"trade_count": "1"}),
    # Claimed return is reproduced only at some fee/slippage points -> CONDITIONAL.
    "fx_reel_conditional_sma": _claim("SMA_CROSS", {"fast": 10, "slow": 30},
                                      {"total_return_pct": "-37"}),
    # Claimed return exceeds the perfect-foresight bound -> IMPOSSIBLE.
    "fx_reel_impossible_sma": _claim("SMA_CROSS", {"fast": 10, "slow": 30},
                                     {"total_return_pct": "3400"}),
})

TITLES = MappingProxyType({
    "fx_reel_supported_hold": "Synthetic demo: buy-and-hold trade count",
    "fx_reel_conditional_sma": "Synthetic demo: SMA 10/30 return depends on costs",
    "fx_reel_impossible_sma": "Synthetic demo: SMA 10/30 claim above the bound",
})
