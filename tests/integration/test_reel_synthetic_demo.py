"""SYNTHETIC_DEMO fixtures through the real pipeline (reel task 8, req 5.6; API contract §3).

Positive: each bundled fixture runs intake -> freeze -> evidence -> run -> outcome ->
bundle -> replay and the engine computes the status the fixture is labelled with.
Negative: no user claim can reach synthetic data; LIVE_EVIDENCE never accepts it.
Tampering: altered fixture bytes, altered embedded evidence and foreign evidence hashes
are refused. Every JSON response is validated against api/openapi.yaml.
"""
from __future__ import annotations

import base64
import hashlib
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

from reel_autopsy.claim_type import ReelClaimType
from reel_autopsy.fixtures import FIXTURES
from reel_autopsy.sources import synthetic
from verdictkit.api.server import create_app
from verdictkit.evidence.store import EvidenceIntegrityError, ReadOnlyEvidence
from verdictkit.model import DataMode
from verdictkit.plugin import EvidenceRequest, Registry

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "api/openapi.yaml").read_text())
KEY = base64.b64encode(b"s" * 32).decode()
EXPECTED = {
    "fx_reel_supported_hold": ("SUPPORTED", {"trade_count": "SUPPORTED"}),
    "fx_reel_conditional_sma": ("CONDITIONAL", {"total_return_pct": "CONDITIONAL",
                                                "total_return_bound": "WITHIN_BOUND"}),
    "fx_reel_impossible_sma": ("IMPOSSIBLE", {"total_return_pct": "REFUTED",
                                              "total_return_bound": "IMPOSSIBLE"}),
}


def check(schema: str, body: object) -> None:
    Draft202012Validator({**SPEC, "$ref": f"#/components/schemas/{schema}"},
                         format_checker=FormatChecker()).validate(body)


@pytest.fixture()
def client(tmp_path):
    reg = Registry()
    reg.register(ReelClaimType())
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY,
           "VK_EXAMINER_SOCKET": "", "VK_EVIDENCE_DIR": ""}
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as c:
            yield c


def _demo(client, fixture_id: str) -> str:
    r = client.post("/api/v1/cases", json={"claimType": "reel.mechanical.v1",
                                           "dataMode": "SYNTHETIC_DEMO", "fixtureId": fixture_id})
    assert r.status_code == 201, r.text
    check("DraftCase", r.json())
    assert r.json()["dataMode"] == "SYNTHETIC_DEMO"
    case_id = r.json()["caseId"]
    frozen = client.post(f"/api/v1/cases/{case_id}/freeze")
    assert frozen.status_code == 200, frozen.text
    check("FrozenCase", frozen.json())
    assert frozen.json()["specimen"]["source"] == "SYNTHETIC_FIXTURE"
    assert frozen.json()["specimen"]["fixtureId"] == fixture_id
    ev = client.post(f"/api/v1/cases/{case_id}/evidence")
    assert ev.status_code == 200, ev.text
    check("EvidenceResult", ev.json())
    (item,) = ev.json()["evidence"]
    assert item["origin"] == "SYNTHETIC_FIXTURE"
    assert item["independenceBasis"] == "SYNTHETIC_NOT_EVIDENCE"
    assert item["licenseClass"] == "SYNTHETIC" and item["embeddedInBundle"] is True
    assert item["snapshotHash"] == synthetic.PINNED_SHA256
    return case_id


