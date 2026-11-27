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

### Push of the PH1-01 record commit and the task-plan remediation (observation, 14.13)

Status: a reading of recorded data plus a publication scan, written 2026-11-26 (UTC date of the system clock). It is the first ledger update after the commit that holds the PUSH-005 row, and it records the push of that commit. It adds no Execution_Record, no E-id and no Outcome_Class. It does not change records E-201 to E-222 or any text above it.

This row is an observation of a ref update and not an Execution_Record: it has no command, exit code or Outcome_Class, as for PUSH-001 to PUSH-005. The time is the timestamp of the last line of the local reflog of `refs/remotes/origin/feature/kiro-next-phase`, converted to UTC. That line is an `update by push` entry and carries Unix time 1795679353. The time is when the local tracking ref was updated after the push, and it is not a server timestamp.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-006 | `refs/heads/feature/kiro-next-phase` | `07cdac4d28ed001080e2299541bdf937eabe8b35` | `b4d150272c6c6b0efc50c8038e9bdfdb6d49d4cb` | 2026-11-26 07:49:13 | Explicitly authorized by the repository owner as an ordinary feature-branch push through Kiro. Stated in the request of 2026-11-26 that asked for this record. The text of the statement is not stored in this repository. |

Reading. The Before value equals the After value of PUSH-005 and the parent of the After commit. The After commit is the commit titled "docs(evidence): record PUSH-005 for the PH1-01 finalization commit". It changed only this ledger, with 31 added lines, which are the PUSH-005 subsection. At the time of this record the local reflog of the tracking ref holds 6 entries, all `update by push`, and they are the 6 rows PUSH-001 to PUSH-006. The local branch, the local tracking ref and the output of `git ls-remote origin refs/heads/feature/kiro-next-phase` all showed the After value when these values were read for this record. That read, and the conversion of the Unix time to UTC, are state checks and not Execution_Records.

Task-plan remediation. The commit that holds this subsection also holds the documentation changes of the task-plan review remediation (31 findings, TPR-C-1 to TPR-L-5): `requirements.md`, `design.md` (section D10.11), `tasks.md`, `REVIEW_REMEDIATION_REGISTER.md` and this ledger. It changes no application code, no test, no script, no configuration and no lock file. It adds no Execution_Record and does not change records E-201 to E-222. The box of task 1.1 PH1-01 stays ticked and no other box is ticked. The register records the result of the document checks. Nothing in the commit is an owner approval: OA-00 and every other owner item are `OPEN`. Kiro credits for this work: NOT_AVAILABLE (no Kiro usage record was read, 16.2).

Publication scan (3.14). The files published by the commit that holds this subsection are `requirements.md`, `design.md`, `tasks.md`, `REVIEW_REMEDIATION_REGISTER.md` and this ledger. They were scanned for the eight classes of 3.14, for other absolute local paths (drive-letter, UNC and home-style) and for long encoded runs other than hexadecimal hashes, by a scratch script that is not part of the repository (the permanent scan is task PH1-03, and it is not implemented). The values of the local checkout path, the temporary directory path, the user-profile path, the user names and the host name were read from the environment and from the version-control configuration at run time and are not written in any file. The scanner was first run on a planted sample built in memory: 10 of 10 classes detected, 0 hits on a clean sample. The scan ran on the text of this subsection before it was written into the ledger and again on the five written files. Both runs give the counts below. The result is one count per class and never a matched value.

| Class | Lines added by this commit, five files | Hits above the HEAD count, any file |
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

Result: 0 hits in every class in the added lines, and no file has more hits than its HEAD version. The hits that exist in the whole files at HEAD are unchanged: the documented constructed example paths of `design.md` and the environment-variable placeholders of `requirements.md` (see `EVIDENCE_REDACTION.md`, "Not redacted, and why"). The scan result does not block the commit.

A push of the commit that holds this subsection is recorded by the first ledger update after it, because a commit cannot contain its own id (see the note after PUSH-003).

### Push of the task-plan remediation commit and the owner scope freeze (observation, 14.13)

Status: a reading of recorded data plus a publication scan, written 2026-11-26 (UTC date of the system clock). It is the first ledger update after the commit that holds the PUSH-006 subsection, and it records the push of that commit. It adds no Execution_Record, no E-id and no Outcome_Class. It does not change records E-201 to E-222 or any text above it.

This row is an observation of a ref update and not an Execution_Record: it has no command, exit code or Outcome_Class, as for PUSH-001 to PUSH-006. The time is the timestamp of the last line of the local reflog of `refs/remotes/origin/feature/kiro-next-phase`, converted to UTC. That line is an `update by push` entry and carries Unix time 1795713872. The time is when the local tracking ref was updated after the push, and it is not a server timestamp. It is not the commit time of the After commit.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-007 | `refs/heads/feature/kiro-next-phase` | `b4d150272c6c6b0efc50c8038e9bdfdb6d49d4cb` | `fff6db49fb6f7f51080ca4fdb5e0ee7c1d37a581` | 2026-11-26 17:24:32 | Owner-executed manual PowerShell push. Stated by the repository owner in the request of 2026-11-26 that asked for this record. The text of the statement is not stored in this repository. |

Reading. The Before value equals the After value of PUSH-006 and the parent of the After commit. The After commit is the commit titled "docs(spec): resolve implementation dependency and verification findings". It holds the PUSH-006 subsection and the documentation changes of the task-plan review remediation. This push was not recorded before, and the row PUSH-006 is unchanged. At the time of this record the local reflog of the tracking ref holds 7 entries, all `update by push`, and they are the 7 rows PUSH-001 to PUSH-007. The local branch, the local tracking ref and the output of `git ls-remote origin refs/heads/feature/kiro-next-phase` all showed the After value when these values were read for this record. That read, and the conversion of the Unix time to UTC, are state checks and not Execution_Records.

Scope freeze and owner decisions. The commit that holds this subsection also holds the owner decisions of 2026-11-26 and the scope reconciliation that follows from them: `requirements.md`, `design.md` (section D10.12), `tasks.md`, `REVIEW_REMEDIATION_REGISTER.md`, the new `OWNER_DECISIONS.md` and this ledger. It changes no application code, no test, no script, no configuration and no lock file. It adds no Execution_Record and does not change records E-201 to E-222. The box of task 1.1 PH1-01 stays ticked and no other box is ticked. OA-00 (`ACCEPTED_WITH_CONDITIONS`) and OA-08 (for OD-D8-1 to OD-D8-4) are recorded `PROVIDED`, and OA-02 is recorded `NOT_PROVIDED`, in `OWNER_DECISIONS.md`. The agent transcribed them from the owner's request and made none of those decisions. OA-01, OA-03, OA-04, OA-05, OA-06, OA-09 and OA-10 stay `OPEN`. The deferred items (15 tasks, OA-07a to OA-07e and CD-01 to CD-09) are not implemented and not verified. Kiro credits for this work: NOT_AVAILABLE (no Kiro usage record was read, 16.2). The owner's request says that nearly 2,000 credits have been consumed in total. That statement is approximate and carries no unit, session identifier or request-identifier count, so it is not a Credit_Record and no figure is added (16.2, 16.5).

Push of this commit. The owner authorized one ordinary non-force push of the Phase_Branch for the commit that holds this subsection, through the normal Kiro approval controls, in the request of 2026-11-26. The text of the authorization is not stored in this repository. The push is recorded by the first ledger update after it, because a commit cannot contain its own id (see the note after PUSH-003).

Publication scan (3.14). The files published by the commit that holds this subsection are `requirements.md`, `design.md`, `tasks.md`, `REVIEW_REMEDIATION_REGISTER.md`, `OWNER_DECISIONS.md` and this ledger. They were scanned for the eight classes of 3.14, for other absolute local paths (drive-letter, UNC and home-style) and for long encoded runs other than hexadecimal hashes, by a scratch script that is not part of the repository (the permanent scan is task PH1-03, and it is not implemented). The values of the local checkout path, the user-profile path, the user names and the host name were read from the environment and from the version-control configuration at run time and are not written in any file. The scanner was first run on a planted sample built in memory: 10 of 10 classes detected, 0 hits on a clean sample. The scan ran on the text of this subsection before it was written into the ledger and again on the six written files. The first run on the draft reported 2 matches that were false positives of the scanner's own rules: a repository reference path was read as a long encoded run, and a time of day was read as a network address. The two rules were narrowed (an IPv6 address needs eight groups or a `::`, and a long run needs an upper-case letter, a lower-case letter and a digit and is not hexadecimal). The planted-sample test was run again with 10 of 10 classes detected and 0 hits on a clean sample that includes a time of day and a reference path. Both runs below use the narrowed scanner and give the counts below. The result is one count per class and never a matched value.

