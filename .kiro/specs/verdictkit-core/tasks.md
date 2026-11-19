# Implementation Plan — VerdictKit Core

Target gate: **Nov 22 — stub-claim bundle replays to `REPRODUCED` offline; P1–P12 pass.**
Contract tests already exist in `tests/contract/`; each task is done when its listed
contract tests pass in addition to Kiro-generated property tests.

- [ ] 1. Project skeleton
  - [ ] 1.1 `uv` workspace (core, apps/*), Python 3.12 pin, lockfile, Ruff, pytest + Hypothesis profiles (`ci`: derandomize)
  - [ ] 1.2 CI: unit + contract tests, LLM fence, lockfile check
  - [ ] 1.3 Generate and commit `uv.lock` (`uv lock`); CI uses `uv sync --frozen`. Gate prerequisite.
  - _Requirements: 11.3_

- [ ] 2. Canonical JSON and hashing (`canonical.py`)
  - [ ] 2.1 Implement `canonical_bytes`, `parse_canonical`, `sha256_hex`; reject float/NaN/dup keys
  - [ ] 2.2 Property tests P1 — contract: `test_canonical.py`
  - _Requirements: 1.2, 1.3_

- [ ] 3. Model and verdict matrix (`model.py`)
  - [ ] 3.1 Implement `validate_finding`, `headline_status`, `compute_verdict_hash`
  - [ ] 3.2 Property tests P12 — contract: `test_verdict_model.py`
  - _Requirements: 6.1–6.5_

- [ ] 4. Intake, partition and spec hash (`custody/intake.py`, `plugin.py`)
  - [ ] 4.1 Registry; `freeze()` validates schemas and partitions params/outcomes
  - [ ] 4.2 `blind()` builds `BlindedTask` from `FrozenClaim` only
  - [ ] 4.3 Property tests P2, P3, P5 — contract: `test_blinding.py`
  - _Requirements: 1.1, 1.4–1.6, 2.1–2.4_

- [ ] 5. Commitment and vault (`custody/commitment.py`, `custody/vault.py`)
  - [ ] 5.1 Commitment with domain tag + 32-byte salt
  - [ ] 5.2 AES-GCM vault, key from `VK_VAULT_KEY`, dir mode check at startup
  - [ ] 5.3 Property tests P4 — contract: `test_commitment.py`
  - _Requirements: 3.1–3.4_

- [ ] 6. Ledger (`custody/ledger.py`)
  - [ ] 6.1 Hash chain, state machine, `verify()`
  - [ ] 6.2 Property tests P6, P7 — contract: `test_ledger.py`
  - _Requirements: 8.1–8.4_

- [ ] 7. Sweep engine (`sweep.py`)
  - [ ] 7.1 `expand_grid` with cap, deterministic order, missing-assumption handling
  - [ ] 7.2 `aggregate` with counterexample selection (first fail, first pass, worst margin)
  - [ ] 7.3 Property tests P11 — contract: `test_sweep.py`
  - _Requirements: 7.1–7.7_

- [ ] 8. Evidence (`evidence/`)
  - [ ] 8.1 Content-addressed store with hash-on-read
  - [ ] 8.2 Policy (permitted sources, forbidden classes) and broker adapter interface
  - [ ] 8.3 Property tests P8, P9 — contract: `test_evidence.py`
  - _Requirements: 5.1–5.5_

- [ ] 9. Examiner process (`examiner/`)
  - [ ] 9.1 Protocol codec with 8 MiB cap
  - [ ] 9.2 Worker main (unix socket), resource limits, scrubbed env
  - [ ] 9.3 Client with timeout; `isolation_mode` detection
  - [ ] 9.4 Container isolation test (`-m isolation`)
  - _Requirements: 4.1–4.6_

- [ ] 10. Comparator, pipeline, diagnostics (`custody/comparator.py`, `pipeline.py`)
  - [ ] 10.1 Reveal → verify commitment → plugin `findings()` → verdict
  - [ ] 10.2 Diagnostics only after `VERDICT_SEALED`, excluded from verdict hash
  - _Requirements: 3.3, 6.4, 10.4_

- [ ] 11. Bundles and replay (`bundle.py`, `envprint.py`)
  - [ ] 11.1 Deterministic zip writer with license-aware evidence embedding
  - [ ] 11.2 Replay with statuses, no network by default
  - [ ] 11.3 Property tests P10 — contract: `test_bundle_replay.py`
  - _Requirements: 9.1–9.5_

  - [ ] 11.4 CLI `run` / `replay` (`cli.py`)
  - _Requirements: 14.1, 14.2_

- [ ] 12. Stub third claim type (`core/examples/stub_claimtype/`)
  - [ ] 12.1 "Receipt total" claim: line items → total; runs end-to-end with no core change
  - [ ] 12.2 Golden bundle committed for CI replay
  - _Requirements: 10.3_

- [ ] 13. CHECKPOINT Nov 22 — run `scripts/gate_nov22.sh`; commit `gate/` transcript
  - [ ] 13.1 Presentation adapter (`api/presenter.py`), `effective_policy` — contract: `test_presenter.py`
  - [ ] 13.3 `specimen_dto`, `sensitivity_dto`, `CONTRACT_VERSION` on every response — contract: `test_presenter.py`, `test_api_schema.py`
  - [ ] 13.2 Startup isolation gate: `python -m verdictkit.api --check-startup` exits non-zero when `VK_JUDGE_MODE=1` and isolation is not ENFORCED
  - Gate requires: core contract tests green (except app-owned files), container isolation tests green, enforced-mode stub run, offline replay `REPRODUCED`
  - _Requirements: 4, 5.6, 9, 13.2–13.4_

- [ ] 14. API, judge mode, MCP (`api/`, `mcp_server.py`)
  - [ ] 14.1 FastAPI routes exactly per `api/openapi.yaml`; run records + SSE (write-then-emit); judge-mode limits; isolation gate — contract: `test_api_schema.py` + response validation
  - [ ] 14.2 MCP server tools; register in `.kiro/settings/mcp.json`
  - _Requirements: 12.1–12.3, 4.6_

- [ ] 15. Container
  - [ ] 15.1 `Dockerfile` at repo root (pinned Python 3.12 base by digest, `uv sync --frozen`), entrypoint creating `vk-custodian`/`vk-examiner`, vault 0700, `setpriv` exec, no root process left. Gate prerequisite.
  - [ ] 15.2 Run `-m isolation` tests in the image in CI
  - [ ] 15.3 Entrypoint subcommands used by the gate: `serve`, `gate-isolation` (creates `vault/probe.sealed` as vk-custodian, then runs `pytest -m isolation` as vk-examiner), `gate-case <claim.json> <out.vkb>` (runs `verdictkit run` with the SocketExaminer, isolation ENFORCED), and pass-through `verdictkit ...`
  - _Requirements: 4.1–4.4_
