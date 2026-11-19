"""Linux UNIX-socket peer verification for the isolated examiner.

A socket pathname or an environment flag does not establish OS separation.
The connecting custodian checks Linux SO_PEERCRED before trusting a worker.
"""
from __future__ import annotations

import os
import socket
import stat
import struct
import sys
from pathlib import Path


class ExaminerIdentityError(RuntimeError):
    """The peer cannot be authenticated as the designated examiner."""


def resolve_examiner_uid(configured: str | None = None) -> int:
    """Resolve the required worker account, without trusting a self-chosen UID."""
    if not sys.platform.startswith("linux") or not hasattr(os, "geteuid"):
        raise ExaminerIdentityError("examiner identity requires Linux")
    if configured is None:
        configured = os.environ.get("VK_EXAMINER_UID")
    if configured is not None and configured != "":
        if not configured.isascii() or not configured.isdecimal():
            raise ExaminerIdentityError("examiner UID must be a nonnegative integer")
        uid = int(configured)
    else:
        try:
            import pwd
            uid = pwd.getpwnam("vk-examiner").pw_uid
        except (ImportError, KeyError) as exc:
            raise ExaminerIdentityError("examiner account is missing") from exc
    if uid == 0 or uid == os.geteuid():
        raise ExaminerIdentityError("examiner must be a distinct non-root OS user")
    return uid


def verify_connected_peer(sock: socket.socket, expected_uid: int) -> int:
    """Return peer PID only after kernel credentials authenticate its UID.

    The same check is required on every examination connection, because the
    listening process could be replaced after the initial startup check.
    """
    if not sys.platform.startswith("linux") or not hasattr(socket, "SO_PEERCRED"):
        raise ExaminerIdentityError("kernel peer credentials unavailable")
    if type(expected_uid) is not int or expected_uid <= 0:
        raise ExaminerIdentityError("invalid examiner UID")
    try:
        data = sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        pid, uid, _gid = struct.unpack("3i", data)
    except (OSError, ValueError, struct.error) as exc:
        raise ExaminerIdentityError("unable to read examiner peer credentials") from exc
    if pid <= 0 or uid != expected_uid or uid == os.geteuid():
        raise ExaminerIdentityError("examiner peer identity mismatch")
    return pid


def verify_examiner_socket(path: str, *, expected_uid: int, timeout_s: float = 1.0) -> int:
    """Check socket inode owner and connect to authenticate live peer credentials."""
    if not path or not os.path.isabs(path) or "\x00" in path:
        raise ExaminerIdentityError("invalid examiner socket path")
    p = Path(path)
    try:
        st = p.lstat()
        if not stat.S_ISSOCK(st.st_mode) or st.st_uid != expected_uid:
            raise ExaminerIdentityError("examiner socket owner or type mismatch")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(timeout_s)
            conn.connect(path)
            return verify_connected_peer(conn, expected_uid)
    except (OSError, ValueError) as exc:
        raise ExaminerIdentityError("examiner socket is unavailable") from exc
