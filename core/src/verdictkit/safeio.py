"""Safe file handling shared by custody, signing, the MCP tools and replay scratch.

No domain logic. Design: DD8-2 (key files), DD8-5 (approved roots), D5.5 (signing keys).

POSIX: owner and mode checks on the opened descriptor, ``O_NOFOLLOW`` component walks.
Windows: POSIX mode bits carry no meaning, so confidentiality is decided by the DACL. A path is
"private" when every ALLOW entry names the current user, SYSTEM, Administrators, CREATOR OWNER
or OWNER RIGHTS. Reparse points are rejected. Residual risk: the Windows checks are
path-based and cannot close a race between the check and the open (documented, R-D5-1).

Error messages are fixed strings. They never contain the path, the file content or an OS error.
"""
from __future__ import annotations

import os
import re
import stat
import sys
from pathlib import Path
from typing import Iterable, Sequence

IS_WINDOWS = sys.platform == "win32"
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400


class PathNotAllowed(ValueError):
    """The path is outside every approved root or has a forbidden form. Never echoes the path."""

    def __init__(self) -> None:
        super().__init__("path is not permitted")


class UnsafeFile(ValueError):
    """A file failed an existence, type, owner, permission or size check.

    ``reason`` is one of MISSING, UNREADABLE, NOT_REGULAR, PERMISSIONS, TOO_LARGE, NOT_REMOVED.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class FileUnavailable(ValueError):
    """Inside an approved root, but the file is missing, too large or not a regular file."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason  # NOT_FOUND, TOO_LARGE


# --------------------------------------------------------------------------- Windows ACLs

# Principals that may appear in the ALLOW entries of a private object on Windows.
_WIN_FIXED_SIDS = frozenset({"S-1-5-18", "S-1-5-32-544", "S-1-3-0", "S-1-3-4"})
_win_user_sid_cache: str | None = None


def _win_libs():
    import ctypes
    from ctypes import wintypes
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.LocalFree.argtypes = [ctypes.c_void_p]
    k32.LocalFree.restype = ctypes.c_void_p
    adv.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    adv.ConvertSidToStringSidW.restype = wintypes.BOOL
    return ctypes, wintypes, adv, k32


def _win_sid_string(adv, k32, ctypes, psid: int) -> str:
    out = ctypes.c_void_p()
    if not adv.ConvertSidToStringSidW(ctypes.c_void_p(psid), ctypes.byref(out)):
        raise OSError("sid conversion failed")
    try:
        return ctypes.wstring_at(out.value)
    finally:
        k32.LocalFree(out)


def _win_current_user_sid() -> str:
    global _win_user_sid_cache
    if _win_user_sid_cache is not None:
        return _win_user_sid_cache
    ctypes, wintypes, adv, k32 = _win_libs()
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    adv.OpenProcessToken.restype = wintypes.BOOL
    adv.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                                        ctypes.POINTER(wintypes.DWORD)]
    adv.GetTokenInformation.restype = wintypes.BOOL
    token = wintypes.HANDLE()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):  # TOKEN_QUERY
        raise OSError("token unavailable")
    try:
        needed = wintypes.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))  # TokenUser
        buf = ctypes.create_string_buffer(needed.value)
        if not adv.GetTokenInformation(token, 1, buf, needed, ctypes.byref(needed)):
            raise OSError("token information unavailable")
        psid = ctypes.c_void_p.from_buffer(buf).value  # TOKEN_USER.User.Sid
        _win_user_sid_cache = _win_sid_string(adv, k32, ctypes, psid)
        return _win_user_sid_cache
    finally:
        k32.CloseHandle(token)


