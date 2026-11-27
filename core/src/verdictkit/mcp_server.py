"""VerdictKit MCP server (stdio). Requirement: core 12.1.

Tools (all write only inside this server's private temporary directory):
  list_claim_types() -> [{type_id, schema_version, outcome_fields}]
  verify_claim(claim: object) -> {verdict, bundle_path, isolation_mode}
  replay_bundle(path: str, allow_refetch: bool = False) -> ReplayReport as JSON
  explain_verdict(path: str) -> plain-language summary built from findings (no LLM)
Uses the official Python MCP SDK. ``VK_MCP_READONLY=1`` disables verify_claim's network
evidence acquisition (fixtures and cached evidence only) and refuses refetching replays.

Hardening (design DD8-5): a ``path`` is read only from an approved root: this server's private
working directory plus the absolute directories listed in ``VK_MCP_BUNDLE_ROOTS`` (separated by
the platform path separator), resolved once per configuration. NUL, relative, UNC, device and
alternate-data-stream names, ``..`` and links are refused. The bundle is read through one opened
handle, size-checked there, copied into the private directory, and every later step works on the
copy, so nothing changes between the check and the use.

Every failure is ``{"error": <fixed text>, "errorCode": <closed code>}``. ``error`` is unchanged
from earlier versions; ``errorCode`` is the stable, machine-readable part. Messages never carry a
path, a key, exception text or bundle content. The server does not sign bundles and never
selects a trust store: ``VK_TRUST_STORE_FILE`` is operator configuration only.

The tool bodies below are plain functions so they can be tested without a transport;
``build_server`` registers them with the SDK.
"""
from __future__ import annotations

import atexit
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import safeio
from .contract import CONTRACT_VERSION

MAX_BUNDLE_BYTES = 8 * 1024 * 1024
MAX_CLAIM_BYTES = 256 * 1024
MAX_EXPLAINED_FINDINGS = 200
MAX_TEXT = 300

_WORKDIR: Path | None = None
_ROOTS_CACHE: tuple[str, tuple[Path, ...]] | None = None

ERROR_CODES = (
    "PATH_NOT_ALLOWED", "BUNDLE_NOT_FOUND", "BUNDLE_TOO_LARGE", "BUNDLE_MALFORMED", "INVALID_ARGUMENT",
    "CLAIM_INVALID", "CLAIM_TOO_LARGE", "READONLY_REFETCH_DISABLED", "EXAMINER_UNAUTHENTICATED",
    "EVIDENCE_DIR_REQUIRED", "VERIFICATION_FAILED", "INTEGRITY_FAILED", "WORKDIR_NOT_PRIVATE",
)


def _err(code: str, message: str) -> dict[str, Any]:
    return {"error": message, "errorCode": code}


def _workdir() -> Path:
    """Private per-process temporary directory; removed at exit.

    POSIX: mode 0700 owned by this user. Windows: a DACL naming only the current user, SYSTEM and
    Administrators (``mkdtemp`` creates it that way on current Python). Fails closed otherwise."""
    global _WORKDIR
    if _WORKDIR is None:
        # Canonical form: the paths this server hands out must lie under the pinned root.
        candidate = Path(tempfile.mkdtemp(prefix="vk-mcp-")).resolve()
        candidate.chmod(0o700)
        if not safeio.is_private_dir(candidate):
            shutil.rmtree(candidate, ignore_errors=True)
            raise PermissionError("private working directory could not be secured")
        _WORKDIR = candidate
        atexit.register(shutil.rmtree, _WORKDIR, True)
    return _WORKDIR


def _approved_roots() -> tuple[Path, ...]:
    """The private working directory plus ``VK_MCP_BUNDLE_ROOTS``, resolved once per value."""
    global _ROOTS_CACHE
    configured = os.environ.get("VK_MCP_BUNDLE_ROOTS", "")
    if _ROOTS_CACHE is None or _ROOTS_CACHE[0] != configured:
        extra = [p for p in configured.split(os.pathsep) if p]
        _ROOTS_CACHE = (configured, safeio.pin_roots([str(_workdir()), *extra]))
    return _ROOTS_CACHE[1]


