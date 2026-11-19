"""M3a HTTP transport: contract-correct system routes, safety-locked case routes.

No case or verdict is fabricated here. The atomic run_case() pipeline must be
refactored behind the frozen multi-stage contract before case routes are enabled.
"""
from __future__ import annotations

import base64
import binascii
import os
import uuid
from datetime import datetime, timezone
import socket
import stat
import sys
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .draft_store import DraftNotFound, DraftStore, FreezeConflict
from .freeze_boundary import prepare_freeze
from .evidence_boundary import preflight_evidence
from .presenter import specimen_dto
from verdictkit.model import DataMode
from .intake_boundary import IntakeRejected, prepare_intake

VERSION = "1.1.0"
MAX_JSON = 256 * 1024
MAX_BUNDLE = 8 * 1024 * 1024
LOCKED = "HTTP_WORKFLOW_NOT_YET_IMPLEMENTED"


def error(code: str, message: str, status: int, field: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"contractVersion": VERSION, "error": {"code": code, "message": message, "field": field}})


def _isolation(judge_mode: bool) -> str:
    from .check_startup import startup_checks
    return startup_checks(force_judge=judge_mode)[1]


class SafetyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, per_minute: int = 120) -> None:
        super().__init__(app)
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.per_minute = per_minute

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
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
        return response


