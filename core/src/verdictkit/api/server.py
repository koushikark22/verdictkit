"""VerdictKit HTTP API (contract 1.1.0): intake -> freeze -> evidence -> run -> outcome
-> bundle -> replay. See docs/API_CONTRACT.md and api/openapi.yaml.

Asserted outcomes are write-only until the verdict join. Every case-route response is
contract-versioned; framework errors never leak unversioned bodies or exception text.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .draft_store import DraftNotFound, DraftStore, FreezeConflict
from .freeze_boundary import prepare_freeze
from .evidence_boundary import preflight_evidence
from .presenter import specimen_dto
from .run_service import (
    CONTRACT_CLAIM_TYPES, blocked_outcome, evidence_dtos, execute_run, item_from_dict,
    item_to_dict, parameter_ledger, utc_now,
)
from verdictkit.model import DataMode
from verdictkit.plugin import Registry
from .intake_boundary import IntakeRejected, _json_safe, prepare_intake

VERSION = "1.1.0"
MAX_JSON = 256 * 1024
MAX_BUNDLE = 8 * 1024 * 1024
CUSTODY_NOT_CONFIGURED = "CUSTODY_NOT_CONFIGURED"
_RUN_ID_CHARS = frozenset("0123456789abcdef")
_MAX_TRACKED_CLIENTS = 10000


def error(code: str, message: str, status: int, field: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"contractVersion": VERSION, "error": {"code": code, "message": message, "field": field}})


def blocked(case_id: str, blockers: list[dict]) -> JSONResponse:
    return JSONResponse(status_code=422, content={
        "contractVersion": VERSION, "caseId": case_id, "executionStatus": "BLOCKED",
        "blockers": blockers,
    })


def _isolation(judge_mode: bool) -> str:
    from .check_startup import startup_checks
    return startup_checks(force_judge=judge_mode)[1]


class SafetyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, per_minute: int = 120) -> None:
        super().__init__(app)
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.per_minute = per_minute

    def _prune(self, now: float) -> None:
        # Bound memory under many distinct client addresses.
        for ip in [ip for ip, h in self.hits.items() if not h or h[-1] <= now - 60]:
            del self.hits[ip]

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        if len(self.hits) > _MAX_TRACKED_CLIENTS:
            self._prune(now)
        hits = self.hits[ip]
        while hits and hits[0] <= now - 60:
            hits.popleft()
        if len(hits) >= self.per_minute:
            return error("RATE_LIMITED", "Request rate limit exceeded", 429)
        hits.append(now)
        if request.method in ("POST", "PATCH", "PUT"):
            cap = MAX_BUNDLE if request.url.path.endswith("/replays") else MAX_JSON
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > cap:
                        return error("BODY_TOO_LARGE", "Request body exceeds size limit", 413)
                except ValueError:
                    return error("SCHEMA_INVALID", "Invalid Content-Length", 400)
            # Safely enforce cap even with chunked requests.
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > cap:
                    return error("BODY_TOO_LARGE", "Request body exceeds size limit", 413)
            # BaseHTTPMiddleware passes a cached Request to downstream routes.
            # Replacing _receive directly loses the cached body on some Starlette
            # versions; use the cached body recognized by wrapped_receive.
            request._body = bytes(data)
        response = await call_next(request)
        response.headers["X-VerdictKit-Contract"] = VERSION
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


def _contract_registry(registry: Any) -> Registry:
    """Only claim types representable in the 1.1.0 contract are exposed over HTTP."""
    view = Registry()
    for tid in registry.type_ids():
        if tid in CONTRACT_CLAIM_TYPES:
            view.register(registry.get(tid))
    return view


def _make_examiner(isolation: str, registry: Any, evidence_dir: Any = None) -> Any:
    """ENFORCED: authenticated socket worker (peer UID checked on every connection).
    Otherwise an in-process examiner that is reported UNENFORCED everywhere."""
    from verdictkit.examiner.client import InProcessExaminer, SocketExaminer
    if isolation == "ENFORCED":
        from verdictkit.examiner.identity import resolve_examiner_uid
        return SocketExaminer(os.environ["VK_EXAMINER_SOCKET"],
                              expected_peer_uid=resolve_examiner_uid(""))
    return InProcessExaminer(registry, evidence_root=None if evidence_dir is None else str(evidence_dir))


def create_app(registry: Any = None, *, judge_mode: bool = False) -> FastAPI:
    # The environment gate cannot be bypassed by the factory's default value.
    from .check_startup import startup_checks
    judge_mode, isolation = startup_checks(force_judge=judge_mode)
    if registry is None:
        from verdictkit.cli import _load_registry
        registry = _load_registry()
    full_registry = registry
    registry = _contract_registry(full_registry)
    app = FastAPI(title="VerdictKit", version=VERSION, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(SafetyMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Never return the framework's unversioned {"detail": ...} object.
        if exc.status_code == 404:
            return error("NOT_FOUND", "Route unavailable", 404)
        if exc.status_code == 405:
            return error("METHOD_NOT_ALLOWED", "HTTP method unavailable", 405)
        return error("HTTP_ERROR", "Request rejected", exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return error("SCHEMA_INVALID", "Request validation failed", 422)

    @app.exception_handler(Exception)
    async def unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:
        # Fail closed without exception text (it may carry asserted outcomes).
        return error("INTERNAL_ERROR", "Internal error; request refused", 500)

    @app.get('/api/v1/health')
    def health() -> dict[str, object]:
        return {"contractVersion": VERSION, "status": "ok", "isolationMode": isolation,
                "judgeMode": judge_mode, "engineVersion": "0.1.0"}

    @app.get('/api/v1/claim-types')
    def claim_types() -> dict[str, object]:
        return {"contractVersion": VERSION, "claimTypes": [
            {"claimType": tid, "schemaVersion": registry.get(tid).schema_version,
             "outcomeFields": sorted(registry.get(tid).outcome_fields),
             "acceptsPastedText": callable(getattr(registry.get(tid), "extract_text", None))}
            for tid in registry.type_ids()
        ]}

    # Draft persistence is opt-in and requires a stable key supplied to the
    # custodian. Never invent a process-local encryption key: that would make
    # persisted claims undecryptable following a restart.
    draft_dir = os.environ.get("VK_DRAFT_DIR")
    vault_key = os.environ.get("VK_VAULT_KEY")
    draft_store = None
    if draft_dir and vault_key:
        try:
            key = base64.b64decode(vault_key, validate=True)
            draft_store = DraftStore(draft_dir, key, expire_frozen=judge_mode)
        except (binascii.Error, ValueError, OSError) as exc:
            raise RuntimeError("invalid draft custody configuration") from exc
    # Evidence written by the custodian and readable by the examiner. In the container
    # this is VK_EVIDENCE_DIR (0750, group vk-examiner); natively a custody subdirectory.
    evidence_dir = None
    if draft_store is not None:
        evidence_dir = Path(os.environ.get("VK_EVIDENCE_DIR") or Path(draft_dir) / "evidence")

    purge_state = {"at": 0.0}
    purge_lock = threading.Lock()

    def store() -> DraftStore | None:
        """Opportunistic TTL purge (judge mode removes frozen cases too; Req 12.2)."""
        if draft_store is not None:
            now = time.monotonic()
            with purge_lock:
                if now - purge_state["at"] >= 60:
                    purge_state["at"] = now
                    draft_store.purge_expired()
        return draft_store

    def unavailable() -> JSONResponse:
        return error(CUSTODY_NOT_CONFIGURED, "Encrypted case custody is not configured", 503)

    def _blockers_for(plugin: Any, raw: dict, confirmed: list[str]) -> list[dict]:
        out = []
        for entry in parameter_ledger(plugin, raw, confirmed):
            if entry["name"] in plugin.outcome_fields:
                continue
            if entry["state"] == "MISSING" and entry["critical"]:
                out.append({"code": "MISSING_CRITICAL_PARAMETER",
                            "message": "A required parameter is missing", "field": entry["name"]})
        return out

    def _draft_response(case_id: str, raw: dict[str, object], expires_at: int,
                        confirmed: list[str] | None = None, *, text_fields: list[str] | None = None,
                        spans: dict | None = None, data_mode: str = "LIVE_EVIDENCE") -> dict[str, object]:
        """Construct only the contract's pre-verdict, non-outcome projection."""
        plugin = registry.get(raw["claim_type"])
        params = raw["params"]
        if not isinstance(params, dict):
            raise RuntimeError("corrupted draft parameter structure")
        outcomes = raw["outcomes"]
        if not isinstance(outcomes, dict):
            raise RuntimeError("corrupted draft outcome structure")
        confirmed = confirmed or []
        return {
            "contractVersion": VERSION,
            "caseId": case_id,
            "claimType": raw["claim_type"],
            "state": "DRAFT",
            "dataMode": data_mode,
            "parameterLedger": parameter_ledger(plugin, raw, confirmed,
                                                text_fields=text_fields or [], spans=spans),
            "outcomeFields": [
                {"name": name, "captured": name in outcomes and outcomes[name] is not None}
                for name in sorted(plugin.outcome_fields)
            ],
            "blockers": _blockers_for(plugin, raw, confirmed),
            "expiresAt": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        }

    def _metadata(case_id: str) -> dict | None:
        try:
            return store().get_metadata(case_id)
        except (DraftNotFound, ValueError):
            return None

    @app.post('/api/v1/cases', status_code=201)
    async def create_case(request: Request) -> Any:
        if store() is None:
            return unavailable()
        try:
            payload = await request.json()
        except (ValueError, UnicodeDecodeError):
            return error("SCHEMA_INVALID", "Invalid JSON request body", 422)
        try:
            prepared = prepare_intake(payload, registry)
        except IntakeRejected as exc:
            return error(exc.code, str(exc), 422, exc.field)
        case_id = "case_" + uuid.uuid4().hex
        draft_store.create(case_id, prepared)
        metadata = draft_store.get_metadata(case_id)
        return _draft_response(case_id, dict(prepared.raw_claim), metadata["expiresAt"],
                               text_fields=sorted(prepared.text_spans),
                               spans=dict(prepared.text_spans), data_mode=prepared.data_mode)

    @app.get('/api/v1/cases/{case_id}')
    def get_case(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        metadata = _metadata(case_id)
        if metadata is None:
            return error("NOT_FOUND", "Case unavailable", 404)
        return {
            "contractVersion": VERSION,
            "caseId": case_id,
            "claimType": metadata["claimType"],
            "state": metadata["state"],
            "dataMode": metadata["dataMode"],
            "isolationMode": isolation,
            "specHash": metadata["specHash"],
            "latestRunId": metadata["latestRunId"],
        }

    @app.patch('/api/v1/cases/{case_id}')
    async def update_case(case_id: str, request: Request) -> Any:
        if store() is None:
            return unavailable()
        metadata = _metadata(case_id)
        if metadata is None:
            return error("NOT_FOUND", "Case unavailable", 404)
        if metadata["state"] != "DRAFT":
            return error("STATE_CONFLICT", "Only draft cases can be edited", 409)
        if metadata["dataMode"] != "LIVE_EVIDENCE":
            return error("POLICY_VIOLATION", "Bundled fixture claims cannot be edited", 422)
        try:
            update = await request.json()
        except (ValueError, UnicodeDecodeError):
            return error("SCHEMA_INVALID", "Invalid JSON request body", 422)
        if not isinstance(update, dict) or set(update) - {"params", "outcomes", "assumptions", "confirm"}:
            return error("SCHEMA_INVALID", "Invalid draft update", 422)
        confirm = update.get("confirm", [])
        if not isinstance(confirm, list) or any(not isinstance(c, str) for c in confirm) or len(confirm) > 100:
            return error("SCHEMA_INVALID", "confirm must be a list of parameter names", 422, "confirm")
        raw = draft_store.load_private(case_id)
        form = {"params": dict(raw["params"]), "outcomes": dict(raw["outcomes"]),
                "assumptions": dict(raw.get("assumptions") or {})}
        for key in ("params", "outcomes", "assumptions"):
            if key in update:
                if not isinstance(update[key], dict):
                    return error("SCHEMA_INVALID", f"{key} must be an object", 422, key)
                form[key].update(update[key])
        try:
            _json_safe(form)
            prepared = prepare_intake({"claimType": metadata["claimType"],
                                       "dataMode": metadata["dataMode"], "form": form}, registry)
        except IntakeRejected as exc:
            return error(exc.code, str(exc), 422, exc.field)
        if set(confirm) - set(form["params"]):
            return error("SCHEMA_INVALID", "Unknown parameter confirmed", 422, "confirm")
        confirmed = sorted(set(draft_store.get_confirmed(case_id)) | set(confirm))
        # A parameter edited in the form is no longer claimant text.
        text_fields = sorted(set(draft_store.get_text_fields(case_id)) - set(update.get("params", {})))
        try:
            draft_store.update_draft(case_id, dict(prepared.raw_claim), confirmed=confirmed)
            draft_store.set_text_fields(case_id, text_fields)
        except DraftNotFound:
            return error("NOT_FOUND", "Case unavailable", 404)
        except FreezeConflict:
            return error("STATE_CONFLICT", "Only draft cases can be edited", 409)
        return _draft_response(case_id, dict(prepared.raw_claim), metadata["expiresAt"],
                               confirmed, text_fields=text_fields)

    @app.post('/api/v1/cases/{case_id}/freeze')
    def freeze_case(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        metadata = _metadata(case_id)
        if metadata is None:
            return error("NOT_FOUND", "Case unavailable", 404)
        if metadata["state"] != "DRAFT":
            return error("STATE_CONFLICT", "Case is already frozen", 409)
        raw = draft_store.load_private(case_id)
        plugin = registry.get(metadata["claimType"])
        confirmed = draft_store.get_confirmed(case_id)
        pre = _blockers_for(plugin, raw, confirmed)
        if pre:
            draft_store.record_blockers(case_id, pre)
            return blocked(case_id, pre)
        from verdictkit.sweep import GridTooLargeError
        try:
            frozen_at = utc_now()
            prepared = prepare_freeze(plugin, raw, case_id=case_id, clock=lambda: frozen_at)
        except GridTooLargeError:
            b = [{"code": "GRID_TOO_LARGE", "message": "Assumption grid exceeds the cap",
                  "field": "assumptions"}]
            draft_store.record_blockers(case_id, b)
            return blocked(case_id, b)
        except (ValueError, TypeError, ArithmeticError, KeyError):
            # Never emit internal validation exceptions; they may contain outcomes.
            b = [{"code": "SCHEMA_INVALID", "message": "Claim cannot be frozen", "field": None}]
            draft_store.record_blockers(case_id, b)
            return blocked(case_id, b)
        try:
            draft_store.freeze(case_id, prepared, frozen_at=frozen_at)
        except DraftNotFound:
            return error("NOT_FOUND", "Case unavailable", 404)
        except FreezeConflict:
            return error("STATE_CONFLICT", "Case is already frozen or changed", 409)
        draft_store.record_blockers(case_id, [])
        stored = draft_store.get_freeze(case_id)
        ledger = parameter_ledger(plugin, raw, confirmed, prepared.frozen,
                                  text_fields=draft_store.get_text_fields(case_id))
        return {
            "contractVersion": VERSION,
            "caseId": case_id,
            "state": "FROZEN",
            "specHash": stored["specHash"],
            "commitment": stored["commitment"],
            "frozenAt": stored["frozenAt"],
            "ledgerSeq": stored["ledgerSeq"],
            "parameterLedger": ledger,
            "specimen": specimen_dto(
                prepared.frozen, claim_type=metadata["claimType"],
                data_mode=DataMode(metadata["dataMode"]), fixture_id=metadata["fixtureId"],
                case_id=case_id, frozen_at=stored["frozenAt"],
            ),
        }

    @app.post('/api/v1/cases/{case_id}/evidence')
    def acquire_case_evidence(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        metadata = _metadata(case_id)
        if metadata is None:
            return error("NOT_FOUND", "Case unavailable", 404)
        if metadata["state"] != "FROZEN":
            return error("STATE_CONFLICT", "Frozen case required", 409)
        raw = draft_store.load_private(case_id)
        plugin = registry.get(metadata["claimType"])
        mode = DataMode(metadata["dataMode"])
        gate = preflight_evidence(plugin, raw["params"], data_mode=mode,
                                  fixture_id=metadata["fixtureId"])
        if not gate.allowed:
            b = [gate.public_blocker()]
            draft_store.record_blockers(case_id, b)
            return blocked(case_id, b)
        items = []
        if gate.request_count:
            from verdictkit.evidence.broker import EvidenceBroker
            from verdictkit.evidence.policy import check as check_policy, effective_policy
            from verdictkit.evidence.store import EvidenceStore
            policy = effective_policy(plugin.evidence_policy(), mode)
            broker = EvidenceBroker(EvidenceStore(evidence_dir), list(plugin.evidence_adapters()),
                                    network=False, clock=utc_now)
            try:
                acquired = broker.acquire(plugin.evidence_requests(raw["params"]), policy)
            except Exception:
                b = [{"code": "EVIDENCE_UNAVAILABLE", "message": "Evidence could not be acquired",
                      "field": None}]
                draft_store.record_blockers(case_id, b)
                return blocked(case_id, b)
            if any(not check_policy(item, policy).allowed for item in acquired):
                b = [{"code": "POLICY_VIOLATION", "message": "Evidence class not permitted",
                      "field": None}]
                draft_store.record_blockers(case_id, b)
                return blocked(case_id, b)
            items = list(acquired)
        try:
            draft_store.acquire_evidence(case_id, [item_to_dict(i) for i in items],
                                         recorded_at=utc_now())
        except DraftNotFound:
            return error("NOT_FOUND", "Case unavailable", 404)
        except FreezeConflict:
            return error("STATE_CONFLICT", "Evidence already committed", 409)
        draft_store.record_blockers(case_id, [])
        return {"contractVersion": VERSION, "caseId": case_id,
                "evidence": evidence_dtos(plugin, items)}

    @app.get('/api/v1/cases/{case_id}/evidence')
    def list_case_evidence(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        metadata = _metadata(case_id)
        if metadata is None:
            return error("NOT_FOUND", "Case unavailable", 404)
        try:
            items = [item_from_dict(d) for d in draft_store.get_evidence(case_id)]
        except (DraftNotFound, ValueError):
            return error("NOT_FOUND", "Evidence not acquired", 404)
        return {"contractVersion": VERSION, "caseId": case_id,
                "evidence": evidence_dtos(registry.get(metadata["claimType"]), items)}

    run_lock = threading.Lock()

    def _run_urls(case_id: str, run_id: str) -> dict[str, str]:
        base = f"/api/v1/cases/{case_id}/runs/{run_id}"
        return {"eventsUrl": base + "/events", "runUrl": base}

    @app.post('/api/v1/cases/{case_id}/runs', status_code=202)
    def start_run(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        metadata = _metadata(case_id)
        if metadata is None:
            return error("NOT_FOUND", "Case unavailable", 404)
        existing = draft_store.get_run(case_id=case_id)
        if existing is not None:  # idempotent per case
            return JSONResponse(status_code=202, content={
                "contractVersion": VERSION, "runId": existing["runId"], "caseId": case_id,
                "state": existing["state"], **_run_urls(case_id, existing["runId"])})
        if metadata["state"] != "EVIDENCE_ACQUIRED":
            return error("STATE_CONFLICT", "Evidence must be acquired before a run", 409)
        run_id = "run_" + uuid.uuid4().hex
        with run_lock:
            if not draft_store.create_run(case_id, run_id, isolation=isolation,
                                          started_at=utc_now()):
                existing = draft_store.get_run(case_id=case_id)
                return JSONResponse(status_code=202, content={
                    "contractVersion": VERSION, "runId": existing["runId"], "caseId": case_id,
                    "state": existing["state"], **_run_urls(case_id, existing["runId"])})
        try:
            examiner = _make_examiner(isolation, full_registry, evidence_dir)
        except Exception:
            examiner = _Unavailable()
        state = execute_run(store=draft_store, registry=registry, examiner=examiner,
                            case_id=case_id, run_id=run_id, judge_mode=judge_mode,
                            evidence_dir=evidence_dir)
        if state == "FAILED":
            return error("RUN_FAILED", "Run failed; no verdict was produced", 500)
        return JSONResponse(status_code=202, content={
            "contractVersion": VERSION, "runId": run_id, "caseId": case_id, "state": state,
            **_run_urls(case_id, run_id)})

    def _valid_run_id(run_id: str) -> bool:
        return (isinstance(run_id, str) and len(run_id) == 36 and run_id.startswith("run_")
                and set(run_id[4:]) <= _RUN_ID_CHARS)

    def _run(case_id: str, run_id: str) -> dict | None:
        if not _valid_run_id(run_id) or _metadata(case_id) is None:
            return None
        run = draft_store.get_run(run_id=run_id)
        if run is None or run["caseId"] != case_id:
            return None
        return run

    @app.get('/api/v1/cases/{case_id}/runs/{run_id}')
    def get_run(case_id: str, run_id: str) -> Any:
        if store() is None:
            return unavailable()
        run = _run(case_id, run_id)
        if run is None:
            return error("NOT_FOUND", "Run unavailable", 404)
        return {"contractVersion": VERSION, "runId": run["runId"], "caseId": case_id,
                "state": run["state"], "isolationMode": run["isolationMode"],
                "startedAt": run["startedAt"], "finishedAt": run["finishedAt"],
                "events": run["events"]}

    @app.get('/api/v1/cases/{case_id}/runs/{run_id}/events')
    async def stream_events(case_id: str, run_id: str, request: Request) -> Any:
        if store() is None:
            return unavailable()
        if _run(case_id, run_id) is None:
            return error("NOT_FOUND", "Run unavailable", 404)
        last = request.headers.get("last-event-id")
        start = 0
        if last is not None:
            if not last.isascii() or not last.isdecimal() or len(last) > 9:
                return error("SCHEMA_INVALID", "Invalid Last-Event-ID", 422, "Last-Event-ID")
            start = int(last) + 1

        async def events() -> Any:
            sent = start
            deadline = time.monotonic() + 120
            while True:
                run = draft_store.get_run(run_id=run_id)  # only persisted events are sent
                if run is None:  # purged (TTL) while streaming
                    return
                for event in run["events"][sent:]:
                    yield f"id: {event['seq']}\nevent: progress\ndata: {json.dumps(event, sort_keys=True)}\n\n"
                    sent = event["seq"] + 1
                if run["finishedAt"] is not None or time.monotonic() > deadline:
                    return
                await asyncio.sleep(0.25)

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.get('/api/v1/cases/{case_id}/outcome')
    def get_outcome(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        metadata = _metadata(case_id)
        if metadata is None:
            return error("NOT_FOUND", "Case unavailable", 404)
        run = draft_store.get_run(case_id=case_id)
        if run is not None and run["outcome"] is not None:
            return run["outcome"]
        if run is not None and run["state"] == "FAILED":
            return error("RUN_FAILED", "Run failed; no verdict was produced", 500)
        if run is None:
            blockers = draft_store.get_blockers(case_id)
            if blockers:
                raw = draft_store.load_private(case_id)
                frozen_at = None
                if metadata["specHash"] is not None:
                    frozen_at = draft_store.get_freeze(case_id)["frozenAt"]
                return blocked_outcome(
                    case_id=case_id, plugin=registry.get(metadata["claimType"]), raw=raw,
                    confirmed=draft_store.get_confirmed(case_id),
                    data_mode=DataMode(metadata["dataMode"]), isolation=isolation,
                    spec_hash=metadata["specHash"], frozen_at=frozen_at, blockers=blockers,
                    text_fields=draft_store.get_text_fields(case_id),
                    fixture_id=metadata["fixtureId"])
        return error("TOO_EARLY", "No sealed verdict for this case yet", 425)

    def _bundle_file(case_id: str) -> tuple[Path, dict] | None:
        if _metadata(case_id) is None:
            return None
        run = draft_store.get_run(case_id=case_id)
        if run is None or run["bundleSha256"] is None:
            return None
        path = draft_store.bundle_path(case_id)
        if not path.is_file() or path.is_symlink():
            return None
        return path, run

    @app.get('/api/v1/cases/{case_id}/bundle')
    def export_bundle(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        found = _bundle_file(case_id)
        if found is None:
            return error("NOT_FOUND", "Bundle unavailable", 404)
        path, run = found
        data = path.read_bytes()
        import hashlib
        if hashlib.sha256(data).hexdigest() != run["bundleSha256"]:
            return error("BUNDLE_INTEGRITY", "Stored bundle failed its integrity check", 500)
        return Response(content=data, media_type="application/zip", headers={
            "Content-Disposition": f'attachment; filename="{case_id}.vkb"'})

    @app.get('/api/v1/cases/{case_id}/bundle/metadata')
    def bundle_metadata(case_id: str) -> Any:
        if store() is None:
            return unavailable()
        found = _bundle_file(case_id)
        if found is None:
            return error("NOT_FOUND", "Bundle unavailable", 404)
        path, run = found
        from verdictkit.bundle import AUTHENTICITY, integrity_dict, verify_bundle_integrity
        import hashlib
        import zipfile
        data = path.read_bytes()
        result, parts = verify_bundle_integrity(path)
        manifest = parts.get("manifest", {})
        fp = manifest.get("env_fingerprint", {}) if isinstance(manifest, dict) else {}
        embedded: list[str] = []
        refetch: list[dict] = []
        try:
            with zipfile.ZipFile(path) as zf:
                index = json.loads(zf.read("evidence/index.json"))
                names = set(zf.namelist())
            for item in index:
                eid = "ev_" + item["sha256"][:16]
                if f"evidence/blobs/{item['sha256']}" in names:
                    embedded.append(eid)
                elif item["license_class"] == "REFETCH_ONLY":
                    refetch.append({"evidenceId": eid, "uri": item["uri"],
                                    "snapshotHash": item["sha256"]})
        except (KeyError, ValueError, zipfile.BadZipFile):
            pass
        verdict_hash = manifest.get("verdict_hash") if isinstance(manifest, dict) else None
        return {
            "contractVersion": VERSION, "caseId": case_id,
            "bundleSha256": hashlib.sha256(data).hexdigest(), "sizeBytes": len(data),
            "engineVersion": str(manifest.get("engine_version", "unknown")),
            "envFingerprint": {
                "engineVersion": str(fp.get("engine_version", "unknown")),
                "pythonVersion": str(fp.get("python_version", "unknown")),
                "lockfileSha256": str(fp.get("lockfile_sha256", "unknown")),
                "imageDigest": str(fp.get("image_digest", "unknown")),
            },
            "isolationMode": manifest.get("isolation_mode", run["isolationMode"]),
            "embeddedEvidence": embedded, "refetchOnlyEvidence": refetch,
            "integrity": integrity_dict(result),
            "reproducibility": {"status": "NOT_RUN", "originalVerdictHash": verdict_hash,
                                "replayedVerdictHash": None, "envMatch": None},
            "authenticity": dict(AUTHENTICITY),
            "replayCommand": f"verdictkit replay {case_id}.vkb",
        }

    replay_slots = threading.BoundedSemaphore(2)

    @app.post('/api/v1/replays')
    async def replay_upload(request: Request) -> Any:
        body = await request.body()
        if not body:
            return error("SCHEMA_INVALID", "Bundle body required", 422)
        if not replay_slots.acquire(blocking=False):
            return error("RATE_LIMITED", "Replay capacity exhausted; retry later", 429)
        try:
            return await asyncio.to_thread(_replay, body)
        finally:
            replay_slots.release()

    def _replay(body: bytes) -> dict:
        from verdictkit.bundle import replay_bundle, replay_report_dict
        with tempfile.TemporaryDirectory(prefix="vk-replay-") as tmp:
            bundle = Path(tmp) / "upload.vkb"
            bundle.write_bytes(body)
            # Embedded evidence is hash-checked, then restored where the examiner can read
            # it: the shared evidence store when isolation is enforced (the worker reads
            # only VK_EVIDENCE_DIR), otherwise a private directory for this replay.
            replay_evidence = (evidence_dir if isolation == "ENFORCED" and evidence_dir is not None
                               else Path(tmp) / "work" / "evidence")
            try:
                examiner = _make_examiner(isolation, full_registry, replay_evidence)
            except Exception:
                examiner = _Unavailable()
            # No network: refetch is never permitted for uploaded bundles.
            report = replay_bundle(bundle, registry=full_registry, workdir=Path(tmp) / "work",
                                   allow_refetch=False, examiner=examiner,
                                   evidence_root=replay_evidence)
        return {"contractVersion": VERSION, **replay_report_dict(report)}

    return app


class _Unavailable:
    """Stands in when the isolated examiner cannot be reached: every use fails closed."""

    from verdictkit.model import IsolationMode as _IM
    isolation = _IM.UNENFORCED

    def examine(self, _task: Any) -> Any:
        raise RuntimeError("isolated examiner unavailable")
