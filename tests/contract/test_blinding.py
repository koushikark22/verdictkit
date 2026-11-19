"""P2 blinding invariance, P3 outcome absence, P5 spec-hash sensitivity.
Core requirements 1.4–1.6, 2.1–2.4."""
from decimal import Decimal

from hypothesis import assume, given
from hypothesis import strategies as st

from contract.receipt_claimtype import ReceiptClaimType, raw_claim
from verdictkit.custody.intake import blind, freeze
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.examiner.protocol import encode_task
from verdictkit.plugin import Registry

money = st.integers(1, 99_999_99).map(lambda c: format(Decimal(c).scaleb(-2), "f"))
items_st = st.lists(money, min_size=1, max_size=6)
# Outcome sentinels are 12+ characters and cannot occur inside the short item strings.
sentinel = st.integers(10**9, 10**10 - 1).map(lambda i: f"{i}.37")

CT = ReceiptClaimType()


def _registry():
    r = Registry()
    r.register(CT)
    return r


@given(items_st, sentinel, sentinel)
def test_task_bytes_independent_of_outcomes(items, out_a, out_b):
    """P2: claims differing only in outcomes give identical spec hashes and task bytes."""
    fa = freeze(CT, raw_claim(items, out_a)).frozen
    fb = freeze(CT, raw_claim(items, out_b)).frozen
    assert fa.spec_hash == fb.spec_hash
    ta = encode_task(blind(fa, case_id="case-1"))
    tb = encode_task(blind(fb, case_id="case-1"))
    assert ta == tb


@given(items_st, sentinel, sentinel)
def test_examination_independent_of_outcomes(items, out_a, out_b):
    """P2: the examiner result is identical regardless of outcomes."""
    ex = InProcessExaminer(_registry())
    ra = ex.examine(blind(freeze(CT, raw_claim(items, out_a)).frozen, case_id="c"))
    rb = ex.examine(blind(freeze(CT, raw_claim(items, out_b)).frozen, case_id="c"))
    assert ra == rb


@given(items_st, sentinel)
def test_outcome_never_in_task_bytes(items, out):
    """P3: the claimed outcome value never appears in what the Examiner receives."""
    task_bytes = encode_task(blind(freeze(CT, raw_claim(items, out)).frozen, case_id="c"))
    assert out.encode() not in task_bytes
    assert b"stated_total" not in task_bytes


@given(items_st, items_st, sentinel)
def test_spec_hash_changes_with_params(items_a, items_b, out):
    """P5: different params -> different spec_hash."""
    assume(items_a != items_b)
    ha = freeze(CT, raw_claim(items_a, out)).frozen.spec_hash
    hb = freeze(CT, raw_claim(items_b, out)).frozen.spec_hash
    assert ha != hb


@given(items_st, sentinel)
def test_spec_hash_changes_with_assumptions(items, out):
    """P5: a declared assumption set changes spec_hash."""
    h0 = freeze(CT, raw_claim(items, out)).frozen.spec_hash
    h1 = freeze(CT, raw_claim(items, out, tip_set=["0", "15"])).frozen.spec_hash
    assert h0 != h1


@given(items_st, sentinel)
def test_intake_keeps_outcomes_custodian_side(items, out):
    res = freeze(CT, raw_claim(items, out))
    assert res.outcomes == {"stated_total": out}
    assert "stated_total" not in res.frozen.params
