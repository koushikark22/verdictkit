"""End-to-end HTTP lifecycle with the real quote plugins (core req 13, API contract 1-10).

intake -> PATCH/confirm -> freeze -> evidence -> run -> run record + SSE -> outcome
-> bundle -> bundle metadata -> replay. Every JSON response is validated against
api/openapi.yaml; asserted outcomes must never appear before the verdict join.
"""
from __future__ import annotations

import base64
import copy
import io
import json
import os
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType
from verdictkit.api.server import create_app
from verdictkit.plugin import Registry

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "api/openapi.yaml").read_text())
KEY = base64.b64encode(b"k" * 32).decode()


def check(schema: str, body: object) -> None:
    Draft202012Validator({**SPEC, "$ref": f"#/components/schemas/{schema}"},
                         format_checker=FormatChecker()).validate(body)


def registry() -> Registry:
    r = Registry()
    r.register(FinanceClaimType())
    r.register(LeaseClaimType())
    return r


PARAMS = {
    "selling_price": "30000.00", "addons": [], "doc_fee": "500.00", "doc_fee_taxable": True,
    "gov_fees": [{"code": "TITLE", "amount": "100.00", "taxable": False}], "rebates": [],
    "trade_allowance": "0.00", "trade_payoff": "0.00", "trade_tax_credit": True,
    "cash_down": "5000.00", "stated_tax_rate_pct": "6.00", "apr_pct": "6.00",
    "term_months": 60, "jurisdiction": {"state": "TX"},
}
# taxable_base = 30500.00, tax = 1830.00, AF = 27430.00 (computed by the engine below).
SECRET = "27999.99"


def intake(outcomes: dict) -> dict:
    return {"claimType": "quote.finance.v1", "dataMode": "LIVE_EVIDENCE",
            "form": {"params": copy.deepcopy(PARAMS), "outcomes": outcomes}}


@pytest.fixture()
def client(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY,
           "VK_JUDGE_MODE": "0", "VK_EXAMINER_SOCKET": ""}
    with patch.dict(os.environ, env):
        with TestClient(create_app(registry())) as c:
            yield c


def _to_evidence(client, outcomes) -> str:
    created = client.post("/api/v1/cases", json=intake(outcomes))
    assert created.status_code == 201, created.text
    check("DraftCase", created.json())
    assert SECRET not in created.text
    case_id = created.json()["caseId"]
    frozen = client.post(f"/api/v1/cases/{case_id}/freeze")
    assert frozen.status_code == 200, frozen.text
    check("FrozenCase", frozen.json())
    assert SECRET not in frozen.text
    evidence = client.post(f"/api/v1/cases/{case_id}/evidence")
    assert evidence.status_code == 200
    check("EvidenceResult", evidence.json())
    return case_id


