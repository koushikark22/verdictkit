"""M3a HTTP transport: contract-correct system routes, safety-locked case routes.

No case or verdict is fabricated here. The atomic run_case() pipeline must be
refactored behind the frozen multi-stage contract before case routes are enabled.
"""
from __future__ import annotations

import os
import socket
import stat
import sys
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

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

    # Do not invent drafts, frozen hashes, SSE records or replay reports. These
    # operations stay closed until the real custodian state machine is integrated.
    @app.api_route('/api/v1/cases', methods=['POST'])
    @app.api_route('/api/v1/cases/{case_id}', methods=['GET', 'PATCH'])
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
