"""Quote rules snapshot loader (quote task 4.1, req 5.1) and post-reveal diagnostics
(quote task 6.1, req 6.1-6.4; property P17c).

The snapshot below is a constructed test fixture, not official tax data. The packaged
official Texas snapshot (decision B7) is covered by its own acceptance tests.
"""
from __future__ import annotations

import copy
import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

from quote_autopsy.claim_type import FinanceClaimType, _finance_worksheet
from quote_autopsy.diagnostics import (
    LABEL, finance_diagnostics, local_checks, payment_packing,
)
from quote_autopsy.finance import chain
from quote_autopsy.rules import RulesIntegrityError, load_rules
from verdictkit.canonical import canonical_bytes
from verdictkit.custody.ledger import EntryKind, Ledger, LedgerOrderError
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.pipeline import run_case
from verdictkit.plugin import Registry

CONSTRUCTED = {
    "state": "ZZ", "state_rate_pct": "6.00", "local_rate_min_pct": "0.00",
    "local_rate_max_pct": "2.00", "localities": {"L1": "7.50"},
    "doc_fee": {"kind": "STATUTORY_MAXIMUM", "amount": "150.00",
                "applies_to": "RETAIL_INSTALLMENT_CONTRACT"},
    "sources": [{"uri": "https://example.invalid/constructed-test-fixture",
                 "retrieved_at": "2026-11-19", "sha256_of_source": "0" * 64}],
}


def _write(tmp_path: Path, doc: dict, *, manifest_hash: str | None = None) -> tuple[Path, Path]:
    data = canonical_bytes(doc)
    snap = tmp_path / "ZZ.json"
    snap.write_bytes(data)
    man = tmp_path / "MANIFEST.json"
    man.write_text(json.dumps({"files": {"ZZ.json": manifest_hash or hashlib.sha256(data).hexdigest()}}))
    return snap, man


def test_loader_verifies_hash_and_exposes_rates(tmp_path):
    rules = load_rules(*_write(tmp_path, CONSTRUCTED))
    assert rules.state == "ZZ"
    assert rules.combined_rate("L1") == Decimal("7.50")
    assert rules.combined_rate("unknown") is None
    assert rules.rate_range() == (Decimal("6.00"), Decimal("8.00"))
    assert rules.doc_fee_kind == "STATUTORY_MAXIMUM"
    assert rules.doc_fee_amount == Decimal("150.00")
    assert rules.snapshot_sha256 == hashlib.sha256(canonical_bytes(CONSTRUCTED)).hexdigest()


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(state_rate_pct="6.5e0"),
    lambda d: d.update(local_rate_min_pct="3.00"),
    lambda d: d.update(sources=[]),
    lambda d: d["sources"][0].update(uri="http://insecure.invalid"),
    lambda d: d.update(extra="x"),
    lambda d: d.update(state="zz"),
    lambda d: d["doc_fee"].update(amount="-1"),
])
def test_loader_rejects_malformed_snapshots(tmp_path, mutate):
    doc = copy.deepcopy(CONSTRUCTED)
    mutate(doc)
    with pytest.raises(RulesIntegrityError):
        load_rules(*_write(tmp_path, doc))


def test_loader_rejects_hash_mismatch_and_noncanonical(tmp_path):
    snap, man = _write(tmp_path, CONSTRUCTED, manifest_hash="1" * 64)
    with pytest.raises(RulesIntegrityError, match="hash"):
        load_rules(snap, man)
    snap.write_bytes(json.dumps(CONSTRUCTED, indent=2).encode())
    man.write_text(json.dumps({"files": {"ZZ.json": hashlib.sha256(snap.read_bytes()).hexdigest()}}))
    with pytest.raises(RulesIntegrityError, match="canonical"):
        load_rules(snap, man)
    with pytest.raises(RulesIntegrityError):
        load_rules(tmp_path / "missing.json", man)


PARAMS = {
    "selling_price": "30000.00", "addons": [], "doc_fee": "500.00", "doc_fee_taxable": True,
    "gov_fees": [], "rebates": [], "trade_allowance": "0.00", "trade_payoff": "0.00",
    "trade_tax_credit": True, "cash_down": "5000.00", "stated_tax_rate_pct": "6.00",
    "apr_pct": "6.00", "term_months": 60, "jurisdiction": {"state": "TX"},
}


