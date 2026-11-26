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

## PH1-01 Start-of-phase preflight (Phase 1)

Task PH1-01 of the spec `verdictkit-next-phase` (requirements 1.1, 1.2, 1.3, 1.9 and 14.14). This section records the start-of-phase leg of VM-13 (Frozen_Release refs and Submission_Artifacts) and the tool versions. The task changes no code, test, script, configuration or lock file. The only repository file it writes is this ledger.

Records E-201 to E-222 are in execution order. Each record was written into this ledger in the same tool invocation as its command, right after the command finished (OD-D10-2), and the Recorded (UTC) column is the time of that write. Each command ran with the working directory at the repository root, without a pipe, and its exit code was read directly from the command. stdout and stderr are merged in capture order. No test runner ran, so no test count is entered (3.3). The SHA-256 value of an output is taken over the output text exactly as published (UTF-8, LF line endings, no trailing newline; for an empty output, the SHA-256 value of the empty string). The Commit column is the full 40-character HEAD at run time. Execution_Index id for every record in this section: not applicable, because the index covers the baseline run only.

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-201 | Working-tree state at phase start | `git status --porcelain` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:10:41 | 0.1 | 0 | 2026-11-26 00:10:41 | `965e106e6c0cb7e29b749e4844080fb15279ad8520568bc734d2b020ad0bbb16` | SUCCEEDED |

E-201 output, in full (3 lines; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class). This is the second run of this command in this task. The first run (start 2026-11-26 00:08:41, exit 0, the same 3 lines) is not recorded, because the recording step stopped before it wrote anything: a check in the scratch recording script stopped on the line endings of the existing ledger text. No ledger byte was changed by that stop. Only this run is used.

