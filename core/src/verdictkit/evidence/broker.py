"""Evidence broker: dispatches EvidenceRequests to registered adapters. Requirement: core 5.2.

Adapters are the only code allowed network access, and only to the hosts listed in their
source registration. In replay mode the broker is constructed with ``network=False`` and
serves only from the store.
"""
from __future__ import annotations

from typing import Callable, Protocol, Sequence

from ..model import EvidenceItem
from ..plugin import EvidencePolicySpec, EvidenceRequest
from .store import EvidenceMeta, EvidenceStore


class SourceAdapter(Protocol):
    """``requires_network`` (optional attribute, default True): local adapters that read
    packaged, hash-pinned files set it False and may run with ``network=False``.
    Optional attributes ``source_class``, ``license_class`` and ``rights_note``."""

    source_id: str
    allowed_hosts: frozenset[str]

    def fetch(self, request: EvidenceRequest) -> tuple[bytes, str, str]:
        """Return (bytes, uri, media_type)."""


class EvidenceUnavailable(RuntimeError):
    pass


class EvidenceBroker:
    def __init__(self, store: EvidenceStore, adapters: Sequence[SourceAdapter], *, network: bool,
                 clock: Callable[[], str] | None = None) -> None:
        self._store = store
        self._adapters: dict[str, SourceAdapter] = {a.source_id: a for a in adapters}
        self._network = network
        self._clock = clock

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
            if not self._network and getattr(adapter, "requires_network", True):
                raise EvidenceUnavailable(
                    f"network access disabled; cannot fetch from {req.source_id!r}"
                )
            data, uri, media_type = adapter.fetch(req)
            # retrieved_at comes from the injected clock (never an evaluator input).
            meta = EvidenceMeta(
                source_id=req.source_id,
                source_class=_source_class_for(adapter),
                uri=uri,
                retrieved_at=self._clock() if self._clock is not None else "",
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
