"""P1 Canonical determinism. Core requirements 1.2, 1.3."""
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from verdictkit.canonical import (
    CanonicalizationError,
    canonical_bytes,
    parse_canonical,
    sha256_hex,
)

json_scalars = st.none() | st.booleans() | st.integers(-(10**18), 10**18) | st.text(max_size=12)
json_values = st.recursive(
    json_scalars,
    lambda c: st.lists(c, max_size=4) | st.dictionaries(st.text(max_size=6), c, max_size=4),
    max_leaves=24,
)


@given(json_values)
def test_roundtrip(value):
    """P1: parse_canonical(canonical_bytes(x)) == x for JSON-safe values without Decimals."""
    assert parse_canonical(canonical_bytes(value)) == value


@given(st.dictionaries(st.text(max_size=6), json_scalars, min_size=1, max_size=8))
def test_key_order_independent(d):
    """P1: dict insertion order never changes the bytes."""
    reversed_d = dict(reversed(list(d.items())))
    assert canonical_bytes(d) == canonical_bytes(reversed_d)


@given(json_values)
def test_matches_reference_serialisation(value):
    """P1: for Decimal-free values the canonical form equals the reference json.dumps form."""
    import json

    ref = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert canonical_bytes(value) == ref.encode("utf-8")


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_floats_rejected_anywhere(f):
    """Req 1.2: floats are never accepted, even nested."""
    for obj in (f, [f], {"a": f}, {"a": [1, {"b": f}]}):
        with pytest.raises(CanonicalizationError):
            canonical_bytes(obj)


@pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_non_finite_decimal_rejected(bad):
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"x": bad})


def test_non_string_keys_rejected():
    with pytest.raises(CanonicalizationError):
        canonical_bytes({1: "a"})


def test_decimal_is_string_fixed_point_preserving_precision():
    assert canonical_bytes({"a": Decimal("1.50")}) == canonical_bytes({"a": "1.50"})
    assert canonical_bytes(Decimal("1E+2")) == canonical_bytes("100")
    assert canonical_bytes(Decimal("340")) != canonical_bytes(Decimal("340.0"))


def test_exact_bytes_example():
    assert canonical_bytes({"b": 1, "a": [True, None, "x"]}) == b'{"a":[true,null,"x"],"b":1}'


@pytest.mark.parametrize(
    "data",
    [
        b'{"a":1,"a":2}',  # duplicate key
        b'{"a":1.5}',  # non-integer number
        b'{"a":NaN}',
        b' {"a":1}',  # not canonical (whitespace)
        b'{"b":1,"a":2}',  # not canonical (key order)
    ],
)
def test_parse_rejects_non_canonical(data):
    with pytest.raises(CanonicalizationError):
        parse_canonical(data)


@given(st.binary(max_size=64))
def test_sha256_hex_format(b):
    h = sha256_hex(b)
    assert len(h) == 64 and h == h.lower() and int(h, 16) >= 0
