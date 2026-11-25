# Execution evidence ledger

Append-only in intent. Each entry records an actual run. Failures stay after a later successful rerun. The corrections made after independent review are listed at the end of this file with the original text, so no correction is silent. Raw output for baseline entries is in `docs/next-phase/baseline/logs/`. The canonical mapping from raw records to entries is `docs/next-phase/baseline/EXECUTION_INDEX.md`.

Commit for all entries below: `84df25c68198e496889b5892a03555ec7d2d860a` on `feature/kiro-next-phase`. Host: Windows (PowerShell), Docker Desktop Linux engine for container entries. Times are UTC start times.

## Baseline_Run (2026-11-24)

| Record | Step | Command | Exit | Seconds | Start (UTC) | Counts | Class |
|---|---|---|---|---|---|---|---|
| E-001 | Lock check | `uv lock --check` | 0 | 0.1 | 16:39:06 | n/a | SUCCEEDED |
| E-002 | Sync | `uv sync --frozen --all-packages --all-extras --group dev` | 0 | 0.1 | 16:36:09 | n/a | SUCCEEDED |
| E-003 | Ruff | `uv run --no-sync ruff check .` | 0 | 0.1 | 16:39:06 | n/a | SUCCEEDED |
| E-004 | Full regression | `uv run --no-sync pytest -q -p no:cacheprovider -m "not isolation" -rfEs` with `HYPOTHESIS_PROFILE=ci` | 1 | 71.4 | 16:36:13 | 444 passed, 2 failed, 5 skipped, 4 deselected | FAILED |
| E-005 | Judge preview rerun | `pytest tests/ui/test_judge_preview.py` | 1 | 4.7 | 16:37:41 | 7 passed, 1 failed | FAILED |
| E-006 | Contract suite | `pytest tests/contract -m "not isolation"` | 1 | 27.1 | 16:39:06 | 259 passed, 1 failed, 4 deselected | FAILED |
| E-007 | API safety | nine `tests/api` files (see baseline report) | 0 | 8.6 | 16:39:33 | 63 passed, 5 skipped | SUCCEEDED |
| E-008 | Startup and attestation | `tests/api/test_startup_gate.py tests/contract/test_examiner_attestation.py` | 0 | 3.8 | 16:39:42 | 16 passed | SUCCEEDED |
| E-009 | MCP tests | `... -k mcp` | 1 | 5.4 | 16:39:46 | 13 passed, 1 failed, 13 deselected | FAILED |
| E-010 | LLM fence | `tests/contract/test_llm_fence.py` | 0 | 2.6 | 16:39:51 | 58 passed | SUCCEEDED |
| E-011 | Isolation collection | `pytest -m isolation --collect-only` | 0 | 5.8 | 16:39:54 | 4 collected | SUCCEEDED |
| E-012 | Hook cmd core | Hook_Set core command | 1 | 12.4 | 16:40:14 | 159 passed, 1 failed | FAILED |
| E-013 | Hook cmd reel | Hook_Set reel command | 0 | 13.2 | 16:40:26 | 13 passed | SUCCEEDED |
| E-014 | Hook cmd quote | Hook_Set quote command | 0 | 3.9 | 16:40:45 | 8 passed | SUCCEEDED |
| E-015 | UI install | `npm ci` | 0 | 13.1 | 16:41:19 | n/a | SUCCEEDED |
| E-016 | UI typecheck | `npm run typecheck` | 0 | 6.9 | 16:41:35 | n/a | SUCCEEDED |
| E-017 | UI tests | `npm test` | 0 | 10.3 | 16:41:46 | 19 passed | SUCCEEDED |
| E-018 | UI build | `npm run build` | 0 | 10.0 | 16:42:00 | n/a | SUCCEEDED |
| E-019 | Docker build | `docker build -t verdictkit:next-baseline .` | 0 | 25.1 | 16:42:45 | n/a | SUCCEEDED |
| E-020 | gate-isolation | `docker run --rm --network none -v <gate>:/out verdictkit:next-baseline gate-isolation /out/isolation.xml` | 0 | 2.6 | 16:43:15 | 4 passed | SUCCEEDED |
| E-021 | gate-startup | `docker run --rm --network none verdictkit:next-baseline gate-startup` | 0 | 0.8 | 16:43:22 | marker `VK_STARTUP_OK isolation=ENFORCED` | SUCCEEDED |
| E-022 | gate-http | `docker run --rm --network none verdictkit:next-baseline gate-http` | 0 | 2.6 | 16:43:26 | "GATE-HTTP PASSED" | SUCCEEDED |
| E-023 | gate-case | `docker run --rm --network none ... gate-case /in/claim.json /out/stub.vkb` | 0 | 1.0 | 16:43:34 | bundle written | SUCCEEDED |
| E-024 | Offline replay | `docker run --rm --network none ... verdictkit replay /out/stub.vkb` | 0 | 0.8 | 16:43:40 | `REPRODUCED`, hash `547fba0c...aaa79` | SUCCEEDED |
| E-025a | MCP tests in Linux image | `.venv/bin/pytest tests/contract/test_mcp_server.py tests/ui/test_judge_preview.py` in `verdictkit:next-baseline` (combined run, index R27) | pytest exit code not captured | 3.8 | 16:44:07 | no `test_mcp_server.py` test in the failure list; no per-test listing | UNVERIFIED (indirect evidence only) |
| E-025b | Judge-preview tests in Linux image | same run as E-025a | pytest exit code not captured | 3.8 | 16:44:07 | 4 failed (named): `test_js_and_css`, `test_main_html`, `test_no_external_assets`, `test_separate_app_files`; cause `FileNotFoundError` because `ui/` is not in the image | FAILED (environment invalid: `ui/` absent) |
| E-026 | Playwright install | `npm install --no-save playwright@1.63.0` | 0 | 4.8 | 16:44:36 | n/a | SUCCEEDED |
| E-027 | Browser E2E | `scripts/ui_e2e.sh` | not run | n/a | n/a | port 8000 held by `splunkd.exe`; Linux-only script | UNVERIFIED |
| E-028 | `gate_nov22.sh` | not run | n/a | n/a | n/a | n/a | UNVERIFIED |

