"""Custodian run stage for the HTTP case lifecycle (core req 13.5, API contract §7).

Order, enforced by the ledger state machine:
  EVIDENCE_ACQUIRED -> blind task -> isolated examination -> EXAMINATION_COMMITTED
  -> reveal + commitment check (OUTCOMES_REVEALED) -> findings -> VERDICT_SEALED
  -> [DIAGNOSTICS_APPENDED] -> bundle (BUNDLE_WRITTEN)

Every progress event is persisted to the run record *before* it can be emitted
(write-then-emit); the SSE endpoint only ever reads the persisted record. Asserted
outcomes are decrypted in the custodian and handed to the comparator only after
the examination result is committed; they never enter the blinded task.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping, Sequence

from verdictkit.bundle import write_bundle
from verdictkit.canonical import canonical_bytes, sha256_hex
from verdictkit.custody.comparator import compare_and_seal
from verdictkit.custody.intake import blind, freeze
from verdictkit.custody.ledger import EntryKind, Ledger
from verdictkit.model import (
    AssumptionKind, Commitment, DataMode, Finding, FrozenClaim, IsolationMode, Origin,
    Status,
)
from verdictkit.pipeline import CaseFile
from verdictkit.plugin import ClaimType, Examination, Registry, examination_payload
from verdictkit.sweep import GRID_CAP_MAX, PointOutcome, expand_grid

from .draft_store import DraftStore
from .examination_boundary import ExaminationRejected, require_isolated_examiner
from .presenter import (
    CONTRACT_VERSION, check_key_records, evidence_dto, outcome_response, sensitivity_dto,
    specimen_dto,
)
from verdictkit.evidence.store import EvidenceStore
from verdictkit.model import EvidenceItem, LicenseClass, SourceClass
from verdictkit.pipeline import EMBEDDABLE

DEFAULT_RIGHTS_NOTE = "Recorded with its licence class; see the evidence index in the bundle."


def item_from_dict(d: Mapping[str, Any]) -> EvidenceItem:
    return EvidenceItem(source_id=d["source_id"], source_class=SourceClass(d["source_class"]),
                        uri=d["uri"], retrieved_at=d["retrieved_at"], sha256=d["sha256"],
                        media_type=d["media_type"], license_class=LicenseClass(d["license_class"]))


def item_to_dict(item: EvidenceItem) -> dict[str, str]:
    return {"source_id": item.source_id, "source_class": item.source_class.value,
            "uri": item.uri, "retrieved_at": item.retrieved_at, "sha256": item.sha256,
            "media_type": item.media_type, "license_class": item.license_class.value}


def evidence_dtos(plugin: ClaimType, items: Sequence[EvidenceItem]) -> list[dict[str, object]]:
    notes = {a.source_id: getattr(a, "rights_note", None)
             for a in getattr(plugin, "evidence_adapters", lambda: ())()}
    out = []
    for item in items:
        dto = evidence_dto(item, rights_note=notes.get(item.source_id) or DEFAULT_RIGHTS_NOTE,
                           embedded=item.license_class in EMBEDDABLE)
        if dto["origin"] == "SYNTHETIC_FIXTURE":
            dto["uri"] = None  # packaged fixture, not a fetchable location
        out.append(dto)
    return out

# Claim types that the 1.1.0 HTTP contract can represent (ClaimTypeId enum).
CONTRACT_CLAIM_TYPES = frozenset({"reel.mechanical.v1", "quote.finance.v1", "quote.lease.v1"})

# Dependency order of findings for point-of-failure marking (quote design).
_DEPENDENCY_ORDER = {
    "quote.finance.v1": ("taxable_base", "sales_tax", "amount_financed", "monthly_payment",
                         "total_of_payments", "finance_charge", "tax_rate", "doc_fee_cap"),
    "quote.lease.v1": ("depreciation_fee", "rent_charge", "base_payment", "monthly_tax",
                       "total_monthly_payment", "tax_rate"),
}

_LEDGER_STAGES = {
    EntryKind.EXAMINATION_COMMITTED: "EXAMINATION_COMMITTED",
    EntryKind.OUTCOMES_REVEALED: "OUTCOMES_REVEALED",
    EntryKind.VERDICT_SEALED: "VERDICT_SEALED",
    EntryKind.DIAGNOSTICS_APPENDED: "DIAGNOSTICS_APPENDED",
    EntryKind.BUNDLE_WRITTEN: "BUNDLE_WRITTEN",
}

_PASSING = frozenset({Status.CONSISTENT, Status.SUPPORTED, Status.WITHIN_BOUND})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _RevealedDraft:
    """Vault adapter: the comparator unseals only after EXAMINATION_COMMITTED."""

    def __init__(self, outcomes: Mapping[str, object]) -> None:
        self._outcomes = dict(outcomes)

    def unseal(self, _ref: object) -> Mapping[str, object]:
        return dict(self._outcomes)


def _decimal_string(value: object) -> str | None:
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not d.is_finite():
        return None
    return format(d, "f")


def parameter_ledger(plugin: ClaimType, raw: Mapping[str, Any], confirmed: Sequence[str],
                     frozen: FrozenClaim | None = None, *, text_fields: Sequence[str] = (),
                     spans: Mapping[str, tuple[int, int]] | None = None) -> list[dict[str, object]]:
    """Parameter ledger (API contract §5). Values only from parameters/assumptions.

    ``spans`` is supplied only for the intake response; after freeze every span is null."""
    params = raw.get("params") or {}
    confirmed_set = set(confirmed)
    text_set = set(text_fields)
    spans = spans if frozen is None else None
    if frozen is not None:
        assumptions = tuple(frozen.assumptions)
    else:
        try:
            assumptions = tuple(plugin.assumption_specs(dict(raw.get("assumptions") or {})))
        except Exception:
            assumptions = ()
    axis_names = {a.name for a in assumptions}
    entries: list[dict[str, object]] = []
    for name, value in sorted(params.items()):
        if value is None and name in axis_names:
            continue  # unknown fact: reported below as an ASSUMED, swept assumption
        if value is None:
            entries.append({"name": name, "value": None, "state": "MISSING",
                            "sourceSpan": None, "basis": "NONE", "critical": True})
            continue
        if isinstance(value, str):
            text = value
        else:
            text = canonical_bytes(value).decode("utf-8")
        if name in confirmed_set:
            basis, span = "USER_CONFIRMED", None
        elif name in text_set:
            basis = "CLAIMANT_TEXT"
            span = None
            if spans and name in spans:
                span = {"start": spans[name][0], "end": spans[name][1]}
        else:
            basis, span = "USER_FORM", None
        entries.append({"name": name, "value": text, "state": "SPECIFIED",
                        "sourceSpan": span, "basis": basis, "critical": False})
    if assumptions:
        for a in sorted(assumptions, key=lambda x: x.name):
            if a.kind is AssumptionKind.MISSING:
                entries.append({"name": a.name, "value": None, "state": "MISSING",
                                "sourceSpan": None, "basis": "NONE", "critical": False})
                continue
            rng: dict[str, object] | None = None
            value: str | None = None
            if a.kind is AssumptionKind.FIXED:
                value = _decimal_string(a.value)
            elif a.kind is AssumptionKind.RANGE:
                rng = {"kind": "RANGE", "min": format(a.minimum, "f"),
                       "max": format(a.maximum, "f"), "step": format(a.step, "f")}
            else:
                rng = {"kind": "SET", "values": [format(v, "f") for v in a.values]}
            if a.origin is Origin.DEFAULT_POLICY:
                state, basis = "ASSUMED", "DEFAULT_POLICY"
            else:
                state = "SPECIFIED"
                basis = "USER_CONFIRMED" if a.origin is Origin.USER_CONFIRMED else "USER_FORM"
            entry: dict[str, object] = {"name": a.name, "value": value, "state": state,
                                        "sourceSpan": None, "basis": basis, "critical": False}
            if rng is not None:
                entry["range"] = rng
            entries.append(entry)
    return entries


def _sensitivity(frozen: FrozenClaim, examination: Examination,
                 findings: Sequence[Finding], plugin: ClaimType | None = None,
                 outcomes: Mapping[str, object] | None = None) -> dict[str, object] | None:
    if not examination.points:
        return None
    grid = expand_grid(frozen.assumptions)
    origins = {a.name: a.origin.value for a in frozen.assumptions}
    axes = []
    for name in sorted({k for p in grid.points for k in p}):
        values: list[str] = []
        for p in grid.points:
            if name in p and p[name] not in values:
                values.append(p[name])
        axes.append({"name": name, "values": values, "origin": origins.get(name, "CLAIMANT")})
    point_outcomes: dict[str, list[PointOutcome]] = {}
    hook = getattr(plugin, "point_outcomes", None) if plugin is not None else None
    if hook is not None and outcomes is not None:
        determinate = {f.finding_id for f in findings if f.status is not Status.INDETERMINATE}
        point_outcomes = {k: list(v) for k, v in hook(frozen, examination, outcomes).items()
                          if k in determinate and v}
    elif len(examination.points) == 1:
        point = examination.points[0].point
        for f in findings:
            if f.status is Status.INDETERMINATE:
                continue
            diff = _decimal_string(f.numbers.get("difference"))
            tol = _decimal_string(f.numbers.get("tolerance"))
            if diff is None or tol is None:
                continue
            margin = Decimal(tol) - abs(Decimal(diff))
            point_outcomes[f.finding_id] = [PointOutcome(dict(point), f.status in _PASSING, margin)]
    return sensitivity_dto(
        examination=examination,
        template_version=f"{frozen.claim_type}/sweep-v1",
        grid_cap=GRID_CAP_MAX,
        axes=axes,
        point_outcomes=point_outcomes,
    )


def _key_records(claim_type: str, findings: Sequence[Finding]) -> tuple[list[dict], dict[str, list[str]], str | None]:
    """WORKSHEET_LINE / GRID_POINT records derived from counterexamples.

    Only the first non-consistent finding in dependency order (the point of failure)
    carries a COUNTEREXAMPLE; propagated findings' lines are ILLUSTRATIVE (quote design).
    """
    order = _DEPENDENCY_ORDER.get(claim_type)
    ranked = sorted(findings, key=lambda f: order.index(f.finding_id)
                    if order and f.finding_id in order else len(order or ()))
    failing = [f for f in ranked if f.status not in _PASSING and f.status is not Status.INDETERMINATE]
    point_of_failure = failing[0].finding_id if failing and order else None
    kind = "WORKSHEET_LINE" if claim_type.startswith("quote.") else "GRID_POINT"
    records: list[dict] = []
    ids: dict[str, list[str]] = {}
    for f in ranked:
        for i, cex in enumerate(f.counterexamples):
            rid = f"kr_{f.finding_id}_{i}"
            role = "COUNTEREXAMPLE"
            if point_of_failure is not None and f.finding_id != point_of_failure:
                role = "ILLUSTRATIVE"
            payload = {"point": dict(cex.point), "expected": _decimal_string(cex.expected),
                       "observed": _decimal_string(cex.observed),
                       "difference": _decimal_string(cex.difference),
                       "tolerance": _decimal_string(cex.tolerance)}
            note = cex.note or "Counterexample"
            if role == "ILLUSTRATIVE":
                note = f"Propagated from {point_of_failure}: {note}"
            records.append({"recordId": rid, "findingId": f.finding_id, "recordRole": role,
                            "recordKind": kind, "payload": payload, "note": note})
            ids.setdefault(f.finding_id, []).append(rid)
    check_key_records(records, findings)
    return records, ids, point_of_failure


def build_outcome(*, case_id: str, run_id: str, plugin: ClaimType, raw: Mapping[str, Any],
                  confirmed: Sequence[str], frozen: FrozenClaim, frozen_at: str | None,
                  data_mode: DataMode, isolation: str, examination: Examination,
                  findings: Sequence[Finding], diagnostics: Mapping[str, object] | None,
                  verdict_hash: str, text_fields: Sequence[str] = (),
                  evidence: Sequence[EvidenceItem] = (), fixture_id: str | None = None,
                  outcomes: Mapping[str, object] | None = None) -> dict[str, object]:
    records, record_ids, point_of_failure = _key_records(frozen.claim_type, findings)
    body = outcome_response(
        case_id=case_id, run_id=run_id, claim_type=frozen.claim_type, data_mode=data_mode,
        isolation_mode=isolation, findings=findings, blockers=[],
        parameter_ledger=parameter_ledger(plugin, raw, confirmed, frozen,
                                          text_fields=text_fields),
        evidence=evidence_dtos(plugin, evidence), key_records=records, diagnostics=diagnostics,
        spec_hash=frozen.spec_hash, verdict_hash=verdict_hash,
        grid_points=len(examination.points),
        specimen=specimen_dto(frozen, claim_type=frozen.claim_type, data_mode=data_mode,
                              fixture_id=fixture_id, case_id=case_id, frozen_at=frozen_at),
        sensitivity=_sensitivity(frozen, examination, findings, plugin, outcomes),
    )
    seen_failure = False
    for dto in body["findings"]:
        dto["keyRecordIds"] = record_ids.get(dto["findingId"], [])
        for key in ("expected", "observed", "difference", "tolerance"):
            dto["numbers"][key] = _decimal_string(dto["numbers"][key])
        if point_of_failure is not None:
            is_pof = dto["findingId"] == point_of_failure
            dto["pointOfFailure"] = is_pof
            dto["propagated"] = seen_failure and dto["status"] not in ("CONSISTENT", "INDETERMINATE")
            seen_failure = seen_failure or is_pof
    return body


def blocked_outcome(*, case_id: str, plugin: ClaimType, raw: Mapping[str, Any],
                    confirmed: Sequence[str], data_mode: DataMode, isolation: str,
                    spec_hash: str | None, frozen_at: str | None,
                    blockers: Sequence[Mapping[str, object]],
                    text_fields: Sequence[str] = (), fixture_id: str | None = None) -> dict[str, object]:
    frozen = None
    try:
        frozen = freeze(plugin, raw).frozen
    except Exception:
        frozen = None
    return outcome_response(
        case_id=case_id, run_id=None, claim_type=plugin.type_id, data_mode=data_mode,
        isolation_mode=isolation, findings=[], blockers=blockers,
        parameter_ledger=[{**e, "sourceSpan": None} for e in
                          parameter_ledger(plugin, raw, confirmed, frozen, text_fields=text_fields)],
        evidence=[], key_records=[], diagnostics=None, spec_hash=spec_hash,
        verdict_hash=None, grid_points=0,
        specimen=specimen_dto(frozen, claim_type=plugin.type_id, data_mode=data_mode,
                              fixture_id=fixture_id, case_id=case_id, frozen_at=frozen_at),
        sensitivity=None,
    )


class RunFailed(RuntimeError):
    """Infrastructure failure: run state FAILED + HTTP 5xx (API contract §2)."""


def execute_run(*, store: DraftStore, registry: Registry, examiner: Any, case_id: str,
                run_id: str, judge_mode: bool, clock: Callable[[], str] = utc_now,
                evidence_dir: Any = None) -> str:
    """Execute a queued run to a terminal state. Returns the terminal run state."""
    seq = 0

    def emit(stage: str, *, ledger_entry=None, detail: dict | None = None,
             state: str | None = None) -> None:
        nonlocal seq
        event = {
            "contractVersion": CONTRACT_VERSION, "runId": run_id, "seq": seq, "stage": stage,
            "at": clock(),
            "ledgerSeq": None if ledger_entry is None else ledger_entry.seq,
            "ledgerKind": None if ledger_entry is None else ledger_entry.kind.value,
            "detail": detail or {},
        }
        store.append_run_event(run_id, event, state=state)  # write ...
        seq += 1                                             # ... then it may be emitted

    try:
        emit("RUN_QUEUED", state="RUNNING")
        metadata = store.get_metadata(case_id)
        plugin = registry.get(metadata["claimType"])
        data_mode = DataMode(metadata["dataMode"])
        raw = store.load_private(case_id)
        confirmed = store.get_confirmed(case_id)
        result = freeze(plugin, raw)
        frozen = result.frozen
        if frozen.spec_hash != metadata["specHash"]:
            raise RunFailed("frozen specification changed after freeze")
        salt, commitment_d, entries = store.load_custody(case_id)
        commitment = Commitment(alg=commitment_d["alg"], digest=commitment_d["digest"])
        ledger = Ledger.from_entries(entries, clock)

        evidence = tuple(item_from_dict(d) for d in store.get_evidence(case_id))
        blobs: dict[str, bytes] = {}
        if evidence:
            if evidence_dir is None:
                raise RunFailed("evidence store not configured")
            ev_store = EvidenceStore(evidence_dir)
            for item in evidence:  # hash-checked before anything reaches the examiner
                data = ev_store.get(item.sha256)
                if item.license_class in EMBEDDABLE:
                    blobs[item.sha256] = data

        require_isolated_examiner(examiner.isolation, judge_mode=judge_mode)
        task = blind(frozen, case_id=case_id, evidence_refs=tuple(e.sha256 for e in evidence))
        emit("TASK_BLINDED")
        total = max(1, len(expand_grid(frozen.assumptions).points))
        emit("EXAMINATION_STARTED", detail={"pointsDone": 0, "pointsTotal": total})
        examination = examiner.examine(task)
        if examination.spec_hash != frozen.spec_hash:
            raise RunFailed("examiner returned a different specification")
        emit("EXAMINATION_PROGRESS", detail={"pointsDone": len(examination.points),
                                             "pointsTotal": total})
        committed = ledger.append(EntryKind.EXAMINATION_COMMITTED, {
            "spec_hash": examination.spec_hash,
            "examination_hash": sha256_hex(canonical_bytes(examination_payload(examination))),
        })
        emit("EXAMINATION_COMMITTED", ledger_entry=committed)

        before = len(ledger.entries)
        sealed = compare_and_seal(
            claim_type=plugin, frozen=frozen, examination=examination, evidence=evidence,
            vault=_RevealedDraft(result.outcomes), sealed=None, commitment=commitment,
            salt=salt, ledger=ledger, data_mode=data_mode,
        )
        for entry in ledger.entries[before:]:
            emit(_LEDGER_STAGES[entry.kind], ledger_entry=entry)

        case = CaseFile(
            case_id=case_id, isolation=examiner.isolation, data_mode=data_mode, frozen=frozen,
            commitment=commitment, salt=salt, outcomes=sealed.outcomes, evidence=evidence,
            examination=examination, verdict=sealed.verdict, diagnostics=sealed.diagnostics,
            ledger=ledger, evidence_blobs=blobs,
        )
        path = store.bundle_path(case_id)
        tmp = path.with_suffix(".tmp")
        write_bundle(case, tmp, clock=clock)
        tmp.chmod(0o600)
        tmp.replace(path)
        emit("BUNDLE_WRITTEN", ledger_entry=ledger.entries[-1])
        bundle_sha = hashlib.sha256(path.read_bytes()).hexdigest()

        frozen_at = store.get_freeze(case_id)["frozenAt"]
        outcome = build_outcome(
            case_id=case_id, run_id=run_id, plugin=plugin, raw=raw, confirmed=confirmed,
            frozen=frozen, frozen_at=frozen_at, data_mode=data_mode,
            isolation=examiner.isolation.value, examination=examination,
            findings=sealed.verdict.findings, diagnostics=sealed.diagnostics,
            verdict_hash=sealed.verdict.verdict_hash,
            text_fields=store.get_text_fields(case_id),
            evidence=evidence, fixture_id=metadata.get("fixtureId"),
            outcomes=sealed.outcomes,
        )
        state = "COMPLETED" if outcome["executionStatus"] == "COMPLETED" else "INDETERMINATE"
        emit("RUN_COMPLETED" if state == "COMPLETED" else "RUN_INDETERMINATE", state=state)
        store.finish_run(run_id, state=state, finished_at=clock(), outcome=outcome,
                         bundle_sha256=bundle_sha)
        return state
    except Exception:
        # Never surface exception text: it may include asserted outcomes or paths.
        try:
            emit("RUN_FAILED", state="FAILED")
        finally:
            store.finish_run(run_id, state="FAILED", finished_at=clock(), outcome=None,
                             bundle_sha256=None)
        return "FAILED"


__all__ = ["CONTRACT_CLAIM_TYPES", "ExaminationRejected", "IsolationMode", "RunFailed",
           "blocked_outcome", "build_outcome", "execute_run", "parameter_ledger", "utc_now"]
