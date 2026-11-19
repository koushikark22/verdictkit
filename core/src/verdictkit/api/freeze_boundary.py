"""Prepare immutable freeze material using the existing forensic custody engine.

This is a custodian-only adapter. It deliberately does not write the HTTP case
state, publish salt, or expose asserted outcomes to an examiner. Persistence
must atomically store its result before the freeze endpoint can be enabled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from verdictkit.custody.commitment import commit, new_salt
from verdictkit.custody.intake import freeze
from verdictkit.custody.ledger import EntryKind, Ledger
from verdictkit.model import Commitment, FrozenClaim
from verdictkit.plugin import ClaimType


@dataclass(frozen=True, slots=True)
class PreparedFreeze:
    frozen: FrozenClaim
    commitment: Commitment
    ledger_entries: tuple
    salt: bytes = field(repr=False)
    asserted_outcomes: Mapping[str, object] = field(repr=False)

    def public_projection(self) -> dict[str, object]:
        """No salt, claimed outcome value, private claim or plaintext payload."""
        return {
            "specHash": self.frozen.spec_hash,
            "commitment": {
                "alg": self.commitment.alg,
                "digest": self.commitment.digest,
            },
            "ledgerSeq": self.ledger_entries[-1].seq,
        }


def prepare_freeze(
    claim_type: ClaimType,
    raw_claim: Mapping[str, object],
    *,
    case_id: str,
    clock,
) -> PreparedFreeze:
    """Use the canonical existing freeze, domain-separated commitment and ledger.

    Raises on validation/grid/ledger errors before any publication or side effect.
    """
    result = freeze(claim_type, raw_claim)
    salt = new_salt()
    commitment = commit(result.outcomes, salt)
    ledger = Ledger(clock)
    ledger.append(EntryKind.CASE_OPENED, {
        "case_id": case_id,
        "claim_type": result.frozen.claim_type,
    })
    ledger.append(EntryKind.CLAIM_FROZEN, {
        "case_id": case_id,
        "spec_hash": result.frozen.spec_hash,
    })
    ledger.append(EntryKind.OUTCOMES_COMMITTED, {
        "case_id": case_id,
        "alg": commitment.alg,
        "digest": commitment.digest,
    })
    if not ledger.verify().ok:
        raise RuntimeError("custody ledger integrity check failed")
    return PreparedFreeze(
        frozen=result.frozen,
        commitment=commitment,
        ledger_entries=ledger.entries,
        salt=salt,
        asserted_outcomes=dict(result.outcomes),
    )
