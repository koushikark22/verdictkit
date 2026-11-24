# Requirements → implementation → tests

Status legend: **Done** (implemented and covered by passing tests), **Partial** (some
acceptance criteria open; listed), **Blocked** (needs an external decision or resource),
**Open** (not implemented). Test counts are from a local run on 2026-11-20 (Python
3.12.13); see the final report for the exact totals; the 4 isolation tests run only in the
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
| 9.3–9.4 Offline replay statuses | `bundle.py::replay_bundle` (spec-hash check, zip limits, UNVERIFIABLE on malformed input including corrupt entries, hash-checked evidence cache) | `test_bundle_replay.py`, `integration/test_bundle_evidence_and_golden.py`, `api/test_http_run_lifecycle.py` (`test_corrupt_zip_entries_are_unverifiable_not_errors`) | Done (`--allow-refetch` has no fetcher: absent REFETCH_ONLY evidence stays UNVERIFIABLE) |
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

| Req | Status | Implementation / tests |
|---|---|---|
| 1 Finance schema | Partial | Implemented field set differs from 1.1–1.2 (finance outcome names have no `stated_` prefix; term 1–120 instead of 1–96). **1.3 Done**: an unshown taxability flag is `null` + a missing assumption of the same name, swept over {0,1} with origin DEFAULT_POLICY (`claim_type.py`; `integration/test_quote_sweeps.py`). |
| 2 Lease schema | Done | Itemised form per 2.1 (`msrp`, `selling_price`, `capitalized_items`, `cap_cost_reductions`, `residual_value` xor `residual_pct_of_msrp`, term 1–60, `stated_tax_rate_pct`, `jurisdiction`) with `stated_gross_cap_cost`, `stated_adjusted_cap_cost`, `stated_residual_value` outcomes; the reduced form remains accepted (`integration/test_quote_lease_itemised.py`, incl. a form-equivalence property). |
| 3 Finance arithmetic | Done | Tolerances per 3.6: 0.00 for sums and exact lines, 0.01 for payment-derived values. 3.1–3.5 (P16, P16b, P17b in `test_quote_contract.py`); 3.6 CONDITIONAL across swept flags with failing and passing points (property test against an independent per-point oracle); 3.7 conventions disclosed in the UI. A negative amount financed is now an intake rejection. `taxable_base` is floored at 0 per 3.1 (trade credit above price; pinned `@example` in `test_finance_chain_matches_oracle`). |
| 4 Lease arithmetic | Done | 4.1–4.2 (P17); **4.3** unconfirmed rounding convention swept over COMPONENT/FINAL; 4.4 APR ≈ MF × 2400 labelled a convention in the UI. |
| 5.1 Rules snapshot | Done | Hash-verified loader with `doc_fee` rule object; packaged Texas snapshot `rules/TX.json` + `MANIFEST.json`. `test_quote_rules_diagnostics.py`, `test_quote_b7_texas.py`. |
| 5.2–5.6 External findings | Done (TX only) | `TexasRulesAdapter` (`sources.py`) and `FinanceClaimType.findings`; non-TX and unavailable evidence stay INDETERMINATE; Texas lease `tax_rate` not applicable. `test_quote_b7_texas.py` (14 tests), `test_http_run_lifecycle.py`. |
| 6 Diagnostics | Done | Local checks + payment packing after VERDICT_SEALED (P17c). Not produced when flags are swept (needs a fully stated worksheet). |
| UI (task 7) | Done | `apps/quote-autopsy/web`: intake with "not shown on worksheet" options, progress, findings with point of failure / propagated, sensitivity, diagnostics, evidence, bundle download, metadata, replay. |
| Constructed examples (task 8) | Done | `apps/quote-autopsy/web/src/examples.json`, asserted by `integration/test_quote_constructed_examples.py`. |

## Reel Autopsy (`.kiro/specs/reel-autopsy`)

| Item | Status | Notes |
|---|---|---|
| Bars, strategies, simulator, metrics, bound (tasks 1–4) | Done | `test_reel_contract.py` (P13–P15b) |
| 5.0 Licensed OHLCV source | Blocked | Needs a documented rights basis (decision B1). Not claimed resolved. |
| 5 Evidence adapter | Partial | Synthetic adapter done (`sources/synthetic.py`: pinned SHA-256, network-free, class SYNTHETIC_FIXTURE). Live adapter blocked on B1; live instruments get no evidence request and stay INDETERMINATE/BLOCKED. |
| Req 1.4, 6.5 Assumptions | Done | `fee_bps_per_side` × `slippage_bps_per_side` × `position_fraction` default grid (16 points, DEFAULT_POLICY); declared values are CLAIMANT. |
| Req 1.5 1h span | Done | Rejected at intake when > 366 days. |
| Req 5.3 Gaps | Done | Missing bars ⇒ INDETERMINATE(`evidence_gap`), never interpolated. |
| Req 5.6 Synthetic fixtures | Done | `synthetic_ohlcv_v1.csv`, regenerated byte-for-byte by `generate()`, LF-pinned in `.gitattributes` so a `core.autocrlf=true` checkout keeps `PINNED_SHA256`; forbidden in LIVE_EVIDENCE by the core (`effective_policy` in pipeline, comparator, HTTP preflight and replay). |
| Req 6, 7 Findings and bound | Done | EXTERNAL_EVIDENCE per metric (SUPPORTED/REFUTED/CONDITIONAL); MECHANICAL_BOUND (`IMPOSSIBLE` when claim − tolerance > bound). |
| 8 SYNTHETIC_DEMO fixtures | Done | `fixtures.py` (3 fixtures, statuses computed by the engine and asserted in `integration/test_reel_synthetic_demo.py`, 18 tests). Container gate `gate-http` runs one through the authenticated isolated worker. |
| 9 Intake text and presentation | Done | `test_reel_intake_presentation.py`; connected to HTTP intake. |
| UI (task 7) | Done | `apps/reel-autopsy/web`: demos, claim intake (form or paste), progress, verdict, sensitivity heatmap, illustrative equity chart (an `EQUITY_SERIES` key record, role ILLUSTRATIVE — no schema change), evidence provenance, bound scope, bundle and replay. |

## Web UIs and verification

| Item | Status |
|---|---|
| Shared `ui-kit` (contract-checked client, SSE progress, components) | Done (`ui-kit/src/*.test.*`) |
| Browser E2E against a real API | Done (`scripts/ui_e2e.sh`, `tests/ui/e2e_browser.cjs`, 19 checks; CI job `web-ui`) |
| Lint | Done (ruff E9/F/B in the dev group and CI) |
| Read-only judge preview (`ui/judge`) | Done (`tests/ui`) |
