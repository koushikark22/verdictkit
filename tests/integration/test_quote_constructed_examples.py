"""The Quote UI's constructed example worksheets (quote task 8) give the labelled results
when run through the engine, so UI copy can never drift from real arithmetic."""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from quote_autopsy.claim_type import FinanceClaimType
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import Status
from verdictkit.pipeline import run_case
from verdictkit.plugin import Registry

ROOT = Path(__file__).resolve().parents[2]
DATA = json.loads((ROOT / "apps/quote-autopsy/web/src/examples.json").read_text())


def _params(form: dict) -> dict:
    flag = {"yes": True, "no": False}
    return {
        "selling_price": form["selling_price"],
        "addons": [{"code": form["addon_code"], "amount": form["addon_amount"],
                    "taxable": flag[form["addon_taxable"]]}],
        "doc_fee": form["doc_fee"], "doc_fee_taxable": flag[form["doc_fee_taxable"]],
        "gov_fees": [{"code": "TITLE", "amount": form["gov_fee_amount"],
                      "taxable": flag[form["gov_fee_taxable"]]}],
        "rebates": [], "trade_allowance": form["trade_allowance"],
        "trade_payoff": form["trade_payoff"], "trade_tax_credit": flag[form["trade_tax_credit"]],
        "cash_down": form["cash_down"], "stated_tax_rate_pct": form["stated_tax_rate_pct"],
        "apr_pct": form["apr_pct"], "term_months": int(form["term_months"]),
        "jurisdiction": {"state": form["state"]},
    }


@pytest.mark.parametrize("example", DATA["examples"], ids=lambda e: e["id"])
def test_constructed_example(tmp_path, example):
    reg = Registry()
    reg.register(FinanceClaimType())
    case = run_case({"claim_type": "quote.finance.v1", "schema_version": 1,
                     "params": _params(example["form"]), "outcomes": example["stated"],
                     "assumptions": {}}, registry=reg, examiner=InProcessExaminer(reg),
                    workdir=tmp_path, clock=lambda: "2026-11-20T00:00:00Z",
                    vault_key=bytes(32), network=False)
    assert case.verdict.headline.value == example["expect"]
    if example["id"] == "padded":
        statuses = {f.finding_id: f.status for f in case.verdict.findings}
        assert statuses["taxable_base"] is Status.CONSISTENT
        assert statuses["amount_financed"] is Status.CONTRADICTED
        assert case.diagnostics["firstBrokenLine"] == "amount_financed"
        unexplained = Decimal(case.diagnostics["paymentPacking"]["unexplainedAmount"])
        bound = Decimal(case.diagnostics["paymentPacking"]["inversionUncertainty"])
        assert abs(unexplained - Decimal("400.00")) <= bound + Decimal("0.01")
