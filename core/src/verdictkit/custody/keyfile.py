"""Vault key loading. Design DD8-2: the vault key is never a process argument.

Containers: the root entrypoint writes the key with shell builtins to a custodian-owned,
mode-0400 file on tmpfs and passes only its *path* (``VK_VAULT_KEY_FILE``). The custodian reads
the file once, validates owner and mode, removes it and keeps the key in process memory.
Non-container runs may still use ``VK_VAULT_KEY`` (base64 of 32 bytes) in the environment.
Setting both is an error, never a precedence rule.

Messages are fixed strings: they never contain the key, a path or an OS error.
"""
from __future__ import annotations

import base64
import binascii
import os
import threading
from typing import Mapping

from ..safeio import UnsafeFile, read_secret_file

KEY_BYTES = 32
_MAX_FILE_BYTES = 256
_lock = threading.Lock()
_from_file: dict[str, bytes] = {}   # path -> key, so a read-once file survives repeated lookups


class VaultKeyError(ValueError):
    """The configured vault key is ambiguous, unreadable or malformed."""


_FILE_MESSAGES = {
    "MISSING": "vault key file is missing",
    "UNREADABLE": "vault key file is unreadable",
    "NOT_REGULAR": "vault key file is not a regular file",
    "PERMISSIONS": "vault key file must be owned by this user and not accessible to others",
    "TOO_LARGE": "vault key file is too large",
    "NOT_REMOVED": "vault key file could not be removed after reading",
}


def _decode(raw: str | bytes) -> bytes:
    text = raw.decode("ascii", "strict") if isinstance(raw, bytes) else raw
    try:
        key = base64.b64decode(text.strip(), validate=True)
    except (binascii.Error, ValueError, UnicodeError):
        raise VaultKeyError("vault key is not valid base64") from None
    if len(key) != KEY_BYTES:
        raise VaultKeyError("vault key must be 32 bytes")
    return key


def load_vault_key(environ: Mapping[str, str] | None = None) -> bytes | None:
    """Return the 32-byte vault key, or ``None`` when neither variable is set."""
    env = os.environ if environ is None else environ
    path = env.get("VK_VAULT_KEY_FILE")
    inline = env.get("VK_VAULT_KEY")
    if path and inline:
        raise VaultKeyError("set only one of VK_VAULT_KEY and VK_VAULT_KEY_FILE")
    if path:
        with _lock:
            cached = _from_file.get(path)
            if cached is not None:
                return cached
            try:
                data = read_secret_file(path, max_bytes=_MAX_FILE_BYTES, remove=True)
            except UnsafeFile as exc:
                raise VaultKeyError(_FILE_MESSAGES.get(exc.reason, "vault key file is unusable")) from None
            key = _decode(data)
            _from_file[path] = key
            return key
    if inline:
        return _decode(inline)
    return None
