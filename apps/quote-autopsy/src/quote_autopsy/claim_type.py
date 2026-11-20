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

Unknown document facts (quote req 1.3, 4.3): a taxability flag that the worksheet does
not show (``doc_fee_taxable``, ``trade_tax_credit``, ``addons[i].taxable``,
``gov_fees[i].taxable``) or an unconfirmed lease ``rounding_convention`` is written as
``null`` *and* declared as a missing assumption of the same name
(``doc_fee_taxable``, ``addons.<i>.taxable``, ``gov_fees.<i>.taxable``,
``rounding_convention``). The policy then sweeps it over {0, 1} with origin
DEFAULT_POLICY; 0 = false / COMPONENT and 1 = true / FINAL. Findings are CONSISTENT or
CONTRADICTED when every grid point agrees and CONDITIONAL when they differ.
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

from .finance import amount_financed, chain, sales_tax, taxable_base
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


def _flag(value: object, name: str) -> bool | None:
    """A taxability flag: true/false, or null when the worksheet does not show it."""
    if value is None:
        return None
    return _boolean(value, name)


_SWEEP_VALUES = (Decimal(0), Decimal(1))


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
        addons.append(Addon(code, _money(entry["amount"], "addon.amount"), _flag(entry["taxable"], "addon.taxable")))
    gov = []
    for entry in _objects(params["gov_fees"], "gov_fees"):
        if set(entry) != {"code", "amount", "taxable"}:
            raise SchemaError("government fee requires code, amount, taxable")
        try:
            code = GovFeeCode(entry["code"])
        except ValueError as exc:
            raise SchemaError("invalid government fee code") from exc
        gov.append(GovFee(code, _money(entry["amount"], "gov_fee.amount"), _flag(entry["taxable"], "gov_fee.taxable")))
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
        doc_fee_taxable=_flag(params["doc_fee_taxable"], "doc_fee_taxable"),
        gov_fees=tuple(gov), rebates=tuple(rebates),
        trade_allowance=_money(params["trade_allowance"], "trade_allowance"),
        trade_payoff=_money(params["trade_payoff"], "trade_payoff"),
        trade_tax_credit=_flag(params["trade_tax_credit"], "trade_tax_credit"),
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
    if params["rounding_convention"] is None:
        conv = None  # swept: see module docstring
    else:
        try:
            conv = LeaseConvention(params["rounding_convention"])
        except ValueError as exc:
            raise SchemaError("invalid rounding_convention") from exc
    if adj <= 0 or residual < 0 or residual > adj or money_factor < 0 or tax < 0:
        raise SchemaError("invalid lease monetary values")
    return adj, residual, money_factor, n, tax, conv


def chain_af(ws: FinanceWorksheet) -> Decimal:
    return amount_financed(ws, sales_tax(taxable_base(ws), ws.stated_tax_rate_pct))


def _unknown_finance_flags(ws: FinanceWorksheet) -> tuple[str, ...]:
    names = []
    if ws.doc_fee_taxable is None:
        names.append("doc_fee_taxable")
    if ws.trade_tax_credit is None:
        names.append("trade_tax_credit")
    names += [f"addons.{i}.taxable" for i, a in enumerate(ws.addons) if a.taxable is None]
    names += [f"gov_fees.{i}.taxable" for i, g in enumerate(ws.gov_fees) if g.taxable is None]
    return tuple(sorted(names))


def _resolve_finance(ws: FinanceWorksheet, point: Mapping[str, str]) -> FinanceWorksheet:
    from dataclasses import replace

    def flag(current: bool | None, name: str) -> bool:
        if current is not None:
            if name in point:
                raise ValueError(f"{name} is both stated and swept")
            return current
        if name not in point:
            raise ValueError(f"{name} is unknown but not swept")
        return point[name] == "1"

    return replace(
        ws,
        doc_fee_taxable=flag(ws.doc_fee_taxable, "doc_fee_taxable"),
        trade_tax_credit=flag(ws.trade_tax_credit, "trade_tax_credit"),
        addons=tuple(replace(a, taxable=flag(a.taxable, f"addons.{i}.taxable"))
                     for i, a in enumerate(ws.addons)),
        gov_fees=tuple(replace(g, taxable=flag(g.taxable, f"gov_fees.{i}.taxable"))
                       for i, g in enumerate(ws.gov_fees)),
    )


