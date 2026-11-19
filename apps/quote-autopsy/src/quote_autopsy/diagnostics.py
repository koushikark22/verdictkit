"""Post-reveal diagnostics. Requirement: quote 6. Property: P17c.

Registered via ClaimType.diagnose(); the core only calls it after VERDICT_SEALED, and its
output is excluded from verdict_hash.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from .finance import (
    amount_financed, annuity_factor, chain, implied_amount_financed, monthly_payment,
    sales_tax, taxable_base,
)
from .worksheet import FinanceWorksheet

LABEL = "diagnostic — computed after reveal"
_CENT = Decimal("0.01")
_ZERO = Decimal("0")


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
    """Each stated line against its formula applied to the *stated* preceding lines
    (falling back to the recomputed value when a predecessor was not stated).

    Lines follow the dependency order taxable_base -> sales_tax -> amount_financed ->
    monthly_payment -> total_of_payments -> finance_charge. Only stated lines are checked.
    Tolerance: one cent for the rounded payment, exact for sums and products.
    """
    computed = chain(ws)

    def pred(name: str) -> Decimal:
        return stated[name] if name in stated else getattr(computed, name)

    formulas = (
        ("taxable_base", lambda: taxable_base(ws), _ZERO),
        ("sales_tax", lambda: sales_tax(pred("taxable_base"), ws.stated_tax_rate_pct), _ZERO),
        ("amount_financed", lambda: amount_financed(ws, pred("sales_tax")), _ZERO),
        ("monthly_payment", lambda: monthly_payment(pred("amount_financed"), ws.apr_pct, ws.term_months), _CENT),
        ("total_of_payments", lambda: pred("monthly_payment") * ws.term_months, _ZERO),
        ("finance_charge", lambda: pred("total_of_payments") - pred("amount_financed"), _ZERO),
    )
    checks = []
    for name, formula, tolerance in formulas:
        if name not in stated:
            continue
        try:
            expected = formula()
        except ValueError:
            continue  # e.g. a stated negative amount financed has no payment
        diff = stated[name] - expected
        checks.append(LocalCheck(name, stated[name], expected, diff, abs(diff) <= tolerance))
    return tuple(checks)


def payment_packing(ws: FinanceWorksheet, stated: Mapping[str, Decimal]) -> PackingDiagnostic | None:
    """None when stated_monthly_payment is absent."""
    payment = stated.get("monthly_payment")
    if payment is None:
        return None
    itemised = chain(ws).amount_financed
    implied = implied_amount_financed(payment, ws.apr_pct, ws.term_months)
    factor = annuity_factor(ws.apr_pct, ws.term_months)
    return PackingDiagnostic(
        implied_amount_financed=implied,
        itemised_amount_financed=itemised,
        unexplained_amount=implied - itemised,
        inversion_uncertainty=Decimal("0.005") * factor,
    )


def _s(value: Decimal, places: str = "0.01") -> str:
    from decimal import ROUND_HALF_EVEN
    return format(value.quantize(Decimal(places), rounding=ROUND_HALF_EVEN), "f")


def finance_diagnostics(ws: FinanceWorksheet, stated: Mapping[str, Decimal]) -> dict[str, object]:
    """Post-reveal diagnostic record (quote req 6). Canonical: all numbers are strings."""
    checks = local_checks(ws, stated)
    first_broken = next((c.line for c in checks if not c.consistent), None)
    packing = payment_packing(ws, stated)
    return {
        "label": LABEL,
        "kind": "LOCAL_CHECKS_AND_PAYMENT_PACKING",
        "firstBrokenLine": first_broken,
        "localChecks": [
            {"line": c.line, "stated": format(c.stated, "f"),
             "fromStatedPredecessors": format(c.from_stated_predecessors, "f"),
             "difference": format(c.difference, "f"), "consistent": c.consistent}
            for c in checks
        ],
        "paymentPacking": None if packing is None else {
            "impliedAmountFinanced": _s(packing.implied_amount_financed, "0.0001"),
            "itemisedAmountFinanced": format(packing.itemised_amount_financed, "f"),
            "unexplainedAmount": _s(packing.unexplained_amount, "0.0001"),
            "inversionUncertainty": _s(packing.inversion_uncertainty, "0.0001"),
        },
    }
