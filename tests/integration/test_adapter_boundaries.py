"""Minimal adapter contract checks. Do not weaken existing core tests."""
from decimal import Decimal

from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType
from reel_autopsy.claim_type import ReelClaimType
from verdictkit.custody.intake import freeze, blind
from verdictkit.model import Basis, Status
from verdictkit.plugin import Registry


def _finance_params():
    return {
        "selling_price": "20000", "addons": [], "doc_fee": "0", "doc_fee_taxable": False,
        "gov_fees": [], "rebates": [], "trade_allowance": "0", "trade_payoff": "0",
        "trade_tax_credit": False, "cash_down": "0", "stated_tax_rate_pct": "0",
        "apr_pct": "0", "term_months": 20, "jurisdiction": {"state": "TX"},
    }


def _task(plugin, params, outcomes):
    claim = freeze(plugin, {"claim_type": plugin.type_id, "schema_version": 1,
                            "params": params, "outcomes": outcomes, "assumptions": {}})
    return claim.frozen, blind(claim.frozen, case_id="case1")


def test_registry_protocol():
    registry = Registry()
    for plugin in (FinanceClaimType(), LeaseClaimType(), ReelClaimType()):
        registry.register(plugin)
    assert registry.type_ids() == ("quote.finance.v1", "quote.lease.v1", "reel.mechanical.v1")


def test_finance_blind_prediction_and_comparison():
    plugin = FinanceClaimType()
    frozen, task = _task(plugin, _finance_params(), {"monthly_payment": "1000.00"})
    assert not hasattr(task, "outcomes")
    exam = plugin.examine(task, None, [{}])
    assert exam.points[0].values["monthly_payment"] == "1000.00"
    finding, = plugin.findings(frozen, exam, {"monthly_payment": "1000.00"}, [])
    assert finding.status is Status.CONSISTENT
    bad, = plugin.findings(frozen, exam, {"monthly_payment": "999.00"}, [])
    assert bad.status is Status.CONTRADICTED and bad.counterexamples


def test_lease_blind_prediction():
    plugin = LeaseClaimType()
    params = {"adjusted_cap_cost": "24000", "residual_value": "12000", "money_factor": "0",
              "tax_rate_pct": "0", "term_months": 24, "rounding_convention": "COMPONENT"}
    frozen, task = _task(plugin, params, {"total_monthly_payment": "500.00"})
    exam = plugin.examine(task, None, [{}])
    assert exam.points[0].values["total_monthly_payment"] == "500.00"
    f, = plugin.findings(frozen, exam, {"total_monthly_payment": "500.00"}, [])
    assert f.status is Status.CONSISTENT


def test_external_quote_claim_fails_closed():
    plugin = FinanceClaimType()
    frozen, task = _task(plugin, _finance_params(), {"tax_rate": "8.25"})
    exam = plugin.examine(task, None, [{}])
    f, = plugin.findings(frozen, exam, {"tax_rate": "8.25"}, [])
    assert f.status is Status.INDETERMINATE and f.basis is Basis.EXTERNAL_EVIDENCE


def test_reel_does_not_claim_unverified_returns():
    plugin = ReelClaimType()
    params = {"instrument": "BTC", "timeframe": "1d", "start": "2025-01-01", "end": "2025-02-01",
              "template": "SMA_CROSS", "template_params": {"fast": 2, "slow": 3},
              "instrument_mode": "SPOT_LONG_FLAT"}
    frozen, task = _task(plugin, params, {"total_return_pct": "340"})
    assert not hasattr(task, "outcomes")
    exam = plugin.examine(task, None, [{}])
    assert "total_return_pct" not in exam.points[0].values
    f, = plugin.findings(frozen, exam, {"total_return_pct": "340"}, [])
    assert f.status is Status.INDETERMINATE