def _outcomes(outcomes: Mapping[str, object], allowed: frozenset[str]) -> None:
    if not outcomes or not set(outcomes) <= allowed:
        raise SchemaError("outcomes must contain one or more recognized fields")
    for name, value in outcomes.items():
        _money(value, f"outcomes.{name}")


def _assumptions(declared: Mapping[str, object], pattern: str) -> tuple[Assumption, ...]:
    """Only unknown document facts may be declared, each as null (missing); the policy
    sweeps it over {0, 1}. Never silently ignore any other declared axis."""
    import re
    axes = []
    for name, value in sorted(declared.items()):
        if not isinstance(name, str) or not re.fullmatch(pattern, name):
            raise SchemaError(f"unsupported assumption: {name!r}")
        if value is not None:
            raise SchemaError(f"{name}: state the value as a parameter; only unknown (null) facts are swept")
        axes.append(Assumption(name, AssumptionKind.SET, Origin.DEFAULT_POLICY, values=_SWEEP_VALUES))
    return tuple(axes)


def _check_axes(unknown: tuple[str, ...], assumptions: Sequence[Assumption]) -> None:
    axes = tuple(sorted(a.name for a in assumptions))
    if axes != unknown:
        raise SchemaError("each unknown (null) fact must be declared as a missing assumption "
                          "of the same name, and only those")


def _per_point(examination: Examination, name: str, claimed: Decimal, tol: Decimal) -> list[PointOutcome]:
    rows = []
    for pr in examination.points:
        if name not in pr.values:
            raise ValueError(f"unsupported computed field: {name}")
        diff = claimed - Decimal(str(pr.values[name]))
        rows.append(PointOutcome(dict(pr.point), abs(diff) <= tol, tol - abs(diff)))
    return rows


