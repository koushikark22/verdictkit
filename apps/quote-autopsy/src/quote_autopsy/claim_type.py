"""VerdictKit adapters for mechanical quote arithmetic.

Boundary: examination never reads claimed outcomes. External legal/rule claims are
INDETERMINATE until an independent evidence provider is configured.

Internal input is intentionally explicit; it is not the frozen HTTP DTO.
Finance params: selling_price, doc_fee, trade_allowance, trade_payoff,
 cash_down, stated_tax_rate_pct, apr_pct (decimal strings), term_months (int),
 doc_fee_taxable, trade_tax_credit (bool), addons, gov_fees, rebates,
 jurisdiction {state, locality_code?}.
Lease params: adjusted_cap_cost, residual_value, money_factor, tax_rate_pct
 (decimal strings), term_months (int), rounding_convention (COMPONENT|FINAL).
"""
from __future__ import annotations

from dataclasses import fields
from decimal import Decimal
from typing import Mapping, Sequence

from verdictkit.custody.intake import SchemaError
from verdictkit.model import (
    Assumption, AssumptionKind, Basis, Counterexample, Finding, Origin,
    Status, FrozenClaim, BlindedTask, EvidenceItem,
)
from verdictkit.plugin import (
    EvidencePolicySpec, EvidenceRequest, EvidenceReader,
    Examination, PointResult,
)
from verdictkit.sweep import PointOutcome, aggregate, AggregateKind

from .finance import chain
from .lease import compute
from .money import D
from .worksheet import (
    Addon, AddonCode, FinanceWorksheet, GovFee, GovFeeCode, Jurisdiction,
    Rebate, RebateTiming, LeaseConvention,
)


def _money(value: object, name: str) -> Decimal:
    if not isinstance(value, str):
        raise SchemaError(f"{name} must be a decimal string")
    try:
        return D(value)
    except (TypeError, ValueError) as exc:
        raise SchemaError(f"invalid {name}") from exc


def _integer(value: object, name: str) -> int:
    if type(value) is not int or value < 1 or value > 120:
        raise SchemaError(f"{name} must be an integer between 1 and 120")
    return value


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise SchemaError(f"{name} must be boolean")
    return value


def _objects(value: object, name: str) -> list[dict]:
    if not isinstance(value, list) or len(value) > 100 or any(not isinstance(v, dict) for v in value):
        raise SchemaError(f"{name} must be a list of objects (at most 100)")
    return value


