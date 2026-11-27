"""Command line (core task 11.4). Used by the Nov 22 gate transcript.

  verdictkit run <claim.json> --out <bundle.vkb> [--data-mode SYNTHETIC_DEMO]
      Runs the full path with the configured examiner (SocketExaminer when
      VK_EXAMINER_SOCKET is set, else InProcessExaminer, reported UNENFORCED).
      Prints: case id, isolation mode, headline, verdict hash, bundle sha256.
  verdictkit replay <bundle.vkb> [--allow-refetch] [--json] [--trust-store FILE] [--as-of TIME]
      Prints integrity, reproducibility, signature validity, signer trust and authenticity
      separately (correction 10, design D5). Exit code 0 only for REPRODUCED /
      REPRODUCED_ACROSS_ENV with integrity VERIFIED; a signature never changes it.
  verdictkit verify <bundle.vkb> [--trust-store FILE] [--as-of TIME] [--json]
      Offline integrity and signature check without re-execution. Exit code 0 only when
      authenticity is ESTABLISHED (valid signature, trusted signer, verified integrity).
  Signing: set VK_SIGNING_KEY_FILE to a private Ed25519 PEM key file. Trust is configured by
  the verifier (--trust-store or VK_TRUST_STORE_FILE), never by the bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from verdictkit.plugin import Registry


def _load_registry() -> "Registry":
    """Load all claim types discoverable on the current path.

    For the gate we load the example stub claim type automatically if it is on
    the Python path (or the entry-point group ``verdictkit.claim_types`` is
    populated).  Any additional types registered via VK_CLAIM_TYPES env var are
    also loaded (comma-separated ``pkg.module:ClassName`` or ``pkg.module``
    if the module registers itself on import).
    """
    from verdictkit.plugin import Registry

    r = Registry()

    # Try the standard entry-points group first (works with installed packages)
    try:
        from importlib.metadata import entry_points
        eps = entry_points(group="verdictkit.claim_types")
        for ep in eps:
            ct = ep.load()
            if callable(ct):
                ct = ct()
            r.register(ct)
    except Exception:
        pass

    # VK_CLAIM_TYPES env override: "pkg.module:ClassName,..."
    extra = os.environ.get("VK_CLAIM_TYPES", "").strip()
    if extra:
        import importlib
        for spec in extra.split(","):
            spec = spec.strip()
            if not spec:
                continue
            if ":" in spec:
                mod_path, cls_name = spec.split(":", 1)
                mod = importlib.import_module(mod_path)
                ct = getattr(mod, cls_name)()
            else:
                # bare module — assume registering on import sets a module-level CLAIM_TYPE
                mod = importlib.import_module(spec)
                ct = getattr(mod, "CLAIM_TYPE", None) or getattr(mod, "claim_type", None)
                if ct is None:
                    print(f"WARNING: {spec} has no CLAIM_TYPE attribute", file=sys.stderr)
                    continue
                if callable(ct):
                    ct = ct()
            r.register(ct)

    return r


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _cmd_run(args: argparse.Namespace) -> int:
    from verdictkit.bundle import write_bundle
    from verdictkit.examiner.client import InProcessExaminer, SocketExaminer
    from verdictkit.model import DataMode
    from verdictkit.pipeline import run_case

    claim_path = Path(args.claim_json)
    if not claim_path.exists():
        print(f"ERROR: claim file not found: {claim_path}", file=sys.stderr)
        return 1

    try:
        with open(claim_path, "rb") as f:
            raw_claim = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: cannot read claim JSON: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data_mode = DataMode.LIVE_EVIDENCE
    if args.data_mode:
        try:
            data_mode = DataMode(args.data_mode)
        except ValueError:
            print(f"ERROR: unknown data-mode {args.data_mode!r}", file=sys.stderr)
            return 1

    from verdictkit.signing import SigningKeyError, load_signer_from_env
    try:
        signer = load_signer_from_env()  # unset: unsigned. Set but unusable: stop, never downgrade.
    except SigningKeyError as exc:
        print(f"ERROR: signing key unusable ({exc.code}); no bundle written", file=sys.stderr)
        return 1

    registry = _load_registry()

    # Choose examiner
    socket_path = os.environ.get("VK_EXAMINER_SOCKET")
    if socket_path:
        from verdictkit.examiner.identity import resolve_examiner_uid

        # A socket path or VK_ISOLATION flag cannot establish separation.
        # The constructor also checks the actual kernel peer credentials.
        examiner = SocketExaminer(
            socket_path, expected_peer_uid=resolve_examiner_uid("")
        )
    else:
        examiner = None

    with tempfile.TemporaryDirectory(prefix="vk-run-") as tmpdir:
        import datetime

        # The examiner must be able to read acquired evidence: the shared, group-readable
        # VK_EVIDENCE_DIR in the container, else a private directory for in-process runs.
        evidence_root = Path(os.environ.get("VK_EVIDENCE_DIR") or Path(tmpdir) / "evidence")
        if examiner is None:
            examiner = InProcessExaminer(registry, evidence_root=str(evidence_root))

        def clock() -> str:
            return datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        try:
            case = run_case(
                raw_claim,
                registry=registry,
                examiner=examiner,
                workdir=Path(tmpdir),
                clock=clock,
                data_mode=data_mode,
                evidence_root=evidence_root,
            )
        except Exception as exc:
            print(f"ERROR: run failed: {exc}", file=sys.stderr)
            return 1

        try:
            bundle_path = write_bundle(case, out_path, clock=clock, signer=signer)
        except Exception as exc:
            print(f"ERROR: bundle write failed: {exc}", file=sys.stderr)
            return 1

    bundle_sha256 = _sha256_file(bundle_path)

    print(f"case_id:       {case.case_id}")
    print(f"isolation:     {case.isolation.value}")
    print(f"headline:      {case.verdict.headline.value}")
    print(f"verdict_hash:  {case.verdict.verdict_hash}")
    print(f"bundle_sha256: {bundle_sha256}")
    print(f"bundle:        {bundle_path}")
    if signer is None:
        print("signed:        no (VK_SIGNING_KEY_FILE is not set)")
    else:
        print(f"signed:        yes (ed25519, key_id {signer.key_id})")
        if case.isolation.value != "ENFORCED":
            print("WARNING: signed a bundle produced with UNENFORCED isolation; the manifest records it.",
                  file=sys.stderr)
    return 0


def _abs_or_none(path: str | None) -> str | None:
    return None if not path else os.path.abspath(path)


def _print_authenticity(a: dict) -> None:
    """Signature validity, signer trust and authenticity are three separate lines (design D5.3)."""
    print(f"signature:         {a['signatureValidity']}")
    if a["signer"] is not None:
        print(f"  signer key_id:   {a['signer']['keyId']}")
    print(f"signer trust:      {a['signerTrust']}")
    if a["trustStore"] is not None:
        print(f"  trust store:     serial {a['trustStore']['serial']}, sha256 {a['trustStore']['sha256']}")
    print(f"authenticity:      {a['status']}")
    if a["reasonCodes"]:
        print(f"  reasons:         {', '.join(a['reasonCodes'])}")
    print(f"  note:            {a['note']}")


_AS_OF = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _valid_as_of(value: str | None) -> bool:
    return value is None or _AS_OF.match(value) is not None


def _cmd_verify(args: argparse.Namespace) -> int:
    """Offline integrity + signature verification. No re-execution, no registry, no network."""
    from verdictkit.bundle import authenticity_dict, integrity_dict, verify_bundle_integrity

    bundle_path = Path(args.bundle)
    if not bundle_path.is_file():
        print(f"ERROR: bundle not found: {bundle_path}", file=sys.stderr)
        return 1
    result, _parts = verify_bundle_integrity(bundle_path)
    integrity = integrity_dict(result)
    authenticity = authenticity_dict(bundle_path, result, as_of=args.as_of,
                                     trust_store_file=_abs_or_none(args.trust_store))
    if args.json:
        print(json.dumps({"integrity": integrity, "authenticity": authenticity}, indent=2))
    else:
        print(f"integrity:         {integrity['status']}")
        for c in integrity["checks"]:
            print(f"  [{'OK' if c['ok'] else 'FAIL'}] {c['check']}")
        print("reproducibility:   NOT_RUN (use `verdictkit replay`)")
        _print_authenticity(authenticity)
    return 0 if authenticity["status"] == "ESTABLISHED" else 1


def _cmd_replay(args: argparse.Namespace) -> int:
    from verdictkit.bundle import ReplayStatus, replay_bundle

    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        print(f"ERROR: bundle not found: {bundle_path}", file=sys.stderr)
        return 1

    registry = _load_registry()

    with tempfile.TemporaryDirectory(prefix="vk-replay-") as tmpdir:
        try:
            report = replay_bundle(
                bundle_path,
                registry=registry,
                workdir=Path(tmpdir),
                allow_refetch=args.allow_refetch,
            )
        except Exception as exc:
            print(f"ERROR: replay failed: {exc}", file=sys.stderr)
            return 1

    from verdictkit.bundle import authenticity_dict, replay_report_dict
    authenticity = authenticity_dict(bundle_path, report, as_of=args.as_of,
                                     trust_store_file=_abs_or_none(args.trust_store))
    body = replay_report_dict(report, authenticity=authenticity)
    integrity_status = body["integrity"]["status"]

    if args.json:
        print(json.dumps(body, indent=2))
    else:
        print(f"integrity:         {integrity_status}")
        for c in body["integrity"]["checks"]:
            mark = "OK" if c["ok"] else "FAIL"
            print(f"  [{mark}] {c['check']}")
        print(f"reproducibility:   {report.status.value}")
        print(f"  original_hash:   {report.original_verdict_hash}")
        print(f"  replayed_hash:   {report.replayed_verdict_hash}")
        print(f"  env_match:       {report.env_match}")
        _print_authenticity(authenticity)
        if report.notes:
            print("notes:")
            for note in report.notes:
                print(f"  - {note}")

    # Exit 0 only for reproduced + verified integrity (Req 14.2)
    reproduced = report.status in (
        ReplayStatus.REPRODUCED,
        ReplayStatus.REPRODUCED_ACROSS_ENV,
    )
    if reproduced and integrity_status == "VERIFIED":
        return 0
    else:
        reason = []
        if not reproduced:
            reason.append(f"reproducibility={report.status.value}")
        if integrity_status != "VERIFIED":
            reason.append("integrity=FAILED")
        print(f"\nREPLAY FAILED: {', '.join(reason)}", file=sys.stderr)
        return 1


def _add_trust_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--trust-store", default=None, metavar="FILE",
                   help="Operator trust store (default: VK_TRUST_STORE_FILE). Never read from the bundle.")
    p.add_argument("--as-of", default=None, metavar="TIME",
                   help="Evaluation time YYYY-MM-DDTHH:MM:SSZ for key validity (default: now)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verdictkit",
        description="VerdictKit — The Claim Autopsy Engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run subcommand
    run_p = sub.add_parser("run", help="Run a claim and produce a .vkb bundle")
    run_p.add_argument("claim_json", metavar="<claim.json>")
    run_p.add_argument("--out", required=True, metavar="<bundle.vkb>")
    run_p.add_argument(
        "--data-mode",
        default=None,
        metavar="MODE",
        help="LIVE_EVIDENCE (default) or SYNTHETIC_DEMO",
    )

    # replay subcommand
    rep_p = sub.add_parser(
        "replay",
        help="Replay a .vkb bundle offline and verify reproducibility",
    )
    rep_p.add_argument("bundle", metavar="<bundle.vkb>")
    rep_p.add_argument(
        "--allow-refetch",
        action="store_true",
        default=False,
        help="Allow network access to re-fetch REFETCH_ONLY evidence",
    )
    rep_p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit machine-readable JSON instead of text",
    )

    _add_trust_args(rep_p)

    ver_p = sub.add_parser(
        "verify",
        help="Offline integrity and signature check of a .vkb bundle (no re-execution)",
    )
    ver_p.add_argument("bundle", metavar="<bundle.vkb>")
    ver_p.add_argument("--json", action="store_true", default=False,
                       help="Emit machine-readable JSON instead of text")
    _add_trust_args(ver_p)

    parsed = parser.parse_args(argv)

    if parsed.command in ("replay", "verify") and not _valid_as_of(parsed.as_of):
        print("ERROR: --as-of must look like 2026-12-01T00:00:00Z", file=sys.stderr)
        return 2

    if parsed.command == "run":
        return _cmd_run(parsed)
    elif parsed.command == "replay":
        return _cmd_replay(parsed)
    elif parsed.command == "verify":
        return _cmd_verify(parsed)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
