"""HTTP draft intake must remain redacted, persistent and fail closed."""
import base64
import os

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from verdictkit.plugin import Registry
from verdictkit.api.server import create_app

class DemoType:
    type_id = "quote.finance.v1"
    schema_version = 1
    outcome_fields = frozenset({"monthly_payment"})
    param_fields = frozenset({"selling_price"})

    def validate_params(self, params):
        if not isinstance(params.get("selling_price"), str):
            raise ValueError("bad selling_price")

    def validate_outcomes(self, outcomes):
        if not isinstance(outcomes.get("monthly_payment"), str):
            raise ValueError("bad monthly_payment")

    def assumption_specs(self, _declared):
        return ()

    def tolerances(self, _params, _outcomes):
        return {"monthly_payment": "0.01"}

    def evidence_requests(self, _params):
        return ()

    def evidence_policy(self):
        from verdictkit.plugin import EvidencePolicySpec
        return EvidencePolicySpec(frozenset())


def _registry():
    registry = Registry()
    registry.register(DemoType())
    return registry


def _payload(secret="OUTCOME_SECRET_125"):
    return {"claimType": "quote.finance.v1", "dataMode": "LIVE_EVIDENCE",
            "form": {"params": {"selling_price": "25000.00"},
                     "outcomes": {"monthly_payment": secret}}}


