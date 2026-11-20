"""Examiner client and in-process dev examiner. Requirements: core 4.

``SocketExaminer`` talks to the long-lived worker (``python -m verdictkit.examiner.worker``)
running as ``vk-examiner`` on ``VK_EXAMINER_SOCKET``. ``InProcessExaminer`` is for tests
and native dev only; it reports ``IsolationMode.UNENFORCED``.
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Protocol

from ..model import BlindedTask, IsolationMode
from ..plugin import Examination, Registry
from .protocol import MAX_FRAME_BYTES, decode_result, decode_task, encode_result, encode_task, frame


class ExaminerTimeout(TimeoutError):
    pass


class Examiner(Protocol):
    isolation: IsolationMode

    def examine(self, task: BlindedTask) -> Examination: ...


class SocketExaminer:
    isolation = IsolationMode.UNENFORCED

    def __init__(self, socket_path: str, timeout_s: float = 60.0,
                 expected_peer_uid: int | None = None) -> None:
        self._socket_path = socket_path
        self._timeout_s = timeout_s
        self._expected_peer_uid = expected_peer_uid
        self.isolation = IsolationMode.UNENFORCED

        if expected_peer_uid is not None:
            from .identity import (
                ExaminerIdentityError,
                resolve_examiner_uid,
                verify_examiner_socket,
            )

            # Do not let a caller choose an arbitrary UID as proof.
            actual_uid = resolve_examiner_uid("")
            if expected_peer_uid != actual_uid:
                raise ExaminerIdentityError("examiner UID does not match designated OS account")
            verify_examiner_socket(socket_path, expected_uid=actual_uid)
            self.isolation = IsolationMode.ENFORCED

    def examine(self, task: BlindedTask) -> Examination:
        import socket as _socket

        payload = encode_task(task)
        framed = frame(payload)

        sock = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        sock.settimeout(self._timeout_s)
        try:
            sock.connect(self._socket_path)
            if self._expected_peer_uid is not None:
                from .identity import verify_connected_peer
                verify_connected_peer(sock, self._expected_peer_uid)
            sock.sendall(framed)

            # Read 4-byte length prefix
            length_data = _recv_exactly(sock, 4)
            if length_data is None:
                raise ExaminerTimeout("examiner closed connection before sending length")
            (length,) = struct.unpack(">I", length_data)
            if length > MAX_FRAME_BYTES:
                raise ValueError(f"response frame too large: {length}")
            result_data = _recv_exactly(sock, length)
            if result_data is None:
                raise ExaminerTimeout("examiner closed connection before sending result")
            return decode_result(result_data)
        except TimeoutError as exc:
            raise ExaminerTimeout(f"examiner timed out after {self._timeout_s}s") from exc
        finally:
            sock.close()


def _recv_exactly(sock, n: int) -> bytes | None:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


class InProcessExaminer:
    """Runs plugin.examine in-process. Still encodes/decodes the task through the wire
    protocol so the blinding path is identical to production."""

    isolation = IsolationMode.UNENFORCED

    def __init__(self, registry: Registry, evidence_root: str | None = None) -> None:
        self._registry = registry
        self._evidence_root = evidence_root

    def examine(self, task: BlindedTask) -> Examination:
        # Encode and decode through the wire protocol to exercise the blinding path
        encoded = encode_task(task)
        decoded_task = decode_task(encoded)

        claim_type = self._registry.get(decoded_task.claim_type)

        # Build an evidence reader (empty for now — no network in in-process mode)
        from ..sweep import expand_grid

        grid = expand_grid(decoded_task.assumptions)
        points = list(grid.points)

        # Build a minimal evidence reader from the evidence store if available
        evidence_reader = _EmptyEvidenceReader()
        if self._evidence_root is not None and decoded_task.evidence_refs:
            from ..evidence.store import ReadOnlyEvidence
            evidence_reader = ReadOnlyEvidence(Path(self._evidence_root),
                                               decoded_task.evidence_refs)

        examination = claim_type.examine(decoded_task, evidence_reader, points)

        # Encode/decode the result too
        encoded_result = encode_result(examination)
        return decode_result(encoded_result)


class _EmptyEvidenceReader:
    def read(self, sha256: str) -> bytes:
        raise KeyError(f"no evidence available: {sha256}")

    def items(self):
        return ()
