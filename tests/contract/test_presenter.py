"""Presentation adapter rules (corrections 1, 2, 4, 6) and B1 data-mode policy."""
import json
from pathlib import Path

import pytest
import yaml
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator, FormatChecker

from verdictkit.api.presenter import (
    CONTRACT_VERSION,
    DEMONSTRATION_NOTICE,
    sensitivity_dto,
    specimen_dto,
    check_key_records,
    confidence_class,
    evidence_dto,
    execution_status,
    outcome_response,
)
from verdictkit.evidence.policy import effective_policy
from verdictkit.model import (
    ALLOWED_STATUSES,
    Basis,
    Counterexample,
    DataMode,
    EvidenceItem,
    Finding,
    LicenseClass,
    NEEDS_COUNTEREXAMPLE,
    SourceClass,
    Status,
)
from verdictkit.plugin import EvidencePolicySpec, Examination, PointResult
from verdictkit.sweep import PointOutcome
from verdictkit.model import Assumption, AssumptionKind, FrozenClaim, Origin
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "api/openapi.yaml").read_text())
CEX = Counterexample(point={}, expected="1", observed="2", difference="1", tolerance="0")
PAIRS = [(b, s) for b, ss in ALLOWED_STATUSES.items() for s in ss]


FROZEN = FrozenClaim(
    claim_type="reel.mechanical.v1", schema_version=1,
    params={"instrument": "BTC-USD", "timeframe": "1d", "start": "2025-01-01", "end": "2026-01-01",
            "template": "SMA_CROSS", "template_params": {"fast": 10, "slow": 30}, "instrument_mode": "SPOT_LONG_FLAT"},
    assumptions=(), tolerances={}, spec_hash="a" * 64,
)


def v(name):
    return Draft202012Validator({**SPEC, "$ref": f"#/components/schemas/{name}"}, format_checker=FormatChecker())


def finding(b, s, i=0):
    return Finding(f"f{i}", b, s, "s", counterexamples=(CEX,) if s in NEEDS_COUNTEREXAMPLE else ())


@given(st.sampled_from(PAIRS), st.sampled_from(list(DataMode)))
def test_confidence_class_rules(pair, mode):
    b, s = pair
    cc = confidence_class(finding(b, s), mode)
    if s is Status.INDETERMINATE or mode is DataMode.SYNTHETIC_DEMO:
        assert cc is None
    else:
        assert cc == {"INTERNAL_ARITHMETIC": "DOCUMENT_INTERNAL", "EXTERNAL_EVIDENCE": "EXTERNAL",
                      "MECHANICAL_BOUND": "MECHANICAL_BOUND"}[b.value]


@given(st.lists(st.sampled_from(PAIRS), max_size=6))
def test_execution_status_rules(pairs):
    fs = [finding(b, s, i) for i, (b, s) in enumerate(pairs)]
    es = execution_status(blockers=[], findings=fs)
    if all(f.status is Status.INDETERMINATE for f in fs):
        assert es == "INDETERMINATE"
    else:
        assert es == "COMPLETED"
    assert execution_status(blockers=[{"code": "EVIDENCE_GAP", "message": "m"}], findings=[]) == "BLOCKED"


def test_blocked_with_findings_is_a_programming_error():
    with pytest.raises(ValueError):
        execution_status(blockers=[{"code": "EVIDENCE_GAP", "message": "m"}],
                         findings=[finding(Basis.EXTERNAL_EVIDENCE, Status.SUPPORTED)])


@pytest.mark.parametrize("mode", list(DataMode))
@pytest.mark.parametrize("pairs", [[], [(Basis.EXTERNAL_EVIDENCE, Status.INDETERMINATE)],
                                   [(Basis.INTERNAL_ARITHMETIC, Status.CONTRADICTED), (Basis.EXTERNAL_EVIDENCE, Status.SUPPORTED)]])
