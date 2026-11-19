"""P4 commitment binding. Core requirements 3.1, 3.3."""
import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from verdictkit.custody.commitment import ALG, commit, new_salt, verify

outcomes_st = st.dictionaries(
    st.sampled_from(["a", "b", "stated_total"]),
    st.integers(0, 10**6).map(str),
    min_size=1,
)
salt_st = st.binary(min_size=32, max_size=32)


@given(outcomes_st, salt_st)
def test_verify_accepts_original(o, s):
    c = commit(o, s)
    assert c.alg == ALG and len(c.digest) == 64
    assert verify(c, o, s)


@given(outcomes_st, outcomes_st, salt_st)
def test_verify_rejects_other_outcomes(o1, o2, s):
    assume(o1 != o2)
    assert not verify(commit(o1, s), o2, s)


@given(outcomes_st, salt_st, salt_st)
def test_verify_rejects_other_salt(o, s1, s2):
    assume(s1 != s2)
    assert not verify(commit(o, s1), o, s2)


@pytest.mark.parametrize("n", [0, 16, 31, 33])
def test_salt_length_enforced(n):
    with pytest.raises(ValueError):
        commit({"a": "1"}, b"\x00" * n)


def test_new_salt_is_32_random_bytes():
    a, b = new_salt(), new_salt()
    assert len(a) == 32 and len(b) == 32 and a != b