def _win_dacl_allow_sids(path: str) -> list[str] | None:
    """SID strings of every ALLOW entry. ``None`` when an entry type is not understood
    (callers treat that as not private). A NULL DACL grants everyone access."""
    ctypes, wintypes, adv, k32 = _win_libs()
    adv.GetNamedSecurityInfoW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, wintypes.DWORD, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
                                          ctypes.POINTER(ctypes.c_void_p)]
    adv.GetNamedSecurityInfoW.restype = wintypes.DWORD
    adv.GetAclInformation.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.c_int]
    adv.GetAclInformation.restype = wintypes.BOOL
    adv.GetAce.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p)]
    adv.GetAce.restype = wintypes.BOOL

    class AclSizeInformation(ctypes.Structure):
        _fields_ = [("AceCount", wintypes.DWORD), ("AclBytesInUse", wintypes.DWORD),
                    ("AclBytesFree", wintypes.DWORD)]

    dacl, sd = ctypes.c_void_p(), ctypes.c_void_p()
    # SE_FILE_OBJECT = 1, DACL_SECURITY_INFORMATION = 4
    if adv.GetNamedSecurityInfoW(path, 1, 4, None, None, ctypes.byref(dacl), None, ctypes.byref(sd)) != 0:
        raise OSError("security descriptor unavailable")
    try:
        if not dacl.value:
            return ["S-1-1-0"]
        info = AclSizeInformation()
        if not adv.GetAclInformation(dacl, ctypes.byref(info), ctypes.sizeof(info), 2):  # AclSizeInformation
            raise OSError("acl unavailable")
        sids: list[str] = []
        for index in range(info.AceCount):
            ace = ctypes.c_void_p()
            if not adv.GetAce(dacl, index, ctypes.byref(ace)):
                raise OSError("ace unavailable")
            ace_type = ctypes.c_ubyte.from_address(ace.value).value
            if ace_type == 1:      # ACCESS_DENIED_ACE_TYPE only restricts access
                continue
            if ace_type != 0:      # object, callback and other allow forms: not understood
                return None
            sids.append(_win_sid_string(adv, k32, ctypes, ace.value + 8))  # SidStart follows Header+Mask
        return sids
    finally:
        k32.LocalFree(sd)


def _win_is_private(path: str) -> bool:
    try:
        sids = _win_dacl_allow_sids(path)
        if sids is None:
            return False
        allowed = _WIN_FIXED_SIDS | {_win_current_user_sid()}
        return all(s in allowed for s in sids)
    except OSError:
        return False


def _win_final_path(fd: int) -> str | None:
    """Real path of an open descriptor (``GetFinalPathNameByHandleW``), without the ``\\\\?\\`` prefix."""
    import ctypes
    import msvcrt
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    k32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    handle = msvcrt.get_osfhandle(fd)
    buf = ctypes.create_unicode_buffer(32768)
    n = k32.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)  # VOLUME_NAME_DOS
    if n == 0 or n >= len(buf):
        return None
    final = buf.value
    if final.startswith("\\\\?\\UNC\\"):
        return None
    return final[4:] if final.startswith("\\\\?\\") else final


# ------------------------------------------------------------------ private files and dirs