def test_http_create_and_get_are_redacted_and_durable(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": base64.b64encode(b"x" * 32).decode()}
    with patch.dict(os.environ, env):
        with TestClient(create_app(_registry())) as client:
            response = client.post("/api/v1/cases", json=_payload())
            assert response.status_code == 201, response.text
            body = response.json()
            assert body["contractVersion"] == "1.1.0"
            assert body["caseId"].startswith("case_")
            assert body["state"] == "DRAFT"
            assert body["outcomeFields"] == [{"name": "monthly_payment", "captured": True}]
            assert "OUTCOME_SECRET_125" not in response.text
            assert "25000.00" in response.text
            case_id = body["caseId"]
            assert client.get(f"/api/v1/cases/{case_id}").status_code == 200
            frozen = client.post(f"/api/v1/cases/{case_id}/freeze")
            assert frozen.status_code == 200, frozen.text
            assert frozen.json()["state"] == "FROZEN"
            assert frozen.json()["commitment"]["alg"] == "sha256/vk-commit-v1"
            assert frozen.json()["ledgerSeq"] == 2
            assert "OUTCOME_SECRET_125" not in frozen.text
            assert client.post(f"/api/v1/cases/{case_id}/freeze").status_code == 409
            evidence = client.post(f"/api/v1/cases/{case_id}/evidence")
            assert evidence.status_code == 200, evidence.text
            assert evidence.json() == {"contractVersion": "1.1.0", "caseId": case_id, "evidence": []}
            assert client.get(f"/api/v1/cases/{case_id}/evidence").json()["evidence"] == []
            assert client.post(f"/api/v1/cases/{case_id}/evidence").status_code == 409
            assert client.patch(f"/api/v1/cases/{case_id}", json={}).status_code == 409
        # Simulate API restart: stable encryption key and database persist.
        with TestClient(create_app(_registry())) as restarted:
            status = restarted.get(f"/api/v1/cases/{case_id}")
            assert status.status_code == 200
            assert status.json()["isolationMode"] == "UNENFORCED"
            assert status.json()["state"] == "EVIDENCE_ACQUIRED"
            assert status.json()["specHash"] == frozen.json()["specHash"]
            assert "OUTCOME_SECRET_125" not in status.text


def test_http_intake_invalid_mode_is_rejected_without_case(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": base64.b64encode(b"x" * 32).decode()}
    with patch.dict(os.environ, env):
        with TestClient(create_app(_registry())) as client:
            payload = _payload()
            payload["dataMode"] = "SYNTHETIC_DEMO"
            payload["fixtureId"] = "fx_example"
            response = client.post("/api/v1/cases", json=payload)
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "POLICY_VIOLATION"


def test_http_missing_key_does_not_start_draft_operations(tmp_path):
    with patch.dict(os.environ, {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": ""}):
        with TestClient(create_app(_registry())) as client:
            response = client.post("/api/v1/cases", json=_payload())
            assert response.status_code == 503
            assert "OUTCOME_SECRET_125" not in response.text


def test_http_malformed_case_id_not_found(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": base64.b64encode(b"x" * 32).decode()}
    with patch.dict(os.environ, env):
        with TestClient(create_app(_registry())) as client:
            r = client.get("/api/v1/cases/../../etc/passwd")
            assert r.status_code in (404, 422)
            r = client.get("/api/v1/cases/invalid")
            assert r.status_code == 404

def test_env_judge_mode_rejects_unenforced_factory(tmp_path):
    env = {"VK_JUDGE_MODE": "1", "VK_ISOLATION": "enforced", "VK_EXAMINER_SOCKET": ""}
    with patch.dict(os.environ, env):
        import pytest
        with pytest.raises(RuntimeError, match="judge mode"):
            create_app(_registry())

def test_freeze_persistence_survives_restart_and_expiry(tmp_path):
    from verdictkit.api.draft_store import DraftStore
    from verdictkit.api.freeze_boundary import prepare_freeze
    case_id = "case_" + "e" * 32
    key = b"z" * 32
    store = DraftStore(tmp_path, key, ttl_seconds=10)
    from verdictkit.api.intake_boundary import prepare_intake
    prepared = prepare_intake(_payload("CONFIDENTIAL_OUTCOME"), _registry())
    store.create(case_id, prepared, now=100)
    freeze = prepare_freeze(DemoType(), store.load_private(case_id, now=100),
                            case_id=case_id, clock=lambda: "2026-01-01T00:00:00Z")
    store.freeze(case_id, freeze, frozen_at="2026-01-01T00:00:00Z", now=100)
    before = store.get_freeze(case_id)
    reopened = DraftStore(tmp_path, key, ttl_seconds=10)
    assert reopened.get_freeze(case_id) == before
    assert reopened.get_metadata(case_id, now=200)["state"] == "FROZEN"
    assert reopened.purge_expired(now=200) == 0
    with pytest.raises(Exception):
        reopened.freeze(case_id, freeze, frozen_at="2026-01-01T00:01:00Z", now=200)
    assert reopened.get_freeze(case_id) == before
    db = (tmp_path / "drafts.sqlite3").read_bytes()
    assert b"CONFIDENTIAL_OUTCOME" not in db
    assert freeze.salt.hex().encode() not in db

def test_reel_without_source_stays_blocked_without_creating_evidence(tmp_path):
    class Reel(DemoType):
        type_id = "reel.mechanical.v1"

    reg = Registry()
    reg.register(Reel())
    env = {"VK_DRAFT_DIR": str(tmp_path),
           "VK_VAULT_KEY": base64.b64encode(b"x" * 32).decode()}
    with patch.dict(os.environ, env):
        with TestClient(create_app(reg)) as client:
            payload = _payload()
            payload["claimType"] = "reel.mechanical.v1"
            created = client.post("/api/v1/cases", json=payload)
            assert created.status_code == 201
            case_id = created.json()["caseId"]
            assert client.post(f"/api/v1/cases/{case_id}/freeze").status_code == 200
            response = client.post(f"/api/v1/cases/{case_id}/evidence")
            assert response.status_code == 422
            assert response.json()["executionStatus"] == "BLOCKED"
            assert response.json()["blockers"][0]["code"] == "EVIDENCE_UNAVAILABLE"
            assert client.get(f"/api/v1/cases/{case_id}").json()["state"] == "FROZEN"
            assert client.get(f"/api/v1/cases/{case_id}/evidence").status_code == 404
