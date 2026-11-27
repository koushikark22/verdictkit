"""Static safety checks for the one-command start and stop scripts (Batch 2, priority 4).

These read the script text. They guard the promises made to the user: nothing unrelated is terminated, services bind to
loopback only, no environment is dumped, and the Windows script survives Windows PowerShell 5.1 (ASCII only).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PS_START = (ROOT / "scripts" / "Start-VerdictKit.ps1").read_text(encoding="utf-8")
PS_STOP = (ROOT / "scripts" / "Stop-VerdictKit.ps1").read_text(encoding="utf-8")
SH_START = (ROOT / "scripts" / "start-verdictkit.sh").read_text(encoding="utf-8")
SH_STOP = (ROOT / "scripts" / "stop-verdictkit.sh").read_text(encoding="utf-8")


def code_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if not ln.strip().startswith("#")]


def test_powershell_scripts_are_ascii_so_windows_powershell_5_reads_them_correctly():
    for name in ("Start-VerdictKit.ps1", "Stop-VerdictKit.ps1"):
        data = (ROOT / "scripts" / name).read_bytes()
        assert all(b < 128 for b in data), f"{name} has non-ASCII bytes"


def test_no_script_can_terminate_an_unrelated_process_or_container():
    for name, text in (("Start", PS_START), ("Stop", PS_STOP), ("start.sh", SH_START), ("stop.sh", SH_STOP)):
        body = "\n".join(code_lines(text))
        for forbidden in (r"taskkill", r"Stop-Process\s+-Name", r"Get-Process[^\n]*\|\s*Stop-Process", r"\bpkill\b", r"\bkillall\b",
                          r"kill\s+-9", r"docker\s+(kill|stop|system\s+prune|container\s+prune|rm\s+-f\s+\$\(|volume\s+rm)", r"Remove-Item\s+-Recurse[^\n]*\$env"):
            assert not re.search(forbidden, body, re.IGNORECASE), f"{name}: {forbidden}"


def test_a_stopped_process_must_be_this_repositorys_own_gateway():
    for text in (PS_START, PS_STOP):
        stop_sites = [ln for ln in code_lines(text) if re.search(r"Stop-Process", ln)]
        assert stop_sites, "scripts stop only through a guarded helper"
        assert "gateway.mjs" in text and "CommandLine" in text and "$Repo" in text
    for text in (SH_START, SH_STOP):
        assert 'grep -q "$REPO/scripts/gateway.mjs"' in text, "the pid is checked against this repository's gateway before kill"


def test_containers_are_only_removed_when_named_and_labelled_as_verdictkit_managed():
    assert "vk-batch2-backend" in PS_START and "com.verdictkit.managed=1" in PS_START
    assert "was not started by VerdictKit" in PS_START and "was not started by VerdictKit" in SH_START
    for text in (PS_STOP, SH_STOP):
        assert "label=com.verdictkit.managed=1" in text or "label=' + $ManagedLabel" in text or "'label=com.verdictkit.managed=1'" in text


def test_every_published_port_is_bound_to_loopback_only():
    assert "'-p', ('127.0.0.1:' + $api + ':8000')" in PS_START
    assert '-p "127.0.0.1:${API}:8000"' in SH_START
    for text in (PS_START, SH_START):
        assert "0.0.0.0:" not in text and "--publish-all" not in text and not re.search(r"docker[^\n]*\s-P\s", text)
    assert PS_START.count("'run', '-d'") == 1 and SH_START.count("docker run -d") == 1, "exactly one container is started"


def test_the_scripts_never_dump_the_environment_or_read_credential_files():
    for text in (PS_START, PS_STOP, SH_START, SH_STOP):
        body = "\n".join(code_lines(text))
        for forbidden in (r"Get-ChildItem\s+Env:", r"\bgci\s+env:", r"\bprintenv\b", r"^\s*env\s*$", r"\bset\s*$", r"\.aws", r"\.ssh", r"credentials", r"\.env\b", r"id_rsa"):
            assert not re.search(forbidden, body, re.IGNORECASE | re.MULTILINE), forbidden


def test_no_secret_is_created_or_printed_by_the_scripts():
    for text in (PS_START, SH_START):
        assert "VK_VAULT_KEY" not in text and "SIGNING_KEY" not in text and "PRIVATE KEY" not in text
        assert "BEGIN" not in text


def test_the_scripts_verify_health_and_refuse_to_continue_without_enforced_isolation():
    for text in (PS_START, SH_START):
        assert "ENFORCED" in text and "judge mode" in text and "1.2.0" in text
    assert "refusing to continue (container removed)" in PS_START and "refusing to continue (container removed)" in SH_START


def test_port_selection_never_frees_a_port_it_does_not_own():
    assert "Get-NetTCPConnection -State Listen" in PS_START and "Find-FreePort" in PS_START
    assert "find_port" in SH_START and "/dev/tcp/127.0.0.1" in SH_START


def test_the_gateway_is_started_without_redirecting_handles_so_a_callers_pipe_cannot_be_held_open():
    start = PS_START[PS_START.index("Start-Process"): PS_START.index("Start-Process") + 400]
    assert "-RedirectStandardOutput" not in start and "-RedirectStandardError" not in start
    assert "--log" in PS_START
