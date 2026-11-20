"""Reveal, compare, seal. Requirements: core 3.3, 5.3, 6, 10.4.

Order inside ``compare_and_seal`` (all ledger appends go through Ledger.append, so the
state machine forbids any reordering):
  1. require last ledger entry == EXAMINATION_COMMITTED
  2. unseal outcomes; verify commitment (CommitmentMismatchError -> CASE_ABORTED)
  3. append OUTCOMES_REVEALED (payload: salt hex + outcomes)
  4. plugin.findings(...) -> apply evidence policy (fail closed) -> validate_finding each
  5. headline_status, compute_verdict_hash -> append VERDICT_SEALED
  6. optional plugin.diagnose(...) -> append DIAGNOSTICS_APPENDED
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..evidence.policy import apply_policy, effective_policy
from ..model import (
    Commitment,
    DataMode,
    EvidenceItem,
    FrozenClaim,
    Status,
    Verdict,
    compute_verdict_hash,
    headline_status,
    validate_finding,
)
from ..plugin import ClaimType, Examination, examination_payload
from .commitment import CommitmentMismatchError, verify as verify_commitment
from .ledger import EntryKind, Ledger
from .vault import SealedRef, Vault


@dataclass(frozen=True, slots=True)
class SealedCase:
    verdict: Verdict
    outcomes: Mapping[str, object]
    salt: bytes
    diagnostics: Mapping[str, object] | None


def compare_and_seal(
    *,
    claim_type: ClaimType,
    frozen: FrozenClaim,
    examination: Examination,
    evidence: tuple[EvidenceItem, ...],
    vault: Vault,
    sealed: SealedRef,
    commitment: Commitment,
    salt: bytes,
    ledger: Ledger,
    data_mode: DataMode = DataMode.LIVE_EVIDENCE,
) -> SealedCase:
    # 1. Verify we are in the right state (EXAMINATION_COMMITTED)
    if not ledger.entries or ledger.entries[-1].kind is not EntryKind.EXAMINATION_COMMITTED:
        raise RuntimeError(
            "compare_and_seal requires last ledger entry to be EXAMINATION_COMMITTED"
        )

    # 2. Unseal outcomes and verify commitment
    outcomes = vault.unseal(sealed)
    if not verify_commitment(commitment, outcomes, salt):
        ledger.append(EntryKind.CASE_ABORTED, {"reason": "commitment_mismatch"})
        raise CommitmentMismatchError("commitment verification failed")

    # 3. Record OUTCOMES_REVEALED
    ledger.append(EntryKind.OUTCOMES_REVEALED, {
        "salt": salt.hex(),
        "outcomes": dict(outcomes),
    })

    # 4. Build findings; apply evidence policy (fail-closed)
    evidence_map = {item.sha256: item for item in evidence}
    # The core, not the plugin, applies the data-mode rule (LIVE forbids synthetic).
    policy = effective_policy(claim_type.evidence_policy(), data_mode)
    raw_findings = claim_type.findings(frozen, examination, outcomes, list(evidence))
    validated_findings = []
    for f in raw_findings:
        f = apply_policy(f, evidence_map, policy)
        f = validate_finding(f)
        validated_findings.append(f)

    findings_tuple = tuple(validated_findings)

    # 5. Headline status + verdict hash
    if findings_tuple:
        headline = headline_status(findings_tuple)
    else:
        headline = Status.INDETERMINATE

    verdict_hash = compute_verdict_hash(
        spec_hash=frozen.spec_hash,
        evidence_hashes=[item.sha256 for item in evidence],
        examination=examination_payload(examination),
        outcomes=dict(outcomes),
        findings=findings_tuple,
    )

    verdict = Verdict(
        findings=findings_tuple,
        headline=headline,
        verdict_hash=verdict_hash,
    )

    ledger.append(EntryKind.VERDICT_SEALED, {"verdict_hash": verdict_hash})

    # 6. Optional diagnostics (after VERDICT_SEALED)
    diagnostics = None
    try:
        diag_result = claim_type.diagnose(frozen, examination, outcomes)
        if diag_result is not None:
            diagnostics = dict(diag_result)
            ledger.append(EntryKind.DIAGNOSTICS_APPENDED, {"has_diagnostics": True})
    except Exception:
        pass  # Diagnostics are optional and must not affect the verdict

    return SealedCase(
        verdict=verdict,
        outcomes=dict(outcomes),
        salt=salt,
        diagnostics=diagnostics,
    )
