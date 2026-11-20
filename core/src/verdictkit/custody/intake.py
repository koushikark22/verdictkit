"""Intake: validate, partition, freeze, blind. Requirements: core 1, 2. Properties P2, P3, P5.

Raw claim shape (JSON object; all numbers that are not integers must be strings)::

    {
      "claim_type": "reel.mechanical.v1",
      "schema_version": 1,
      "params": {...},
      "outcomes": {...},          # sealed; never reaches the Examiner
      "assumptions": {...},       # name -> value | {"min","max","step"} | {"set": [...]} | null
      "tolerances": {...}         # optional overrides
    }
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Sequence

from ..canonical import canonical_bytes, sha256_hex
from ..model import Assumption, AssumptionKind, BlindedTask, FrozenClaim, Origin
from ..plugin import ClaimType
from ..sweep import expand_grid


class SchemaError(ValueError):
    """Claim does not match the claim type's schema."""


@dataclass(frozen=True, slots=True)
class IntakeResult:
    frozen: FrozenClaim
    outcomes: Mapping[str, object]  # held by the Custodian only; sealed immediately


def _parse_assumption_value(raw: object, name: str) -> Assumption:
    """Parse one raw assumption declaration into an Assumption."""
    if raw is None:
        return Assumption(name, AssumptionKind.MISSING, Origin.CLAIMANT)

    if isinstance(raw, dict):
        if "set" in raw:
            values = tuple(
                Decimal(str(v)) if not isinstance(v, str) else Decimal(v)
                for v in raw["set"]
            )
            return Assumption(name, AssumptionKind.SET, Origin.CLAIMANT, values=values)
        if "min" in raw and "max" in raw and "step" in raw:
            return Assumption(
                name,
                AssumptionKind.RANGE,
                Origin.CLAIMANT,
                minimum=Decimal(str(raw["min"])),
                maximum=Decimal(str(raw["max"])),
                step=Decimal(str(raw["step"])),
            )
        raise SchemaError(f"unrecognised assumption format for {name!r}: {raw!r}")

    # scalar
    return Assumption(name, AssumptionKind.FIXED, Origin.CLAIMANT, value=Decimal(str(raw)))


def _make_canonical_params(params: Mapping[str, object]) -> Mapping[str, object]:
    """Return params with any Decimal string values kept as-is for canonicalisation."""
    return dict(params)


def freeze(claim_type: ClaimType, raw: Mapping[str, object]) -> IntakeResult:
    """Validate ``raw``, partition params/outcomes, resolve assumptions, compute spec_hash.

    Raises SchemaError, CanonicalizationError, or GridTooLargeError (from sweep).
    """
    # Basic structure checks
    if not isinstance(raw.get("params"), dict):
        raise SchemaError("params must be a dict")
    if not isinstance(raw.get("outcomes"), dict):
        raise SchemaError("outcomes must be a dict")

    raw_params = dict(raw["params"])
    raw_outcomes = dict(raw["outcomes"])

    # Ensure partition: outcomes must not appear in params
    param_keys = frozenset(raw_params.keys())
    extra_in_params = param_keys & outcome_fields_of(claim_type)
    if extra_in_params:
        raise SchemaError(f"outcome fields found in params: {extra_in_params}")

    # Validate via plugin
    claim_type.validate_params(raw_params)
    claim_type.validate_outcomes(raw_outcomes)

    # Parse assumptions
    raw_assumptions: dict = dict(raw.get("assumptions") or {})
    plugin_assumptions = claim_type.assumption_specs(raw_assumptions)
    # Optional plugin hook: cross-check parameters against the resolved axes (e.g. a
    # parameter left unknown must have a swept axis of the same name).
    cross_check = getattr(claim_type, "validate_assumptions", None)
    if cross_check is not None:
        cross_check(raw_params, plugin_assumptions)

    # Validate grid size
    expand_grid(plugin_assumptions)  # raises GridTooLargeError if over cap

    # Compute tolerances
    tolerances = dict(claim_type.tolerances(raw_params, raw_outcomes))

    # Build assumption serialisable form for spec_hash (sort by name)
    assumptions_for_hash = _assumptions_to_hash_form(plugin_assumptions)

    # spec_hash covers: type, schema version, params, assumptions, tolerances (not outcomes)
    spec_payload = {
        "claim_type": claim_type.type_id,
        "schema_version": raw.get("schema_version", claim_type.schema_version),
        "params": raw_params,
        "assumptions": assumptions_for_hash,
        "tolerances": tolerances,
    }
    spec_hash = sha256_hex(canonical_bytes(spec_payload))

    frozen = FrozenClaim(
        claim_type=claim_type.type_id,
        schema_version=raw.get("schema_version", claim_type.schema_version),
        params=raw_params,
        assumptions=plugin_assumptions,
        tolerances=tolerances,
        spec_hash=spec_hash,
    )

    return IntakeResult(frozen=frozen, outcomes=raw_outcomes)


def outcome_fields_of(claim_type: ClaimType) -> frozenset[str]:
    return claim_type.outcome_fields


def _assumptions_to_hash_form(assumptions: tuple[Assumption, ...]) -> list[dict]:
    """Convert assumptions to a canonical hash-friendly form, sorted by name."""
    result = []
    for a in sorted(assumptions, key=lambda x: x.name):
        entry: dict = {
            "name": a.name,
            "kind": a.kind.value,
            "origin": a.origin.value,
        }
        if a.kind is AssumptionKind.FIXED:
            entry["value"] = format(a.value, "f") if isinstance(a.value, Decimal) else str(a.value) if a.value is not None else None
        elif a.kind is AssumptionKind.RANGE:
            entry["minimum"] = format(a.minimum, "f")
            entry["maximum"] = format(a.maximum, "f")
            entry["step"] = format(a.step, "f")
        elif a.kind is AssumptionKind.SET:
            entry["values"] = [
                format(v, "f") if isinstance(v, Decimal) else str(v)
                for v in a.values
            ]
        result.append(entry)
    return result


def blind(frozen: FrozenClaim, *, case_id: str, evidence_refs: Sequence[str] = ()) -> BlindedTask:
    """Build the Examiner task from a FrozenClaim only. The signature makes it impossible
    to pass outcomes (Req 2.2)."""
    return BlindedTask(
        case_id=case_id,
        claim_type=frozen.claim_type,
        schema_version=frozen.schema_version,
        spec_hash=frozen.spec_hash,
        params=frozen.params,
        assumptions=frozen.assumptions,
        evidence_refs=tuple(evidence_refs),
    )
