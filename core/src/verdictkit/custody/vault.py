"""Sealed outcome storage. Requirement: core 3.2, 4.1.

AES-256-GCM with a 32-byte key supplied by the Custodian (see ``keyfile.load_vault_key``).
The key is never written to disk by this module, never logged, and never placed in a child
environment. Files: ``<vault_dir>/<case_id>.sealed`` = nonce(12) || ciphertext; AAD = case_id.

Hardening: ``case_id`` must be a plain identifier (no path syntax), the file location is always
derived from it (a ``SealedRef.path`` is only accepted when it names that same file), writes are
atomic with mode 0600, and reads are bounded. When isolation is ENFORCED the vault directory must
be mode 0700 and owned by the current uid, otherwise ``PermissionError``.
"""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..canonical import canonical_bytes, parse_canonical
from ..model import IsolationMode
from ..safeio import read_secret_file, write_private_file, UnsafeFile

_CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_MAX_SEALED_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class SealedRef:
    case_id: str
    path: str


class Vault:
    def __init__(self, vault_dir: Path, key: bytes, isolation: IsolationMode) -> None:
        vault_dir = Path(vault_dir)
        vault_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        # Explicitly chmod after mkdir in case the process umask masked bits.
        vault_dir.chmod(0o700)

        if isolation is IsolationMode.ENFORCED:
            st = vault_dir.stat()
            mode = stat.S_IMODE(st.st_mode)
            if mode != 0o700:
                raise PermissionError(
                    f"vault directory {vault_dir} must have mode 0700, got {oct(mode)}"
                )
            if st.st_uid != os.getuid():
                raise PermissionError(
                    f"vault directory {vault_dir} must be owned by current uid {os.getuid()}, "
                    f"got uid {st.st_uid}"
                )

        if len(key) != 32:
            raise ValueError(f"vault key must be 32 bytes, got {len(key)}")

        self._vault_dir = vault_dir
        self._aesgcm = AESGCM(key)

    def _path_for(self, case_id: str) -> Path:
        if not isinstance(case_id, str) or _CASE_ID.fullmatch(case_id) is None:
            raise ValueError("case_id must be a plain identifier")
        return self._vault_dir / f"{case_id}.sealed"

    def seal(self, case_id: str, outcomes: Mapping[str, object]) -> SealedRef:
        path = self._path_for(case_id)
        plaintext = canonical_bytes(dict(outcomes))
        nonce = os.urandom(12)
        aad = case_id.encode("utf-8")
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, aad)
        write_private_file(path, nonce + ciphertext)
        return SealedRef(case_id=case_id, path=str(path))

    def unseal(self, ref: SealedRef) -> Mapping[str, object]:
        path = self._path_for(ref.case_id)
        # The reference cannot redirect the read: it must name the vault's own file.
        if os.path.normcase(os.path.abspath(ref.path)) != os.path.normcase(os.path.abspath(path)):
            raise ValueError("sealed reference does not belong to this vault")
        try:
            blob = _read_vault_file(path)
        except UnsafeFile:
            raise ValueError("sealed outcomes are unavailable") from None
        nonce, ciphertext = blob[:12], blob[12:]
        aad = ref.case_id.encode("utf-8")
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, aad)
        result = parse_canonical(plaintext)
        if not isinstance(result, dict):
            raise ValueError("sealed outcomes must be a JSON object")
        return result


def _read_vault_file(path: Path) -> bytes:
    """Bounded read of a regular, non-link file. Sealed files are written 0600 by this process."""
    return read_secret_file(os.path.abspath(path), max_bytes=_MAX_SEALED_BYTES)
