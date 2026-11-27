"""Examiner worker entry point: ``python -I -m verdictkit.examiner.worker``.

Started by the container entrypoint as ``vk-examiner`` with a scrubbed environment
(allowlist: PATH, LANG, PYTHONHASHSEED=0, VK_EXAMINER_SOCKET, VK_EVIDENCE_DIR, VK_REPLAY_DIR,
VK_SOURCES_CONFIG). Applies RLIMIT_CPU and RLIMIT_AS before serving.
Refuses to start if a custodian secret (``VK_VAULT_KEY``, ``VK_VAULT_KEY_FILE``,
``VK_SIGNING_KEY_FILE``) is present in its environment. Requirement: core 4.

Under enforced isolation the worker also authenticates each *client*: kernel peer credentials
(``SO_PEERCRED``) must show the ``vk-custodian`` uid. Group access to the socket is not enough.
"""
from __future__ import annotations

import os
import socket
import stat
import struct
import sys

from .protocol import MAX_FRAME_BYTES, decode_namespace, decode_task, encode_result, frame

FORBIDDEN_ENV = ("VK_VAULT_KEY", "VK_VAULT_KEY_FILE", "VK_SIGNING_KEY_FILE")
CLIENT_TIMEOUT_S = 60.0  # a connected client that stalls cannot hold the single worker forever


def main() -> int:
    # Security: refuse to start if a custodian secret is in the environment
    for name in FORBIDDEN_ENV:
        if name in os.environ:
            print(f"ERROR: {name} must not be present in examiner environment", file=sys.stderr)
            return 1

    socket_path = os.environ.get("VK_EXAMINER_SOCKET", "/tmp/vk-examiner.sock")

    custodian_uid = None
    if os.environ.get("VK_ISOLATION") == "enforced":
        custodian_uid = _custodian_uid()
        if custodian_uid is None:
            print("ERROR: enforced isolation requires the vk-custodian account", file=sys.stderr)
            return 1

    # Apply resource limits on POSIX
    _apply_rlimits()

    # Load claim type registry
    registry = _load_registry()

    # Serve on unix socket
    if os.path.exists(socket_path):
        os.unlink(socket_path)

    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    old_umask = os.umask(0o117)  # socket inode is created 0660, never wider
    try:
        srv.bind(socket_path)
    finally:
        os.umask(old_umask)
    srv.listen(16)

    print(f"VerdictKit Examiner listening on {socket_path}", file=sys.stderr)

    while True:
        conn, _ = srv.accept()
        try:
            conn.settimeout(CLIENT_TIMEOUT_S)
            if custodian_uid is not None and not _peer_uid_is(conn, custodian_uid):
                print("examiner: rejected a client that is not the custodian", file=sys.stderr)
                continue
            _handle(conn, registry)
        except Exception as exc:
            print(f"examiner error: {type(exc).__name__}", file=sys.stderr)
        finally:
            conn.close()


def _custodian_uid() -> int | None:
    try:
        import pwd
        return pwd.getpwnam("vk-custodian").pw_uid
    except (ImportError, KeyError):
        return None


def _peer_uid_is(conn: socket.socket, uid: int) -> bool:
    try:
        data = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        _pid, peer_uid, _gid = struct.unpack("3i", data)
    except (AttributeError, OSError, struct.error):
        return False
    return peer_uid == uid


def _evidence_root(namespace: str | None) -> str | None:
    """Shared evidence root for live cases; a validated replay namespace for uploaded bundles."""
    if namespace is None:
        return os.environ.get("VK_EVIDENCE_DIR")
    base = os.environ.get("VK_REPLAY_DIR")
    if not base:
        raise ValueError("replay namespaces are not configured")
    path = os.path.join(base, namespace)  # the token is exactly 32 hex characters
    if not stat.S_ISDIR(os.lstat(path).st_mode):
        raise ValueError("replay namespace is not a directory")
    return path


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
    namespace = decode_namespace(payload)

    from ..sweep import expand_grid
    from .client import _EmptyEvidenceReader

    claim_type = registry.get(task.claim_type)
    grid = expand_grid(task.assumptions)
    reader = _EmptyEvidenceReader()
    evidence_dir = _evidence_root(namespace)
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