| Class | Lines added by this commit, six files | Hits above the HEAD count, any file |
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

Result: 0 hits in every class in the added lines, and no file has more hits than its HEAD version. The hits that exist in the whole files at HEAD are unchanged: 7 user-profile-style and 11 other absolute-path matches in the specification files, which are the documented constructed example paths of `design.md` and the environment-variable placeholders of `requirements.md` (see `EVIDENCE_REDACTION.md`, "Not redacted, and why"). Under the earlier, looser long-run rule the specification files at HEAD had 70 matches, and each of them contained a path or identifier separator, with a highest entropy of 4.69 bits per character, so none looks like an encoded secret. The scan result does not block the commit.

A push of the commit that holds this subsection is recorded by the first ledger update after it, because a commit cannot contain its own id (see the note after PUSH-003).

## Accelerated Batch 1 (OA-11)

Status: a record of work and runs, written 2026-11-27 (UTC date of the system clock) under the owner decision OA-11 in `OWNER_DECISIONS.md`. It adds no E-id and does not change records E-201 to E-222 or any section above it. The ids B1-01 to B1-18 below belong to this batch only: the minimal evidence recorder of PH1-02 is not implemented, so these rows are typed by hand from the tool output of the session. The raw logs are scratch files outside the repository and are not published. No task box of `tasks.md` is ticked by this batch.

Start state, checked before any change: branch `feature/kiro-next-phase`, HEAD `327c5eb0064e2f9c686fa3765ed8bf85d53716ad`, the tags `v1.0.0-submission` and `verified-quote-e2e-20261118` and `master` untouched, and two untracked files (`.config.kiro`, `tasks.meta.json`) under `.kiro/specs/verdictkit-next-phase/` that this batch does not publish.

### PUSH-008 (observation, 14.13)

This row is an observation of a ref update and not an Execution_Record, as for PUSH-001 to PUSH-007. The time is the Unix time of the newest line of the local reflog of `refs/remotes/origin/feature/kiro-next-phase`, converted to UTC (`1795730917`; the same conversion reproduces the recorded time of PUSH-007). It is when the local tracking ref was updated, not a server timestamp and not the commit time.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-008 | `refs/heads/feature/kiro-next-phase` | `fff6db49fb6f7f51080ca4fdb5e0ee7c1d37a581` | `327c5eb0064e2f9c686fa3765ed8bf85d53716ad` | 2026-11-26 22:08:37 | The owner authorized one ordinary non-force push of this commit through the normal Kiro approval controls (the PUSH-007 subsection above). Whether it was executed through Kiro or by hand is not recorded in git and stays `UNVERIFIED`. |

Reading. Before equals the After value of PUSH-007 and the parent of the After commit, "docs(scope): approve and freeze enhanced release implementation scope". The tracking-ref reflog holds 8 entries, all `update by push`, which are the 8 rows PUSH-001 to PUSH-008. `git ls-remote origin refs/heads/feature/kiro-next-phase` returned the After value when read. The push of the commit that holds this section is recorded by the first ledger update after it.

### Execution records

Hosts. `Windows`: the owner's Windows host, Python 3.12.10, Node 24.14.1, `uv run --frozen`. `Linux container`: Docker Desktop Linux container from an image built from the changed tree, run with `--network none`. This is not the Linux_Docker_Host full-checkout run that DLV-1 to DLV-4 require (see "Open items").

| Id | Host | What ran | Exit | Result | Class |
|---|---|---|---|---|---|
| B1-01 | Windows | `pytest tests/contract tests/api tests/integration -q -x`, BE-1 test deselected, unmodified tree | 0 | 428 passed, 9 skipped, 1 deselected, 36.19 s | SUCCEEDED |
| B1-02 | Windows | BE-2 test in a detached worktree of `327c5eb` | 1 | fails with a socket timeout, the 7 other tests of the file pass | FAILED, baseline exception BE-2 reproduced at the baseline commit |
| B1-03 | Windows | `npm audit` before any dependency change | 1 | 5 findings: 2 critical (`tinypool`, `vitest`), 1 high (`vite`), 2 moderate (`esbuild`, `@vitest/mocker`) | SUCCEEDED |
| B1-04 | Windows | collected test ids, baseline vs final tree | 0 | 438 vs 447 collected, 9 added (7 in `test_signed_bundle_http.py`, 2 in `test_llm_fence.py` for the new modules), 0 removed | SUCCEEDED |
| B1-05 | Windows | same selection as B1-01 on the final tree, nothing deselected | 0 | 438 passed, 9 skipped, 40.5 s. The delta to B1-01 is the 9 added tests plus BE-1, which passes now. | SUCCEEDED |
| B1-06 | Windows | `pytest tests/security tests/api/test_signed_bundle_http.py` | 0 | 160 passed, 11 skipped (POSIX-only or link-privilege cases), 7.6 s | SUCCEEDED |
| B1-07 | Windows | `HYPOTHESIS_PROFILE=ci pytest -q -m "not isolation"` (whole repository) | 1 | 607 passed, 16 skipped, 4 deselected, 1 failed (BE-2, as in B1-02), 48.2 s | FAILED, only the baseline exception |
| B1-08 | Windows | `ruff check .` | 0 | All checks passed | SUCCEEDED |
| B1-09 | Windows | `npm run typecheck`, `npm test`, `npm run build`, `npm audit` after the upgrade | 0 | typecheck clean in 3 workspaces; 22 tests passed (ui-kit 12, quote 6, reel 4; 19 before, 3 added); both apps build; 0 vulnerabilities | SUCCEEDED |
| B1-10 | Linux container, user `vk-custodian` | `pytest tests/contract tests/api tests/integration tests/security -m "not isolation"`, 2 line-ending tests deselected | 0 | 600 passed, 5 skipped (Windows-only checks, UI sources absent from the image), 6 deselected, 34.0 s. The POSIX-only tests ran here. | SUCCEEDED |
| B1-11 | Linux container | `gate-isolation` | 0 | 4 passed, JUnit tests=4 failures=0 errors=0 | SUCCEEDED |
| B1-12 | Linux container | `gate-startup` | 0 | `VK_STARTUP_OK isolation=ENFORCED` | SUCCEEDED |
| B1-13 | Linux container | `gate-http` (judge mode through the socket examiner: a live Finance case, a Reel synthetic fixture, a blocked live Reel case, server replay of both bundles) | 0 | `GATE-HTTP PASSED`; live and demo server replays `REPRODUCED`; `/proc` scan: 604 polls, canary seen, 0 key hits | SUCCEEDED |
| B1-14 | Linux container | `gate-sign` | 0 | `GATE-SIGN PASSED`: 14 checks, including a signed run under ENFORCED, offline verification as `vk-examiner`, unknown and revoked signer, three tamper cases, unsigned bundle replay, examiner cannot read the key, worker refusals | SUCCEEDED |
| B1-15 | Linux container | `gate-case` then `verdictkit replay` of its bundle | 0 | isolation ENFORCED, headline CONTRADICTED, integrity VERIFIED, `REPRODUCED`, `signature: UNSIGNED`, `authenticity: NOT_ESTABLISHED` | SUCCEEDED |
| B1-16 | Windows | 6 source mutations, each with its targeted test (admission after buffering, vault case-id check removed, `SealedRef.path` trusted, replay written to the trusted root, manifest binding removed, unknown signer trusted) | 0 | 6 of 6 detected; the files were verified byte-identical afterwards | SUCCEEDED |
| B1-17 | Linux container | `gate-sign` against a worker with its client uid check removed | 1 | fails on exactly that check (a valid task from `vk-examiner` is served) | SUCCEEDED (the mutation is detected) |
| B1-18 | Windows | the documented key and trust-entry commands of `docs/SIGNING.md` | 0 | an OpenSSL Ed25519 key is refused with `SIGNING_KEY_PERMISSIONS` until locked down with `icacls`, then loads; the trust-entry command prints a valid entry | SUCCEEDED |

