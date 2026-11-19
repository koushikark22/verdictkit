"""VerdictKit MCP server (stdio). Requirement: core 12.1.

Tools (all write only inside a per-call temporary directory):
  list_claim_types() -> [{type_id, schema_version, outcome_fields}]
  verify_claim(claim: object) -> {verdict, bundle_path, isolation_mode}
  replay_bundle(path: str, allow_refetch: bool = False) -> ReplayReport as JSON
  explain_verdict(path: str) -> plain-language summary built from findings (no LLM)
Uses the official Python MCP SDK. ``VK_MCP_READONLY=1`` disables verify_claim's network
evidence acquisition (fixtures and cached evidence only).
"""
from __future__ import annotations


def main() -> int:
    raise NotImplementedError("core task 14.2")


if __name__ == "__main__":
    raise SystemExit(main())
