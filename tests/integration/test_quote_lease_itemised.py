"""Itemised lease worksheet (quote req 2.1, 4.1) and per-line tolerances (req 3.6)."""
from __future__ import annotations

import copy
from decimal import ROUND_HALF_UP, Decimal

import pytest
from hypothesis import given, settings, strategies as st

from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType
from verdictkit.custody.intake import SchemaError, freeze
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import Status
from verdictkit.pipeline import run_case
from verdictkit.plugin import Registry

ITEMISED = {
    "msrp": "42000.00", "selling_price": "39500.00",
    "capitalized_items": [{"code": "ACQUISITION_FEE", "amount": "895.00"},
                          {"code": "DOC_FEE", "amount": "150.00"}],
    "cap_cost_reductions": [{"code": "CASH", "amount": "2000.00"},
                            {"code": "REBATE", "amount": "1000.00"}],
    "residual_pct_of_msrp": "58", "money_factor": "0.00125", "term_months": 36,
    "stated_tax_rate_pct": "8.25", "jurisdiction": {"state": "TX"}, "rounding_convention": "COMPONENT",
}


def registry():
    r = Registry()
    r.register(LeaseClaimType())
    r.register(FinanceClaimType())
    return r


def run(tmp_path, claim_type, params, outcomes, assumptions=None):
    reg = registry()
    return run_case({"claim_type": claim_type, "schema_version": 1, "params": params,
                     "outcomes": outcomes, "assumptions": assumptions or {}},
                    registry=reg, examiner=InProcessExaminer(reg), workdir=tmp_path,
                    clock=lambda: "2026-11-20T00:00:00Z", vault_key=bytes(32), network=False)


def statuses(case):
    return {f.finding_id: f.status for f in case.verdict.findings}


def test_itemised_cap_cost_and_residual(tmp_path):
    # gross = 39500 + 895 + 150 = 40545.00; adjusted = 40545 - 3000 = 37545.00;
    # residual = 42000 * 58% = 24360.00
    case = run(tmp_path, "quote.lease.v1", ITEMISED, {
        "stated_gross_cap_cost": "40545.00", "stated_adjusted_cap_cost": "37545.00",
        "stated_residual_value": "24360.00"})
    assert set(statuses(case).values()) == {Status.CONSISTENT}


def test_itemised_line_mismatch_is_contradicted_exactly(tmp_path):
    case = run(tmp_path, "quote.lease.v1", ITEMISED, {"stated_adjusted_cap_cost": "37545.01"})
    (f,) = case.verdict.findings
    assert f.status is Status.CONTRADICTED and f.numbers["tolerance"] == "0.00"


def test_residual_pct_rounds_half_up_to_cents(tmp_path):
    p = dict(ITEMISED, msrp="33333.33", residual_pct_of_msrp="57.5")
    expected = (Decimal("33333.33") * Decimal("57.5") / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
    case = run(tmp_path, "quote.lease.v1", p, {"stated_residual_value": format(expected, "f")})
    assert case.verdict.findings[0].status is Status.CONSISTENT


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(residual_value="20000.00"),           # both residual forms
    lambda p: p.pop("residual_pct_of_msrp"),                   # neither
    lambda p: p.update(term_months=61),                        # req 2.1: 1-60
    lambda p: p["capitalized_items"].append({"code": "GAP", "amount": "1"}),
    lambda p: p["cap_cost_reductions"].append({"code": "CASH", "amount": "-1"}),
    lambda p: p.update(residual_pct_of_msrp="101"),
    lambda p: p.update(jurisdiction={"state": "Texas"}),
])
def test_itemised_schema_rejections(mutate):
    p = copy.deepcopy(ITEMISED)
    mutate(p)
    with pytest.raises(SchemaError):
        LeaseClaimType().validate_params(p)


def test_reduced_form_cannot_derive_gross_cap_cost(tmp_path):
    reduced = {"adjusted_cap_cost": "24000.00", "residual_value": "12000.00", "money_factor": "0.00125",
               "tax_rate_pct": "8.25", "term_months": 36, "rounding_convention": "FINAL"}
    case = run(tmp_path, "quote.lease.v1", reduced, {"stated_gross_cap_cost": "1.00",
                                                     "stated_adjusted_cap_cost": "24000.00"})
    s = statuses(case)
    assert s["stated_gross_cap_cost"] is Status.INDETERMINATE
    assert s["stated_adjusted_cap_cost"] is Status.CONSISTENT
    assert case.verdict.headline is Status.INDETERMINATE or case.verdict.headline is Status.CONSISTENT


def test_itemised_rounding_sweep(tmp_path):
    p = dict(ITEMISED, rounding_convention=None)
    case = run(tmp_path, "quote.lease.v1", p, {"stated_adjusted_cap_cost": "37545.00"},
               {"rounding_convention": None})
    assert len(case.examination.points) == 2
    assert case.verdict.findings[0].status is Status.CONSISTENT


cents = st.integers(1_000_000, 8_000_000).map(lambda c: Decimal(c) / 100)


@settings(max_examples=60, deadline=None)
@given(price=cents, fee=st.integers(0, 200_000).map(lambda c: Decimal(c) / 100),
       pct=st.integers(30, 70), mf=st.integers(0, 400).map(lambda m: Decimal(m) / 100000),
       n=st.integers(12, 60), conv=st.sampled_from(["COMPONENT", "FINAL"]))
def test_property_itemised_equals_reduced(tmp_path_factory, price, fee, pct, mf, n, conv):
    """For the same adjusted cap cost and residual, both lease forms give the same payment."""
    msrp = price + 1000
    itemised = {"msrp": format(msrp, "f"), "selling_price": format(price, "f"),
                "capitalized_items": [{"code": "ACQUISITION_FEE", "amount": format(fee, "f")}],
                "cap_cost_reductions": [], "residual_pct_of_msrp": str(pct),
                "money_factor": format(mf, "f"), "term_months": n, "stated_tax_rate_pct": "7.00",
                "jurisdiction": {"state": "TX"}, "rounding_convention": conv}
    residual = (msrp * pct / Decimal(100)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    reduced = {"adjusted_cap_cost": format(price + fee, "f"), "residual_value": format(residual, "f"),
               "money_factor": format(mf, "f"), "tax_rate_pct": "7.00", "term_months": n,
               "rounding_convention": conv}
    a = run(tmp_path_factory.mktemp("a"), "quote.lease.v1", itemised, {"total_monthly_payment": "1.00"})
    b = run(tmp_path_factory.mktemp("b"), "quote.lease.v1", reduced, {"total_monthly_payment": "1.00"})
    assert a.examination.points[0].values["total_monthly_payment"] == \
        b.examination.points[0].values["total_monthly_payment"]


def test_finance_tolerances_follow_req_3_6():
    t = FinanceClaimType().tolerances({}, {"amount_financed": "1", "monthly_payment": "1",
                                           "taxable_base": "1", "finance_charge": "1"})
    assert t == {"amount_financed": "0.00", "taxable_base": "0.00", "monthly_payment": "0.01",
                 "finance_charge": "0.01"}
