"""Local evidence adapter serving the hash-pinned Texas rules snapshot (quote req 5.1).

No network. ``fetch`` verifies the snapshot against its manifest (``load_rules``) and
raises if it does not match, so tampered bytes are never served as evidence.
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from verdictkit.model import LicenseClass, SourceClass
from verdictkit.plugin import EvidenceRequest

from .rules import load_rules

SOURCE_ID = "tx-rules-snapshot-v1"
URI = "package://quote-autopsy/rules/TX.json"
RIGHTS_NOTE = ("Derived summary of Texas government publications (Comptroller of Public "
               "Accounts, Texas OCCC); the source URIs are listed inside the snapshot.")


class TexasRulesAdapter:
    source_id = SOURCE_ID
    allowed_hosts: frozenset[str] = frozenset()
    requires_network = False
    source_class = SourceClass.GOVERNMENT_OFFICIAL
    license_class = LicenseClass.REDISTRIBUTABLE
    rights_note = RIGHTS_NOTE

    def __init__(self, snapshot: Path | None = None, manifest: Path | None = None) -> None:
        # Constructor-only override (used by tests); nothing external can set it.
        self._snapshot = Path(snapshot) if snapshot is not None else None
        self._manifest = Path(manifest) if manifest is not None else None

    def fetch(self, request: EvidenceRequest) -> tuple[bytes, str, str]:
        if request.source_id != SOURCE_ID or request.query.get("state") != "TX":
            raise ValueError("this adapter serves only the Texas rules snapshot")
        if self._snapshot is not None and self._manifest is not None:
            load_rules(self._snapshot, self._manifest)  # raises RulesIntegrityError
            return self._snapshot.read_bytes(), URI, "application/json"
        folder = resources.files("quote_autopsy").joinpath("rules")
        with resources.as_file(folder.joinpath("TX.json")) as snap, \
                resources.as_file(folder.joinpath("MANIFEST.json")) as man:
            load_rules(snap, man)  # raises RulesIntegrityError
            return snap.read_bytes(), URI, "application/json"
