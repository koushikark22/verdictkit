"""Single-state rules snapshot. Requirement: quote 5.1. State chosen at decision B7.

Snapshot file ``rules/<STATE>.json`` (canonical JSON):
  {"state", "state_rate_pct", "local_rate_min_pct", "local_rate_max_pct",
   "localities": {code: combined_rate_pct} | null,
   "doc_fee": {"kind": "STATUTORY_MAXIMUM" | "PRESUMED_REASONABLE_AMOUNT" | "NO_STATUTORY_LIMIT",
               "amount": "<decimal string>" | null, "applies_to": "RETAIL_INSTALLMENT_CONTRACT"},
   "sources": [{"uri", "retrieved_at", "sha256_of_source"}]}
The loader verifies the file's own SHA-256 against ``rules/MANIFEST.json``.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from verdictkit.canonical import canonical_bytes, parse_canonical

_DECIMAL = re.compile(r"^[0-9]+(\.[0-9]+)?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
DOC_FEE_KINDS = frozenset({"STATUTORY_MAXIMUM", "PRESUMED_REASONABLE_AMOUNT", "NO_STATUTORY_LIMIT"})
DOC_FEE_APPLIES_TO = "RETAIL_INSTALLMENT_CONTRACT"
MAX_SNAPSHOT_BYTES = 1024 * 1024


class RulesIntegrityError(ValueError):
    """The snapshot is missing, malformed or does not match its manifest hash.

    Callers map this to INDETERMINATE(evidence_integrity) for external findings."""


@dataclass(frozen=True, slots=True)
class StateRules:
    state: str
    state_rate_pct: Decimal
    local_rate_min_pct: Decimal
    local_rate_max_pct: Decimal
    localities: dict[str, Decimal] | None
    doc_fee_kind: str
    doc_fee_amount: Decimal | None
    snapshot_sha256: str

    def combined_rate(self, locality_code: str) -> Decimal | None:
        """Official combined (state + local) rate for a locality; None if unknown."""
        if self.localities is None:
            return None
        return self.localities.get(locality_code)

    def rate_range(self) -> tuple[Decimal, Decimal]:
        """Official combined-rate range: state rate plus the local add-on range."""
        return (self.state_rate_pct + self.local_rate_min_pct,
                self.state_rate_pct + self.local_rate_max_pct)


def _pct(value: object, name: str) -> Decimal:
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise RulesIntegrityError(f"{name} must be a non-negative decimal string")
    try:
        d = Decimal(value)
    except InvalidOperation as exc:
        raise RulesIntegrityError(f"invalid {name}") from exc
    if d > Decimal(100):
        raise RulesIntegrityError(f"{name} out of range")
    return d


def load_rules(path: Path, manifest: Path) -> StateRules:
    """Load a single-state snapshot after verifying its SHA-256 against the manifest.

    The manifest is ``{"files": {"<file name>": "<sha256>"}}``. The snapshot must be
    canonical JSON (no floats, sorted keys) so that its hash is unambiguous.
    """
    path, manifest = Path(path), Path(manifest)
    try:
        if path.stat().st_size > MAX_SNAPSHOT_BYTES or manifest.stat().st_size > MAX_SNAPSHOT_BYTES:
            raise RulesIntegrityError("rules file too large")
        data = path.read_bytes()
        listing = json.loads(manifest.read_bytes())
    except (OSError, ValueError) as exc:
        raise RulesIntegrityError("rules snapshot or manifest unreadable") from exc
    expected = listing.get("files", {}).get(path.name) if isinstance(listing, dict) else None
    if not isinstance(expected, str) or not _SHA256.fullmatch(expected):
        raise RulesIntegrityError("snapshot not listed in manifest")
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RulesIntegrityError("snapshot hash does not match manifest")
    try:
        doc = parse_canonical(data)
    except Exception as exc:
        raise RulesIntegrityError("snapshot is not canonical JSON") from exc
    if not isinstance(doc, dict) or canonical_bytes(doc) != data:
        raise RulesIntegrityError("snapshot is not canonical JSON")
    required = {"state", "state_rate_pct", "local_rate_min_pct", "local_rate_max_pct",
                "localities", "doc_fee", "sources"}
    if set(doc) != required:
        raise RulesIntegrityError("snapshot fields do not match the schema")
    state = doc["state"]
    if not isinstance(state, str) or not re.fullmatch(r"[A-Z]{2}", state):
        raise RulesIntegrityError("state must be a two-letter upper-case code")
    lo = _pct(doc["local_rate_min_pct"], "local_rate_min_pct")
    hi = _pct(doc["local_rate_max_pct"], "local_rate_max_pct")
    if lo > hi:
        raise RulesIntegrityError("local rate range is inverted")
    localities = doc["localities"]
    if localities is not None:
        if not isinstance(localities, dict):
            raise RulesIntegrityError("localities must be an object or null")
        localities = {str(k): _pct(v, f"localities.{k}") for k, v in localities.items()}
    doc_fee_kind, doc_fee_amount = _doc_fee(doc["doc_fee"])
    sources = doc["sources"]
    if not isinstance(sources, list) or not sources:
        raise RulesIntegrityError("at least one official source is required")
    for src in sources:
        if (not isinstance(src, dict) or set(src) != {"uri", "retrieved_at", "sha256_of_source"}
                or not isinstance(src["uri"], str) or not src["uri"].startswith("https://")
                or not isinstance(src["retrieved_at"], str)
                or not isinstance(src["sha256_of_source"], str)
                or not _SHA256.fullmatch(src["sha256_of_source"])):
            raise RulesIntegrityError("invalid source record")
    return StateRules(
        state=state,
        state_rate_pct=_pct(doc["state_rate_pct"], "state_rate_pct"),
        local_rate_min_pct=lo, local_rate_max_pct=hi,
        localities=localities, doc_fee_kind=doc_fee_kind, doc_fee_amount=doc_fee_amount,
        snapshot_sha256=actual,
    )


def _doc_fee(value: object) -> tuple[str, Decimal | None]:
    if not isinstance(value, dict) or set(value) != {"kind", "amount", "applies_to"}:
        raise RulesIntegrityError("doc_fee must be an object with kind, amount and applies_to")
    kind = value["kind"]
    if not isinstance(kind, str) or kind not in DOC_FEE_KINDS:
        raise RulesIntegrityError("doc_fee.kind is not a recognised rule kind")
    if value["applies_to"] != DOC_FEE_APPLIES_TO:
        raise RulesIntegrityError("doc_fee.applies_to must be RETAIL_INSTALLMENT_CONTRACT")
    amount = value["amount"]
    if kind == "NO_STATUTORY_LIMIT":
        if amount is not None:
            raise RulesIntegrityError("doc_fee.amount must be null when there is no statutory limit")
        return kind, None
    if not isinstance(amount, str) or not _DECIMAL.fullmatch(amount):
        raise RulesIntegrityError("doc_fee.amount must be a non-negative decimal string")
    return kind, Decimal(amount)