def _finance_worksheet(params: Mapping[str, object]) -> FinanceWorksheet:
    expected = {
        "selling_price", "addons", "doc_fee", "doc_fee_taxable", "gov_fees", "rebates",
        "trade_allowance", "trade_payoff", "trade_tax_credit", "cash_down",
        "stated_tax_rate_pct", "apr_pct", "term_months", "jurisdiction",
    }
    if set(params) != expected:
        raise SchemaError(f"finance params must contain exactly: {sorted(expected)}")
    addons = []
    for entry in _objects(params["addons"], "addons"):
        if set(entry) != {"code", "amount", "taxable"}:
            raise SchemaError("addon requires code, amount, taxable")
        try:
            code = AddonCode(entry["code"])
        except ValueError as exc:
            raise SchemaError("invalid addon code") from exc
        addons.append(Addon(code, _money(entry["amount"], "addon.amount"), _boolean(entry["taxable"], "addon.taxable")))
    gov = []
    for entry in _objects(params["gov_fees"], "gov_fees"):
        if set(entry) != {"code", "amount", "taxable"}:
            raise SchemaError("government fee requires code, amount, taxable")
        try:
            code = GovFeeCode(entry["code"])
        except ValueError as exc:
            raise SchemaError("invalid government fee code") from exc
        gov.append(GovFee(code, _money(entry["amount"], "gov_fee.amount"), _boolean(entry["taxable"], "gov_fee.taxable")))
    rebates = []
    for entry in _objects(params["rebates"], "rebates"):
        if set(entry) != {"amount", "applied"}:
            raise SchemaError("rebate requires amount, applied")
        try:
            applied = RebateTiming(entry["applied"])
        except ValueError as exc:
            raise SchemaError("invalid rebate timing") from exc
        rebates.append(Rebate(_money(entry["amount"], "rebate.amount"), applied))
    jurisdiction = params["jurisdiction"]
    if not isinstance(jurisdiction, dict) or not (set(jurisdiction) <= {"state", "locality_code"} and "state" in jurisdiction):
        raise SchemaError("jurisdiction requires state and optional locality_code")
    state = jurisdiction["state"]
    local = jurisdiction.get("locality_code")
    if not isinstance(state, str) or len(state) != 2 or not state.isalpha():
        raise SchemaError("jurisdiction.state must be a two-letter code")
    if local is not None and not isinstance(local, str):
        raise SchemaError("jurisdiction.locality_code must be a string or null")
    ws = FinanceWorksheet(
        selling_price=_money(params["selling_price"], "selling_price"),
        addons=tuple(addons), doc_fee=_money(params["doc_fee"], "doc_fee"),
        doc_fee_taxable=_boolean(params["doc_fee_taxable"], "doc_fee_taxable"),
        gov_fees=tuple(gov), rebates=tuple(rebates),
        trade_allowance=_money(params["trade_allowance"], "trade_allowance"),
        trade_payoff=_money(params["trade_payoff"], "trade_payoff"),
        trade_tax_credit=_boolean(params["trade_tax_credit"], "trade_tax_credit"),
        cash_down=_money(params["cash_down"], "cash_down"),
        stated_tax_rate_pct=_money(params["stated_tax_rate_pct"], "stated_tax_rate_pct"),
        apr_pct=_money(params["apr_pct"], "apr_pct"),
        term_months=_integer(params["term_months"], "term_months"),
        jurisdiction=Jurisdiction(state.upper(), local),
    )
    if ws.selling_price <= 0 or ws.stated_tax_rate_pct < 0 or ws.apr_pct < 0:
        raise SchemaError("price must be positive and rates nonnegative")
    for v in (ws.doc_fee, ws.trade_allowance, ws.trade_payoff, ws.cash_down):
        if v < 0:
            raise SchemaError("money amounts must be nonnegative")
    if any(x.amount < 0 for x in (*ws.addons, *ws.gov_fees, *ws.rebates)):
        raise SchemaError("line-item amounts must be nonnegative")
    return ws


def _lease_params(params: Mapping[str, object]) -> tuple:
    expected = {"adjusted_cap_cost", "residual_value", "money_factor", "tax_rate_pct", "term_months", "rounding_convention"}
    if set(params) != expected:
        raise SchemaError(f"lease params must contain exactly: {sorted(expected)}")
    adj = _money(params["adjusted_cap_cost"], "adjusted_cap_cost")
    residual = _money(params["residual_value"], "residual_value")
    money_factor = _money(params["money_factor"], "money_factor")
    tax = _money(params["tax_rate_pct"], "tax_rate_pct")
    n = _integer(params["term_months"], "term_months")
    try:
        conv = LeaseConvention(params["rounding_convention"])
    except ValueError as exc:
        raise SchemaError("invalid rounding_convention") from exc
    if adj <= 0 or residual < 0 or residual > adj or money_factor < 0 or tax < 0:
        raise SchemaError("invalid lease monetary values")
    return adj, residual, money_factor, n, tax, conv


def _outcomes(outcomes: Mapping[str, object], allowed: frozenset[str]) -> None:
    if not outcomes or not set(outcomes) <= allowed:
        raise SchemaError("outcomes must contain one or more recognized fields")
    for name, value in outcomes.items():
        _money(value, f"outcomes.{name}")


def _assumptions(declared: Mapping[str, object]) -> tuple[Assumption, ...]:
    # These first adapters have no sweep axes. Never silently ignore user axes.
    if declared:
        raise SchemaError("this adapter requires an empty assumptions object; sweep axes are not yet supported")
    return ()


def _findings(frozen: FrozenClaim, examination: Examination, outcomes: Mapping[str, object], arithmetic: frozenset[str], external: frozenset[str]) -> tuple[Finding, ...]:
    if len(examination.points) != 1 or examination.points[0].point:
        raise ValueError("expected one empty mechanical calculation point")
    values = examination.points[0].values
    results = []
    for name, claimed in outcomes.items():
        if name in external:
            results.append(Finding(name, Basis.EXTERNAL_EVIDENCE, Status.INDETERMINATE,
                f"Independent evidence is unavailable for {name}", reason="evidence_unavailable"))
            continue
        if name not in arithmetic or name not in values:
            raise ValueError(f"unsupported computed field: {name}")
        expected = Decimal(str(values[name]))
        observed = _money(claimed, f"outcomes.{name}")
        tol = Decimal(frozen.tolerances[name])
        diff = observed - expected
        passed = abs(diff) <= tol
        ce = () if passed else (Counterexample({}, str(expected), str(observed), str(diff), str(tol), "Arithmetic mismatch"),)
        results.append(Finding(
            finding_id=name, basis=Basis.INTERNAL_ARITHMETIC,
            status=Status.CONSISTENT if passed else Status.CONTRADICTED,
            statement=f"Recomputed {name} from frozen parameters",
            counterexamples=ce,
            numbers={"expected": str(expected), "observed": str(observed), "difference": str(diff), "tolerance": str(tol)},
        ))
    return tuple(results)


