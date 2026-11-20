"""Examiner worker entry point: ``python -I -m verdictkit.examiner.worker``.

Started by the container entrypoint as ``vk-examiner`` with a scrubbed environment
(allowlist: PATH, LANG, PYTHONHASHSEED=0, VK_EXAMINER_SOCKET, VK_EVIDENCE_DIR,
VK_SOURCES_CONFIG). Applies RLIMIT_CPU and RLIMIT_AS before serving.
Refuses to start if ``VK_VAULT_KEY`` is present in its environment. Requirement: core 4.
"""
from __future__ import annotations

import os
import socket
import struct
import sys

from .protocol import MAX_FRAME_BYTES, decode_task, encode_result, frame


def main() -> int:
    # Security: refuse to start if vault key is in the environment
    if "VK_VAULT_KEY" in os.environ:
        print("ERROR: VK_VAULT_KEY must not be present in examiner environment", file=sys.stderr)
        return 1

    socket_path = os.environ.get("VK_EXAMINER_SOCKET", "/tmp/vk-examiner.sock")

    # Apply resource limits on POSIX
    _apply_rlimits()

    # Load claim type registry
    registry = _load_registry()

    # Serve on unix socket
    if os.path.exists(socket_path):
        os.unlink(socket_path)

    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(socket_path)
    srv.listen(16)

    print(f"VerdictKit Examiner listening on {socket_path}", file=sys.stderr)

    while True:
        conn, _ = srv.accept()
        try:
            _handle(conn, registry)
        except Exception as exc:
            print(f"examiner error: {exc}", file=sys.stderr)
        finally:
            conn.close()


def _handle(conn: socket.socket, registry) -> None:
    # Read 4-byte length prefix
    length_data = _recv_exactly(conn, 4)
    if not length_data:
        return
    (length,) = struct.unpack(">I", length_data)
    if length > MAX_FRAME_BYTES:
        return  # silently drop oversized frames
    payload = _recv_exactly(conn, length)
    if not payload:
        return

    task = decode_task(payload)

    from ..plugin import Registry as _Registry
    from ..sweep import expand_grid
    from .client import _EmptyEvidenceReader

    claim_type = registry.get(task.claim_type)
    grid = expand_grid(task.assumptions)
    reader = _EmptyEvidenceReader()
    evidence_dir = os.environ.get("VK_EVIDENCE_DIR")
    if evidence_dir and task.evidence_refs:
        from ..evidence.store import ReadOnlyEvidence
        reader = ReadOnlyEvidence(evidence_dir, task.evidence_refs)
    examination = claim_type.examine(task, reader, list(grid.points))

    result_payload = encode_result(examination)
    conn.sendall(frame(result_payload))


def _recv_exactly(sock: socket.socket, n: int) -> bytes | None:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def _apply_rlimits() -> None:
    """Apply CPU and address-space limits on POSIX platforms."""
    try:
        import resource
        # CPU: 300 seconds
        cpu_limit = int(os.environ.get("VK_RLIMIT_CPU", "300"))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
        # Address space: 2 GiB
        as_limit = int(os.environ.get("VK_RLIMIT_AS", str(2 * 1024 ** 3)))
        resource.setrlimit(resource.RLIMIT_AS, (as_limit, as_limit))
    except (ImportError, ValueError, OSError):
        pass  # Windows or permission denied; non-fatal in dev


def _load_registry():
    """Load the same configured claim types as the custodian CLI."""
    from verdictkit.cli import _load_registry as load_registry
    return load_registry()

if __name__ == "__main__":
    raise SystemExit(main())