```text
 M .kiro/specs/verdictkit-next-phase/tasks.md
?? .kiro/specs/verdictkit-next-phase/.config.kiro
?? .kiro/specs/verdictkit-next-phase/tasks.meta.json
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-202 | Current branch | `git branch --show-current` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:11 | 0.1 | 0 | 2026-11-26 00:11:11 | `2e83dc36b78ad3f687176be6c438bde5cda263b30bdb50b2e064770a705c67ba` | SUCCEEDED |

E-202 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
feature/kiro-next-phase
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-203 | HEAD commit | `git rev-parse HEAD` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:11 | 0.1 | 0 | 2026-11-26 00:11:12 | `f7df4a98eb983b659ee5861be45b6f35b747a96ecb457100d5676fe576b350fe` | SUCCEEDED |

E-203 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
a7ab9ab1b79721998b2961c9c2ae955aa90b3598
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-204 | Baseline commit 84df25c resolved to its full id | `git rev-parse 84df25c` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `e9e5dd8726c44ad5535b42606991b23549ebab587d8c03662f5914f8df7e80c4` | SUCCEEDED |

E-204 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
84df25c68198e496889b5892a03555ec7d2d860a
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-205 | Frozen_Release: master | `git rev-parse refs/heads/master` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `e9e5dd8726c44ad5535b42606991b23549ebab587d8c03662f5914f8df7e80c4` | SUCCEEDED |

E-205 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
84df25c68198e496889b5892a03555ec7d2d860a
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-206 | Frozen_Release: tag object of v1.0.0-submission | `git rev-parse refs/tags/v1.0.0-submission` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.0 | 0 | 2026-11-26 00:11:12 | `64c6f698eb55faed179b9fc9adbe0b61eba80cbc712ca2b1601ae8f52ba6039e` | SUCCEEDED |

E-206 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
e9ca8d2bac4a65483f3a7357e00600a1210a6f4f
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-207 | Frozen_Release: peeled commit of v1.0.0-submission | `git rev-parse "refs/tags/v1.0.0-submission^{commit}"` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `e9e5dd8726c44ad5535b42606991b23549ebab587d8c03662f5914f8df7e80c4` | SUCCEEDED |

E-207 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
84df25c68198e496889b5892a03555ec7d2d860a
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-208 | Frozen_Release: verified-quote-e2e-20261118 | `git rev-parse refs/tags/verified-quote-e2e-20261118` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `0da3b6aa266adfa601f504dc96ad86b9720239780c608d21daac0899c17454f4` | SUCCEEDED |

E-208 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
407478be97a8979a8e3555bba3b3ab302229f91d
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-209 | Submission_Artifacts diff, 84df25c against HEAD | `git diff --quiet 84df25c HEAD -- docs/SUBMISSION_DRAFT.md docs/SUBMISSION_READINESS.md docs/JUDGE_DEMO.md docs/RELEASE_READINESS.md docs/KIRO_USAGE.md` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | SUCCEEDED |

E-209 output, in full: empty (0 bytes, so the hash is that of the empty string; no pipe; exit code read directly). Sanitization: no sanitization needed (0 hits per class). Exit 0 means the five files are identical at the two commits. Exit 1 means a difference.

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-210 | Submission_Artifacts blob ids at 84df25c | `git ls-tree 84df25c -- docs/SUBMISSION_DRAFT.md docs/SUBMISSION_READINESS.md docs/JUDGE_DEMO.md docs/RELEASE_READINESS.md docs/KIRO_USAGE.md` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `624eb7d1687ded9a182ce22d06f1c0672f43859b1c681b0a4607c2da3b58c098` | SUCCEEDED |

E-210 output, in full (5 lines; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
100644 blob 08e54e7d6febd7136fde1c22720958aac5ed500e	docs/JUDGE_DEMO.md
100644 blob 69575c6e43dbc40be09149d096e1fcf455211e89	docs/KIRO_USAGE.md
100644 blob acfe16a67246ce070e4fcafce83449ede1e6c673	docs/RELEASE_READINESS.md
100644 blob f02cfa89b652a1ff78c86f194d776f58e56818d3	docs/SUBMISSION_DRAFT.md
100644 blob ccd75511502cb1c1e2622b51fb65989c6ca622c1	docs/SUBMISSION_READINESS.md
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-211 | Submission_Artifacts blob ids at HEAD | `git ls-tree HEAD -- docs/SUBMISSION_DRAFT.md docs/SUBMISSION_READINESS.md docs/JUDGE_DEMO.md docs/RELEASE_READINESS.md docs/KIRO_USAGE.md` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `624eb7d1687ded9a182ce22d06f1c0672f43859b1c681b0a4607c2da3b58c098` | SUCCEEDED |

E-211 output, in full (5 lines; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
100644 blob 08e54e7d6febd7136fde1c22720958aac5ed500e	docs/JUDGE_DEMO.md
100644 blob 69575c6e43dbc40be09149d096e1fcf455211e89	docs/KIRO_USAGE.md
100644 blob acfe16a67246ce070e4fcafce83449ede1e6c673	docs/RELEASE_READINESS.md
100644 blob f02cfa89b652a1ff78c86f194d776f58e56818d3	docs/SUBMISSION_DRAFT.md
100644 blob ccd75511502cb1c1e2622b51fb65989c6ca622c1	docs/SUBMISSION_READINESS.md
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-212 | Tracked files that differ from HEAD | `git diff --numstat HEAD` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:12 | 0.1 | 0 | 2026-11-26 00:11:12 | `fe4de20e89b183e42233e869e109ecf70701bd0f63f669b04a4a0e5341c0a31a` | SUCCEEDED |

E-212 output, in full (4 lines; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class). When this command ran, this task had already appended 123 lines to this ledger (records E-201 to E-211), so the ledger itself appears in the output as an addition. See the working-tree reading in the acceptance results.

```text
warning: in the working copy of '.kiro/specs/verdictkit-next-phase/tasks.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/next-phase/EXECUTION_EVIDENCE.md', LF will be replaced by CRLF the next time Git touches it
1	1	.kiro/specs/verdictkit-next-phase/tasks.md
123	0	docs/next-phase/EXECUTION_EVIDENCE.md
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-213 | Tool version: git | `git --version` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:55 | 0.1 | 0 | 2026-11-26 00:11:55 | `4d64195d02d9b6c34b8cdaf295198f8d80ee34b3a13e4bd353b66c08a490c769` | SUCCEEDED |