All container rows B1-11 to B1-15 and B1-17, and B1-10, used image `86e3419c67ef`, built from the code that this batch commits (the files committed after that build are documentation only).

### Defects fixed

| Defect | Where | Fix | Evidence |
|---|---|---|---|
| Vault key in process arguments (`env VK_VAULT_KEY=...`, and in the `env -i` list of `as_custodian`) | `deploy/entrypoint.sh` | tmpfs key file written with builtins, custodian reads it once and removes it (`custody/keyfile.py`); the entrypoint holds no key variable; the examiner worker refuses `VK_VAULT_KEY_FILE` | static test, B1-13 scan, B1-11 |
| Examiner worker served any client in the socket's group; a stalled client blocked the single worker | `examiner/worker.py` | `SO_PEERCRED` check of the client (only `vk-custodian`), socket created `0660`, 60 s client timeout, refuses custodian secrets in its environment | B1-14 (valid task refused for the examiner, served for the custodian), B1-17 |
| Uploaded replay evidence written into the trusted evidence root, so a bundle could pre-set metadata for hashes that live cases later use | `api/server.py` | per-replay namespace (32 hex) under a separate root, removed in `finally`, orphans swept, examiner reads it by validated namespace | unit and API tests, B1-13, B1-16 |
| Whole upload buffered twice before any slot check; unbounded replay storage | `api/server.py` | slot before the first body byte, body streamed to a private spool file under a 30 s deadline, 2 slots, 64 MiB per replay, 128 MiB total, atomic reservation | async tests with a lazy ASGI client |
| Vault used `case_id` as a file name and trusted `SealedRef.path` for reads | `custody/vault.py` | plain-identifier check, location derived from the id, atomic `0600` write, bounded read, no link following | tests, B1-16 |
| Hash strings from an uploaded index became file names (replay cache, evidence store, examiner reader) | `bundle.py`, `evidence/store.py` | 64 lowercase hex only | tests with 10 hostile forms |
| MCP tools opened any readable path (and expanded `~`) | `mcp_server.py` | approved roots (private directory plus `VK_MCP_BUNDLE_ROOTS`), safe open, size check on the open handle, work on a private copy, structured `errorCode`, bounded and sanitized explanations, malformed bundles never raise | 26 tests; a real junction was refused on Windows |
| Private-directory check was POSIX-only (BE-1 on Windows) | `safeio.py`, `mcp_server.py` | Windows access-list check next to the unchanged POSIX `0700` check | tests on both hosts |

Found by the new checks during the batch and fixed before this record: the container gate exposed `server replay DIVERGED` because a `0750` replay namespace carries the custodian's primary group, so the examiner could not read it (the namespace is now `0755` below a `0750` root, with a regression test); a first draft of the peer-credential gate used a malformed frame and could not tell the uid check from a parse failure (replaced by a valid-task probe with a positive control, B1-17).

### Dependency finding (B1-03, B1-09)

All five findings were in the development and build toolchain (`vitest`, `vite`, `esbuild`, `tinypool`, `@vitest/mocker`). The advisories concern the Vitest API and UI servers, the Vite dev server and its file-serving rules, and worker options of the test runner. The shipped UI output is static files, the Python image contains none of these packages, and the API does not load them. This describes exposure at the time of the audit and was not tested by exploiting any advisory. The fix that `npm audit` offered (`vitest 2.1.9`) would not have removed the critical `tinypool` advisories, because no 1.x `tinypool` is outside the vulnerable range and Vitest 2 and 3 depend on 1.x. The upgrade applied is `vitest 4.1.12` (drops `tinypool`) and `vite 6.4.6` in the three manifests, with `package-lock.json` regenerated by `npm install`. `npm audit fix --force` was not used. The 19 existing frontend tests, typecheck and both builds pass on the new versions.

### Deviations from the reviewed designs

1. Contract 1.2.0 carries only the `authenticity` change of D5. The other items of the joint event in D5.8 (health `commitSha`, owner cookie, new 429 routes) are not implemented. Strict 1.1.0 validators fail on the new required fields, as D5.8 states for any bump.
2. Windows signing and key files get an access-list check; D5.5 had none (R-D5-1). This is stricter than the design.
3. Replay metadata is written inside the namespace, because the examiner reads it; DD8-3 kept it in custodian scratch.
4. D5.6 step 1 (reading every archive name by its raw form so that Windows and Linux agree) is applied only to the signature member names. The archive-wide tightening is not implemented.
5. MCP errors keep the existing `error` string and add `errorCode`, so existing callers keep working.
6. `tests/contract/test_mcp_server.py` was edited in two places. BE-1: a Windows branch asserts the access-list check, and the POSIX assertion is unchanged. `test_tampered_bundle_is_not_explained` sets `VK_MCP_BUNDLE_ROOTS` for its temporary directory, which the approved-root rule now requires. No assertion was removed or loosened.
7. The tests that pin the contract version, `ui-kit`, `ui/judge` and the examples moved from 1.1.0 to 1.2.0 in lockstep. `README.md` and the submission documents keep stating 1.1.0 for the frozen release and are not edited.

### Open items and what is not verified

- BE-2 (`test_case_outcome_get_to_offline_backend` times out on Windows) fails at the baseline commit (B1-02) and is untouched. Its cause is not established.
- DLV-1 to DLV-4 stay `UNVERIFIED`. The container runs above are not full-checkout runs on a Linux_Docker_Host.
- The browser end-to-end run (`scripts/ui_e2e.sh`) was not run, so the changed UI is verified by typecheck, unit tests, builds and API-level tests only.
- The `/proc` scan samples. It shows no key at 604 samples with a canary seen; it is not proof for every instant. The static test and the design carry the guarantee.
- On Windows the permission checks are path-based and cannot close a race between check and open.
- No trusted timestamp and no online revocation (D5.7). A stale trust store is the operator's risk.
- KL-1 (plugin loading from entry points and `VK_CLAIM_TYPES`) is unchanged, so public deployment stays blocked. No public deployment was made.
- Not implemented from the queued plan: PH1-02 to PH1-05 and PH1-08 to PH1-10 tooling (recorder, publication scanner, AST guard, BE closure records), PH1-13 and PH1-15 (Isolation_Mode and Security_Profile resolver), PH2-01 and PH2-04 to PH2-09, PH3-01 and PH3-02, and Phases 4 to 7.
- Kiro credits for this batch: `NOT_AVAILABLE`. No usage record was readable.

## Accelerated Batch 2 (competition-ready product experience)

Scope: a unified portal, upgraded Quote and Reel UIs, a browser-visible signed-bundle verification lab, a one-command start, browser end-to-end tests, the BE-2 root cause and a test-environment credential fix. No new specification was created and no requirement or architecture was expanded.

### PUSH-009 (observation, 14.13)

This row is an observation of a ref update and not an Execution_Record, as for PUSH-001 to PUSH-008. It records the push of the Batch 1 commit, which the PUSH-008 subsection said the first ledger update after it would record. The time is the Unix time of the newest line of the local reflog of `refs/remotes/origin/feature/kiro-next-phase` (`1795742782`, read with `git reflog show refs/remotes/origin/feature/kiro-next-phase --date=unix`), converted to UTC. It is when the local tracking ref was updated, not a server timestamp and not the commit time.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-009 | `refs/heads/feature/kiro-next-phase` | `327c5eb0064e2f9c686fa3765ed8bf85d53716ad` | `f42a6d016202c0864a19dde1ee866a0d71d0f88a` | 2026-11-27 01:26:22 | The owner executed this push (stated in the Batch 2 request). Whether it ran through Kiro or by hand is not recorded in git and stays `UNVERIFIED`. |

