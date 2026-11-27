"""MCP server tools (core req 12.1, task 14.2)."""
from __future__ import annotations

import asyncio
import json
import sys
import zipfile
from pathlib import Path

import pytest

from verdictkit import mcp_server, safeio

ROOT = Path(__file__).resolve().parents[2]
STUB_CLAIM = json.loads((ROOT / "examples/stub_claimtype/claim.json").read_text())


def test_lists_registered_claim_types():
    types = {t["type_id"]: t for t in mcp_server.list_claim_types()}
    assert "example.receipt.v1" in types
    assert types["example.receipt.v1"]["outcome_fields"] == ["stated_total"]


def test_verify_replay_and_explain_roundtrip():
    result = mcp_server.verify_claim(STUB_CLAIM)
    assert "error" not in result, result
    assert result["isolation_mode"] == "UNENFORCED"
    bundle = Path(result["bundle_path"])
    assert bundle.is_file()
    assert bundle.parent == mcp_server._workdir()  # writes only in the private temp dir
    if sys.platform == "win32":
        # BE-1: POSIX mode bits carry no meaning on Windows. The equivalent check is an access
        # control check: only the current user, SYSTEM and Administrators may be granted access.
        assert safeio.is_private_dir(bundle.parent)
    else:
        assert oct(bundle.parent.stat().st_mode & 0o777) == "0o700"

    replay = mcp_server.replay_bundle(str(bundle))
    assert replay["integrity"]["status"] == "VERIFIED"
    assert replay["reproducibility"]["status"] in ("REPRODUCED", "REPRODUCED_ACROSS_ENV")

    explained = mcp_server.explain_verdict(str(bundle))
    assert explained["verdict_hash"] == result["verdict"]["verdict_hash"]
    assert "Verified at 1 grid point" in explained["summary"]
    assert "for all values" not in explained["summary"].replace("not a claim that it holds for all values", "")
    assert "NOT_ESTABLISHED" in explained["summary"]


def test_float_claims_and_garbage_are_refused():
    bad = json.loads(json.dumps(STUB_CLAIM))
    bad["params"]["items"] = [1.5]
    assert "error" in mcp_server.verify_claim(bad)
    assert "error" in mcp_server.verify_claim("not an object")  # type: ignore[arg-type]
    assert "error" in mcp_server.replay_bundle("/nonexistent/bundle.vkb")


def test_tampered_bundle_is_not_explained(tmp_path, monkeypatch):
    # Paths outside the private working directory need an operator-approved root (design DD8-5).
    monkeypatch.setenv("VK_MCP_BUNDLE_ROOTS", str(tmp_path))
    result = mcp_server.verify_claim(STUB_CLAIM)
    src = Path(result["bundle_path"])
    dst = tmp_path / "tampered.vkb"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name == "verdict/verdict.json":
                data = data.replace(b"CONTRADICTED", b"CONSISTENT")
                assert b"CONSISTENT" in data
            zout.writestr(name, data)
    explained = mcp_server.explain_verdict(str(dst))
    assert explained["integrity"]["status"] == "FAILED"
    assert "summary" not in explained


def test_readonly_refuses_refetch(monkeypatch):
    monkeypatch.setenv("VK_MCP_READONLY", "1")
    result = mcp_server.verify_claim(STUB_CLAIM)
    assert "error" not in result
    assert "error" in mcp_server.replay_bundle(result["bundle_path"], allow_refetch=True)


def test_sdk_registers_exactly_the_four_tools():
    pytest.importorskip("mcp")
    server = mcp_server.build_server()
    tools = asyncio.run(server.list_tools())
    assert sorted(t.name for t in tools) == [
        "explain_verdict", "list_claim_types", "replay_bundle", "verify_claim"]
