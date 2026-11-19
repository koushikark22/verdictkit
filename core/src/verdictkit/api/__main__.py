"""VerdictKit API startup, including fail-closed judge-mode enforcement."""
from __future__ import annotations

import argparse
import sys

from .check_startup import (
    IsolationNotEnforcedError,
    StartupConfigurationError,
    startup_checks,
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m verdictkit.api")
    parser.add_argument("--check-startup", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        judge_mode, isolation = startup_checks()
    except StartupConfigurationError:
        print("VK_STARTUP_ERROR=CONFIG_INVALID:VK_JUDGE_MODE", file=sys.stderr)
        return 2
    except IsolationNotEnforcedError:
        print("VK_STARTUP_ERROR=ISOLATION_NOT_ENFORCED", file=sys.stderr)
        return 3

    if args.check_startup:
        print(f"isolation_mode: {isolation}")
        print(f"judge_mode: {judge_mode}")
        print(f"VK_STARTUP_OK isolation={isolation}")
        return 0

    try:
        import uvicorn
        from .server import create_app
        app = create_app(judge_mode=judge_mode)
    except ImportError as exc:
        print(f"API dependencies unavailable: {exc}", file=sys.stderr)
        return 1
    except (IsolationNotEnforcedError, StartupConfigurationError) as exc:
        print(f"VK_STARTUP_ERROR={type(exc).__name__}", file=sys.stderr)
        return 3

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
