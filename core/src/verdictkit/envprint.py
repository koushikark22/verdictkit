"""Environment fingerprint. Requirement: core 9.1, 9.4 (decision B5)."""
from __future__ import annotations

import hashlib
import os
import platform
from dataclasses import dataclass
from pathlib import Path

ENGINE_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class EnvFingerprint:
    engine_version: str
    python_version: str  # platform.python_version()
    lockfile_sha256: str  # of uv.lock, or "unknown"
    image_digest: str  # VK_IMAGE_DIGEST env var, or "unknown"


def fingerprint() -> EnvFingerprint:
    # Try to find and hash the lockfile
    lockfile_sha = "unknown"
    for candidate in [
        Path(__file__).resolve().parents[4] / "uv.lock",
        Path.cwd() / "uv.lock",
    ]:
        if candidate.is_file():
            lockfile_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
            break

    return EnvFingerprint(
        engine_version=ENGINE_VERSION,
        python_version=platform.python_version(),
        lockfile_sha256=lockfile_sha,
        image_digest=os.environ.get("VK_IMAGE_DIGEST", "unknown"),
    )