Reading. Before equals the After value of PUSH-008 and the parent of the After commit, "feat(security): batch 1 remediation, Ed25519 signed bundles and MCP hardening". The reflog held 9 entries, all `update by push`, which are the 9 rows PUSH-001 to PUSH-009. `git ls-remote origin refs/heads/feature/kiro-next-phase` returned the After value when read, at the start of Batch 2. The frozen refs were unchanged at the start: `master` and tag `v1.0.0-submission` at `84df25c68198e496889b5892a03555ec7d2d860a`, tag `verified-quote-e2e-20261118` at `407478be97a8979a8e3555bba3b3ab302229f91d`. The push of the Batch 2 commit, if the owner's one authorized push succeeds, is recorded by the first ledger update after it.

### Execution records

Hosts. `Windows`: the owner's Windows host, Python 3.12.10, Node 24.14.1, system Chrome driven by `playwright-core` 1.65.1. `Linux container`: Docker Desktop, image `verdictkit:batch2` (`sha256:913397af4ac3cc764be59c4bdeee9821ac7ae8ea33cc62ee9e410c37a93ad0f4`, the final build from the committed tree; rows B2-08 to B2-13 and B2-15 were produced by one consolidated verification pass against it, with the raw logs kept in the private evidence archive described below), run with `--network none`. Neither is the Linux_Docker_Host full-checkout run that DLV-1 to DLV-4 require.

| Id | Host | What ran | Exit | Result | Class |
|---|---|---|---|---|---|
| B2-01 | Windows | 30 refused loopback connects to a closed port (BE-2 mechanism) | 0 | min 2.0156 s, median 2.0539 s, max 2.0735 s | SUCCEEDED |
| B2-02 | Linux container | the same 30 connects | 0 | min 0.0000 s, median 0.0000 s, max 0.0124 s (kernel 6.6.87.2-microsoft-standard-WSL2, same machine) | SUCCEEDED |
| B2-03 | Windows | `tests/ui/test_judge_preview.py`, before the fix | 1 | the offline-backend test fails with a socket timeout after 2.00 s; 7 others pass | FAILED, BE-2 reproduced |
| B2-04 | Windows | the same file after the fix: first the 8 original tests, then 9 with one new regression test | 0 | 8 passed and the offline-backend case answered in 1.02 s against the unchanged 2 s client timeout; 9 passed with the regression test | SUCCEEDED |
| B2-05 | Windows | `HYPOTHESIS_PROFILE=ci pytest -q -m "not isolation"` (whole repository) | 0 | 642 passed, 16 skipped, 4 deselected, 0 failed, 95.3 s in the final pass (73.0 s in an earlier identical run; B1-07 had 607 passed and 1 failed) | SUCCEEDED |
| B2-06 | Windows | `ruff check .` | 0 | All checks passed | SUCCEEDED |
| B2-07 | Windows | `npm run typecheck`, `npm test`, `npm run build:portal`, `npm audit` | 0 | typecheck clean in 4 workspaces; 49 tests passed (ui-kit 29, portal 10, quote 6, reel 4); three portal builds; 0 vulnerabilities | SUCCEEDED |
| B2-08 | Linux container | `gate-startup` | 0 | `VK_STARTUP_OK isolation=ENFORCED` | SUCCEEDED |
| B2-09 | Linux container | `gate-isolation` | 0 | 4 passed | SUCCEEDED |
| B2-10 | Linux container | `gate-sign` | 0 | `GATE-SIGN PASSED`, 14 checks (peer refusal and control, signed run under ENFORCED, offline verification as `vk-examiner`, unknown and revoked signer, three tamper cases, unsigned replay, key unreadable, worker refusal) | SUCCEEDED |
| B2-11 | Linux container | `gate-http` | 0 | `GATE-HTTP PASSED`; live and demo server replays `REPRODUCED`; `/proc` scan 963 polls, canary seen, 0 key hits (815 polls in an earlier run) | SUCCEEDED |
| B2-12 | Linux container | `gate-case`, then `verdictkit replay` of its bundle | 0 | integrity VERIFIED, `REPRODUCED`, `signature: UNSIGNED`, `authenticity: NOT_ESTABLISHED` | SUCCEEDED |
| B2-13 | Linux container, user `vk-custodian` | `pytest tests/contract tests/api tests/integration tests/security tests/ui/test_start_scripts.py tests/ui/test_gateway.py -m "not isolation"`, 2 line-ending tests deselected | 0 | 623 passed, 15 skipped, 6 deselected, 50.7 s. Skips: 10 need Node.js (not in the image), 3 Windows access-control checks, 1 NTFS-only, 1 UI sources absent | SUCCEEDED |
| B2-14 | Windows, real stack | `node tests/ui/e2e_product.cjs` against the Docker backend (ENFORCED, judge mode, signer) behind the gateway; first run | 1 | 93 passed, 2 failed (my assertion used `replay` where the documented exit rule needs `verify`; a 429 from the existing 120-requests-a-minute limit during a test burst, shown by the UI as "Backend offline") | FAILED, both causes fixed |
| B2-15 | Windows, real stack | the same suite after the fixes, the explanation and diagram checks and the Quote-to-Verify-Lab handoff, on a stack running the final image (`913397af4ac3`) | 0 | 103 checks passed, 0 failed, 0 browser console or page errors. An immediately preceding run of the same code failed 4 checks, all HTTP 429 from the existing request limit after the new handoff check added requests; the test now lets the limiter window drain before the Verify Lab section. Earlier runs on earlier builds: 101 of 101 twice | SUCCEEDED |
| B2-16 | Windows | `scripts\Start-VerdictKit.ps1 -NoBrowser`, three runs | 0 | the first run completed but held its caller's output pipe open (fixed, see defects); the other two returned in 11 s and 12 s. With port 8000 held by an unrelated process and 8001 by the owner's `verdictkit-demo` container it chose backend 8002 and entry 5170, stopped only its own earlier container and gateway, and left 8000, 8001 and 5174 untouched | SUCCEEDED |
| B2-17 | Kiro IDE | the four MCP tools through the IDE's MCP client | 0 | see "Kiro capabilities" below | SUCCEEDED, with a finding |
| B2-18 | Kiro IDE | PostFileSave hook experiment | n/a | see "Kiro capabilities" below | PARTIALLY OBSERVED |
| B2-19 | Windows | resource cleanup of Kiro-owned PowerShell hosts, after the evidence archive verified (29 files, 0 problems) | 0 | 19 shell hosts before; 14 closed (idle, no children, parent `Kiro.exe`); 5 kept: the shell running the command and its launcher, one Windows Terminal window and two Explorer windows (not the IDE's, so the user's). 5 after. The gateway, the backend container and the IDE-managed MCP servers were not touched. The IDE may keep dead terminal tabs until dismissed | SUCCEEDED |

The browser suite covers: the landing page against `/health` and `/demo/status`; navigation and the current-page marker; Quote Autopsy finance (consistent, padded, doc-fee `CONDITIONAL`), cap-cost-known lease (consistent and padded) and itemised lease, with the financial table, the plain-language explanation and an auto-scrolled verdict; Reel Autopsy demonstrations (`SUPPORTED`, `CONDITIONAL`, `IMPOSSIBLE`), a privacy rejection and a blocked real claim; signed-bundle generation, download of the bundle and the public trust store, all five scenarios side by side (trusted, unknown, revoked, unsigned historical, tampered), re-upload of the downloaded bundle, a hand-tampered upload and a non-bundle upload; the "Open in Verify Lab" handoff from a Quote result to the very bundle it produced; offline replay with `docker run --network none` of the downloaded files (valid, tampered, and `verify` with no trust store, which exits 1 with `NOT_EVALUATED`); an unreachable-backend state; and layout at 390, 768 and 1366 px with no horizontal overflow. Screenshots are in `docs/screenshots/`.

Private evidence archive. Raw logs are not in this repository. A sanitised local archive outside it (a folder named `KIRO_EVIDENCE` beside the repository, readable only by the owner, SYSTEM and Administrators) holds 29 files in 9 categories, with `evidence-index.json` listing each file's SHA-256, size, capture time, category, source (`copied`, `transcribed` or `derived`), the HEAD at capture and the Batch 2 commit. Identical files are stored once. Nothing that was not available is reconstructed: the IDE's own hook and MCP log files for this run are 0 bytes, no per-session usage or credit record exists, and terminal scrollback cannot be read, so the index lists those three as `unavailable` with the reason. The archive holds the session transcript snapshot as the only retrievable record of terminal outputs. A scan of the stored text for credential shapes, e-mail addresses, the user name and environment dumps found 0 problems.