E-025a and E-025b come from one combined run. The pytest summary was `4 failed, 10 passed`. The combined total of 14 and the split of the 10 passes between the two files were not recorded. The recorded `exit` in `records.jsonl` (0) is the exit code of `tail` and is not used as a result. Two earlier attempts (R25 and R26) did not run pytest and are execution errors.

## Historical evidence reconciliation (read-only, 2026-11-24)

| Record | Item | Result |
|---|---|---|
| E-100 | Recompute credits, request ids, tool calls, sub-agents, sessions | CONFIRMED, see `HISTORICAL_EVIDENCE_RECONCILIATION.md` H1 to H5 |
| E-101 | MCP tool usage from Kiro | CONFIRMED (23 calls), H6 |
| E-102 | Claim types exercised | CONFIRMED_WITH_CORRECTION, H7 |
| E-103 | Hook load and execution | Hooks registered 4 of 4; execution disabled in untrusted workspace; no execution observed. Execution UNVERIFIED, H8 |

## Kiro usage for this phase

| Item | Value |
|---|---|
| Credits consumed in this phase | NOT_AVAILABLE |
| Kiro features observed running inside Kiro in this session | spec workflow sub-agents (requirements, requirement-detailer) were invoked from this session; no Kiro-side usage record was read |

### Separately observed usage evidence (maintainer-reported, recorded 2026-11-24)

These entries were reported by the maintainer when D3 was conditionally approved. The agent did not read them from a Kiro usage record, so they are not Credit_Records (Requirement 16.1). They are kept apart from the Historical_Audit total (16.4). The table above is unchanged.

