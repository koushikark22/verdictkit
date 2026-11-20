"""Command line (core task 11.4). Used by the Nov 22 gate transcript.

  verdictkit run <claim.json> --out <bundle.vkb> [--data-mode SYNTHETIC_DEMO]
      Runs the full path with the configured examiner (SocketExaminer when
      VK_EXAMINER_SOCKET is set, else InProcessExaminer, reported UNENFORCED).
      Prints: case id, isolation mode, headline, verdict hash, bundle sha256.
  verdictkit replay <bundle.vkb> [--allow-refetch] [--json]
      Prints integrity, reproducibility and authenticity separately (correction 10).
      Exit code 0 only for REPRODUCED / REPRODUCED_ACROSS_ENV with integrity VERIFIED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path


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
            bundle_path = write_bundle(case, out_path, clock=clock)
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
    return 0


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

    from verdictkit.bundle import replay_report_dict
    body = replay_report_dict(report)
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
        print("authenticity:      NOT_ESTABLISHED (bundles unsigned in v1)")
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

    parsed = parser.parse_args(argv)

    if parsed.command == "run":
        return _cmd_run(parsed)
    elif parsed.command == "replay":
        return _cmd_replay(parsed)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
