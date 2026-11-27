"""Presentation adapter: domain objects -> API DTOs (docs/API_CONTRACT.md). Core req 13.

Pure functions. No domain status is changed here; the adapter only *withholds* a confidence
class where the contract requires it and adds execution-level framing.
"""
from __future__ import annotations

import hashlib
from typing import Mapping, Sequence

from ..contract import CONTRACT_VERSION
from ..model import Basis, DataMode, EvidenceItem, Finding, FrozenClaim, LicenseClass, SourceClass, Status
from ..plugin import Examination
from ..sweep import AggregateKind, PointOutcome, aggregate

DEMONSTRATION_NOTICE = (
    "DEMONSTRATION ONLY: synthetic price data generated for testing. "
    "This result says nothing about any real trading claim or market."
)

CONFIDENCE_BY_BASIS: Mapping[Basis, str] = {
    Basis.INTERNAL_ARITHMETIC: "DOCUMENT_INTERNAL",
    Basis.EXTERNAL_EVIDENCE: "EXTERNAL",
    Basis.MECHANICAL_BOUND: "MECHANICAL_BOUND",
}

EXECUTION_STATUSES = ("COMPLETED", "BLOCKED", "INDETERMINATE")

# Per-claim-type specimen templates
_SPECIMEN_TEMPLATES: Mapping[str, dict] = {
    "reel.mechanical.v1": {
        "label": "Reel Autopsy — Mechanical Strategy",
        "fields": ["instrument", "timeframe", "template", "start", "end"],
    },
    "quote.finance.v1": {
        "label": "Quote Autopsy — Finance Worksheet",
        "fields": ["selling_price", "apr_pct", "term_months"],
    },
    "quote.lease.v1": {
        "label": "Quote Autopsy — Lease Worksheet",
        "fields": ["selling_price", "residual_pct", "term_months"],
    },
}


def confidence_class(finding: Finding, data_mode: DataMode) -> str | None:
    """None if status is INDETERMINATE or data_mode is SYNTHETIC_DEMO; else by basis."""
    if finding.status is Status.INDETERMINATE or data_mode is DataMode.SYNTHETIC_DEMO:
        return None
    return CONFIDENCE_BY_BASIS.get(finding.basis)


def execution_status(*, blockers: Sequence[Mapping[str, object]], findings: Sequence[Finding]) -> str:
    """BLOCKED if any blocker (findings must then be empty); INDETERMINATE if every finding
    is INDETERMINATE (or there are none); otherwise COMPLETED."""
    if blockers:
        if findings:
            raise ValueError("cannot have both blockers and findings")
        return "BLOCKED"
    if not findings or all(f.status is Status.INDETERMINATE for f in findings):
        return "INDETERMINATE"
    return "COMPLETED"


def evidence_dto(item: EvidenceItem, *, rights_note: str, embedded: bool) -> dict[str, object]:
    """EvidenceDTO per api/openapi.yaml. evidenceId = "ev_" + sha256[:16];
    origin maps DOCUMENT/USER_SUPPLIED -> CLAIMANT_DOCUMENT."""
    origin_map = {
        SourceClass.EXCHANGE_PUBLIC_DATA: "EXCHANGE_PUBLIC_DATA",
        SourceClass.GOVERNMENT_OFFICIAL: "GOVERNMENT_OFFICIAL",
        SourceClass.DOCUMENT: "CLAIMANT_DOCUMENT",
        SourceClass.USER_SUPPLIED: "CLAIMANT_DOCUMENT",
        SourceClass.SYNTHETIC_FIXTURE: "SYNTHETIC_FIXTURE",
        SourceClass.CLAIMANT: "CLAIMANT_DOCUMENT",
    }
    independence_map = {
        SourceClass.EXCHANGE_PUBLIC_DATA: "INDEPENDENT_OF_CLAIMANT",
        SourceClass.GOVERNMENT_OFFICIAL: "INDEPENDENT_OF_CLAIMANT",
        SourceClass.DOCUMENT: "CLAIMANT_DOCUMENT_SELF",
        SourceClass.USER_SUPPLIED: "CLAIMANT_DOCUMENT_SELF",
        SourceClass.SYNTHETIC_FIXTURE: "SYNTHETIC_NOT_EVIDENCE",
        SourceClass.CLAIMANT: "CLAIMANT_DOCUMENT_SELF",
    }
    return {
        "evidenceId": "ev_" + item.sha256[:16],
        "providerId": item.source_id,
        "origin": origin_map.get(item.source_class, "EXCHANGE_PUBLIC_DATA"),
        "retrievedAt": item.retrieved_at,
        "snapshotHash": item.sha256,
        "independenceBasis": independence_map.get(item.source_class, "INDEPENDENT_OF_CLAIMANT"),
        "rightsNote": rights_note,
        "licenseClass": item.license_class.value,
        "embeddedInBundle": embedded and item.license_class is not LicenseClass.REFETCH_ONLY,
        "uri": item.uri,
    }


