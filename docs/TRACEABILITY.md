# Requirements → implementation → tests

Status legend: **Done** (implemented and covered by passing tests), **Partial** (some
acceptance criteria open; listed), **Blocked** (needs an external decision or resource),
**Open** (not implemented). Test counts are from a local run on 2026-11-19 (Python
3.12.13): `374 passed, 4 deselected (isolation)`; the 4 isolation tests run only in the
container (`entrypoint.sh gate-isolation`) and are validated in CI, not locally.

Priority tiers used in the integration report: **P0** security/custody gate
(core 1–11, 15), **P1** HTTP API + MCP (core 12–14), **P2** application logic (quote,
reel evaluators), **P3** UIs and demo fixtures.

## VerdictKit core (`.kiro/specs/verdictkit-core`)

| Req | Implementation | Tests | Status |
|---|---|---|---|
| 1 Canonical freezing, spec hash | `canonical.py`, `custody/intake.py` | `contract/test_canonical.py`, `test_blinding.py` (P1, P5) | Done |
| 2 Partition and blinding | `custody/intake.py::blind`, `examiner/protocol.py` | `test_blinding.py` (P2, P3) | Done |
| 3 Commitment and sealed outcomes | `custody/commitment.py`, `custody/vault.py`, `api/draft_store.py` (AES-GCM, 0700) | `test_commitment.py` (P4), `api/test_m3b_draft_store.py` | Done |
| 4.1–4.4 Examiner isolation | `examiner/{worker,client,identity}.py`, `deploy/entrypoint.sh` | `test_isolation.py` (container), `test_examiner_attestation.py`, `api/test_m3b_examiner_identity.py` | Done (container part CI-verified) |
| 4.5 UNENFORCED stamping | ledger/bundle manifest/API `isolationMode` | `api/test_m3a_transport.py`, `api/test_http_run_lifecycle.py` | Done |
| 4.6–4.7 Judge-mode startup contract | `api/check_startup.py`, `api/__main__.py` | `api/test_startup_gate.py`, `entrypoint gate-startup` | Done |
| 5.1–5.5 Evidence provenance/policy | `evidence/{store,policy,broker}.py` | `test_evidence.py` (P8, P9) | Done |
| 5.6–5.7 Data mode / rights gate | `evidence/policy.py::effective_policy`, `api/evidence_boundary.py` | `test_presenter.py`, `api/test_m3b_evidence_boundary.py` | Done |
| 6 Verdict model | `model.py` | `test_verdict_model.py` (P12) | Done |
| 7 Assumptions and sweep | `sweep.py` | `test_sweep.py` (P11) | Done |
| 8 Ledger | `custody/ledger.py` | `test_ledger.py` (P6, P7) | Done |
| 9.1, 9.5 Deterministic bundles | `bundle.py::write_bundle` | `test_bundle_replay.py` (P10) | Done |
| 9.2 Licence-aware embedding | `bundle.py` (embeds REDISTRIBUTABLE/DOCUMENT/USER_SUPPLIED; was a no-op before this pass) | `integration/test_bundle_evidence_and_golden.py` | Done |
| 9.3–9.4 Offline replay statuses | `bundle.py::replay_bundle` (spec-hash check, zip limits, UNVERIFIABLE on malformed input, hash-checked evidence cache) | `test_bundle_replay.py`, `integration/test_bundle_evidence_and_golden.py`, `api/test_http_run_lifecycle.py` | Done (`--allow-refetch` has no fetcher: absent REFETCH_ONLY evidence stays UNVERIFIABLE) |
| 10 Plugin API, stub type, post-reveal diagnostics | `plugin.py`, `examples/stub_claimtype/`, `custody/comparator.py` | `test_bundle_replay.py`, golden bundle replay | Done |
| 11 Determinism, LLM fence | Decimal everywhere; `tests/contract/test_llm_fence.py` | 55 fence tests | Done |
| 12.1 MCP tools | `mcp_server.py` (MCP SDK 2.3 `MCPServer`, stdio) | `contract/test_mcp_server.py`; stdio client smoke test | Done |
| 12.2 Judge-mode limits | `api/server.py` (rate limit, 256 KiB / 8 MiB caps, TTL purge incl. frozen cases in judge mode) | `api/test_m3a_transport.py`, `api/test_http_run_lifecycle.py` | Done |
| 12.3 No free text in frozen schemas; transient paste | `api/intake_boundary.py`, `reel_autopsy.claim_type.extract_text` | `api/test_http_run_lifecycle.py` (paste tests) | Done |
| 13.1 Routes per OpenAPI; responses validate | `api/server.py`, `api/run_service.py` | every response in `api/test_http_run_lifecycle.py` validated against `api/openapi.yaml` | Done |
| 13.2–13.4 Execution status, confidence, key records | `api/presenter.py`, `api/run_service.py` | `test_presenter.py`, lifecycle tests | Done |
| 13.5 Write-then-emit progress events | `api/run_service.py::execute_run`, SSE reads only the persisted record | lifecycle test (SSE, `Last-Event-ID`) | Done |
| 13.6 Integrity ≠ reproducibility ≠ authenticity | `bundle.py::integrity_dict/replay_report_dict` | metadata + replay schema checks | Done |
| 14 CLI | `cli.py` | gate (`gate-case`, replay), golden bundle | Done |

