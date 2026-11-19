"""HTTP draft intake must remain redacted, persistent and fail closed."""
import base64
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from verdictkit.api.server import create_app
from verdictkit.plugin import Registry


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
            assert client.post(f"/api/v1/cases/{case_id}/freeze").status_code == 503
            assert client.patch(f"/api/v1/cases/{case_id}", json={}).status_code == 503
        # Simulate API restart: stable encryption key and database persist.
        with TestClient(create_app(_registry())) as restarted:
            status = restarted.get(f"/api/v1/cases/{case_id}")
            assert status.status_code == 200
            assert status.json()["isolationMode"] == "UNENFORCED"
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
