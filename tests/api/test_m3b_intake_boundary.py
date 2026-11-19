"""Focused M3b intake boundary regressions. No network or custody side effects."""
import pytest

from verdictkit.api.intake_boundary import IntakeRejected, prepare_intake
from verdictkit.plugin import Registry


class Claim:
    type_id = "quote.finance.v1"
    schema_version = 1
    outcome_fields = frozenset({"monthly_payment"})
    param_fields = frozenset({"selling_price"})

    def validate_params(self, params):
        if not isinstance(params.get("selling_price"), str):
            raise ValueError("invalid param")

    def validate_outcomes(self, outcomes):
        if not isinstance(outcomes.get("monthly_payment"), str):
            raise ValueError("invalid outcome")

    def assumption_specs(self, assumptions):
        return ()


@pytest.fixture
def registry():
    r = Registry()
    r.register(Claim())
    return r


@pytest.fixture
def payload():
    return {
        "claimType": "quote.finance.v1",
        "dataMode": "LIVE_EVIDENCE",
        "form": {"params": {"selling_price": "25000.00"},
                 "outcomes": {"monthly_payment": "555.12"}},
    }


def test_only_capture_flag_is_public(registry, payload):
    case = prepare_intake(payload, registry)
    assert case.outcome_fields == ({"name": "monthly_payment", "captured": True},)
    assert "555.12" not in str(case.outcome_fields)
    assert case.raw_claim["outcomes"]["monthly_payment"] == "555.12"


@pytest.mark.parametrize("mutation", [
    {"dataMode": "SYNTHETIC_DEMO", "fixtureId": "fx_demo"},
    {"pastedText": "claimed profit 99%"},
    {"fixtureId": "fx_demo"},
    {"unexpected": "some data"},
])
def test_unwired_or_extra_inputs_fail_closed(registry, payload, mutation):
    payload.update(mutation)
    with pytest.raises(IntakeRejected):
        prepare_intake(payload, registry)


def test_float_is_never_coerced(registry, payload):
    payload["form"]["outcomes"]["monthly_payment"] = 555.12
    with pytest.raises(IntakeRejected) as exc:
        prepare_intake(payload, registry)
    assert exc.value.code == "SCHEMA_INVALID"


def test_outcome_in_parameters_rejected(registry, payload):
    payload["form"]["params"]["monthly_payment"] = "555.12"
    with pytest.raises(IntakeRejected):
        prepare_intake(payload, registry)


def test_validation_error_does_not_echo_outcome(registry, payload):
    payload["form"]["outcomes"]["monthly_payment"] = "SECRET_SENTINEL"
    # Deliberately make plugin fail with a secret in its exception.
    registry.get("quote.finance.v1").validate_outcomes = lambda _: (_ for _ in ()).throw(ValueError("SECRET_SENTINEL"))
    with pytest.raises(IntakeRejected) as exc:
        prepare_intake(payload, registry)
    assert "SECRET_SENTINEL" not in str(exc.value)


def test_prepared_intake_repr_never_contains_claimed_outcome(registry, payload):
    prepared = prepare_intake(payload, registry)
    assert "555.12" not in repr(prepared)
    assert "monthly_payment" in repr(prepared)