def create_app(registry: Any = None, *, judge_mode: bool = False) -> FastAPI:
    # The environment gate cannot be bypassed by the factory's default value.
    from .check_startup import startup_checks
    judge_mode, isolation = startup_checks(force_judge=judge_mode)
    if registry is None:
        from verdictkit.cli import _load_registry
        registry = _load_registry()
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

    @app.get('/api/v1/health')
    def health() -> dict[str, object]:
        return {"contractVersion": VERSION, "status": "ok", "isolationMode": isolation,
                "judgeMode": judge_mode, "engineVersion": "0.1.0"}

    @app.get('/api/v1/claim-types')
    def claim_types() -> dict[str, object]:
        return {"contractVersion": VERSION, "claimTypes": [
            {"claimType": tid, "schemaVersion": registry.get(tid).schema_version,
             "outcomeFields": sorted(registry.get(tid).outcome_fields),
             "acceptsPastedText": tid == "reel.mechanical.v1"}
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
            draft_store = DraftStore(draft_dir, key)
        except (binascii.Error, ValueError, OSError) as exc:
            raise RuntimeError("invalid draft custody configuration") from exc

    def _draft_response(case_id: str, raw: dict[str, object], expires_at: int) -> dict[str, object]:
        """Construct only the contract's pre-verdict, non-outcome projection."""
        plugin = registry.get(raw["claim_type"])
        params = raw["params"]
        if not isinstance(params, dict):
            raise RuntimeError("corrupted draft parameter structure")
        outcomes = raw["outcomes"]
        if not isinstance(outcomes, dict):
            raise RuntimeError("corrupted draft outcome structure")
        ledger = [
            {"name": name, "value": value if isinstance(value, str) else str(value),
             "state": "SPECIFIED", "sourceSpan": None, "basis": "USER_FORM",
             "critical": False}
            for name, value in sorted(params.items())
            if value is not None
        ]
        return {
            "contractVersion": VERSION,
            "caseId": case_id,
            "claimType": raw["claim_type"],
            "state": "DRAFT",
            "dataMode": "LIVE_EVIDENCE",
            "parameterLedger": ledger,
            "outcomeFields": [
                {"name": name, "captured": name in outcomes and outcomes[name] is not None}
                for name in sorted(plugin.outcome_fields)
            ],
            "blockers": [],
            "expiresAt": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        }

    @app.post('/api/v1/cases', status_code=201)
    async def create_case(request: Request) -> Any:
        if draft_store is None:
            return error(LOCKED, "Encrypted draft custody not configured", 503)
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
        return _draft_response(case_id, dict(prepared.raw_claim), metadata["expiresAt"])

    @app.get('/api/v1/cases/{case_id}')
    def get_case(case_id: str) -> Any:
        if draft_store is None:
            return error(LOCKED, "Encrypted draft custody not configured", 503)
        try:
            metadata = draft_store.get_metadata(case_id)
        except (DraftNotFound, ValueError):
            return error("NOT_FOUND", "Case unavailable", 404)
        return {
            "contractVersion": VERSION,
            "caseId": case_id,
            "claimType": metadata["claimType"],
            "state": metadata["state"],
            "dataMode": metadata["dataMode"],
            "isolationMode": isolation,
            "specHash": metadata["specHash"],
            "latestRunId": None,
        }


    @app.post('/api/v1/cases/{case_id}/freeze')
    def freeze_case(case_id: str) -> Any:
        if draft_store is None:
            return error(LOCKED, "Encrypted draft custody not configured", 503)
        try:
            metadata = draft_store.get_metadata(case_id)
        except (DraftNotFound, ValueError):
            return error("NOT_FOUND", "Case unavailable", 404)
        if metadata["state"] != "DRAFT":
            return error("STATE_CONFLICT", "Case is already frozen", 409)
        try:
            raw = draft_store.load_private(case_id)
            plugin = registry.get(metadata["claimType"])
            frozen_at = datetime.now(timezone.utc).isoformat()
            prepared = prepare_freeze(plugin, raw, case_id=case_id, clock=lambda: frozen_at)
        except (ValueError, TypeError, ArithmeticError, KeyError):
            # Never emit internal validation exceptions; they may contain outcomes.
            return error("SCHEMA_INVALID", "Claim cannot be frozen", 422)
        try:
            draft_store.freeze(case_id, prepared, frozen_at=frozen_at)
        except DraftNotFound:
            return error("NOT_FOUND", "Case unavailable", 404)
        except FreezeConflict:
            return error("STATE_CONFLICT", "Case is already frozen or changed", 409)
        stored = draft_store.get_freeze(case_id)
        ledger = _draft_response(case_id, raw, metadata["expiresAt"])["parameterLedger"]
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
                data_mode=DataMode(metadata["dataMode"]), fixture_id=None,
                case_id=case_id, frozen_at=stored["frozenAt"],
            ),
        }


    @app.post('/api/v1/cases/{case_id}/evidence')
    def acquire_case_evidence(case_id: str) -> Any:
        if draft_store is None:
            return error(LOCKED, "Encrypted draft custody not configured", 503)
        try:
            metadata = draft_store.get_metadata(case_id)
        except (DraftNotFound, ValueError):
            return error("NOT_FOUND", "Case unavailable", 404)
        if metadata["state"] != "FROZEN":
            return error("STATE_CONFLICT", "Frozen case required", 409)
        raw = draft_store.load_private(case_id)
        plugin = registry.get(metadata["claimType"])
        gate = preflight_evidence(plugin, raw["params"],
                                  data_mode=DataMode(metadata["dataMode"]))
        if not gate.allowed:
            return JSONResponse(status_code=422, content={
                "contractVersion": VERSION,
                "caseId": case_id, "executionStatus": "BLOCKED",
                "blockers": [gate.public_blocker()],
            })
        try:
            draft_store.acquire_internal_evidence(
                case_id, recorded_at=datetime.now(timezone.utc).isoformat())
        except DraftNotFound:
            return error("NOT_FOUND", "Case unavailable", 404)
        except FreezeConflict:
            return error("STATE_CONFLICT", "Evidence already committed", 409)
        return {"contractVersion": VERSION, "caseId": case_id, "evidence": []}

    @app.get('/api/v1/cases/{case_id}/evidence')
    def list_case_evidence(case_id: str) -> Any:
        if draft_store is None:
            return error(LOCKED, "Encrypted draft custody not configured", 503)
        try:
            return {"contractVersion": VERSION, "caseId": case_id, "evidence": draft_store.get_evidence(case_id)}
        except (DraftNotFound, ValueError):
            return error("NOT_FOUND", "Evidence not acquired", 404)

    # Do not invent SSE records or replay reports. These
    # operations stay closed until the real custodian state machine is integrated.
    @app.api_route('/api/v1/cases/{case_id}', methods=['PATCH'])
    @app.api_route('/api/v1/cases/{case_id}/runs', methods=['POST'])
    @app.api_route('/api/v1/cases/{case_id}/runs/{run_id}', methods=['GET'])
    @app.api_route('/api/v1/cases/{case_id}/runs/{run_id}/events', methods=['GET'])
    @app.api_route('/api/v1/cases/{case_id}/outcome', methods=['GET'])
    @app.api_route('/api/v1/cases/{case_id}/bundle', methods=['GET'])
    @app.api_route('/api/v1/cases/{case_id}/bundle/metadata', methods=['GET'])
    @app.api_route('/api/v1/replays', methods=['POST'])
    def disabled_workflow() -> JSONResponse:
        return error(LOCKED, "Multi-stage custody API is not integrated; operation refused", 503)

    return app
