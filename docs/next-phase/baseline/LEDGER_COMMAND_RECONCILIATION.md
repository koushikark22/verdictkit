# Ledger command reconciliation (baseline)

Purpose: map each baseline ledger entry in `EXECUTION_EVIDENCE.md` to its canonical raw record in `baseline/EXECUTION_INDEX.md`, and show the exact command that was recorded. This is a documentation reconciliation made on 2026-11-25. It is not an Execution_Record and runs nothing (finding L-4 of the independent review, design D8.5).

Source of the commands: the sanitized record files `baseline/records.sanitized.jsonl` (R) and `baseline/records-first-pass-overlapping.jsonl` (F). Line n of a file is record R n or F n. Placeholders `<REPO>`, `<TEMP>` and `<USERPROFILE>` replace local paths (`EVIDENCE_REDACTION.md`). The original of `records.jsonl` is private.

## Result

- 27 ledger rows (E-001 to E-026, with E-025 split into E-025a and E-025b) map to 26 canonical records. E-027 and E-028 were not run and have no record.
- Seconds and UTC start time of every ledger row equal the canonical record (seconds to one decimal, start to the second). 0 mismatches.
- Seven ledger rows state their command in abbreviated form (`...`, `<gate>` or "Hook_Set command"): E-009, E-012, E-013, E-014, E-020, E-023, E-024. The exact command is in the table below. The ledger text is not rewritten; correction C-007 points here.
- E-025a and E-025b come from one run (R27). Its recorded exit code is the exit code of `tail`, not of pytest, so it is not a test result (correction C-002). The same holds for the discarded invocations R25 and R26.
- The ledger rows carry no Execution_Index identifier. The "Record" column below supplies it. Requirement 3.12 asks for it in every new Execution_Record.

## BE-2 attribution wording

The failure of `test_case_outcome_get_to_offline_backend` was observed on a Windows host in two runs (E-004 and E-005). No Linux per-test run exists: the combined run R27 is invalid for that file because `ui/` is not in the image. The ledger and report call BE-2 a "Windows" exception. Until a Linux per-test run from a full checkout exists, read that as "observed on Windows". Attribution to the Windows host is UNVERIFIED and the root cause is not established (requirements 1.12 and 1.19, design D8.5).

## Table

