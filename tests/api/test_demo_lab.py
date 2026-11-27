"""Demonstration verification lab (Batch 2): five scenarios over one real signed examination.

Every assertion is about what the backend's own verification code reported for a real bundle.
The lab holds public verifier profiles only; a client names a scenario and never supplies a key.
"""
from __future__ import annotations

import base64
import copy
import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType
from security.helpers import clock, make_case, new_signer
from verdictkit.api.server import create_app
from verdictkit.bundle import write_bundle
from verdictkit.plugin import Registry

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("demo_signer", ROOT / "scripts" / "demo_signer.py")
demo_signer = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(demo_signer)

KEY = base64.b64encode(b"k" * 32).decode()
PARAMS = {
    "selling_price": "30000.00", "addons": [], "doc_fee": "500.00", "doc_fee_taxable": True,
    "gov_fees": [{"code": "TITLE", "amount": "100.00", "taxable": False}], "rebates": [],
    "trade_allowance": "0.00", "trade_payoff": "0.00", "trade_tax_credit": True,
    "cash_down": "5000.00", "stated_tax_rate_pct": "6.00", "apr_pct": "6.00",
    "term_months": 60, "jurisdiction": {"state": "TX"},
}


def registry() -> Registry:
    r = Registry()
    r.register(FinanceClaimType())
    r.register(LeaseClaimType())
    return r


def run_case(client: TestClient) -> str:
    created = client.post("/api/v1/cases", json={
        "claimType": "quote.finance.v1", "dataMode": "LIVE_EVIDENCE",
        "form": {"params": copy.deepcopy(PARAMS), "outcomes": {"sales_tax": "1830.00"}}})
    assert created.status_code == 201, created.text
    case_id = created.json()["caseId"]
    assert client.post(f"/api/v1/cases/{case_id}/freeze").status_code == 200
    assert client.post(f"/api/v1/cases/{case_id}/evidence").status_code == 200
    assert client.post(f"/api/v1/cases/{case_id}/runs").status_code == 202
    return case_id


@pytest.fixture()
def lab_env(tmp_path):
    """The provisioning script's real output: one signing key plus three public verifier profiles."""
    sign_dir, lab_dir = tmp_path / "signing", tmp_path / "lab"
    sign_dir.mkdir()
    key_id = demo_signer.provision(sign_dir, lab_dir)
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY, "VK_JUDGE_MODE": "0",
           "VK_EXAMINER_SOCKET": "", "VK_SIGNING_KEY_FILE": str(sign_dir / "signing.pem"),
           "VK_TRUST_STORE_FILE": str(lab_dir / "trust-trusted.json"), "VK_DEMO_LAB_DIR": str(lab_dir)}
    with patch.dict(os.environ, env):
        yield key_id, sign_dir, lab_dir, tmp_path


def verify(client: TestClient, bundle: bytes, scenario: str):
    return client.post(f"/api/v1/demo/verify?scenario={scenario}", content=bundle)


def test_lab_routes_do_not_exist_unless_the_operator_enables_them(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY, "VK_JUDGE_MODE": "0",
           "VK_EXAMINER_SOCKET": ""}
    with patch.dict(os.environ, env), TestClient(create_app(registry())) as client:
        os.environ.pop("VK_DEMO_LAB_DIR", None)
        assert client.get("/api/v1/demo/status").status_code == 404
        assert verify(client, b"x", "trusted-signer").status_code == 404


def test_status_publishes_public_facts_and_never_key_material(lab_env):
    key_id, sign_dir, _lab, _tmp = lab_env
    pem = (sign_dir / "signing.pem").read_bytes()
    secret_b64 = b"".join(pem.splitlines()[1:-1]).decode()
    with TestClient(create_app(registry())) as client:
        res = client.get("/api/v1/demo/status")
        assert res.status_code == 200 and res.headers["X-VerdictKit-Contract"] == "1.2.0"
        body = res.json()
        assert body["contractVersion"] == "1.2.0" and body["signer"]["keyId"] == key_id
        assert body["signer"]["disposable"] is True
        assert [s["id"] for s in body["scenarios"]] == [
            "trusted-signer", "unknown-signer", "revoked-signer", "unsigned-historical", "tampered-bundle"]
        statuses = {p["id"]: [k["status"] for k in p["trustStore"]["keys"]] for p in body["verifierProfiles"]}
        assert statuses == {"trusted": ["ACTIVE"], "unknown": ["ACTIVE"], "revoked": ["REVOKED"]}
        # The unknown profile must not hold the signer's key.
        keys = {p["id"]: [k["keyId"] for k in p["trustStore"]["keys"]] for p in body["verifierProfiles"]}
        assert key_id in keys["trusted"] and key_id in keys["revoked"] and key_id not in keys["unknown"]
        everything = res.text + client.get("/api/v1/demo/trust-store").text
        assert secret_b64 not in everything and "PRIVATE" not in everything
        assert client.get("/api/v1/demo/trust-store").json()["keys"][0]["key_id"] == key_id