def _readonly() -> bool:
    return os.environ.get("VK_MCP_READONLY", "0") == "1"


def _registry():
    from verdictkit.cli import _load_registry
    return _load_registry()


def _examiner(registry, evidence_root: Path | None = None):
    """Same rule as the CLI: an authenticated socket worker or an UNENFORCED in-process
    examiner. An environment flag alone never yields ENFORCED."""
    from verdictkit.examiner.client import InProcessExaminer, SocketExaminer
    socket_path = os.environ.get("VK_EXAMINER_SOCKET")
    if socket_path:
        from verdictkit.examiner.identity import resolve_examiner_uid
        return SocketExaminer(socket_path, expected_peer_uid=resolve_examiner_uid(""))
    return InProcessExaminer(registry, evidence_root=None if evidence_root is None else str(evidence_root))


def _shared_evidence_dir(work: Path) -> Path | None:
    """VK_EVIDENCE_DIR if it is an existing absolute directory outside ``work``, else None."""
    raw = os.environ.get("VK_EVIDENCE_DIR", "")
    if not raw or "\x00" in raw:
        return None
    p = Path(raw)
    if not p.is_absolute() or not p.is_dir():
        return None
    resolved, scratch = p.resolve(), work.resolve()
    if resolved == scratch or scratch in resolved.parents:
        return None
    return p


def _checked_copy(path: Any) -> tuple[Path | None, dict[str, Any] | None]:
    """Validate ``path`` against the approved roots and copy the bundle into a private file.

    Returns ``(copy, None)`` or ``(None, error)``. The copy is what every later step reads."""
    if not isinstance(path, str) or not path:
        return None, _err("INVALID_ARGUMENT", "path must be a non-empty string")
    try:
        data = safeio.read_file_under_roots(path, _approved_roots(), max_bytes=MAX_BUNDLE_BYTES)
    except safeio.PathNotAllowed:
        return None, _err("PATH_NOT_ALLOWED", "path is not permitted")
    except safeio.FileUnavailable as exc:
        if exc.reason == "TOO_LARGE":
            return None, _err("BUNDLE_TOO_LARGE", "bundle exceeds 8 MiB")
        return None, _err("BUNDLE_NOT_FOUND", "bundle not found")
    except (OSError, PermissionError):
        return None, _err("WORKDIR_NOT_PRIVATE", "private working directory is unavailable")
    copy = _workdir() / f"in-{uuid.uuid4().hex}.vkb"
    safeio.write_private_file(copy, data)
    return copy, None


def _clip(value: Any) -> str:
    """Bundle-controlled text reaches the model client, so it is bounded and stripped of controls."""
    text = value if isinstance(value, str) else str(value)
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + "..."


def list_claim_types() -> list[dict[str, Any]]:
    registry = _registry()
    return [
        {"type_id": tid, "schema_version": registry.get(tid).schema_version,
         "outcome_fields": sorted(registry.get(tid).outcome_fields)}
        for tid in registry.type_ids()
    ]