def test_outcome_response_validates(mode, pairs):
    fs = [finding(b, s, i) for i, (b, s) in enumerate(pairs)]
    blockers = [] if fs else [{"code": "EVIDENCE_RIGHTS_UNVERIFIED", "message": "m", "field": None}]
    blocked = bool(blockers)
    spec = specimen_dto(FROZEN, claim_type="reel.mechanical.v1", data_mode=mode,
                        fixture_id="fx_demo" if mode is DataMode.SYNTHETIC_DEMO else None,
                        case_id="case_" + "0" * 32, frozen_at="2026-11-22T12:00:00Z")
    resp = outcome_response(
        case_id="case_" + "0" * 32, run_id=None if blocked else "run_" + "0" * 32,
        claim_type="reel.mechanical.v1", data_mode=mode, isolation_mode="ENFORCED",
        findings=fs, blockers=blockers, parameter_ledger=[], evidence=[], key_records=[],
        diagnostics=None, spec_hash="a" * 64, verdict_hash=None if blocked else "b" * 64, grid_points=16,
        specimen=spec, sensitivity=None,
    )
    assert resp["contractVersion"] == CONTRACT_VERSION
    if mode is DataMode.SYNTHETIC_DEMO:
        assert resp["demonstrationOnly"] and resp["demonstrationNotice"] == DEMONSTRATION_NOTICE
    v("OutcomeResponse").validate(resp)
    if mode is DataMode.SYNTHETIC_DEMO or blocked:
        assert resp["headline"]["confidenceClass"] is None


def test_trade_records_can_never_be_counterexamples():
    f = finding(Basis.EXTERNAL_EVIDENCE, Status.REFUTED)
    rec = {"recordId": "r", "findingId": "f0", "recordRole": "COUNTEREXAMPLE", "recordKind": "TRADE", "payload": {}, "note": ""}
    with pytest.raises(ValueError):
        check_key_records([rec], [f])


def test_counterexample_needs_a_failing_finding():
    f = finding(Basis.EXTERNAL_EVIDENCE, Status.SUPPORTED)
    rec = {"recordId": "r", "findingId": "f0", "recordRole": "COUNTEREXAMPLE", "recordKind": "GRID_POINT", "payload": {}, "note": ""}
    with pytest.raises(ValueError):
        check_key_records([rec], [f])


@pytest.mark.parametrize("cls,lic", [(SourceClass.EXCHANGE_PUBLIC_DATA, LicenseClass.REFETCH_ONLY),
                                     (SourceClass.SYNTHETIC_FIXTURE, LicenseClass.SYNTHETIC),
                                     (SourceClass.DOCUMENT, LicenseClass.DOCUMENT)])
def test_evidence_dto_validates(cls, lic):
    item = EvidenceItem("p", cls, "https://example.invalid/x", "2026-11-22T00:00:00Z", "c" * 64, "text/csv", lic)
    dto = evidence_dto(item, rights_note="note", embedded=lic is not LicenseClass.REFETCH_ONLY)
    v("EvidenceDTO").validate(dto)


def test_live_mode_forbids_synthetic_evidence():
    spec = EvidencePolicySpec(permitted_sources=frozenset({"p"}))
    live = effective_policy(spec, DataMode.LIVE_EVIDENCE)
    demo = effective_policy(spec, DataMode.SYNTHETIC_DEMO)
    assert SourceClass.SYNTHETIC_FIXTURE in live.forbidden_classes
    assert SourceClass.CLAIMANT in live.forbidden_classes and SourceClass.CLAIMANT in demo.forbidden_classes
    assert SourceClass.SYNTHETIC_FIXTURE not in demo.forbidden_classes


def test_specimen_has_no_outcome_channel_and_validates():
    import inspect
    assert "outcome" not in " ".join(inspect.signature(specimen_dto).parameters)
    for mode in DataMode:
        d = specimen_dto(FROZEN, claim_type="reel.mechanical.v1", data_mode=mode,
                         fixture_id="fx_demo" if mode is DataMode.SYNTHETIC_DEMO else None,
                         case_id="case_" + "0" * 32, frozen_at=None)
        v("Specimen").validate(d)
        assert d["source"] == ("SYNTHETIC_FIXTURE" if mode is DataMode.SYNTHETIC_DEMO else "USER_SUBMITTED")


def test_sensitivity_reports_executed_variants():
    pts = [{"fee_bps_per_side": f} for f in ("0", "10", "25")]
    ex = Examination(spec_hash="a" * 64, shared={}, points=tuple(PointResult(point=p, values={}) for p in pts))
    outs = {"total_return": [PointOutcome(point=p, passed=i == 0, margin=Decimal(1 - i)) for i, p in enumerate(pts)]}
    d = sensitivity_dto(examination=ex, template_version="reel.mechanical.v1/sweep-v1", grid_cap=1000,
                        axes=[{"name": "fee_bps_per_side", "values": ["0", "10", "25"], "origin": "DEFAULT_POLICY"}],
                        point_outcomes=outs)
    v("Sensitivity").validate(d)
    assert d["variantsExecuted"] == 3
    r = d["results"][0]
    assert (r["aggregate"], r["passCount"], r["failCount"]) == ("MIXED", 1, 2)
    assert [c["variant"] for c in r["cells"]] == [0, 1, 2]
