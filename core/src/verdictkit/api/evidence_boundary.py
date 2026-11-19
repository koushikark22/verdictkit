"""Evidence acquisition gate for frozen VerdictKit claims.

Do not mistake an empty plugin request list for independently verified evidence.
Internal quote arithmetic needs no external source; Reel mechanics require
licensed, hash-verified OHLCV evidence and remain blocked without a provider.
"""
from __future__ import annotations

from dataclasses import dataclass

from verdictkit.model import DataMode
from verdictkit.plugin import ClaimType
from verdictkit.evidence.policy import effective_policy

_QUOTE_INTERNAL = frozenset({"quote.finance.v1", "quote.lease.v1"})


@dataclass(frozen=True, slots=True)
class EvidenceGate:
    allowed: bool
    blocker_code: str | None
    reason: str | None
    request_count: int

    def public_blocker(self) -> dict[str, object] | None:
        if self.allowed:
            return None
        return {"code": self.blocker_code, "message": self.reason, "field": None}


def preflight_evidence(claim_type: ClaimType, params: dict,
                       *, data_mode: DataMode) -> EvidenceGate:
    """Reject unsupported acquisition before any network or ledger transition.

    A no-request finance/lease claim may proceed solely for document-internal
    calculations; this does not verify taxes, rules, or market claims.
    """
    policy = effective_policy(claim_type.evidence_policy(), data_mode)
    requests = tuple(claim_type.evidence_requests(params))
    if data_mode is DataMode.SYNTHETIC_DEMO:
        return EvidenceGate(False, "POLICY_VIOLATION",
                            "Only trusted bundled fixtures may use synthetic mode", len(requests))
    if not requests:
        if claim_type.type_id in _QUOTE_INTERNAL:
            return EvidenceGate(True, None, None, 0)
        return EvidenceGate(False, "EVIDENCE_UNAVAILABLE",
                            "Independent evidence provider is not configured", 0)
    for request in requests:
        if request.source_id not in policy.permitted_sources:
            return EvidenceGate(False, "POLICY_VIOLATION",
                                "Evidence source is not permitted", len(requests))
    return EvidenceGate(False, "EVIDENCE_UNAVAILABLE",
                        "Verified evidence adapter is not connected to the HTTP service",
                        len(requests))
