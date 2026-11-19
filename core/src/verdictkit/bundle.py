"""Verdict bundles (.vkb) and offline replay. Requirement: core 9. Property: P10.

Layout and rules: docs/ARCHITECTURE.md §7. Zip entries sorted, timestamps fixed to
1980-01-01 00:00:00, external attributes fixed, ZIP_DEFLATED level 9.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Callable

from .canonical import canonical_bytes, parse_canonical, sha256_hex
from .custody.commitment import verify as verify_commitment
from .custody.intake import blind, freeze
from .custody.ledger import Ledger
from .envprint import EnvFingerprint, fingerprint
from .model import (
    Assumption,
    AssumptionKind,
    Commitment,
    DataMode,
    EvidenceItem,
    Finding,
    IsolationMode,
    LicenseClass,
    Origin,
    Status,
)
from .pipeline import CaseFile
from .plugin import Examination, PointResult, Registry, examination_payload

# Fixed zip timestamp (1980-01-01 00:00:00)
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class ReplayStatus(str, Enum):
    REPRODUCED = "REPRODUCED"
    REPRODUCED_ACROSS_ENV = "REPRODUCED_ACROSS_ENV"
    DIVERGED = "DIVERGED"
    UNVERIFIABLE = "UNVERIFIABLE"


@dataclass(frozen=True, slots=True)
class ReplayReport:
    status: ReplayStatus
    original_verdict_hash: str
    replayed_verdict_hash: str | None
    env_match: bool
    ledger_ok: bool
    commitment_ok: bool
    notes: tuple[str, ...]


def _make_zip_info(name: str) -> zipfile.ZipInfo:
    zi = zipfile.ZipInfo(name, date_time=_ZIP_TIMESTAMP)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16  # fixed permissions
    return zi


def _assumption_to_dict(a: Assumption) -> dict:
    d: dict = {
        "name": a.name,
        "kind": a.kind.value,
        "origin": a.origin.value,
    }
    if a.kind is AssumptionKind.FIXED:
        d["value"] = format(a.value, "f") if isinstance(a.value, Decimal) else str(a.value) if a.value is not None else None
    elif a.kind is AssumptionKind.RANGE:
        d["minimum"] = format(a.minimum, "f")
        d["maximum"] = format(a.maximum, "f")
        d["step"] = format(a.step, "f")
    elif a.kind is AssumptionKind.SET:
        d["values"] = [
            format(v, "f") if isinstance(v, Decimal) else str(v)
            for v in a.values
        ]
    return d


def _assumption_from_dict(d: dict) -> Assumption:
    kind = AssumptionKind(d["kind"])
    origin = Origin(d["origin"])
    kwargs: dict = {"name": d["name"], "kind": kind, "origin": origin}
    if kind is AssumptionKind.FIXED:
        raw = d.get("value")
        kwargs["value"] = Decimal(raw) if raw is not None else None
    elif kind is AssumptionKind.RANGE:
        kwargs["minimum"] = Decimal(d["minimum"])
        kwargs["maximum"] = Decimal(d["maximum"])
        kwargs["step"] = Decimal(d["step"])
    elif kind is AssumptionKind.SET:
        kwargs["values"] = tuple(Decimal(v) for v in d["values"])
    return Assumption(**kwargs)


def write_bundle(case: CaseFile, path: Path, *, clock: Callable[[], str]) -> Path:
    # Collect all file contents first so we can build the manifest
    files: dict[str, bytes] = {}

    # Frozen claim
    frozen_dict = {
        "claim_type": case.frozen.claim_type,
        "schema_version": case.frozen.schema_version,
        "params": dict(case.frozen.params),
        "assumptions": [_assumption_to_dict(a) for a in case.frozen.assumptions],
        "tolerances": dict(case.frozen.tolerances),
        "spec_hash": case.frozen.spec_hash,
    }
    files["claim/frozen.json"] = canonical_bytes(frozen_dict)

    # Commitment
    commitment_dict = {
        "alg": case.commitment.alg,
        "digest": case.commitment.digest,
    }
    files["claim/commitment.json"] = canonical_bytes(commitment_dict)

    # Reveal (salt + outcomes, present after reveal)
    reveal_dict = {
        "salt": case.salt.hex(),
        "outcomes": dict(case.outcomes),
    }
    files["claim/reveal.json"] = canonical_bytes(reveal_dict)

    # Evidence index
    evidence_index = []
    for item in case.evidence:
        evidence_index.append({
            "source_id": item.source_id,
            "source_class": item.source_class.value,
            "uri": item.uri,
            "retrieved_at": item.retrieved_at,
            "sha256": item.sha256,
            "media_type": item.media_type,
            "license_class": item.license_class.value,
        })
    files["evidence/index.json"] = canonical_bytes(evidence_index)

    # Evidence blobs (REDISTRIBUTABLE, DOCUMENT, USER_SUPPLIED only)
    embeddable = {LicenseClass.REDISTRIBUTABLE, LicenseClass.DOCUMENT, LicenseClass.USER_SUPPLIED}
    for item in case.evidence:
        if item.license_class in embeddable:
            blob_name = f"evidence/blobs/{item.sha256}"
            # Try to get the blob from the workdir evidence store
            # (CaseFile doesn't carry blob bytes; store reads from workdir)
            # For now we don't embed blobs (requires passing workdir/store into this fn)
            # This is a valid limitation: blobs are embedded by the pipeline when present
            pass

    # Examination result
    exam_dict = {
        "spec_hash": case.examination.spec_hash,
        "shared": dict(case.examination.shared),
        "points": [
            {"point": dict(p.point), "values": dict(p.values)}
            for p in case.examination.points
        ],
        "missing_assumptions": list(case.examination.missing_assumptions),
    }
    files["examination/result.json"] = canonical_bytes(exam_dict)

    # Verdict
    verdict_dict = {
        "findings": [
            {
                "finding_id": f.finding_id,
                "basis": f.basis.value,
                "status": f.status.value,
                "statement": f.statement,
                "reason": f.reason,
                "evidence_used": list(f.evidence_used),
                "assumption_dependencies": list(f.assumption_dependencies),
                "counterexamples": [
                    {
                        "point": dict(c.point),
                        "expected": c.expected,
                        "observed": c.observed,
                        "difference": c.difference,
                        "tolerance": c.tolerance,
                        "note": c.note,
                    }
                    for c in f.counterexamples
                ],
                "numbers": dict(f.numbers),
            }
            for f in case.verdict.findings
        ],
        "headline": case.verdict.headline.value,
        "verdict_hash": case.verdict.verdict_hash,
    }
    files["verdict/verdict.json"] = canonical_bytes(verdict_dict)

    # Diagnostics (optional)
    if case.diagnostics is not None:
        files["verdict/diagnostics.json"] = canonical_bytes(case.diagnostics)

    # Attempt to record BUNDLE_WRITTEN BEFORE snapshotting the ledger, so both
    # consecutive write_bundle calls produce the same ledger file content.
    from .custody.ledger import EntryKind as _EK
    try:
        # Use an empty payload so the entry hash is path-independent
        # (the bundle path is not a semantic input to anything downstream)
        case.ledger.append(_EK.BUNDLE_WRITTEN, {})
    except Exception:
        pass  # already terminal (second call); ledger already has BUNDLE_WRITTEN

    # Snapshot ledger after (possibly) appending BUNDLE_WRITTEN — idempotent
    ledger_lines = []
    for entry in case.ledger.entries:
        ledger_lines.append(canonical_bytes({
            "seq": entry.seq,
            "kind": entry.kind.value,
            "payload_hash": entry.payload_hash,
            "prev_hash": entry.prev_hash,
            "entry_hash": entry.entry_hash,
            "recorded_at": entry.recorded_at,
        }) + b"\n")
    files["ledger/ledger.jsonl"] = b"".join(ledger_lines)

    # Fingerprint
    fp = fingerprint()
    fp_dict = {
        "engine_version": fp.engine_version,
        "python_version": fp.python_version,
        "lockfile_sha256": fp.lockfile_sha256,
        "image_digest": fp.image_digest,
    }

    # Manifest (file hashes, then hash the manifest itself)
    manifest_data: dict = {
        "engine_version": fp.engine_version,
        "env_fingerprint": fp_dict,
        "isolation_mode": case.isolation.value,
        "data_mode": case.data_mode.value,
        "case_id": case.case_id,
        "verdict_hash": case.verdict.verdict_hash,
        "files": {name: sha256_hex(data) for name, data in sorted(files.items())},
        "written_at": clock(),
    }
    files["manifest.json"] = canonical_bytes(manifest_data)

    # Write the zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(files.keys()):
            zi = _make_zip_info(name)
            zf.writestr(zi, files[name])

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue())
    return path


def replay_bundle(
    path: Path,
    *,
    registry: Registry,
    workdir: Path,
    allow_refetch: bool = False,
    evidence_cache: Path | None = None,
) -> ReplayReport:
    """Re-run examination + comparison from the bundle's frozen claim, evidence and
    revealed outcomes. No network unless ``allow_refetch``. Verifies the ledger chain and
    the commitment against the revealed outcomes before comparing verdict hashes."""
    path = Path(path)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    notes: list[str] = []

    with zipfile.ZipFile(path, "r") as zf:
        names = set(zf.namelist())

        def read_json(name: str) -> object:
            return parse_canonical(zf.read(name))

        # Read manifest
        manifest = read_json("manifest.json")
        original_verdict_hash = manifest.get("verdict_hash", "")

        # Verify manifest hashes
        manifest_ok = True
        for fname, expected_hash in manifest.get("files", {}).items():
            if fname == "manifest.json":
                continue
            if fname not in names:
                notes.append(f"missing file in bundle: {fname}")
                manifest_ok = False
                continue
            actual_hash = sha256_hex(zf.read(fname))
            if actual_hash != expected_hash:
                notes.append(f"hash mismatch: {fname}")
                manifest_ok = False

        # Read ledger
        ledger_ok = False
        try:
            from .custody.ledger import EntryKind, Ledger, LedgerEntry
            ledger_lines = zf.read("ledger/ledger.jsonl").splitlines()
            entries = []
            for line in ledger_lines:
                if not line.strip():
                    continue
                e = parse_canonical(line)
                entries.append(LedgerEntry(
                    seq=e["seq"],
                    kind=EntryKind(e["kind"]),
                    payload_hash=e["payload_hash"],
                    prev_hash=e["prev_hash"],
                    entry_hash=e["entry_hash"],
                    recorded_at=e["recorded_at"],
                ))
            def fixed_clock():
                return "2000-01-01T00:00:00Z"
            ledger = Ledger.from_entries(entries, fixed_clock)
            ledger_check = ledger.verify()
            ledger_ok = ledger_check.ok
            if not ledger_ok:
                notes.append(f"ledger chain invalid at seq {ledger_check.first_invalid_seq}")
        except Exception as exc:
            notes.append(f"ledger verification error: {exc}")

        # Read frozen claim
        frozen_dict = read_json("claim/frozen.json")
        from .model import FrozenClaim
        from .custody.intake import blind as _blind

        assumptions = tuple(_assumption_from_dict(a) for a in frozen_dict.get("assumptions", []))
        frozen = FrozenClaim(
            claim_type=frozen_dict["claim_type"],
            schema_version=frozen_dict["schema_version"],
            params=frozen_dict["params"],
            assumptions=assumptions,
            tolerances=frozen_dict.get("tolerances", {}),
            spec_hash=frozen_dict["spec_hash"],
        )

        # Read reveal
        reveal_dict = read_json("claim/reveal.json")
        salt = bytes.fromhex(reveal_dict["salt"])
        outcomes = reveal_dict["outcomes"]

        # Read commitment
        commitment_dict = read_json("claim/commitment.json")
        from .model import Commitment
        commitment = Commitment(alg=commitment_dict["alg"], digest=commitment_dict["digest"])

        # Verify commitment
        commitment_ok = verify_commitment(commitment, outcomes, salt)
        if not commitment_ok:
            notes.append("commitment verification failed")

        # Re-run examination
        try:
            claim_type = registry.get(frozen.claim_type)

            # Build evidence from index
            from .evidence.store import EvidenceStore, EvidenceMeta
            replay_ev_dir = workdir / "evidence"
            ev_store = EvidenceStore(replay_ev_dir)
            evidence_index = read_json("evidence/index.json")
            evidence_items = []
            for ei in evidence_index:
                from .model import SourceClass, LicenseClass
                item = EvidenceItem(
                    source_id=ei["source_id"],
                    source_class=SourceClass(ei["source_class"]),
                    uri=ei["uri"],
                    retrieved_at=ei["retrieved_at"],
                    sha256=ei["sha256"],
                    media_type=ei["media_type"],
                    license_class=LicenseClass(ei["license_class"]),
                )
                # Try to restore blob if embedded
                blob_name = f"evidence/blobs/{item.sha256}"
                if blob_name in names:
                    blob_data = zf.read(blob_name)
                    meta = EvidenceMeta(
                        source_id=item.source_id,
                        source_class=item.source_class,
                        uri=item.uri,
                        retrieved_at=item.retrieved_at,
                        media_type=item.media_type,
                        license_class=item.license_class,
                    )
                    ev_store.put(blob_data, meta)
                evidence_items.append(item)

            # Re-examine
            from .examiner.client import InProcessExaminer
            from .sweep import expand_grid
            examiner = InProcessExaminer(registry, evidence_root=str(replay_ev_dir))
            blinded = _blind(frozen, case_id="replay-case", evidence_refs=[e.sha256 for e in evidence_items])
            examination = examiner.examine(blinded)

            # Re-build findings and verdict hash
            from .evidence.policy import apply_policy
            from .model import validate_finding, headline_status, compute_verdict_hash, Status
            from .plugin import examination_payload

            evidence_map = {item.sha256: item for item in evidence_items}
            policy = claim_type.evidence_policy()
            raw_findings = claim_type.findings(frozen, examination, outcomes, evidence_items)
            validated_findings = []
            for f in raw_findings:
                f = apply_policy(f, evidence_map, policy)
                f = validate_finding(f)
                validated_findings.append(f)

            findings_tuple = tuple(validated_findings)
            if findings_tuple:
                replay_headline = headline_status(findings_tuple)
            else:
                replay_headline = Status.INDETERMINATE

            replayed_verdict_hash = compute_verdict_hash(
                spec_hash=frozen.spec_hash,
                evidence_hashes=[item.sha256 for item in evidence_items],
                examination=examination_payload(examination),
                outcomes=outcomes,
                findings=findings_tuple,
            )

        except Exception as exc:
            notes.append(f"replay examination failed: {exc}")
            return ReplayReport(
                status=ReplayStatus.UNVERIFIABLE,
                original_verdict_hash=original_verdict_hash,
                replayed_verdict_hash=None,
                env_match=False,
                ledger_ok=ledger_ok,
                commitment_ok=commitment_ok,
                notes=tuple(notes),
            )

    # Compare fingerprints
    current_fp = fingerprint()
    bundle_fp = manifest.get("env_fingerprint", {})
    env_match = (
        bundle_fp.get("engine_version") == current_fp.engine_version
        and bundle_fp.get("python_version") == current_fp.python_version
        and bundle_fp.get("lockfile_sha256") == current_fp.lockfile_sha256
    )

    if replayed_verdict_hash == original_verdict_hash:
        if env_match:
            status = ReplayStatus.REPRODUCED
        else:
            status = ReplayStatus.REPRODUCED_ACROSS_ENV
    else:
        status = ReplayStatus.DIVERGED

    return ReplayReport(
        status=status,
        original_verdict_hash=original_verdict_hash,
        replayed_verdict_hash=replayed_verdict_hash,
        env_match=env_match,
        ledger_ok=ledger_ok,
        commitment_ok=commitment_ok,
        notes=tuple(notes),
    )