def finding_dto(finding: Finding, *, data_mode: DataMode, grid_points: int,
                key_record_ids: Sequence[str], evidence_ids: Mapping[str, str]) -> dict[str, object]:
    cc = confidence_class(finding, data_mode)
    cs = finding.basis.value and _confidence_scope(finding.basis) if cc is not None else None
    numbers = {
        "expected": finding.numbers.get("expected"),
        "observed": finding.numbers.get("observed"),
        "difference": finding.numbers.get("difference"),
        "tolerance": finding.numbers.get("tolerance"),
    }
    if finding.counterexamples:
        cex = finding.counterexamples[0]
        numbers = {
            "expected": cex.expected,
            "observed": cex.observed,
            "difference": cex.difference,
            "tolerance": cex.tolerance,
        }
    return {
        "findingId": finding.finding_id,
        "status": finding.status.value,
        "confidenceClass": cc,
        "confidenceScope": cs,
        "statement": finding.statement,
        "reason": finding.reason,
        "numbers": numbers,
        "evidenceIds": [evidence_ids.get(sha, f"ev_{sha[:16]}") for sha in finding.evidence_used],
        "assumptionDependencies": list(finding.assumption_dependencies),
        "gridPointsEvaluated": grid_points,
        "keyRecordIds": list(key_record_ids),
    }


def _confidence_scope(basis: Basis) -> str:
    from ..model import CONFIDENCE_SCOPE
    return CONFIDENCE_SCOPE[basis]


def check_key_records(records: Sequence[Mapping[str, object]], findings: Sequence[Finding]) -> None:
    """Raise ValueError if a COUNTEREXAMPLE record references a finding whose status is not
    CONTRADICTED/REFUTED/CONDITIONAL/IMPOSSIBLE, or if a TRADE/EQUITY_SERIES record is
    anything but ILLUSTRATIVE (correction 6)."""
    from ..model import NEEDS_COUNTEREXAMPLE
    finding_map = {f.finding_id: f for f in findings}

    for rec in records:
        role = rec.get("recordRole")
        kind = rec.get("recordKind")

        # TRADE and EQUITY_SERIES must always be ILLUSTRATIVE
        if kind in ("TRADE", "EQUITY_SERIES") and role != "ILLUSTRATIVE":
            raise ValueError(
                f"TRADE/EQUITY_SERIES records must be ILLUSTRATIVE, got {role!r}"
            )

        # COUNTEREXAMPLE role requires a failing finding
        if role == "COUNTEREXAMPLE":
            fid = rec.get("findingId")
            f = finding_map.get(fid)
            if f is None or f.status not in NEEDS_COUNTEREXAMPLE:
                raise ValueError(
                    f"COUNTEREXAMPLE record {rec.get('recordId')!r} references finding "
                    f"{fid!r} with status {'unknown' if f is None else f.status!r} which does not "
                    f"require a counterexample"
                )


