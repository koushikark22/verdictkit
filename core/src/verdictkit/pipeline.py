"""Case orchestration. Requirements: core 2–10.

run_case performs, in order: CASE_OPENED; freeze -> CLAIM_FROZEN; commit + seal ->
OUTCOMES_COMMITTED; evidence acquisition -> EVIDENCE_ACQUIRED; blind + examine ->
EXAMINATION_COMMITTED; compare_and_seal (reveal, verdict, diagnostics).
"""
from __future__ import annotations

import base64
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from .custody.commitment import commit, new_salt
from .custody.comparator import compare_and_seal
from .custody.intake import blind, freeze
from .custody.ledger import EntryKind, Ledger
from .custody.vault import Vault
from .evidence.broker import EvidenceBroker
from .evidence.store import EvidenceStore
from .examiner.client import Examiner
from .model import Commitment, DataMode, EvidenceItem, FrozenClaim, IsolationMode, Verdict
from .plugin import Examination, Registry


@dataclass(frozen=True, slots=True)
class CaseFile:
    case_id: str
    isolation: IsolationMode
    data_mode: DataMode
    frozen: FrozenClaim
    commitment: Commitment
    salt: bytes
    outcomes: Mapping[str, object]
    evidence: tuple[EvidenceItem, ...]
    examination: Examination
    verdict: Verdict
    diagnostics: Mapping[str, object] | None
    ledger: Ledger


def run_case(
    raw_claim: Mapping[str, object],
    *,
    registry: Registry,
    examiner: Examiner,
    workdir: Path,
    clock: Callable[[], str],
    case_id: str | None = None,
    vault_key: bytes | None = None,
    network: bool = True,
    data_mode: DataMode = DataMode.LIVE_EVIDENCE,
) -> CaseFile:
    """``case_id`` defaults to a random UUID4 hex; pass one for deterministic tests.

    ``vault_key`` defaults to ``VK_VAULT_KEY``; tests pass an explicit key.
    """
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    if case_id is None:
        case_id = uuid.uuid4().hex

    # Resolve vault key
    if vault_key is None:
        raw_key = os.environ.get("VK_VAULT_KEY")
        if raw_key is None:
            vault_key = os.urandom(32)
        else:
            vault_key = base64.b64decode(raw_key)

    # Initialise components
    ledger = Ledger(clock)
    vault_dir = workdir / "vault"
    vault_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    vault = Vault(vault_dir, vault_key, examiner.isolation)
    evidence_dir = workdir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(evidence_dir)
    broker = EvidenceBroker(store, [], network=network)

    # 1. CASE_OPENED
    ledger.append(EntryKind.CASE_OPENED, {"case_id": case_id, "data_mode": data_mode.value})

    # 2. Freeze claim -> CLAIM_FROZEN
    claim_type_id = raw_claim.get("claim_type")
    if not isinstance(claim_type_id, str):
        raise ValueError("raw_claim must contain a string 'claim_type'")
    claim_type = registry.get(claim_type_id)
    intake_result = freeze(claim_type, raw_claim)
    frozen = intake_result.frozen
    outcomes = intake_result.outcomes
    ledger.append(EntryKind.CLAIM_FROZEN, {"spec_hash": frozen.spec_hash})

    # 3. Commit + seal outcomes -> OUTCOMES_COMMITTED
    salt = new_salt()
    commitment = commit(outcomes, salt)
    sealed_ref = vault.seal(case_id, outcomes)
    ledger.append(EntryKind.OUTCOMES_COMMITTED, {
        "commitment_digest": commitment.digest,
        "alg": commitment.alg,
    })

    # 4. Evidence acquisition -> EVIDENCE_ACQUIRED
    evidence_requests = claim_type.evidence_requests(frozen.params)
    policy = claim_type.evidence_policy()
    evidence_items: tuple[EvidenceItem, ...] = ()
    if evidence_requests:
        try:
            evidence_items = broker.acquire(evidence_requests, policy)
        except Exception:
            evidence_items = ()
    ledger.append(EntryKind.EVIDENCE_ACQUIRED, {
        "evidence_count": len(evidence_items),
        "evidence_hashes": [e.sha256 for e in evidence_items],
    })

    # 5. Blind + examine -> EXAMINATION_COMMITTED
    evidence_refs = [e.sha256 for e in evidence_items]
    blinded = blind(frozen, case_id=case_id, evidence_refs=evidence_refs)
    examination = examiner.examine(blinded)
    ledger.append(EntryKind.EXAMINATION_COMMITTED, {
        "spec_hash": examination.spec_hash,
    })

    # 6. Reveal + compare + seal verdict + optional diagnostics
    sealed_case = compare_and_seal(
        claim_type=claim_type,
        frozen=frozen,
        examination=examination,
        evidence=evidence_items,
        vault=vault,
        sealed=sealed_ref,
        commitment=commitment,
        salt=salt,
        ledger=ledger,
    )

    # 7. Bundle written will be recorded by write_bundle
    # (not recorded here — the caller decides)

    return CaseFile(
        case_id=case_id,
        isolation=examiner.isolation,
        data_mode=data_mode,
        frozen=frozen,
        commitment=commitment,
        salt=salt,
        outcomes=sealed_case.outcomes,
        evidence=evidence_items,
        examination=examination,
        verdict=sealed_case.verdict,
        diagnostics=sealed_case.diagnostics,
        ledger=ledger,
    )
