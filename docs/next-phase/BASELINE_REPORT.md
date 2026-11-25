# Baseline report

Phase branch `feature/kiro-next-phase`, commit `84df25c68198e496889b5892a03555ec7d2d860a`. Run date 2026-11-24. Host: Windows, PowerShell, Python 3.12.10, uv 0.13.9, Node 24.14.1, npm 11.11.0, git 2.51.0. Docker Desktop 29.9.3 (Linux engine, `linux/amd64`) was run through `C:\Program Files\Docker\Docker\resources\bin\docker.exe`, which is not on `PATH`.

Raw command records: `docs/next-phase/baseline/records.jsonl`. Raw output: `docs/next-phase/baseline/logs/`. Full ledger: `EXECUTION_EVIDENCE.md`. No application code was changed.

## 1. Repository state

| Check | Result |
|---|---|
| Current branch | `feature/kiro-next-phase` (SUCCEEDED) |
| HEAD | `84df25c68198e496889b5892a03555ec7d2d860a` |
| `master` | `84df25c68198e496889b5892a03555ec7d2d860a` |
| Tag `v1.0.0-submission` (annotated) | tag object `e9ca8d2bac4a65483f3a7357e00600a1210a6f4f`, peeled commit `84df25c68198e496889b5892a03555ec7d2d860a` |
| Tag `verified-quote-e2e-20261118` (lightweight) | commit `407478be97a8979a8e3555bba3b3ab302229f91d` ("Baseline: verified VerdictKit core and autopsy adapters", 2026-11-18), an ancestor of `84df25c`. **Correction:** an earlier version of this report said this tag resolves to `84df25c`. That was wrong. The first check looked only at the first tag. |
| Working tree before the baseline run | only `?? .kiro/specs/verdictkit-next-phase/` |
| Working tree after the baseline run | the same, plus the new `docs/next-phase/` files. `npm ci` and `npm install --no-save` wrote only to `node_modules`, which is ignored by git. |

## 2. Results

Outcome classes: SUCCEEDED (exit 0 in this phase), FAILED (non-zero exit), UNVERIFIED (not run).

| # | Step | Command | Result | Counts | Seconds | Class |
|---|---|---|---|---|---|---|
| 1 | Lockfile | `uv lock --check` | exit 0, "Resolved 56 packages" | n/a | 0.1 | SUCCEEDED |
| 2 | Sync | `uv sync --frozen --all-packages --all-extras --group dev` | exit 0 | n/a | 0.1 | SUCCEEDED |
| 3 | Lint | `uv run --no-sync ruff check .` | exit 0, "All checks passed!" | n/a | 0.1 | SUCCEEDED |
| 4 | Full Python regression | `HYPOTHESIS_PROFILE=ci uv run --no-sync pytest -q -m "not isolation"` | exit 1 | 444 passed, 2 failed, 5 skipped, 4 deselected | 71.4 (pytest 64.35) | FAILED (2 Windows-host failures, section 3) |
| 5 | Contract suite | `pytest tests/contract -m "not isolation"` | exit 1 | 259 passed, 1 failed, 4 deselected | 27.1 | FAILED (one Windows-host failure) |
| 6 | API safety (CI list) | nine `tests/api/` files from `m3b-api-checks.yml` and `p0-integration.yml` | exit 0 | 63 passed, 5 skipped | 8.6 | SUCCEEDED |
| 7 | Startup gate and attestation | `tests/api/test_startup_gate.py tests/contract/test_examiner_attestation.py` | exit 0 | 16 passed | 3.8 | SUCCEEDED |
| 8 | MCP tests | `tests/contract/test_mcp_server.py tests/integration/test_quote_b7_texas.py -k mcp` | exit 1 | 13 passed, 1 failed, 13 deselected | 5.4 | FAILED (same Windows-host failure) |
| 9 | LLM fence | `tests/contract/test_llm_fence.py` | exit 0 | 58 passed | 2.6 | SUCCEEDED |
| 10 | Isolation tests (collection only) | `pytest -m isolation --collect-only` | exit 0 | 4 of 455 collected | 5.8 | SUCCEEDED (collection) |
| 11 | Hook command: llm-fence | step 9 command | exit 0 | 58 passed | 2.6 | SUCCEEDED |
| 12 | Hook command: core | `pytest tests/contract -q -x -m "not isolation" --ignore=...reel --ignore=...quote` | exit 1 | 159 passed, 1 failed (stopped at first failure) | 12.4 | FAILED (same Windows-host failure) |
| 13 | Hook command: reel | `pytest tests/contract/test_reel_contract.py -q -x` | exit 0 | 13 passed | 13.2 | SUCCEEDED |
| 14 | Hook command: quote | `pytest tests/contract/test_quote_contract.py -q -x` | exit 0 | 8 passed | 3.9 | SUCCEEDED |
| 15 | UI install | `npm ci` | exit 0 | n/a | 13.1 | SUCCEEDED |
| 16 | UI typecheck | `npm run typecheck` | exit 0 | n/a | 6.9 | SUCCEEDED |
| 17 | UI unit tests | `npm test` | exit 0 | 19 passed (9 + 6 + 4) in 3 workspaces | 10.3 | SUCCEEDED |
| 18 | UI build | `npm run build` | exit 0 | n/a | 10.0 | SUCCEEDED |
| 19 | Browser E2E | `bash scripts/ui_e2e.sh` | not run | n/a | n/a | UNVERIFIED (section 4) |
| 20 | Docker build | `docker build -t verdictkit:next-baseline .` | exit 0 | n/a | 25.1 | SUCCEEDED |
| 21 | `gate-isolation` | `docker run --rm --network none ... gate-isolation` | exit 0 | 4 passed | 2.6 | SUCCEEDED |
| 22 | `gate-startup` | `docker run --rm --network none ... gate-startup` | exit 0, printed `VK_STARTUP_OK isolation=ENFORCED` | n/a | 0.8 | SUCCEEDED |
| 23 | `gate-http` | `docker run --rm --network none ... gate-http` | exit 0, "GATE-HTTP PASSED" | n/a | 2.6 | SUCCEEDED |
| 24 | `gate-case` | `docker run --rm --network none ... gate-case /in/claim.json /out/stub.vkb` | exit 0, bundle written | n/a | 1.0 | SUCCEEDED |
| 25 | Offline replay | `docker run --rm --network none ... verdictkit replay /out/stub.vkb` | exit 0, integrity `VERIFIED`, reproducibility `REPRODUCED`, authenticity `NOT_ESTABLISHED` | n/a | 0.8 | SUCCEEDED |
| 26 | `scripts/gate_nov22.sh` | `bash scripts/gate_nov22.sh` | not run | n/a | n/a | UNVERIFIED |