def specimen_dto(
    frozen: FrozenClaim | None,
    *,
    claim_type: str,
    data_mode: DataMode,
    fixture_id: str | None,
    case_id: str,
    frozen_at: str | None,
) -> dict[str, object]:
    """Specimen per api/openapi.yaml, built from frozen *parameters* only (the signature
    cannot receive outcomes). title/fields come from a fixed per-claim-type template;
    specimenId = "SPC-" + first 8 hex of sha256(case_id), upper-case.
    source = SYNTHETIC_FIXTURE iff data_mode is SYNTHETIC_DEMO."""
    specimen_id = "SPC-" + hashlib.sha256(case_id.encode()).hexdigest()[:8].upper()
    template = _SPECIMEN_TEMPLATES.get(claim_type, {"label": claim_type, "fields": []})

    source = "SYNTHETIC_FIXTURE" if data_mode is DataMode.SYNTHETIC_DEMO else "USER_SUBMITTED"

    # Build fields from frozen params
    fields: list[dict] = []
    if frozen is not None:
        for field_name in template.get("fields", []):
            val = frozen.params.get(field_name)
            if val is not None:
                fields.append({"label": field_name, "value": str(val)})

    # Build title from params
    if frozen is not None:
        p = frozen.params
        if claim_type == "reel.mechanical.v1":
            title = f"{p.get('instrument', '?')} {p.get('template', '?')} {p.get('timeframe', '?')}"
        elif claim_type in ("quote.finance.v1", "quote.lease.v1"):
            title = f"Quote worksheet {p.get('selling_price', '')}"
        else:
            title = f"{claim_type} claim"
    else:
        title = f"{template['label']} (fixture)"
    title = title[:120]

    spec_hash_short = frozen.spec_hash[:12] if frozen is not None else None

    return {
        "specimenId": specimen_id,
        "claimType": claim_type,
        "claimTypeLabel": template["label"],
        "source": source,
        "fixtureId": fixture_id,
        "title": title,
        "fields": fields,
        "frozenAt": frozen_at,
        "specHashShort": spec_hash_short,
    }


def sensitivity_dto(
    *,
    examination: Examination,
    template_version: str,
    grid_cap: int,
    axes: Sequence[Mapping[str, object]],
    point_outcomes: Mapping[str, Sequence[PointOutcome]],
) -> dict[str, object]:
    """Sensitivity per api/openapi.yaml. variantsExecuted = len(examination.points);
    cells keep grid order and carry the variant index; margins as Decimal strings.
    Presentation only: evaluators never see this structure."""
    results = []
    for finding_id, outcomes in point_outcomes.items():
        outcomes_list = list(outcomes)
        agg = aggregate(outcomes_list)

        agg_kind_map = {
            AggregateKind.ALL_PASS: "ALL_PASS",
            AggregateKind.NONE_PASS: "NONE_PASS",
            AggregateKind.MIXED: "MIXED",
        }

        pass_count = sum(1 for o in outcomes_list if o.passed)
        fail_count = sum(1 for o in outcomes_list if not o.passed)

        cells = [
            {
                "variant": i,
                "point": dict(o.point),
                "passed": o.passed,
                "margin": format(o.margin, "f"),
            }
            for i, o in enumerate(outcomes_list)
        ]

        results.append({
            "findingId": finding_id,
            "aggregate": agg_kind_map[agg.kind],
            "passCount": pass_count,
            "failCount": fail_count,
            "cells": cells,
        })

    return {
        "templateVersion": template_version,
        "gridCap": grid_cap,
        "variantsExecuted": len(examination.points),
        "axes": [dict(a) for a in axes],
        "results": results,
    }


