"""Examiner handoff must be deterministic, blinded and bound to a specification."""
import pytest

from verdictkit.api.examination_boundary import (
    ExaminationRejected, prepare_examiner_handoff, require_isolated_examiner,
    verify_examiner_result,
)
from verdictkit.custody.intake import freeze
from verdictkit.examiner.protocol import decode_task, encode_result
from verdictkit.model import IsolationMode
from verdictkit.plugin import Examination, PointResult


class Claim:
    type_id = "quote.finance.v1"
    schema_version = 1
    param_fields = frozenset({"selling_price"})
    outcome_fields = frozenset({"monthly_payment"})

    def validate_params(self, params):
        assert isinstance(params["selling_price"], str)

    def validate_outcomes(self, outcomes):
        assert isinstance(outcomes["monthly_payment"], str)

    def assumption_specs(self, declared):
        return ()

    def tolerances(self, params, outcomes):
        return {"monthly_payment": "0.01"}


def _frozen(secret):
    return freeze(Claim(), {
        "claim_type": "quote.finance.v1", "schema_version": 1,
        "params": {"selling_price": "15000.00"},
        "outcomes": {"monthly_payment": secret}, "assumptions": {},
    }).frozen


def test_protocol_never_carries_asserted_outcome():
    a = prepare_examiner_handoff(_frozen("OUTCOME_SECRET_1"),
                                  case_id="case_" + "a" * 32)
    b = prepare_examiner_handoff(_frozen("OUTCOME_SECRET_2"),
                                  case_id="case_" + "a" * 32)
    assert a.task_bytes == b.task_bytes
    assert b"OUTCOME_SECRET" not in a.task_bytes
    task = decode_task(a.task_bytes)
    assert task.params == {"selling_price": "15000.00"}
    assert task.evidence_refs == ()


def test_verified_result_must_match_frozen_spec():
    gate = prepare_examiner_handoff(_frozen("100.00"),
                                    case_id="case_" + "b" * 32)
    result = Examination(gate.spec_hash, {}, (PointResult({}, {"monthly_payment": "99.99"}),))
    assert verify_examiner_result(encode_result(result),
                                  expected_spec_hash=gate.spec_hash) == result
    altered = Examination("f" * 64, {}, ())
    with pytest.raises(ExaminationRejected, match="different specification"):
        verify_examiner_result(encode_result(altered),
                               expected_spec_hash=gate.spec_hash)


def test_malformed_evidence_hash_rejected():
    with pytest.raises(ExaminationRejected):
        prepare_examiner_handoff(_frozen("100.00"),
                                 case_id="case_" + "b" * 32,
                                 evidence_refs=("../not-a-sha",))


def test_judge_cannot_use_in_process_executor():
    with pytest.raises(ExaminationRejected, match="isolated"):
        require_isolated_examiner(IsolationMode.UNENFORCED, judge_mode=True)
    require_isolated_examiner(IsolationMode.ENFORCED, judge_mode=True)
    require_isolated_examiner(IsolationMode.UNENFORCED, judge_mode=False)
