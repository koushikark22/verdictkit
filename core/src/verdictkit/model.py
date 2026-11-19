"""VerdictKit data model. Requirements: core 1, 2, 5, 6, 7.

All types are immutable. No field is ever a float. Constants in this module are part of
the specification and may be used directly; functions raise NotImplementedError until the
Kiro task that owns them is complete.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Mapping, Sequence


class Basis(str, Enum):
    INTERNAL_ARITHMETIC = "INTERNAL_ARITHMETIC"
    EXTERNAL_EVIDENCE = "EXTERNAL_EVIDENCE"
    MECHANICAL_BOUND = "MECHANICAL_BOUND"


class Status(str, Enum):
    CONSISTENT = "CONSISTENT"
    CONTRADICTED = "CONTRADICTED"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    CONDITIONAL = "CONDITIONAL"
    WITHIN_BOUND = "WITHIN_BOUND"
    IMPOSSIBLE = "IMPOSSIBLE"
    INDETERMINATE = "INDETERMINATE"


class Origin(str, Enum):
    CLAIMANT = "CLAIMANT"
    USER_CONFIRMED = "USER_CONFIRMED"
    DEFAULT_POLICY = "DEFAULT_POLICY"


class AssumptionKind(str, Enum):
    FIXED = "FIXED"
    RANGE = "RANGE"
    SET = "SET"
    MISSING = "MISSING"


class SourceClass(str, Enum):
    CLAIMANT = "CLAIMANT"
    EXCHANGE_PUBLIC_DATA = "EXCHANGE_PUBLIC_DATA"
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    DOCUMENT = "DOCUMENT"
    USER_SUPPLIED = "USER_SUPPLIED"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"  # generated test data; never evidence about the world


class LicenseClass(str, Enum):
    REDISTRIBUTABLE = "REDISTRIBUTABLE"
    REFETCH_ONLY = "REFETCH_ONLY"
    DOCUMENT = "DOCUMENT"
    USER_SUPPLIED = "USER_SUPPLIED"
    SYNTHETIC = "SYNTHETIC"


class DataMode(str, Enum):
    """B1 decision. LIVE_EVIDENCE forbids SYNTHETIC_FIXTURE evidence (fail closed).
    SYNTHETIC_DEMO runs compute normally but are presented as demonstrations only."""

    LIVE_EVIDENCE = "LIVE_EVIDENCE"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"


class IsolationMode(str, Enum):
    ENFORCED = "ENFORCED"
    UNENFORCED = "UNENFORCED"


# --- Specification constants (Req 6.1–6.3) ------------------------------------------

ALLOWED_STATUSES: Mapping[Basis, frozenset[Status]] = {
    Basis.INTERNAL_ARITHMETIC: frozenset(
        {Status.CONSISTENT, Status.CONTRADICTED, Status.CONDITIONAL, Status.INDETERMINATE}
    ),
    Basis.EXTERNAL_EVIDENCE: frozenset(
        {Status.SUPPORTED, Status.REFUTED, Status.CONDITIONAL, Status.INDETERMINATE}
    ),
    Basis.MECHANICAL_BOUND: frozenset(
        {Status.WITHIN_BOUND, Status.IMPOSSIBLE, Status.INDETERMINATE}
    ),
}

#: Higher number = more severe. Passing statuses share the lowest rank.
SEVERITY: Mapping[Status, int] = {
    Status.SUPPORTED: 0,
    Status.CONSISTENT: 0,
    Status.WITHIN_BOUND: 0,
    Status.INDETERMINATE: 1,
    Status.CONDITIONAL: 2,
    Status.REFUTED: 3,
    Status.CONTRADICTED: 4,
    Status.IMPOSSIBLE: 5,
}

#: Statuses that require at least one counterexample (Req 6.5).
NEEDS_COUNTEREXAMPLE: frozenset[Status] = frozenset(
    {Status.CONTRADICTED, Status.REFUTED, Status.CONDITIONAL, Status.IMPOSSIBLE}
)

CONFIDENCE_SCOPE: Mapping[Basis, str] = {
    Basis.INTERNAL_ARITHMETIC: (
        "Given the frozen document values and the stated formula convention."
    ),
    Basis.EXTERNAL_EVIDENCE: (
        "Given the cited evidence snapshots and the declared assumption ranges."
    ),
    Basis.MECHANICAL_BOUND: "Given the declared mechanics only.",
}

GRID_CAP_MAX = 1000


# --- Data types --------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Assumption:
    """One assumption axis (Req 7.1).

    FIXED uses ``value``; RANGE uses ``minimum``/``maximum``/``step`` (inclusive, Decimal);
    SET uses ``values`` (Decimal or str tokens); MISSING uses none of them.
    """

    name: str
    kind: AssumptionKind
    origin: Origin
    value: Decimal | str | None = None
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    step: Decimal | None = None
    values: tuple[Decimal | str, ...] = ()


@dataclass(frozen=True, slots=True)
class FrozenClaim:
    """Canonical frozen claim, excluding outcomes (Req 1.4)."""

    claim_type: str
    schema_version: int
    params: Mapping[str, object]
    assumptions: tuple[Assumption, ...]
    tolerances: Mapping[str, str]
    spec_hash: str


@dataclass(frozen=True, slots=True)
class BlindedTask:
    """The only message the Examiner ever receives (Req 2.2, 2.4)."""

    case_id: str
    claim_type: str
    schema_version: int
    spec_hash: str
    params: Mapping[str, object]
    assumptions: tuple[Assumption, ...]
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Commitment:
    alg: str  # "sha256/vk-commit-v1"
    digest: str  # 64 lowercase hex


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    source_id: str
    source_class: SourceClass
    uri: str
    retrieved_at: str  # ISO-8601 UTC; informational, excluded from verdict hash
    sha256: str
    media_type: str
    license_class: LicenseClass


@dataclass(frozen=True, slots=True)
class Counterexample:
    point: Mapping[str, str]  # assumption name -> canonical value
    expected: str | None
    observed: str | None
    difference: str | None
    tolerance: str | None
    note: str = ""


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: str
    basis: Basis
    status: Status
    statement: str
    reason: str | None = None  # e.g. "missing_assumption:fee_bps_per_side"
    evidence_used: tuple[str, ...] = ()  # evidence sha256 values
    assumption_dependencies: tuple[str, ...] = ()
    counterexamples: tuple[Counterexample, ...] = ()
    numbers: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Verdict:
    findings: tuple[Finding, ...]
    headline: Status
    verdict_hash: str


class InvalidFindingError(ValueError):
    """Raised for a disallowed basis/status pair or a missing counterexample."""


# --- Functions (Kiro core task 3) ---------------------------------------------------

def validate_finding(finding: Finding) -> Finding:
    """Return ``finding`` unchanged if valid, else raise InvalidFindingError.

    Valid means: status in ALLOWED_STATUSES[basis]; at least one counterexample when the
    status is in NEEDS_COUNTEREXAMPLE; all ``numbers`` values parse as finite Decimals.
    """
    allowed = ALLOWED_STATUSES.get(finding.basis, frozenset())
    if finding.status not in allowed:
        raise InvalidFindingError(
            f"status {finding.status!r} is not allowed for basis {finding.basis!r}"
        )
    if finding.status in NEEDS_COUNTEREXAMPLE and not finding.counterexamples:
        raise InvalidFindingError(
            f"status {finding.status!r} requires at least one counterexample"
        )
    for key, val in finding.numbers.items():
        try:
            d = Decimal(val)
            if not d.is_finite():
                raise InvalidFindingError(f"numbers[{key!r}] is not a finite Decimal: {val!r}")
        except (InvalidOperation, TypeError):
            raise InvalidFindingError(f"numbers[{key!r}] is not a valid Decimal string: {val!r}")
    return finding


def headline_status(findings: Sequence[Finding]) -> Status:
    """Worst status by SEVERITY (Req 6.3). Empty input raises ValueError.

    Among equal-severity passing statuses, return the status of the first finding.
    """
    if not findings:
        raise ValueError("headline_status requires at least one finding")
    worst_sev = max(SEVERITY[f.status] for f in findings)
    # At severity 0 (passing), return the first finding's status.
    if worst_sev == 0:
        return findings[0].status
    # Return the status of the first finding with the worst severity.
    for f in findings:
        if SEVERITY[f.status] == worst_sev:
            return f.status
    # unreachable
    raise ValueError("logic error in headline_status")


def compute_verdict_hash(
    *,
    spec_hash: str,
    evidence_hashes: Sequence[str],
    examination: Mapping[str, object],
    outcomes: Mapping[str, object],
    findings: Sequence[Finding],
) -> str:
    """SHA-256 hex over canonical JSON of the arguments (Req 6.4).

    ``examination`` is ``verdictkit.plugin.examination_payload(examination)``.

    ``evidence_hashes`` are sorted before hashing. Timestamps, salts, ledger entries and
    diagnostics are not inputs and therefore cannot affect the result.
    """
    from .canonical import canonical_bytes, sha256_hex

    payload = {
        "spec_hash": spec_hash,
        "evidence_hashes": sorted(evidence_hashes),
        "examination": examination,
        "outcomes": outcomes,
        "findings": [
            {
                "finding_id": f.finding_id,
                "basis": f.basis.value,
                "status": f.status.value,
                "statement": f.statement,
                "reason": f.reason,
                "evidence_used": list(f.evidence_used),
                "assumption_dependencies": list(f.assumption_dependencies),
                "counterexamples": [
                    {
                        "point": dict(c.point),
                        "expected": c.expected,
                        "observed": c.observed,
                        "difference": c.difference,
                        "tolerance": c.tolerance,
                        "note": c.note,
                    }
                    for c in f.counterexamples
                ],
                "numbers": dict(f.numbers),
            }
            for f in findings
        ],
    }
    return sha256_hex(canonical_bytes(payload))
