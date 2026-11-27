"""Verdict bundles (.vkb) and offline replay. Requirement: core 9. Property: P10.

Layout and rules: docs/ARCHITECTURE.md §7. Zip entries sorted, timestamps fixed to
1980-01-01 00:00:00, external attributes fixed, ZIP_DEFLATED level 9.
"""
from __future__ import annotations

import io
import os
import zipfile
import zlib
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Callable

from .canonical import canonical_bytes, parse_canonical, sha256_hex
from .custody.commitment import verify as verify_commitment
from .custody.intake import blind
from .custody.ledger import Ledger
from .envprint import fingerprint
from .model import (
    Assumption,
    AssumptionKind,
    Commitment,
    EvidenceItem,
    Origin,
)
from .pipeline import CaseFile
from .plugin import Registry, examination_payload
from .signing import SIGNATURE_MEMBER, Signer, build_envelope, bundle_authenticity, unsigned_authenticity

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
    manifest_ok: bool = True
    spec_hash_ok: bool = True


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


def write_bundle(case: CaseFile, path: Path, *, clock: Callable[[], str],
                 signer: "Signer | None" = None) -> Path:
    """Write the bundle. ``signer`` (already loaded and validated by the caller, so a bad key
    fails before any file or ledger entry exists) adds ``signature/envelope.json`` over the
    exact manifest bytes. The envelope is not listed in the manifest and never feeds the
    verdict hash, so unsigned bytes and every verdict hash are unchanged."""
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

    # Evidence blobs (REDISTRIBUTABLE, DOCUMENT, USER_SUPPLIED only; Req 9.2).
    # REFETCH_ONLY evidence is sealed by URI + SHA-256 only and never embedded.
    from .pipeline import EMBEDDABLE as embeddable
    for item in case.evidence:
        if item.license_class not in embeddable:
            continue
        blob = case.evidence_blobs.get(item.sha256)
        if blob is None:
            raise ValueError(f"embeddable evidence bytes missing for {item.sha256}")
        if sha256_hex(blob) != item.sha256:
            raise ValueError(f"evidence bytes do not match recorded hash {item.sha256}")
        files[f"evidence/blobs/{item.sha256}"] = blob

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
    if signer is not None:
        files[SIGNATURE_MEMBER] = build_envelope(signer, files["manifest.json"])

    # Write the zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(files.keys()):
            zi = _make_zip_info(name)
            zf.writestr(zi, files[name])

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic: a failed write leaves neither a partial bundle nor a temporary file.
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_bytes(buf.getvalue())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path


# Limits applied before any bundle content is parsed (malformed-input / DoS resistance).
MAX_BUNDLE_ENTRIES = 4096
MAX_BUNDLE_UNCOMPRESSED = 64 * 1024 * 1024
MAX_ENTRY_UNCOMPRESSED = 16 * 1024 * 1024
_REQUIRED_ENTRIES = (
    "manifest.json", "claim/frozen.json", "claim/commitment.json", "claim/reveal.json",
    "evidence/index.json", "examination/result.json", "verdict/verdict.json",
    "ledger/ledger.jsonl",
)


class BundleFormatError(ValueError):
    """The file is not a structurally valid, size-bounded VerdictKit bundle."""


def _check_zip_safety(zf: zipfile.ZipFile) -> set[str]:
    infos = zf.infolist()
    if len(infos) > MAX_BUNDLE_ENTRIES:
        raise BundleFormatError("too many bundle entries")
    total = 0
    names: set[str] = set()
    for info in infos:
        name = info.filename
        if (name.startswith("/") or "\\" in name or ".." in name.split("/")
                or name in names or info.is_dir()):
            raise BundleFormatError("unsafe or duplicate bundle entry name")
        if info.file_size > MAX_ENTRY_UNCOMPRESSED:
            raise BundleFormatError("bundle entry too large")
        total += info.file_size
        if total > MAX_BUNDLE_UNCOMPRESSED:
            raise BundleFormatError("bundle too large when uncompressed")
        names.add(name)
    missing = [n for n in _REQUIRED_ENTRIES if n not in names]
    if missing:
        raise BundleFormatError("bundle is missing required entries")
    return names