E-213 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
git version 2.51.0.windows.2
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-214 | Tool version: uv | `uv --version` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:55 | 0.1 | 0 | 2026-11-26 00:11:55 | `dd75b2209ae5d73f07e8de75d68794eb86ed53c4c4544f188e42317b2074114e` | SUCCEEDED |

E-214 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
uv 0.13.9 (6b2d39dcc 2026-11-17 x86_64-pc-windows-msvc)
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-215 | Tool version: Python in the project environment | `uv run --no-sync python --version` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:55 | 0.6 | 0 | 2026-11-26 00:11:56 | `70cdabcb3db65c88ed55af941186c296a35d83238bb44aac7dff3f71f5ca5be9` | SUCCEEDED |

E-215 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
Python 3.12.10
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-216 | Tool version: Node | `node --version` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:56 | 0.1 | 0 | 2026-11-26 00:11:56 | `c838acc27f7f4069057257c3d53594b2e38b16deb4e8762db625cb924b2789fd` | SUCCEEDED |

E-216 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
v24.14.1
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-217 | Tool version: npm | `npm --version` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:56 | 1.1 | 0 | 2026-11-26 00:11:57 | `542a2b4513f2abd4197f5ab06ee1ac40aac4d865bbcac6864417d28e1ae9b9d2` | SUCCEEDED |

E-217 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
11.11.0
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-218 | Tool version: ruff | `uv run --no-sync ruff --version` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:57 | 0.1 | 0 | 2026-11-26 00:11:57 | `d6236ddc3f537ec51a522b977b0ae6c96978443d733461a78368fce038578f1d` | SUCCEEDED |

E-218 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
ruff 0.8.4
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-219 | Tool version: pytest | `uv run --no-sync pytest --version` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:57 | 1.2 | 0 | 2026-11-26 00:11:58 | `be35e47e13b646c95d5c54ef378cf25d0dff18921079c20926f22949f0139924` | SUCCEEDED |

E-219 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
pytest 9.2.0
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-220 | Tool version: Hypothesis | `uv run --no-sync python -c "import hypothesis; print(hypothesis.__version__)"` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:11:58 | 1.7 | 0 | 2026-11-26 00:12:00 | `6124b8d2d7aee52d3a70419e3d3fa61df36cac8db5ad82e84d8133ca18fa7ba9` | SUCCEEDED |

E-220 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
6.170.15
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-221 | Locked version of mcp in uv.lock | `uv run --no-sync python -c "import tomllib; print([p['version'] for p in tomllib.load(open('uv.lock','rb'))['package'] if p['name']=='mcp'])"` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:12:00 | 0.2 | 0 | 2026-11-26 00:12:00 | `b05d4a597d0374c6dd17ce8f7cde048e754672bec35b52f6b29c6b6574d636b6` | SUCCEEDED |

E-221 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class).

```text
['2.3.0']
```

| Record | Step | Command | Working directory | Commit | Host | Start (UTC) | Seconds | Exit | Recorded (UTC) | Output SHA-256 | Class |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E-222 | Docker engine Server.Os and version | `docker version --format "{{.Server.Os}} {{.Server.Version}}"` | repository root | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | Windows (PowerShell) | 2026-11-26 00:12:20 | 0.2 | 0 | 2026-11-26 00:12:20 | `4f87e051c989ef53884069c1078a84213a27849ecc1e4d66368ed2a64cb1c1f5` | SUCCEEDED |

