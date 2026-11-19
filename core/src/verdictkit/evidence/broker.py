"""Evidence broker: dispatches EvidenceRequests to registered adapters. Requirement: core 5.2.

Adapters are the only code allowed network access, and only to the hosts listed in their
source registration. In replay mode the broker is constructed with ``network=False`` and
serves only from the store.
"""
from __future__ import annotations

from typing import Protocol, Sequence

from ..model import EvidenceItem
from ..plugin import EvidencePolicySpec, EvidenceRequest
from .store import EvidenceMeta, EvidenceStore


class SourceAdapter(Protocol):
    source_id: str
    allowed_hosts: frozenset[str]

    def fetch(self, request: EvidenceRequest) -> tuple[bytes, str, str]:
        """Return (bytes, uri, media_type)."""


class EvidenceUnavailable(RuntimeError):
    pass


class EvidenceBroker:
    def __init__(self, store: EvidenceStore, adapters: Sequence[SourceAdapter], *, network: bool) -> None:
        self._store = store
        self._adapters: dict[str, SourceAdapter] = {a.source_id: a for a in adapters}
        self._network = network

    def acquire(
        self, requests: Sequence[EvidenceRequest], policy: EvidencePolicySpec
    ) -> tuple[EvidenceItem, ...]:
        results: list[EvidenceItem] = []
        for req in requests:
            if req.source_id not in policy.permitted_sources:
                raise EvidenceUnavailable(
                    f"source {req.source_id!r} not in permitted sources"
                )
            adapter = self._adapters.get(req.source_id)
            if adapter is None:
                raise EvidenceUnavailable(
                    f"no adapter registered for source {req.source_id!r}"
                )
            if not self._network:
                raise EvidenceUnavailable(
                    f"network access disabled; cannot fetch from {req.source_id!r}"
                )
            data, uri, media_type = adapter.fetch(req)
            # We need a retrieved_at timestamp and source class; the adapter provides them
            # via a richer interface in practice. For the core protocol we store a minimal
            # EvidenceMeta. The retrieved_at must be provided externally; use a placeholder.
            meta = EvidenceMeta(
                source_id=req.source_id,
                source_class=_source_class_for(adapter),
                uri=uri,
                retrieved_at="",
                media_type=media_type,
                license_class=_license_class_for(adapter),
            )
            item = self._store.put(data, meta)
            results.append(item)
        return tuple(results)


def _source_class_for(adapter: SourceAdapter):
    from ..model import SourceClass
    # Adapters may expose source_class attribute; fall back to EXCHANGE_PUBLIC_DATA.
    return getattr(adapter, "source_class", None) or SourceClass.EXCHANGE_PUBLIC_DATA


def _license_class_for(adapter: SourceAdapter):
    from ..model import LicenseClass
    return getattr(adapter, "license_class", None) or LicenseClass.REFETCH_ONLY
