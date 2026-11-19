"""Worksheet models. Requirements: quote 1, 2.

Finance flags are ``bool`` once resolved. Unknown flags (``None``) are resolved per sweep
point by the claim type before calling ``finance.chain``.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class AddonCode(str, Enum):
    SERVICE_CONTRACT = "SERVICE_CONTRACT"
    GAP = "GAP"
    PAINT_PROTECTION = "PAINT_PROTECTION"
    THEFT_ETCH = "THEFT_ETCH"
    TIRE_WHEEL = "TIRE_WHEEL"
    OTHER = "OTHER"


class GovFeeCode(str, Enum):
    TITLE = "TITLE"
    REGISTRATION = "REGISTRATION"
    PLATE = "PLATE"
    OTHER = "OTHER"


class RebateTiming(str, Enum):
    PRE_TAX = "PRE_TAX"
    POST_TAX = "POST_TAX"


class LeaseConvention(str, Enum):
    COMPONENT = "COMPONENT"
    FINAL = "FINAL"


@dataclass(frozen=True, slots=True)
class Addon:
    code: AddonCode
    amount: Decimal
    taxable: bool | None


@dataclass(frozen=True, slots=True)
class GovFee:
    code: GovFeeCode
    amount: Decimal
    taxable: bool | None


@dataclass(frozen=True, slots=True)
class Rebate:
    amount: Decimal
    applied: RebateTiming


@dataclass(frozen=True, slots=True)
class Jurisdiction:
    state: str  # two-letter
    locality_code: str | None = None


@dataclass(frozen=True, slots=True)
class FinanceWorksheet:
    selling_price: Decimal
    addons: tuple[Addon, ...]
    doc_fee: Decimal
    doc_fee_taxable: bool | None
    gov_fees: tuple[GovFee, ...]
    rebates: tuple[Rebate, ...]
    trade_allowance: Decimal
    trade_payoff: Decimal
    trade_tax_credit: bool | None
    cash_down: Decimal
    stated_tax_rate_pct: Decimal
    apr_pct: Decimal
    term_months: int
    jurisdiction: Jurisdiction


@dataclass(frozen=True, slots=True)
class FinanceChain:
    taxable_base: Decimal
    sales_tax: Decimal
    amount_financed: Decimal
    monthly_payment: Decimal
    total_of_payments: Decimal
    finance_charge: Decimal


@dataclass(frozen=True, slots=True)
class LeaseNumbers:
    depreciation_fee: Decimal
    rent_charge: Decimal
    base_payment: Decimal
    monthly_tax: Decimal
    total_monthly_payment: Decimal
