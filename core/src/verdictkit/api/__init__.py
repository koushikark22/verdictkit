"""FastAPI app factory shared by both applications (core task 14.1).

create_app(registry, *, judge_mode: bool) -> FastAPI
Judge mode: no auth, per-IP rate limit, 256 KiB body cap, 24 h case TTL, refuses to start
unless the examiner reports IsolationMode.ENFORCED (Req 4.6, 12.2).
"""
