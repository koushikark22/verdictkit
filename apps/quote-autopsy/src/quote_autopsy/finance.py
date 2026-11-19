"""Retail-installment arithmetic. Requirements: quote 3, 6.2. Properties: P16, P16b, P17b."""
from __future__ import annotations

from decimal import Decimal, localcontext

from .money import cents
from .worksheet import FinanceChain, FinanceWorksheet, RebateTiming

_ZERO = Decimal(0)
_HUNDRED = Decimal(100)
_TWELVE_HUNDRED = Decimal(1200)


def _check_flags(ws: FinanceWorksheet) -> None:
    if ws.doc_fee_taxable is None or ws.trade_tax_credit is None:
        raise ValueError("unresolved taxability flag")
    if any(item.taxable is None for item in ws.addons):
        raise ValueError("unresolved add-on taxability flag")
    if any(fee.taxable is None for fee in ws.gov_fees):
        raise ValueError("unresolved government-fee taxability flag")


def taxable_base(ws: FinanceWorksheet) -> Decimal:
    """Price plus taxable charges, less pre-tax rebates and eligible trade credit."""
    _check_flags(ws)
    base = ws.selling_price
    base += sum((item.amount for item in ws.addons if item.taxable), _ZERO)
    if ws.doc_fee_taxable:
        base += ws.doc_fee
    base += sum((fee.amount for fee in ws.gov_fees if fee.taxable), _ZERO)
    base -= sum((rebate.amount for rebate in ws.rebates if rebate.applied == RebateTiming.PRE_TAX), _ZERO)
    if ws.trade_tax_credit:
        base -= ws.trade_allowance
    return base


def sales_tax(base: Decimal, rate_pct: Decimal) -> Decimal:
    """Apply the declared percentage and round tax half-up to whole cents."""
    with localcontext() as ctx:
        ctx.prec = 80
        return cents(base * rate_pct / _HUNDRED)


def amount_financed(ws: FinanceWorksheet, tax: Decimal) -> Decimal:
    """Cash selling amount less credits and down payment, plus payoff and tax."""
    gross = ws.selling_price
    gross += sum((item.amount for item in ws.addons), _ZERO)
    gross += ws.doc_fee
    gross += sum((fee.amount for fee in ws.gov_fees), _ZERO)
    gross += tax
    gross += ws.trade_payoff
    gross -= ws.trade_allowance
    gross -= ws.cash_down
    gross -= sum((rebate.amount for rebate in ws.rebates), _ZERO)
    return gross


def annuity_factor(apr_pct: Decimal, n: int) -> Decimal:
    """Exact-to-working-precision annuity factor; no monetary rounding."""
    if n < 1:
        raise ValueError("term must be a positive integer")
    if apr_pct < 0:
        raise ValueError("APR must be nonnegative")
    if apr_pct == 0:
        return Decimal(n)
    with localcontext() as ctx:
        ctx.prec = 80
        i = apr_pct / _TWELVE_HUNDRED
        return (Decimal(1) - (Decimal(1) + i) ** (-n)) / i


def monthly_payment(af: Decimal, apr_pct: Decimal, n: int) -> Decimal:
    """Monthly fully-amortizing payment, rounded once at the end."""
    if n < 1:
        raise ValueError("term must be a positive integer")
    if af < 0 or apr_pct < 0:
        raise ValueError("financed amount and APR must be nonnegative")
    with localcontext() as ctx:
        ctx.prec = 80
        return cents(af / annuity_factor(apr_pct, n))


def implied_amount_financed(payment: Decimal, apr_pct: Decimal, n: int) -> Decimal:
    """Diagnostic inversion of a disclosed payment; deliberately unrounded."""
    with localcontext() as ctx:
        ctx.prec = 80
        return payment * annuity_factor(apr_pct, n)


def chain(ws: FinanceWorksheet) -> FinanceChain:
    """Build the dependency-ordered, blind retail-installment worksheet."""
    base = taxable_base(ws)
    tax = sales_tax(base, ws.stated_tax_rate_pct)
    af = amount_financed(ws, tax)
    payment = monthly_payment(af, ws.apr_pct, ws.term_months)
    total = payment * ws.term_months
    return FinanceChain(
        taxable_base=base,
        sales_tax=tax,
        amount_financed=af,
        monthly_payment=payment,
        total_of_payments=total,
        finance_charge=total - af,
    )