Skipped tests in step 4 (5): `test_m3b_draft_store.py:80` (symlinks unavailable on this platform) and four in `test_m3b_examiner_identity.py` (Linux peer credentials). The Linux peer-credential tests are covered on Linux by `gate-isolation` and `gate-http`, but those tests as written were not run as pytest cases on Linux in this phase. They remain UNVERIFIED as Linux pytest cases.

Execution index: the shell tool re-executed some commands, which produced duplicate and overlapping records. `docs/next-phase/baseline/EXECUTION_INDEX.md` is the canonical index. It maps all 45 raw records (28 in `records.jsonl`, 17 in `records-first-pass-overlapping.jsonl`) to 26 canonical executions, 14 superseded duplicates and 5 execution errors. Both raw files and all logs are preserved unchanged, and their SHA-256 values are in the index and in `baseline/LOG_HASHES.txt`. The 5 execution-error records (3 log-file lock collisions, 2 wrong invocations) are not test failures. Every count in this report comes from a canonical row.

## 3. Failures, diagnosis and host attribution

No application code was changed to resolve any failure. Both failures are recorded as Pre_Existing_Defect on the Windows host.

### F1. `tests/contract/test_mcp_server.py::test_verify_replay_and_explain_roundtrip`

- Failure: assertion at `tests/contract/test_mcp_server.py:30`, `oct(bundle.parent.stat().st_mode & 0o777) == "0o700"` fails with `0o777` on Windows.
- Cause: `Path.chmod(0o700)` does not set POSIX permission bits on Windows.
- Evidence of attribution: the historical Linux run in image `verdictkit:submission` records this test as passed (`FINAL_KIRO_VERIFICATION.md`, section B). In this phase a combined run of `tests/contract/test_mcp_server.py` and `tests/ui/test_judge_preview.py` in the freshly built image printed `4 failed, 10 passed`. The four named failures are all in the judge-preview file (`ui/` is not in the image). No failure from `test_mcp_server.py` was listed. This is indirect evidence: no per-test listing and no pytest exit code were captured (section 7).
- Effect: the failure stops the test before its replay and explain steps, so on Windows those steps are not exercised by this test. It also fails three Hook_Set-related runs (steps 5, 8 and 12) and the core hook command.
- Status: ACCEPTED_BASELINE_EXCEPTION BE-1 (documented pre-existing Windows platform defect, accepted for baseline continuation only). Mandatory remediation before the final next-phase release: keep the Linux permission assertion and add platform-appropriate Windows security handling. Removing or weakening the assertion is not permitted.
- Linux evidence is indirect (section 7). The historical audit recorded a pass of this test in the image `verdictkit:submission`. This phase did not capture a per-test pass in Linux.

