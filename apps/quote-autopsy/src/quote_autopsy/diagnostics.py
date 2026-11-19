"""Post-reveal diagnostics. Requirement: quote 6. Property: P17c.

Registered via ClaimType.diagnose(); the core only calls it after VERDICT_SEALED, and its
output is excluded from verdict_hash.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from .worksheet import FinanceWorksheet


@dataclass(frozen=True, slots=True)
class LocalCheck:
    line: str
    stated: Decimal
    from_stated_predecessors: Decimal
    difference: Decimal
    consistent: bool


@dataclass(frozen=True, slots=True)
class PackingDiagnostic:
    implied_amount_financed: Decimal
    itemised_amount_financed: Decimal
    unexplained_amount: Decimal
    inversion_uncertainty: Decimal  # 0.005 * annuity_factor


def local_checks(ws: FinanceWorksheet, stated: Mapping[str, Decimal]) -> tuple[LocalCheck, ...]:
    raise NotImplementedError("quote task 6.1")


def payment_packing(ws: FinanceWorksheet, stated: Mapping[str, Decimal]) -> PackingDiagnostic | None:
    """None when stated_monthly_payment is absent."""
    raise NotImplementedError("quote task 6.1")