def test_full_lifecycle_contradicted_and_replayed(client):
    case_id = _to_evidence(client, {"amount_financed": SECRET, "sales_tax": "1830.00"})
    status = client.get(f"/api/v1/cases/{case_id}")
    check("CaseSummary", status.json())
    assert status.json()["state"] == "EVIDENCE_ACQUIRED"
    assert client.get(f"/api/v1/cases/{case_id}/outcome").status_code == 425

    run = client.post(f"/api/v1/cases/{case_id}/runs")
    assert run.status_code == 202, run.text
    check("RunAccepted", run.json())
    assert run.json()["state"] == "COMPLETED"
    run_id = run.json()["runId"]

    # Idempotent per case.
    again = client.post(f"/api/v1/cases/{case_id}/runs")
    assert again.status_code == 202 and again.json()["runId"] == run_id

    record = client.get(f"/api/v1/cases/{case_id}/runs/{run_id}")
    check("RunRecord", record.json())
    events = record.json()["events"]
    stages = [e["stage"] for e in events]
    assert stages == ["RUN_QUEUED", "TASK_BLINDED", "EXAMINATION_STARTED",
                      "EXAMINATION_PROGRESS", "EXAMINATION_COMMITTED", "OUTCOMES_REVEALED",
                      "VERDICT_SEALED", "DIAGNOSTICS_APPENDED", "BUNDLE_WRITTEN",
                      "RUN_COMPLETED"]
    assert [e["seq"] for e in events] == list(range(len(events)))
    ledger_seqs = {e["stage"]: e["ledgerSeq"] for e in events if e["ledgerSeq"] is not None}
    assert ledger_seqs == {"EXAMINATION_COMMITTED": 4, "OUTCOMES_REVEALED": 5,
                           "VERDICT_SEALED": 6, "DIAGNOSTICS_APPENDED": 7,
                           "BUNDLE_WRITTEN": 8}
    for e in events:
        check("ProgressEvent", e)
        if e["stage"] in ledger_seqs:
            assert e["ledgerKind"] == e["stage"]

    # SSE replays the persisted record; Last-Event-ID resumes after that seq.
    sse = client.get(f"/api/v1/cases/{case_id}/runs/{run_id}/events")
    assert sse.status_code == 200
    assert sse.headers["content-type"].startswith("text/event-stream")
    data = [json.loads(line[6:]) for line in sse.text.splitlines() if line.startswith("data: ")]
    assert data == events
    resumed = client.get(f"/api/v1/cases/{case_id}/runs/{run_id}/events",
                         headers={"Last-Event-ID": "5"})
    ids = [int(line[4:]) for line in resumed.text.splitlines() if line.startswith("id: ")]
    assert ids == list(range(6, len(events)))
    bad = client.get(f"/api/v1/cases/{case_id}/runs/{run_id}/events",
                     headers={"Last-Event-ID": "-1"})
    assert bad.status_code == 422

    outcome = client.get(f"/api/v1/cases/{case_id}/outcome")
    assert outcome.status_code == 200
    body = outcome.json()
    check("OutcomeResponse", body)
    assert body["executionStatus"] == "COMPLETED"
    assert body["headline"] == {"status": "CONTRADICTED", "confidenceClass": "DOCUMENT_INTERNAL"}
    by_id = {f["findingId"]: f for f in body["findings"]}
    assert by_id["sales_tax"]["status"] == "CONSISTENT"
    af = by_id["amount_financed"]
    assert af["status"] == "CONTRADICTED"
    assert af["numbers"]["observed"] == SECRET  # revealed only after the seal
    assert af["pointOfFailure"] is True
    assert body["keyRecords"][0]["recordRole"] == "COUNTEREXAMPLE"
    assert body["keyRecords"][0]["recordKind"] == "WORKSHEET_LINE"
    assert body["isolationMode"] == "UNENFORCED"
    assert body["sensitivity"]["variantsExecuted"] == 1
    diag = body["diagnostics"]
    assert diag["computedAfterReveal"] is True and diag["affectsVerdict"] is False
    assert diag["items"][0]["label"] == "diagnostic — computed after reveal"
    assert diag["items"][0]["firstBrokenLine"] == "amount_financed"

    bundle = client.get(f"/api/v1/cases/{case_id}/bundle")
    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["verdict_hash"] == body["verdictHash"]
        assert manifest["isolation_mode"] == "UNENFORCED"
        ledger = [json.loads(l) for l in zf.read("ledger/ledger.jsonl").splitlines()]
        assert [e["kind"] for e in ledger][-1] == "BUNDLE_WRITTEN"

    meta = client.get(f"/api/v1/cases/{case_id}/bundle/metadata")
    check("BundleMetadata", meta.json())
    assert meta.json()["integrity"]["status"] == "VERIFIED"
    assert meta.json()["reproducibility"]["status"] == "NOT_RUN"
    assert meta.json()["authenticity"]["status"] == "NOT_ESTABLISHED"

    replay = client.post("/api/v1/replays", content=bundle.content,
                         headers={"content-type": "application/zip"})
    assert replay.status_code == 200
    check("ReplayReport", replay.json())
    assert replay.json()["integrity"]["status"] == "VERIFIED"
    assert replay.json()["reproducibility"]["status"] in ("REPRODUCED", "REPRODUCED_ACROSS_ENV")
    assert replay.json()["reproducibility"]["replayedVerdictHash"] == body["verdictHash"]


