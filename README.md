# VerdictKit — The Claim Autopsy Engine

A reusable forensic verification framework: freeze a claim, seal the claimed answer away
from the evaluator, examine it blind on policy-checked evidence across a bounded
assumption grid, and emit a reproducible verdict bundle.

Two applications on one core:

* `apps/reel-autopsy` — mechanical trading-strategy performance claims
* `apps/quote-autopsy` — vehicle finance and lease worksheets

Status (2026-11-19): the core custody pipeline, CLI, MCP server and the full HTTP API
(contract 1.1.0: intake → freeze → evidence → run → outcome → bundle → replay) are
implemented and tested. Quote Autopsy runs document-internal arithmetic with post-reveal
diagnostics; external tax/fee checks await an official state snapshot (decision B7). Reel
Autopsy is fail-closed (BLOCKED / INDETERMINATE) until a licensed OHLCV source exists
(decision B1). Per-requirement status: `docs/TRACEABILITY.md`.

Quick start:

```bash
uv sync --frozen --all-packages --all-extras --group dev
HYPOTHESIS_PROFILE=ci uv run --no-sync pytest -q -m "not isolation"
uv run --no-sync verdictkit replay examples/stub_claimtype/golden.vkb
```

Enforced isolation (two OS users, authenticated examiner socket) exists only in the
container: `docker build -t verdictkit . && docker run --rm --network none verdictkit gate-http`.
The full gate is `scripts/gate_nov22.sh` (Linux with Docker).

* Architecture and decision log: `docs/ARCHITECTURE.md`
* Specs: `.kiro/specs/{verdictkit-core,reel-autopsy,quote-autopsy}/`
* Contract tests: `uv run pytest tests/contract -q`
* API: `docs/API_CONTRACT.md`, `api/openapi.yaml`; MCP: `python -m verdictkit.mcp_server`
