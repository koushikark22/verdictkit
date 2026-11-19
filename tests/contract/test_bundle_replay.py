"""P10 replay determinism, end-to-end custody order, diagnostics inertness.
Core requirements 3, 6.4, 8, 9, 10.4."""
from pathlib import Path

from contract.receipt_claimtype import ReceiptClaimType, raw_claim
from verdictkit.bundle import ReplayStatus, replay_bundle, write_bundle
from verdictkit.custody.ledger import EntryKind as K
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import IsolationMode, Status, compute_verdict_hash
from verdictkit.pipeline import run_case
from verdictkit.plugin import Registry, examination_payload

KEY = bytes(range(32))


def clock():
    return "2026-11-22T12:00:00Z"


def registry():
    r = Registry()
    r.register(ReceiptClaimType())
    return r


def run(tmp: Path, stated: str, tips=None, case_id="case-0001"):
    reg = registry()
    return run_case(
        raw_claim(["10.00", "5.50"], stated, tips),
        registry=reg, examiner=InProcessExaminer(reg), workdir=tmp,
        clock=clock, case_id=case_id, vault_key=KEY, network=False,
    )


def test_custody_order_in_ledger(tmp_path):
    case = run(tmp_path, "15.50")
    kinds = [e.kind for e in case.ledger.entries]
    assert kinds.index(K.EXAMINATION_COMMITTED) < kinds.index(K.OUTCOMES_REVEALED)
    assert kinds.index(K.OUTCOMES_REVEALED) < kinds.index(K.VERDICT_SEALED)
    assert case.ledger.verify().ok
    assert case.isolation is IsolationMode.UNENFORCED  # in-process dev examiner


def test_statuses_end_to_end(tmp_path):
    assert run(tmp_path / "a", "15.50").verdict.headline is Status.CONSISTENT
    assert run(tmp_path / "b", "99.99").verdict.headline is Status.CONTRADICTED
    # 15.50 matches tip 0 but not tip 10 -> CONDITIONAL with a counterexample
    v = run(tmp_path / "c", "15.50", tips=["0", "10"]).verdict
    assert v.headline is Status.CONDITIONAL and v.findings[0].counterexamples


def test_bundle_bytes_deterministic(tmp_path):
    """P10: same case + fixed clock -> byte-identical bundles."""
    case = run(tmp_path / "w", "15.50")
    a = write_bundle(case, tmp_path / "a.vkb", clock=clock)
    b = write_bundle(case, tmp_path / "b.vkb", clock=clock)
    assert a.read_bytes() == b.read_bytes()


def test_replay_reproduces_offline(tmp_path):
    """P10 / Req 9.4: replay in the same environment reports REPRODUCED."""
    case = run(tmp_path / "w", "99.99")
    path = write_bundle(case, tmp_path / "x.vkb", clock=clock)
    rep = replay_bundle(path, registry=registry(), workdir=tmp_path / "replay")
    assert rep.status is ReplayStatus.REPRODUCED
    assert rep.ledger_ok and rep.commitment_ok
    assert rep.replayed_verdict_hash == rep.original_verdict_hash == case.verdict.verdict_hash


def test_verdict_hash_stable_across_runs_despite_random_salt(tmp_path):
    """B5: salts and timestamps differ between runs; verdict_hash does not."""
    a = run(tmp_path / "a", "99.99", case_id="case-a")
    b = run(tmp_path / "b", "99.99", case_id="case-b")
    assert a.salt != b.salt
    assert a.verdict.verdict_hash == b.verdict.verdict_hash


def test_diagnostics_are_inert(tmp_path):
    """Req 10.4 / P12 / P17c: diagnostics exist but are not inputs to verdict_hash."""
    case = run(tmp_path, "99.99")
    assert case.diagnostics is not None
    recomputed = compute_verdict_hash(
        spec_hash=case.frozen.spec_hash,
        evidence_hashes=[e.sha256 for e in case.evidence],
        examination=examination_payload(case.examination),
        outcomes=case.outcomes,
        findings=case.verdict.findings,
    )
    assert recomputed == case.verdict.verdict_hash