def test_five_scenarios_report_what_the_backend_actually_verified(lab_env):
    key_id, *_ = lab_env
    with TestClient(create_app(registry())) as client:
        case_id = run_case(client)
        bundle = client.get(f"/api/v1/cases/{case_id}/bundle").content
        got = {}
        for name in ("trusted-signer", "unknown-signer", "revoked-signer", "unsigned-historical",
                     "tampered-bundle"):
            res = verify(client, bundle, name)
            assert res.status_code == 200, (name, res.text)
            got[name] = res.json()
            assert got[name]["contractVersion"] == "1.2.0"
            assert got[name]["demo"]["scenario"]["id"] == name
            assert got[name]["demo"]["isolationMode"] in ("ENFORCED", "UNENFORCED")

    def summary(name: str) -> tuple:
        r = got[name]
        a = r["authenticity"]
        return (r["integrity"]["status"], a["signatureValidity"], a["signerTrust"], a["status"],
                r["reproducibility"]["status"])

    reproduced = ("REPRODUCED", "REPRODUCED_ACROSS_ENV")
    s = summary("trusted-signer")
    assert s[:4] == ("VERIFIED", "VALID", "TRUSTED", "ESTABLISHED") and s[4] in reproduced
    assert got["trusted-signer"]["authenticity"]["signer"]["keyId"] == key_id

    s = summary("unknown-signer")
    assert s[:4] == ("VERIFIED", "VALID", "UNTRUSTED_SIGNER", "NOT_ESTABLISHED") and s[4] in reproduced
    assert "KEY_NOT_IN_TRUST_STORE" in got["unknown-signer"]["authenticity"]["reasonCodes"]

    s = summary("revoked-signer")
    assert s[:4] == ("VERIFIED", "VALID", "UNTRUSTED_SIGNER", "NOT_ESTABLISHED") and s[4] in reproduced
    assert "KEY_REVOKED" in got["revoked-signer"]["authenticity"]["reasonCodes"]

    # An unsigned historical bundle still verifies and replays; nothing proves who made it.
    s = summary("unsigned-historical")
    assert s[:4] == ("VERIFIED", "UNSIGNED", "NOT_EVALUATED", "NOT_ESTABLISHED") and s[4] in reproduced
    assert got["unsigned-historical"]["demo"]["tested"]["transform"] == "strip-signature"

    # Tampering is caught by integrity, never excused by a valid signature over the manifest.
    s = summary("tampered-bundle")
    assert s[0] == "FAILED" and s[3] == "NOT_ESTABLISHED" and s[4] == "UNVERIFIABLE"
    assert "INTEGRITY_NOT_VERIFIED" in got["tampered-bundle"]["authenticity"]["reasonCodes"] \
        or got["tampered-bundle"]["authenticity"]["signatureValidity"] != "VALID"
    # The tested bytes differ from the original only for the two transformed scenarios.
    digests = {n: r["demo"]["tested"]["sha256"] for n, r in got.items()}
    assert digests["trusted-signer"] == digests["unknown-signer"] == digests["revoked-signer"]
    assert digests["unsigned-historical"] != digests["trusted-signer"] != digests["tampered-bundle"]


def test_a_key_embedded_in_an_uploaded_bundle_is_never_trusted(lab_env):
    _key_id, _sign, _lab, tmp = lab_env
    (tmp / "stranger").mkdir()
    stranger, _path = new_signer(tmp / "stranger", "stranger.pem")
    case = make_case(tmp / "work")
    bundle = write_bundle(case, tmp / "stranger.vkb", clock=clock, signer=stranger)
    with TestClient(create_app(registry())) as client:
        res = verify(client, bundle.read_bytes(), "trusted-signer")
    assert res.status_code == 200
    a = res.json()["authenticity"]
    assert (a["signatureValidity"], a["signerTrust"], a["status"]) == ("VALID", "UNTRUSTED_SIGNER", "NOT_ESTABLISHED")
    assert a["reasonCodes"] == ["KEY_NOT_IN_TRUST_STORE"] and a["signer"]["keyId"] == stranger.key_id


def test_unknown_scenarios_and_unreadable_uploads_are_refused(lab_env):
    with TestClient(create_app(registry())) as client:
        res = verify(client, b"anything", "trust-me")
        assert res.status_code == 422 and res.json()["error"]["code"] == "UNKNOWN_SCENARIO"
        res = verify(client, b"not a zip archive", "tampered-bundle")
        assert res.status_code == 422 and res.json()["error"]["code"] == "BUNDLE_UNREADABLE"
        res = verify(client, b"", "trusted-signer")
        assert res.status_code == 422


def test_an_enabled_lab_with_unusable_profiles_stops_the_start(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY, "VK_JUDGE_MODE": "0",
           "VK_EXAMINER_SOCKET": "", "VK_DEMO_LAB_DIR": str(empty)}
    with patch.dict(os.environ, env), pytest.raises(RuntimeError, match="demo lab profile"):
        create_app(registry())


def test_provisioning_writes_a_private_key_and_three_public_profiles(tmp_path):
    sign_dir, lab_dir = tmp_path / "s", tmp_path / "l"
    key_id = demo_signer.provision(sign_dir, lab_dir)
    assert sorted(p.name for p in lab_dir.iterdir()) == ["trust-revoked.json", "trust-trusted.json",
                                                         "trust-unknown.json"]
    assert [p.name for p in sign_dir.iterdir()] == ["signing.pem"]
    pem = (sign_dir / "signing.pem").read_bytes()
    for profile in lab_dir.iterdir():
        assert b"PRIVATE" not in profile.read_bytes() and pem.splitlines()[1] not in profile.read_bytes()
    assert key_id in (lab_dir / "trust-trusted.json").read_text()
    assert key_id not in (lab_dir / "trust-unknown.json").read_text()
    again = demo_signer.provision(tmp_path / "s2", tmp_path / "l2")
    assert again != key_id, "the demonstration key is regenerated at every provisioning"