### Defects found and fixed

| Defect | Where | Fix | Evidence |
|---|---|---|---|
| BE-2: a refused loopback connect takes about 2.05 s on this Windows host and under 13 ms on a Linux kernel; one 10 s timeout covered connect and read, so the bridge answered after the preview client's 2 s patience | `scripts/serve_judge_ui.py` | the connect phase has its own 1.0 s bound; reads keep 10 s. The test and its 2 s timeout are unchanged. A host-independent regression test asserts the connect bound is below 2 s | B2-01 to B2-04 |
| A credential-like variable of the owner's environment appeared in a pytest traceback in Batch 1 | `tests/conftest.py`, `tests/envscrub.py` | credential-like names (not `VK_*`) are removed from the test process before any test runs; only a count is reported. A canary test confirmed that two set canary variables never reached the output | `tests/security/test_test_environment.py` (3 tests) |
| Gateway: a dot-segment path such as `/quote/%2e%2e/%2e%2e/.git/config` and an encoded NUL fell through to the single-page-app index (no file was read) | `scripts/gateway.mjs` | dot-names, NUL and backslash are refused before routing | `tests/ui/test_gateway.py`, found by the first run of that test |
| The start script did not return when run under a tool that waits for its output pipe: the hidden gateway inherited the pipe | `scripts/Start-VerdictKit.ps1`, `scripts/gateway.mjs` | the gateway writes its own log (`--log`) and is started without redirecting any handle | B2-16, a regression assertion in `tests/ui/test_start_scripts.py` |
| Hero buttons were unreadable on the dark hero (a specificity bug), the verdict stayed below the form after a click, negative values were drawn as positive bars, tables did not fill their cards, the mobile navigation was clipped, a 429 read "Backend offline" | `ui-kit/src/theme.css`, `components.tsx`, `shell.tsx` | fixed. The first was found by looking at screenshots, not by DOM assertions | B2-14, B2-15 |

### Deviations and limits

1. `api/openapi.yaml` and contract 1.2.0 are unchanged. The `/api/v1/demo/*` routes are an opt-in extension (`VK_DEMO_LAB_DIR`) documented in `docs/DEMO_LAB.md`; unset, they do not exist.
2. The Python change in the engine package is `core/src/verdictkit/api/server.py` (77 insertions, 3 deletions) and the new `api/demo_lab.py`. No evaluator, custody, examiner, evidence, sweep or app domain module changed.
3. `deploy/entrypoint.sh` gains a `demo` subcommand and one passthrough variable (`VK_DEMO_LAB_DIR`). The vault key stays a tmpfs file and the signing key a custodian-only file; the examiner's environment is unchanged.
4. The earlier browser script `tests/ui/e2e_browser.cjs` and `scripts/ui_e2e.sh` were not run: they need the full `playwright` package with bundled Chromium and a native API on port 8000, which is held by an unrelated process. The new suite keeps their selectors and test ids.
5. The Quote sample worksheets are constructed. The consistent lease states the engine's own computed figures; the padded lease carries 40.00 through by plain arithmetic. `tests/integration/test_quote_constructed_examples.py` runs both through the engine.
6. The demonstration signing key is valid for seven days from provisioning and is new at every start. It proves nothing about any real signer.
7. The 120-requests-a-minute per-client limit is unchanged. Behind the gateway every browser tab shares one client address; the UI polls `/health` every 30 s and not while a tab is hidden.

### Kiro capabilities (observed in this session)

- **MCP tools.** `list_claim_types` returned 4 claim types. `verify_claim` on the stub receipt claim returned a bundle path and `CONTRADICTED`; `explain_verdict` and `replay_bundle` on that bundle returned integrity `VERIFIED` and `REPRODUCED` with equal original and replayed hashes `547fba0c67e3bcdfa7da58b914d36dc3301b7503fb1278753bbb0eb23d9aaa79`. **Finding:** the IDE's MCP server processes started at 00:43 on 2026-11-26, about 19 hours before the Batch 1 commit (19:24). Their answers carry pre-hardening wording (`contractVersion: "1.1.0"`, "bundles are unsigned in v1") and `verify_claim` refused a Quote claim with a bare `SchemaError` that the current code runs to `CONTRADICTED` in a fresh process. The server needs a restart in Kiro; `.kiro/settings/mcp.json` was not edited and `permissions.yaml` was not touched.
- **Hooks.** `PostFileSave` command output is not forwarded to the agent, so pass or fail is `UNVERIFIED`. What was observed: a save of a `.py` file moved `.pytest_cache/v/cache/nodeids` 1.4 s later with no pytest of mine running, and the cache listed 61 node ids, all from `test_llm_fence.py`, which is the `llm-fence` hook's command. A save of a non-`.py` file did not move it. A process poll saw the IDE spawn `cmd /c "uv run pytest tests/contract/test_llm_fence.py -q"` and, after a save by workspace-relative path, also `cmd /c "uv run pytest tests/contract -q -x -m \"not isolation\" --ignore=..."` (the `core-contract-tests` hook) followed by the fence run, 15 s apart. A save by absolute Windows path started only the fence hook; the cause of that difference is not established. `lastfailed` was absent afterwards. Hooks created during a session activate only at the next session start, so probe hooks could not be used and were deleted.
- **Steering.** Five steering files (`product`, `structure`, `tech`, `verdict-integrity`, `testing`) were in the session as included rules and were applied (no float in comparators or chart arithmetic of findings, "verified at N grid points" wording, no LLM imports, no test weakening, counts only from runs). `money-math` was not among the included rules.
- **Specifications.** No specification was created or edited. The existing next-phase design (D5, through `docs/SIGNING.md`) was the reference for signing and trust. Its task checkboxes are unchanged (1 of 99), because the Batch 2 work is not among those tasks. A Kiro spec workflow was not exercised in this batch: `UNVERIFIED`.
- **Shared code.** Both applications and the portal consume one `ui-kit`; both applications and the lab run on one engine package. See the footprint in deviation 2.

### Open items and what is not verified

- DLV-1 to DLV-4 stay `UNVERIFIED`; the container runs are not full-checkout runs on a Linux_Docker_Host. BE-2's host attribution is now supported by per-host connect timings (B2-01, B2-02), but a Linux per-test run of `test_judge_preview.py` from a full checkout does not exist: the image has no UI sources.
- Public deployment stays blocked (KL-1 and unchanged) and was not attempted.
- Hook pass or fail inside Kiro, a Kiro spec workflow, and the MCP server restart are `UNVERIFIED` as stated above.
- On Windows the permission checks are path-based and cannot close a race between check and open (unchanged).
- Kiro credits for this batch: `NOT_AVAILABLE`. No usage record was readable (the archive index records the search).
- The IDE's MCP server processes are stale (see "Kiro capabilities") and need a restart in Kiro; this was not done by the agent.

## Final Batch 3 (release validation and submission preparation)

Scope: final inspection of the running product, an independent security review, Kiro MCP and hook evidence, a documents and evidence audit, the release gates, and the competition documents. No architecture change, no specification change, no new dependency, no public deployment. The ids B3-01 to B3-18 belong to this batch only. Raw logs are in the private archive (`KIRO_EVIDENCE`, Batch 3 files indexed by `evidence-index-batch3.json`; the Batch 2 index and files are untouched); this section holds the summaries.

### PUSH-010 (observation, 14.13)

This row records the push of the Batch 2 commit, which the Batch 2 section said the first ledger update after it would record. It is an observation of a ref update and not an Execution_Record, as for PUSH-001 to PUSH-009. The time is the Unix time of the newest line of the local reflog of `refs/remotes/origin/feature/kiro-next-phase` (`1795755249`, read with `git reflog show refs/remotes/origin/feature/kiro-next-phase --date=unix`), converted to UTC. It is when the local tracking ref was updated, not a server timestamp and not the commit time.

