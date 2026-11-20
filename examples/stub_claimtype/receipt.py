"""Minimal claim type used only by the core contract tests ("receipt total").

It implements the ClaimType protocol with trivial domain logic so that core behaviour
(blinding, ledger order, bundles, replay) is tested independently of the two apps.
Params: {"items": ["12.50", ...]}. Outcome: {"stated_total": "..."}.
Assumption axis: tip_pct (SET if declared by the claimant, else FIXED 0 by policy).
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Mapping, Sequence

from verdictkit.custody.intake import SchemaError
from verdictkit.model import (
    Assumption,
    AssumptionKind,
    Basis,
    Counterexample,
    Finding,
    Origin,
    Status,
)
from verdictkit.plugin import EvidencePolicySpec, Examination, PointResult


def _dec(text: object) -> Decimal:
    if not isinstance(text, str):
        raise SchemaError("amounts must be decimal strings")
    d = Decimal(text)
    if not d.is_finite():
        raise SchemaError("non-finite amount")
    return d


class ReceiptClaimType:
    type_id = "example.receipt.v1"
    schema_version = 1
    param_fields = frozenset({"items"})
    outcome_fields = frozenset({"stated_total"})

    def validate_params(self, params: Mapping[str, object]) -> None:
        items = params.get("items")
        if not isinstance(items, list) or not items:
            raise SchemaError("items must be a non-empty list")
        for it in items:
            _dec(it)

    def validate_outcomes(self, outcomes: Mapping[str, object]) -> None:
        if "stated_total" not in outcomes:
            raise SchemaError("stated_total required")
        _dec(outcomes["stated_total"])

    def assumption_specs(self, declared: Mapping[str, object]) -> tuple[Assumption, ...]:
        if "tip_pct" in declared and isinstance(declared["tip_pct"], dict):
            values = tuple(sorted(_dec(v) for v in declared["tip_pct"]["set"]))
            return (Assumption("tip_pct", AssumptionKind.SET, Origin.CLAIMANT, values=values),)
        return (Assumption("tip_pct", AssumptionKind.FIXED, Origin.DEFAULT_POLICY, value=Decimal("0")),)

    def tolerances(self, params, outcomes) -> Mapping[str, str]:
        return {"stated_total": "0.00"}

    def evidence_requests(self, params):
        return ()

    def evidence_policy(self) -> EvidencePolicySpec:
        return EvidencePolicySpec(permitted_sources=frozenset())

    def examine(self, task, evidence, points: Sequence[Mapping[str, str]]) -> Examination:
        with localcontext() as ctx:
            ctx.prec = 34
            subtotal = sum((_dec(x) for x in task.params["items"]), Decimal(0))
            results = []
            for p in points:
                tip = Decimal(p["tip_pct"])
                total = (subtotal * (1 + tip / 100)).quantize(Decimal("0.01"))
                results.append(PointResult(point=dict(p), values={"total": format(total, "f")}))
        return Examination(
            spec_hash=task.spec_hash,
            shared={"subtotal": format(subtotal, "f")},
            points=tuple(results),
        )

    def findings(self, frozen, examination, outcomes, evidence) -> Sequence[Finding]:
        stated = _dec(outcomes["stated_total"])
        passes, fails = [], []
        for pr in examination.points:
            computed = Decimal(pr.values["total"])
            (passes if computed == stated else fails).append((pr, computed))
        if not fails:
            status = Status.CONSISTENT
        elif not passes:
            status = Status.CONTRADICTED
        else:
            status = Status.CONDITIONAL
        cex = tuple(
            Counterexample(
                point=dict(pr.point),
                expected=format(c, "f"),
                observed=format(stated, "f"),
                difference=format(stated - c, "f"),
                tolerance="0.00",
            )
            for pr, c in fails[:1]
        )
        return (
            Finding(
                finding_id="total",
                basis=Basis.INTERNAL_ARITHMETIC,
                status=status,
                statement="Stated total vs sum of items (plus tip at each grid point).",
                assumption_dependencies=("tip_pct",),
                counterexamples=cex,
            ),
        )

    def diagnose(self, frozen, examination, outcomes):
        return {"note": "diagnostic computed after reveal", "stated": outcomes["stated_total"]}


def raw_claim(items: list[str], stated_total: str, tip_set: list[str] | None = None) -> dict:
    raw = {
        "claim_type": ReceiptClaimType.type_id,
        "schema_version": 1,
        "params": {"items": items},
        "outcomes": {"stated_total": stated_total},
        "assumptions": {},
        "tolerances": {},
    }
    if tip_set is not None:
        raw["assumptions"] = {"tip_pct": {"set": tip_set}}
    return raw
