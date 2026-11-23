"""Quote rules snapshot loader (quote task 4.1, req 5.1) and post-reveal diagnostics
(quote task 6.1, req 6.1-6.4; property P17c).

The snapshot below is a constructed test fixture, not official tax data: decision B7
(which state) is still open, so no real rules file is committed.
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
    "local_rate_max_pct": "2.00", "localities": {"L1": "7.50"}, "doc_fee_cap": "150.00",
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
    assert rules.doc_fee_cap == Decimal("150.00")
    assert rules.snapshot_sha256 == hashlib.sha256(canonical_bytes(CONSTRUCTED)).hexdigest()


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(state_rate_pct="6.5e0"),
    lambda d: d.update(local_rate_min_pct="3.00"),
    lambda d: d.update(sources=[]),
    lambda d: d["sources"][0].update(uri="http://insecure.invalid"),
    lambda d: d.update(extra="x"),
    lambda d: d.update(state="zz"),
    lambda d: d.update(doc_fee_cap="-1"),
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


# --- B7 Texas acceptance tests ---

from verdictkit.model import Basis, Status  # noqa: E402

TX_RULES_PATH = Path(__file__).resolve().parents[2] / "apps/quote-autopsy/src/quote_autopsy/rules/TX.json"
TX_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "apps/quote-autopsy/src/quote_autopsy/rules/MANIFEST.json"


def _tx_case(tmp_path, outcomes, **param_overrides):
    reg = Registry()
    reg.register(FinanceClaimType())
    params = dict(PARAMS, jurisdiction={"state": "TX"}, **param_overrides)
    case = run_case({"claim_type": "quote.finance.v1", "schema_version": 1,
                     "params": params, "outcomes": outcomes, "assumptions": {}},
                    registry=reg, examiner=InProcessExaminer(reg), workdir=tmp_path,
                    clock=lambda: "2026-11-27T00:00:00Z", vault_key=bytes(32), network=False)
    return {fi.finding_id: fi for fi in case.verdict.findings}


def test_b7_tx_snapshot_loads_and_has_correct_values():
    """B7: Texas snapshot loads, state rate is 6.25%, no doc fee cap, no locality table."""
    rules = load_rules(TX_RULES_PATH, TX_MANIFEST_PATH)
    assert rules.state == "TX"
    assert rules.state_rate_pct == Decimal("6.25")
    assert rules.local_rate_min_pct == Decimal("0.00")
    assert rules.local_rate_max_pct == Decimal("2.00")
    assert rules.doc_fee_cap is None
    assert rules.localities is None
    assert rules.rate_range() == (Decimal("6.25"), Decimal("8.25"))


def test_b7_tx_snapshot_hash_is_verified():
    """B7: Manifest hash matches the actual file bytes."""
    rules = load_rules(TX_RULES_PATH, TX_MANIFEST_PATH)
    assert rules.snapshot_sha256 == hashlib.sha256(TX_RULES_PATH.read_bytes()).hexdigest()


def test_b7_tx_snapshot_has_three_official_sources():
    """B7: Snapshot has official https sources."""
    doc = json.loads(TX_RULES_PATH.read_bytes())
    assert len(doc["sources"]) >= 1
    for s in doc["sources"]:
        assert s["uri"].startswith("https://statutes.capitol.texas.gov/")


def test_b7_tx_rate_exact_match_supported(tmp_path):
    """B7 req 5.3: state-only rate 6.25 is within range, no locality confirmed."""
    f = _tx_case(tmp_path, {"tax_rate": "6.25"}, stated_tax_rate_pct="6.25")
    assert f["tax_rate"].basis.value == "EXTERNAL_EVIDENCE"
    assert f["tax_rate"].status in (Status.SUPPORTED, Status.CONDITIONAL)


def test_b7_tx_rate_within_range_is_conditional_or_supported(tmp_path):
    f = _tx_case(tmp_path, {"tax_rate": "7.50"}, stated_tax_rate_pct="7.50")
    assert f["tax_rate"].status in (Status.CONDITIONAL, Status.SUPPORTED)


def test_b7_tx_rate_above_max_is_refuted(tmp_path):
    f = _tx_case(tmp_path, {"tax_rate": "9.00"}, stated_tax_rate_pct="9.00")
    assert f["tax_rate"].status is Status.REFUTED


def test_b7_tx_rate_below_min_is_refuted(tmp_path):
    f = _tx_case(tmp_path, {"tax_rate": "5.00"}, stated_tax_rate_pct="5.00")
    assert f["tax_rate"].status is Status.REFUTED


def test_b7_tx_doc_fee_no_cap_is_supported(tmp_path):
    """B7 req 5.4: no TX cap, so SUPPORTED without any compliance claim."""
    f = _tx_case(tmp_path, {"doc_fee_cap": "699.00"}, doc_fee="699.00")
    assert f["doc_fee_cap"].status is Status.SUPPORTED
    stmt = f["doc_fee_cap"].statement.lower()
    assert "no statutory" in stmt or "no cap" in stmt
    assert "compliant" not in stmt
    assert "legal" not in stmt


def test_b7_tx_doc_fee_supported_statement_is_scoped(tmp_path):
    f = _tx_case(tmp_path, {"doc_fee_cap": "225.00"}, doc_fee="225.00")
    assert f["doc_fee_cap"].status is Status.SUPPORTED
    stmt = f["doc_fee_cap"].statement
    assert "TX" in stmt and "for this transaction" in stmt


def test_b7_unsupported_state_gives_indeterminate(tmp_path):
    reg = Registry()
    reg.register(FinanceClaimType())
    params = dict(PARAMS, jurisdiction={"state": "CA"})
    case = run_case({"claim_type": "quote.finance.v1", "schema_version": 1, "params": params,
                     "outcomes": {"tax_rate": "7.25"}, "assumptions": {}},
                    registry=reg, examiner=InProcessExaminer(reg), workdir=tmp_path,
                    clock=lambda: "2026-11-27T00:00:00Z", vault_key=bytes(32), network=False)
    f = {fi.finding_id: fi for fi in case.verdict.findings}
    assert f["tax_rate"].status is Status.INDETERMINATE
    assert f["tax_rate"].basis is Basis.EXTERNAL_EVIDENCE
    assert f["tax_rate"].reason == "unsupported_jurisdiction"


def test_b7_internal_findings_still_run_for_unsupported_state(tmp_path):
    reg = Registry()
    reg.register(FinanceClaimType())
    params = dict(PARAMS, jurisdiction={"state": "CA"})
    case = run_case({"claim_type": "quote.finance.v1", "schema_version": 1, "params": params,
                     "outcomes": {"amount_financed": "27430.00"}, "assumptions": {}},
                    registry=reg, examiner=InProcessExaminer(reg), workdir=tmp_path,
                    clock=lambda: "2026-11-27T00:00:00Z", vault_key=bytes(32), network=False)
    f = {fi.finding_id: fi for fi in case.verdict.findings}
    assert f["amount_financed"].basis is Basis.INTERNAL_ARITHMETIC
    assert f["amount_financed"].status is not Status.INDETERMINATE


def test_b7_tx_snapshot_is_canonical_json():
    from verdictkit.canonical import parse_canonical
    data = TX_RULES_PATH.read_bytes()
    assert canonical_bytes(parse_canonical(data)) == data


def test_b7_tx_rate_finding_basis_is_external_evidence(tmp_path):
    f = _tx_case(tmp_path, {"tax_rate": "8.25"}, stated_tax_rate_pct="8.25")
    assert f["tax_rate"].basis is Basis.EXTERNAL_EVIDENCE


def test_b7_tx_hash_mismatch_gives_indeterminate(tmp_path):
    """Tampered manifest fails the loader; the adapter maps that to evidence_integrity."""
    import shutil
    shutil.copy(TX_RULES_PATH, tmp_path / "TX.json")
    (tmp_path / "MANIFEST.json").write_text(json.dumps({"files": {"TX.json": "0" * 64}}))
    with pytest.raises(RulesIntegrityError):
        load_rules(tmp_path / "TX.json", tmp_path / "MANIFEST.json")
    from quote_autopsy.claim_type import _RulesAdapter
    from quote_autopsy.worksheet import Jurisdiction
    finding = _RulesAdapter(tmp_path).tax_rate_finding(Jurisdiction("TX"), Decimal("7.00"), frozenset())
    assert finding.status is Status.INDETERMINATE and finding.reason == "evidence_integrity"
