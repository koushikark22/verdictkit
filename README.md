# VerdictKit — The Claim Autopsy Engine

A reusable forensic verification framework: freeze a claim, seal the claimed answer away
from the evaluator, examine it blind on policy-checked evidence across a bounded
assumption grid, and emit a reproducible verdict bundle.

Two applications on one core:

* `apps/reel-autopsy` — mechanical trading-strategy performance claims
* `apps/quote-autopsy` — vehicle finance and lease worksheets

Status (2026-11-20): the core custody pipeline, CLI, MCP server, the full HTTP API
(contract 1.1.0) and both web UIs are implemented and tested. Quote Autopsy runs
document-internal arithmetic, sweeps facts the worksheet does not show, and adds
post-reveal diagnostics; external tax-rate and doc-fee checks use a hash-pinned Texas rules snapshot
(decision B7 = TX). Reel Autopsy runs its full evaluator on labelled synthetic demo data;
real claims are fail-closed (BLOCKED) until a licensed OHLCV source exists (decision B1).
Per-requirement status: `docs/TRACEABILITY.md`.

Quick start:

```bash
uv sync --frozen --all-packages --all-extras --group dev
HYPOTHESIS_PROFILE=ci uv run --no-sync pytest -q -m "not isolation"
uv run --no-sync verdictkit replay examples/stub_claimtype/golden.vkb
```

Web UIs (real API, no mock verdicts): run the API with
`VK_DRAFT_DIR=/tmp/vk VK_VAULT_KEY=$(python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())') uv run --no-sync python -m verdictkit.api --port 8000`,
then `npm ci && npm run dev -w apps/quote-autopsy/web` (port 5173) or
`-w apps/reel-autopsy/web` (port 5174). Browser E2E: `bash scripts/ui_e2e.sh`.

Enforced isolation (two OS users, authenticated examiner socket) exists only in the
container: `docker build -t verdictkit . && docker run --rm --network none verdictkit gate-http`.
The full gate is `scripts/gate_nov22.sh` (Linux with Docker).

* Reproducible judge demonstration: `docs/JUDGE_DEMO.md`
* Submission preparation and authentic Kiro evidence: `docs/SUBMISSION_READINESS.md`
* Architecture and decision log: `docs/ARCHITECTURE.md`
* Specs: `.kiro/specs/{verdictkit-core,reel-autopsy,quote-autopsy}/`
* Contract tests: `uv run pytest tests/contract -q`
* API: `docs/API_CONTRACT.md`, `api/openapi.yaml`; MCP: `python -m verdictkit.mcp_server`