def _read_bounded(zf: zipfile.ZipFile, name: str) -> bytes:
    try:
        with zf.open(name) as fh:
            data = fh.read(MAX_ENTRY_UNCOMPRESSED + 1)
    except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError) as exc:
        # Corrupt entry (bad CRC, broken deflate stream, unsupported method).
        raise BundleFormatError("bundle entry is corrupt") from exc
    if len(data) > MAX_ENTRY_UNCOMPRESSED:
        raise BundleFormatError("bundle entry too large")
    return data


def _spec_hash_of(frozen_dict: dict) -> str:
    from .custody.intake import _assumptions_to_hash_form
    assumptions = tuple(_assumption_from_dict(a) for a in frozen_dict.get("assumptions", []))
    return sha256_hex(canonical_bytes({
        "claim_type": frozen_dict["claim_type"],
        "schema_version": frozen_dict["schema_version"],
        "params": frozen_dict["params"],
        "assumptions": _assumptions_to_hash_form(assumptions),
        "tolerances": frozen_dict.get("tolerances", {}),
    }))


@dataclass(frozen=True, slots=True)
class IntegrityResult:
    manifest_ok: bool
    ledger_ok: bool
    commitment_ok: bool
    spec_hash_ok: bool
    notes: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.manifest_ok and self.ledger_ok and self.commitment_ok and self.spec_hash_ok


