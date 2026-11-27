"""Signed bundles through the HTTP API (design D5, contract 1.2.0), with the real quote plugins.

The custodian signs when VK_SIGNING_KEY_FILE is set; verification reads the operator's trust
store (VK_TRUST_STORE_FILE). Responses are validated against api/openapi.yaml.
"""
from __future__ import annotations

import base64
import copy
import io
import os
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType
from security.helpers import new_signer, trust_store
from verdictkit.api.server import create_app
from verdictkit.plugin import Registry

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "api/openapi.yaml").read_text(encoding="utf-8"))
KEY = base64.b64encode(b"k" * 32).decode()
PARAMS = {
    "selling_price": "30000.00", "addons": [], "doc_fee": "500.00", "doc_fee_taxable": True,
    "gov_fees": [{"code": "TITLE", "amount": "100.00", "taxable": False}], "rebates": [],
    "trade_allowance": "0.00", "trade_payoff": "0.00", "trade_tax_credit": True,
    "cash_down": "5000.00", "stated_tax_rate_pct": "6.00", "apr_pct": "6.00",
    "term_months": 60, "jurisdiction": {"state": "TX"},
}


def check(schema: str, body: object) -> None:
    Draft202012Validator({**SPEC, "$ref": f"#/components/schemas/{schema}"},
                         format_checker=FormatChecker()).validate(body)


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
def signing_env(tmp_path):
    signer, key_file = new_signer(tmp_path)
    trust = trust_store(tmp_path / "trust.json", signer)
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY, "VK_JUDGE_MODE": "0",
           "VK_EXAMINER_SOCKET": "", "VK_SIGNING_KEY_FILE": str(key_file), "VK_TRUST_STORE_FILE": str(trust)}
    with patch.dict(os.environ, env):
        yield signer, tmp_path


def test_signed_run_is_exported_verifiable_and_replays(signing_env):
    signer, _tmp = signing_env
    with TestClient(create_app(registry())) as client:
        case_id = run_case(client)
        bundle = client.get(f"/api/v1/cases/{case_id}/bundle").content
        meta = client.get(f"/api/v1/cases/{case_id}/bundle/metadata").json()
        check("BundleMetadata", meta)
        a = meta["authenticity"]
        assert (a["signatureValidity"], a["signerTrust"], a["status"]) == ("VALID", "TRUSTED", "ESTABLISHED")
        assert a["signer"]["keyId"] == signer.key_id and meta["integrity"]["status"] == "VERIFIED"
        assert meta["reproducibility"]["status"] == "NOT_RUN", "authenticity never stands in for reproducibility"
        assert zipfile.ZipFile(io.BytesIO(bundle)).namelist().count("signature/envelope.json") == 1

        replay = client.post("/api/v1/replays", content=bundle).json()
        check("ReplayReport", replay)
        assert replay["reproducibility"]["status"] in ("REPRODUCED", "REPRODUCED_ACROSS_ENV")
        assert replay["authenticity"]["status"] == "ESTABLISHED"
        assert replay["contractVersion"] == "1.2.0"
        outcome = client.get(f"/api/v1/cases/{case_id}/outcome").json()
        assert replay["reproducibility"]["replayedVerdictHash"] == outcome["verdictHash"]


def test_a_tampered_signed_bundle_is_not_authentic_and_is_not_reproduced(signing_env):
    with TestClient(create_app(registry())) as client:
        case_id = run_case(client)
        original = client.get(f"/api/v1/cases/{case_id}/bundle").content
        src = zipfile.ZipFile(io.BytesIO(original))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as dst:
            for name in src.namelist():
                data = src.read(name)
                if name == "claim/reveal.json":
                    data = data.replace(b"1830.00", b"1830.01")
                dst.writestr(name, data)
        replay = client.post("/api/v1/replays", content=out.getvalue()).json()
        check("ReplayReport", replay)
        assert replay["integrity"]["status"] == "FAILED"
        assert replay["reproducibility"]["status"] == "UNVERIFIABLE"
        assert replay["authenticity"]["status"] == "NOT_ESTABLISHED"
        assert replay["authenticity"]["signatureValidity"] == "VALID", "the signed manifest bytes are unchanged"
        assert replay["authenticity"]["reasonCodes"] == ["INTEGRITY_NOT_VERIFIED"]


