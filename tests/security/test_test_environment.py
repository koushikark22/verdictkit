"""The test process must not carry unrelated credentials (Batch 2; previous batch leaked one)."""
from __future__ import annotations

import os
import subprocess
import sys

from envscrub import is_sensitive, scrub_environment


def test_credential_like_names_are_removed_and_everything_else_is_kept():
    env = {
        "ALPACA_API_KEY_ID": "x", "APCA_API_SECRET_KEY": "x", "AWS_ACCESS_KEY_ID": "x", "GITHUB_TOKEN": "x",
        "OPENAI_API_KEY": "x", "ANTHROPIC_API_KEY": "x", "NPM_CONFIG_TOKEN": "x", "MY_DB_PASSWORD": "x",
        "SSH_AUTH_SOCK": "x", "AZURE_CLIENT_SECRET": "x", "DOCKER_PASSWORD": "x",
        "PATH": "p", "SystemRoot": "C:\\Windows", "TEMP": "t", "HOME": "h", "LANG": "C", "UV_CACHE_DIR": "u",
        "HYPOTHESIS_PROFILE": "ci", "PYTHONHASHSEED": "0",
        "VK_VAULT_KEY": "kept", "VK_SIGNING_KEY_FILE": "kept", "vk_trust_store_file": "kept",
    }
    removed = scrub_environment(env)
    assert removed == 11
    assert sorted(env) == sorted(["PATH", "SystemRoot", "TEMP", "HOME", "LANG", "UV_CACHE_DIR",
                                  "HYPOTHESIS_PROFILE", "PYTHONHASHSEED", "VK_VAULT_KEY",
                                  "VK_SIGNING_KEY_FILE", "vk_trust_store_file"])
    assert scrub_environment(env) == 0, "scrubbing is idempotent"


def test_the_running_test_process_holds_no_credential_like_variables():
    assert [n for n in os.environ if is_sensitive(n)] == []


def test_a_subprocess_started_from_the_test_process_inherits_none():
    code = ("import os,sys; sys.path.insert(0, %r); from envscrub import is_sensitive; "
            "print(sum(is_sensitive(n) for n in os.environ))" % os.path.dirname(os.path.dirname(__file__)))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "0"