def test_consistent_claim_and_state_conflicts(client):
    created = client.post("/api/v1/cases", json=intake({"sales_tax": "1830.00"}))
    case_id = created.json()["caseId"]
    # Run before evidence is a state conflict, not a fabricated verdict.
    assert client.post(f"/api/v1/cases/{case_id}/runs").status_code == 409
    client.post(f"/api/v1/cases/{case_id}/freeze")
    assert client.post(f"/api/v1/cases/{case_id}/runs").status_code == 409
    client.post(f"/api/v1/cases/{case_id}/evidence")
    assert client.post(f"/api/v1/cases/{case_id}/runs").json()["state"] == "COMPLETED"
    body = client.get(f"/api/v1/cases/{case_id}/outcome").json()
    check("OutcomeResponse", body)
    assert body["headline"]["status"] == "CONSISTENT"
    assert body["keyRecords"] == []
    assert client.get(f"/api/v1/cases/{case_id}").json()["state"] == "SEALED"


def test_external_only_claim_is_indeterminate(client):
    # Unsupported jurisdiction (B7 supports TX only): external findings stay INDETERMINATE.
    created = client.post("/api/v1/cases", json={
        **intake({"tax_rate": "6.00"}),
        "form": {"params": {**copy.deepcopy(PARAMS), "jurisdiction": {"state": "CA"}},
                 "outcomes": {"tax_rate": "6.00"}}})
    assert created.status_code == 201, created.text
    case_id = created.json()["caseId"]
    client.post(f"/api/v1/cases/{case_id}/freeze")
    client.post(f"/api/v1/cases/{case_id}/evidence")
    run = client.post(f"/api/v1/cases/{case_id}/runs")
    assert run.json()["state"] == "INDETERMINATE"
    body = client.get(f"/api/v1/cases/{case_id}/outcome").json()
    check("OutcomeResponse", body)
    assert body["executionStatus"] == "INDETERMINATE"
    assert body["headline"] == {"status": "INDETERMINATE", "confidenceClass": None}


def test_patch_confirms_and_edits_without_echoing_outcomes(client):
    created = client.post("/api/v1/cases", json=intake({"monthly_payment": "530.31"}))
    case_id = created.json()["caseId"]
    patched = client.patch(f"/api/v1/cases/{case_id}",
                           json={"params": {"cash_down": "6000.00"},
                                 "outcomes": {"monthly_payment": "511.00"},
                                 "confirm": ["apr_pct"]})
    assert patched.status_code == 200, patched.text
    check("DraftCase", patched.json())
    assert "511.00" not in patched.text and "530.31" not in patched.text
    ledger = {e["name"]: e for e in patched.json()["parameterLedger"]}
    assert ledger["apr_pct"]["basis"] == "USER_CONFIRMED"
    assert ledger["cash_down"]["value"] == "6000.00"
    for bad in ({"confirm": ["no_such_param"]}, {"params": {"selling_price": 1.5}},
                {"unknown": 1}, {"params": {"monthly_payment": "1.00"}}):
        r = client.patch(f"/api/v1/cases/{case_id}", json=bad)
        assert r.status_code == 422, bad
        check("ErrorEnvelope", r.json())
    client.post(f"/api/v1/cases/{case_id}/freeze")
    assert client.patch(f"/api/v1/cases/{case_id}", json={}).status_code == 409


class _NullableQuote(FinanceClaimType):
    """Accepts a null parameter at intake so the critical-blocker path is reachable."""

    def validate_params(self, params):
        if params.get("apr_pct") is None:
            return
        super().validate_params(params)


