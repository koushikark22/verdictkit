"""Claim-type plugin protocol and registry. Requirements: core 10.

The core calls plugin code only through these methods. ``examine`` runs in the Examiner
and never receives outcomes. ``findings`` and ``diagnose`` run in the Custodian after
reveal.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence, runtime_checkable

from .model import Assumption, BlindedTask, EvidenceItem, Finding, FrozenClaim, SourceClass


@dataclass(frozen=True, slots=True)
class EvidenceRequest:
    source_id: str
    query: Mapping[str, object]  # canonical JSON-safe


@dataclass(frozen=True, slots=True)
class EvidencePolicySpec:
    permitted_sources: frozenset[str]
    forbidden_classes: frozenset[SourceClass] = frozenset({SourceClass.CLAIMANT})


class EvidenceReader(Protocol):
    """Read-only, hash-verified access to acquired evidence inside the Examiner."""

    def read(self, sha256: str) -> bytes: ...

    def items(self) -> Sequence[EvidenceItem]: ...


@dataclass(frozen=True, slots=True)
class PointResult:
    """Computed values at one grid point. Values are canonical Decimal strings or ints."""

    point: Mapping[str, str]
    values: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class Examination:
    spec_hash: str
    shared: Mapping[str, object]  # point-independent values (e.g. bound, coverage)
    points: tuple[PointResult, ...]
    missing_assumptions: tuple[str, ...] = ()


def examination_payload(examination: Examination) -> dict[str, object]:
    """The canonical form of an Examination used for hashing and bundles:
    ``{"shared": {...}, "points": [{"point": {...}, "values": {...}}, ...]}``
    (``spec_hash`` and ``missing_assumptions`` are covered elsewhere and omitted)."""
    return {
        "shared": dict(examination.shared),
        "points": [
            {"point": dict(p.point), "values": dict(p.values)}
            for p in examination.points
        ],
    }


@runtime_checkable
class ClaimType(Protocol):
    type_id: str
    schema_version: int
    param_fields: frozenset[str]
    outcome_fields: frozenset[str]

    def validate_params(self, params: Mapping[str, object]) -> None:
        """Raise ``SchemaError`` (from verdictkit.custody.intake) if params are invalid."""

    def validate_outcomes(self, outcomes: Mapping[str, object]) -> None:
        """Raise ``SchemaError`` if outcomes are invalid (e.g. none present)."""

    def assumption_specs(self, declared: Mapping[str, object]) -> tuple[Assumption, ...]:
        """Resolve declared assumptions + policy defaults into axes with origins."""

    def tolerances(
        self, params: Mapping[str, object], outcomes: Mapping[str, object]
    ) -> Mapping[str, str]:
        """Tolerances per outcome. May depend on stated precision; must not depend on
        outcome *values* beyond their written precision."""

    def evidence_requests(self, params: Mapping[str, object]) -> Sequence[EvidenceRequest]: ...

    def evidence_policy(self) -> EvidencePolicySpec: ...

    def examine(
        self, task: BlindedTask, evidence: EvidenceReader, points: Sequence[Mapping[str, str]]
    ) -> Examination:
        """Pure, deterministic, Decimal-only. Runs in the Examiner."""

    def findings(
        self,
        frozen: FrozenClaim,
        examination: Examination,
        outcomes: Mapping[str, object],
        evidence: Sequence[EvidenceItem],
    ) -> Sequence[Finding]:
        """Pure comparison after reveal. Runs in the Custodian."""

    # Optional hooks (looked up with getattr; absent on most claim types):
    #   validate_assumptions(params, assumptions) -> None   cross-check at freeze/intake
    #   point_outcomes(frozen, examination, outcomes) -> {finding_id: [PointOutcome]}
    #   evidence_adapters() -> [SourceAdapter]               local evidence adapters
    #   fixtures() -> {fixture_id: raw_claim}                trusted SYNTHETIC_DEMO claims
    #   extract_text(text) -> (params, outcomes, spans)      transient pasted-text intake

    def diagnose(
        self,
        frozen: FrozenClaim,
        examination: Examination,
        outcomes: Mapping[str, object],
    ) -> Mapping[str, object] | None:
        """Optional post-reveal diagnostics (Req 10.4). Return None if not supported."""


class Registry:
    """Claim types keyed by ``type_id`` (Req 10.1)."""

    def __init__(self) -> None:
        self._types: dict[str, ClaimType] = {}

    def register(self, claim_type: ClaimType) -> None:
        self._types[claim_type.type_id] = claim_type

    def get(self, type_id: str) -> ClaimType:
        try:
            return self._types[type_id]
        except KeyError:
            raise KeyError(f"unknown claim type: {type_id!r}") from None

    def type_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._types.keys()))
