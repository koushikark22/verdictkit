"""Encrypted custodian draft storage regressions (isolated temporary directory)."""

import pytest
from cryptography.exceptions import InvalidTag

from verdictkit.api.draft_store import DraftAlreadyExists, DraftNotFound, DraftStore
from verdictkit.api.intake_boundary import PreparedIntake

CASE_ID = "case_" + "a" * 32


def _prepared(secret="OUTPUT_SECRET_987"):
    return PreparedIntake(
        "quote.finance.v1", "LIVE_EVIDENCE",
        {"claim_type": "quote.finance.v1", "params": {"selling_price": "25000"},
         "outcomes": {"monthly_payment": secret}, "assumptions": {}},
        ({"name": "monthly_payment", "captured": True},),
    )


def test_encrypted_at_rest_and_metadata_redacted(tmp_path):
    store = DraftStore(tmp_path / "cases", b"k" * 32)
    store.create(CASE_ID, _prepared(), now=100)
    raw = (tmp_path / "cases" / "drafts.sqlite3").read_bytes()
    assert b"OUTPUT_SECRET_987" not in raw
    assert b"25000" not in raw
    metadata = store.get_metadata(CASE_ID, now=100)
    assert metadata["state"] == "DRAFT"
    assert "outcomes" not in metadata
    assert "OUTPUT_SECRET_987" not in str(metadata)
    assert store.load_private(CASE_ID, now=100)["outcomes"]["monthly_payment"] == "OUTPUT_SECRET_987"


def test_duplicate_case_is_not_overwritten(tmp_path):
    store = DraftStore(tmp_path, b"k" * 32)
    store.create(CASE_ID, _prepared("ORIGINAL"), now=100)
    with pytest.raises(DraftAlreadyExists):
        store.create(CASE_ID, _prepared("REPLACEMENT"), now=100)
    assert store.load_private(CASE_ID, now=100)["outcomes"]["monthly_payment"] == "ORIGINAL"


def test_expiration_and_purge(tmp_path):
    store = DraftStore(tmp_path, b"k" * 32, ttl_seconds=10)
    store.create(CASE_ID, _prepared(), now=100)
    with pytest.raises(DraftNotFound):
        store.get_metadata(CASE_ID, now=110)
    with pytest.raises(DraftNotFound):
        store.load_private(CASE_ID, now=110)
    assert store.purge_expired(now=110) == 1


def test_wrong_key_cannot_decrypt(tmp_path):
    DraftStore(tmp_path, b"k" * 32).create(CASE_ID, _prepared(), now=100)
    other = DraftStore(tmp_path, b"x" * 32)
    with pytest.raises(InvalidTag):
        other.load_private(CASE_ID, now=100)


def test_invalid_id_and_key_rejected(tmp_path):
    with pytest.raises(ValueError):
        DraftStore(tmp_path, b"short")
    store = DraftStore(tmp_path, b"k" * 32)
    with pytest.raises(ValueError):
        store.create("../escape", _prepared(), now=100)


def test_read_metadata_after_new_process_object(tmp_path):
    DraftStore(tmp_path, b"k" * 32).create(CASE_ID, _prepared(), now=100)
    reopened = DraftStore(tmp_path, b"k" * 32)
    assert reopened.get_metadata(CASE_ID, now=100)["claimType"] == "quote.finance.v1"

def test_symlink_draft_directory_does_not_change_target_permissions(tmp_path):
    target = tmp_path / "target"
    target.mkdir(mode=0o755)
    target.chmod(0o755)
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")
    before = target.stat().st_mode & 0o777
    with pytest.raises(ValueError, match="symlink"):
        DraftStore(link, b"k" * 32)
    assert target.stat().st_mode & 0o777 == before
