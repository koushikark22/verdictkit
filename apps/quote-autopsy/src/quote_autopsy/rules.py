"""Single-state rules snapshot. Requirement: quote 5.1. State chosen at decision B7.

Snapshot file ``rules/<STATE>.json`` (canonical JSON):
  {"state", "state_rate_pct", "local_rate_min_pct", "local_rate_max_pct",
   "localities": {code: combined_rate_pct} | null,
   "doc_fee_cap": "<amount>" | null,
   "sources": [{"uri", "retrieved_at", "sha256_of_source"}]}
The loader verifies the file's own SHA-256 against ``rules/MANIFEST.json``.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StateRules:
    state: str
    state_rate_pct: Decimal
    local_rate_min_pct: Decimal
    local_rate_max_pct: Decimal
    localities: dict[str, Decimal] | None
    doc_fee_cap: Decimal | None
    snapshot_sha256: str

    def combined_rate(self, locality_code: str) -> Decimal | None:
        raise NotImplementedError("quote task 4.1")

    def rate_range(self) -> tuple[Decimal, Decimal]:
        raise NotImplementedError("quote task 4.1")


def load_rules(path: Path, manifest: Path) -> StateRules:
    raise NotImplementedError("quote task 4.1")
