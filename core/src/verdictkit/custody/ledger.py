"""Hash-chained, state-machine-enforced case ledger. Requirement: core 8. Properties P6, P7.

entry_hash = SHA256(b"vk-ledger-v1" || canonical([seq, kind, payload_hash, prev_hash]))
payload_hash = sha256_hex(canonical_bytes(payload)); prev_hash of seq 0 = "0" * 64.
``recorded_at`` comes from the injected clock and is excluded from entry_hash.

Allowed transitions (TRANSITIONS below is normative):
  start -> CASE_OPENED
  CASE_OPENED -> CLAIM_FROZEN -> OUTCOMES_COMMITTED -> EVIDENCE_ACQUIRED
    -> EXAMINATION_COMMITTED -> OUTCOMES_REVEALED -> VERDICT_SEALED
  VERDICT_SEALED -> DIAGNOSTICS_APPENDED | BUNDLE_WRITTEN
  DIAGNOSTICS_APPENDED -> DIAGNOSTICS_APPENDED | BUNDLE_WRITTEN
  any state before VERDICT_SEALED (after start) -> CASE_ABORTED
  BUNDLE_WRITTEN and CASE_ABORTED are terminal.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, Sequence

from ..canonical import canonical_bytes, sha256_hex


class EntryKind(str, Enum):
    CASE_OPENED = "CASE_OPENED"
    CLAIM_FROZEN = "CLAIM_FROZEN"
    OUTCOMES_COMMITTED = "OUTCOMES_COMMITTED"
    EVIDENCE_ACQUIRED = "EVIDENCE_ACQUIRED"
    EXAMINATION_COMMITTED = "EXAMINATION_COMMITTED"
    OUTCOMES_REVEALED = "OUTCOMES_REVEALED"
    VERDICT_SEALED = "VERDICT_SEALED"
    DIAGNOSTICS_APPENDED = "DIAGNOSTICS_APPENDED"
    BUNDLE_WRITTEN = "BUNDLE_WRITTEN"
    CASE_ABORTED = "CASE_ABORTED"


_MAIN = (
    EntryKind.CASE_OPENED,
    EntryKind.CLAIM_FROZEN,
    EntryKind.OUTCOMES_COMMITTED,
    EntryKind.EVIDENCE_ACQUIRED,
    EntryKind.EXAMINATION_COMMITTED,
    EntryKind.OUTCOMES_REVEALED,
    EntryKind.VERDICT_SEALED,
)

#: Normative transition table. ``None`` is the empty-ledger start state.
TRANSITIONS: Mapping[EntryKind | None, frozenset[EntryKind]] = {
    None: frozenset({EntryKind.CASE_OPENED}),
    **{
        k: frozenset({_MAIN[i + 1], EntryKind.CASE_ABORTED})
        for i, k in enumerate(_MAIN[:-1])
    },
    EntryKind.VERDICT_SEALED: frozenset(
        {EntryKind.DIAGNOSTICS_APPENDED, EntryKind.BUNDLE_WRITTEN}
    ),
    EntryKind.DIAGNOSTICS_APPENDED: frozenset(
        {EntryKind.DIAGNOSTICS_APPENDED, EntryKind.BUNDLE_WRITTEN}
    ),
    EntryKind.BUNDLE_WRITTEN: frozenset(),
    EntryKind.CASE_ABORTED: frozenset(),
}


class LedgerOrderError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    seq: int
    kind: EntryKind
    payload_hash: str
    prev_hash: str
    entry_hash: str
    recorded_at: str


@dataclass(frozen=True, slots=True)
class LedgerCheck:
    ok: bool
    first_invalid_seq: int | None


def _compute_entry_hash(seq: int, kind: EntryKind, payload_hash: str, prev_hash: str) -> str:
    """entry_hash = SHA256(b"vk-ledger-v1" || canonical([seq, kind, payload_hash, prev_hash]))"""
    domain = b"vk-ledger-v1"
    data = canonical_bytes([seq, kind.value, payload_hash, prev_hash])
    import hashlib
    return hashlib.sha256(domain + data).hexdigest()


class Ledger:
    def __init__(self, clock: Callable[[], str]) -> None:
        """``clock`` returns an ISO-8601 UTC string; injected for determinism."""
        self._clock = clock
        self._entries: list[LedgerEntry] = []
        self._last_kind: EntryKind | None = None

    @classmethod
    def from_entries(cls, entries: Sequence[LedgerEntry], clock: Callable[[], str]) -> "Ledger":
        """Load entries without validating them; call ``verify()`` to check."""
        ledger = cls.__new__(cls)
        ledger._clock = clock
        ledger._entries = list(entries)
        ledger._last_kind = entries[-1].kind if entries else None
        return ledger

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def append(self, kind: EntryKind, payload: Mapping[str, object]) -> LedgerEntry:
        """Raise LedgerOrderError (ledger unchanged) if ``kind`` is not allowed next."""
        allowed = TRANSITIONS.get(self._last_kind, frozenset())
        if kind not in allowed:
            raise LedgerOrderError(
                f"cannot append {kind!r} after {self._last_kind!r}; "
                f"allowed: {sorted(k.value for k in allowed)}"
            )

        seq = len(self._entries)
        payload_hash = sha256_hex(canonical_bytes(dict(payload)))
        prev_hash = self._entries[-1].entry_hash if self._entries else "0" * 64
        entry_hash = _compute_entry_hash(seq, kind, payload_hash, prev_hash)

        entry = LedgerEntry(
            seq=seq,
            kind=kind,
            payload_hash=payload_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            recorded_at=self._clock(),
        )
        self._entries.append(entry)
        self._last_kind = kind
        return entry

    def verify(self) -> LedgerCheck:
        """Recompute every entry hash and transition; report the first invalid seq."""
        prev_hash = "0" * 64
        prev_kind: EntryKind | None = None

        for entry in self._entries:
            # Check transition
            allowed = TRANSITIONS.get(prev_kind, frozenset())
            if entry.kind not in allowed:
                return LedgerCheck(ok=False, first_invalid_seq=entry.seq)

            # Check prev_hash linkage
            if entry.prev_hash != prev_hash:
                return LedgerCheck(ok=False, first_invalid_seq=entry.seq)

            # Recompute entry_hash (excludes recorded_at)
            expected_hash = _compute_entry_hash(
                entry.seq, entry.kind, entry.payload_hash, entry.prev_hash
            )
            if entry.entry_hash != expected_hash:
                return LedgerCheck(ok=False, first_invalid_seq=entry.seq)

            prev_hash = entry.entry_hash
            prev_kind = entry.kind

        return LedgerCheck(ok=True, first_invalid_seq=None)
