# Canonical execution index

Purpose: reconcile the two raw record files into one index without altering either. Both raw files are preserved byte for byte.

| Raw file | SHA-256 | Lines |
|---|---|---|
| `baseline/records.jsonl` (`R`) | `828d336960a1e7787b6d41d6bacb03cb7e80e5e6367c784025c2d5b4cbd35ea4` | 28 |
| `baseline/records-first-pass-overlapping.jsonl` (`F`) | `5cee53f557544a2e220a89ab0abbc8569f0f7d2a0aff61c06d48a56b7b1dd4ba` | 17 |

Per-step logs under `baseline/logs/` are named by step. When two executions of one step ran at overlapping times, the later write replaced the earlier log. A log therefore belongs to the execution that wrote it last. Log SHA-256 values are listed in `docs/next-phase/baseline/LOG_HASHES.txt`.

## Status vocabulary

| Status | Meaning |
|---|---|
| CANONICAL | The execution whose result the ledger and baseline report use. Its log (where one exists) was written by that execution. |
| SUPERSEDED_DUPLICATE | A completed execution of the same step that is not used. Its result agreed with the canonical one or its log did not survive. Kept for the record. |
| EXECUTION_ERROR | The runner collided with another execution on the log file and wrote no result of the command. The recorded `exit` is the runner's, not a test result. Not a test failure and not an Outcome_Class. |
| EXECUTION_ERROR_WRONG_INVOCATION | The command was invoked incorrectly (tool not found), so no test ran. |

Rule for choosing CANONICAL: the completed execution whose log file survives; where no log survives, the only completed execution.

## Index

