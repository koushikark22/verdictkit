"""Canonical JSON and hashing. Requirements: core 1.2, 1.3. Property: P1.

Canonical form:
* UTF-8, object keys sorted by Unicode code point, separators ``,`` and ``:``, no spaces.
* Allowed values: None, bool, int, str, Decimal (finite), list/tuple, dict with str keys.
* Decimal is emitted as a JSON *string* using ``format(d, "f")`` (no exponent; trailing
  zeros preserved because they carry the claimant's stated precision).
* Enums with a ``str`` value are emitted as that string.
* Strings are escaped exactly as ``json.dumps(..., ensure_ascii=False)`` does; for
  Decimal-free input the output equals
  ``json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()``.
* Floats, NaN, Infinity, non-str keys and duplicate keys are rejected.
"""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from enum import Enum


class CanonicalizationError(ValueError):
    """Raised with a JSON-pointer-like ``path`` attribute describing the offending value."""

    def __init__(self, message: str, path: str = "") -> None:
        super().__init__(f"{message} at {path or '/'}")
        self.path = path


def _build(obj: object, path: str) -> object:
    """Recursively validate and transform obj into a JSON-serialisable object.

    Returns an object where Decimals have been replaced by their fixed-point string
    representation and enum values by their string value.
    """
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        raise CanonicalizationError("float values are not allowed", path)
    if isinstance(obj, Decimal):
        if not obj.is_finite():
            raise CanonicalizationError("non-finite Decimal is not allowed", path)
        return format(obj, "f")
    if isinstance(obj, str):
        return obj
    if isinstance(obj, Enum):
        if isinstance(obj.value, str):
            return obj.value
        raise CanonicalizationError(f"enum with non-str value {obj!r}", path)
    if isinstance(obj, (list, tuple)):
        return [_build(v, f"{path}/{i}") for i, v in enumerate(obj)]
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonicalizationError(f"non-string key {k!r}", path)
            result[k] = _build(v, f"{path}/{k}")
        return result
    raise CanonicalizationError(f"unsupported type {type(obj).__name__}", path)


def canonical_bytes(obj: object) -> bytes:
    """Serialise ``obj`` to canonical JSON bytes or raise CanonicalizationError."""
    transformed = _build(obj, "")
    return json.dumps(
        transformed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def parse_canonical(data: bytes) -> object:
    """Parse canonical bytes strictly.

    Raises CanonicalizationError if the input contains a non-integer number, a duplicate
    key, or is not byte-identical to ``canonical_bytes`` of its own parse (i.e. it was not
    canonical). Decimal values come back as ``str``.
    """
    # First pass: use a custom decoder that rejects floats and duplicate keys.
    try:
        decoder = json.JSONDecoder(object_pairs_hook=_check_pairs)
        obj, idx = decoder.raw_decode(data.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise CanonicalizationError(str(exc)) from exc

    # Reject any non-integer number found in the raw bytes: JSON floats contain "."
    # or "e"/"E" outside strings.  We detect this by checking that the raw json.loads
    # output from the standard parser finds no floats in the structure.
    _reject_floats(obj, "")

    # Second pass: re-encode and check identity (catches key ordering, whitespace, etc.).
    reencoded = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    if reencoded != data:
        raise CanonicalizationError("not in canonical form")

    return obj


def _check_pairs(pairs: list[tuple[str, object]]) -> dict:
    """object_pairs_hook that raises on duplicate keys."""
    seen: set[str] = set()
    result: dict = {}
    for k, v in pairs:
        if k in seen:
            raise CanonicalizationError(f"duplicate key {k!r}")
        seen.add(k)
        result[k] = v
    return result


def _reject_floats(obj: object, path: str) -> None:
    """Raise CanonicalizationError if obj (from json.loads) contains any float."""
    if isinstance(obj, float):
        raise CanonicalizationError("non-integer number in canonical data", path)
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            _reject_floats(v, f"{path}/{i}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _reject_floats(v, f"{path}/{k}")


def sha256_hex(data: bytes) -> str:
    """Lowercase hex SHA-256 of ``data``."""
    return hashlib.sha256(data).hexdigest()
