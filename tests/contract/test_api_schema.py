"""API contract (docs/API_CONTRACT.md, api/openapi.yaml). Corrections 1–10.

Valid examples must validate; each mutation below breaks exactly one contract rule and
must be rejected by the schema itself, so the frontend and backend cannot drift from it.
"""
import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate as validate_openapi

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "api/openapi.yaml").read_text())
EX = ROOT / "api/examples"


def validator(name):
    return Draft202012Validator({**SPEC, "$ref": f"#/components/schemas/{name}"}, format_checker=FormatChecker())


def load(f):
    return json.loads((EX / f).read_text())


def test_openapi_document_is_valid():
    validate_openapi(SPEC)


@pytest.mark.parametrize(
    "file,schema",
    [
        ("outcome_completed_quote.json", "OutcomeResponse"),
        ("outcome_blocked_reel_rights.json", "OutcomeResponse"),
        ("outcome_indeterminate_gap.json", "OutcomeResponse"),
        ("outcome_synthetic_reel.json", "OutcomeResponse"),
        ("draft_reel_paste.json", "DraftCase"),
        ("bundle_metadata.json", "BundleMetadata"),
        ("replay_report.json", "ReplayReport"),
        ("health_judge.json", "Health"),
        ("intake_reel_paste.json", "IntakeRequest"),
        ("intake_synthetic_fixture.json", "IntakeRequest"),
        ("run_record.json", "RunRecord"),
    ],
)
def test_valid_examples(file, schema):
    validator(schema).validate(load(file))


def test_progress_examples():
    for ev in load("progress_events.json"):
        validator("ProgressEvent").validate(ev)


def _set(obj, path, value):
    cur = obj
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value
    return obj


