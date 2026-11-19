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
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .draft_store import DraftNotFound, DraftStore
from .intake_boundary import IntakeRejected, prepare_intake

VERSION = "1.1.0"
MAX_JSON = 256 * 1024
MAX_BUNDLE = 8 * 1024 * 1024
LOCKED = "HTTP_WORKFLOW_NOT_YET_IMPLEMENTED"


def error(code: str, message: str, status: int, field: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "field": field}})


def _isolation(judge_mode: bool) -> str:
    from .__main__ import _isolation_check
    result = _isolation_check()
    if judge_mode:
        # Env alone must never be accepted as proof of distinct OS identities.
        path = os.environ.get("VK_EXAMINER_SOCKET")
        if (sys.platform == "win32" or not path or not os.path.exists(path)
                or not stat.S_ISSOCK(os.stat(path).st_mode) or result != "ENFORCED"):
            raise RuntimeError("judge mode requires a live UNIX examiner socket and ENFORCED isolation")
    return result


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
            raw = bytes(data)
            async def receive() -> dict[str, object]:
                return {"type": "http.request", "body": raw, "more_body": False}
            request._receive = receive
        response = await call_next(request)
        response.headers["X-VerdictKit-Contract"] = VERSION
        response.headers["Cache-Control"] = "no-store"
        return response


def create_app(registry: Any = None, *, judge_mode: bool = False) -> FastAPI:
    isolation = _isolation(judge_mode)
    if registry is None:
        from verdictkit.cli import _load_registry
        registry = _load_registry()
    app = FastAPI(title="VerdictKit", version=VERSION, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(SafetyMiddleware)

    @app.get('/api/v1/health')
    def health() -> dict[str, object]:
        return {"contractVersion": VERSION, "status": "ok", "isolationMode": isolation,
                "judgeMode": judge_mode, "engineVersion": "0.1.0"}

    @app.get('/api/v1/claim-types')
    def claim_types() -> list[dict[str, object]]:
        return [{"claimType": tid, "schemaVersion": registry.get(tid).schema_version,
                 "outcomeFields": sorted(registry.get(tid).outcome_fields),
                 "acceptsPastedText": tid == "reel.mechanical.v1"}
                for tid in registry.type_ids()]

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
            "caseId": case_id,
            "claimType": metadata["claimType"],
            "state": "DRAFT",
            "dataMode": metadata["dataMode"],
            "isolationMode": isolation,
            "specHash": None,
            "latestRunId": None,
        }

    # Do not invent frozen hashes, SSE records or replay reports. These
    # operations stay closed until the real custodian state machine is integrated.
    @app.api_route('/api/v1/cases/{case_id}', methods=['PATCH'])
    @app.api_route('/api/v1/cases/{case_id}/freeze', methods=['POST'])
    @app.api_route('/api/v1/cases/{case_id}/evidence', methods=['GET', 'POST'])
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
