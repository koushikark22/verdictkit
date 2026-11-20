"""Socket examiner must not claim enforced isolation without authenticated OS peer."""

import pytest

from verdictkit.examiner.client import SocketExaminer
from verdictkit.examiner.identity import ExaminerIdentityError
from verdictkit.model import IsolationMode


def test_socket_path_alone_is_not_isolation_proof():
    examiner = SocketExaminer("/not/a/real/examiner.sock")
    assert examiner.isolation is IsolationMode.UNENFORCED


def test_cannot_select_arbitrary_peer_uid(monkeypatch):
    monkeypatch.setattr(
        "verdictkit.examiner.identity.resolve_examiner_uid",
        lambda configured: 901,
    )
    with pytest.raises(ExaminerIdentityError, match="designated OS account"):
        SocketExaminer("/not/a/real/examiner.sock", expected_peer_uid=902)


def test_failed_peer_verification_never_stamps_enforced(monkeypatch):
    monkeypatch.setattr(
        "verdictkit.examiner.identity.resolve_examiner_uid",
        lambda configured: 901,
    )

    def reject_socket(path, *, expected_uid):
        raise ExaminerIdentityError("peer not authenticated")

    monkeypatch.setattr(
        "verdictkit.examiner.identity.verify_examiner_socket",
        reject_socket,
    )
    with pytest.raises(ExaminerIdentityError, match="peer not authenticated"):
        SocketExaminer("/not/a/real/examiner.sock", expected_peer_uid=901)


def test_verified_peer_can_enable_enforced_stamping(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "verdictkit.examiner.identity.resolve_examiner_uid",
        lambda configured: 901,
    )

    def accept_socket(path, *, expected_uid):
        calls.append((path, expected_uid))
        return 1234

    monkeypatch.setattr(
        "verdictkit.examiner.identity.verify_examiner_socket",
        accept_socket,
    )
    examiner = SocketExaminer("/run/vk/examiner.sock", expected_peer_uid=901)
    assert examiner.isolation is IsolationMode.ENFORCED
    assert calls == [("/run/vk/examiner.sock", 901)]
