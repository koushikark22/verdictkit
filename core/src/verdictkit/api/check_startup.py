"""Fail-closed API startup checks for OS-user isolation.

Environment flags and socket pathname presence are not security attestations.
"""
from __future__ import annotations

import os
import stat
import sys


class StartupConfigurationError(ValueError):
    """Unsupported judge mode configuration."""


class IsolationNotEnforcedError(RuntimeError):
    """The required examiner/custodian separation could not be verified."""


def parse_judge_mode() -> bool:
    raw = os.environ.get("VK_JUDGE_MODE", "0")
    if raw == "1":
        return True
    if raw == "0":
        return False
    raise StartupConfigurationError("invalid VK_JUDGE_MODE value")


def isolation_enforced() -> bool:
    if sys.platform != "linux":
        return False
    try:
        import grp
        import pwd
        from verdictkit.examiner.identity import verify_examiner_socket

        custodian = pwd.getpwnam("vk-custodian")
        examiner = pwd.getpwnam("vk-examiner")
        ipc = grp.getgrnam("vk-ipc")

        if os.geteuid() != custodian.pw_uid or custodian.pw_uid == examiner.pw_uid:
            return False
        vault_path = os.environ.get("VK_VAULT_DIR", "/var/lib/vk/vault")
        sock_path = os.environ.get("VK_EXAMINER_SOCKET", "")
        if not sock_path:
            return False
        vault = os.lstat(vault_path)
        sock = os.lstat(sock_path)
        if not stat.S_ISDIR(vault.st_mode) or vault.st_uid != custodian.pw_uid:
            return False
        if stat.S_IMODE(vault.st_mode) != 0o700:
            return False
        if not stat.S_ISSOCK(sock.st_mode) or sock.st_uid != examiner.pw_uid:
            return False
        if sock.st_gid != ipc.gr_gid or stat.S_IMODE(sock.st_mode) != 0o660:
            return False
        if ipc.gr_gid not in os.getgroups():
            return False

        verify_examiner_socket(sock_path, expected_uid=examiner.pw_uid)
        return True
    except (OSError, KeyError, ValueError, RuntimeError):
        return False


def isolation_mode() -> str:
    return "ENFORCED" if isolation_enforced() else "UNENFORCED"


def startup_checks(force_judge: bool = False) -> tuple[bool, str]:
    judge_mode = parse_judge_mode() or force_judge
    mode = isolation_mode()
    if judge_mode and mode != "ENFORCED":
        raise IsolationNotEnforcedError("judge mode requires authenticated examiner isolation")
    return judge_mode, mode
