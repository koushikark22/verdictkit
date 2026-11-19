"""Fail-closed VerdictKit adapter for reel.mechanical.v1.

This is a boundary-safe integration scaffold, NOT a live-data implementation.
The current Examiner worker supplies _EmptyEvidenceReader, so it cannot verify
OHLCV evidence. Reporting numerical performance would fabricate provenance.
Until an independent, hash-verified evidence feed is wired and replay-tested,
the adapter explicitly produces INDETERMINATE findings only.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from verdictkit.custody.intake import SchemaError
from verdictkit.model import (
    Assumption, Basis, BlindedTask, EvidenceItem, Finding, FrozenClaim, Status,
)
from verdictkit.plugin import EvidencePolicySpec, EvidenceReader, EvidenceRequest, Examination, PointResult

from .strategies import Template, validate_params as validate_strategy
from .tolerance import precision_tolerance


class ReelClaimType:
    type_id = "reel.mechanical.v1"
    schema_version = 1
    param_fields = frozenset({"instrument", "timeframe", "start", "end", "template", "template_params", "instrument_mode"})
    outcome_fields = frozenset({"total_return_pct", "max_drawdown_pct", "trade_count", "win_rate_pct"})

    def validate_params(self, params: Mapping[str, object]) -> None:
        if set(params) != self.param_fields:
            raise SchemaError(f"reel params require exactly {sorted(self.param_fields)}")
        if not isinstance(params["instrument"], str) or not params["instrument"].strip() or len(params["instrument"]) > 32:
            raise SchemaError("invalid instrument")
        if params["timeframe"] not in ("1h", "4h", "1d"):
            raise SchemaError("timeframe must be 1h, 4h or 1d")
        if not isinstance(params["start"], str) or not isinstance(params["end"], str):
            raise SchemaError("start and end must be date strings")
        from datetime import date
        try:
            start = date.fromisoformat(params["start"])
            end = date.fromisoformat(params["end"])
        except ValueError as exc:
            raise SchemaError("invalid ISO dates") from exc
        if start >= end:
            raise SchemaError("start must precede end")
        if params["instrument_mode"] != "SPOT_LONG_FLAT":
            raise SchemaError("only SPOT_LONG_FLAT supported")
        try:
            template = Template(params["template"])
        except (ValueError, TypeError) as exc:
            raise SchemaError("unsupported template") from exc
        if not isinstance(params["template_params"], dict):
            raise SchemaError("template_params must be a mapping")
        try:
            validate_strategy(template, params["template_params"])
        except ValueError as exc:
            raise SchemaError(str(exc)) from exc

    def extract_text(self, text: str) -> tuple[dict, dict, dict[str, tuple[int, int]]]:
        """Optional intake hook (API contract §8): deterministic, no LLM, no persistence.

        Returns (params, outcomes, spans). Every parameter is present; values not found
        in the text are None (MISSING). Raises ValueError("privacy:<kinds>") for URLs,
        handles, emails, phone numbers or text over 2000 characters.
        """
        from .intake_text import extract, privacy_violations
        issues = privacy_violations(text)
        if issues:
            raise ValueError("privacy:" + ",".join(issues))
        found = extract(text)
        params: dict[str, object] = {name: None for name in self.param_fields}
        params["instrument_mode"] = None
        outcomes: dict[str, object] = {}
        spans: dict[str, tuple[int, int]] = {}
        template_params: dict[str, int] = {}
        for f in found.fields:
            if f.name.startswith("template_params."):
                template_params[f.name.split(".", 1)[1]] = int(f.value)
                continue
            if f.name in self.outcome_fields:
                outcomes.setdefault(f.name, f.value)
                continue
            if f.name in params and params[f.name] is None:
                params[f.name] = f.value
                spans[f.name] = (f.start, f.end)
        if template_params:
            params["template_params"] = template_params
        return params, outcomes, spans

    def validate_outcomes(self, outcomes: Mapping[str, object]) -> None:
        if not outcomes or not set(outcomes) <= self.outcome_fields:
            raise SchemaError("at least one recognized outcome required")
        for key, value in outcomes.items():
            if not isinstance(value, str):
                raise SchemaError(f"{key} must be a decimal string")
            try:
                precision_tolerance(value)
            except ValueError as exc:
                raise SchemaError(f"invalid {key}") from exc

    def assumption_specs(self, declared: Mapping[str, object]) -> tuple[Assumption, ...]:
        if declared:
            raise SchemaError("reel policy axes require verified evidence integration; currently unavailable")
        return ()

    def tolerances(self, params: Mapping[str, object], outcomes: Mapping[str, object]) -> Mapping[str, str]:
        return {key: format(precision_tolerance(value), "f") for key, value in outcomes.items()}

    def evidence_requests(self, params: Mapping[str, object]) -> Sequence[EvidenceRequest]:
        # Do not invent a data provider or pass claimant-provided OHLCV as proof.
        return ()

    def evidence_policy(self) -> EvidencePolicySpec:
        return EvidencePolicySpec(frozenset())

    def examine(self, task: BlindedTask, evidence: EvidenceReader, points: Sequence[Mapping[str, str]]) -> Examination:
        # No OHLCV source configured. This cannot legitimately compute a return.
        # Keep all claimed outcomes out of the Examiner.
        return Examination(
            spec_hash=task.spec_hash,
            shared={"coverage": "UNVERIFIED", "reason": "evidence_unavailable"},
            points=tuple(PointResult(dict(p), {}) for p in points),
            missing_assumptions=("verified_ohlcv_evidence",),
        )

    def findings(
        self, frozen: FrozenClaim, examination: Examination,
        outcomes: Mapping[str, object], evidence: Sequence[EvidenceItem],
    ) -> Sequence[Finding]:
        return tuple(
            Finding(key, Basis.MECHANICAL_BOUND, Status.INDETERMINATE,
                    f"{key} cannot be evaluated without hash-verified OHLCV evidence",
                    reason="evidence_unavailable")
            for key in sorted(outcomes)
        )

    def diagnose(self, frozen: FrozenClaim, examination: Examination, outcomes: Mapping[str, object]) -> Mapping[str, object] | None:
        return None
