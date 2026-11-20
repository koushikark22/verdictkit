"""Quote sweeps over unknown document facts (quote req 1.3, 3.6, 4.3; tasks 5.1).

Unknown taxability flags and an unconfirmed lease rounding convention are swept over
{0, 1} with origin DEFAULT_POLICY. Oracle: each grid point is recomputed independently
with the flag resolved, and the expected status is derived from how many points agree.
"""
from __future__ import annotations

import base64
import copy
import os
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st
from jsonschema import Draft202012Validator, FormatChecker

from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType, _finance_worksheet
from quote_autopsy.finance import chain
from quote_autopsy.lease import compute
from quote_autopsy.worksheet import LeaseConvention
from verdictkit.api.server import create_app
from verdictkit.bundle import ReplayStatus, replay_bundle, write_bundle
from verdictkit.custody.intake import SchemaError, freeze
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import Origin, Status
from verdictkit.pipeline import run_case
from verdictkit.plugin import Registry
from verdictkit.sweep import expand_grid

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "api/openapi.yaml").read_text())


def check(schema, body):
    Draft202012Validator({**SPEC, "$ref": f"#/components/schemas/{schema}"},
                         format_checker=FormatChecker()).validate(body)


BASE = {
    "selling_price": "30000.00", "addons": [{"code": "GAP", "amount": "800.00", "taxable": True}],
    "doc_fee": "500.00", "doc_fee_taxable": True,
    "gov_fees": [{"code": "TITLE", "amount": "100.00", "taxable": False}], "rebates": [],
    "trade_allowance": "0.00", "trade_payoff": "0.00", "trade_tax_credit": True,
    "cash_down": "5000.00", "stated_tax_rate_pct": "6.00", "apr_pct": "6.00",
    "term_months": 60, "jurisdiction": {"state": "TX"},
}


def registry():
    r = Registry()
    r.register(FinanceClaimType())
    r.register(LeaseClaimType())
    return r


def run(tmp_path, claim, case_id="c" * 32):
    reg = registry()
    return run_case(claim, registry=reg, examiner=InProcessExaminer(reg), workdir=tmp_path,
                    clock=lambda: "2026-11-20T00:00:00Z", case_id=case_id,
                    vault_key=bytes(32), network=False)


def finance_claim(params, outcomes, unknown=()):
    return {"claim_type": "quote.finance.v1", "schema_version": 1, "params": params,
            "outcomes": outcomes, "assumptions": {name: None for name in unknown}}


def with_unknown_doc_fee():
    p = copy.deepcopy(BASE)
    p["doc_fee_taxable"] = None
    return p


def test_unknown_flag_conditional_with_both_points(tmp_path):
    # taxable_base is 31300.00 if the doc fee is taxable and 30800.00 otherwise.
    case = run(tmp_path, finance_claim(with_unknown_doc_fee(), {"taxable_base": "31300.00"},
                                       ["doc_fee_taxable"]))
    (f,) = case.verdict.findings
    assert f.status is Status.CONDITIONAL
    assert f.assumption_dependencies == ("doc_fee_taxable",)
    assert {c.point["doc_fee_taxable"] for c in f.counterexamples} == {"0", "1"}
    assert "verified at 2 grid points" in f.statement
    (axis,) = case.frozen.assumptions
    assert axis.origin is Origin.DEFAULT_POLICY
    assert case.diagnostics is None  # diagnostics need a fully stated worksheet


def test_unknown_flag_irrelevant_value_is_consistent(tmp_path):
    p = with_unknown_doc_fee()
    p["doc_fee"] = "0.00"
    case = run(tmp_path, finance_claim(p, {"taxable_base": "30800.00"}, ["doc_fee_taxable"]))
    assert case.verdict.findings[0].status is Status.CONSISTENT


def test_unknown_flag_matching_neither_is_contradicted(tmp_path):
    case = run(tmp_path, finance_claim(with_unknown_doc_fee(), {"taxable_base": "1.00"},
                                       ["doc_fee_taxable"]))
    f = case.verdict.findings[0]
    assert f.status is Status.CONTRADICTED and len(f.counterexamples) == 1