def _integrity(zf: zipfile.ZipFile, names: set[str]) -> tuple[IntegrityResult, dict]:
    """Internal-consistency checks only (no re-execution). Returns the parsed parts."""
    from .custody.ledger import EntryKind, LedgerEntry

    notes: list[str] = []
    manifest = parse_canonical(_read_bounded(zf, "manifest.json"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise BundleFormatError("invalid manifest")

    manifest_ok = True
    listed = set(manifest["files"])
    for fname, expected_hash in sorted(manifest["files"].items()):
        if fname not in names:
            notes.append(f"missing file in bundle: {fname}")
            manifest_ok = False
            continue
        if sha256_hex(_read_bounded(zf, fname)) != expected_hash:
            notes.append(f"hash mismatch: {fname}")
            manifest_ok = False
    # The signature envelope is the one member the manifest never lists (design D5.4).
    unlisted = sorted(names - listed - {"manifest.json", SIGNATURE_MEMBER})
    if unlisted:
        manifest_ok = False
        notes.append("bundle contains files not listed in the manifest")

    ledger_ok = False
    try:
        entries = []
        for line in _read_bounded(zf, "ledger/ledger.jsonl").splitlines():
            if not line.strip():
                continue
            e = parse_canonical(line)
            entries.append(LedgerEntry(
                seq=e["seq"], kind=EntryKind(e["kind"]), payload_hash=e["payload_hash"],
                prev_hash=e["prev_hash"], entry_hash=e["entry_hash"],
                recorded_at=e["recorded_at"],
            ))
        check = Ledger.from_entries(entries, lambda: "2000-01-01T00:00:00Z").verify()
        kinds = [e.kind for e in entries]
        ledger_ok = check.ok and EntryKind.VERDICT_SEALED in kinds
        if not check.ok:
            notes.append(f"ledger chain invalid at seq {check.first_invalid_seq}")
        elif EntryKind.VERDICT_SEALED not in kinds:
            notes.append("ledger has no sealed verdict")
    except Exception:
        notes.append("ledger could not be parsed")

    frozen_dict = parse_canonical(_read_bounded(zf, "claim/frozen.json"))
    reveal = parse_canonical(_read_bounded(zf, "claim/reveal.json"))
    commitment_dict = parse_canonical(_read_bounded(zf, "claim/commitment.json"))
    if not all(isinstance(x, dict) for x in (frozen_dict, reveal, commitment_dict)):
        raise BundleFormatError("invalid claim records")

    try:
        spec_hash_ok = _spec_hash_of(frozen_dict) == frozen_dict.get("spec_hash")
    except Exception:
        spec_hash_ok = False
    if not spec_hash_ok:
        notes.append("spec hash does not match frozen claim")

    try:
        salt = bytes.fromhex(reveal["salt"])
        commitment = Commitment(alg=commitment_dict["alg"], digest=commitment_dict["digest"])
        commitment_ok = len(salt) == 32 and verify_commitment(commitment, reveal["outcomes"], salt)
    except Exception:
        commitment_ok = False
    if not commitment_ok:
        notes.append("commitment verification failed")

    return (IntegrityResult(manifest_ok, ledger_ok, commitment_ok, spec_hash_ok, tuple(notes)),
            {"manifest": manifest, "frozen": frozen_dict, "reveal": reveal})


def verify_bundle_integrity(path: Path) -> tuple[IntegrityResult, dict]:
    """Integrity of a bundle since it was written (no re-execution, no network)."""
    try:
        with zipfile.ZipFile(Path(path), "r") as zf:
            names = _check_zip_safety(zf)
            return _integrity(zf, names)
    except (zipfile.BadZipFile, BundleFormatError, KeyError, ValueError, OSError):
        return IntegrityResult(False, False, False, False, ("bundle is malformed",)), {}


def replay_bundle(
    path: Path,
    *,
    registry: Registry,
    workdir: Path,
    allow_refetch: bool = False,
    evidence_cache: Path | None = None,
    examiner=None,
    evidence_root: Path | None = None,
) -> ReplayReport:
    """Re-run examination + comparison from the bundle's frozen claim, evidence and
    revealed outcomes. No network unless ``allow_refetch``. Verifies the ledger chain, the
    spec hash and the commitment against the revealed outcomes before comparing verdict
    hashes. Malformed or oversized bundles yield ``UNVERIFIABLE``, never an exception.

    ``examiner`` defaults to an in-process examiner; services pass their configured
    (isolated) examiner so untrusted bundles are evaluated under the same boundary."""
    path = Path(path)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    def unverifiable(note: str, *, original: str = "", ledger_ok: bool = False,
                     commitment_ok: bool = False, manifest_ok: bool = False,
                     spec_hash_ok: bool = False, prior: tuple[str, ...] = ()) -> ReplayReport:
        return ReplayReport(
            status=ReplayStatus.UNVERIFIABLE, original_verdict_hash=original,
            replayed_verdict_hash=None, env_match=False, ledger_ok=ledger_ok,
            commitment_ok=commitment_ok, notes=prior + (note,),
            manifest_ok=manifest_ok, spec_hash_ok=spec_hash_ok,
        )

    try:
        zf = zipfile.ZipFile(path, "r")
    except (zipfile.BadZipFile, OSError):
        return unverifiable("bundle is not a readable zip archive")

    with zf:
        try:
            names = _check_zip_safety(zf)
            integrity, parts = _integrity(zf, names)
        except (BundleFormatError, KeyError, ValueError, TypeError):
            return unverifiable("bundle is malformed")

        manifest = parts["manifest"]
        original_verdict_hash = manifest.get("verdict_hash", "")
        if not isinstance(original_verdict_hash, str):
            original_verdict_hash = ""
        notes = list(integrity.notes)
        common = dict(original=original_verdict_hash, ledger_ok=integrity.ledger_ok,
                      commitment_ok=integrity.commitment_ok,
                      manifest_ok=integrity.manifest_ok, spec_hash_ok=integrity.spec_hash_ok)
        if not integrity.ok:
            # Never re-execute content that failed integrity checks.
            return unverifiable("integrity checks failed; not re-executed",
                                prior=tuple(notes), **common)

        frozen_dict = parts["frozen"]
        reveal_dict = parts["reveal"]
        outcomes = reveal_dict["outcomes"]

        try:
            from .model import FrozenClaim, LicenseClass, SourceClass
            from .evidence.store import EvidenceMeta, EvidenceStore, check_sha256

            claim_type = registry.get(frozen_dict["claim_type"])
            assumptions = tuple(_assumption_from_dict(a) for a in frozen_dict.get("assumptions", []))
            frozen = FrozenClaim(
                claim_type=frozen_dict["claim_type"],
                schema_version=frozen_dict["schema_version"],
                params=frozen_dict["params"],
                assumptions=assumptions,
                tolerances=frozen_dict.get("tolerances", {}),
                spec_hash=frozen_dict["spec_hash"],
            )
            # Restored bytes are hash-checked before being stored; ``evidence_root`` lets a
            # service place them where its isolated examiner can read them.
            replay_ev_dir = Path(evidence_root) if evidence_root is not None else workdir / "evidence"
            ev_store = EvidenceStore(replay_ev_dir)
            evidence_index = parse_canonical(_read_bounded(zf, "evidence/index.json"))
            if not isinstance(evidence_index, list):
                raise BundleFormatError("invalid evidence index")
            evidence_items = []
            for ei in evidence_index:
                item = EvidenceItem(
                    source_id=ei["source_id"], source_class=SourceClass(ei["source_class"]),
                    uri=ei["uri"], retrieved_at=ei["retrieved_at"], sha256=ei["sha256"],
                    media_type=ei["media_type"], license_class=LicenseClass(ei["license_class"]),
                )
                # The index comes from the uploaded bundle. Its hash becomes a member name and a
                # cache file name, so it must be exactly 64 lowercase hex characters.
                check_sha256(item.sha256)
                blob_name = f"evidence/blobs/{item.sha256}"
                if blob_name in names:
                    blob = _read_bounded(zf, blob_name)
                    if sha256_hex(blob) != item.sha256:
                        raise BundleFormatError("embedded evidence hash mismatch")
                    ev_store.put(blob, EvidenceMeta(
                        source_id=item.source_id, source_class=item.source_class,
                        uri=item.uri, retrieved_at=item.retrieved_at,
                        media_type=item.media_type, license_class=item.license_class,
                    ))
                elif evidence_cache is not None and (Path(evidence_cache) / item.sha256).is_file():
                    cached = (Path(evidence_cache) / item.sha256).read_bytes()
                    if sha256_hex(cached) != item.sha256:
                        return unverifiable("cached evidence fails its hash", prior=tuple(notes), **common)
                    ev_store.put(cached, EvidenceMeta(
                        source_id=item.source_id, source_class=item.source_class,
                        uri=item.uri, retrieved_at=item.retrieved_at,
                        media_type=item.media_type, license_class=item.license_class,
                    ))
                else:
                    # Offline replay cannot reproduce without the sealed bytes (Req 9.3, 9.4).
                    reason = ("required evidence absent; refetch is not implemented for this source"
                              if allow_refetch else "required evidence absent (offline replay)")
                    return unverifiable(reason, prior=tuple(notes), **common)
                evidence_items.append(item)

            if examiner is None:
                from .examiner.client import InProcessExaminer
                examiner = InProcessExaminer(registry, evidence_root=str(replay_ev_dir))
            blinded = blind(frozen, case_id="replay-case",
                            evidence_refs=[e.sha256 for e in evidence_items])
            examination = examiner.examine(blinded)
            if examination.spec_hash != frozen.spec_hash:
                return unverifiable("examiner returned a different specification",
                                    prior=tuple(notes), **common)

            from .evidence.policy import apply_policy, effective_policy
            from .model import DataMode
            from .model import compute_verdict_hash, validate_finding

            evidence_map = {item.sha256: item for item in evidence_items}
            try:
                bundle_mode = DataMode(manifest.get("data_mode", "LIVE_EVIDENCE"))
            except ValueError:
                return unverifiable("unknown data mode in manifest", prior=tuple(notes), **common)
            policy = effective_policy(claim_type.evidence_policy(), bundle_mode)
            findings_tuple = tuple(
                validate_finding(apply_policy(f, evidence_map, policy))
                for f in claim_type.findings(frozen, examination, outcomes, evidence_items)
            )
            replayed_verdict_hash = compute_verdict_hash(
                spec_hash=frozen.spec_hash,
                evidence_hashes=[item.sha256 for item in evidence_items],
                examination=examination_payload(examination),
                outcomes=outcomes,
                findings=findings_tuple,
            )
        except Exception as exc:  # untrusted input: report, never raise
            return unverifiable(f"replay examination failed ({type(exc).__name__})",
                                prior=tuple(notes), **common)

    current_fp = fingerprint()
    bundle_fp = manifest.get("env_fingerprint", {})
    if not isinstance(bundle_fp, dict):
        bundle_fp = {}
    env_match = (
        bundle_fp.get("engine_version") == current_fp.engine_version
        and bundle_fp.get("python_version") == current_fp.python_version
        and bundle_fp.get("lockfile_sha256") == current_fp.lockfile_sha256
    )

    if replayed_verdict_hash == original_verdict_hash:
        status = ReplayStatus.REPRODUCED if env_match else ReplayStatus.REPRODUCED_ACROSS_ENV
    else:
        status = ReplayStatus.DIVERGED

    return ReplayReport(
        status=status,
        original_verdict_hash=original_verdict_hash,
        replayed_verdict_hash=replayed_verdict_hash,
        env_match=env_match,
        ledger_ok=integrity.ledger_ok,
        commitment_ok=integrity.commitment_ok,
        notes=tuple(notes),
        manifest_ok=integrity.manifest_ok,
        spec_hash_ok=integrity.spec_hash_ok,
    )


_SHA256_RE = __import__("re").compile(r"^[0-9a-f]{64}$")


def integrity_dict(result: "IntegrityResult | ReplayReport") -> dict:
    checks = [
        {"check": "MANIFEST_HASHES", "ok": result.manifest_ok},
        {"check": "LEDGER_CHAIN", "ok": result.ledger_ok},
        {"check": "COMMITMENT", "ok": result.commitment_ok},
        {"check": "SPEC_HASH", "ok": result.spec_hash_ok},
    ]
    ok = all(c["ok"] for c in checks)
    return {"status": "VERIFIED" if ok else "FAILED", "checks": checks}


def verifier_time() -> str:
    """The verifier's clock for trust evaluation (``as_of``). Never an evaluator or comparator input."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def authenticity_dict(path: Path, result: "IntegrityResult | ReplayReport", *, as_of: str | None = None,
                      trust_store_file: str | None = None, trust_store_sha256: str | None = None) -> dict:
    """The contract ``AuthenticityReport`` for a bundle file, from the signature check, the
    operator's trust store and the integrity result. Offline; reads only the archive and the store."""
    return bundle_authenticity(
        path, integrity_ok=integrity_dict(result)["status"] == "VERIFIED",
        as_of=as_of or verifier_time(), trust_store_file=trust_store_file,
        trust_store_sha256=trust_store_sha256)


def replay_report_dict(report: ReplayReport, *, authenticity: dict | None = None) -> dict:
    """The contract ReplayReport body (without contractVersion): integrity,
    reproducibility and authenticity reported separately (correction 10).
    ``authenticity`` comes from ``authenticity_dict``; without it the bundle is reported unsigned."""
    notes = list(report.notes)
    original = report.original_verdict_hash
    if not _SHA256_RE.match(original or ""):
        # The schema requires a hash; an all-zero value is a documented sentinel.
        original = "0" * 64
        notes.append("original verdict hash unavailable; all-zero sentinel reported")
    return {
        "integrity": integrity_dict(report),
        "reproducibility": {
            "status": report.status.value,
            "originalVerdictHash": original,
            "replayedVerdictHash": report.replayed_verdict_hash,
            "envMatch": report.env_match if report.replayed_verdict_hash is not None else None,
        },
        "authenticity": authenticity if authenticity is not None else unsigned_authenticity(),
        "notes": notes,
    }
