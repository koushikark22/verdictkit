"""Evidence policy, fail closed. Requirements: core 5.2, 5.3. Property: P8."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Mapping

from ..model import DataMode, EvidenceItem, Finding, SourceClass, Status
from ..plugin import EvidencePolicySpec


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str | None  # "forbidden_source_class:<CLASS>" | "source_not_permitted:<id>"


def check(item: EvidenceItem, policy: EvidencePolicySpec) -> PolicyDecision:
    # Forbidden class check (always overrides permitted-source check)
    if item.source_class in policy.forbidden_classes:
        return PolicyDecision(
            allowed=False,
            reason=f"forbidden_source_class:{item.source_class.value}",
        )
    # Permitted source check
    if item.source_id not in policy.permitted_sources:
        return PolicyDecision(
            allowed=False,
            reason=f"source_not_permitted:{item.source_id}",
        )
    return PolicyDecision(allowed=True, reason=None)


def apply_policy(
    finding: Finding, evidence: Mapping[str, EvidenceItem], policy: EvidencePolicySpec
) -> Finding:
    """Return ``finding`` unchanged if every cited evidence hash is present and allowed.

    Otherwise return a copy with status INDETERMINATE, reason ``policy_violation`` (or
    ``evidence_missing`` for an unknown hash), and no counterexamples. The basis is kept.
    """
    for sha in finding.evidence_used:
        item = evidence.get(sha)
        if item is None:
            return dataclasses.replace(
                finding,
                status=Status.INDETERMINATE,
                reason="evidence_missing",
                counterexamples=(),
            )
        decision = check(item, policy)
        if not decision.allowed:
            return dataclasses.replace(
                finding,
                status=Status.INDETERMINATE,
                reason="policy_violation",
                counterexamples=(),
            )
    return finding


def effective_policy(spec: EvidencePolicySpec, data_mode: DataMode) -> EvidencePolicySpec:
    """LIVE_EVIDENCE: add SYNTHETIC_FIXTURE to ``forbidden_classes``. SYNTHETIC_DEMO:
    unchanged. CLAIMANT stays forbidden in both. Applied by the core, not by plugins."""
    if data_mode is DataMode.LIVE_EVIDENCE:
        new_forbidden = spec.forbidden_classes | frozenset({SourceClass.SYNTHETIC_FIXTURE})
        return EvidencePolicySpec(
            permitted_sources=spec.permitted_sources,
            forbidden_classes=new_forbidden,
        )
    return spec