E-222 output, in full (1 line; no pipe; stdout and stderr merged in capture order; exit code read directly). Sanitization: no sanitization needed (0 hits per class). The Docker client is not on the PATH of this session; session PATH extended with the Docker Desktop client directory.

```text
linux 29.9.3
```

### Privacy check of the published outputs

Each output of E-201 to E-222 was checked before publication for user-profile paths, repository-root paths, other absolute paths, user names, host names, e-mail addresses, non-loopback network addresses, secrets and key blocks. Result for all 22 outputs: no sanitization needed (0 hits per class). The text of this section, including the tables and lines below, was checked the same way before it was written: 0 hits per class. No local drive path, user name or host name is written in this section.

### Acceptance results

E-201 to E-222: 22 records, 22 with exit 0 and Outcome_Class SUCCEEDED, 0 FAILED or UNVERIFIED. The Commit column holds one value in all 22 rows. The largest value of Recorded (UTC) minus Start (UTC) minus Seconds over the 22 records, from the whole-second columns, is 0.9 s (limit 5 s).

| Check | Result | Evidence |
|---|---|---|
| A1 Branch and HEAD (1.1) | PASS | E-202 prints `feature/kiro-next-phase` and E-203 prints `a7ab9ab1b79721998b2961c9c2ae955aa90b3598`, both with exit 0. HEAD did not move during the task: the Commit column of E-201 to E-222 holds this one value. |
| A2 Frozen_Release refs (1.2; D9-AC-16 phase-start leg) | PASS | 4 of 4 ref values equal Requirement 1.2. Tag object of `v1.0.0-submission`: `e9ca8d2bac4a65483f3a7357e00600a1210a6f4f` (E-206). Peeled commit: `84df25c68198e496889b5892a03555ec7d2d860a` (E-207). `master`: `84df25c68198e496889b5892a03555ec7d2d860a` (E-205). `verified-quote-e2e-20261118`: `407478be97a8979a8e3555bba3b3ab302229f91d` (E-208). `84df25c` resolves to `84df25c68198e496889b5892a03555ec7d2d860a` (E-204). All five records have exit 0. |
| A3 Submission_Artifacts (1.2, 14.14; D9-AC-16 phase-start leg) | PASS | E-209 (`git diff --quiet 84df25c HEAD` over the five files) has exit 0 and empty output. The five blob ids are equal at `84df25c` (E-210) and at HEAD (E-211), line for line: `docs/JUDGE_DEMO.md` `08e54e7d6febd7136fde1c22720958aac5ed500e`; `docs/KIRO_USAGE.md` `69575c6e43dbc40be09149d096e1fcf455211e89`; `docs/RELEASE_READINESS.md` `acfe16a67246ce070e4fcafce83449ede1e6c673`; `docs/SUBMISSION_DRAFT.md` `f02cfa89b652a1ff78c86f194d776f58e56818d3`; `docs/SUBMISSION_READINESS.md` `ccd75511502cb1c1e2622b51fb65989c6ca622c1`. |
| A4 Working tree (1.9) | PASS | E-201 lists 3 entries, all inside `.kiro/specs/verdictkit-next-phase/`. E-212 lists `tasks.md` (1 insertion, 1 deletion) and this ledger (123 insertions, 0 deletions). See the reading below the table. |
| A5 Tool versions | PASS | git 2.51.0.windows.2 (E-213); uv 0.13.9 (E-214); Python 3.12.10 in the project environment (E-215; patch version 10; at least 3.12.4: yes); Node v24.14.1 (E-216); npm 11.11.0 (E-217); ruff 0.8.4 (E-218); pytest 9.2.0 (E-219); Hypothesis 6.170.15 (E-220); locked mcp 2.3.0 (E-221). All nine records have exit 0. |
| A6 Docker engine Server.Os | PASS | E-222: Server.Os `linux`, Server.Version `29.9.3`, exit 0. The engine answered through Docker Desktop, so this host is a Linux_Docker_Host (Glossary). The session PATH was extended with the Docker Desktop client directory for E-222, and this task started nothing. |

