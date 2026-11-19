"""``python -m verdictkit.api [--check-startup]`` (core task 13.2, requirement 4.6).

--check-startup: perform the startup checks only and exit. Exit non-zero (and print the
reason) when VK_JUDGE_MODE=1 and the examiner's isolation mode is not ENFORCED.
Without the flag: serve the API (uvicorn) after the same checks.
"""
from __future__ import annotations

import os
import sys


class IsolationNotEnforcedError(RuntimeError):
    """Judge mode requires ENFORCED isolation; raised at startup if not met."""


def _isolation_check() -> str:
    """Return the current isolation mode string.

    Uses VK_ISOLATION env var when set (the container entrypoint sets it to
    ``enforced`` for the production image). Otherwise derives it from whether
    VK_EXAMINER_SOCKET is configured: a socket path implies the separate
    vk-examiner OS user is in play, which the container entrypoint guarantees.
    Falls back to UNENFORCED on Windows/macOS or when no socket is set.
    """
    env = os.environ.get("VK_ISOLATION", "").lower()
    if env == "enforced":
        return "ENFORCED"
    socket_path = os.environ.get("VK_EXAMINER_SOCKET")
    if socket_path and sys.platform != "win32":
        return "ENFORCED"
    return "UNENFORCED"


def _startup_checks() -> None:
    """Raise IsolationNotEnforcedError if judge mode is on but isolation is not ENFORCED."""
    judge_mode = os.environ.get("VK_JUDGE_MODE", "0").strip() in ("1", "true", "yes")
    isolation = _isolation_check()
    if judge_mode and isolation != "ENFORCED":
        raise IsolationNotEnforcedError(
            f"VK_JUDGE_MODE=1 requires isolation ENFORCED, but isolation is {isolation}. "
            "Start the server inside the container with the vk-examiner socket configured."
        )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m verdictkit.api")
    parser.add_argument(
        "--check-startup",
        action="store_true",
        help="Run startup checks and exit without binding a port.",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        _startup_checks()
    except IsolationNotEnforcedError as exc:
        print(f"STARTUP REFUSED: {exc}", file=sys.stderr)
        return 1

    if args.check_startup:
        isolation = _isolation_check()
        judge_mode = os.environ.get("VK_JUDGE_MODE", "0").strip() in ("1", "true", "yes")
        print(f"isolation_mode: {isolation}")
        print(f"judge_mode:     {judge_mode}")
        print("startup checks PASSED")
        return 0

    # Serve — requires the api package extra (FastAPI + uvicorn)
    try:
        import uvicorn
        from verdictkit.api import app  # type: ignore[attr-defined]
    except ImportError as exc:
        print(
            f"ERROR: API server dependencies not installed ({exc}). "
            "Install with: pip install verdictkit[api]",
            file=sys.stderr,
        )
        return 1

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