def outcome_response(
    *,
    case_id: str,
    run_id: str | None,
    claim_type: str,
    data_mode: DataMode,
    isolation_mode: str,
    findings: Sequence[Finding],
    blockers: Sequence[Mapping[str, object]],
    parameter_ledger: Sequence[Mapping[str, object]],
    evidence: Sequence[Mapping[str, object]],
    key_records: Sequence[Mapping[str, object]],
    diagnostics: Mapping[str, object] | None,
    spec_hash: str | None,
    verdict_hash: str | None,
    grid_points: int,
    specimen: Mapping[str, object],
    sensitivity: Mapping[str, object] | None,
) -> dict[str, object]:
    """Build an OutcomeResponse (contractVersion = CONTRACT_VERSION). Sets
    demonstrationNotice = DEMONSTRATION_NOTICE for SYNTHETIC_DEMO, else None; forces
    sensitivity to None when BLOCKED; nulls every parameter-ledger sourceSpan.
    The result must validate against the schema."""
    exec_status = execution_status(blockers=list(blockers), findings=list(findings))

    # Null all sourceSpans in parameter ledger (post-freeze)
    cleaned_ledger = [
        {**entry, "sourceSpan": None}
        for entry in parameter_ledger
    ]

    # Confidence class for headline
    if exec_status == "BLOCKED":
        headline_status_val = None
        headline_cc = None
        sensitivity = None  # blocked has no sensitivity
    elif exec_status == "INDETERMINATE":
        headline_status_val = "INDETERMINATE"
        headline_cc = None
    else:
        from ..model import headline_status as _headline_status, SEVERITY
        h = _headline_status(list(findings))
        headline_status_val = h.value
        worst_finding = max(findings, key=lambda f: SEVERITY[f.status])
        headline_cc = confidence_class(worst_finding, data_mode)

    # demonstration flags
    is_demo = data_mode is DataMode.SYNTHETIC_DEMO
    demo_notice = DEMONSTRATION_NOTICE if is_demo else None

    return {
        "contractVersion": CONTRACT_VERSION,
        "caseId": case_id,
        "runId": run_id,
        "claimType": claim_type,
        "dataMode": data_mode.value,
        "demonstrationOnly": is_demo,
        "demonstrationNotice": demo_notice,
        "specimen": dict(specimen),
        "executionStatus": exec_status,
        "headline": {
            "status": headline_status_val,
            "confidenceClass": headline_cc,
        },
        "findings": [
            {
                "findingId": f.finding_id,
                "status": f.status.value,
                "confidenceClass": confidence_class(f, data_mode),
                "confidenceScope": _confidence_scope(f.basis) if confidence_class(f, data_mode) is not None else None,
                "statement": f.statement,
                "reason": f.reason,
                "numbers": _finding_numbers(f),
                "evidenceIds": [f"ev_{sha[:16]}" for sha in f.evidence_used],
                "assumptionDependencies": list(f.assumption_dependencies),
                "gridPointsEvaluated": grid_points,
                "keyRecordIds": [],
            }
            for f in findings
        ],
        "sensitivity": dict(sensitivity) if sensitivity is not None else None,
        "parameterLedger": cleaned_ledger,
        "evidence": [dict(e) for e in evidence],
        "keyRecords": [dict(r) for r in key_records],
        "diagnostics": _wrap_diagnostics(diagnostics),
        "blockers": [dict(b) for b in blockers],
        "specHash": spec_hash,
        "verdictHash": verdict_hash,
        "isolationMode": isolation_mode,
        "bundleAvailable": exec_status != "BLOCKED",
    }


def _finding_numbers(f: Finding) -> dict:
    if f.counterexamples:
        cex = f.counterexamples[0]
        return {
            "expected": cex.expected,
            "observed": cex.observed,
            "difference": cex.difference,
            "tolerance": cex.tolerance,
        }
    return {
        "expected": f.numbers.get("expected"),
        "observed": f.numbers.get("observed"),
        "difference": f.numbers.get("difference"),
        "tolerance": f.numbers.get("tolerance"),
    }


def _wrap_diagnostics(diagnostics: Mapping[str, object] | None) -> dict | None:
    if diagnostics is None:
        return None
    return {
        "computedAfterReveal": True,
        "affectsVerdict": False,
        "items": [dict(diagnostics)],
    }


# Status re-export for type checkers of callers
__all__ = [
    "CONTRACT_VERSION", "DEMONSTRATION_NOTICE", "specimen_dto", "sensitivity_dto",
    "CONFIDENCE_BY_BASIS", "EXECUTION_STATUSES", "confidence_class", "execution_status",
    "evidence_dto", "finding_dto", "check_key_records", "outcome_response", "Status",
]