MUTATIONS = [
    # (base file, schema, path, bad value, rule)
    ("outcome_blocked_reel_rights.json", "OutcomeResponse", ["headline", "confidenceClass"], "EXTERNAL", "2: blocked => confidence null"),
    ("outcome_blocked_reel_rights.json", "OutcomeResponse", ["headline", "confidenceClass"], "DOCUMENT_INTERNAL", "2: blocked => confidence null"),
    ("outcome_blocked_reel_rights.json", "OutcomeResponse", ["blockers"], [], "1: blocked needs a blocker"),
    ("outcome_blocked_reel_rights.json", "OutcomeResponse", ["verdictHash"], "b" * 64, "1: blocked has no verdict"),
    ("outcome_indeterminate_gap.json", "OutcomeResponse", ["findings", 0, "confidenceClass"], "EXTERNAL", "2: indeterminate => confidence null"),
    ("outcome_indeterminate_gap.json", "OutcomeResponse", ["headline", "confidenceClass"], "EXTERNAL", "2: indeterminate => confidence null"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["executionStatus"], "BLOCKED", "1: completed findings cannot be blocked"),
    ("outcome_synthetic_reel.json", "OutcomeResponse", ["findings", 0, "confidenceClass"], "EXTERNAL", "B1: synthetic never has confidence"),
    ("outcome_synthetic_reel.json", "OutcomeResponse", ["demonstrationOnly"], False, "B1: synthetic is demonstration only"),
    ("outcome_synthetic_reel.json", "OutcomeResponse", ["keyRecords", 1, "recordRole"], "COUNTEREXAMPLE", "6: a trade never refutes an aggregate"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["keyRecords", 1, "recordRole"], "COUNTEREXAMPLE", "6: ledger entries are traces"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["diagnostics", "affectsVerdict"], True, "diagnostics are inert"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["evidence", 1, "independenceBasis"], "CLAIMANT_DOCUMENT_SELF", "4: official source is independent"),
    ("draft_reel_paste.json", "DraftCase", ["parameterLedger", 1, "value"], "1d", "5: MISSING has no value"),
    ("draft_reel_paste.json", "DraftCase", ["parameterLedger", 2, "basis"], "USER_FORM", "5: ASSUMED basis is policy"),
    ("draft_reel_paste.json", "DraftCase", ["parameterLedger", 2, "sourceSpan"], {"start": 0, "end": 1}, "5: span only for claimant text"),
    ("bundle_metadata.json", "BundleMetadata", ["authenticity", "status"], "VERIFIED", "10: authenticity not claimed"),
    ("bundle_metadata.json", "BundleMetadata", ["reproducibility", "status"], "REPRODUCED", "10: metadata is not a replay"),
    ("health_judge.json", "Health", ["isolationMode"], "UNENFORCED", "9: judge mode requires isolation"),
    ("intake_reel_paste.json", "IntakeRequest", ["pastedText"], "x" * 2001, "8: pasted text capped"),
    ("intake_reel_paste.json", "IntakeRequest", ["claimType"], "quote.finance.v1", "8: quote has no free text"),
    # --- contract 1.1.0 corrections ---
    ("draft_reel_paste.json", "DraftCase", ["outcomeFields", 0, "value"], "340", "v1.1-1: draft never echoes asserted values"),
    ("intake_synthetic_fixture.json", "IntakeRequest", ["pastedText"], "SMA cross +340%", "no user claim on synthetic data"),
    ("intake_synthetic_fixture.json", "IntakeRequest", ["fixtureId"], None, "synthetic requires a fixture"),
    ("intake_reel_paste.json", "IntakeRequest", ["fixtureId"], "fx_any", "live cases are never fixtures"),
    ("outcome_synthetic_reel.json", "OutcomeResponse", ["demonstrationNotice"], None, "synthetic always labelled"),
    ("outcome_synthetic_reel.json", "OutcomeResponse", ["specimen", "source"], "USER_SUBMITTED", "synthetic specimen is a fixture"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["demonstrationNotice"], "Demonstration only, synthetic data, not real.", "live has no demo notice"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["parameterLedger", 0, "sourceSpan"], {"start": 0, "end": 3}, "no source highlighting after freeze"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["contractVersion"], "1.0.0", "v1.1-2: contract version pinned"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["sensitivity", "variantsExecuted"], 1001, "v1.1-2: sweep bounded"),
    ("outcome_completed_quote.json", "OutcomeResponse", ["sensitivity", "templateVersion"], "v1", "v1.1-2: template version format"),
    ("outcome_blocked_reel_rights.json", "OutcomeResponse", ["sensitivity"], {"templateVersion": "reel.mechanical.v1/sweep-v1", "gridCap": 1000, "variantsExecuted": 1, "axes": [], "results": []}, "blocked has no sensitivity"),
]


@pytest.mark.parametrize("file,schema,path,bad,rule", MUTATIONS, ids=[m[4] for m in MUTATIONS])
def test_contract_rules_enforced_by_schema(file, schema, path, bad, rule):
    doc = _set(copy.deepcopy(load(file)), path, bad)
    assert not validator(schema).is_valid(doc), rule


def test_refetch_only_never_embedded():
    meta = load("outcome_completed_quote.json")["evidence"][1]
    bad = dict(meta, licenseClass="REFETCH_ONLY", embeddedInBundle=True)
    assert not validator("EvidenceDTO").is_valid(bad)


def test_ledger_bound_events_carry_ledger_seq():
    ev = load("progress_events.json")[3]
    assert not validator("ProgressEvent").is_valid(dict(ev, ledgerSeq=None))
    assert not validator("ProgressEvent").is_valid(dict(load("progress_events.json")[0], ledgerSeq=3))


def test_frozen_ledger_drops_source_spans():
    entry = load("draft_reel_paste.json")["parameterLedger"][0]  # has a span
    specimen = load("outcome_completed_quote.json")["specimen"]
    frozen = {"contractVersion": "1.1.0", "specimen": specimen, "caseId": "case_" + "0" * 32, "state": "FROZEN", "specHash": "a" * 64,
              "commitment": {"alg": "sha256/vk-commit-v1", "digest": "b" * 64},
              "frozenAt": "2026-11-22T12:00:00Z", "ledgerSeq": 2, "parameterLedger": [entry]}
    assert not validator("FrozenCase").is_valid(frozen)
    frozen["parameterLedger"] = [dict(entry, sourceSpan=None)]
    validator("FrozenCase").validate(frozen)