def test_grid_is_product_of_unknown_flags(tmp_path):
    p = copy.deepcopy(BASE)
    p["doc_fee_taxable"] = None
    p["trade_tax_credit"] = None
    p["addons"][0]["taxable"] = None
    unknown = ["addons.0.taxable", "doc_fee_taxable", "trade_tax_credit"]
    case = run(tmp_path, finance_claim(p, {"sales_tax": "1878.00"}, unknown))
    assert len(case.examination.points) == 8


@pytest.mark.parametrize("params_mut,unknown", [
    (lambda p: p.update(doc_fee_taxable=None), []),               # unknown but not declared
    (lambda p: None, ["doc_fee_taxable"]),                         # declared but stated
    (lambda p: p.update(doc_fee_taxable=None), ["no_such_flag"]),  # unsupported axis
    (lambda p: p.update(doc_fee_taxable=None), ["gov_fees.5.taxable"]),
])
def test_inconsistent_declarations_are_rejected(params_mut, unknown):
    p = copy.deepcopy(BASE)
    params_mut(p)
    with pytest.raises(SchemaError):
        freeze(FinanceClaimType(), finance_claim(p, {"taxable_base": "1.00"}, unknown))


def test_negative_amount_financed_is_rejected_at_intake():
    p = copy.deepcopy(BASE)
    p["selling_price"] = "1000.00"  # cash down 5000.00 exceeds everything financed
    with pytest.raises(SchemaError, match="negative"):
        FinanceClaimType().validate_params(p)


def test_declared_axis_value_must_be_null():
    claim = finance_claim(with_unknown_doc_fee(), {"taxable_base": "1.00"})
    claim["assumptions"] = {"doc_fee_taxable": "1"}
    with pytest.raises(SchemaError):
        freeze(FinanceClaimType(), claim)


LEASE = {"adjusted_cap_cost": "24123.45", "residual_value": "13001.23", "money_factor": "0.00125",
         "tax_rate_pct": "8.875", "term_months": 36, "rounding_convention": None}


def lease_claim(outcomes, params=LEASE):
    return {"claim_type": "quote.lease.v1", "schema_version": 1, "params": dict(params),
            "outcomes": outcomes, "assumptions": {"rounding_convention": None}}


def test_lease_rounding_sweep(tmp_path):
    args = (Decimal("24123.45"), Decimal("13001.23"), Decimal("0.00125"), 36, Decimal("8.875"))
    comp = compute(*args, LeaseConvention.COMPONENT).total_monthly_payment
    final = compute(*args, LeaseConvention.FINAL).total_monthly_payment
    case = run(tmp_path, lease_claim({"total_monthly_payment": str(comp)}))
    (f,) = case.verdict.findings
    expected = Status.CONSISTENT if abs(comp - final) <= Decimal("0.01") else Status.CONDITIONAL
    assert f.status is expected
    assert len(case.examination.points) == 2
    assert {p.point["rounding_convention"] for p in case.examination.points} == {"0", "1"}


def test_lease_unknown_convention_requires_axis():
    claim = lease_claim({"total_monthly_payment": "1.00"})
    claim["assumptions"] = {}
    with pytest.raises(SchemaError):
        freeze(LeaseClaimType(), claim)


money = st.integers(0, 500_000).map(lambda c: Decimal(c) / 100)


@settings(max_examples=100, deadline=None)
@given(price=st.integers(600_000, 10_000_000).map(lambda c: Decimal(c) / 100), fee=money,
       rate=st.integers(0, 1000).map(lambda b: Decimal(b) / 100),
       pick=st.sampled_from(["taxable", "untaxable", "neither"]))
def test_property_status_matches_independent_oracle(tmp_path_factory, price, fee, rate, pick):
    """Status = CONSISTENT if the stated value matches at both flag values, CONDITIONAL if
    at exactly one, CONTRADICTED if at none (quote req 3.6)."""
    p = copy.deepcopy(BASE)
    p.update(selling_price=format(price, "f"), doc_fee=format(fee, "f"),
             stated_tax_rate_pct=format(rate, "f"), doc_fee_taxable=None)
    oracle = {}
    for flag in (True, False):
        q = dict(p, doc_fee_taxable=flag)
        oracle[flag] = chain(_finance_worksheet(q)).sales_tax
    stated = {"taxable": oracle[True], "untaxable": oracle[False],
              "neither": oracle[True] + Decimal("5.00")}[pick]
    matches = sum(stated == v for v in oracle.values())  # sales_tax tolerance is $0.00 (req 3.6)
    expected = {2: Status.CONSISTENT, 1: Status.CONDITIONAL, 0: Status.CONTRADICTED}[matches]
    case = run(tmp_path_factory.mktemp("p"),
               finance_claim(p, {"sales_tax": format(stated, "f")}, ["doc_fee_taxable"]))
    assert case.verdict.findings[0].status is expected