| Record | Ref | Before | After | Updated (UTC) | Owner authorization |
|---|---|---|---|---|---|
| PUSH-010 | `refs/heads/feature/kiro-next-phase` | `f42a6d016202c0864a19dde1ee866a0d71d0f88a` | `78f3f583a71f87f5034f35157294694ed479168c` | 2026-11-27 04:54:09 | The owner's one authorized push of the Batch 2 commit (stated in the Batch 2 request). Whether it ran through Kiro or by hand is not recorded in git and stays `UNVERIFIED`. |

Reading. Before equals the After value of PUSH-009 and the parent of the After commit, "feat(product): unified portal, signed-bundle Verify Lab, one-command start and browser e2e (batch 2)". The reflog holds 10 entries, all `update by push`, which are the 10 rows PUSH-001 to PUSH-010. The push result is that git recorded the tracking ref as updated by a push. Remote verification, read at the start of Batch 3 and again later: `git ls-remote origin refs/heads/feature/kiro-next-phase` returned `78f3f583a71f87f5034f35157294694ed479168c`, and the GitHub API (`git/ref/heads/feature/kiro-next-phase`) returned the same commit. The frozen refs were unchanged at both readings: `master` and tag `v1.0.0-submission` (commit) at `84df25c68198e496889b5892a03555ec7d2d860a`, the tag object at `e9ca8d2bac4a65483f3a7357e00600a1210a6f4f`, tag `verified-quote-e2e-20261118` at `407478be97a8979a8e3555bba3b3ab302229f91d`. PUSH-011, the push of the commit that first held this section, and the CI run on it are recorded in the next subsection.

### PUSH-011 and the CI run on the release candidate (observation, 14.13)

PUSH-011 is the push of the commit that holds the first version of this section (`298ed8cd4e41c5a23600052a22d255c08503a76d`, "fix(ui): final release validation, security review and competition documents (batch 3)"). It is an observation of a ref update and not an Execution_Record. The time is the Unix time of the newest reflog line of the tracking ref (`1795799252`).

| Record | Ref | Before | After | Updated (UTC) | Authorization and result |
|---|---|---|---|---|---|
| PUSH-011 | `refs/heads/feature/kiro-next-phase` | `78f3f583a71f87f5034f35157294694ed479168c` | `298ed8cd4e41c5a23600052a22d255c08503a76d` | 2026-11-27 17:07:32 | An ordinary push (no force) to the feature branch only, run by the agent in the Kiro IDE session `sess_5920a573-8bf7-4888-8504-8c3434164e9a` on the owner's Batch 3 instruction. git printed `78f3f58..298ed8c  feature/kiro-next-phase -> feature/kiro-next-phase`. |

Remote verification: `git ls-remote origin` returned `298ed8cd4e41c5a23600052a22d255c08503a76d` for the branch, and the frozen refs were unchanged (`master` and the `v1.0.0-submission` commit at `84df25c68198e496889b5892a03555ec7d2d860a`, tag `verified-quote-e2e-20261118` at `407478be97a8979a8e3555bba3b3ab302229f91d`).

CI. The existing `workflow_dispatch` trigger of `p0-integration.yml` ("Integration gate") was run on the branch with `gh workflow run p0-integration.yml --ref feature/kiro-next-phase`. Run `46039452426`, event `workflow_dispatch`, branch `feature/kiro-next-phase`, **head SHA `298ed8cd4e41c5a23600052a22d255c08503a76d`, the pushed commit**, created 2026-11-27 17:08:40 UTC, finished 17:10:11 UTC, conclusion `success` for both jobs and for every step. The step logs were downloaded and read, not only the check mark:

| Step | What the log shows |
|---|---|
| checkout | fetched and checked out `298ed8cd…` |
| lock, lint | `uv lock --check` resolved 56 packages; `ruff`: all checks passed |
| startup and examiner negative tests | 16 passed |
| full regression (Linux runner) | 654 passed, 4 skipped, 4 deselected in 26.09 s |
| Docker isolation, enforced startup | 4 passed; `VK_STARTUP_OK isolation=ENFORCED` |
| judge-mode HTTP lifecycle | `GATE-HTTP PASSED`; 486 process samples, canary seen, 0 key hits |
| signed bundles under enforced isolation | `GATE-SIGN PASSED` |
| Docker receipt and replay | `CONTRADICTED`, integrity `VERIFIED`, `REPRODUCED`; original and replayed hash `547fba0c67e3bcdfa7da58b914d36dc3301b7503fb1278753bbb0eb23d9aaa79` |
| complete November gate | 232 passed, 4 deselected; `GATE-HTTP PASSED` again (479 samples, 0 key hits) |
| web-ui | typecheck clean; 32, 11, 6 and 4 unit tests passed; builds; the earlier browser harness reported `UI-E2E PASSED` |

The stub claim's sealed verdict hash is therefore the same in three environments: in-process on Windows, in the enforced Linux container on the owner's host, and on the GitHub Actions Linux runner. The browser end-to-end suite of this batch (105 checks) needs Docker and a system Chrome and is not part of the workflow; it ran locally (B3-17).

PUSH-012, the push of the commit that holds this subsection, and the CI run on that commit are recorded by the first ledger update after it (a commit cannot contain its own id). Until then they are in the private archive and the batch report.

### Execution records

Hosts. `Windows`: the owner's Windows host, Python 3.12.10, Node 24.14.1, system Chrome 158.0.8127.37 driven by `playwright-core` 1.65.1. `Linux container`: Docker Desktop, image `verdictkit:batch3` (`sha256:d6deed1c620311d83f26c32341b49734e8405c025c6bbc186f2c5b72a8ae577c`), built during this batch, with no Python file differing from the Batch 2 commit; run with `--network none` unless stated. Neither is the Linux_Docker_Host full-checkout run that DLV-1 to DLV-4 require.

