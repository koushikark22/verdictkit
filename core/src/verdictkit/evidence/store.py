"""Content-addressed evidence store. Requirement: core 5.4. Property: P9.

Layout: ``<root>/blobs/<sha256>`` (bytes) and ``<root>/meta/<sha256>.json`` (canonical).
Every ``get`` recomputes SHA-256 and raises EvidenceIntegrityError on mismatch.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..canonical import canonical_bytes, parse_canonical
from ..model import EvidenceItem, LicenseClass, SourceClass


class EvidenceIntegrityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceMeta:
    source_id: str
    source_class: SourceClass
    uri: str
    retrieved_at: str
    media_type: str
    license_class: LicenseClass


class EvidenceStore:
    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._blobs = self._root / "blobs"
        self._meta = self._root / "meta"
        self._blobs.mkdir(parents=True, exist_ok=True)
        self._meta.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes, meta: EvidenceMeta) -> EvidenceItem:
        sha = hashlib.sha256(data).hexdigest()
        blob_path = self._blobs / sha
        blob_path.write_bytes(data)

        meta_obj = {
            "source_id": meta.source_id,
            "source_class": meta.source_class.value,
            "uri": meta.uri,
            "retrieved_at": meta.retrieved_at,
            "media_type": meta.media_type,
            "license_class": meta.license_class.value,
            "sha256": sha,
        }
        meta_path = self._meta / f"{sha}.json"
        meta_path.write_bytes(canonical_bytes(meta_obj))

        return EvidenceItem(
            source_id=meta.source_id,
            source_class=meta.source_class,
            uri=meta.uri,
            retrieved_at=meta.retrieved_at,
            sha256=sha,
            media_type=meta.media_type,
            license_class=meta.license_class,
        )

    def get(self, sha256: str) -> bytes:
        blob_path = self._blobs / sha256
        data = blob_path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != sha256:
            raise EvidenceIntegrityError(
                f"evidence integrity check failed: expected {sha256}, got {actual}"
            )
        return data

    def item(self, sha256: str) -> EvidenceItem:
        meta_path = self._meta / f"{sha256}.json"
        meta_obj = parse_canonical(meta_path.read_bytes())
        return EvidenceItem(
            source_id=meta_obj["source_id"],
            source_class=SourceClass(meta_obj["source_class"]),
            uri=meta_obj["uri"],
            retrieved_at=meta_obj["retrieved_at"],
            sha256=meta_obj["sha256"],
            media_type=meta_obj["media_type"],
            license_class=LicenseClass(meta_obj["license_class"]),
        )

    def blob_path(self, sha256: str) -> Path:
        return self._blobs / sha256