## Quote Autopsy (`.kiro/specs/quote-autopsy`)

| Req | Status | Notes |
|---|---|---|
| 1 Finance schema | Partial | Implemented field set differs from 1.1–1.2 (outcome names without `stated_` prefix; term 1–120); 1.3 "unknown" taxability flags swept over {true,false} is **Open**. |
| 2 Lease schema | Partial | Implemented lease params are the reduced set (`adjusted_cap_cost`, `residual_value`, …), not 2.1's itemised `msrp`/`capitalized_items`/`cap_cost_reductions`. |
| 3 Finance arithmetic | Done (3.1–3.5), Partial (3.6 CONDITIONAL needs 1.3 sweeps) | P16, P16b, P17b in `test_quote_contract.py`; P16b also in `integration/test_quote_rules_diagnostics.py` |
| 4 Lease arithmetic | Done (4.1–4.2 math, P17); 4.3 convention sweep **Open** (convention is a fixed parameter) | |
| 5.1 Rules snapshot | Partial | Hash-verified loader done (`rules.py`, 11 tests). **Blocked**: no official snapshot — decision B7 (which state) is open. |
| 5.2–5.5 External findings | Blocked | External fields report INDETERMINATE(`evidence_unavailable`) until a snapshot exists. |
| 6 Diagnostics | Done | `diagnostics.py`, wired through `FinanceClaimType.diagnose`; P17c test. Lease has no diagnostics. |

## Reel Autopsy (`.kiro/specs/reel-autopsy`)

| Item | Status | Notes |
|---|---|---|
| Bars, strategies, simulator, metrics, bound (tasks 1–4) | Done | `test_reel_contract.py` (P13–P15b) |
| 5.0 Licensed OHLCV source | Blocked | Needs a documented rights basis (decision B1). |
| 5 Evidence adapter | Blocked | Depends on 5.0. Staging tooling exists (`scripts/reel_ohlcv_acquire.py`, `tests/reel_evidence`). |
| 6 Claim type | Partial | Fail-closed scaffold: validates params/outcomes and returns INDETERMINATE(`evidence_unavailable`); evaluator not wired to evidence. |
| 8 Synthetic demo fixtures (`SYNTHETIC_DEMO`) | Open | Intake refuses `SYNTHETIC_DEMO` until a trusted fixture loader and a synthetic evidence path through the isolated worker exist. |
| 9 Intake text and presentation | Done | `test_reel_intake_presentation.py`; now connected to HTTP intake. |

## UIs

| Item | Status |
|---|---|
| Read-only judge preview (`ui/judge`, `scripts/serve_judge_ui.py`) | Done (`tests/ui`) |
| React/Vite apps (`apps/*/web`, `ui-kit/`) | Open |
