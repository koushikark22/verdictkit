"""Strict startup gate regression contract."""
import os
import subprocess
import sys

import pytest

from verdictkit.api.check_startup import (
    IsolationNotEnforcedError,
    StartupConfigurationError,
    startup_checks,
)


def check_with_env(values):
    env = dict(os.environ)
    env.update(values)
    return subprocess.run(
        [sys.executable, "-m", "verdictkit.api", "--check-startup"],
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
    )


def test_reject_invalid_judge_mode(monkeypatch):
    monkeypatch.setenv("VK_JUDGE_MODE", "banana")
    with pytest.raises(StartupConfigurationError):
        startup_checks()


def test_reject_environment_spoof(monkeypatch):
    monkeypatch.setenv("VK_JUDGE_MODE", "1")
    monkeypatch.setenv("VK_ISOLATION", "enforced")
    monkeypatch.setenv("VK_EXAMINER_SOCKET", "/nonexistent/vk.sock")
    with pytest.raises(IsolationNotEnforcedError):
        startup_checks()


def test_invalid_mode_has_specific_error_contract():
    p = check_with_env({"VK_JUDGE_MODE": "banana"})
    assert p.returncode == 2
    assert "VK_STARTUP_ERROR=INVALID_JUDGE_MODE" in p.stderr


def test_enforced_request_refused_without_real_isolation():
    p = check_with_env({
        "VK_JUDGE_MODE": "1",
        "VK_ISOLATION": "enforced",
        "VK_EXAMINER_SOCKET": "/nonexistent/vk.sock",
    })
    assert p.returncode == 3
    assert "VK_STARTUP_ERROR=ISOLATION_NOT_ENFORCED" in p.stderr
