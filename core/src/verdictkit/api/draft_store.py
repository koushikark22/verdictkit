"""Custodian-owned encrypted draft storage for the HTTP case lifecycle.

No asserted outcomes are stored in SQLite. Decryption is permitted only through
the custodian-side `load_private` method, never in a response serializer.
The store is not a substitute for operating-system examiner isolation.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path

from .freeze_boundary import PreparedFreeze
from verdictkit.custody.ledger import EntryKind, Ledger, LedgerEntry

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .intake_boundary import PreparedIntake

_CASE_ID = re.compile(r"^case_[0-9a-f]{32}$")
_TTL_SECONDS = 86400


class DraftNotFound(KeyError):
    pass


class DraftAlreadyExists(ValueError):
    pass


class FreezeConflict(ValueError):
    pass


class DraftStore:
    def __init__(self, directory: str | Path, key: bytes, *, ttl_seconds: int = _TTL_SECONDS):
        if len(key) != 32:
            raise ValueError("custody key must be 32 bytes")
        if ttl_seconds <= 0 or ttl_seconds > _TTL_SECONDS:
            raise ValueError("draft TTL must be between 1 and 86400 seconds")
        self.directory = Path(directory)
        # Check before any chmod: chmod on a symlink may change its target.
        if self.directory.is_symlink():
            raise ValueError("draft storage cannot be a symlink")
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink() or not self.directory.is_dir():
            raise ValueError("draft storage must be a real directory")
        self.directory.chmod(0o700)
        self._db = self.directory / "drafts.sqlite3"
        self._cipher = AESGCM(key)
        self._ttl = ttl_seconds
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS drafts ("
                "case_id TEXT PRIMARY KEY, created_at INTEGER NOT NULL,"
                "expires_at INTEGER NOT NULL, claim_type TEXT NOT NULL,"
                "data_mode TEXT NOT NULL, encrypted BLOB NOT NULL)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS drafts_expiry ON drafts(expires_at)")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS evidence_stages ("
                "case_id TEXT PRIMARY KEY, sealed BLOB NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS freezes ("
                "case_id TEXT PRIMARY KEY, frozen_at TEXT NOT NULL,"
                "spec_hash TEXT NOT NULL, commitment_digest TEXT NOT NULL,"
                "sealed BLOB NOT NULL)"
            )

    def _connect(self):
        conn = sqlite3.connect(str(self._db), timeout=10)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    @staticmethod
    def _case_id(case_id: str):
        if not isinstance(case_id, str) or _CASE_ID.fullmatch(case_id) is None:
            raise ValueError("invalid case id")

    def create(self, case_id: str, prepared: PreparedIntake, *, now: int | None = None) -> None:
        self._case_id(case_id)
        now = int(time.time()) if now is None else int(now)
        # The complete claim is encrypted. No unencrypted params or outcomes are
        # placed in SQLite; loggers must never serialize PreparedIntake.
        plaintext = json.dumps(
            dict(prepared.raw_claim), sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        nonce = os.urandom(12)
        ciphertext = nonce + self._cipher.encrypt(
            nonce, plaintext, case_id.encode("ascii")
        )
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO drafts VALUES (?, ?, ?, ?, ?, ?)",
                    (case_id, now, now + self._ttl,
                     prepared.claim_type, prepared.data_mode, ciphertext),
                )
        except sqlite3.IntegrityError as exc:
            raise DraftAlreadyExists("case ID already exists") from exc

    def load_private(self, case_id: str, *, now: int | None = None) -> dict:
        """Custodian-only private retrieval. Never return through an HTTP handler."""
        self._case_id(case_id)
        now = int(time.time()) if now is None else int(now)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT d.encrypted FROM drafts d LEFT JOIN freezes f ON "
                "f.case_id=d.case_id WHERE d.case_id=? AND (d.expires_at>? OR f.case_id IS NOT NULL)",
                (case_id, now),
            ).fetchone()
        if row is None:
            raise DraftNotFound("case unavailable")
        blob = bytes(row[0])
        if len(blob) < 29:
            raise ValueError("corrupt sealed draft")
        plaintext = self._cipher.decrypt(
            blob[:12], blob[12:], case_id.encode("ascii")
        )
        raw = json.loads(plaintext.decode("utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("invalid sealed draft")
        return raw

    def get_metadata(self, case_id: str, *, now: int | None = None) -> dict:
        """Only safe, non-outcome metadata for status responses."""
        self._case_id(case_id)
        now = int(time.time()) if now is None else int(now)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT d.created_at, d.expires_at, d.claim_type, d.data_mode, "
                "f.spec_hash, e.case_id FROM drafts d LEFT JOIN freezes f ON f.case_id=d.case_id "
                "LEFT JOIN evidence_stages e ON e.case_id=d.case_id "
                "WHERE d.case_id=? AND (d.expires_at>? OR f.case_id IS NOT NULL)",
                (case_id, now),
            ).fetchone()
        if row is None:
            raise DraftNotFound("case unavailable")
        return {
            "caseId": case_id, "createdAt": row[0], "expiresAt": row[1],
            "claimType": row[2], "dataMode": row[3],
            "state": "EVIDENCE_ACQUIRED" if row[5] is not None else (
                "FROZEN" if row[4] is not None else "DRAFT"),
            "specHash": row[4],
        }

    def purge_expired(self, *, now: int | None = None) -> int:
        now = int(time.time()) if now is None else int(now)
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM drafts WHERE expires_at<=? AND NOT EXISTS "
                "(SELECT 1 FROM freezes f WHERE f.case_id=drafts.case_id)", (now,)
            )
            return cur.rowcount

    def freeze(self, case_id: str, prepared: PreparedFreeze, *, frozen_at: str,
               now: int | None = None) -> None:
        """Atomically persist an irreversible custody commitment and sealed ledger."""
        self._case_id(case_id)
        now = int(time.time()) if now is None else int(now)
        if not frozen_at:
            raise ValueError("frozen_at required")
        if not prepared.ledger_entries or prepared.ledger_entries[-1].kind.value != "OUTCOMES_COMMITTED":
            raise ValueError("invalid custody ledger")
        record = {
            "salt": prepared.salt.hex(),
            "specHash": prepared.frozen.spec_hash,
            "commitment": {"alg": prepared.commitment.alg, "digest": prepared.commitment.digest},
            "ledger": [
                {"seq": e.seq, "kind": e.kind.value,
                 "payloadHash": e.payload_hash, "prevHash": e.prev_hash,
                 "entryHash": e.entry_hash, "recordedAt": e.recorded_at}
                for e in prepared.ledger_entries
            ],
        }
        plaintext = json.dumps(record, separators=(",", ":"), sort_keys=True).encode("utf-8")
        nonce = os.urandom(12)
        sealed = nonce + self._cipher.encrypt(nonce, plaintext, (case_id + ":freeze").encode())
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT d.encrypted, d.expires_at, f.case_id FROM drafts d "
                "LEFT JOIN freezes f ON f.case_id=d.case_id WHERE d.case_id=?",
                (case_id,),
            ).fetchone()
            if row is None or (row[1] <= now and row[2] is None):
                raise DraftNotFound("case unavailable")
            if row[2] is not None:
                raise FreezeConflict("case already frozen")
            blob = bytes(row[0])
            raw = json.loads(self._cipher.decrypt(
                blob[:12], blob[12:], case_id.encode("ascii")).decode("utf-8"))
            if raw.get("outcomes") != dict(prepared.asserted_outcomes) or raw.get("params") != dict(prepared.frozen.params):
                raise FreezeConflict("draft changed before freeze")
            conn.execute(
                "INSERT INTO freezes(case_id,frozen_at,spec_hash,commitment_digest,sealed) "
                "VALUES(?,?,?,?,?)",
                (case_id, frozen_at, prepared.frozen.spec_hash,
                 prepared.commitment.digest, sealed),
            )

    def get_freeze(self, case_id: str) -> dict:
        """Return safe freeze metadata after checking encrypted snapshot consistency."""
        self._case_id(case_id)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT frozen_at, spec_hash, commitment_digest, sealed "
                "FROM freezes WHERE case_id=?", (case_id,)
            ).fetchone()
        if row is None:
            raise DraftNotFound("case has no freeze")
        blob = bytes(row[3])
        sealed = json.loads(self._cipher.decrypt(
            blob[:12], blob[12:], (case_id + ":freeze").encode()
        ).decode("utf-8"))
        if sealed["specHash"] != row[1] or sealed["commitment"]["digest"] != row[2]:
            raise ValueError("freeze metadata integrity mismatch")
        return {
            "frozenAt": row[0], "specHash": row[1],
            "commitment": sealed["commitment"],
            "ledgerSeq": sealed["ledger"][-1]["seq"],
        }

    def acquire_internal_evidence(self, case_id: str, *, recorded_at: str) -> None:
        """Commit empty external evidence only for a policy-vetted quote claim."""
        self._case_id(case_id)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT f.sealed, e.case_id FROM freezes f "
                "LEFT JOIN evidence_stages e ON e.case_id=f.case_id "
                "WHERE f.case_id=?", (case_id,)
            ).fetchone()
            if row is None:
                raise DraftNotFound("case is not frozen")
            if row[1] is not None:
                raise FreezeConflict("evidence stage already committed")
            blob = bytes(row[0])
            info = json.loads(self._cipher.decrypt(
                blob[:12], blob[12:], (case_id + ":freeze").encode()
            ).decode("utf-8"))
            prior = tuple(
                LedgerEntry(seq=item["seq"], kind=EntryKind(item["kind"]),
                    payload_hash=item["payloadHash"], prev_hash=item["prevHash"],
                    entry_hash=item["entryHash"], recorded_at=item["recordedAt"])
                for item in info["ledger"]
            )
            ledger = Ledger.from_entries(prior, lambda: recorded_at)
            if not ledger.verify().ok or prior[-1].kind is not EntryKind.OUTCOMES_COMMITTED:
                raise ValueError("freeze ledger integrity failure")
            entry = ledger.append(EntryKind.EVIDENCE_ACQUIRED, {
                "evidence_count": 0, "evidence_hashes": []
            })
            record = {"evidence": [], "ledgerSeq": entry.seq,
                      "ledgerEntryHash": entry.entry_hash, "prevHash": entry.prev_hash}
            nonce = os.urandom(12)
            sealed = nonce + self._cipher.encrypt(
                nonce, json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8"),
                (case_id + ":evidence").encode("utf-8"))
            conn.execute("INSERT INTO evidence_stages(case_id,sealed) VALUES(?,?)",
                         (case_id, sealed))

    def get_evidence(self, case_id: str) -> list[dict]:
        """Read only a committed, authenticated zero-request evidence record."""
        self._case_id(case_id)
        with self._connect() as conn:
            row = conn.execute("SELECT sealed FROM evidence_stages WHERE case_id=?",
                               (case_id,)).fetchone()
        if row is None:
            raise DraftNotFound("evidence stage is not committed")
        blob = bytes(row[0])
        record = json.loads(self._cipher.decrypt(
            blob[:12], blob[12:], (case_id + ":evidence").encode("utf-8")
        ).decode("utf-8"))
        if record["evidence"] != [] or record["ledgerSeq"] != 3:
            raise ValueError("invalid internal evidence record")
        return []
