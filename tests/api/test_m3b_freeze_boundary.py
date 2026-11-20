"""Freeze-boundary invariants across real canonical custody primitives."""
import pytest

from verdictkit.api.freeze_boundary import prepare_freeze
from verdictkit.custody.commitment import verify
from verdictkit.custody.ledger import EntryKind
from verdictkit.custody.intake import blind


class Claim:
    type_id = "quote.finance.v1"
    schema_version = 1
    param_fields = frozenset({"selling_price"})
    outcome_fields = frozenset({"monthly_payment"})

    def validate_params(self, params):
        if not isinstance(params.get("selling_price"), str):
            raise ValueError("missing selling_price")

    def validate_outcomes(self, outcomes):
        if not isinstance(outcomes.get("monthly_payment"), str):
            raise ValueError("missing monthly_payment")

    def assumption_specs(self, _declared):
        return ()

    def tolerances(self, _params, _outcomes):
        return {"monthly_payment": "0.01"}


def raw(outcome):
    return {
        "claim_type": "quote.finance.v1",
        "schema_version": 1,
        "params": {"selling_price": "25000.00"},
        "outcomes": {"monthly_payment": outcome},
        "assumptions": {},
    }


def test_spec_independent_of_asserted_outcomes():
    one = prepare_freeze(Claim(), raw("123.45"), case_id="case_"+"a"*32,
                         clock=lambda: "2026-01-01T00:00:00Z")
    two = prepare_freeze(Claim(), raw("999.99"), case_id="case_"+"a"*32,
                         clock=lambda: "2026-01-01T00:00:00Z")
    assert one.frozen.spec_hash == two.frozen.spec_hash
    assert one.commitment.digest != two.commitment.digest
    assert one.salt != two.salt
    assert verify(one.commitment, one.asserted_outcomes, one.salt)
    assert not verify(one.commitment, two.asserted_outcomes, one.salt)


def test_blinded_task_has_no_asserted_outcomes():
    result = prepare_freeze(Claim(), raw("SECRET_SENTINEL"),
                            case_id="case_"+"b"*32, clock=lambda: "2026-01-01T00:00:00Z")
    task = blind(result.frozen, case_id="case_"+"b"*32)
    assert "SECRET_SENTINEL" not in repr(task)
    assert "SECRET_SENTINEL" not in repr(result)
    assert "SECRET_SENTINEL" not in str(result.public_projection())
    assert result.salt.hex() not in repr(result)
    assert [e.kind for e in result.ledger_entries] == [
        EntryKind.CASE_OPENED, EntryKind.CLAIM_FROZEN, EntryKind.OUTCOMES_COMMITTED
    ]
    assert result.public_projection()["ledgerSeq"] == 2


def test_invalid_outcomes_cannot_be_frozen():
    malformed = raw("123.45")
    malformed["outcomes"] = {}
    with pytest.raises(ValueError):
        prepare_freeze(Claim(), malformed, case_id="case_"+"c"*32,
                       clock=lambda: "2026-01-01T00:00:00Z")


def test_outcome_in_params_rejected():
    malformed = raw("123.45")
    malformed["params"]["monthly_payment"] = "123.45"
    with pytest.raises(ValueError):
        prepare_freeze(Claim(), malformed, case_id="case_"+"c"*32,
                       clock=lambda: "2026-01-01T00:00:00Z")
