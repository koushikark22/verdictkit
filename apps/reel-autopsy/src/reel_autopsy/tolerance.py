"""Half a unit at the precision represented by a claimant decimal (reel 6.2)."""
from __future__ import annotations

import re
from decimal import Decimal


def precision_tolerance(claimed: str) -> Decimal:
    if not isinstance(claimed, str) or not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", claimed):
        raise ValueError("claimed value must be a plain decimal string")
    value = Decimal(claimed)
    return Decimal("0.5").scaleb(value.as_tuple().exponent)