Reading of A4 (1.9). E-201 ran before this task wrote anything and lists 3 entries, all inside `.kiro/specs/verdictkit-next-phase/`: the modified `tasks.md` and the untracked `.config.kiro` and `tasks.meta.json`. The `tasks.md` entry is the in-progress marker of the task tracker. It is a change to an existing tracked file (1 insertion and 1 deletion in E-212) and not a new file, so the word "new" in the acceptance test is met in substance (no application, test, script, configuration or lock file differs from HEAD) and not literally. E-212 also lists this ledger (123 insertions, 0 deletions), because records are written as the commands run. Those 123 lines are the lines that E-201 to E-211 had appended when E-212 ran, so the ledger entry is the append-only write of this task and not an earlier change. Read without the ledger, E-212 shows exactly one changed tracked file, `tasks.md`. Read literally, "exactly one changed tracked file" does not hold for the raw output of E-212, because that output includes the ledger.

D9-AC-16 phase-start leg: SUCCEEDED

VM-13 at the start recorded

Kiro credits for this task: NOT_AVAILABLE (no Kiro usage record was read, 16.2)

### Push of the task-plan checkpoint (observation, 14.13)

This row is an observation of a ref update and not an Execution_Record: it has no command, exit code or Outcome_Class, as for PUSH-001 to PUSH-003. The time is the timestamp of the last line of the local reflog of `refs/remotes/origin/feature/kiro-next-phase`, converted to UTC. That line is an `update by push` entry. The time is when the local tracking ref was updated after the push, and it is not a server timestamp.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-004 | `refs/heads/feature/kiro-next-phase` | `aea7d06d11cf32f9f5abba7cbd3f33a3472c935a` | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | 2026-11-25 23:42:40 | Stated by the repository owner in the request of 2026-11-25 that asked for the commit and push of the task plan. The text of the authorization is not stored in this repository. |

### Finalization of PH1-01 (after the host shutdown)

Status: a reading of recorded data plus a publication scan, written 2026-11-26 (UTC date of the system clock). It adds no Execution_Record, no E-id and no Outcome_Class. It does not change records E-201 to E-222 or any text above it.

Interruption. A host shutdown interrupted task PH1-01 after E-222 and before the task was finalized (owner-stated). Records E-201 to E-222 were present in the uncommitted working-tree copy of this ledger at the resume (V1 below). The preflight was not run again. The resume did not add, change, remove or repeat any record of E-201 to E-222. Its read-only state check (the working-tree status in short form, a read of the local HEAD, and `git ls-remote origin refs/heads/feature/kiro-next-phase`) is not an Execution_Record. The read of the local HEAD used the same command text as E-203, was not recorded, and does not replace or add to E-203. Result of that state check: the local HEAD and the remote head of `feature/kiro-next-phase` were both `a7ab9ab1b79721998b2961c9c2ae955aa90b3598`, the value in the Commit column of E-201 to E-222. The working tree differed from HEAD in `tasks.md` and this ledger (modified) and in the two spec files `.config.kiro` and `tasks.meta.json` (untracked). Owner-stated at the resume and not verified by it (the resume ran no Docker command): Docker Desktop was restarted and its Linux engine 29.9.3 is operational, which equals the version recorded in E-222.

Method. V1 to V6 are a recomputation over the text of this ledger by a scratch script that is not part of the repository. The script ran no repository command and changed no file. V7 is the numstat that git reports for this file against HEAD. It is a read, like the state check above, and not an Execution_Record.