| Record | Item | Value | Unit | Session identifier | Date | Status |
|---|---|---|---|---|---|---|
| U-001 | Additional credits | 94.1594 | credit (as reported) | NOT_AVAILABLE | NOT_AVAILABLE | OBSERVED_SEPARATELY. Not deduplicated. Not attributed. |
| U-002 | Additional request identifiers | 197 | count | NOT_AVAILABLE | NOT_AVAILABLE | OBSERVED_SEPARATELY. Not deduplicated. Not attributed. |
| U-003 | Deduplication against the 318 Historical_Audit request identifiers | NOT_PERFORMED | n/a | n/a | n/a | The identifier values were not supplied, so any overlap is unknown. |
| U-004 | Combined total with the Historical_Audit (92.9518 credits, 318 request identifiers) | NOT_COMPUTED | n/a | n/a | n/a | Needs U-003. No sum is stated. |
| U-005 | Usage of the current turn | NOT_AVAILABLE | n/a | n/a | n/a | No usage record was read (16.2). |

The deduplication key is the request identifier. A credit figure that belongs to a duplicate identifier is counted once. The figures are not attributed to a track, to hooks or to D3 (16.3), and no cost per task, test or requirement is derived from them (16.5).

## Phase_Branch pushes and remote ref check (Requirement 14.13)

PUSH-001 to PUSH-003 record every push of the Phase_Branch that the local reflog of the remote-tracking ref shows (`update by push` entries, remote `origin`). The local reflogs of all other remote-tracking refs show no push. A row is an observation of a ref update and not a command execution: the original push command text and exit code were not captured in this ledger, so both are NOT_AVAILABLE and the row carries no Outcome_Class. The time is the reflog timestamp converted to UTC. It is the time at which the local tracking ref was updated after the push, and it is not a server timestamp.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-001 | `refs/heads/feature/kiro-next-phase` | none (the reflog old value is the all-zero id, so the ref was created) | `c29d2fee95cd0cbc0d59e89111b0d80af1b19d8a` | 2026-11-25 04:31:16 | Not stated in this record. UNVERIFIED. |
| PUSH-002 | `refs/heads/feature/kiro-next-phase` | `c29d2fee95cd0cbc0d59e89111b0d80af1b19d8a` | `1cb3e481439cf31d2a7ba45a1b98129e095a02fd` | 2026-11-25 20:06:03 | Not stated in this record. UNVERIFIED. |
| PUSH-003 | `refs/heads/feature/kiro-next-phase` | `1cb3e481439cf31d2a7ba45a1b98129e095a02fd` | `aea7d06d11cf32f9f5abba7cbd3f33a3472c935a` | 2026-11-25 21:38:28 | Stated by the repository owner as authorized, in the request of 2026-11-25 that asked for this record. The text of the original authorization is not stored in this repository. |

A push of the commit that contains this section is recorded by the first ledger update after it, because a commit cannot contain its own id.

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| E-200 | Remote ref check | `git ls-remote origin refs/heads/feature/kiro-next-phase refs/heads/master refs/tags/v1.0.0-submission refs/tags/v1.0.0-submission^{} refs/tags/verified-quote-e2e-20261118` | repository root | `aea7d06d11cf32f9f5abba7cbd3f33a3472c935a` | Windows (PowerShell) | 2026-11-25 23:39:11 | 1.1 | 0 | 2026-11-25 23:39:13 | SUCCEEDED |

E-200 output, in full (5 lines, no pipe, exit code read directly). Execution_Index id: not applicable, because the index covers the baseline run only.

```text
aea7d06d11cf32f9f5abba7cbd3f33a3472c935a  refs/heads/feature/kiro-next-phase
84df25c68198e496889b5892a03555ec7d2d860a  refs/heads/master
e9ca8d2bac4a65483f3a7357e00600a1210a6f4f  refs/tags/v1.0.0-submission
84df25c68198e496889b5892a03555ec7d2d860a  refs/tags/v1.0.0-submission^{}
407478be97a8979a8e3555bba3b3ab302229f91d  refs/tags/verified-quote-e2e-20261118
```

Reading. The Phase_Branch value equals the After value of PUSH-003. The four Frozen_Release values equal those of Requirement 1.2 (tag object, peeled commit, `master`, `verified-quote-e2e-20261118`). This is a check at the time of the record. The end-of-phase check of 14.14 is task PH7-15.
## Capability register