def verify_claim(claim: dict[str, Any]) -> dict[str, Any]:
    """Run the full custody pipeline on a raw claim and write a bundle in the private
    temporary directory. Failures return an error object without exception text."""
    from verdictkit.bundle import write_bundle
    from verdictkit.canonical import canonical_bytes, parse_canonical
    from verdictkit.pipeline import run_case

    if not isinstance(claim, dict):
        return _err("CLAIM_INVALID", "claim must be a JSON object")
    try:
        encoded = json.dumps(claim, allow_nan=False).encode("utf-8")
        if len(encoded) > MAX_CLAIM_BYTES:
            return _err("CLAIM_TOO_LARGE", "claim exceeds 256 KiB")
        # Rejects floats, NaN and duplicate keys exactly as the core does.
        parse_canonical(canonical_bytes(json.loads(encoded)))
    except (ValueError, TypeError):
        return _err("CLAIM_INVALID", "claim is not canonical JSON (decimals must be strings)")

    try:
        root = _workdir()
    except (OSError, PermissionError):
        return _err("WORKDIR_NOT_PRIVATE", "private working directory is unavailable")
    registry = _registry()
    case_id = uuid.uuid4().hex
    work = root / f"case-{case_id}"
    # One evidence root for both acquisition (run_case) and examination. Socket mode uses
    # the shared VK_EVIDENCE_DIR, the only place the worker reads evidence from, and fails
    # closed without it. In-process mode keeps the private scratch directory.
    if os.environ.get("VK_EXAMINER_SOCKET"):
        evidence_root = _shared_evidence_dir(work)
        if evidence_root is None:
            return _err("EVIDENCE_DIR_REQUIRED",
                        "isolated examiner requires VK_EVIDENCE_DIR (shared evidence directory)")
    else:
        evidence_root = work / "evidence"
    try:
        examiner = _examiner(registry, evidence_root)
    except Exception:
        return _err("EXAMINER_UNAUTHENTICATED",
                    "isolated examiner is configured but could not be authenticated")

    def clock() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        case = run_case(claim, registry=registry, examiner=examiner, workdir=work,
                        clock=clock, case_id=case_id, network=not _readonly(),
                        evidence_root=evidence_root)
        bundle = write_bundle(case, root / f"{case_id}.vkb", clock=clock)
    except Exception:
        return _err("VERIFICATION_FAILED", "verification failed")
    finally:
        shutil.rmtree(work, ignore_errors=True)  # vault and evidence scratch space
    return {
        "case_id": case_id,
        "isolation_mode": case.isolation.value,
        "verdict": {
            "headline": case.verdict.headline.value,
            "verdict_hash": case.verdict.verdict_hash,
            "findings": [{"finding_id": f.finding_id, "basis": f.basis.value,
                          "status": f.status.value, "statement": f.statement,
                          "reason": f.reason} for f in case.verdict.findings],
        },
        "bundle_path": str(bundle),
    }


def replay_bundle(path: str, allow_refetch: bool = False) -> dict[str, Any]:
    from verdictkit.bundle import authenticity_dict, replay_bundle as _replay, replay_report_dict

    if not isinstance(allow_refetch, bool):
        return _err("INVALID_ARGUMENT", "allow_refetch must be a boolean")
    copy, failure = _checked_copy(path)
    if failure is not None:
        return failure
    if allow_refetch and _readonly():
        copy.unlink(missing_ok=True)
        return _err("READONLY_REFETCH_DISABLED", "refetch is disabled (VK_MCP_READONLY=1)")
    registry = _registry()
    work = Path(tempfile.mkdtemp(prefix="replay-", dir=_workdir()))
    try:
        report = _replay(copy, registry=registry, workdir=work, allow_refetch=allow_refetch)
        authenticity = authenticity_dict(copy, report)
    except Exception:
        return _err("BUNDLE_MALFORMED", "bundle could not be replayed")
    finally:
        shutil.rmtree(work, ignore_errors=True)
        copy.unlink(missing_ok=True)
    return {"contractVersion": CONTRACT_VERSION,
            **replay_report_dict(report, authenticity=authenticity)}


_STATUS_WORDS = {
    "CONSISTENT": "is consistent with the recomputed value",
    "CONTRADICTED": "is contradicted by the document's own arithmetic",
    "SUPPORTED": "is supported by the cited evidence",
    "REFUTED": "is refuted by the cited evidence",
    "CONDITIONAL": "holds at some swept assumption values but not others",
    "WITHIN_BOUND": "is within the mechanical bound",
    "IMPOSSIBLE": "exceeds what the declared mechanics allow",
    "INDETERMINATE": "could not be determined",
}