def is_private_dir(path: str | os.PathLike) -> bool:
    """POSIX: a real directory owned by this user with mode exactly 0700.
    Windows: a real directory (not a reparse point) whose DACL names only trusted principals."""
    p = os.fspath(path)
    try:
        st = os.lstat(p)
    except OSError:
        return False
    if not stat.S_ISDIR(st.st_mode):
        return False
    if IS_WINDOWS:
        if getattr(st, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT:
            return False
        return _win_is_private(p)
    return st.st_uid == os.geteuid() and stat.S_IMODE(st.st_mode) == 0o700


def read_secret_file(path: str | os.PathLike, *, max_bytes: int, remove: bool = False,
                     require_private: bool = True) -> bytes:
    """Read a key file once. The file must be a regular file, not a link, owned by this user
    and unreadable by anyone else (POSIX), or have a private DACL (Windows).
    ``require_private=False`` keeps the type, link and size checks for public files."""
    p = os.fspath(path)
    if not isinstance(p, str) or not p or "\x00" in p or not os.path.isabs(p):
        raise UnsafeFile("UNREADABLE")
    if IS_WINDOWS:
        try:
            pre = os.lstat(p)
        except FileNotFoundError:
            raise UnsafeFile("MISSING") from None
        except OSError:
            raise UnsafeFile("UNREADABLE") from None
        if stat.S_ISLNK(pre.st_mode) or getattr(pre, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise UnsafeFile("NOT_REGULAR")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(p, flags)
    except FileNotFoundError:
        raise UnsafeFile("MISSING") from None
    except OSError:
        raise UnsafeFile("UNREADABLE") from None  # includes a symlink under O_NOFOLLOW
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise UnsafeFile("NOT_REGULAR")
        if require_private:
            if IS_WINDOWS:
                if not _win_is_private(p):
                    raise UnsafeFile("PERMISSIONS")
            elif st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) & 0o077:
                raise UnsafeFile("PERMISSIONS")
        if st.st_size > max_bytes:
            raise UnsafeFile("TOO_LARGE")
        with os.fdopen(fd, "rb", closefd=False) as fh:
            data = fh.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise UnsafeFile("TOO_LARGE")
    finally:
        os.close(fd)
    if remove:
        try:
            os.unlink(p)
        except OSError:
            raise UnsafeFile("NOT_REMOVED") from None
    return data


def write_private_file(path: Path, data: bytes) -> None:
    """Atomic write: exclusive temporary file with mode 0600, fsync, then replace."""
    path = Path(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{os.urandom(4).hex()}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ------------------------------------------------------------------------- approved roots

_WIN_DRIVE_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_WIN_FORBIDDEN = re.compile(r'[<>"|?*]')


def _syntactically_allowed(path: str) -> bool:
    """Rejects NUL, relative, UNC, ``\\\\?\\`` and ``\\\\.\\`` device paths, alternate data streams
    and parent-directory components, before any file system access."""
    if not isinstance(path, str) or not path or len(path) > 4096 or "\x00" in path:
        return False
    if IS_WINDOWS:
        if path.startswith(("\\\\", "//")) or not _WIN_DRIVE_ABS.match(path):
            return False
        if ":" in path[2:] or _WIN_FORBIDDEN.search(path):
            return False
        parts = re.split(r"[\\/]+", path)
    else:
        if not path.startswith("/"):
            return False
        parts = path.split("/")
    return ".." not in parts


def pin_roots(raw_roots: Iterable[str]) -> tuple[Path, ...]:
    """Resolve approved roots once. Invalid, missing or file-system-root entries are dropped,
    so a bad configuration can only shrink the set of readable locations."""
    pinned: list[Path] = []
    for raw in raw_roots:
        if not _syntactically_allowed(raw):
            continue
        try:
            resolved = Path(raw).resolve(strict=True)
        except OSError:
            continue
        if not resolved.is_dir() or resolved.parent == resolved or resolved in pinned:
            continue
        pinned.append(resolved)
    return tuple(pinned)


def _below(root: Path, path: Path) -> tuple[str, ...] | None:
    rp = [os.path.normcase(x) for x in root.parts]
    pp = [os.path.normcase(x) for x in path.parts]
    if len(pp) <= len(rp) or pp[:len(rp)] != rp:
        return None
    return path.parts[len(rp):]


def read_file_under_roots(path: str, roots: Sequence[Path], *, max_bytes: int) -> bytes:
    """Read one regular file located below an approved root.

    Outside every root (or a forbidden form) is ``PathNotAllowed`` whether or not the file exists.
    Inside a root, a missing or oversized file is ``FileUnavailable``. Type and size are checked on
    the opened handle, never on the path."""
    if not _syntactically_allowed(path):
        raise PathNotAllowed()
    candidate = Path(path)
    for root in roots:
        rel = _below(root, candidate)
        if rel is not None:
            return _open_below(root, rel, max_bytes)
    raise PathNotAllowed()


def _read_handle(fd: int, max_bytes: int) -> bytes:
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode):
        raise PathNotAllowed()
    if st.st_size > max_bytes:
        raise FileUnavailable("TOO_LARGE")
    with os.fdopen(fd, "rb", closefd=False) as fh:
        data = fh.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise FileUnavailable("TOO_LARGE")
    return data


def _open_below(root: Path, rel: tuple[str, ...], max_bytes: int) -> bytes:
    if IS_WINDOWS:
        return _open_below_windows(root, rel, max_bytes)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    dir_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | cloexec)
    try:
        for part in rel[:-1]:
            try:
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | cloexec, dir_fd=dir_fd)
            except FileNotFoundError:
                raise FileUnavailable("NOT_FOUND") from None
            except OSError:
                raise PathNotAllowed() from None  # symlink or not a directory
            os.close(dir_fd)
            dir_fd = nxt
        try:
            fd = os.open(rel[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | cloexec, dir_fd=dir_fd)
        except FileNotFoundError:
            raise FileUnavailable("NOT_FOUND") from None
        except OSError:
            raise PathNotAllowed() from None
    finally:
        os.close(dir_fd)
    try:
        return _read_handle(fd, max_bytes)
    finally:
        os.close(fd)


def _open_below_windows(root: Path, rel: tuple[str, ...], max_bytes: int) -> bytes:
    current = root
    for part in rel:
        current = current / part
        try:
            st = os.lstat(current)
        except FileNotFoundError:
            raise FileUnavailable("NOT_FOUND") from None
        except OSError:
            raise PathNotAllowed() from None
        if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise PathNotAllowed()
    try:
        fd = os.open(current, os.O_RDONLY | os.O_BINARY)
    except FileNotFoundError:
        raise FileUnavailable("NOT_FOUND") from None
    except OSError:
        raise PathNotAllowed() from None
    try:
        final = _win_final_path(fd)
        if final is None or _below(root, Path(final)) is None:
            raise PathNotAllowed()
        return _read_handle(fd, max_bytes)
    finally:
        os.close(fd)