| Step | Source | Start (UTC) | Recorded exit | Seconds | Status | Note |
|---|---|---|---|---|---|---|
| uv-lock-check | F1 | 16:36:09 | 0 | 0.1 | SUPERSEDED_DUPLICATE | |
| uv-lock-check | R1 | 16:39:06 | 0 | 0.1 | CANONICAL | |
| uv-sync | F2 | 16:36:09 | 0 | 0.1 | CANONICAL | only execution |
| ruff | F3 | 16:36:09 | 0 | 0.1 | SUPERSEDED_DUPLICATE | |
| ruff | R2 | 16:39:06 | 0 | 0.1 | CANONICAL | |
| pytest-full-not-isolation | F4 | 16:36:13 | 1 | 71.4 | CANONICAL | 2 failed (F1, F2) |
| pytest-judge-preview-rerun | F5 | 16:37:41 | 1 | 4.7 | CANONICAL | F2 reproduced |
| pytest-contract | F11 | 16:37:54 | 1 | 31.1 | SUPERSEDED_DUPLICATE | concurrent with another loop; log overwritten |
| pytest-contract | F6 | 16:38:02 | 1 | 0 | EXECUTION_ERROR | lock collision, no test result |
| pytest-contract | R3 | 16:39:06 | 1 | 27.1 | CANONICAL | 259 passed, 1 failed (F1) |
| pytest-api-safety-m3b | F7 | 16:38:02 | 0 | 9 | SUPERSEDED_DUPLICATE | |
| pytest-api-safety-m3b | F13 | 16:38:25 | 0 | 8.3 | SUPERSEDED_DUPLICATE | |
| pytest-api-safety-m3b | R4 | 16:39:33 | 0 | 8.6 | CANONICAL | 63 passed, 5 skipped |
| pytest-startup-attestation | F8 | 16:38:11 | 0 | 3.4 | SUPERSEDED_DUPLICATE | |
| pytest-startup-attestation | F14 | 16:38:34 | 0 | 3.5 | SUPERSEDED_DUPLICATE | |
| pytest-startup-attestation | R5 | 16:39:42 | 0 | 3.8 | CANONICAL | 16 passed |
| pytest-mcp | F9 | 16:38:15 | 1 | 6.3 | SUPERSEDED_DUPLICATE | |
| pytest-mcp | F15 | 16:38:37 | 1 | 6 | SUPERSEDED_DUPLICATE | |
| pytest-mcp | R6 | 16:39:46 | 1 | 5.4 | CANONICAL | 13 passed, 1 failed (F1) |
| pytest-llm-fence | F10 | 16:38:21 | 0 | 2.4 | SUPERSEDED_DUPLICATE | |
| pytest-llm-fence | F16 | 16:38:43 | 0 | 2.8 | SUPERSEDED_DUPLICATE | |
| pytest-llm-fence | R7 | 16:39:51 | 0 | 2.6 | CANONICAL | 58 passed |
| pytest-isolation-collect | F12 | 16:38:24 | 0 | 5 | SUPERSEDED_DUPLICATE | |
| pytest-isolation-collect | F17 | 16:38:46 | 0 | 5.4 | SUPERSEDED_DUPLICATE | |
| pytest-isolation-collect | R8 | 16:39:54 | 0 | 5.8 | CANONICAL | 4 collected |
| hookcmd-core | R10 | 16:40:14 | 1 | 12.4 | CANONICAL | 159 passed, 1 failed (F1) |
| hookcmd-core | R9 | 16:40:25 | 1 | 0 | EXECUTION_ERROR | lock collision with R10 |
| hookcmd-reel | R11 | 16:40:26 | 1 | 0 | EXECUTION_ERROR | lock collision with R13 |
| hookcmd-reel | R13 | 16:40:26 | 0 | 13.2 | CANONICAL | 13 passed |
| hookcmd-quote | R12 | 16:40:26 | 0 | 4.1 | SUPERSEDED_DUPLICATE | log overwritten by R14 |
| hookcmd-quote | R14 | 16:40:45 | 0 | 3.9 | CANONICAL | 8 passed (2.11 s pytest) |
| npm-ci | R15 | 16:41:19 | 0 | 13.1 | CANONICAL | |
| npm-typecheck | R16 | 16:41:35 | 0 | 6.9 | CANONICAL | |
| npm-test | R17 | 16:41:46 | 0 | 10.3 | CANONICAL | 19 passed |
| npm-build | R18 | 16:42:00 | 0 | 10.0 | CANONICAL | |
| docker-build | R19 | 16:42:45 | 0 | 25.1 | CANONICAL | |
| gate-isolation | R20 | 16:43:15 | 0 | 2.6 | CANONICAL | 4 passed |
| gate-startup | R21 | 16:43:22 | 0 | 0.8 | CANONICAL | |
| gate-http | R22 | 16:43:26 | 0 | 2.6 | CANONICAL | |
| gate-case | R23 | 16:43:34 | 0 | 1.0 | CANONICAL | |
| gate-replay | R24 | 16:43:40 | 0 | 0.8 | CANONICAL | |
| linux-win-failures | R25 | 16:43:48 | 0 | 0.4 | EXECUTION_ERROR_WRONG_INVOCATION | `pytest: not found`; recorded exit is of `tail` |
| linux-win-failures | R26 | 16:43:54 | 0 | 0.4 | EXECUTION_ERROR_WRONG_INVOCATION | `No module named pytest` under system python; recorded exit is of `tail` |
| linux-win-failures | R27 | 16:44:07 | 0 | 3.8 | CANONICAL (partial evidence) | summary `4 failed, 10 passed`. Recorded exit is of `tail`; the pytest exit code was not captured |
| playwright-install | R28 | 16:44:36 | 0 | 4.8 | CANONICAL | `npm install --no-save` |

## Totals

- 45 raw execution records: 28 in R and 17 in F.
- 26 CANONICAL (one per distinct step), 14 SUPERSEDED_DUPLICATE, 3 EXECUTION_ERROR (F6, R9, R11) and 2 EXECUTION_ERROR_WRONG_INVOCATION (R25, R26).
- The 5 execution-error records are not test failures and are excluded from every pass or fail count.
- Counts of passed, failed and skipped tests in the ledger and the baseline report come only from CANONICAL rows.