def _explain(copy: Path, integrity: dict, authenticity: dict) -> dict[str, Any]:
    """Build the explanation from a bundle that passed integrity. The content is still
    attacker-chosen (an adversary can build a self-consistent bundle), so every field is type-checked."""
    import zipfile

    from verdictkit.canonical import parse_canonical

    with zipfile.ZipFile(copy) as zf:
        verdict = parse_canonical(zf.read("verdict/verdict.json"))
        manifest = parse_canonical(zf.read("manifest.json"))
        exam = parse_canonical(zf.read("examination/result.json"))
    if not (isinstance(verdict, dict) and isinstance(manifest, dict) and isinstance(exam, dict)
            and isinstance(verdict.get("findings"), list) and isinstance(verdict.get("headline"), str)
            and isinstance(verdict.get("verdict_hash"), str)):
        raise ValueError("unexpected bundle structure")
    points = exam.get("points", [])
    point_count = len(points) if isinstance(points, list) else 0
    lines = [f"Headline: {_clip(verdict['headline'])} (worst finding status wins)."]
    findings = verdict["findings"][:MAX_EXPLAINED_FINDINGS]
    for f in findings:
        if not isinstance(f, dict):
            raise ValueError("unexpected finding structure")
        status = f.get("status")
        words = _STATUS_WORDS.get(status, "has an unrecognised status") if isinstance(status, str) else "has an unrecognised status"
        sentence = f"- {_clip(f.get('finding_id'))} ({_clip(f.get('basis'))}): the claimed value {words}"
        if f.get("reason"):
            sentence += f" [reason: {_clip(f['reason'])}]"
        nums = f.get("numbers")
        if isinstance(nums, dict) and nums.get("expected") is not None and nums.get("observed") is not None:
            sentence += (f"; expected {_clip(nums['expected'])}, observed {_clip(nums['observed'])}, "
                         f"difference {_clip(nums.get('difference'))}, tolerance {_clip(nums.get('tolerance'))}")
        lines.append(sentence + ".")
    if len(verdict["findings"]) > MAX_EXPLAINED_FINDINGS:
        lines.append(f"({len(verdict['findings']) - MAX_EXPLAINED_FINDINGS} further findings not shown.)")
    lines.append(f"Verified at {point_count} grid point{'s' if point_count != 1 else ''}; "
                 "this is not a claim that it holds for all values.")
    lines.append(f"Isolation mode when sealed: {_clip(manifest.get('isolation_mode'))}.")
    lines.append(f"Authenticity: {authenticity['status']} (signature: {authenticity['signatureValidity']}; "
                 f"signer trust: {authenticity['signerTrust']}). {authenticity['note']}")
    return {"integrity": integrity, "authenticity": authenticity, "headline": _clip(verdict["headline"]),
            "verdict_hash": _clip(verdict["verdict_hash"]), "summary": "\n".join(lines)}


def explain_verdict(path: str) -> dict[str, Any]:
    """Deterministic, template-based explanation of a bundle's sealed findings.

    Integrity is checked first; an explanation is never produced for a bundle whose
    manifest, ledger, spec hash or commitment fail verification."""
    from verdictkit.bundle import authenticity_dict, integrity_dict, verify_bundle_integrity

    copy, failure = _checked_copy(path)
    if failure is not None:
        return failure
    try:
        result, _parts = verify_bundle_integrity(copy)
        integrity = integrity_dict(result)
        authenticity = authenticity_dict(copy, result)
        if integrity["status"] != "VERIFIED":
            return {"integrity": integrity, "authenticity": authenticity, "errorCode": "INTEGRITY_FAILED",
                    "error": "bundle failed integrity checks; not explained"}
        return _explain(copy, integrity, authenticity)
    except Exception:
        return _err("BUNDLE_MALFORMED", "bundle structure is not valid")
    finally:
        copy.unlink(missing_ok=True)


def build_server():
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(name="verdictkit", version="0.1.0",
                       instructions="Deterministic claim verification. No LLM in the verdict path.")
    for fn in (list_claim_types, verify_claim, replay_bundle, explain_verdict):
        server.tool()(fn)
    return server


def main() -> int:
    build_server().run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
