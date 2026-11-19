"""M3b intake boundary: strict, side-effect-free validation before custody.

This module does not persist cases or freeze outcomes. In particular, no request
is admitted to the examination path until encrypted custody is available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from verdictkit.plugin import Registry

_ALLOWED_TOP = frozenset({"claimType", "dataMode", "fixtureId", "form", "pastedText"})
_ALLOWED_FORM = frozenset({"params", "outcomes", "assumptions"})


class IntakeRejected(ValueError):
    """A submitted case violates the frozen HTTP intake boundary."""

    def __init__(self, code: str, message: str, field: str | None = None):
        self.code = code
        self.field = field
        super().__init__(message)


def _json_safe(value: Any, *, path: str = "form") -> None:
    """Reject floats, arbitrary Python objects and non-string map keys.

    The forensic core uses decimal strings; float conversion would destroy
    information before canonicalization.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        raise IntakeRejected("SCHEMA_INVALID", "Decimal values must be strings", path)
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_safe(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise IntakeRejected("SCHEMA_INVALID", "Object keys must be strings", path)
            _json_safe(item, path=f"{path}.{key}")
        return
    raise IntakeRejected("SCHEMA_INVALID", "Unsupported JSON value", path)


@dataclass(frozen=True)
class PreparedIntake:
    """Private custodian-side preparation. NEVER serialize this object directly.

    `raw_claim` contains asserted outcomes; the API may only return the
    allowlisted `outcome_fields` projection until the verdict join.
    """
    claim_type: str
    data_mode: str
    raw_claim: Mapping[str, object] = field(repr=False)
    outcome_fields: tuple[dict[str, object], ...]
    # Draft-response-only provenance for text-derived parameters. The pasted text
    # itself is never stored here, persisted, logged, frozen or bundled.
    text_spans: Mapping[str, tuple[int, int]] = field(default_factory=dict, repr=False)


def prepare_intake(payload: Mapping[str, object], registry: Registry) -> PreparedIntake:
    """Validate live form intake without creating a case or exposing outcomes.

    Synthetic claims require a trusted bundled fixture loader and are refused
    here rather than accepting client-selected fixture IDs. Pasted Reel claims
    require transient privacy-safe parsing and are likewise not enabled here.
    """
    if not isinstance(payload, dict):
        raise IntakeRejected("SCHEMA_INVALID", "Object required", None)
    extra = set(payload) - _ALLOWED_TOP
    if extra:
        raise IntakeRejected("SCHEMA_INVALID", "Unknown intake field", sorted(extra)[0])
    claim_id = payload.get("claimType")
    if not isinstance(claim_id, str) or claim_id not in registry.type_ids():
        raise IntakeRejected("SCHEMA_INVALID", "Unknown claim type", "claimType")
    mode = payload.get("dataMode")
    if mode not in ("LIVE_EVIDENCE", "SYNTHETIC_DEMO"):
        raise IntakeRejected("SCHEMA_INVALID", "Unknown data mode", "dataMode")
    if mode == "SYNTHETIC_DEMO":
        raise IntakeRejected(
            "POLICY_VIOLATION", "Synthetic intake requires a verified bundled fixture", "fixtureId"
        )
    if payload.get("fixtureId") is not None:
        raise IntakeRejected("SCHEMA_INVALID", "Fixture forbidden in live mode", "fixtureId")
    plugin = registry.get(claim_id)
    form = payload.get("form")
    if form is None and payload.get("pastedText") is not None:
        form = {"params": {}, "outcomes": {}}
    if not isinstance(form, dict) or set(form) - _ALLOWED_FORM:
        raise IntakeRejected("SCHEMA_INVALID", "Invalid form object", "form")
    params = form.get("params")
    outcomes = form.get("outcomes")
    assumptions = form.get("assumptions", {})
    if not isinstance(params, dict) or not isinstance(outcomes, dict) or not isinstance(assumptions, dict):
        raise IntakeRejected("SCHEMA_INVALID", "params, outcomes and assumptions must be objects", "form")
    _json_safe(form)
    spans: dict[str, tuple[int, int]] = {}
    text = payload.get("pastedText")
    if text is not None:
        hook = getattr(plugin, "extract_text", None)
        if hook is None:
            raise IntakeRejected("SCHEMA_INVALID", "Claim type does not accept pasted text", "pastedText")
        if not isinstance(text, str) or len(text) > 2000:
            raise IntakeRejected("SCHEMA_INVALID", "pastedText must be at most 2000 characters", "pastedText")
        try:
            t_params, t_outcomes, spans = hook(text)
        except ValueError as exc:
            if str(exc).startswith("privacy:"):
                raise IntakeRejected("PRIVACY_REJECTED",
                                     "Pasted text contains a URL, handle, email or phone number",
                                     "pastedText") from None
            raise IntakeRejected("SCHEMA_INVALID", "Pasted text could not be parsed", "pastedText") from None
        # Explicit form values (basis USER_FORM) take precedence over extracted text.
        merged = dict(t_params)
        merged.update({k: v for k, v in params.items() if v is not None})
        spans = {k: v for k, v in spans.items() if params.get(k) is None}
        params = merged
        outcomes = {**t_outcomes, **outcomes}
        del text
    if set(params) & set(plugin.outcome_fields):
        raise IntakeRejected("SCHEMA_INVALID", "Asserted outcome placed in parameters", "form.params")
    if set(params) - set(plugin.param_fields):
        raise IntakeRejected("SCHEMA_INVALID", "Unknown parameter", "form.params")
    incomplete = any(v is None for v in params.values())
    try:
        # A draft may be incomplete; MISSING parameters become blockers that refuse the
        # freeze. Complete drafts are validated in full at intake.
        if not incomplete:
            plugin.validate_params(params)
        if outcomes:
            plugin.validate_outcomes(outcomes)
        elif not incomplete:
            plugin.validate_outcomes(outcomes)
        plugin.assumption_specs(assumptions)
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        # Deliberately do not return exception text (may contain outcome values).
        raise IntakeRejected("SCHEMA_INVALID", "Claim validation rejected the form", "form") from exc
    raw = {
        "claim_type": claim_id,
        "schema_version": plugin.schema_version,
        "params": dict(params),
        "outcomes": dict(outcomes),
        "assumptions": dict(assumptions),
    }
    fields = tuple(
        {"name": name, "captured": name in outcomes and outcomes[name] is not None}
        for name in sorted(plugin.outcome_fields)
    )
    return PreparedIntake(claim_id, mode, raw, fields, spans)
