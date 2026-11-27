"""Keep unrelated credentials out of the test process (Batch 2 security fix).

Batch 1 exposed an unrelated Alpaca credential in a pytest traceback, because tests copy
``os.environ`` into subprocesses and pytest prints values it finds in failing assertions. The
fix removes credential-looking variables from the test process itself, before any test runs, so
no subprocess can inherit them and no traceback can show them. Only the NAMES are matched and
only a COUNT is ever reported: neither a value nor a name is printed.

``VK_*`` variables belong to this project and are left alone.
"""
from __future__ import annotations

import re
from collections.abc import MutableMapping

SENSITIVE = re.compile(
    r"(KEY|SECRET|TOKEN|PASSW|CREDENTIAL|AUTH|SESSION|COOKIE|PRIVATE|CERT|BEARER|SSH"
    r"|ALPACA|APCA|AWS_|AZURE|GCP|GOOGLE|OPENAI|ANTHROPIC|GITHUB|GITLAB|NPM_|PYPI|DOCKER_|KUBE)",
    re.IGNORECASE,
)
PROTECTED_PREFIX = "VK_"


def is_sensitive(name: str) -> bool:
    return not name.upper().startswith(PROTECTED_PREFIX) and SENSITIVE.search(name) is not None


def scrub_environment(environ: MutableMapping[str, str]) -> int:
    """Delete credential-looking variables in place. Returns how many were removed."""
    doomed = [name for name in list(environ) if is_sensitive(name)]
    for name in doomed:
        del environ[name]
    return len(doomed)