| Id | Host | What ran | Exit | Result | Class |
|---|---|---|---|---|---|
| B3-01 | Windows, Chrome | independent inspection of the live stack at 1440, 768 and 390 px: 27 scenes and 4 follow-up probes covering landing, Quote finance and lease, Reel (three demos, equity chart), all five Verify Lab scenarios, the side-by-side table, empty and error states, upload of a non-bundle, loading, rate limit, backend offline (a second gateway with a closed API port), gateway path probes; every screenshot was looked at | 0 | 0 page errors and 0 failed requests in the normal flows; the five scenarios read from the page matched the designed results; a real 429 appeared at request 121 and the page said "The backend is busy"; four presentation defects found (see "Defects found and fixed") | SUCCEEDED, defects found |
| B3-02 | Windows | `npm run typecheck`, `npm test` after the four fixes; the new and changed tests first run against the original sources | 0 | typecheck clean in 4 workspaces; 53 tests passed (ui-kit 32, portal 11, quote 6, reel 4; 49 before); on the original sources 4 of the new or changed tests failed as intended | SUCCEEDED |
| B3-03 | Windows, Chrome | re-check of the fixes on the rebuilt UI | 0 | no `/favicon.ico` request and 0 console errors; after a guided run the first result label sat at 116 px below a 57 px bar (desktop) and at 185 px below a 127 px bar (390 px), the published bar height equal to the measured one; on both demo charts 0 series points fall inside the end label's box; "not enabled" no longer shown while the lab status is pending or the backend is offline | SUCCEEDED |
| B3-04 | Windows | black-box probes of a second gateway instance: 40 hostile paths, 11 `Host` forms, 8 methods, 3 request-smuggling shapes | 0 | no hang, no escape from `dist`, foreign hosts 421; the instance still served afterwards | SUCCEEDED, no finding above NON-BLOCKER |
| B3-05 | Linux container (throwaway backend, 1 GiB cap) | API probes: malformed requests, oversize and lying `Content-Length`, archives with 4097 entries, 70 MiB declared, 400000-deep JSON, duplicate members, slot exhaustion with two stalled uploads | 0 | every archive case answered with a FAILED report in under 0.15 s, no 500; third upload 429 with `Retry-After: 5`; stalled uploads ended with 408 at 28.5 s and the slot came back; cross-site simple POST accepted (NB-1) | SUCCEEDED, NB-1 and NB-2 reproduced |
| B3-06 | Linux container (live backend, read-only) | processes, environment names, directory modes, container logs (606 lines), image environment and contents; reads and writes as `vk-examiner` | 0 | no secret in arguments, logs or image; examiner denied the signing key, vault, drafts and the API's environment and descriptors; examiner can read evidence and cannot write evidence, vault or trust stores | SUCCEEDED |
| B3-07 | Linux container (throwaway backend) | one real Quote examination, then a search of every table and column of the draft database for four claimed or recomputed figures | 0 | pre-reveal tables hold none; only the post-reveal `runs.outcome` does (NB-4) | SUCCEEDED |
| B3-08 | Kiro IDE | the four MCP tools through the IDE's MCP client, stub claim, server as it was running | 0 | `CONTRADICTED`, integrity `VERIFIED`, `REPRODUCED`, hashes equal (`547fba0c67e3bcdfa7da58b914d36dc3301b7503fb1278753bbb0eb23d9aaa79`); `contractVersion` 1.1.0 and "unsigned in v1" wording; same private directory as in Batch 2, process started 2026-11-26 00:43 | SUCCEEDED, stale server confirmed |
| B3-09 | Windows | restart attempt: the server's process tree (uv, python, python) ended after checking each id, creation time, command line and parent; then a tool call; then a timestamp-only touch of `.kiro/settings/mcp.json` | 0 | Kiro did not start a fresh server: "Not connected" at each later call; config content hash unchanged. Reconnect in the MCP Servers panel is a UI action (`_kiro/mcp/resetServer`) | BLOCKED, UNVERIFIED after restart |
| B3-10 | Windows | fresh `python -m verdictkit.mcp_server` driven by the MCP SDK client (not Kiro's integration) | 0 | `contractVersion` 1.2.0, new authenticity wording, same verdict hash, equal original and replayed hashes, repository path refused with `PATH_NOT_ALLOWED` | SUCCEEDED (outside Kiro) |
| B3-11 | Kiro IDE and Windows | hooks: agent saves of harmless `.py` files while an independent poller watched the process list, a temporary untracked pytest plugin recorded the exit status, a `.txt` save as negative control | 0 | IDE-spawned `cmd.exe /d /s /c "uv run pytest tests/contract/test_llm_fence.py -q"` with ancestry `Kiro.exe` (extension host) from `Kiro.exe`, ended after about 5.7 s; recorded exit status 0, 61 collected, 61 passed, 0 failed, parent id matching; two earlier saves gave the same records; `.txt` save started nothing | SUCCEEDED for the `llm-fence` hook |
| B3-12 | Windows | `ruff check .`; `pytest -q -m "not isolation"` with `HYPOTHESIS_PROFILE=ci` (whole repository) | 0 | all checks passed; 642 passed, 16 skipped, 4 deselected, 57.37 s | SUCCEEDED |
| B3-13 | Windows | `npm run build:portal`; `npm audit` and `npm audit --omit=dev`; `uvx pip-audit --no-deps --disable-pip` on the 51 pins exported from `uv.lock` | 0 | three builds; 0 vulnerabilities; no known vulnerabilities (the audit tool ran in a temporary environment and was not added to the project) | SUCCEEDED |
| B3-14 | Linux container | `docker build`, then `gate-startup`, `gate-isolation`, `gate-sign`, `gate-http`, `gate-case` and `verdictkit replay` | 0 | `VK_STARTUP_OK isolation=ENFORCED`; 4 passed; `GATE-SIGN PASSED` (14 checks); `GATE-HTTP PASSED`, 926 polls, canary seen, 0 key hits; case bundle sha256 `89411957149cfa67a77853073456b8f4fb000fe5a37f4b781d8e91a1bd719db4` equal to the host file's; replay `REPRODUCED`, hash `547fba0c67e3bcdfa7da58b914d36dc3301b7503fb1278753bbb0eb23d9aaa79` | SUCCEEDED |
| B3-15 | Linux container, user `vk-custodian` | `pytest tests/contract tests/api tests/integration tests/security tests/ui/test_start_scripts.py tests/ui/test_gateway.py -m "not isolation"`, the two repository-tree line-ending checks deselected as in Batch 2 | 0 | 623 passed, 15 skipped, 6 deselected, 39.45 s. A first run without the second deselection failed 1 test that reads `.gitattributes`, which the image does not contain (log kept) | SUCCEEDED |
| B3-16 | Windows | `scripts\Start-VerdictKit.ps1 -Image verdictkit:batch3 -NoBrowser` | 0 | replaced its own earlier container and gateway only; backend on 8001 because an unrelated process holds 8000 (untouched); health `1.2.0`, `ENFORCED`, judge mode; a new demonstration key | SUCCEEDED |
| B3-17 | Windows, real stack | `node tests/ui/e2e_product.cjs` against the stack on the batch 3 image, three runs (the later two after the screenshot helper was added and refined) | 0 | 105 checks passed, 0 failed, 0 browser console or page errors in each; two checks added (the first result label clears the sticky bar on desktop and at 390 px) | SUCCEEDED |
| B3-18 | Windows | secret and privacy scan of the added lines and new files, and of every tracked text file | 0 | see "Privacy check of the published outputs" below | SUCCEEDED |

### Defects found and fixed

| Defect | Where | Fix | Evidence |
|---|---|---|---|
| After a guided Verify Lab run the result scrolled under the sticky bar, hiding the heading and the first tile labels (57 px bar on desktop, 127 px when the navigation wraps) | `ui-kit/src/shell.tsx`, `theme.css` | the shell publishes the bar's measured height and the page uses it as its scroll padding; the old fixed 78 px margin is gone | B3-01 screenshots, B3-02, B3-03, the two e2e checks of B3-17 |
| `/verify` said "The demonstration lab is not enabled" while the lab status was still loading and when the backend was offline | `ui/hub/src/VerifyLab.tsx` | unknown and disabled are different states; "Checking whether the demonstration lab is enabled" or "Waiting for the backend" is shown until a definite answer | unit test, B3-03 |
| The equity chart's end label was struck through by the series line | `ui-kit/src/components.tsx` | the label sits in a right margin level with the end point, so the line cannot cross it; the start label gets a halo | unit test, geometry check in B3-03 |
| Every first page load logged a red `GET /favicon.ico 404` | the three `index.html` files | an inline brand icon (allowed by the existing `img-src data:`) | B3-03 |

No Python file, security control, contract or dependency was changed. The browser end-to-end script gained a helper that scrolls a result into view before a screenshot, and the stills in `docs/screenshots/` were regenerated; each was looked at before it was kept.

### Findings not fixed

The independent security review (`docs/SECURITY_REVIEW_BATCH3.md`) found no BLOCKER. Seven NON-BLOCKER items are reproduced and listed there with the change that would close each; twelve hypotheses were NOT REPRODUCED. Remediation was therefore limited to the four presentation defects above, as the scope required.

### Privacy check of the published outputs

Method: a pattern scan for user-profile paths, the local user name, e-mail addresses, GitHub, cloud and chat token shapes, private-key headers, credential-like assignments and vault-key assignments. It ran over the lines this batch adds (13 modified files, 4 new text files) and over all 261 tracked text files. The private archive, the private originals file of the baseline (untracked and outside every image) and the screenshots (images of the application only) are not part of the published tree.

Result. The added lines hold no match in any class. The 261 tracked files hold 13 matches that all predate this batch: 7 constructed example paths (`C:\Users\Jane`, `c:\Users\dev`, `/home/dev/`) in the next-phase design; 2 test e-mail strings and 2 credential-looking test canaries; and **one real local path that contains the Windows user name, `docs/KIRO_B7_PROMPT.md` line 9**. That last one is in frozen `master` and in tag `v1.0.0-submission` (commit `c399e36`, 2026-11-23). It was left unchanged: history cannot be rewritten under this batch's rules, so editing the branch tip would not remove it from the published record, and the file is a historical attribution record. It reveals a user name and a folder name, not a credential. No token, key or credential was found anywhere. The evidence index of the private archive is not published; the ledger and the sanitised baseline records are.
### Deviations and limits

1. The MCP restart was not done through the panel. The server's process tree was ended after checks, and Kiro did not restart it, so **the `verdictkit` server is disconnected in the IDE until Reconnect is pressed**. The post-restart calls from inside Kiro are `UNVERIFIED`; B3-10 shows what the current code answers, outside Kiro.
2. The hook exit status needed instrumentation, because `PostFileSave` output is not forwarded to the agent: a temporary untracked pytest plugin (removed; a copy is in the private archive) and a process poller. Only the `llm-fence` hook was instrumented; the other three hook commands were not.
3. The throwaway probe container and the extra gateway instances were removed after use. The live stack was restarted once, on the batch 3 image, with its own start script.
4. The scripts' default image tag stays `verdictkit:batch2`, so a judge's fresh build creates it; the batch 3 tag was used for this batch's gates and stack.
5. Kiro credits for this batch: `NOT_AVAILABLE`. The IDE's agent log has content in window 1 (see C-012) but records no usage.
6. `docs/KIRO_USAGE.md` gained a dated Batch 3 section and annotations that keep the earlier wording; `README.md` was rewritten; `docs/DEVPOST.md`, `docs/DEMO_STORYBOARD.md`, `docs/HOW_IT_WORKS.md` and `docs/SECURITY_REVIEW_BATCH3.md` are new.

### Open items and what is not verified

- A post-restart MCP call from inside Kiro, for all four tools, is `UNVERIFIED` until Reconnect is pressed on the `verdictkit` row of Kiro's MCP Servers panel.
- DLV-1 to DLV-4 stay `UNVERIFIED`: no full-checkout run on a Linux Docker host exists.
- The pass or fail of the `core-contract-tests` and `app-contract-tests` hooks inside Kiro is `UNVERIFIED`.
- The demo video is not recorded. The storyboard and checklist are in `docs/DEMO_STORYBOARD.md`.
- Public deployment stays blocked (KL-1) and was not attempted.
- Kiro credits for this batch: `NOT_AVAILABLE`.

## Capability register

| Capability | Status |
|---|---|
| Frozen release refs unchanged | SUCCEEDED (checked at start; recheck at end required by Requirement 14.14) |
| Hook execution inside Kiro | UNVERIFIED |
| Kiro MCP calls | SUCCEEDED in the historical record (E-101); not repeated in this phase |
| Browser E2E | UNVERIFIED |
| Public demonstration | UNVERIFIED (none exists) |
| Signed bundles (Ed25519, signer trust, offline verification) | IMPLEMENTED in Accelerated Batch 1; verified by B1-05, B1-06, B1-10, B1-14 (container) and B1-16/B1-17 (mutations). Contract 1.2.0 covers only the authenticity change. |
| Plugin SDK, regulatory expansion | not implemented |

### Capability register, Batch 2 update

The table above is the historical record and is not edited. These rows supersede it where they differ.

| Capability | Batch 2 status |
|---|---|
| Hook execution inside Kiro | PARTIALLY OBSERVED (B2-18): the IDE spawned the `llm-fence` and `core-contract-tests` commands after agent saves; hook pass or fail is `UNVERIFIED` because `PostFileSave` output is not forwarded |
| Kiro MCP calls | SUCCEEDED (B2-17) for all four tools, with the stale-server finding recorded above |
| Browser E2E | SUCCEEDED (B2-14, B2-15): 103 checks against the real Docker stack on the final image |
| Unified portal, signed-bundle verification in the browser, one-command start | IMPLEMENTED and verified by B2-14 to B2-16; routes and operation in `docs/PRODUCT_TOUR.md` and `docs/DEMO_LAB.md` |
| BE-2 | root cause measured (B2-01, B2-02) and fixed (B2-03, B2-04); a Linux per-test run from a full checkout is still missing |
| Public demonstration | UNVERIFIED (none exists, none authorized) |

### Capability register, Batch 3 update

The two tables above are the historical record and are not edited. These rows supersede them where they differ.

| Capability | Batch 3 status |
|---|---|
| Hook execution inside Kiro | OBSERVED with an exit status for the `llm-fence` hook (B3-11): IDE-spawned command, ancestry recorded, exit status 0, 61 of 61 passed. The other three hook commands were not instrumented: `UNVERIFIED` |
| Kiro MCP calls | SUCCEEDED for all four tools before any restart (B3-08), with the stale server confirmed. After a restart: `UNVERIFIED` (B3-09); the server is disconnected until Reconnect is pressed in the MCP Servers panel. Current code checked outside Kiro (B3-10) |
| Browser E2E | SUCCEEDED (B3-17): 105 checks, 0 console errors, three runs on the batch 3 stack |
| Release gates on the batch 3 image | SUCCEEDED (B3-14, B3-15): startup, isolation, signed bundles, judge-mode HTTP lifecycle, case and replay; Python suite as the custodian user |
| Independent security review | no BLOCKER; 7 NON-BLOCKER, 12 NOT REPRODUCED (`docs/SECURITY_REVIEW_BATCH3.md`) |
| Dependency audits | `npm audit` 0 vulnerabilities; `pip-audit` no known vulnerabilities (B3-13) |
| Demonstration video | not recorded; storyboard and checklist in `docs/DEMO_STORYBOARD.md` |
| Public demonstration | UNVERIFIED (none exists, none authorized) |

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
| C-009 | Capability register row "Signed bundles, plugin SDK, regulatory expansion" | `not implemented` | Split into one row for signed bundles (`IMPLEMENTED` in Accelerated Batch 1) and one for the plugin SDK and regulatory expansion (`not implemented`) | Batch 1 implemented signed bundles. The old row would now be false. The section above it is unchanged. |
| C-010 | `KIRO_USAGE.md`, Batch 2 section | "with a one-file change in the engine package" | One modified file (`core/src/verdictkit/api/server.py`) and one new module (`api/demo_lab.py`) | `git diff --name-status f42a6d0 78f3f58 -- core` lists exactly those two. The ledger's own deviation 2 of Batch 2 already said so. |
| C-011 | `KIRO_USAGE.md`, Summary and Open items (statements dated 2026-11-24) | "No Kiro agent-hook run and no Kiro MCP tool call has been observed in any Kiro session" and the two matching open items | Wording kept, each marked "as of 2026-11-24" and superseded, pointing to Batch 2 and Batch 3 | B2-17, B2-18, B3-08, B3-11. The 2026-11-24 statements were true when written; read as present tense they are not. |
| C-012 | Batch 2 ledger paragraph "Private evidence archive" and the archive's `unavailable` entry for the IDE logs | "the IDE's own hook and MCP log files for this run are 0 bytes" | Window 1's logs are not empty: `Kiro Logs.log` 41,994 bytes (last written 2026-11-26 22:09:32) and `Kiro - MCP Logs.log` 332 bytes (last written 00:43:50). Window 2's are 0 bytes. They record hook loading at session start and the server's connection, and no hook or tool-call outcome | Read in Batch 3; neither file changed after the Batch 2 archive was made, so the earlier statement probably read window 2. The private Batch 2 index is left as it was. |

## Accepted baseline exceptions

| ID | Defect | Host | Remediation required before final release |
|---|---|---|---|
| BE-1 | `tests/contract/test_mcp_server.py::test_verify_replay_and_explain_roundtrip` asserts POSIX mode `0o700` | Windows | Preserve the Linux permission assertion. Design Windows-appropriate security handling (for example an access-control check). Do not remove the assertion. |
| BE-2 | `tests/ui/test_judge_preview.py::JudgePreviewTests::test_case_outcome_get_to_offline_backend` times out | Windows | Instrument, establish the root cause, fix the cause. A longer timeout alone is not a fix. |

Batch 2 status of the exceptions. BE-1: unchanged (remediated in Batch 1). BE-2: the cause is measured (a refused loopback connect takes 2.02 to 2.07 s on the Windows host and under 13 ms on a Linux kernel, B2-01 and B2-02) and fixed in the bridge by a separate connect bound, without touching the test or its timeout (B2-03, B2-04). The remaining gap is a Linux per-test run from a full checkout.

Batch 3 status of the exceptions. B3-12 ran the whole Windows suite with 0 failures, so neither BE-1 nor BE-2 reproduces on the final tree. For BE-2 the missing piece is still a Linux per-test run from a full checkout (DLV-1 to DLV-4, UNVERIFIED).
