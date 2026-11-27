#!/usr/bin/env python3
"""Container gate helper: the vault key must not be exposed to other local processes.

Design DD8-2. Started as root by ``entrypoint.sh`` before the custodian starts and stopped when it
finishes. It samples ``/proc`` repeatedly and records a hit when the vault key (read from its key
file, so the key is never an argument of this process either) appears

  * in the command line of any process other than this scanner, or
  * in the environment of any process owned by neither root nor ``vk-custodian``.

A canary process whose argument holds a random string is started first. The result is only
meaningful if the scanner saw it, which shows it can read other processes' arguments. Sampling
cannot prove absence at every instant; it is evidence next to the static test and the design.

usage: gate_argv_scan.py KEY_FILE RESULT_FILE STOP_FILE READY_FILE
exit:  0 no hit and canary seen; 1 hit or canary missed; 3 key file unreadable
"""
from __future__ import annotations

import os
import pwd
import secrets
import subprocess
import sys
import time


def _read(path: str) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return b""


def main(argv: list[str]) -> int:
    key_file, result_file, stop_file, ready_file = argv[1:5]
    try:
        needle = _read(key_file).strip()
        if not needle:
            raise OSError("empty")
        custodian_uid = pwd.getpwnam("vk-custodian").pw_uid
    except (OSError, KeyError):
        with open(result_file, "w", encoding="utf-8") as out:
            out.write("argv-scan: key file or custodian account unavailable\n")
        return 3

    canary = secrets.token_hex(16).encode()
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)", canary.decode()])
    me = os.getpid()
    polls, canary_seen, hits = 0, False, set()
    open(ready_file, "w").close()
    try:
        while not os.path.exists(stop_file):
            for entry in os.listdir("/proc"):
                if not entry.isdigit() or int(entry) == me:
                    continue
                cmdline = _read(f"/proc/{entry}/cmdline")
                if canary in cmdline:
                    canary_seen = True
                if needle in cmdline:
                    hits.add(("argv", entry, cmdline.split(b"\0", 1)[0][-40:].decode("utf-8", "replace")))
                try:
                    owner = os.stat(f"/proc/{entry}").st_uid
                except OSError:
                    continue
                if owner not in (0, custodian_uid) and needle in _read(f"/proc/{entry}/environ"):
                    hits.add(("environ", entry, f"uid {owner}"))
            polls += 1
            time.sleep(0.002)
    finally:
        child.kill()
        child.wait()

    with open(result_file, "w", encoding="utf-8") as out:
        out.write(f"argv-scan: polls={polls} canary_seen={str(canary_seen).lower()} key_hits={len(hits)}\n")
        for where, pid, who in sorted(hits):
            out.write(f"argv-scan: KEY FOUND in {where} of pid {pid} ({who})\n")
    return 0 if canary_seen and not hits else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
