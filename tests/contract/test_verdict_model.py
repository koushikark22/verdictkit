"""P12 verdict matrix, headline, verdict hash. Core requirement 6."""
import dataclasses

import pytest
from hypothesis import given
from hypothesis import strategies as st

from verdictkit.model import (
    ALLOWED_STATUSES,
    NEEDS_COUNTEREXAMPLE,
    SEVERITY,
    Basis,
    Counterexample,
    Finding,
    InvalidFindingError,
    Status,
    compute_verdict_hash,
    headline_status,
    validate_finding,
)

CEX = Counterexample(point={}, expected="1.00", observed="2.00", difference="1.00", tolerance="0.00")

# Independent copy of the specification matrix (Req 6.1).
SPEC = {
    Basis.INTERNAL_ARITHMETIC: {Status.CONSISTENT, Status.CONTRADICTED, Status.CONDITIONAL, Status.INDETERMINATE},
    Basis.EXTERNAL_EVIDENCE: {Status.SUPPORTED, Status.REFUTED, Status.CONDITIONAL, Status.INDETERMINATE},
    Basis.MECHANICAL_BOUND: {Status.WITHIN_BOUND, Status.IMPOSSIBLE, Status.INDETERMINATE},
}


def make(basis, status, cex=True, fid="f"):
    return Finding(
        finding_id=fid, basis=basis, status=status, statement="s",
        counterexamples=(CEX,) if cex else (),
    )


def test_spec_constant_matches_requirements():
    assert {b: set(s) for b, s in ALLOWED_STATUSES.items()} == SPEC


@pytest.mark.parametrize("basis", list(Basis))
@pytest.mark.parametrize("status", list(Status))
def test_matrix_enforced(basis, status):
    f = make(basis, status)
    if status in SPEC[basis]:
        assert validate_finding(f) == f
    else:
        with pytest.raises(InvalidFindingError):
            validate_finding(f)


@pytest.mark.parametrize("status", sorted(NEEDS_COUNTEREXAMPLE, key=lambda s: s.value))
def test_counterexample_required(status):
    basis = next(b for b, s in SPEC.items() if status in s)
    with pytest.raises(InvalidFindingError):
        validate_finding(make(basis, status, cex=False))


def test_numbers_must_be_decimal_strings():
    f = dataclasses.replace(make(Basis.INTERNAL_ARITHMETIC, Status.CONSISTENT), numbers={"x": "abc"})
    with pytest.raises(InvalidFindingError):
        validate_finding(f)


valid_pairs = [(b, s) for b, ss in SPEC.items() for s in ss]


@given(st.lists(st.sampled_from(valid_pairs), min_size=1, max_size=8))
def test_headline_is_worst(pairs):
    fs = [make(b, s, fid=f"f{i}") for i, (b, s) in enumerate(pairs)]
    h = headline_status(fs)
    worst = max(SEVERITY[f.status] for f in fs)
    assert SEVERITY[h] == worst
    if worst == 0:
        assert h == fs[0].status


def test_headline_empty_rejected():
    with pytest.raises(ValueError):
        headline_status([])


def _hash(findings, evidence=("aa", "bb")):
    return compute_verdict_hash(
        spec_hash="0" * 64,
        evidence_hashes=list(evidence),
        examination={"x": "1"},
        outcomes={"o": "2"},
        findings=findings,
    )


def test_verdict_hash_deterministic_and_sensitive():
    f1 = [make(Basis.INTERNAL_ARITHMETIC, Status.CONSISTENT)]
    f2 = [make(Basis.INTERNAL_ARITHMETIC, Status.CONTRADICTED)]
    assert _hash(f1) == _hash(f1)
    assert _hash(f1) != _hash(f2)
    assert len(_hash(f1)) == 64


def test_verdict_hash_ignores_evidence_order():
    f = [make(Basis.INTERNAL_ARITHMETIC, Status.CONSISTENT)]
    assert _hash(f, ("aa", "bb")) == _hash(f, ("bb", "aa"))
