"""Decision B7 (Texas): packaged rules snapshot, evidence adapter and external findings.
Requirements: quote 5.1-5.6. Spec: docs/B7_TEXAS_SPEC.md section 7.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import shutil
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

import quote_autopsy.rules as rules_module
from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType
from quote_autopsy.rules import RulesIntegrityError, load_rules
from quote_autopsy.sources import TexasRulesAdapter
from verdictkit import mcp_server
from verdictkit.api.server import create_app
from verdictkit.bundle import ReplayStatus, replay_bundle, write_bundle
from verdictkit.canonical import canonical_bytes, parse_canonical
from verdictkit.evidence.broker import EvidenceBroker
from verdictkit.evidence.store import EvidenceStore
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import Status
from verdictkit.pipeline import run_case
from verdictkit.plugin import EvidenceRequest, Registry

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "api/openapi.yaml").read_text())
RULES_DIR = Path(rules_module.__file__).parent / "rules"
TX_BYTES = (RULES_DIR / "TX.json").read_bytes()
CLOCK = lambda: "2026-11-24T00:00:00Z"  # noqa: E731


def check(schema, body):
    Draft202012Validator({**SPEC, "$ref": f"#/components/schemas/{schema}"},
                         format_checker=FormatChecker()).validate(body)


class FinanceNoAdapter(FinanceClaimType):
    """Same claim type, but the Texas adapter is not registered with the broker."""

    def evidence_adapters(self):
        return ()


class FinanceTampered(FinanceClaimType):
    def __init__(self, adapter):
        super().__init__()
        self._adapter = adapter

    def evidence_adapters(self):
        return (self._adapter,)


BASE = {
    "selling_price": "30000.00", "addons": [{"code": "GAP", "amount": "800.00", "taxable": True}],
    "doc_fee": "150.00", "doc_fee_taxable": False,
    "gov_fees": [{"code": "TITLE", "amount": "100.00", "taxable": False}], "rebates": [],
    "trade_allowance": "0.00", "trade_payoff": "0.00", "trade_tax_credit": True,
    "cash_down": "5000.00", "stated_tax_rate_pct": "6.25", "apr_pct": "6.00",
    "term_months": 60, "jurisdiction": {"state": "TX"},
}
INTERNAL = {"taxable_base": "30800.00", "sales_tax": "1925.00"}


def params(**over):
    p = copy.deepcopy(BASE)
    for k, v in over.items():
        if k == "state":
            p["jurisdiction"] = {"state": v}
        elif k == "locality":
            p["jurisdiction"] = {"state": "TX", "locality_code": v}
        else:
            p[k] = v
    return p


def claim(p, outcomes, claim_type="quote.finance.v1"):
    return {"claim_type": claim_type, "schema_version": 1, "params": p,
            "outcomes": outcomes, "assumptions": {}}


def run(tmp_path, raw, finance=None, case_id="b" * 32):
    reg = Registry()
    reg.register(finance or FinanceClaimType())
    reg.register(LeaseClaimType())
    return run_case(raw, registry=reg, examiner=InProcessExaminer(reg, evidence_root=str(tmp_path / "evidence")),
                    workdir=tmp_path,
                    clock=CLOCK, case_id=case_id, vault_key=bytes(32), network=False)


def by_id(case):
    return {f.finding_id: f for f in case.verdict.findings}


def test_tx_snapshot_matches_manifest_and_is_canonical():
    """Req 5.1: packaged snapshot loads, is canonical, matches the manifest, cites sources."""
    rules = load_rules(RULES_DIR / "TX.json", RULES_DIR / "MANIFEST.json")
    assert canonical_bytes(parse_canonical(TX_BYTES)) == TX_BYTES
    manifest = json.loads((RULES_DIR / "MANIFEST.json").read_bytes())
    assert manifest["files"]["TX.json"] == hashlib.sha256(TX_BYTES).hexdigest() == rules.snapshot_sha256
    sources = parse_canonical(TX_BYTES)["sources"]
    for needle in ("motor-vehicle/sales-use", "96-254/tax-rates", "98-805", "b16-5"):
        assert any(needle in s["uri"] for s in sources), needle
    for s in sources:
        assert s["uri"].startswith("https://")
        assert len(s["retrieved_at"]) == 10 and s["retrieved_at"][4] == "-"
        assert len(s["sha256_of_source"]) == 64 and int(s["sha256_of_source"], 16) >= 0


def test_tx_snapshot_values():
    """Req 5.1: Texas values exactly as spec section 2."""
    r = load_rules(RULES_DIR / "TX.json", RULES_DIR / "MANIFEST.json")
    assert r.state == "TX" and r.state_rate_pct == Decimal("6.25")
    assert (r.local_rate_min_pct, r.local_rate_max_pct) == (Decimal("0.00"), Decimal("0.00"))
    assert r.localities is None
    assert r.doc_fee_kind == "PRESUMED_REASONABLE_AMOUNT" and r.doc_fee_amount == Decimal("225.00")


def test_loader_rejects_doc_fee_schema_violations(tmp_path):
    """Req 5.1: each doc_fee schema violation raises RulesIntegrityError."""
    good = parse_canonical(TX_BYTES)

    def attempt(mutate):
        doc = copy.deepcopy(good)
        mutate(doc)
        data = canonical_bytes(doc)
        (tmp_path / "TX.json").write_bytes(data)
        (tmp_path / "MANIFEST.json").write_text(
            json.dumps({"files": {"TX.json": hashlib.sha256(data).hexdigest()}}))
        with pytest.raises(RulesIntegrityError):
            load_rules(tmp_path / "TX.json", tmp_path / "MANIFEST.json")

    attempt(lambda d: d["doc_fee"].update(kind="CAP"))
    attempt(lambda d: d["doc_fee"].update(kind="NO_STATUTORY_LIMIT"))  # amount not null
    attempt(lambda d: d["doc_fee"].update(amount=225))
    attempt(lambda d: d["doc_fee"].pop("applies_to"))
    attempt(lambda d: d.update(doc_fee_cap="225.00"))


def test_tampered_snapshot_serves_no_evidence(tmp_path):
    """Design (hash mismatch): tampered snapshot -> no evidence, tax_rate evidence_unavailable."""
    tampered = tmp_path / "TX.json"
    tampered.write_bytes(TX_BYTES.replace(b"6.25", b"6.26", 1))
    shutil.copy(RULES_DIR / "MANIFEST.json", tmp_path / "MANIFEST.json")
    adapter = TexasRulesAdapter(tampered, tmp_path / "MANIFEST.json")
    ft = FinanceTampered(adapter)
    broker = EvidenceBroker(EvidenceStore(tmp_path / "ev"), [adapter], network=False, clock=CLOCK)
    with pytest.raises(RulesIntegrityError):
        broker.acquire([EvidenceRequest("tx-rules-snapshot-v1", {"state": "TX"})], ft.evidence_policy())
    raw = claim(params(), {**INTERNAL, "tax_rate": "6.25"})
    case = run(tmp_path / "bad", raw, finance=ft)
    plain = run(tmp_path / "ok", claim(params(), INTERNAL), case_id="c" * 32)
    f = by_id(case)
    assert f["tax_rate"].status is Status.INDETERMINATE and f["tax_rate"].reason == "evidence_unavailable"
    assert case.evidence == ()
    for k in INTERNAL:
        assert f[k] == by_id(plain)[k]


def test_tx_tax_rate_supported_and_refuted(tmp_path):
    """Req 5.2, 5.3: 6.25/6.250 SUPPORTED; other rates REFUTED with expected 6.25."""
    for i, rate in enumerate(("6.25", "6.250")):
        f = by_id(run(tmp_path / f"s{i}", claim(params(), {"tax_rate": rate})))["tax_rate"]
        assert f.status is Status.SUPPORTED
        assert f.evidence_used and f.numbers["tolerance"] == "0"
    for i, rate in enumerate(("6.00", "8.25")):
        f = by_id(run(tmp_path / f"r{i}", claim(params(), {"tax_rate": rate})))["tax_rate"]
        assert f.status is Status.REFUTED
        assert f.numbers["expected"] == "6.25" and f.numbers["observed"] == rate
        assert f.counterexamples


def test_tx_locality_does_not_change_rate(tmp_path):
    """Req 5.2: a locality code is ignored; Texas has no local motor vehicle tax."""
    ok = by_id(run(tmp_path / "a", claim(params(locality="AUSTIN"), {"tax_rate": "6.25"})))["tax_rate"]
    bad = by_id(run(tmp_path / "b", claim(params(locality="AUSTIN"), {"tax_rate": "8.25"})))["tax_rate"]
    assert ok.status is Status.SUPPORTED
    assert bad.status is Status.REFUTED


def test_tx_doc_fee_at_or_below_presumed_amount_supported(tmp_path):
    """Req 5.4 (TX): fee at or below 225.00 is SUPPORTED."""
    for i, fee in enumerate(("150.00", "225.00")):
        f = by_id(run(tmp_path / str(i), claim(params(doc_fee=fee), {"doc_fee_cap": fee})))["doc_fee_cap"]
        assert f.status is Status.SUPPORTED
        assert "7 TAC" in f.statement and "no OCCC filing required" in f.statement


def test_tx_doc_fee_above_presumed_amount_is_never_refuted(tmp_path):
    """Req 5.4 (TX): fee above 225.00 is INDETERMINATE(requires_regulator_filing)."""
    for i, fee in enumerate(("225.01", "500.00", "1500.00")):
        f = by_id(run(tmp_path / str(i), claim(params(doc_fee=fee), {"doc_fee_cap": fee})))["doc_fee_cap"]
        assert f.status is Status.INDETERMINATE and f.reason == "requires_regulator_filing"


def test_non_tx_external_findings_unsupported_jurisdiction(tmp_path):
    """Req 5.5: non-TX external findings are INDETERMINATE(unsupported_jurisdiction)."""
    case = run(tmp_path / "ca", claim(params(state="CA"), {**INTERNAL, "tax_rate": "6.25",
                                                          "doc_fee_cap": "150.00"}))
    plain = run(tmp_path / "tx0", claim(params(), INTERNAL), case_id="c" * 32)
    f = by_id(case)
    for name in ("tax_rate", "doc_fee_cap"):
        assert f[name].status is Status.INDETERMINATE and f[name].reason == "unsupported_jurisdiction"
    assert case.evidence == ()
    for k in INTERNAL:
        assert f[k] == by_id(plain)[k]


def test_tx_lease_tax_rate_not_applicable(tmp_path):
    """Req 5.6: Texas lease tax_rate is INDETERMINATE(not_applicable_lease_tax_model)."""
    lease = {"adjusted_cap_cost": "30000.00", "residual_value": "18000.00", "money_factor": "0.00125",
             "tax_rate_pct": "6.25", "term_months": 36, "rounding_convention": "COMPONENT"}
    reduced = run(tmp_path / "r", claim(lease, {"tax_rate": "6.25"}, "quote.lease.v1"))
    assert by_id(reduced)["tax_rate"].reason == "evidence_unavailable"  # no jurisdiction: unchanged
    itemised = {"msrp": "35000.00", "selling_price": "30000.00", "capitalized_items": [],
                "cap_cost_reductions": [], "residual_value": "18000.00", "money_factor": "0.00125",
                "term_months": 36, "stated_tax_rate_pct": "6.25", "jurisdiction": {"state": "TX"},
                "rounding_convention": "COMPONENT"}
    f = by_id(run(tmp_path / "i", claim(itemised, {"tax_rate": "6.25"}, "quote.lease.v1")))["tax_rate"]
    assert f.status is Status.INDETERMINATE and f.reason == "not_applicable_lease_tax_model"


def test_external_snapshot_does_not_change_internal_verdict(tmp_path):
    """Core invariant: internal findings are identical with and without the adapter."""
    raw = claim(params(stated_tax_rate_pct="6.00"), {"taxable_base": "30800.00", "sales_tax": "1925.00",
                                                    "amount_financed": "27000.00"})
    with_adapter = run(tmp_path / "a", raw)
    without = run(tmp_path / "b", raw, finance=FinanceNoAdapter())
    assert len(with_adapter.evidence) == 1 and without.evidence == ()
    assert with_adapter.verdict.findings == without.verdict.findings
    assert with_adapter.verdict.headline == without.verdict.headline


def test_tx_bundle_replays_offline(tmp_path):
    """Core 9: a TX bundle embeds the snapshot and replays with no refetch."""
    case = run(tmp_path / "run", claim(params(), {**INTERNAL, "tax_rate": "6.25", "doc_fee_cap": "150.00"}))
    assert case.evidence_blobs and TX_BYTES in case.evidence_blobs.values()
    path = write_bundle(case, tmp_path / "b.vkb", clock=CLOCK)
    reg = Registry()
    reg.register(FinanceClaimType())
    reg.register(LeaseClaimType())
    report = replay_bundle(path, registry=reg, workdir=tmp_path / "replay", allow_refetch=False)
    assert report.manifest_ok and report.ledger_ok and report.commitment_ok and report.spec_hash_ok
    assert report.replayed_verdict_hash == report.original_verdict_hash
    assert report.status in (ReplayStatus.REPRODUCED, ReplayStatus.REPRODUCED_ACROSS_ENV), report.notes


def test_http_tx_case_acquires_official_evidence(tmp_path):
    """HTTP: LIVE_EVIDENCE TX case freezes, acquires one GOVERNMENT_OFFICIAL item, tax_rate SUPPORTED."""
    reg = Registry()
    reg.register(FinanceClaimType())
    reg.register(LeaseClaimType())
    env = {"VK_DRAFT_DIR": str(tmp_path / "custody"), "VK_JUDGE_MODE": "0", "VK_EXAMINER_SOCKET": "",
           "VK_VAULT_KEY": base64.b64encode(b"k" * 32).decode()}
    with patch.dict(os.environ, env), TestClient(create_app(reg)) as c:
        created = c.post("/api/v1/cases", json={
            "claimType": "quote.finance.v1", "dataMode": "LIVE_EVIDENCE",
            "form": {"params": params(), "outcomes": {"tax_rate": "6.25"}}})
        assert created.status_code == 201, created.text
        case_id = created.json()["caseId"]
        assert c.post(f"/api/v1/cases/{case_id}/freeze").status_code == 200
        ev = c.post(f"/api/v1/cases/{case_id}/evidence")
        assert ev.status_code == 200, ev.text
        check("EvidenceResult", ev.json())
        items = ev.json()["evidence"]
        assert len(items) == 1 and items[0]["origin"] == "GOVERNMENT_OFFICIAL"
        assert items[0]["independenceBasis"] == "INDEPENDENT_OF_CLAIMANT"
        assert c.post(f"/api/v1/cases/{case_id}/runs").status_code == 202
        body = c.get(f"/api/v1/cases/{case_id}/outcome").json()
        check("OutcomeResponse", body)
        assert len(body["evidence"]) == 1
        tax = next(f for f in body["findings"] if f["findingId"] == "tax_rate")
        assert tax["status"] == "SUPPORTED"


def test_mcp_verify_claim_tx(monkeypatch):
    """MCP: verify_claim with VK_MCP_READONLY=1 serves the local snapshot without network."""
    monkeypatch.setenv("VK_MCP_READONLY", "1")
    result = mcp_server.verify_claim(claim(params(), {"tax_rate": "6.25"}))
    assert "error" not in result, result
    f = {x["finding_id"]: x for x in result["verdict"]["findings"]}
    assert f["tax_rate"]["status"] == "SUPPORTED"
