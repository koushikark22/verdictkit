#!/usr/bin/env python3
"""Container gate helper: is a *valid* task served to this OS user?

Sends one well-formed blinded task to the examiner socket and prints ``served`` when the worker
answers or ``peer-rejected`` when it closes the connection without answering. A malformed frame is
dropped for every client, so only a valid task shows whether the worker's SO_PEERCRED check (only
the custodian uid is served) is what refused a client. ``entrypoint.sh gate-sign`` runs it as the
examiner (expects peer-rejected) and as the custodian (expects served, the positive control).

usage: gate_peer_probe.py CLAIM.json     (VK_EXAMINER_SOCKET must be set)
"""
from __future__ import annotations

import json
import os
import socket
import sys

from verdictkit.cli import _load_registry
from verdictkit.custody.intake import blind, freeze
from verdictkit.examiner.protocol import encode_task, frame


def main(claim_path: str) -> int:
    with open(claim_path, encoding="utf-8") as fh:
        raw = json.load(fh)
    frozen = freeze(_load_registry().get(raw["claim_type"]), raw).frozen
    task = blind(frozen, case_id="peer-probe", evidence_refs=())
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(20)
        conn.connect(os.environ["VK_EXAMINER_SOCKET"])
        try:
            conn.sendall(frame(encode_task(task)))
            head = conn.recv(4)
        except (ConnectionResetError, BrokenPipeError):
            head = b""
    print("served" if len(head) == 4 else "peer-rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