@pytest.mark.parametrize("fixture_id", sorted(FIXTURES))
def test_fixture_runs_through_real_pipeline(client, fixture_id):
    headline, statuses = EXPECTED[fixture_id]
    case_id = _demo(client, fixture_id)
    run = client.post(f"/api/v1/cases/{case_id}/runs")
    assert run.status_code == 202, run.text
    assert run.json()["state"] == "COMPLETED"
    record = client.get(run.json()["runUrl"]).json()
    check("RunRecord", record)
    assert {e["stage"] for e in record["events"]} >= {"EXAMINATION_COMMITTED", "VERDICT_SEALED",
                                                      "BUNDLE_WRITTEN", "RUN_COMPLETED"}
    out = client.get(f"/api/v1/cases/{case_id}/outcome").json()
    check("OutcomeResponse", out)
    assert out["dataMode"] == "SYNTHETIC_DEMO" and out["demonstrationOnly"] is True
    assert out["demonstrationNotice"].startswith("DEMONSTRATION ONLY")
    assert out["headline"] == {"status": headline, "confidenceClass": None}
    assert {f["findingId"]: f["status"] for f in out["findings"]} == statuses
    assert all(f["confidenceClass"] is None for f in out["findings"])
    assert out["specimen"]["fixtureId"] == fixture_id
    assert out["evidence"][0]["snapshotHash"] == synthetic.PINNED_SHA256
    sens = out["sensitivity"]
    assert sens["variantsExecuted"] == 16  # 4 fee x 4 slippage x 1 position fraction
    assert {a["name"]: a["origin"] for a in sens["axes"]} == {
        "fee_bps_per_side": "DEFAULT_POLICY", "slippage_bps_per_side": "DEFAULT_POLICY",
        "position_fraction": "DEFAULT_POLICY"}
    for rec in out["keyRecords"]:
        assert rec["recordKind"] == "GRID_POINT"

    bundle = client.get(f"/api/v1/cases/{case_id}/bundle").content
    with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
        assert json.loads(zf.read("manifest.json"))["data_mode"] == "SYNTHETIC_DEMO"
        assert zf.read(f"evidence/blobs/{synthetic.PINNED_SHA256}") == synthetic.load()
    meta = client.get(f"/api/v1/cases/{case_id}/bundle/metadata").json()
    check("BundleMetadata", meta)
    assert meta["embeddedEvidence"] == ["ev_" + synthetic.PINNED_SHA256[:16]]
    replay = client.post("/api/v1/replays", content=bundle).json()
    check("ReplayReport", replay)
    assert replay["integrity"]["status"] == "VERIFIED"
    assert replay["reproducibility"]["status"] == "REPRODUCED"
    assert replay["reproducibility"]["replayedVerdictHash"] == out["verdictHash"]


def test_conditional_fixture_reports_both_passing_and_failing_points(client):
    case_id = _demo(client, "fx_reel_conditional_sma")
    client.post(f"/api/v1/cases/{case_id}/runs")
    out = client.get(f"/api/v1/cases/{case_id}/outcome").json()
    (res,) = [r for r in out["sensitivity"]["results"] if r["findingId"] == "total_return_pct"]
    assert res["aggregate"] == "MIXED" and res["passCount"] > 0 and res["failCount"] > 0
    assert res["passCount"] + res["failCount"] == 16
    f = next(f for f in out["findings"] if f["findingId"] == "total_return_pct")
    assert "verified at 16 grid points" in f["statement"]


@pytest.mark.parametrize("payload", [
    {"fixtureId": "fx_does_not_exist"},
    {"fixtureId": "../../etc/passwd"},
    {"fixtureId": None},
    {"fixtureId": "fx_reel_supported_hold",
     "form": {"params": {}, "outcomes": {"trade_count": "99"}}},
    {"fixtureId": "fx_reel_supported_hold", "pastedText": "BUY_AND_HOLD return 50%"},
])
def test_no_user_claim_reaches_synthetic_data(client, payload):
    r = client.post("/api/v1/cases", json={"claimType": "reel.mechanical.v1",
                                           "dataMode": "SYNTHETIC_DEMO", **payload})
    assert r.status_code == 422
    check("ErrorEnvelope", r.json())
    assert r.json()["error"]["code"] == "POLICY_VIOLATION"


def test_fixture_claims_cannot_be_edited(client):
    r = client.post("/api/v1/cases", json={"claimType": "reel.mechanical.v1",
                                           "dataMode": "SYNTHETIC_DEMO",
                                           "fixtureId": "fx_reel_impossible_sma"})
    case_id = r.json()["caseId"]
    patched = client.patch(f"/api/v1/cases/{case_id}",
                           json={"outcomes": {"total_return_pct": "1"}})
    assert patched.status_code == 422
    assert patched.json()["error"]["code"] == "POLICY_VIOLATION"


def test_live_case_on_synthetic_instrument_is_blocked(client):
    claim = FIXTURES["fx_reel_impossible_sma"]
    r = client.post("/api/v1/cases", json={
        "claimType": "reel.mechanical.v1", "dataMode": "LIVE_EVIDENCE",
        "form": {"params": claim["params"], "outcomes": claim["outcomes"]}})
    assert r.status_code == 201
    case_id = r.json()["caseId"]
    assert client.post(f"/api/v1/cases/{case_id}/freeze").status_code == 200
    ev = client.post(f"/api/v1/cases/{case_id}/evidence")
    assert ev.status_code == 422
    check("BlockedResponse", ev.json())
    assert ev.json()["blockers"][0]["code"] == "POLICY_VIOLATION"
    out = client.get(f"/api/v1/cases/{case_id}/outcome").json()
    check("OutcomeResponse", out)
    assert out["executionStatus"] == "BLOCKED" and out["verdictHash"] is None