| Check | What was recomputed | Result | Counts |
|---|---|---|---|
| V1 | Rows E-201 to E-222: each once, in ascending order, no gap; one "output, in full" statement each (E-209 states an empty output) | PASS | 22 rows, 22 statements, 0 duplicates, 0 gaps |
| V2 | Exit and Class of every row; the Commit column | PASS | 22 of 22 with exit 0, 22 of 22 SUCCEEDED, 1 distinct Commit value (the HEAD named above) |
| V3 | SHA-256 of each output as published (UTF-8, LF, no trailing newline; the empty string for E-209) against the Output SHA-256 column; the stated line count against the real line count of each block | PASS | 22 of 22 hashes equal, 22 of 22 line counts equal |
| V4 | (Recorded - Start) - Seconds from the whole-second columns; order of the start times; dates | PASS | largest value 0.9 s (E-203), 0 values above 5 s, start times never decrease, 0 rows with Recorded before Start, 1 distinct date |
| V5 | The 22 command fields: each is one code span that starts with git, uv, node, npm or docker | PASS | 0 ellipsis, 0 angle-bracket placeholder, 0 descriptive stand-in |
| V6 | D9-AC-16, phase-start leg, as recorded | PASS | 4 of 4 ref values (E-205 to E-208) equal Requirement 1.2; the outputs of E-210 and E-211 are identical (5 lines each, same hash); E-209 has exit 0 and an empty output |
| V7 | Append-only: numstat of this file against HEAD, read before this subsection was added | PASS | 0 deleted lines, 269 added lines |

Line endings. At the resume the working copy of this ledger had mixed line endings (101 lines with CRLF, 296 lines with LF), and the index and HEAD hold LF only (read with the line-ending listing of git and a comparison with the HEAD blob). Git compares after its line-ending normalization, so V7 is read in that form. The resume left every existing line as it was and wrote this subsection with LF endings.

A4 (1.9), owner acceptance. The documented reading of A4 above is accepted by the repository owner. This is owner-stated, in the request of 2026-11-26 (UTC date of the system clock) that asked to finalize PH1-01. The text of the acceptance is not stored in this repository. Effect: the A4 reading stands as documented, and the wording "only new phase documents" of the acceptance test is accepted as met in substance and not literally. The A4 row is unchanged. The acceptance is a statement of the owner and not a command result, so it carries no Outcome_Class.

Publication scan (3.14). The files published by the commit that holds this subsection are this ledger and `tasks.md`. Both were scanned for the eight classes of 3.14, for other absolute local paths (drive-letter, UNC and home-style), and for long encoded runs other than hexadecimal hashes, a class of the earlier scan in `EVIDENCE_REDACTION.md`. The rules RR-1 to RR-3 of that document were applied to the local checkout path, the temporary directory path and the user-profile path. Those values, and the user names and the host name, were read from the environment and from the version-control configuration at run time. They are not written in this file. The result is one count per class and never a matched value. The scanner was first run on a planted sample built in memory: 10 of 10 classes detected, 0 hits on a clean sample. The scan covered the ledger as it was before this subsection was added (397 lines, 269 of them added against HEAD) and `tasks.md` as it was before the checkbox change (1,226 lines, 1 of them changed against HEAD). The text of this subsection was checked before it was written into this ledger.

| Class | Ledger, whole file | Ledger, added lines | `tasks.md`, whole file | `tasks.md`, changed line | Text of this subsection |
|---|---|---|---|---|---|
| User-profile path (RR-2, RR-3 and profile-style paths) | 0 | 0 | 0 | 0 | 0 |
| Repository-root path (RR-1) | 0 | 0 | 0 | 0 | 0 |
| Other absolute local path (drive-letter, UNC, home-style) | 0 | 0 | 0 | 0 | 0 |
| User name (account, version-control and hosting identities) | 0 | 0 | 0 | 0 | 0 |
| Host name | 0 | 0 | 0 | 0 | 0 |
| E-mail address | 0 | 0 | 0 | 0 | 0 |
| Non-loopback network address (IPv4 and IPv6) | 0 | 0 | 0 | 0 | 0 |
| Secret assignment or token | 0 | 0 | 0 | 0 | 0 |
| Key block | 0 | 0 | 0 | 0 | 0 |
| Long encoded run other than a hexadecimal hash | 0 | 0 | 0 | 0 | 0 |