@settings(max_examples=50, deadline=None)
@given(k=st.integers(0, 3))
def test_property_grid_size_is_two_to_the_unknowns(k):
    p = copy.deepcopy(BASE)
    names = ["doc_fee_taxable", "trade_tax_credit", "addons.0.taxable"][:k]
    for n in names:
        if n == "addons.0.taxable":
            p["addons"][0]["taxable"] = None
        else:
            p[n] = None
    frozen = freeze(FinanceClaimType(), finance_claim(p, {"sales_tax": "1.00"}, names)).frozen
    assert len(expand_grid(frozen.assumptions).points) == 2 ** k


def test_swept_bundle_replays(tmp_path):
    case = run(tmp_path / "run", finance_claim(with_unknown_doc_fee(),
                                               {"taxable_base": "31300.00"}, ["doc_fee_taxable"]))
    path = write_bundle(case, tmp_path / "b.vkb", clock=lambda: "2026-11-20T00:00:00Z")
    report = replay_bundle(path, registry=registry(), workdir=tmp_path / "r")
    assert report.status in (ReplayStatus.REPRODUCED, ReplayStatus.REPRODUCED_ACROSS_ENV), report.notes


def test_http_unknown_flag_is_assumed_and_conditional(tmp_path):
    env = {"VK_DRAFT_DIR": str(tmp_path), "VK_VAULT_KEY": base64.b64encode(b"q" * 32).decode()}
    with patch.dict(os.environ, env):
        with TestClient(create_app(registry())) as c:
            r = c.post("/api/v1/cases", json={
                "claimType": "quote.finance.v1", "dataMode": "LIVE_EVIDENCE",
                "form": {"params": with_unknown_doc_fee(),
                         "outcomes": {"taxable_base": "31300.00"},
                         "assumptions": {"doc_fee_taxable": None}}})
            assert r.status_code == 201, r.text
            check("DraftCase", r.json())
            assert r.json()["blockers"] == []
            ledger = {e["name"]: e for e in r.json()["parameterLedger"]}
            assert ledger["doc_fee_taxable"]["state"] == "ASSUMED"
            assert ledger["doc_fee_taxable"]["basis"] == "DEFAULT_POLICY"
            assert ledger["doc_fee_taxable"]["range"] == {"kind": "SET", "values": ["0", "1"]}
            case_id = r.json()["caseId"]
            assert c.post(f"/api/v1/cases/{case_id}/freeze").status_code == 200
            assert c.post(f"/api/v1/cases/{case_id}/evidence").status_code == 200
            assert c.post(f"/api/v1/cases/{case_id}/runs").json()["state"] == "COMPLETED"
            out = c.get(f"/api/v1/cases/{case_id}/outcome").json()
            check("OutcomeResponse", out)
            assert out["headline"] == {"status": "CONDITIONAL", "confidenceClass": "DOCUMENT_INTERNAL"}
            (res,) = out["sensitivity"]["results"]
            assert res["aggregate"] == "MIXED" and res["passCount"] == 1 and res["failCount"] == 1
            assert [k["recordRole"] for k in out["keyRecords"]] == ["COUNTEREXAMPLE", "COUNTEREXAMPLE"]
            assert all(k["recordKind"] == "WORKSHEET_LINE" for k in out["keyRecords"])
            bundle = c.get(f"/api/v1/cases/{case_id}/bundle").content
            replay = c.post("/api/v1/replays", content=bundle).json()
            assert replay["reproducibility"]["status"] == "REPRODUCED"
            # Undeclared unknown flag: a critical MISSING blocker, freeze refused.
            bad = c.post("/api/v1/cases", json={
                "claimType": "quote.finance.v1", "dataMode": "LIVE_EVIDENCE",
                "form": {"params": with_unknown_doc_fee(), "outcomes": {"taxable_base": "1.00"}}})
            assert bad.status_code == 201
            assert bad.json()["blockers"][0]["code"] == "MISSING_CRITICAL_PARAMETER"
            assert c.post(f"/api/v1/cases/{bad.json()['caseId']}/freeze").status_code == 422