def test_without_a_trust_store_the_signer_is_valid_but_not_trusted(signing_env):
    with patch.dict(os.environ):
        os.environ.pop("VK_TRUST_STORE_FILE")
        with TestClient(create_app(registry())) as client:
            case_id = run_case(client)
            a = client.get(f"/api/v1/cases/{case_id}/bundle/metadata").json()["authenticity"]
            assert (a["signatureValidity"], a["signerTrust"], a["status"]) == (
                "VALID", "NOT_EVALUATED", "NOT_ESTABLISHED")
            assert a["reasonCodes"] == ["TRUST_STORE_NOT_CONFIGURED"]


def test_bundles_from_an_unconfigured_server_stay_unsigned_and_replay(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY, "VK_JUDGE_MODE": "0",
           "VK_EXAMINER_SOCKET": ""}
    with patch.dict(os.environ, env):
        for name in ("VK_SIGNING_KEY_FILE", "VK_TRUST_STORE_FILE"):
            os.environ.pop(name, None)
        with TestClient(create_app(registry())) as client:
            case_id = run_case(client)
            bundle = client.get(f"/api/v1/cases/{case_id}/bundle").content
            assert "signature/envelope.json" not in zipfile.ZipFile(io.BytesIO(bundle)).namelist()
            a = client.get(f"/api/v1/cases/{case_id}/bundle/metadata").json()["authenticity"]
            check("AuthenticityReport", a)
            assert (a["signatureValidity"], a["status"]) == ("UNSIGNED", "NOT_ESTABLISHED")
            replay = client.post("/api/v1/replays", content=bundle).json()
            assert replay["reproducibility"]["status"] in ("REPRODUCED", "REPRODUCED_ACROSS_ENV")


def test_an_unusable_signing_key_stops_the_server_instead_of_downgrading(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY": KEY, "VK_JUDGE_MODE": "0",
           "VK_EXAMINER_SOCKET": "", "VK_SIGNING_KEY_FILE": str(tmp_path / "absent.pem")}
    with patch.dict(os.environ, env):
        with pytest.raises(RuntimeError, match="SIGNING_KEY_MISSING") as err:
            create_app(registry())
        assert str(tmp_path) not in str(err.value)


def test_startup_entry_point_exits_2_on_an_unusable_signing_key(tmp_path, capsys):
    from verdictkit.api import __main__ as entry
    with patch.dict(os.environ, {"VK_SIGNING_KEY_FILE": str(tmp_path / "absent.pem"), "VK_JUDGE_MODE": "0"}):
        with patch("sys.argv", ["verdictkit.api", "--check-startup"]):
            assert entry.main() == 2
    assert "VK_STARTUP_ERROR=CONFIG_INVALID:VK_SIGNING_KEY_FILE" in capsys.readouterr().err


def test_a_key_file_given_as_vault_key_source_works_through_the_server(tmp_path):
    """DD8-2 end to end: the custodian takes its key from VK_VAULT_KEY_FILE, once, and removes it."""
    from verdictkit.custody import keyfile
    key_file = tmp_path / "vault.key"
    key_file.write_text(KEY)
    if os.name != "nt":
        key_file.chmod(0o400)
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_VAULT_KEY_FILE": str(key_file), "VK_JUDGE_MODE": "0",
           "VK_EXAMINER_SOCKET": ""}
    keyfile._from_file.clear()
    with patch.dict(os.environ, env):
        os.environ.pop("VK_VAULT_KEY", None)
        for name in ("VK_SIGNING_KEY_FILE", "VK_TRUST_STORE_FILE"):
            os.environ.pop(name, None)
        with TestClient(create_app(registry())) as client:
            assert not key_file.exists(), "the key file is removed after the single read"
            assert run_case(client).startswith("case_")
    keyfile._from_file.clear()