def test_local_checks_localise_first_broken_line():
    ws = _finance_worksheet(PARAMS)
    c = chain(ws)
    # The dealer overstated the amount financed by $300 and computed later lines from it.
    af = c.amount_financed + Decimal("300.00")
    from quote_autopsy.finance import monthly_payment
    pay = monthly_payment(af, ws.apr_pct, ws.term_months)
    stated = {"sales_tax": c.sales_tax, "amount_financed": af, "monthly_payment": pay,
              "total_of_payments": pay * 60}
    checks = {k.line: k for k in local_checks(ws, stated)}
    assert checks["sales_tax"].consistent
    assert not checks["amount_financed"].consistent
    assert checks["amount_financed"].difference == Decimal("300.00")
    assert checks["monthly_payment"].consistent  # consistent with the stated (wrong) AF
    assert checks["total_of_payments"].consistent
    diag = finance_diagnostics(ws, stated)
    assert diag["label"] == LABEL
    assert diag["firstBrokenLine"] == "amount_financed"
    packed = payment_packing(ws, stated)
    assert abs(packed.unexplained_amount - Decimal("300.00")) <= packed.inversion_uncertainty + Decimal("0.01")


def test_packing_absent_without_payment():
    ws = _finance_worksheet(PARAMS)
    assert payment_packing(ws, {"sales_tax": Decimal("1830.00")}) is None


@settings(max_examples=100, deadline=None)
@given(principal=st.integers(100, 20_000_000), apr_milli=st.integers(0, 30_000),
       n=st.integers(1, 96))
def test_p16b_inversion_bound(principal, apr_milli, n):
    """P16b (quote req 6.2, 6.4): |implied(payment(P)) - P| <= 0.005*factor + 0.01."""
    from quote_autopsy.finance import annuity_factor, implied_amount_financed, monthly_payment
    p = Decimal(principal) / 100
    apr = Decimal(apr_milli) / 1000
    pay = monthly_payment(p, apr, n)
    implied = implied_amount_financed(pay, apr, n)
    bound = Fraction(Decimal("0.005") * annuity_factor(apr, n)) + Fraction(1, 100)
    assert abs(Fraction(implied) - Fraction(p)) <= bound


def _registry() -> Registry:
    r = Registry()
    r.register(FinanceClaimType())
    return r


class _NoDiagnostics(FinanceClaimType):
    def diagnose(self, frozen, examination, outcomes):
        return None


def test_p17c_diagnostics_are_inert_and_post_seal(tmp_path):
    """P17c (quote req 6.3): verdict_hash is identical with and without diagnostics, and
    diagnostics are recorded only after VERDICT_SEALED."""
    claim = {"claim_type": "quote.finance.v1", "schema_version": 1, "params": PARAMS,
             "outcomes": {"amount_financed": "26000.00", "monthly_payment": "502.00"},
             "assumptions": {}}
    clock = lambda: "2026-11-19T00:00:00Z"  # noqa: E731
    with_diag = run_case(claim, registry=_registry(), examiner=InProcessExaminer(_registry()),
                         workdir=tmp_path / "a", clock=clock, case_id="c" * 32,
                         vault_key=b"v" * 32)
    other = Registry()
    other.register(_NoDiagnostics())
    without = run_case(claim, registry=other, examiner=InProcessExaminer(other),
                       workdir=tmp_path / "b", clock=clock, case_id="c" * 32, vault_key=b"v" * 32)
    assert with_diag.diagnostics is not None and without.diagnostics is None
    assert with_diag.verdict.verdict_hash == without.verdict.verdict_hash
    assert [f.status for f in with_diag.verdict.findings] == [f.status for f in without.verdict.findings]
    kinds = [e.kind for e in with_diag.ledger.entries]
    assert kinds.index(EntryKind.DIAGNOSTICS_APPENDED) == kinds.index(EntryKind.VERDICT_SEALED) + 1
    # The ledger state machine forbids diagnostics before the seal.
    ledger = Ledger(clock)
    for kind in (EntryKind.CASE_OPENED, EntryKind.CLAIM_FROZEN, EntryKind.OUTCOMES_COMMITTED,
                 EntryKind.EVIDENCE_ACQUIRED, EntryKind.EXAMINATION_COMMITTED,
                 EntryKind.OUTCOMES_REVEALED):
        ledger.append(kind, {})
    with pytest.raises(LedgerOrderError):
        ledger.append(EntryKind.DIAGNOSTICS_APPENDED, {})
    assert with_diag.diagnostics["paymentPacking"] is not None
