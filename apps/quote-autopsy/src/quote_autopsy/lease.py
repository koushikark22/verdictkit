"""Lease arithmetic using explicit component versus final rounding conventions."""
from __future__ import annotations

from decimal import Decimal, localcontext

from .money import cents
from .worksheet import LeaseConvention, LeaseNumbers


def residual_from_pct(msrp: Decimal, residual_pct: Decimal) -> Decimal:
    """Contract residual value, rounded half-up to whole cents."""
    with localcontext() as ctx:
        ctx.prec = 80
        return cents(msrp * residual_pct / Decimal(100))


def compute(
    adjusted_cap_cost: Decimal,
    residual_value: Decimal,
    money_factor: Decimal,
    n: int,
    tax_rate_pct: Decimal,
    convention: LeaseConvention,
) -> LeaseNumbers:
    """Compute a lease's depreciation, rent, base, tax, and monthly payment."""
    if n < 1:
        raise ValueError("lease term must be positive")
    if residual_value > adjusted_cap_cost:
        raise ValueError("residual cannot exceed adjusted capitalized cost")
    if money_factor < 0 or tax_rate_pct < 0:
        raise ValueError("money factor and tax rate must be nonnegative")
    if not isinstance(convention, LeaseConvention):
        raise ValueError("unknown lease rounding convention")

    with localcontext() as ctx:
        ctx.prec = 80
        dep_exact = (adjusted_cap_cost - residual_value) / Decimal(n)
        rent_exact = (adjusted_cap_cost + residual_value) * money_factor
        base_exact = dep_exact + rent_exact
        tax_factor = tax_rate_pct / Decimal(100)

        if convention == LeaseConvention.COMPONENT:
            dep = cents(dep_exact)
            rent = cents(rent_exact)
            base = dep + rent
            tax = cents(base * tax_factor)
            total = base + tax
        else:
            # Expose exact components while rounding the independent lines
            # only at their prescribed final reporting points.
            dep = dep_exact
            rent = rent_exact
            base = cents(base_exact)
            tax = cents(base_exact * tax_factor)
            total = cents(base_exact * (Decimal(1) + tax_factor))

    return LeaseNumbers(
        depreciation_fee=dep,
        rent_charge=rent,
        base_payment=base,
        monthly_tax=tax,
        total_monthly_payment=total,
    )
