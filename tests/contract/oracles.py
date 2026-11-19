"""Independent exact oracles (fractions.Fraction). These never import implementation code
other than plain data types, so they can catch errors in the implementation's math."""
from __future__ import annotations

import math
from decimal import Decimal
from fractions import Fraction

CENT = Fraction(1, 100)
HALF_CENT_EPS = Fraction(1, 10**12)


def F(x) -> Fraction:
    if isinstance(x, float):
        raise TypeError("oracles never accept floats")
    return Fraction(x) if not isinstance(x, str) else Fraction(Decimal(x))


def round_half_up_cents(x: Fraction) -> Fraction:
    """Decimal ROUND_HALF_UP semantics (ties away from zero) to 0.01."""
    sign = -1 if x < 0 else 1
    scaled = abs(x) * 100
    return sign * Fraction(math.floor(scaled + Fraction(1, 2)), 100)


def near_half_cent(x: Fraction) -> bool:
    """True when x*100 is within 1e-12 of a .5 boundary (rounding is fragile there)."""
    scaled = abs(x) * 100
    frac_part = scaled - math.floor(scaled)
    return abs(frac_part - Fraction(1, 2)) < HALF_CENT_EPS


def to_decimal_cents(x: Fraction) -> Decimal:
    return (Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal("0.01"))


# --- Finance ---------------------------------------------------------------------------

def monthly_rate(apr_pct: Fraction) -> Fraction:
    return apr_pct / 1200


def annuity_factor_exact(apr_pct: Fraction, n: int) -> Fraction:
    if apr_pct == 0:
        return Fraction(n)
    i = monthly_rate(apr_pct)
    return (1 - (1 + i) ** (-n)) / i


def payment_exact(principal: Fraction, apr_pct: Fraction, n: int) -> Fraction:
    return principal / annuity_factor_exact(apr_pct, n)


def finance_chain_oracle(ws) -> dict[str, Fraction]:
    """ws: quote_autopsy.worksheet.FinanceWorksheet with all flags resolved to bool.
    Follows quote requirements 3.1–3.5 literally. Returns unrounded payment too."""
    base = F(ws.selling_price)
    base += sum((F(a.amount) for a in ws.addons if a.taxable), Fraction(0))
    if ws.doc_fee_taxable:
        base += F(ws.doc_fee)
    base += sum((F(g.amount) for g in ws.gov_fees if g.taxable), Fraction(0))
    if ws.trade_tax_credit:
        base -= F(ws.trade_allowance)
    base -= sum((F(r.amount) for r in ws.rebates if r.applied.value == "PRE_TAX"), Fraction(0))
    base = max(base, Fraction(0))
    tax_exact = base * F(ws.stated_tax_rate_pct) / 100
    tax = round_half_up_cents(tax_exact)
    af = (
        F(ws.selling_price)
        + sum((F(a.amount) for a in ws.addons), Fraction(0))
        + F(ws.doc_fee)
        + sum((F(g.amount) for g in ws.gov_fees), Fraction(0))
        + tax
        - F(ws.trade_allowance)
        + F(ws.trade_payoff)
        - sum((F(r.amount) for r in ws.rebates), Fraction(0))
        - F(ws.cash_down)
    )
    pay_exact = payment_exact(af, F(ws.apr_pct), ws.term_months) if af > 0 else Fraction(0)
    pay = round_half_up_cents(pay_exact)
    top = pay * ws.term_months
    return {
        "taxable_base": base,
        "tax_exact": tax_exact,
        "sales_tax": tax,
        "amount_financed": af,
        "payment_exact": pay_exact,
        "monthly_payment": pay,
        "total_of_payments": top,
        "finance_charge": top - af,
    }


# --- Lease -----------------------------------------------------------------------------

def lease_exact_base(adj_cap: Fraction, residual: Fraction, mf: Fraction, n: int) -> Fraction:
    return (adj_cap - residual) / n + (adj_cap + residual) * mf


# --- Reel ------------------------------------------------------------------------------

def interval_returns_oracle(bars) -> list[Fraction]:
    n = len(bars)
    out = []
    for k in range(1, n):
        if k < n - 1:
            out.append(F(bars[k + 1].open) / F(bars[k].open) - 1)
        else:
            out.append(F(bars[n - 1].close) / F(bars[n - 1].open) - 1)
    return out


def bound_pct_oracle(bars) -> Fraction:
    prod = Fraction(1)
    for r in interval_returns_oracle(bars):
        prod *= 1 + max(r, Fraction(0))
    return (prod - 1) * 100


def buy_and_hold_return_pct_oracle(bars) -> Fraction:
    """Zero cost, fraction 1: buy at open[1], mark at close[n-1]."""
    return (F(bars[-1].close) / F(bars[1].open) - 1) * 100