class _BaseQuote:
    schema_version = 1
    param_fields = frozenset()
    outcome_fields = frozenset()
    arithmetic_fields = frozenset()
    external_fields = frozenset()

    def __init__(self) -> None:
        pass

    def validate_outcomes(self, outcomes: Mapping[str, object]) -> None:
        _outcomes(outcomes, self.outcome_fields)

    def assumption_specs(self, declared: Mapping[str, object]) -> tuple[Assumption, ...]:
        return _assumptions(declared)

    def tolerances(self, params: Mapping[str, object], outcomes: Mapping[str, object]) -> Mapping[str, str]:
        return {name: "0.01" if name not in self.external_fields else "0" for name in outcomes}

    def evidence_requests(self, params: Mapping[str, object]) -> Sequence[EvidenceRequest]:
        return ()

    def evidence_policy(self) -> EvidencePolicySpec:
        return EvidencePolicySpec(frozenset())

    def findings(self, frozen: FrozenClaim, examination: Examination, outcomes: Mapping[str, object], evidence: Sequence[EvidenceItem]) -> Sequence[Finding]:
        return _findings(frozen, examination, outcomes, self.arithmetic_fields, self.external_fields)

    def diagnose(self, frozen: FrozenClaim, examination: Examination, outcomes: Mapping[str, object]) -> Mapping[str, object] | None:
        return None


class FinanceClaimType(_BaseQuote):
    type_id = "quote.finance.v1"
    param_fields = frozenset({"selling_price", "addons", "doc_fee", "doc_fee_taxable", "gov_fees", "rebates", "trade_allowance", "trade_payoff", "trade_tax_credit", "cash_down", "stated_tax_rate_pct", "apr_pct", "term_months", "jurisdiction"})
    arithmetic_fields = frozenset({"taxable_base", "sales_tax", "amount_financed", "monthly_payment", "total_of_payments", "finance_charge"})
    external_fields = frozenset({"tax_rate", "doc_fee_cap"})
    outcome_fields = arithmetic_fields | external_fields

    def validate_params(self, params: Mapping[str, object]) -> None:
        _finance_worksheet(params)

    def examine(self, task: BlindedTask, evidence: EvidenceReader, points: Sequence[Mapping[str, str]]) -> Examination:
        ws = _finance_worksheet(task.params)
        calculated = chain(ws)
        vals = {f.name: format(getattr(calculated, f.name), "f") for f in fields(calculated)}
        if any(point for point in points):
            raise ValueError("unexpected assumption grid")
        return Examination(task.spec_hash, {}, tuple(PointResult(dict(p), vals) for p in points))


class LeaseClaimType(_BaseQuote):
    type_id = "quote.lease.v1"
    param_fields = frozenset({"adjusted_cap_cost", "residual_value", "money_factor", "tax_rate_pct", "term_months", "rounding_convention"})
    arithmetic_fields = frozenset({"depreciation_fee", "rent_charge", "base_payment", "monthly_tax", "total_monthly_payment"})
    external_fields = frozenset({"tax_rate"})
    outcome_fields = arithmetic_fields | external_fields

    def validate_params(self, params: Mapping[str, object]) -> None:
        _lease_params(params)

    def examine(self, task: BlindedTask, evidence: EvidenceReader, points: Sequence[Mapping[str, str]]) -> Examination:
        vals = _lease_params(task.params)
        calculated = compute(*vals)
        numbers = {f.name: format(getattr(calculated, f.name), "f") for f in fields(calculated)}
        if any(point for point in points):
            raise ValueError("unexpected assumption grid")
        return Examination(task.spec_hash, {}, tuple(PointResult(dict(p), numbers) for p in points))
