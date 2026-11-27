"""Vault key hand-off and file hygiene (design DD8-2) plus vault and path hardening.

Regression tests for: key exposure through process arguments, unsafe key and sealed-file
handling (links, permissions, path syntax in a case id), and POSIX/Windows permission checks.
"""
from __future__ import annotations

import base64
import os
import re
import stat
import sys
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

from security.helpers import POSIX, grant_everyone
from verdictkit import safeio
from verdictkit.custody import keyfile
from verdictkit.custody.keyfile import VaultKeyError, load_vault_key
from verdictkit.custody.vault import SealedRef, Vault
from verdictkit.model import IsolationMode

ROOT = Path(__file__).resolve().parents[2]
KEY = bytes(range(32))
KEY_B64 = base64.b64encode(KEY).decode()


@pytest.fixture(autouse=True)
def _clear_key_cache():
    keyfile._from_file.clear()
    yield
    keyfile._from_file.clear()


def _key_file(tmp_path: Path, text: str = KEY_B64 + "\n", mode: int = 0o400) -> Path:
    path = tmp_path / "vault.key"
    path.write_text(text)
    if POSIX:
        path.chmod(mode)
    return path


# ----------------------------------------------------------------------------- key loader

def test_key_file_is_read_once_removed_and_kept_in_memory(tmp_path):
    path = _key_file(tmp_path)
    env = {"VK_VAULT_KEY_FILE": str(path)}
    assert load_vault_key(env) == KEY
    assert not path.exists(), "the key file must be removed after the first read"
    assert load_vault_key(env) == KEY  # later lookups are served from process memory


def test_environment_key_still_supported_and_unset_means_none():
    assert load_vault_key({"VK_VAULT_KEY": KEY_B64}) == KEY
    assert load_vault_key({}) is None


def test_both_key_sources_set_is_an_error_not_a_precedence_rule(tmp_path):
    path = _key_file(tmp_path)
    with pytest.raises(VaultKeyError):
        load_vault_key({"VK_VAULT_KEY_FILE": str(path), "VK_VAULT_KEY": KEY_B64})
    assert path.exists(), "an ambiguous configuration must not consume the file"


@pytest.mark.parametrize("text", ["not base64 !!!", base64.b64encode(b"too short").decode(),
                                  base64.b64encode(bytes(33)).decode()])
def test_malformed_key_is_refused_without_echoing_it(tmp_path, text):
    with pytest.raises(VaultKeyError) as excinfo:
        load_vault_key({"VK_VAULT_KEY": text})
    assert text not in str(excinfo.value)
    path = _key_file(tmp_path, text=text + "\n")
    with pytest.raises(VaultKeyError) as excinfo:
        load_vault_key({"VK_VAULT_KEY_FILE": str(path)})
    assert text not in str(excinfo.value) and str(path) not in str(excinfo.value)


def test_missing_or_relative_key_file_is_refused(tmp_path):
    with pytest.raises(VaultKeyError):
        load_vault_key({"VK_VAULT_KEY_FILE": str(tmp_path / "absent.key")})
    with pytest.raises(VaultKeyError):
        load_vault_key({"VK_VAULT_KEY_FILE": "relative/vault.key"})


def test_key_file_that_is_a_directory_is_refused(tmp_path):
    with pytest.raises(VaultKeyError):
        load_vault_key({"VK_VAULT_KEY_FILE": str(tmp_path)})


@pytest.mark.skipif(not POSIX, reason="POSIX mode bits")
@pytest.mark.parametrize("mode", [0o640, 0o604, 0o644, 0o660])
def test_key_file_readable_by_group_or_others_is_refused_and_kept(tmp_path, mode):
    path = _key_file(tmp_path, mode=mode)
    with pytest.raises(VaultKeyError, match="not accessible to others"):
        load_vault_key({"VK_VAULT_KEY_FILE": str(path)})
    assert path.exists()


@pytest.mark.skipif(not POSIX, reason="POSIX symlinks and O_NOFOLLOW")
def test_symlinked_key_file_is_refused(tmp_path):
    target = _key_file(tmp_path)
    link = tmp_path / "link.key"
    link.symlink_to(target)
    with pytest.raises(VaultKeyError):
        load_vault_key({"VK_VAULT_KEY_FILE": str(link)})
    assert target.exists()


@pytest.mark.skipif(POSIX, reason="Windows access-control check")
def test_windows_key_file_readable_by_everyone_is_refused(tmp_path):
    path = _key_file(tmp_path)
    assert load_vault_key({"VK_VAULT_KEY_FILE": str(path)}) == KEY  # private ACL: accepted
    keyfile._from_file.clear()
    path = _key_file(tmp_path)
    grant_everyone(path)
    with pytest.raises(VaultKeyError, match="not accessible to others"):
        load_vault_key({"VK_VAULT_KEY_FILE": str(path)})


# --------------------------------------------------------------- entrypoint (static check)

def _function_body(text: str, name: str) -> str:
    match = re.search(rf"^{name}\(\) \{{\n(.*?)^\}}", text, re.S | re.M)
    assert match, name
    return match.group(1)