def test_missing_critical_parameter_blocks_freeze_and_outcome(tmp_path):
    reg = Registry()
    reg.register(_NullableQuote())
    env = {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": KEY}
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as c:
            payload = intake({"monthly_payment": "1.00"})
            payload["form"]["params"]["apr_pct"] = None
            created = c.post("/api/v1/cases", json=payload)
            assert created.status_code == 201, created.text
            check("DraftCase", created.json())
            assert created.json()["blockers"][0]["code"] == "MISSING_CRITICAL_PARAMETER"
            case_id = created.json()["caseId"]
            r = c.post(f"/api/v1/cases/{case_id}/freeze")
            assert r.status_code == 422
            check("BlockedResponse", r.json())
            assert c.get(f"/api/v1/cases/{case_id}").json()["state"] == "DRAFT"
            outcome = c.get(f"/api/v1/cases/{case_id}/outcome")
            assert outcome.status_code == 200
            check("OutcomeResponse", outcome.json())
            assert outcome.json()["executionStatus"] == "BLOCKED"
            assert "1.00" not in json.dumps(outcome.json()["findings"])


def test_tampered_or_hostile_replays_are_unverifiable(client):
    case_id = _to_evidence(client, {"sales_tax": "1830.00"})
    client.post(f"/api/v1/cases/{case_id}/runs")
    original = client.get(f"/api/v1/cases/{case_id}/bundle").content

    def rezip(mutate) -> bytes:
        src = zipfile.ZipFile(io.BytesIO(original))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as dst:
            for name in src.namelist():
                data = mutate(name, src.read(name))
                if data is not None:
                    dst.writestr(name, data)
        return out.getvalue()

    tampered = rezip(lambda n, d: d.replace(b"1830.00", b"1830.01") if n == "claim/reveal.json" else d)
    dropped = rezip(lambda n, d: None if n == "ledger/ledger.jsonl" else d)
    for blob in (tampered, dropped, b"not a zip", b"PK\x03\x04garbage"):
        r = client.post("/api/v1/replays", content=blob, headers={"content-type": "application/zip"})
        assert r.status_code == 200, r.text
        check("ReplayReport", r.json())
        assert r.json()["reproducibility"]["status"] == "UNVERIFIABLE"
        assert r.json()["reproducibility"]["replayedVerdictHash"] is None
    r = client.post("/api/v1/replays", content=tampered, headers={"content-type": "application/zip"})
    assert r.json()["integrity"]["status"] == "FAILED"
    too_big = client.post("/api/v1/replays", content=b"x" * (8 * 1024 * 1024 + 1))
    assert too_big.status_code == 413


def test_zip_bomb_is_refused_before_decompression(client):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", b"0" * (70 * 1024 * 1024))
    assert len(out.getvalue()) < 8 * 1024 * 1024
    r = client.post("/api/v1/replays", content=out.getvalue())
    assert r.status_code == 200
    assert r.json()["reproducibility"]["status"] == "UNVERIFIABLE"
    assert r.json()["notes"][0] == "bundle is malformed"


def test_unknown_runs_and_cases_are_not_found(client):
    fake = "case_" + "0" * 32
    for path in (f"/api/v1/cases/{fake}/outcome", f"/api/v1/cases/{fake}/bundle",
                 f"/api/v1/cases/{fake}/bundle/metadata",
                 f"/api/v1/cases/{fake}/runs/run_{'0' * 32}",
                 f"/api/v1/cases/{fake}/runs/run_{'0' * 32}/events",
                 f"/api/v1/cases/{fake}/runs/../../x"):
        r = client.get(path)
        assert r.status_code == 404, path
        assert r.json()["contractVersion"] == "1.1.0"


def test_run_of_other_case_is_not_disclosed(client):
    a = _to_evidence(client, {"sales_tax": "1830.00"})
    b = _to_evidence(client, {"sales_tax": "1830.00"})
    run_a = client.post(f"/api/v1/cases/{a}/runs").json()["runId"]
    assert client.get(f"/api/v1/cases/{b}/runs/{run_a}").status_code == 404


def test_examiner_failure_fails_closed_without_verdict(client, monkeypatch):
    import verdictkit.api.server as server_mod

    class Broken:
        from verdictkit.model import IsolationMode
        isolation = IsolationMode.UNENFORCED

        def examine(self, task):
            raise RuntimeError("SECRET_PATH /var/lib/vk/vault")

    monkeypatch.setattr(server_mod, "_make_examiner", lambda *_a: Broken())
    case_id = _to_evidence(client, {"sales_tax": "1830.00"})
    r = client.post(f"/api/v1/cases/{case_id}/runs")
    assert r.status_code == 500
    assert "SECRET_PATH" not in r.text
    check("ErrorEnvelope", r.json())
    assert client.get(f"/api/v1/cases/{case_id}").json()["state"] == "FAILED"
    assert client.get(f"/api/v1/cases/{case_id}/bundle").status_code == 404
    out = client.get(f"/api/v1/cases/{case_id}/outcome")
    assert out.status_code == 500 and "verdictHash" not in out.text


def test_examiner_spec_substitution_is_rejected(client, monkeypatch):
    import verdictkit.api.server as server_mod
    from verdictkit.examiner.client import InProcessExaminer

    class Substituting(InProcessExaminer):
        def examine(self, task):
            from dataclasses import replace
            result = super().examine(task)
            return replace(result, spec_hash="f" * 64)

    monkeypatch.setattr(server_mod, "_make_examiner", lambda _iso, reg: Substituting(reg))
    case_id = _to_evidence(client, {"sales_tax": "1830.00"})
    assert client.post(f"/api/v1/cases/{case_id}/runs").status_code == 500


def test_claim_types_outside_contract_are_not_exposed(tmp_path):
    from stub_claimtype.receipt import ReceiptClaimType
    reg = Registry()
    reg.register(FinanceClaimType())
    reg.register(ReceiptClaimType())
    env = {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": KEY}
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as c:
            body = c.get("/api/v1/claim-types").json()
            check("ClaimTypesResponse", body)
            assert {t["claimType"] for t in body["claimTypes"]} == {"quote.finance.v1"}
            r = c.post("/api/v1/cases", json={"claimType": "example.receipt.v1",
                                              "dataMode": "LIVE_EVIDENCE",
                                              "form": {"params": {"items": ["1.00"]},
                                                       "outcomes": {"stated_total": "1.00"}}})
            assert r.status_code == 422


def test_judge_mode_expires_frozen_cases(tmp_path):
    from verdictkit.api.draft_store import DraftStore
    from verdictkit.api.freeze_boundary import prepare_freeze
    from verdictkit.api.intake_boundary import prepare_intake

    case_id = "case_" + "a" * 32
    store = DraftStore(tmp_path, b"q" * 32, ttl_seconds=10, expire_frozen=True)
    prepared = prepare_intake(intake({"sales_tax": "1830.00"}), registry())
    store.create(case_id, prepared, now=100)
    freeze = prepare_freeze(FinanceClaimType(), store.load_private(case_id, now=100),
                            case_id=case_id, clock=lambda: "2026-01-01T00:00:00Z")
    store.freeze(case_id, freeze, frozen_at="2026-01-01T00:00:00Z", now=100)
    assert store.get_metadata(case_id, now=105)["state"] == "FROZEN"
    from verdictkit.api.draft_store import DraftNotFound
    with pytest.raises(DraftNotFound):
        store.get_metadata(case_id, now=200)
    assert store.purge_expired(now=200) == 1
    with pytest.raises(DraftNotFound):
        store.load_private(case_id, now=105)


# ---- Reel pasted text (API contract §8) ----------------------------------------------

def _reel_client(tmp_path):
    from reel_autopsy.claim_type import ReelClaimType
    reg = Registry()
    reg.register(ReelClaimType())
    reg.register(FinanceClaimType())
    env = {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": KEY}
    return env, reg


PASTE = "SMA_CROSS fast 10 slow 30 instrument BTCUSD timeframe 1d start 2024-01-01 end 2025-01-01, return +340%"


def test_reel_paste_is_transient_spanned_and_write_only(tmp_path):
    env, reg = _reel_client(tmp_path)
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as c:
            types = {t["claimType"]: t for t in c.get("/api/v1/claim-types").json()["claimTypes"]}
            assert types["reel.mechanical.v1"]["acceptsPastedText"] is True
            assert types["quote.finance.v1"]["acceptsPastedText"] is False
            r = c.post("/api/v1/cases", json={"claimType": "reel.mechanical.v1",
                                              "dataMode": "LIVE_EVIDENCE", "pastedText": PASTE})
            assert r.status_code == 201, r.text
            body = r.json()
            check("DraftCase", body)
            assert "340" not in r.text  # extracted outcome is write-only
            ledger = {e["name"]: e for e in body["parameterLedger"]}
            assert ledger["template"]["basis"] == "CLAIMANT_TEXT"
            span = ledger["template"]["sourceSpan"]
            assert PASTE[span["start"]:span["end"]] == "SMA_CROSS"
            assert ledger["instrument_mode"]["state"] == "MISSING"
            assert {b["field"] for b in body["blockers"]} == {"instrument_mode"}
            captured = {o["name"]: o["captured"] for o in body["outcomeFields"]}
            assert captured == {"max_drawdown_pct": False, "total_return_pct": True,
                                "trade_count": False, "win_rate_pct": False}
            case_id = body["caseId"]
            # Freeze is refused while a critical parameter is missing.
            assert c.post(f"/api/v1/cases/{case_id}/freeze").status_code == 422
            patched = c.patch(f"/api/v1/cases/{case_id}",
                              json={"params": {"instrument_mode": "SPOT_LONG_FLAT"}})
            assert patched.status_code == 200, patched.text
            check("DraftCase", patched.json())
            after = {e["name"]: e for e in patched.json()["parameterLedger"]}
            assert after["template"]["basis"] == "CLAIMANT_TEXT"
            assert after["template"]["sourceSpan"] is None  # text was discarded
            assert after["instrument_mode"]["basis"] == "USER_FORM"
            assert patched.json()["blockers"] == []
            frozen = c.post(f"/api/v1/cases/{case_id}/freeze")
            assert frozen.status_code == 200, frozen.text
            check("FrozenCase", frozen.json())
            # No licensed OHLCV provider: evidence stays BLOCKED (fail closed).
            ev = c.post(f"/api/v1/cases/{case_id}/evidence")
            assert ev.status_code == 422
            outcome = c.get(f"/api/v1/cases/{case_id}/outcome").json()
            check("OutcomeResponse", outcome)
            assert outcome["executionStatus"] == "BLOCKED"
    for f in tmp_path.rglob("*"):
        if f.is_file():
            data = f.read_bytes()
            assert b"SMA_CROSS fast 10" not in data and b"return +340%" not in data


@pytest.mark.parametrize("text", [
    "SMA cross on BTC, see https://example.com/x", "SMA cross by @trader_joe",
    "mail me a@b.co SMA cross", "call 415-555-0100 SMA cross", "x" * 2001,
])
def test_reel_paste_privacy_rejected(tmp_path, text):
    env, reg = _reel_client(tmp_path)
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as c:
            r = c.post("/api/v1/cases", json={"claimType": "reel.mechanical.v1",
                                              "dataMode": "LIVE_EVIDENCE", "pastedText": text})
            assert r.status_code == 422
            assert r.json()["error"]["code"] in ("PRIVACY_REJECTED", "SCHEMA_INVALID")
            if len(text) <= 2000:
                assert r.json()["error"]["code"] == "PRIVACY_REJECTED"
            assert text not in r.text


def test_iso_dates_do_not_trip_phone_rule(tmp_path):
    env, reg = _reel_client(tmp_path)
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as c:
            r = c.post("/api/v1/cases", json={"claimType": "reel.mechanical.v1",
                                              "dataMode": "LIVE_EVIDENCE",
                                              "pastedText": "BUY_AND_HOLD start 2024-01-01 end 2025-06-30"})
            assert r.status_code == 201, r.text


def test_quote_rejects_pasted_text(tmp_path):
    env, reg = _reel_client(tmp_path)
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as c:
            payload = intake({"sales_tax": "1.00"})
            payload["pastedText"] = "anything"
            r = c.post("/api/v1/cases", json=payload)
            assert r.status_code == 422
