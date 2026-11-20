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
                       *, data_mode: DataMode, fixture_id: str | None = None) -> EvidenceGate:
    """Reject unsupported acquisition before any network or ledger transition.

    A no-request finance/lease claim may proceed solely for document-internal
    calculations; this does not verify taxes, rules, or market claims.
    SYNTHETIC_DEMO is admitted only for a trusted bundled fixture whose every request
    is served by a local adapter that the data-mode policy permits. In LIVE_EVIDENCE,
    a request for a source class the policy forbids (synthetic data) is a violation.
    """
    policy = effective_policy(claim_type.evidence_policy(), data_mode)
    requests = tuple(claim_type.evidence_requests(params))
    adapters = {a.source_id: a for a in getattr(claim_type, "evidence_adapters", lambda: ())()}
    if data_mode is DataMode.SYNTHETIC_DEMO:
        fixtures = getattr(claim_type, "fixtures", lambda: {})()
        if fixture_id is None or fixture_id not in fixtures:
            return EvidenceGate(False, "POLICY_VIOLATION",
                                "Only trusted bundled fixtures may use synthetic mode", len(requests))
    if not requests:
        if claim_type.type_id in _QUOTE_INTERNAL and data_mode is DataMode.LIVE_EVIDENCE:
            return EvidenceGate(True, None, None, 0)
        return EvidenceGate(False, "EVIDENCE_UNAVAILABLE",
                            "Independent evidence provider is not configured", 0)
    for request in requests:
        if request.source_id not in policy.permitted_sources:
            return EvidenceGate(False, "POLICY_VIOLATION",
                                "Evidence source is not permitted", len(requests))
        adapter = adapters.get(request.source_id)
        if adapter is None:
            return EvidenceGate(False, "EVIDENCE_UNAVAILABLE",
                                "Verified evidence adapter is not connected to the HTTP service",
                                len(requests))
        if getattr(adapter, "source_class", None) in policy.forbidden_classes:
            return EvidenceGate(False, "POLICY_VIOLATION",
                                "Synthetic fixture data cannot support a live case", len(requests))
        if getattr(adapter, "requires_network", True):
            return EvidenceGate(False, "EVIDENCE_UNAVAILABLE",
                                "Network evidence acquisition is not enabled in the HTTP service",
                                len(requests))
    return EvidenceGate(True, None, None, len(requests))
