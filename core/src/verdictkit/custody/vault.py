"""Sealed outcome storage. Requirement: core 3.2, 4.1.

AES-256-GCM with a 32-byte key read from ``VK_VAULT_KEY`` (base64) at Custodian start-up.
The key is never written to disk, never logged, and never placed in a child environment.
Files: ``<vault_dir>/<case_id>.sealed`` = nonce(12) || ciphertext; AAD = case_id.
On start-up the Vault checks the directory mode is 0700 and owned by the current uid when
isolation is ENFORCED, and raises otherwise.
"""
from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..canonical import canonical_bytes, parse_canonical
from ..model import IsolationMode


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

    def seal(self, case_id: str, outcomes: Mapping[str, object]) -> SealedRef:
        plaintext = canonical_bytes(dict(outcomes))
        nonce = os.urandom(12)
        aad = case_id.encode("utf-8")
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, aad)
        path = self._vault_dir / f"{case_id}.sealed"
        path.write_bytes(nonce + ciphertext)
        return SealedRef(case_id=case_id, path=str(path))

    def unseal(self, ref: SealedRef) -> Mapping[str, object]:
        blob = Path(ref.path).read_bytes()
        nonce, ciphertext = blob[:12], blob[12:]
        aad = ref.case_id.encode("utf-8")
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, aad)
        result = parse_canonical(plaintext)
        if not isinstance(result, dict):
            raise ValueError("sealed outcomes must be a JSON object")
        return result