| Ledger | Record | Exact command as recorded (sanitized) | Exit (record) | Seconds | Start (UTC) | Ledger text abbreviated | Note |
|---|---|---|---|---|---|---|---|
| E-001 | R1 | `uv lock --check` | 0 | 0.1 | 16:39:06 | no |  |
| E-002 | F2 | `uv sync --frozen --all-packages --all-extras --group dev` | 0 | 0.1 | 16:36:09 | no |  |
| E-003 | R2 | `uv run --no-sync ruff check .` | 0 | 0.1 | 16:39:06 | no |  |
| E-004 | F4 | `uv run --no-sync pytest -q -p no:cacheprovider -m "not isolation" -rfEs` | 1 | 71.4 | 16:36:13 | no |  |
| E-005 | F5 | `uv run --no-sync pytest -q -p no:cacheprovider tests/ui/test_judge_preview.py` | 1 | 4.7 | 16:37:41 | no |  |
| E-006 | R3 | `uv run --no-sync pytest -q -p no:cacheprovider tests/contract -m "not isolation" -rfEs` | 1 | 27.1 | 16:39:06 | no |  |
| E-007 | R4 | `uv run --no-sync pytest -q -p no:cacheprovider tests/api/test_m3b_intake_boundary.py tests/api/test_m3b_draft_store.py tests/api/test_m3b_http_drafts.py tests/api/test_m3a_transport.py tests/api/test_m3b_freeze_boundary.py tests/api/test_m3b_evidence_boundary.py tests/api/test_m3b_examination_boundary.py tests/api/test_m3b_examiner_identity.py tests/api/test_http_run_lifecycle.py -rs` | 0 | 8.6 | 16:39:33 | no |  |
| E-008 | R5 | `uv run --no-sync pytest -q -p no:cacheprovider tests/api/test_startup_gate.py tests/contract/test_examiner_attestation.py -rs` | 0 | 3.8 | 16:39:42 | no |  |
| E-009 | R6 | `uv run --no-sync pytest -q -p no:cacheprovider tests/contract/test_mcp_server.py tests/integration/test_quote_b7_texas.py -k mcp -rfs` | 1 | 5.4 | 16:39:46 | yes |  |
| E-010 | R7 | `uv run --no-sync pytest -q -p no:cacheprovider tests/contract/test_llm_fence.py` | 0 | 2.6 | 16:39:51 | no |  |
| E-011 | R8 | `uv run --no-sync pytest -q -p no:cacheprovider -m isolation --collect-only` | 0 | 5.8 | 16:39:54 | no |  |
| E-012 | R10 | `uv run --no-sync pytest tests/contract -q -x -m "not isolation" --ignore=tests/contract/test_reel_contract.py --ignore=tests/contract/test_quote_contract.py -p no:cacheprovider` | 1 | 12.4 | 16:40:14 | yes |  |
| E-013 | R13 | `uv run --no-sync pytest tests/contract/test_reel_contract.py -q -x -p no:cacheprovider` | 0 | 13.2 | 16:40:26 | yes |  |
| E-014 | R14 | `uv run --no-sync pytest tests/contract/test_quote_contract.py -q -x -p no:cacheprovider` | 0 | 3.9 | 16:40:45 | yes |  |
| E-015 | R15 | `npm ci` | 0 | 13.1 | 16:41:19 | no |  |
| E-016 | R16 | `npm run typecheck` | 0 | 6.9 | 16:41:35 | no |  |
| E-017 | R17 | `npm test` | 0 | 10.3 | 16:41:46 | no |  |
| E-018 | R18 | `npm run build` | 0 | 10.0 | 16:42:00 | no |  |
| E-019 | R19 | `docker build -t verdictkit:next-baseline .` | 0 | 25.1 | 16:42:45 | no |  |
| E-020 | R20 | `docker run --rm --network none -v <TEMP>\vk-gate:/out verdictkit:next-baseline gate-isolation /out/isolation.xml` | 0 | 2.6 | 16:43:15 | yes |  |
| E-021 | R21 | `docker run --rm --network none verdictkit:next-baseline gate-startup` | 0 | 0.8 | 16:43:22 | no |  |
| E-022 | R22 | `docker run --rm --network none verdictkit:next-baseline gate-http` | 0 | 2.6 | 16:43:26 | no |  |
| E-023 | R23 | `docker run --rm --network none -v <TEMP>\vk-gate:/out -v <REPO>\examples\stub_claimtype:/in:ro verdictkit:next-baseline gate-case /in/claim.json /out/stub.vkb` | 0 | 1.0 | 16:43:34 | yes |  |
| E-024 | R24 | `docker run --rm --network none -v <TEMP>\vk-gate:/out:ro verdictkit:next-baseline verdictkit replay /out/stub.vkb` | 0 | 0.8 | 16:43:40 | yes |  |
| E-025a | R27 | `docker run --rm --network none -e PYTHONDONTWRITEBYTECODE=1 --entrypoint sh verdictkit:next-baseline -c "cd /app && /app/.venv/bin/pytest -p no:cacheprovider -q tests/contract/test_mcp_server.py tests/ui/test_judge_preview.py 2>&1 \| tail -8"` | 0 | 3.8 | 16:44:07 | no | exit of tail, not pytest (recorded exit not a test result) |
| E-025b | R27 | `docker run --rm --network none -e PYTHONDONTWRITEBYTECODE=1 --entrypoint sh verdictkit:next-baseline -c "cd /app && /app/.venv/bin/pytest -p no:cacheprovider -q tests/contract/test_mcp_server.py tests/ui/test_judge_preview.py 2>&1 \| tail -8"` | 0 | 3.8 | 16:44:07 | no | exit of tail, not pytest (recorded exit not a test result) |
| E-026 | R28 | `npm install --no-save playwright@1.63.0` | 0 | 4.8 | 16:44:36 | no |  |

E-027 (browser E2E) and E-028 (`scripts/gate_nov22.sh`) were not run: UNVERIFIED, no record.
