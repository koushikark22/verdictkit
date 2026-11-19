"""Kernel peer credentials are required before the judge can trust a socket."""
from __future__ import annotations

import os
import socket
import struct
import sys
from unittest.mock import patch

import pytest

from verdictkit.examiner.identity import (
    ExaminerIdentityError,
    resolve_examiner_uid,
    verify_connected_peer,
    verify_examiner_socket,
)
from verdictkit.api.server import create_app
from verdictkit.plugin import Registry


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux peer credentials")
def test_same_uid_cannot_be_claimed_as_examiner():
    with pytest.raises(ExaminerIdentityError, match="distinct"):
        resolve_examiner_uid(str(os.geteuid()))
    with pytest.raises(ExaminerIdentityError):
        resolve_examiner_uid("not-an-id")
    with pytest.raises(ExaminerIdentityError):
        resolve_examiner_uid("-1")
    with pytest.raises(ExaminerIdentityError):
        resolve_examiner_uid("0")


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux peer credentials")
def test_local_socket_cannot_impersonate_separate_worker(tmp_path):
    path = str(tmp_path / "examiner.sock")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(path)
        server.listen(1)
        other_uid = os.geteuid() + 1
        with pytest.raises(ExaminerIdentityError, match="owner or type"):
            verify_examiner_socket(path, expected_uid=other_uid)
        with patch.dict(os.environ, {
            "VK_JUDGE_MODE": "1",
            "VK_EXAMINER_SOCKET": path,
            "VK_EXAMINER_UID": str(other_uid),
        }):
            with pytest.raises(RuntimeError, match="authenticated"):
                create_app(Registry())


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux peer credentials")
def test_socket_paths_are_not_authorization():
    with pytest.raises(ExaminerIdentityError):
        verify_examiner_socket("/tmp/absent-verdictkit-examiner.sock", expected_uid=1001)
    with pytest.raises(ExaminerIdentityError):
        verify_examiner_socket("relative.sock", expected_uid=1001)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux peer credentials")
def test_kernel_peer_uid_validation():
    class FakeSocket:
        def __init__(self, uid):
            self.uid = uid

        def getsockopt(self, level, opt, size):
            assert level == socket.SOL_SOCKET
            assert opt == socket.SO_PEERCRED
            assert size == struct.calcsize("3i")
            return struct.pack("3i", 12345, self.uid, 12345)

    peer_uid = os.geteuid() + 1
    assert verify_connected_peer(FakeSocket(peer_uid), peer_uid) == 12345
    with pytest.raises(ExaminerIdentityError, match="mismatch"):
        verify_connected_peer(FakeSocket(os.geteuid()), peer_uid)
    with pytest.raises(ExaminerIdentityError, match="mismatch"):
        verify_connected_peer(FakeSocket(peer_uid), peer_uid + 1)
