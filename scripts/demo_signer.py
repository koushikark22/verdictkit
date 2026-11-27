#!/usr/bin/env python3
"""Provision the disposable demonstration signer (Batch 2; used by ``entrypoint.sh demo``).

  demo_signer.py provision SIGN_DIR LAB_DIR
      Run as vk-custodian. Writes one throwaway Ed25519 private key to SIGN_DIR/signing.pem
      (mode 0600, directory 0700) and three PUBLIC verifier trust stores to LAB_DIR:

        trust-trusted.json   lists the signer as ACTIVE            (serial 1)
        trust-unknown.json   lists one unrelated public key only   (serial 1)
        trust-revoked.json   lists the signer as REVOKED           (serial 2)

      The unrelated key's private half is discarded without ever being serialised. The only
      output is the signer's public key id. The key is regenerated at every start, so it is
      disposable by construction; nothing here is a production key and it is never committed.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from verdictkit.safeio import write_private_file
from verdictkit.signing import signer_from_private_key, trust_entry_for

VALID_FOR = timedelta(days=7)
FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _store(serial: int, *entries: dict) -> str:
    return json.dumps({"format": "vk-trust-store", "format_version": 1, "serial": serial,
                       "keys": list(entries)}, indent=2) + "\n"


def provision(sign_dir: Path, lab_dir: Path, *, now: datetime | None = None) -> str:
    """Create the key and the three profiles. Returns the signer's public key id."""
    now = now or datetime.now(timezone.utc)
    window = {"not_before": (now - timedelta(hours=1)).strftime(FORMAT),
              "not_after": (now + VALID_FOR).strftime(FORMAT)}
    private = Ed25519PrivateKey.generate()
    signer = signer_from_private_key(private)
    unrelated = signer_from_private_key(Ed25519PrivateKey.generate())   # public half only is used
    pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    Path(sign_dir).mkdir(parents=True, exist_ok=True)
    Path(lab_dir).mkdir(parents=True, exist_ok=True)
    write_private_file(Path(sign_dir) / "signing.pem", pem)
    lab = Path(lab_dir)
    (lab / "trust-trusted.json").write_text(_store(1, trust_entry_for(signer, **window)), encoding="utf-8")
    (lab / "trust-unknown.json").write_text(_store(1, trust_entry_for(unrelated, **window)), encoding="utf-8")
    (lab / "trust-revoked.json").write_text(
        _store(2, trust_entry_for(signer, **window, status="REVOKED")), encoding="utf-8")
    return signer.key_id


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "provision":
        print(f"demo-signer: key_id {provision(Path(argv[2]), Path(argv[3]))}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