def test_generator_reproduces_committed_fixture_and_digest():
    assert synthetic.generate() == synthetic.load()
    assert hashlib.sha256(synthetic.generate()).hexdigest() == synthetic.PINNED_SHA256
    assert synthetic.load().startswith(b"# SYNTHETIC OHLCV - generated test data, NOT market data")


def test_adapter_refuses_tampered_fixture_and_other_instruments(monkeypatch):
    adapter = synthetic.SyntheticFixtureAdapter()
    with pytest.raises(ValueError):
        adapter.fetch(EvidenceRequest(synthetic.SOURCE_ID, {"instrument": "BTC-USD"}))
    from importlib import resources
    real = resources.files

    class Tampered:
        def __init__(self, pkg):
            self._p = real(pkg)

        def joinpath(self, name):
            src = self._p.joinpath(name)

            class F:
                def read_bytes(self_inner):
                    return src.read_bytes().replace(b"100.00", b"100.01", 1)
            return F()

    monkeypatch.setattr(resources, "files", Tampered)
    with pytest.raises(ValueError, match="pinned digest"):
        synthetic.load()


def test_examiner_reader_is_limited_to_task_hashes(tmp_path):
    from verdictkit.evidence.store import EvidenceMeta, EvidenceStore
    store = EvidenceStore(tmp_path)
    a = store.put(b"aaa", EvidenceMeta("s", synthetic.SyntheticFixtureAdapter.source_class,
                                       "u", "t", "text/plain",
                                       synthetic.SyntheticFixtureAdapter.license_class))
    b = store.put(b"bbb", EvidenceMeta("s", synthetic.SyntheticFixtureAdapter.source_class,
                                       "u", "t", "text/plain",
                                       synthetic.SyntheticFixtureAdapter.license_class))
    reader = ReadOnlyEvidence(tmp_path, [a.sha256])
    assert reader.read(a.sha256) == b"aaa"
    with pytest.raises(KeyError):
        reader.read(b.sha256)
    (tmp_path / "blobs" / a.sha256).write_bytes(b"tampered")
    with pytest.raises(EvidenceIntegrityError):
        reader.read(a.sha256)


def test_tampered_embedded_evidence_is_unverifiable(client):
    case_id = _demo(client, "fx_reel_supported_hold")
    client.post(f"/api/v1/cases/{case_id}/runs")
    original = client.get(f"/api/v1/cases/{case_id}/bundle").content
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as src, zipfile.ZipFile(out, "w") as dst:
        for name in src.namelist():
            data = src.read(name)
            if name.startswith("evidence/blobs/"):
                data = data.replace(b"100.00", b"100.01", 1)
            dst.writestr(name, data)
    r = client.post("/api/v1/replays", content=out.getvalue()).json()
    check("ReplayReport", r)
    assert r["integrity"]["status"] == "FAILED"
    assert r["reproducibility"]["status"] == "UNVERIFIABLE"


def test_cli_pipeline_live_mode_drops_synthetic_evidence(tmp_path):
    """Core-level fail-closed: the same claim in LIVE_EVIDENCE gets no synthetic evidence."""
    from verdictkit.examiner.client import InProcessExaminer
    from verdictkit.pipeline import run_case
    reg = Registry()
    reg.register(ReelClaimType())
    case = run_case(FIXTURES["fx_reel_impossible_sma"], registry=reg,
                    examiner=InProcessExaminer(reg, evidence_root=str(tmp_path / "ev")),
                    workdir=tmp_path / "w", clock=lambda: "2026-11-20T00:00:00Z",
                    vault_key=bytes(32), data_mode=DataMode.LIVE_EVIDENCE,
                    evidence_root=tmp_path / "ev", network=False)
    assert case.evidence == ()
    assert {f.status.value for f in case.verdict.findings} == {"INDETERMINATE"}


def test_ui_fixture_list_matches_server():
    """The Reel UI may only offer fixture ids the server actually bundles."""
    import re
    source = (ROOT / "apps/reel-autopsy/web/src/intake.ts").read_text()
    ui_ids = set(re.findall(r'id: "(fx_[a-z0-9_]+)"', source))
    assert ui_ids == set(FIXTURES)