def _findings(frozen: FrozenClaim, examination: Examination, outcomes: Mapping[str, object], arithmetic: frozenset[str], external: frozenset[str]) -> tuple[Finding, ...]:
    if not examination.points:
        raise ValueError("examination has no grid points")
    axes = tuple(sorted({k for pr in examination.points for k in pr.point}))
    n = len(examination.points)
    results = []
    for name, claimed in outcomes.items():
        if name in external:
            results.append(Finding(name, Basis.EXTERNAL_EVIDENCE, Status.INDETERMINATE,
                f"Independent evidence is unavailable for {name}", reason="evidence_unavailable"))
            continue
        if name not in arithmetic:
            raise ValueError(f"unsupported computed field: {name}")
        observed = _money(claimed, f"outcomes.{name}")
        tol = Decimal(frozen.tolerances[name])
        rows = _per_point(examination, name, observed, tol)
        agg = aggregate(rows)
        status = {AggregateKind.ALL_PASS: Status.CONSISTENT,
                  AggregateKind.NONE_PASS: Status.CONTRADICTED,
                  AggregateKind.MIXED: Status.CONDITIONAL}[agg.kind]

        def cex(po: PointOutcome, note: str, name: str = name, observed: Decimal = observed,
                tol: Decimal = tol) -> Counterexample:
            expected = next(Decimal(str(pr.values[name])) for pr in examination.points
                            if dict(pr.point) == dict(po.point))
            return Counterexample(dict(po.point), str(expected), str(observed),
                                  str(observed - expected), str(tol), note)

        if status is Status.CONTRADICTED:
            ces = (cex(agg.first_fail, "Arithmetic mismatch"),)
        elif status is Status.CONDITIONAL:
            ces = (cex(agg.first_fail, "Inconsistent under these unknown document facts"),
                   cex(agg.first_pass, "Consistent under these unknown document facts"))
        else:
            ces = ()
        worst = cex(agg.worst, "")
        statement = f"Recomputed {name} from frozen parameters"
        if axes:
            statement += f"; verified at {n} grid points over unknown facts {', '.join(axes)}"
        results.append(Finding(
            finding_id=name, basis=Basis.INTERNAL_ARITHMETIC, status=status,
            statement=statement, assumption_dependencies=axes, counterexamples=ces,
            numbers={"expected": worst.expected, "observed": worst.observed,
                     "difference": worst.difference, "tolerance": str(tol)},
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

    assumption_pattern = r"(?!)"  # overridden per claim type

    def assumption_specs(self, declared: Mapping[str, object]) -> tuple[Assumption, ...]:
        return _assumptions(declared, self.assumption_pattern)

    def point_outcomes(self, frozen: FrozenClaim, examination: Examination,
                       outcomes: Mapping[str, object]) -> Mapping[str, Sequence[PointOutcome]]:
        """Presentation hook: per-grid-point pass/fail for the sensitivity view."""
        return {name: _per_point(examination, name, _money(v, name), Decimal(frozen.tolerances[name]))
                for name, v in outcomes.items() if name in self.arithmetic_fields}

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

    assumption_pattern = r"doc_fee_taxable|trade_tax_credit|(addons|gov_fees)\.(0|[1-9][0-9]?)\.taxable"

    def validate_params(self, params: Mapping[str, object]) -> None:
        ws = _finance_worksheet(params)
        # Design (error handling): a negative amount financed is an intake rejection,
        # checked at every resolution of the unknown flags (bounded by the grid cap).
        unknown = _unknown_finance_flags(ws)
        if 2 ** len(unknown) > 1000:
            raise SchemaError("too many unknown document facts to sweep (grid cap 1000)")
        import itertools
        for combo in itertools.product("01", repeat=len(unknown)):
            if chain_af(_resolve_finance(ws, dict(zip(unknown, combo, strict=False)))) < 0:
                raise SchemaError("amount financed would be negative")

    def validate_assumptions(self, params: Mapping[str, object], assumptions: Sequence[Assumption]) -> None:
        _check_axes(_unknown_finance_flags(_finance_worksheet(params)), assumptions)

    def diagnose(self, frozen: FrozenClaim, examination: Examination, outcomes: Mapping[str, object]) -> Mapping[str, object] | None:
        """Post-reveal only (core req 10.4): local checks and payment packing.
        Never changes a finding status; excluded from verdict_hash. Requires a fully
        stated worksheet: with swept (unknown) taxability flags no diagnostic is made."""
        from .diagnostics import finance_diagnostics
        ws = _finance_worksheet(frozen.params)
        if _unknown_finance_flags(ws):
            return None
        stated = {k: _money(v, k) for k, v in outcomes.items() if k in self.arithmetic_fields}
        if not stated:
            return None
        return finance_diagnostics(ws, stated)

    def examine(self, task: BlindedTask, evidence: EvidenceReader, points: Sequence[Mapping[str, str]]) -> Examination:
        ws = _finance_worksheet(task.params)
        results = []
        for p in points:
            calculated = chain(_resolve_finance(ws, p))
            vals = {f.name: format(getattr(calculated, f.name), "f") for f in fields(calculated)}
            results.append(PointResult(dict(p), vals))
        return Examination(task.spec_hash, {}, tuple(results))


class LeaseClaimType(_BaseQuote):
    type_id = "quote.lease.v1"
    param_fields = frozenset({"adjusted_cap_cost", "residual_value", "money_factor", "tax_rate_pct", "term_months", "rounding_convention"})
    arithmetic_fields = frozenset({"depreciation_fee", "rent_charge", "base_payment", "monthly_tax", "total_monthly_payment"})
    external_fields = frozenset({"tax_rate"})
    outcome_fields = arithmetic_fields | external_fields

    assumption_pattern = r"rounding_convention"

    def validate_params(self, params: Mapping[str, object]) -> None:
        _lease_params(params)

    def validate_assumptions(self, params: Mapping[str, object], assumptions: Sequence[Assumption]) -> None:
        unknown = ("rounding_convention",) if _lease_params(params)[5] is None else ()
        _check_axes(unknown, assumptions)

    def examine(self, task: BlindedTask, evidence: EvidenceReader, points: Sequence[Mapping[str, str]]) -> Examination:
        adj, residual, mf, n, tax, conv = _lease_params(task.params)
        results = []
        for p in points:
            if conv is None:
                if "rounding_convention" not in p:
                    raise ValueError("rounding_convention is unknown but not swept")
                point_conv = LeaseConvention.FINAL if p["rounding_convention"] == "1" else LeaseConvention.COMPONENT
            else:
                if "rounding_convention" in p:
                    raise ValueError("rounding_convention is both stated and swept")
                point_conv = conv
            calculated = compute(adj, residual, mf, n, tax, point_conv)
            numbers = {f.name: format(getattr(calculated, f.name), "f") for f in fields(calculated)}
            results.append(PointResult(dict(p), numbers))
        return Examination(task.spec_hash, {}, tuple(results))