| Capability | Status |
|---|---|
| Frozen release refs unchanged | SUCCEEDED (checked at start; recheck at end required by Requirement 14.14) |
| Hook execution inside Kiro | UNVERIFIED |
| Kiro MCP calls | SUCCEEDED in the historical record (E-101); not repeated in this phase |
| Browser E2E | UNVERIFIED |
| Public demonstration | UNVERIFIED (none exists) |
| Signed bundles, plugin SDK, regulatory expansion | not implemented |
## Corrections log (after independent review)

| ID | Item | Original text | Correction | Reason |
|---|---|---|---|---|
| C-001 | `BASELINE_REPORT.md` section 1 | Tag `verified-quote-e2e-20261118` resolves to `84df25c...` | Resolves to `407478be97a8979a8e3555bba3b3ab302229f91d` (lightweight tag, ancestor of `84df25c`) | The first check inspected only the first tag. Verified with `git rev-parse` and `git merge-base --is-ancestor`. |
| C-002 | E-025 | `PARTIAL`; exit `0 (of tail; pytest result in log)`; "10 passed, 4 failed" attributed to the MCP file and the preview file together | Split into E-025a (UNVERIFIED) and E-025b (FAILED, invalid environment). Exit recorded as not captured. | `PARTIAL` is not a defined Outcome_Class. An exit code must not be inferred from `tail`. |
| C-003 | E-014 | 4.1 s, start 16:40:26 | 3.9 s, start 16:40:45 | The surviving log (`8 passed in 2.11s`) was written by the later execution. See the index. |
| C-004 | Records | Duplicate and lock-collision rows described as noise | 5 execution-error records classified as EXECUTION_ERROR, not test failures, and excluded from pass or fail counts | Maintainer decision A.5. See `EXECUTION_INDEX.md`. |
| C-005 | Baseline defects | Pre_Existing_Defect, awaiting acceptance | BE-1 accepted (baseline continuation only). BE-2 provisionally accepted, cause not established. Both need remediation before the final release. | Maintainer decision B. |
| C-006 | Raw record files: `BASELINE_REPORT.md` header and `baseline/EXECUTION_INDEX.md` | "Raw command records: `docs/next-phase/baseline/records.jsonl`"; "Both raw files are preserved byte for byte" (read as published in the repository) | The original `records.jsonl` is a Private_Original kept outside the published tree. Its hash in the Execution_Index is unchanged. The published file is `baseline/records.sanitized.jsonl` with its own hash. `records-first-pass-overlapping.jsonl` is published unchanged. Method, rules and hashes: `EVIDENCE_REDACTION.md`. | Four command fields held local user-profile paths. Requirements 1.14, 3.11 and 3.14. |
| C-007 | Ledger rows E-009, E-012, E-013, E-014, E-020, E-023, E-024 | Command text abbreviated (`...`, `<gate>`, "Hook_Set command") | Text left unchanged. The exact command and the Execution_Index record id of every baseline row are in `baseline/LEDGER_COMMAND_RECONCILIATION.md`. Seconds and start times of all rows equal the canonical records (0 mismatches). | Independent review finding L-4. Requirement 3.12. |
| C-008 | BE-2 host attribution in the ledger and the baseline report ("Windows") | BE-2 recorded as a Windows exception | Read as "observed on Windows". Attribution to the host is UNVERIFIED and the root cause is not established until a Linux per-test run from a full checkout exists. | Requirements 1.12 and 1.19. Independent review finding L-4. |

## Accepted baseline exceptions

| ID | Defect | Host | Remediation required before final release |
|---|---|---|---|
| BE-1 | `tests/contract/test_mcp_server.py::test_verify_replay_and_explain_roundtrip` asserts POSIX mode `0o700` | Windows | Preserve the Linux permission assertion. Design Windows-appropriate security handling (for example an access-control check). Do not remove the assertion. |
| BE-2 | `tests/ui/test_judge_preview.py::JudgePreviewTests::test_case_outcome_get_to_offline_backend` times out | Windows | Instrument, establish the root cause, fix the cause. A longer timeout alone is not a fix. |