Result: 0 hits in every class and every column, so the scan does not block the commit.

Task status. The box of task 1.1 PH1-01 in `tasks.md` is ticked in the same commit as this subsection (4.9). D9-AC-16 (phase-start leg) is recorded as SUCCEEDED above, and every record of E-201 to E-222 has Outcome_Class SUCCEEDED. Kiro credits for this task: NOT_AVAILABLE (no Kiro usage record was read, 16.2).

Push. The push of the commit that holds this subsection is recorded by the first ledger update after it, because a commit cannot contain its own id (see the note after PUSH-003). No PUSH-005 row is written here.

### Push of the PH1-01 finalization commit (observation, 14.13)

Status: a reading of recorded data plus a publication scan, written 2026-11-26 (UTC date of the system clock). It is the first ledger update after the Finalization of PH1-01 and records the push that the Finalization left open. It adds no Execution_Record, no E-id and no Outcome_Class. It does not change records E-201 to E-222 or any text above it.

This row is an observation of a ref update and not an Execution_Record: it has no command, exit code or Outcome_Class, as for PUSH-001 to PUSH-004. The time is the timestamp of the last line of the local reflog of `refs/remotes/origin/feature/kiro-next-phase`, converted to UTC. That line is an `update by push` entry and carries Unix time 1795677952. The time is when the local tracking ref was updated after the push, and it is not a server timestamp.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-005 | `refs/heads/feature/kiro-next-phase` | `a7ab9ab1b79721998b2961c9c2ae955aa90b3598` | `07cdac4d28ed001080e2299541bdf937eabe8b35` | 2026-11-26 07:25:52 | Owner-executed manual PowerShell push. Stated by the repository owner in the request of 2026-11-26 that asked for this record. The text of the statement is not stored in this repository. |

Reading. The Before value equals the After value of PUSH-004 and the parent of the After commit. The After commit is the commit titled "docs(evidence): finalize PH1-01 start-of-phase preflight (E-201 to E-222)", which holds the Finalization of PH1-01 and the ticked box of task 1.1 PH1-01. At the time of this record the local reflog of the tracking ref holds 5 entries, all `update by push`, and they are the 5 rows PUSH-001 to PUSH-005.

Publication scan (3.14). The file published by the commit that holds this subsection is this ledger. It was scanned for the eight classes of 3.14, for other absolute local paths (drive-letter, UNC and home-style) and for long encoded runs other than hexadecimal hashes, by a scratch script that is not part of the repository (the permanent scan is task PH1-03). The values of the local checkout path, the temporary directory path, the user-profile path, the user names and the host name were read from the environment and from the version-control configuration at run time and are not written in this file. The scanner was first run on a planted sample built in memory: 10 of 10 classes detected, 0 hits on a clean sample. The scan ran on the file text with the draft of this subsection in place, before it was written, and again on the written file. Both runs give the counts below. The result is one count per class and never a matched value.

| Class | Ledger, whole file, after this update | Added lines of this update |
|---|---|---|
| User-profile path (RR-2, RR-3 and profile-style paths) | 0 | 0 |
| Repository-root path (RR-1) | 0 | 0 |
| Other absolute local path (drive-letter, UNC, home-style) | 0 | 0 |
| User name (account, version-control and hosting identities) | 0 | 0 |
| Host name | 0 | 0 |
| E-mail address | 0 | 0 |
| Non-loopback network address (IPv4 and IPv6) | 0 | 0 |
| Secret assignment or token | 0 | 0 |
| Key block | 0 | 0 |
| Long encoded run other than a hexadecimal hash | 0 | 0 |

Result: 0 hits in every class and both columns, so the scan does not block the commit.

A push of the commit that holds this subsection is recorded by the first ledger update after it, because a commit cannot contain its own id (see the note after PUSH-003).

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
