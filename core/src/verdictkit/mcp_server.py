"""VerdictKit MCP server (stdio). Requirement: core 12.1.

Tools (all write only inside this server's private temporary directory):
  list_claim_types() -> [{type_id, schema_version, outcome_fields}]
  verify_claim(claim: object) -> {verdict, bundle_path, isolation_mode}
  replay_bundle(path: str, allow_refetch: bool = False) -> ReplayReport as JSON
  explain_verdict(path: str) -> plain-language summary built from findings (no LLM)
Uses the official Python MCP SDK. ``VK_MCP_READONLY=1`` disables verify_claim's network
evidence acquisition (fixtures and cached evidence only) and refuses refetching replays.

The tool bodies below are plain functions so they can be tested without a transport;
``build_server`` registers them with the SDK.
"""
from __future__ import annotations

import atexit
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_BUNDLE_BYTES = 8 * 1024 * 1024
MAX_CLAIM_BYTES = 256 * 1024

_WORKDIR: Path | None = None


def _workdir() -> Path:
    """Private per-process temporary directory (mode 0700); removed at exit."""
    global _WORKDIR
    if _WORKDIR is None:
        _WORKDIR = Path(tempfile.mkdtemp(prefix="vk-mcp-"))
        _WORKDIR.chmod(0o700)
        atexit.register(shutil.rmtree, _WORKDIR, True)
    return _WORKDIR


def _readonly() -> bool:
    return os.environ.get("VK_MCP_READONLY", "0") == "1"


def _registry():
    from verdictkit.cli import _load_registry
    return _load_registry()


def _examiner(registry):
    """Same rule as the CLI: an authenticated socket worker or an UNENFORCED in-process
    examiner. An environment flag alone never yields ENFORCED."""
    from verdictkit.examiner.client import InProcessExaminer, SocketExaminer
    socket_path = os.environ.get("VK_EXAMINER_SOCKET")
    if socket_path:
        from verdictkit.examiner.identity import resolve_examiner_uid
        return SocketExaminer(socket_path, expected_peer_uid=resolve_examiner_uid(""))
    return InProcessExaminer(registry)


def _bundle_path(path: str) -> Path:
    if not isinstance(path, str) or not path or "\x00" in path:
        raise ValueError("path must be a non-empty string")
    p = Path(path).expanduser()
    if not p.is_file():
        raise ValueError("bundle not found")
    if p.stat().st_size > MAX_BUNDLE_BYTES:
        raise ValueError("bundle exceeds 8 MiB")
    return p


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
        return {"error": "claim must be a JSON object"}
    try:
        encoded = json.dumps(claim, allow_nan=False).encode("utf-8")
        if len(encoded) > MAX_CLAIM_BYTES:
            return {"error": "claim exceeds 256 KiB"}
        # Rejects floats, NaN and duplicate keys exactly as the core does.
        parse_canonical(canonical_bytes(json.loads(encoded)))
    except (ValueError, TypeError):
        return {"error": "claim is not canonical JSON (decimals must be strings)"}

    registry = _registry()
    try:
        examiner = _examiner(registry)
    except Exception:
        return {"error": "isolated examiner is configured but could not be authenticated"}
    case_id = uuid.uuid4().hex
    root = _workdir()
    work = root / f"case-{case_id}"

    def clock() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        case = run_case(claim, registry=registry, examiner=examiner, workdir=work,
                        clock=clock, case_id=case_id, network=not _readonly())
        bundle = write_bundle(case, root / f"{case_id}.vkb", clock=clock)
    except Exception as exc:
        return {"error": f"verification failed ({type(exc).__name__})"}
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
    from verdictkit.bundle import replay_bundle as _replay, replay_report_dict

    try:
        bundle = _bundle_path(path)
    except (ValueError, OSError) as exc:
        return {"error": str(exc)}
    if allow_refetch and _readonly():
        return {"error": "refetch is disabled (VK_MCP_READONLY=1)"}
    registry = _registry()
    work = Path(tempfile.mkdtemp(prefix="replay-", dir=_workdir()))
    try:
        report = _replay(bundle, registry=registry, workdir=work, allow_refetch=allow_refetch)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return {"contractVersion": "1.1.0", **replay_report_dict(report)}


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


def explain_verdict(path: str) -> dict[str, Any]:
    """Deterministic, template-based explanation of a bundle's sealed findings.

    Integrity is checked first; an explanation is never produced for a bundle whose
    manifest, ledger, spec hash or commitment fail verification."""
    import zipfile

    from verdictkit.bundle import integrity_dict, verify_bundle_integrity
    from verdictkit.canonical import parse_canonical

    try:
        bundle = _bundle_path(path)
    except (ValueError, OSError) as exc:
        return {"error": str(exc)}
    result, _parts = verify_bundle_integrity(bundle)
    integrity = integrity_dict(result)
    if integrity["status"] != "VERIFIED":
        return {"integrity": integrity, "error": "bundle failed integrity checks; not explained"}
    with zipfile.ZipFile(bundle) as zf:
        verdict = parse_canonical(zf.read("verdict/verdict.json"))
        manifest = parse_canonical(zf.read("manifest.json"))
        exam = parse_canonical(zf.read("examination/result.json"))
    points = len(exam.get("points", []))
    lines = [f"Headline: {verdict['headline']} (worst finding status wins)."]
    for f in verdict["findings"]:
        sentence = f"- {f['finding_id']} ({f['basis']}): the claimed value {_STATUS_WORDS.get(f['status'], f['status'])}"
        if f.get("reason"):
            sentence += f" [reason: {f['reason']}]"
        nums = f.get("numbers") or {}
        if nums.get("expected") is not None and nums.get("observed") is not None:
            sentence += (f"; expected {nums['expected']}, observed {nums['observed']}, "
                         f"difference {nums.get('difference')}, tolerance {nums.get('tolerance')}")
        lines.append(sentence + ".")
    lines.append(f"Verified at {points} grid point{'s' if points != 1 else ''}; "
                 "this is not a claim that it holds for all values.")
    lines.append(f"Isolation mode when sealed: {manifest.get('isolation_mode')}.")
    lines.append("Authenticity: NOT_ESTABLISHED (bundles are unsigned in v1).")
    return {"integrity": integrity, "headline": verdict["headline"],
            "verdict_hash": verdict["verdict_hash"], "summary": "\n".join(lines)}


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
