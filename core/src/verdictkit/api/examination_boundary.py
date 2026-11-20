"""Safe examiner handoff for a committed, evidence-acquired case.

This boundary never accepts claimed outcomes. The HTTP execution route remains
locked until scheduling, durable events and verdict joining are implemented.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from verdictkit.custody.intake import blind
from verdictkit.examiner.protocol import decode_result, decode_task, encode_result, encode_task
from verdictkit.model import FrozenClaim, IsolationMode
from verdictkit.plugin import Examination


class ExaminationRejected(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExaminationGate:
    task_bytes: bytes
    spec_hash: str


def prepare_examiner_handoff(
    frozen: FrozenClaim,
    *,
    case_id: str,
    evidence_refs: Sequence[str] = (),
) -> ExaminationGate:
    """Materialize only the existing blinded task protocol.

    The caller must verify frozen custody and acquired evidence before invoking
    this function. No outcome mapping or salt can be passed through its API.
    """
    if not isinstance(case_id, str) or re.fullmatch(r"case_[0-9a-f]{32}", case_id) is None:
        raise ExaminationRejected("invalid case identifier")
    if any(not isinstance(ref, str) or len(ref) != 64 or
           any(c not in "0123456789abcdef" for c in ref) for ref in evidence_refs):
        raise ExaminationRejected("invalid evidence hash")
    task = blind(frozen, case_id=case_id, evidence_refs=tuple(evidence_refs))
    payload = encode_task(task)
    decoded = decode_task(payload)
    if decoded.spec_hash != frozen.spec_hash or decoded.params != frozen.params:
        raise ExaminationRejected("blinded task mismatch")
    return ExaminationGate(payload, frozen.spec_hash)


def verify_examiner_result(
    result_bytes: bytes,
    *,
    expected_spec_hash: str,
) -> Examination:
    """Reject stale, malformed, or mismatched results before any outcome reveal."""
    result = decode_result(result_bytes)
    if result.spec_hash != expected_spec_hash:
        raise ExaminationRejected("examiner returned a different specification")
    # Canonical roundtrip rejects unsafe payloads and ambiguous numeric values.
    if encode_result(result) != result_bytes:
        raise ExaminationRejected("examiner result is not canonical")
    return result


def require_isolated_examiner(mode: IsolationMode, *, judge_mode: bool) -> None:
    """A judge-run request cannot fall back to in-process examination."""
    if judge_mode and mode is not IsolationMode.ENFORCED:
        raise ExaminationRejected("isolated examiner required")
