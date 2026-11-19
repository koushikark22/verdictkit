"""P8 fail-closed policy, P9 evidence integrity. Core requirement 5."""
import hashlib

import pytest
from hypothesis import given
from hypothesis import strategies as st

from verdictkit.evidence.policy import apply_policy, check
from verdictkit.evidence.store import EvidenceIntegrityError, EvidenceMeta, EvidenceStore
from verdictkit.model import (
    Basis,
    Counterexample,
    EvidenceItem,
    Finding,
    LicenseClass,
    SourceClass,
    Status,
)
from verdictkit.plugin import EvidencePolicySpec

SOURCES = ["src_a", "src_b", "src_c"]
PASSING = {Status.SUPPORTED, Status.CONSISTENT, Status.WITHIN_BOUND}


def item(source_id, source_class, sha):
    return EvidenceItem(
        source_id=source_id, source_class=source_class, uri=f"https://example.invalid/{sha[:6]}",
        retrieved_at="2026-11-20T00:00:00Z", sha256=sha, media_type="text/csv",
        license_class=LicenseClass.REFETCH_ONLY,
    )


@given(
    st.sampled_from(SOURCES),
    st.sampled_from(list(SourceClass)),
    st.frozensets(st.sampled_from(SOURCES)),
    st.sampled_from([Status.SUPPORTED, Status.REFUTED, Status.CONDITIONAL]),
)
def test_policy_fails_closed(source_id, source_class, permitted, status):
    """P8: forbidden or unpermitted evidence can never yield a passing finding."""
    sha = hashlib.sha256(source_id.encode()).hexdigest()
    ev = item(source_id, source_class, sha)
    policy = EvidencePolicySpec(permitted_sources=permitted)
    cex = (Counterexample(point={}, expected="1", observed="2", difference="1", tolerance="0"),)
    f = Finding("f", Basis.EXTERNAL_EVIDENCE, status, "s", evidence_used=(sha,),
                counterexamples=cex if status is not Status.SUPPORTED else ())
    out = apply_policy(f, {sha: ev}, policy)
    allowed = source_id in permitted and source_class is not SourceClass.CLAIMANT
    assert check(ev, policy).allowed == allowed
    if allowed:
        assert out == f
    else:
        assert out.status is Status.INDETERMINATE and out.reason == "policy_violation"
        assert out.basis is f.basis


def test_unknown_evidence_hash_is_indeterminate():
    f = Finding("f", Basis.EXTERNAL_EVIDENCE, Status.SUPPORTED, "s", evidence_used=("ab" * 32,))
    out = apply_policy(f, {}, EvidencePolicySpec(permitted_sources=frozenset(SOURCES)))
    assert out.status is Status.INDETERMINATE and out.status not in PASSING


META = EvidenceMeta("src_a", SourceClass.EXCHANGE_PUBLIC_DATA, "https://example.invalid/x",
                    "2026-11-20T00:00:00Z", "text/csv", LicenseClass.REDISTRIBUTABLE)


@given(st.binary(min_size=1, max_size=256))
def test_store_roundtrip_content_addressed(tmp_path_factory, data):
    store = EvidenceStore(tmp_path_factory.mktemp("ev"))
    it = store.put(data, META)
    assert it.sha256 == hashlib.sha256(data).hexdigest()
    assert store.get(it.sha256) == data


@given(st.binary(min_size=1, max_size=256), st.data())
def test_store_detects_any_byte_flip(tmp_path_factory, data, d):
    """P9: any modification of a stored blob raises on read."""
    store = EvidenceStore(tmp_path_factory.mktemp("ev"))
    it = store.put(data, META)
    path = store.blob_path(it.sha256)
    raw = bytearray(path.read_bytes())
    i = d.draw(st.integers(0, len(raw) - 1))
    raw[i] ^= 0xFF
    path.write_bytes(bytes(raw))
    with pytest.raises(EvidenceIntegrityError):
        store.get(it.sha256)
