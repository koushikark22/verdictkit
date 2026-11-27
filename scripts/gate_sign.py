#!/usr/bin/env python3
"""Helpers for the ``gate-sign`` container gate (signed bundles, design D5).

  gate_sign.py keygen SIGN_DIR TRUST_DIR
      Run as vk-custodian. Writes a throwaway Ed25519 signing key (mode 0600, SIGN_DIR) and three
      trust stores (TRUST_DIR): ``trust-good.json`` accepts it, ``trust-other.json`` holds an
      unrelated key only, ``trust-revoked.json`` lists it as REVOKED. The key exists only inside
      this container run; nothing here is a production key.
  gate_sign.py tamper {member|manifest|signature} IN.vkb OUT.vkb
      Rewrite a bundle with one defect, leaving everything else byte-identical.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from verdictkit.canonical import canonical_bytes
from verdictkit.safeio import write_private_file
from verdictkit.signing import signer_from_private_key, trust_entry_for

NOT_BEFORE, NOT_AFTER = "2000-01-01T00:00:00Z", "2999-12-31T23:59:59Z"


def _store(*entries: dict) -> str:
    return json.dumps({"format": "vk-trust-store", "format_version": 1, "serial": 1, "keys": list(entries)},
                      indent=2) + "\n"


def keygen(sign_dir: Path, trust_dir: Path) -> None:
    private = Ed25519PrivateKey.generate()
    signer = signer_from_private_key(private)
    other = signer_from_private_key(Ed25519PrivateKey.generate())
    pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    write_private_file(sign_dir / "signing.pem", pem)
    trust_dir.mkdir(parents=True, exist_ok=True)
    (trust_dir / "trust-good.json").write_text(_store(trust_entry_for(signer, not_before=NOT_BEFORE,
                                                                      not_after=NOT_AFTER)))
    (trust_dir / "trust-other.json").write_text(_store(trust_entry_for(other, not_before=NOT_BEFORE,
                                                                       not_after=NOT_AFTER)))
    (trust_dir / "trust-revoked.json").write_text(_store(trust_entry_for(
        signer, not_before=NOT_BEFORE, not_after=NOT_AFTER, status="REVOKED")))
    print(f"gate-sign: key_id {signer.key_id}")


def tamper(kind: str, source: Path, target: Path) -> None:
    def mutate(name: str, data: bytes) -> bytes:
        if kind == "member" and name == "verdict/verdict.json":
            marker = b'"verdict_hash":"'
            i = data.index(marker) + len(marker)
            return data[:i] + (b"0" if data[i:i + 1] != b"0" else b"1") + data[i + 1:]
        if kind == "manifest" and name == "manifest.json":
            marker = b'"written_at":"'
            i = data.index(marker) + len(marker)
            return data[:i] + (b"3" if data[i:i + 1] != b"3" else b"4") + data[i + 1:]
        if kind == "signature" and name == "signature/envelope.json":
            envelope = json.loads(data)
            sig = envelope["signature"]
            envelope["signature"] = ("0" if sig[0] != "0" else "1") + sig[1:]
            return canonical_bytes(envelope)
        return data

    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            zout.writestr(info, mutate(info.filename, zin.read(info.filename)))


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "keygen":
        keygen(Path(argv[2]), Path(argv[3]))
        return 0
    if len(argv) == 5 and argv[1] == "tamper" and argv[2] in ("member", "manifest", "signature"):
        tamper(argv[2], Path(argv[3]), Path(argv[4]))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
