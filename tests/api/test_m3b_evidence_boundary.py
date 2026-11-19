"""No independent evidence may be silently inferred from an empty request list."""
from dataclasses import dataclass

from verdictkit.api.evidence_boundary import preflight_evidence
from verdictkit.model import DataMode
from verdictkit.plugin import EvidencePolicySpec, EvidenceRequest
from quote_autopsy.claim_type import FinanceClaimType, LeaseClaimType
from reel_autopsy.claim_type import ReelClaimType


def test_internal_quote_claims_need_no_external_data():
    for plugin in (FinanceClaimType(), LeaseClaimType()):
        gate = preflight_evidence(plugin, {}, data_mode=DataMode.LIVE_EVIDENCE)
        assert gate.allowed
        assert gate.public_blocker() is None
        assert gate.request_count == 0


def test_reel_without_verified_feed_is_explicitly_blocked():
    gate = preflight_evidence(ReelClaimType(), {}, data_mode=DataMode.LIVE_EVIDENCE)
    assert not gate.allowed
    assert gate.blocker_code == "EVIDENCE_UNAVAILABLE"
    assert gate.public_blocker()["code"] == "EVIDENCE_UNAVAILABLE"


def test_synthetic_mode_is_not_admitted_through_live_boundary():
    gate = preflight_evidence(FinanceClaimType(), {}, data_mode=DataMode.SYNTHETIC_DEMO)
    assert not gate.allowed
    assert gate.blocker_code == "POLICY_VIOLATION"


class UnregisteredSource:
    type_id = "custom.source.v1"

    def evidence_requests(self, params):
        return (EvidenceRequest("not-registered", {}),)

    def evidence_policy(self):
        return EvidencePolicySpec(frozenset({"some-other-source"}))


class PermittedButUnavailable(UnregisteredSource):
    def evidence_policy(self):
        return EvidencePolicySpec(frozenset({"not-registered"}))


def test_unpermitted_source_is_denied():
    gate = preflight_evidence(UnregisteredSource(), {}, data_mode=DataMode.LIVE_EVIDENCE)
    assert not gate.allowed and gate.blocker_code == "POLICY_VIOLATION"


def test_permitted_but_unwired_source_is_not_marked_acquired():
    gate = preflight_evidence(PermittedButUnavailable(), {}, data_mode=DataMode.LIVE_EVIDENCE)
    assert not gate.allowed and gate.blocker_code == "EVIDENCE_UNAVAILABLE"