def test_entrypoint_never_puts_the_vault_key_in_an_argument_vector():
    """DD8-2: the key reaches the custodian as a file path. Static guard; the container gate
    ``gate-http`` additionally samples /proc for the key while a real run executes."""
    # In a checkout the script is deploy/entrypoint.sh; in the image it is the installed copy.
    script = ROOT / "deploy/entrypoint.sh"
    if not script.exists():
        script = Path("/usr/local/bin/entrypoint.sh")
    text = script.read_text(encoding="utf-8")
    assert not re.search(r"\bVK_VAULT_KEY=", text), "the key must not be assigned as an argument"
    assert not re.search(r"\$\{?vault_key\b", text), "no script variable may carry the key"
    assert "VK_VAULT_KEY_FILE" in _function_body(text, "as_custodian")
    assert re.search(r'printf \'%s\' "\$VK_VAULT_KEY" > "\$key_file"', text), "builtin printf redirection"
    assert "chmod 0400" in text and "chown vk-custodian:vk-custodian" in text
    examiner_env = _function_body(text, "as_examiner")
    for secret in ("VK_VAULT_KEY", "VK_SIGNING_KEY_FILE", "VK_TRUST_STORE"):
        assert secret not in examiner_env, f"examiner environment allowlist must not contain {secret}"


def test_examiner_worker_refuses_custodian_secrets_in_its_environment(monkeypatch, capsys):
    from verdictkit.examiner import worker
    for name in ("VK_VAULT_KEY", "VK_VAULT_KEY_FILE", "VK_SIGNING_KEY_FILE"):
        monkeypatch.delenv("VK_VAULT_KEY", raising=False)
        monkeypatch.setenv(name, "x")
        assert worker.main() == 1
        assert name in capsys.readouterr().err
        monkeypatch.delenv(name)


# ------------------------------------------------------------------------------- vault

@pytest.mark.parametrize("case_id", ["../escape", "a/b", "a\\b", "", ".hidden", "x" * 129, "bad id",
                                     "a\x00b", "..", "C:evil", "case.1", "-leading"])
def test_vault_refuses_case_ids_with_path_syntax(tmp_path, case_id):
    vault = Vault(tmp_path / "v", KEY, IsolationMode.UNENFORCED)
    with pytest.raises(ValueError):
        vault.seal(case_id, {"stated_total": "1.00"})
    assert [p.name for p in tmp_path.rglob("*") if p.is_file()] == []


def test_seal_round_trip_is_atomic_and_private(tmp_path):
    vault_dir = tmp_path / "v"
    vault = Vault(vault_dir, KEY, IsolationMode.UNENFORCED)
    ref = vault.seal("case-1", {"stated_total": "15.50"})
    assert vault.unseal(ref) == {"stated_total": "15.50"}
    assert [p.name for p in vault_dir.iterdir()] == ["case-1.sealed"], "no temporary file may remain"
    if POSIX:
        assert stat.S_IMODE(Path(ref.path).stat().st_mode) == 0o600
    vault.seal("case-1", {"stated_total": "16.00"})  # replacement is atomic and allowed
    assert vault.unseal(ref) == {"stated_total": "16.00"}


def test_sealed_reference_cannot_redirect_the_read(tmp_path):
    vault = Vault(tmp_path / "v", KEY, IsolationMode.UNENFORCED)
    ref = vault.seal("case-1", {"stated_total": "15.50"})
    elsewhere = tmp_path / "elsewhere.sealed"
    elsewhere.write_bytes(Path(ref.path).read_bytes())
    with pytest.raises(ValueError):
        vault.unseal(SealedRef(case_id="case-1", path=str(elsewhere)))
    with pytest.raises(ValueError):
        vault.unseal(SealedRef(case_id="../case-1", path=ref.path))
    with pytest.raises(ValueError):
        vault.unseal(SealedRef(case_id="case-1", path=str(tmp_path / ".." / "v" / "case-1.sealed") + "x"))


def test_tampered_or_oversized_sealed_file_is_refused(tmp_path):
    vault = Vault(tmp_path / "v", KEY, IsolationMode.UNENFORCED)
    ref = vault.seal("case-1", {"stated_total": "15.50"})
    blob = bytearray(Path(ref.path).read_bytes())
    blob[-1] ^= 0xFF
    Path(ref.path).write_bytes(bytes(blob))
    with pytest.raises(InvalidTag):
        vault.unseal(ref)
    Path(ref.path).write_bytes(b"\0" * (2 * 1024 * 1024))
    with pytest.raises(ValueError):
        vault.unseal(ref)


@pytest.mark.skipif(not POSIX, reason="POSIX symlinks and O_NOFOLLOW")
def test_symlinked_sealed_file_is_refused(tmp_path):
    vault = Vault(tmp_path / "v", KEY, IsolationMode.UNENFORCED)
    ref = vault.seal("case-1", {"stated_total": "15.50"})
    real = tmp_path / "real.sealed"
    Path(ref.path).rename(real)
    Path(ref.path).symlink_to(real)
    with pytest.raises(ValueError):
        vault.unseal(ref)


# -------------------------------------------------------- permission checks, both platforms

@pytest.mark.skipif(not POSIX, reason="POSIX mode bits")
def test_private_directory_check_on_posix(tmp_path):
    directory = tmp_path / "d"
    directory.mkdir(mode=0o700)
    directory.chmod(0o700)
    assert safeio.is_private_dir(directory)
    for mode in (0o750, 0o755, 0o701, 0o777):
        directory.chmod(mode)
        assert not safeio.is_private_dir(directory), oct(mode)
    assert not safeio.is_private_dir(tmp_path / "missing")
    (tmp_path / "f").write_text("x")
    assert not safeio.is_private_dir(tmp_path / "f")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows access-control list")
def test_private_directory_check_on_windows(tmp_path):
    """BE-1: on Windows the equivalent of mode 0700 is a DACL naming only the current user,
    SYSTEM and Administrators."""
    directory = tmp_path / "d"
    os.mkdir(directory, 0o700)
    assert safeio.is_private_dir(directory)
    grant_everyone(directory)
    assert not safeio.is_private_dir(directory), "an extra ALLOW entry must make it non-private"
    assert not safeio.is_private_dir(tmp_path / "missing")
