# VerdictKit — The Claim Autopsy Engine

A reusable forensic verification framework: freeze a claim, seal the claimed answer away
from the evaluator, examine it blind on policy-checked evidence across a bounded
assumption grid, and emit a reproducible verdict bundle.

Two applications on one core (Kiroween 2026 — Skeleton Crew):

* `apps/reel-autopsy` — mechanical trading-strategy performance claims
* `apps/quote-autopsy` — vehicle finance and lease worksheets

Status: architecture, specs, interfaces and contract tests (API contract 1.1.0).
The contract-test baseline is a **starting state, not a passing implementation**: most
tests fail with `NotImplementedError` until Kiro implements the stubs. The Nov 22 gate
(`scripts/gate_nov22.sh`) is not executable until `uv.lock`, the `Dockerfile` and the core
implementation exist; the script checks this and exits 2 otherwise.
Implementation proceeds through Kiro (see `docs/KIRO_SESSION_CORE.md`).

* Architecture and decision log: `docs/ARCHITECTURE.md`
* Specs: `.kiro/specs/{verdictkit-core,reel-autopsy,quote-autopsy}/`
* Contract tests: `uv run pytest tests/contract -q`