### F2. `tests/ui/test_judge_preview.py::JudgePreviewTests::test_case_outcome_get_to_offline_backend`

- Failure: `TimeoutError: timed out` in `http.client` waiting for a response, client timeout 2 seconds.
- Reproduction: failed again when run alone (7 passed, 1 failed, 2.67 s).
- Cause: NOT ESTABLISHED. Working hypothesis only: the test points the preview server at a closed local port (65534) and expects an immediate 502, and a connection to a closed local port on Windows may take longer than the test's 2-second client timeout. No trace, timing instrumentation or Linux comparison run exists. An increased timeout alone would not be a verified fix.
- Evidence of attribution: the test was not reported as failing in the historical audit. In the Linux image run its name does not appear in the failure list, which suggests but does not show a pass (section 7). The `ui/` directory absence in the image affects other tests in the same file.
- Status: ACCEPTED_BASELINE_EXCEPTION BE-2 (provisional): a reproducible pre-existing Windows failure whose root cause is not established. Mandatory remediation before the final next-phase release: add instrumentation, establish the root cause on Windows and on Linux from a full checkout, and fix the cause. A longer timeout alone is not accepted as a fix.
- This defect is not in the frozen documentation or in the historical audit.

## 4. Unverified items and reasons

| Item | Reason | What would verify it |
|---|---|---|
| Browser E2E (`scripts/ui_e2e.sh`, `tests/ui/e2e_browser.cjs`) | The script requires Linux tools (`setsid`, `/dev/tcp`) and TCP port 8000, which is held by `splunkd.exe` (PID 5780) on this host. The script refuses a stale server on 8000, 4173 or 4174, and stopping an unrelated service was out of scope. Playwright 1.63.0 was installed with `--no-save` and Chromium builds exist in the local cache, so only the port and shell constraints block it. | Run on a Linux CI runner, or on this host with port 8000 free and Linux tooling. |
| `scripts/gate_nov22.sh` | Same shell and Docker-in-script dependencies; not attempted. | Linux runner. |
| Linux execution of the five skipped tests | They skip on Windows. | Linux pytest run from a full checkout. |
| Hook execution inside Kiro | See `HISTORICAL_EVIDENCE_RECONCILIATION.md` H8. | A trusted workspace, an agent edit, and the Kiro log. |
| Public deployment | No deployment exists in this phase. | Phase work (P1). |
| Credits used by this phase | No usage record is available to the agent. | Kiro usage view. |

## 5. Comparison with the historical record

| Historical record | This phase |
|---|---|
| Linux image tests: `27 passed` for `test_mcp_server.py` plus `test_quote_b7_texas.py` | Not repeated in full. Linux MCP test file ran: no MCP failures. |
| Windows MCP failure `0o777 != 0o700` | Reproduced at the same assertion. |
| Terminal preflight of hook commands: llm-fence 58, quote 8, reel 13, core 1 failed 159 passed | Reproduced exactly: 58, 8, 13, 159 passed and 1 failed. |

## 6. Maintainer decisions (independent review, recorded)

- BE-1 (F1) is accepted as a documented pre-existing Windows platform defect, for baseline continuation only.
- BE-2 (F2) is provisionally accepted as a reproducible pre-existing Windows failure. The root cause is not established.
- Both remain mandatory remediation items before the final next-phase release. They are the only accepted baseline exceptions. Any other failing test, on any host, is a new regression and is not permitted.
- Outstanding verification items, not resolved by this baseline: Browser E2E, `scripts/gate_nov22.sh`, the five skipped Linux cases, and automatic Kiro hook execution.
- Port 8000 is held by `splunkd.exe` on this host. That process is not to be stopped. Local test ports must be configurable by design.

## 7. Limits of the indirect Linux per-test evidence

- The Linux comparison for F1 and F2 comes from one combined `pytest` run in the image (execution R27). Its summary was `4 failed, 10 passed`.
- The command ended in a pipeline through `tail`. The recorded exit code is the exit code of `tail`, not of pytest. No pytest exit code was captured.
- No `-v` or `-rA` listing was captured, so no per-test pass is recorded. A pass is inferred only from a test's absence from the four named failures.
- The count of tests per file was not recorded for the combined run, so the split of 10 passes between the two files is not established.
- The two earlier attempts (R25, R26) did not run pytest and are execution errors.
- The image does not contain `ui/`, so the judge-preview results from the image are an invalid environment for that file and do not support or contradict F2.
- Consequently the Linux behaviour of F1 and F2 is `UNVERIFIED` in this phase. It must be re-established with a per-test listing (`-rA`) and a captured pytest exit code, from a full Linux checkout.
