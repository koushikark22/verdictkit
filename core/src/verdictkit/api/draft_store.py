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
    def __init__(self, directory: str | Path, key: bytes, *, ttl_seconds: int = _TTL_SECONDS,
                 expire_frozen: bool = False):
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
        # Judge mode (Req 12.2): every case, frozen or not, expires after the TTL.
        self._expire_frozen = expire_frozen
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
                "CREATE TABLE IF NOT EXISTS confirmations ("
                "case_id TEXT PRIMARY KEY, names TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS text_fields ("
                "case_id TEXT PRIMARY KEY, names TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS blockers ("
                "case_id TEXT PRIMARY KEY, blockers TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS runs ("
                "run_id TEXT PRIMARY KEY, case_id TEXT NOT NULL UNIQUE,"
                "state TEXT NOT NULL, isolation TEXT NOT NULL, started_at TEXT NOT NULL,"
                "finished_at TEXT, events TEXT NOT NULL, outcome TEXT,"
                "bundle_sha256 TEXT)"
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
        if prepared.text_spans:
            # Names only: the pasted text and its spans are never persisted.
            self.set_text_fields(case_id, sorted(prepared.text_spans))

    def set_text_fields(self, case_id: str, names: list[str]) -> None:
        self._case_id(case_id)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO text_fields(case_id,names) VALUES(?,?) "
                "ON CONFLICT(case_id) DO UPDATE SET names=excluded.names",
                (case_id, json.dumps(sorted(set(names)))))

    def get_text_fields(self, case_id: str) -> list[str]:
        self._case_id(case_id)
        with self._connect() as conn:
            row = conn.execute("SELECT names FROM text_fields WHERE case_id=?",
                               (case_id,)).fetchone()
        return [] if row is None else list(json.loads(row[0]))

    def load_private(self, case_id: str, *, now: int | None = None) -> dict:
        """Custodian-only private retrieval. Never return through an HTTP handler."""
        self._case_id(case_id)
        now = int(time.time()) if now is None else int(now)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT d.encrypted FROM drafts d LEFT JOIN freezes f ON "
                "f.case_id=d.case_id WHERE d.case_id=? AND (d.expires_at>? OR (f.case_id IS NOT NULL AND ?=0))",
                (case_id, now, int(self._expire_frozen)),
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
                "WHERE d.case_id=? AND (d.expires_at>? OR (f.case_id IS NOT NULL AND ?=0))",
                (case_id, now, int(self._expire_frozen)),
            ).fetchone()
        if row is None:
            raise DraftNotFound("case unavailable")
        state = "EVIDENCE_ACQUIRED" if row[5] is not None else (
            "FROZEN" if row[4] is not None else "DRAFT")
        run = self.get_run(case_id=case_id)
        if run is not None:
            state = {"QUEUED": "RUNNING", "RUNNING": "RUNNING", "FAILED": "FAILED",
                     "BLOCKED": "BLOCKED"}.get(run["state"], "SEALED")
        return {
            "caseId": case_id, "createdAt": row[0], "expiresAt": row[1],
            "claimType": row[2], "dataMode": row[3],
            "state": state,
            "specHash": row[4],
            "latestRunId": None if run is None else run["runId"],
        }

    def purge_expired(self, *, now: int | None = None) -> int:
        """Delete expired drafts (and, in judge mode, expired frozen cases with their
        custody records, runs and bundles). Returns the number of cases removed."""
        now = int(time.time()) if now is None else int(now)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if self._expire_frozen:
                ids = [r[0] for r in conn.execute(
                    "SELECT case_id FROM drafts WHERE expires_at<=?", (now,))]
            else:
                ids = [r[0] for r in conn.execute(
                    "SELECT case_id FROM drafts WHERE expires_at<=? AND NOT EXISTS "
                    "(SELECT 1 FROM freezes f WHERE f.case_id=drafts.case_id)", (now,))]
            for case_id in ids:
                for table in ("drafts", "freezes", "evidence_stages", "confirmations",
                              "text_fields", "blockers", "runs"):
                    conn.execute(f"DELETE FROM {table} WHERE case_id=?", (case_id,))
        for case_id in ids:
            bundle = self.directory / "bundles" / f"{case_id}.vkb"
            try:
                bundle.unlink()
            except FileNotFoundError:
                pass
        return len(ids)

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
                      "ledgerEntryHash": entry.entry_hash, "prevHash": entry.prev_hash,
                      "kind": entry.kind.value, "payloadHash": entry.payload_hash,
                      "recordedAt": entry.recorded_at}
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

    # ---- custodian-only reconstruction for the run stage -------------------------
    def _decrypt(self, blob: bytes, aad: bytes) -> dict:
        blob = bytes(blob)
        if len(blob) < 29:
            raise ValueError("corrupt sealed record")
        return json.loads(self._cipher.decrypt(blob[:12], blob[12:], aad).decode("utf-8"))

    def load_custody(self, case_id: str) -> tuple[bytes, dict, tuple[LedgerEntry, ...]]:
        """Return (salt, commitment, ledger entries through EVIDENCE_ACQUIRED).

        Custodian-only. The salt must never be published before the verdict seal.
        The reconstructed chain is verified before it is returned.
        """
        self._case_id(case_id)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT f.sealed, e.sealed FROM freezes f JOIN evidence_stages e "
                "ON e.case_id=f.case_id WHERE f.case_id=?", (case_id,)
            ).fetchone()
        if row is None:
            raise DraftNotFound("case has no committed evidence stage")
        info = self._decrypt(row[0], (case_id + ":freeze").encode())
        ev = self._decrypt(row[1], (case_id + ":evidence").encode("utf-8"))
        if "payloadHash" not in ev or "recordedAt" not in ev:
            raise ValueError("evidence record predates full ledger persistence")
        entries = [
            LedgerEntry(seq=item["seq"], kind=EntryKind(item["kind"]),
                        payload_hash=item["payloadHash"], prev_hash=item["prevHash"],
                        entry_hash=item["entryHash"], recorded_at=item["recordedAt"])
            for item in info["ledger"]
        ]
        entries.append(LedgerEntry(
            seq=ev["ledgerSeq"], kind=EntryKind(ev["kind"]), payload_hash=ev["payloadHash"],
            prev_hash=ev["prevHash"], entry_hash=ev["ledgerEntryHash"],
            recorded_at=ev["recordedAt"]))
        ledger = Ledger.from_entries(tuple(entries), lambda: "")
        check = ledger.verify()
        if not check.ok or entries[-1].kind is not EntryKind.EVIDENCE_ACQUIRED:
            raise ValueError("custody ledger integrity failure")
        salt = bytes.fromhex(info["salt"])
        if len(salt) != 32:
            raise ValueError("invalid sealed salt")
        return salt, dict(info["commitment"]), tuple(entries)

    # ---- draft edits ---------------------------------------------------------------
    def update_draft(self, case_id: str, raw: dict, *, confirmed: list[str],
                     now: int | None = None) -> None:
        """Replace the encrypted draft claim while it is still a DRAFT."""
        self._case_id(case_id)
        now = int(time.time()) if now is None else int(now)
        plaintext = json.dumps(raw, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False).encode("utf-8")
        nonce = os.urandom(12)
        ciphertext = nonce + self._cipher.encrypt(nonce, plaintext, case_id.encode("ascii"))
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT d.expires_at, f.case_id FROM drafts d LEFT JOIN freezes f "
                "ON f.case_id=d.case_id WHERE d.case_id=?", (case_id,)
            ).fetchone()
            if row is None or (row[0] <= now and row[1] is None):
                raise DraftNotFound("case unavailable")
            if row[1] is not None:
                raise FreezeConflict("case already frozen")
            conn.execute("UPDATE drafts SET encrypted=? WHERE case_id=?", (ciphertext, case_id))
            conn.execute(
                "INSERT INTO confirmations(case_id,names) VALUES(?,?) "
                "ON CONFLICT(case_id) DO UPDATE SET names=excluded.names",
                (case_id, json.dumps(sorted(set(confirmed)))))

    def get_confirmed(self, case_id: str) -> list[str]:
        self._case_id(case_id)
        with self._connect() as conn:
            row = conn.execute("SELECT names FROM confirmations WHERE case_id=?",
                               (case_id,)).fetchone()
        return [] if row is None else list(json.loads(row[0]))

    # ---- blockers and runs ----------------------------------------------------------
    def record_blockers(self, case_id: str, blockers: list[dict]) -> None:
        self._case_id(case_id)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO blockers(case_id,blockers) VALUES(?,?) "
                "ON CONFLICT(case_id) DO UPDATE SET blockers=excluded.blockers",
                (case_id, json.dumps(blockers, sort_keys=True)))

    def get_blockers(self, case_id: str) -> list[dict]:
        self._case_id(case_id)
        with self._connect() as conn:
            row = conn.execute("SELECT blockers FROM blockers WHERE case_id=?",
                               (case_id,)).fetchone()
        return [] if row is None else list(json.loads(row[0]))

    def create_run(self, case_id: str, run_id: str, *, isolation: str, started_at: str) -> bool:
        """Insert a QUEUED run. Returns False if the case already has a run (idempotent)."""
        self._case_id(case_id)
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO runs(run_id,case_id,state,isolation,started_at,events) "
                    "VALUES(?,?,?,?,?,?)",
                    (run_id, case_id, "QUEUED", isolation, started_at, "[]"))
            return True
        except sqlite3.IntegrityError:
            return False

    def append_run_event(self, run_id: str, event: dict, *, state: str | None = None) -> None:
        """Persist one progress event (write-then-emit). Sequence must be contiguous."""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT events FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if row is None:
                raise DraftNotFound("run unavailable")
            events = json.loads(row[0])
            if event["seq"] != len(events):
                raise ValueError("non-contiguous progress event sequence")
            events.append(event)
            if state is None:
                conn.execute("UPDATE runs SET events=? WHERE run_id=?",
                             (json.dumps(events, sort_keys=True), run_id))
            else:
                conn.execute("UPDATE runs SET events=?, state=? WHERE run_id=?",
                             (json.dumps(events, sort_keys=True), state, run_id))

    def finish_run(self, run_id: str, *, state: str, finished_at: str,
                   outcome: dict | None, bundle_sha256: str | None) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET state=?, finished_at=?, outcome=?, bundle_sha256=? "
                "WHERE run_id=?",
                (state, finished_at, None if outcome is None else json.dumps(outcome, sort_keys=True),
                 bundle_sha256, run_id))

    def get_run(self, *, case_id: str | None = None, run_id: str | None = None) -> dict | None:
        with self._connect() as conn:
            if run_id is not None:
                row = conn.execute(
                    "SELECT run_id,case_id,state,isolation,started_at,finished_at,events,"
                    "outcome,bundle_sha256 FROM runs WHERE run_id=?", (run_id,)).fetchone()
            else:
                row = conn.execute(
                    "SELECT run_id,case_id,state,isolation,started_at,finished_at,events,"
                    "outcome,bundle_sha256 FROM runs WHERE case_id=?", (case_id,)).fetchone()
        if row is None:
            return None
        return {
            "runId": row[0], "caseId": row[1], "state": row[2], "isolationMode": row[3],
            "startedAt": row[4], "finishedAt": row[5], "events": json.loads(row[6]),
            "outcome": None if row[7] is None else json.loads(row[7]),
            "bundleSha256": row[8],
        }

    def bundle_path(self, case_id: str) -> Path:
        self._case_id(case_id)
        directory = self.directory / "bundles"
        if directory.is_symlink():
            raise ValueError("bundle storage cannot be a symlink")
        directory.mkdir(mode=0o700, exist_ok=True)
        return directory / f"{case_id}.vkb"
