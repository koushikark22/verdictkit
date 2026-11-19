"""Container-only isolation checks. Core requirement 4.

CI runs this inside the image as the examiner user:
    setpriv --reuid=vk-examiner --regid=vk-examiner --init-groups \
        env -i PATH=$PATH VK_ISOLATION=enforced VK_VAULT_DIR=/var/lib/vk/vault \
        uv run pytest -m isolation tests/contract/test_isolation.py
"""
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.isolation


def test_examiner_cannot_list_vault():
    with pytest.raises(PermissionError):
        os.listdir(os.environ["VK_VAULT_DIR"])


def test_examiner_cannot_read_sealed_files():
    vault = Path(os.environ["VK_VAULT_DIR"])
    probe = vault / "probe.sealed"  # created by the entrypoint as vk-custodian for this test
    with pytest.raises(PermissionError):
        probe.read_bytes()


def test_examiner_environment_has_no_vault_key():
    assert "VK_VAULT_KEY" not in os.environ


def test_examiner_is_not_custodian_or_root():
    assert os.getuid() != 0
    import pwd

    assert pwd.getpwuid(os.getuid()).pw_name == "vk-examiner"
