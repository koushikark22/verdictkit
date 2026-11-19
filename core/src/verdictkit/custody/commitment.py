"""Outcome commitments. Requirement: core 3. Property: P4.

digest = SHA256(b"vk-commit-v1" || salt || canonical_bytes(outcomes))
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Mapping

from ..canonical import canonical_bytes
from ..model import Commitment

DOMAIN_TAG = b"vk-commit-v1"
SALT_BYTES = 32
ALG = "sha256/vk-commit-v1"


class CommitmentMismatchError(ValueError):
    pass


def new_salt() -> bytes:
    """32 bytes from ``secrets.token_bytes``."""
    return secrets.token_bytes(SALT_BYTES)


def commit(outcomes: Mapping[str, object], salt: bytes) -> Commitment:
    """Raise ValueError if ``len(salt) != 32``."""
    if len(salt) != SALT_BYTES:
        raise ValueError(f"salt must be exactly {SALT_BYTES} bytes, got {len(salt)}")
    digest = hashlib.sha256(DOMAIN_TAG + salt + canonical_bytes(outcomes)).hexdigest()
    return Commitment(alg=ALG, digest=digest)


def verify(commitment: Commitment, outcomes: Mapping[str, object], salt: bytes) -> bool:
    """Constant-time comparison of the recomputed digest."""
    expected = commit(outcomes, salt)
    return hmac.compare_digest(commitment.digest, expected.digest)
