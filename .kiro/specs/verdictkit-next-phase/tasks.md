# Implementation Plan: VerdictKit Next Phase

## Overview

This plan turns `.kiro/specs/verdictkit-next-phase/design.md` into coding and test tasks for `.kiro/specs/verdictkit-next-phase/requirements.md`. It has seven phases. Phases 1 to 6 each end in a checkpoint, and Phase 7 ends in the final release report (PH7-18). All work happens on the Phase_Branch `feature/kiro-next-phase`, from the baseline commit `84df25c68198e496889b5892a03555ec7d2d860a`.

Status: Task PH1-01 (start-of-phase preflight, read-only) is complete. Its box is ticked and its records E-201 to E-222 are in `docs/next-phase/EXECUTION_EVIDENCE.md`. No other task has started, so every other box is unchecked and nothing else is implemented or verified. This revision applies the independent task-plan review (31 findings, TPR-C-1 to TPR-L-5, design D10.11). It changes documentation only. It is DESIGNED and UNVERIFIED. The owner recorded OA-00 as `ACCEPTED_WITH_CONDITIONS` on 2026-11-26 and froze the scope of the enhanced release (section "Scope freeze" below, design D10.12, `docs/next-phase/OWNER_DECISIONS.md`). That acceptance makes nothing implemented or verified.

Execution-evidence rule. A box is ticked only when the Execution_Record for that task shows every linked criterion SUCCEEDED (4.9). A box is never ticked without evidence. A criterion that several tasks verify in parts is judged for each task by that task's acceptance tests. The track record at the phase checkpoint (4.4) judges the whole criterion. A row that has a Windows leg and a Linux leg is two rows (D10.11 TR-1). The Windows leg and every row that the agent runs on the Windows host or on a reachable Linux_Docker_Host are autonomous completion rows, and only they decide a task's box and every later dependency. A Linux full-checkout leg is a deferred row (DLV-1 to DLV-4 in the Notes). It stays UNVERIFIED until a `SUCCEEDED` record that names a Linux source exists, it blocks no box of Phases 1 to 6, it is a mandatory release gate that PH7-17 runs again on S, and a deferred row that fails unticks its task in the same change as the `FAILED` record. A Windows result never sets a deferred row. A row that needs an owner action stays UNVERIFIED until the owner's record exists. It blocks a box only where the task names the OA id in Depends on. An owner item is `OPEN`, `PROVIDED` or `NOT_PROVIDED` (D10.11 TR-8). A GATE item (OA-00, OA-07a, OA-08 for the tasks that name it, and OA-09) must be `PROVIDED` before a task that names it starts. An EVIDENCE item may be `NOT_PROVIDED`, which keeps its rows `UNVERIFIED` and its blockers open. The agent never writes an owner record and never approves its own hashes.

Environment legend:

- Windows: the Windows development host, run by the agent.
- Linux_Docker_Host: a Docker Engine with `Server.Os` equal to `linux`. The agent can run container gates and image tests through Docker Desktop's Linux engine, with `--network none` where the gate permits. Full-checkout Linux per-test runs are deferred rows (DLV-1 to DLV-4). The agent runs them through the autonomous route of PH7-09a (a Git bundle copied into the Linux container file system, never a bind mount of a Windows directory), and the owner may supply them through OA-02.
- CI/VM: a Linux host with Docker.
- Both: Windows and Linux_Docker_Host.
- Owner: owner-only.
- CI by workflow dispatch needs OA-01, after OA-09 has selected S.

ID scheme. Tasks are named `PHn-nn` (the phase number, a hyphen and a two-digit number, for example PH1-01) and carry a checkbox. Owner-only actions are `OA-nn` and conditional public deployment items are `CD-nn`. OA and CD items have no checkbox, so a task runner never queues them. A task that a review split keeps its id, and the new part takes a suffix letter (PH1-02a, numbered 1.2a), so no id or number moves. A split owner item is named the same way (OA-07a to OA-07e). Rollback rows RP-1 to RP-9 are in design D9.7. Blockers RB-1 to RB-17, RB-19 and RB-20 are in D9.6, and RB-18 (a rollback that did not complete) is added by OD-D10-3 in D10.10. Finding ids are H-1, M-1 to M-7 and L-1 to L-7 of the architecture review, and TPR-C-1 to TPR-C-4, TPR-H-1 to TPR-H-10, TPR-M-1 to TPR-M-12 and TPR-L-1 to TPR-L-5 of the task-plan review (`docs/next-phase/REVIEW_REMEDIATION_REGISTER.md`). The design rules TR-1 to TR-19, the rows D10-AC-10 to D10-AC-30 and the credential inventory CSI-1 to CSI-7 are in D10.11.

Final decisions of 2026-11-25 (design D10.10) and the tasks that carry them:

- OD-D10-2 (5 s recording target, a recording failure is visible and never SUCCEEDED): PH1-02, PH1-02a, PH7-08.
- OD-D10-3 (a failed rollback is blocker RB-18 and needs recovery to a verified checkpoint): every phase checkpoint (PH1-18, PH2-10, PH3-14, PH4-10, PH5-17, PH6-12), PH7-08, PH7-12, PH7-18.
- OD-D9-1 (evidence commits name the exact tested Release_Candidate SHA and are never that SHA; the path rule that let Test_Inputs change after S was replaced by TPR-C-2, D10.11 TR-2): PH7-08, PH7-17, PH7-18.
- OD-D10-1 (5 failed attempts per 15 minutes per source and account, bounded): PH5-11.
- OD-D10-4 (manifest integrity, signature authenticity and complete archive-byte integrity are three results): PH3-07, PH3-09, PH3-13, PH5-05.

Task-plan review rules (design D10.11) and the tasks that carry them. These are DESIGNED and wait for OA-00.

- TR-1 deferred Linux verification (DLV-1 to DLV-4): PH1-04, PH1-08, PH1-09, PH1-10, PH1-18, PH2-01, PH7-09a, PH7-17.
- TR-2 candidate, Evidence_Commit and Test_Input: PH7-08, PH7-12, PH7-17, PH7-18, OA-09.
- TR-3 extended isolation gate: PH1-12a and every task that adds an `isolation` test.
- TR-4 recorder, source and ingestion times, scan before evidence commits: PH1-02, PH1-02a, PH1-03.
- TR-5 BE-1 abstract-syntax-tree guard: PH1-04. TR-6 final security matrix: PH7-05. TR-7 checkpoints and RB-19, RB-20: PH7-17, OA-09.
- TR-8 owner items: OA-00 to OA-09. TR-9 autonomous Linux route: PH7-09a.
- TR-10 secure filesystem module: PH1-04a, PH1-05, PH1-06, PH1-11, PH1-16, PH2-02, PH3-04, PH3-06, PH6-02.
- TR-11 authentication before allocation: PH1-17, PH5-09, PH5-11. TR-12 CI provenance and collection: PH5-14, PH7-08, PH7-11.
- TR-13 evidence rules and single owners: the "TPR-M-2 mapping" table in the Notes. TR-14 legacy replay gate: PH3-05, PH3-08.
- TR-15 wording catalog: PH1-03a. TR-16 credential inventory: PH1-11, PH3-04, PH5-10, PH5-11, PH7-04. TR-17 redaction fixtures: PH1-03.
- TR-18 runtime floor: PH1-05, PH5-14, PH7-09a, PH7-11. TR-19 same-file order: PH1-16, PH1-17.

Evidence-commit gate EG-1 (TPR-H-10). From the first commit after the PH1-03 record, every commit that publishes evidence or a document passes the PH1-03 scan on all files to be published (3.14), and every task except PH1-01 (already complete), PH1-02 and PH1-03 depends on PH1-03, directly or through another task. The evidence commits of PH1-02 and PH1-03 are covered by a disclosed scratch scan, as the PH1-01 finalization was. PH1-01 stays completed bootstrap evidence with its documented scan, and no later task rewrites it.

## Scope freeze

The owner recorded OA-00 as `ACCEPTED_WITH_CONDITIONS` on 2026-11-26 for the checkpoint `fff6db49fb6f7f51080ca4fdb5e0ee7c1d37a581` and froze the scope of the enhanced release. The record is `docs/next-phase/OWNER_DECISIONS.md` and the design reading is D10.12. Specification planning is frozen. Implementation begins at PH1-02 in a Spec execution session.

- Queued: Phase 1 security remediation, Phase 2 MCP hardening, Phase 3 signed Bundles and signer trust, Phase 4 Kiro hooks and evidence tooling, Phase 5 Judge UI and local deployment hardening, the legacy replay checkpoint PH6-12 and Phase 7 release verification. That is 92 tasks, all mandatory: 1 complete (PH1-01) and 91 remaining. Ten owner items stay in the graph for traceability (OA-00 to OA-06 and OA-08 to OA-10).
- Deferred, not queued, not implemented and not verified: 15 tasks (PH1-07 and PH6-01 to PH6-11, including PH6-08a, PH6-09a and PH6-10a), 5 owner items (OA-07a to OA-07e) and 9 conditional public deployment items (CD-01 to CD-09). The Claim_Plugin_SDK, the Conformance_Suite, scaffolding, the loader rules, the fail-closed public loader, Texas completion, snapshot loader v2 and the California, Florida and New York adapters are deferred. The existing Texas adapter and historical replay stay intact and are guarded by D7-AC-1, D8-AC-15 and P-g in PH6-12.
- Marking: a deferred task keeps its id and its text, has no checkbox so that no task runner queues it, and carries a `Status: DEFERRED` line. No queued task or owner item names a deferred item in a `Depends on` line. A mention of a deferred item in the text of a queued task is a forward reference and creates no dependency. A criterion that only a deferred task could verify is listed `UNVERIFIED` with the reason `deferred scope`, never `SUCCEEDED`.
- Kept as release gates: the Linux full-checkout rows DLV-1 to DLV-4 stay mandatory. OA-02 is `NOT_PROVIDED`, so PH7-09a is the route. The reading of criterion 4.9 that the owner accepted is the one in the Overview: autonomous rows decide an autonomous task's box, and a deferred Linux row stays `UNVERIFIED` and is never reported as passed.
- Known limitation KL-1 (baseline entry-point loading in the public profile). The baseline loader (`core/src/verdictkit/cli.py`, `_load_registry`) imports every entry point of the group `verdictkit.claim_types` and every module named in `VK_CLAIM_TYPES`, in every Security_Profile, in the custodian and in the examiner. It has no allowlist and no provenance check, and an exception raised while loading the group is swallowed without a message. The fail-closed public loader (PH6-04, criteria 11.16 to 11.18) and its tests (PD-1 to PD-12, FC-10 and FC-12) are deferred, so secure public operation with respect to plugin loading is `UNVERIFIED`. The release report lists KL-1 under the known limitations (PH7-12). Public deployment is not authorized. While CD-01 to CD-09 are deferred, RB-16 and RB-17 stay open (no hosting decision, monitoring, rehearsed rollback or go decision is recorded), so Public_Deployment_Readiness stays `NOT_VERIFIED`. A later authorization of public deployment must first assess KL-1: if the retained loading behavior prevents secure public operation, public deployment stays blocked.

## Task Dependency Graph

Waves follow the Depends on lines. A task sits in a later wave than every task and OA item it depends on, and the graph has no cycle. Tasks in one wave do not depend on each other and no two of them name the same source file in their Objective; where the Depends on lines leave two tasks unordered and both name one file, the later wave is used (see Notes, same-file placement). An OA id carries its own Depends on line (the tasks that give the owner the material) and sits in a later wave than each of them and in an earlier wave than the first task that names it in Depends on. Where a task names an OA id, the task starts only after that item is `PROVIDED`, or after the owner has recorded an EVIDENCE item as `NOT_PROVIDED`. OA-10 sits in the last wave because nothing in this plan authorizes it. The deferred items (PH1-07, PH6-01 to PH6-11 with PH6-08a, PH6-09a and PH6-10a, OA-07a to OA-07e and CD-01 to CD-09) are not in the graph. The graph holds 92 tasks and 10 owner items in 52 waves. OA ids are listed for traceability only, and none of them is queued.

```json
{
  "waves": [
    { "id": 0, "tasks": ["PH1-01", "OA-00", "OA-08"] },
    { "id": 1, "tasks": ["PH1-02"] },
    { "id": 2, "tasks": ["PH1-03"] },
    { "id": 3, "tasks": ["PH1-02a", "PH1-04", "PH1-04a", "PH1-08"] },
    { "id": 4, "tasks": ["PH1-03a", "PH1-05", "PH1-09", "PH1-11"] },
    { "id": 5, "tasks": ["PH1-06", "PH1-12"] },
    { "id": 6, "tasks": ["PH1-10", "PH1-12a"] },
    { "id": 7, "tasks": ["PH1-13"] },
    { "id": 8, "tasks": ["PH1-14", "PH1-17"] },
    { "id": 9, "tasks": ["PH1-15"] },
    { "id": 10, "tasks": ["PH1-16"] },
    { "id": 11, "tasks": ["PH1-18"] },
    { "id": 12, "tasks": ["PH2-01"] },
    { "id": 13, "tasks": ["PH2-03"] },
    { "id": 14, "tasks": ["PH2-02"] },
    { "id": 15, "tasks": ["PH2-04"] },
    { "id": 16, "tasks": ["PH2-05"] },
    { "id": 17, "tasks": ["PH2-06"] },
    { "id": 18, "tasks": ["PH2-07", "PH2-08"] },
    { "id": 19, "tasks": ["PH2-09", "PH4-01"] },
    { "id": 20, "tasks": ["PH2-10", "PH4-02"] },
    { "id": 21, "tasks": ["PH3-01", "PH4-03"] },
    { "id": 22, "tasks": ["PH3-02", "PH4-04", "PH4-05"] },
    { "id": 23, "tasks": ["PH3-03", "PH4-06", "PH4-07", "PH4-08", "PH4-09"] },
    { "id": 24, "tasks": ["PH3-04", "PH3-08", "PH4-10", "OA-04"] },
    { "id": 25, "tasks": ["PH3-05", "PH5-01", "OA-06"] },
    { "id": 26, "tasks": ["PH3-06", "PH5-02", "OA-05"] },
    { "id": 27, "tasks": ["PH3-07", "PH5-03"] },
    { "id": 28, "tasks": ["PH3-09", "PH3-11", "PH3-13", "PH5-04"] },
    { "id": 29, "tasks": ["PH3-10", "PH3-12"] },
    { "id": 30, "tasks": ["PH3-14", "PH5-05", "PH5-08"] },
    { "id": 31, "tasks": ["PH5-06", "PH5-09"] },
    { "id": 32, "tasks": ["PH5-07", "PH5-10"] },
    { "id": 33, "tasks": ["PH5-11"] },
    { "id": 34, "tasks": ["PH5-12"] },
    { "id": 35, "tasks": ["PH5-13"] },
    { "id": 36, "tasks": ["PH5-14"] },
    { "id": 37, "tasks": ["PH5-15", "PH5-16"] },
    { "id": 38, "tasks": ["PH5-17"] },
    { "id": 39, "tasks": ["PH6-12"] },
    { "id": 40, "tasks": ["PH7-01", "PH7-06"] },
    { "id": 41, "tasks": ["PH7-02", "PH7-08"] },
    { "id": 42, "tasks": ["PH7-03", "PH7-04", "PH7-07", "PH7-09", "PH7-10"] },
    { "id": 43, "tasks": ["PH7-05", "PH7-09a", "PH7-11", "PH7-16", "OA-02"] },
    { "id": 44, "tasks": ["PH7-12"] },
    { "id": 45, "tasks": ["PH7-13", "PH7-14", "PH7-15"] },
    { "id": 46, "tasks": ["OA-09"] },
    { "id": 47, "tasks": ["OA-01"] },
    { "id": 48, "tasks": ["PH7-17"] },
    { "id": 49, "tasks": ["OA-03"] },
    { "id": 50, "tasks": ["PH7-18"] },
    { "id": 51, "tasks": ["OA-10"] }
  ]
}
```

## Tasks

- [ ] 1. Phase 1: BE-1, BE-2 and existing security remediation
  - Goal: Close BE-1 and BE-2 on the Windows leg, take the vault key out of every argument list, fix isolation, replay, upload and evidence-publication findings, and end at a verified checkpoint.
  - _Requirements: 1.1, 1.2, 1.3, 1.9, 1.13, 1.14, 1.17, 1.18, 1.19, 2.4, 2.5, 2.6, 2.11, 2.13, 2.14, 3.1, 3.2, 3.3, 3.5, 3.9, 3.11, 3.12, 3.14, 4.4, 4.9, 7.7, 7.8, 7.9, 7.10, 7.19, 7.20, 7.21, 7.22, 7.25, 8.13, 13.10, 13.11, 13.12, 13.13, 13.15, 13.16, 13.17, 13.18, 13.24, 13.25, 13.26, 14.10, 14.14_

  - [x] 1.1 PH1-01 Start-of-phase preflight
    - Objective: Record in the Evidence_Ledger the branch, HEAD, the Frozen_Release refs (tag object and peeled commit of `v1.0.0-submission`, `master`, `verified-quote-e2e-20261118`), `git status --porcelain` and the tool versions (Python patch, uv, Node, npm, git, ruff, pytest, Hypothesis, locked `mcp`, Docker engine `Server.Os`). Confirm each Submission_Artifacts file equals its content at `84df25c`. No code change.
    - Acceptance tests: D9-AC-16 at phase start: 4 of 4 ref values equal 1.2 (tag object `e9ca8d2bac4a65483f3a7357e00600a1210a6f4f`, peeled commit and `master` `84df25c68198e496889b5892a03555ec7d2d860a`, `verified-quote-e2e-20261118` `407478be97a8979a8e3555bba3b3ab302229f91d`). `git diff --quiet 84df25c HEAD` over `docs/SUBMISSION_DRAFT.md`, `docs/SUBMISSION_READINESS.md`, `docs/JUDGE_DEMO.md`, `docs/RELEASE_READINESS.md` and `docs/KIRO_USAGE.md` (the Submission_Artifacts of the Glossary) exits 0. `git status --porcelain` lists only new phase documents (1.9).
    - Environment: Windows. The Docker engine version is read through Docker Desktop.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, commit SHA, UTC start, recorded_utc within 5 s) for the branch and HEAD reads, the four ref reads (`git rev-parse "refs/tags/v1.0.0-submission^{commit}"` among them), `git status --porcelain`, the Submission_Artifacts diff and one version command per tool. D9-AC-16 (phase-start leg) SUCCEEDED. VM-13 at the start recorded.
    - Rollback: None (records are append-only; a wrong record is superseded, never edited).
    - Depends on: none
    - _Requirements: 1.1, 1.2, 1.3, 1.9, 14.14_

  - [ ] 1.2 PH1-02 Minimal evidence recorder (first implementation tooling task, OD-D10-2)
    - Objective: Create `scripts/release_verify.py` (stdlib only, DD9-10) with the subcommand `run [--step NAME] -- <command> [args]` and the subcommand `ingest`, and tests under `tests/release/` (D10.11 TR-4, TPR-C-4). `run` executes the command without a shell and without a pipe, takes the exit status from the process itself (a signal or a timeout is a non-zero status), measures the duration from integer monotonic nanoseconds (no float), takes the passed, failed, skipped and deselected counts only from the runner's summary line (absent when there is none, 3.3), keeps the names and reasons of failed and skipped tests from the `-rA` listing, hashes the merged output as published, reads the full HEAD SHA, and writes one record atomically (a temporary file in the same directory, flush, fsync and rename, so a crash leaves a complete record or none; the ledger text is only appended). `recorded_utc` is taken in the same invocation as the command. `ingest` records evidence that another party produced, with `source_recorded_utc` taken from the artifact, `ingested_utc`, a source type and the artifact hash (3.15). The records E-201 to E-222 stay the completed bootstrap evidence of PH1-01, made by a scratch procedure with the limitations that the ledger states. The recorder does not rewrite or repeat them.
    - Acceptance tests: D10-AC-10 and D10-AC-11. The exit status is the process's own for a passing, a failing and a killed command. `recorded_utc` is at most 5 s after the end of the command. A crash injected at each write step leaves 0 partial records. A 2 s sleep records a duration of at least 2.0 s and at most 2.5 s. Skipped and failed test names keep their reasons. A command with a pipe to `tail` or `head` is refused (1.15). An `ingest` record has separate `source_recorded_utc` and `ingested_utc` fields. A scan finds 0 float values in the duration arithmetic. The recorder writes the records of its own test run, and each such record says so.
    - Environment: Both. Stdlib code and unit tests run on Windows and on Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release` on each host and `uv run --no-sync ruff check .`, written by the recorder. The evidence commit of this task is covered by a disclosed scratch publication scan, because PH1-03 does not exist yet (EG-1). D10-AC-10 and D10-AC-11 SUCCEEDED on both hosts.
    - Rollback: RP-1 `git revert` of this task's commits (forward commits only). A failed rollback: OD-D10-3.
    - Depends on: PH1-01, OA-00
    - Findings: TPR-C-4, L-4
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.12, 3.15, 1.10, 1.15, 4.10_

  - [ ] 1.2a PH1-02a Ledger lint and recording-time check (OD-D10-2)
    - Objective: Extend `scripts/release_verify.py` (created by PH1-02; stdlib only, DD9-10) with the ledger lint, and tests under `tests/release/`. The lint rejects an ellipsis, an angle-bracket placeholder or a descriptive stand-in in a command field. It requires the Execution_Index id and counts equal to the canonical row. It allows BE-2 only as "observed on" a named host until a diagnosis exists. It requires `recorded_utc` and lists a recorder record written more than 5 s after the command ended, or with a time missing or unreadable, as a visible recording failure that never maps to SUCCEEDED. It applies that bound only to records whose source is the recorder. A record from an owner, a CI run or a Kiro capture must carry `source_recorded_utc`, `ingested_utc`, the source type and the artifact hash, and `ingested_utc` must not precede `source_recorded_utc` (3.15). It treats E-201 to E-222 as `BOOTSTRAP` records. It requires a rollback record to carry the track id, the risk that occurred, the action taken and its outcome (4.5), and it lists a FAILED record that has no diagnosis note before the next commit that changes application code (1.11). It fails a ticked box that has no SUCCEEDED record (4.9).
    - Acceptance tests: D8-AC-23: 0 ellipsis or placeholders in the command fields of new records, every new record cites its Execution_Index id, counts equal the canonical row, 0 BE-2 sentences imply a cause before the DD8-8 diagnosis. Negative controls that each fail the lint: a command with an ellipsis, a record with no Execution_Index id, a count changed by 1, `recorded_utc` 6 s after command end, a missing `recorded_utc`, a ticked box with no record, an owner record with no `source_recorded_utc`, an owner record whose `ingested_utc` precedes `source_recorded_utc`, a rollback record with a missing field, and a FAILED record with no diagnosis before a code commit. A late record stays in the ledger and is reported, never SUCCEEDED (3.5, OD-D10-2). A late owner record is not a recording failure, because its bound is not applied (D10-AC-11). Baseline rows E-001 to E-028 are checked against `docs/next-phase/baseline/EXECUTION_INDEX.md` and `docs/next-phase/baseline/LEDGER_COMMAND_RECONCILIATION.md`. The `recorded_utc` rule applies to recorder records written after PH1-02 lands.
    - Environment: Both. Stdlib code and unit tests run on Windows and on Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release` on each host, `uv run --no-sync ruff check .`, and the lint run over `docs/next-phase/EXECUTION_EVIDENCE.md` (exit 0). D8-AC-23 SUCCEEDED on both hosts.
    - Rollback: RP-1 `git revert` of this task's commits (forward commits only). A failed rollback: OD-D10-3.
    - Depends on: PH1-02, PH1-03
    - Findings: L-4, TPR-C-4
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.9, 3.12, 3.15, 1.10, 1.11, 1.15, 1.19, 4.5, 4.9_

  - [ ] 1.3 PH1-03 Publication scan and sanitizer
    - Objective: Implement the sanitizer and zero-hit scan once (13.28), as a stdlib-only module under `scripts/` (name chosen at implementation) with tests under `tests/release/`. It applies the ordered exact-string rules RR-1 to RR-3 of `docs/next-phase/EVIDENCE_REDACTION.md` and scans the classes of 3.14 (user-profile paths, repository-root paths, user names, host names, e-mail addresses, non-loopback addresses, secrets, key blocks). It is idempotent, reports counts per class only and never a matched value, and exits non-zero on any hit so that it gates every commit that publishes evidence or documents. From the first commit after the record of this task, every commit that publishes evidence or a document runs this scan on all files to be published, and every task except PH1-01 (already complete) and PH1-02 depends on it, directly or through another task (EG-1, D10.11 TR-4). A committed allowlist names the documented constructed example paths of `design.md` (the hook-matcher fixtures listed in `docs/next-phase/EVIDENCE_REDACTION.md`) by file and line hash. An allowlisted match is counted in its own column, and any other match is a hit.
    - Acceptance tests: D8-AC-22: applying the sanitizer twice gives the same output (P-k, 200 of 200 examples under the `ci` profile; this task holds the only Hypothesis test of P-k and PH7-04 only supplements it). The published tree has 0 hits in each class, apart from the allowlisted constructed examples, which are counted separately. Each Private_Original SHA-256 equals its Execution_Index entry and each Sanitized_Copy hash is listed. Applying RR-1 to RR-3 in order to the Private_Original of `docs/next-phase/baseline/records.sanitized.jsonl` reproduces its published SHA-256. That reproduction runs only on the authorized host that holds the Private_Original, which stays outside the public repository, and it is UNVERIFIED with that reason on any other host (TPR-L-3). Every automated test on every host, including the Linux container, builds its sensitive-looking inputs as synthetic fixtures inside the test and uses no value read from the environment (D10-AC-26). A planted canary of each class makes the scan exit non-zero and the output holds counts only.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the `tests/release` run on each host (`-rA`, `HYPOTHESIS_PROFILE=ci`), the scan over the tree to be published (counts per class, all 0), and `uv run --no-sync ruff check .`. D8-AC-22 and D10-AC-26 SUCCEEDED on both hosts. The evidence commit of this task is covered by a disclosed scratch scan, because the scanner is not yet recorded (EG-1).
    - Rollback: RP-8 (supersede with a new Sanitized_Copy and a new hash, never rewrite history) and RP-1 `git revert` of the code. A failed rollback: OD-D10-3.
    - Depends on: PH1-02
    - Findings: H-1, TPR-H-10, TPR-L-3
    - _Requirements: 1.14, 3.11, 3.14_

  - [ ] 1.3a PH1-03a Claim and wording scan (authoritative catalog WS-1 to WS-8)
    - Objective: Extend `scripts/release_verify.py` with the subcommand `wording-scan`, which holds the rule catalog WS-1 to WS-8 of D10.11 TR-15 as the only implementation of claim and wording verification (TPR-L-1): "byte-for-byte intact" (10.36); "authenticated", "signed" or "verified" for an unsigned Bundle (10.14); "tamper-proof", "secure", "authentic" or "signed" for the hook guard, chain or marker; "all values", "every value" or "any value" for a sweep; a capability statement without a `SUCCEEDED` record of the Release_Candidate (3.9, 3.10); a combined readiness line, or a public URL presented as live (14.26, 7.14); a Kiro attribution without a captured artifact (3.6, 4.7); and a Windows observation worded as a verified Linux result (1.12, 1.16). The subcommand takes rule ids and paths, reports the rule id, the file and the line and never a matched private value, and exits non-zero on a violation. Tests are under `tests/release/`.
    - Acceptance tests: D10-AC-24. Each of WS-1 to WS-8 finds its planted negative control with file and line, a documented negation for WS-1 passes, and `git grep` finds 0 other implementation of these rules. The tasks that check wording cite rule ids (PH2-09, PH3-07, PH3-13, PH4-04, PH4-07, PH5-02, PH5-05, PH5-16, PH6-05, PH6-11, PH7-14) and add no scanner of their own.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release` on each host, `uv run --no-sync ruff check .` and a `wording-scan` run over the tree for the rules that apply (one violation count per rule). D10-AC-24 SUCCEEDED on both hosts.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-02a
    - Findings: TPR-L-1
    - _Requirements: 3.9, 3.10, 10.36, 4.7_

  - [ ] 1.4 PH1-04 BE-1 POSIX assertion preserved by AST equality and executed, with the AST guard
    - Objective: In `tests/contract/test_mcp_server.py` put the permission check of `test_verify_replay_and_explain_roundtrip` behind the platform branch `if os.name == "posix"`. Keep the original assertion `oct(bundle.parent.stat().st_mode & 0o777) == "0o700"` with the same abstract syntax tree on that branch (the indentation that the branch adds is not a change, TPR-H-1), with no skip, `skipif` or `xfail`. The replay and explain assertions of the test run on every host. In the baseline test the permission assertion comes before them and fails first on Windows, so the Windows run never reached them. The Windows branch therefore has no early return, skip or `pytest.fail` before them, and until PH1-05 lands it ends the test with an explicit `pytest.fail` placed after the last of them (never a pass and never a skip). Add the BE1-5 guard test under `tests/contract/`. It reads `git show 84df25c:tests/contract/test_mcp_server.py`, compares `ast.dump` of the original comparison with the current file, and checks the branch, the marks and that the replay and explain assertions sit at the top level of the test function (D10.11 TR-5).
    - Acceptance tests: D10-AC-14, D3.9 BE1-1 and BE1-5. The guard passes on the real file and fails on six mutated copies: comparison removed, comparison weakened, `skipif` added, `xfail` added, an early `return` on Windows, and a replay or explain assertion moved under the POSIX branch. The `ast.dump` of the comparison equals the baseline's and `git diff -w 84df25c` shows 0 changed tokens on the POSIX assertion (D8-AC-4), and indentation is not compared. The Windows failure of the test is raised at the final `pytest.fail` line, which follows the explain assertions (read from the `-rA` traceback), so `replay_bundle` and `explain_verdict` ran. The guard runs on both host classes.
    - Environment: Windows. The Linux leg (full-checkout `-rA` run with the direct exit code, and the POSIX negative control: a `0o755` directory fails the original expression, BE1-6) is the deferred row DLV-1 and needs the route of PH7-09a or OA-02.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_mcp_server.py` (the BE-1 failure is recorded FAILED on Windows and not hidden) and the guard run on each host. D8-AC-4 (guard leg), D10-AC-14 and D3-AC-17 (guard and POSIX parts) SUCCEEDED. DLV-1 stays UNVERIFIED until its own record exists.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-03
    - Findings: M-4, TPR-H-1, TPR-C-1
    - _Requirements: 13.11, 2.11, 8.13_

  - [ ] 1.4a PH1-04a Shared secure-filesystem module (containment, secure open, private directory)
    - Objective: Add one Core production module, stdlib only (name chosen at implementation, under `core/src/verdictkit/`), that every later task reuses (D10.11 TR-10, TPR-M-5, TPR-M-7). It holds the containment check (the root is pinned once, and NUL, relative, UNC and Windows device-path names, alternate data streams and name aliases are rejected). It holds the secure open: on POSIX the components are opened with `O_NOFOLLOW` and `dir_fd`, then `fstat` of the opened descriptor is compared with the expected type, owner, mode and size (and, where an earlier `lstat` exists, the same device and inode), so identity is checked on the opened object and not on its name. On Windows a reparse point below the root is rejected and the final path of the opened handle is checked again. It holds exclusive secure create (`O_CREAT`, `O_EXCL`, `O_NOFOLLOW`, mode 0600) and `private_directory` enforcement (POSIX: the owner is the process uid and no group or other bit is set; Windows: it calls the access-list provider that PH1-05 adds, and fails closed with `PRIVATE_DIR_UNSAFE` while no provider exists). It is the one containment implementation of DD8-14. The vault key file reader (PH1-11), the replay namespaces (PH1-16), the MCP Approved_Root policy (PH2-02), the signing key and Trust_Store readers (PH3-04, PH3-06) and the scaffold destination (PH6-02) import it and add no containment code of their own.
    - Acceptance tests: D10-AC-19 (module leg). Negative tests, POSIX cases in the image on Linux_Docker_Host and Windows cases on Windows: a symbolic link as the final component and as a component below the root, a precreated file with another owner or mode, a swap between the check and the open (1000 iterations, 0 opens outside the root), a private directory with group or other access, and on Windows a junction and a reparse point. A positive control opens a regular file inside the root. A mutant that checks the name only fails the race test. A scan finds 0 other implementation of path containment under `core/src`.
    - Environment: Both. POSIX cases run in the image with `--network none` and Windows cases run on Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the module tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci), `uv run --no-sync ruff check .` and the source scan. D10-AC-19 (module leg) SUCCEEDED on each host for its own cases.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-03
    - Findings: TPR-M-5, TPR-M-7
    - _Requirements: 13.30, 13.19, 13.28, 9.21_

  - [ ] 1.5 PH1-05 BE-1 Windows access-list reader in the production module (oracle O1)
    - Objective: Add the Windows branch of the same test, and add the access-list reader to the Core production module of PH1-04a (BE1-2 to BE1-4, TPR-M-8), not as a helper that exists only under `tests/`. The test calls that function directly, and `mcp_server._workdir()` calls the same function in PH1-06. The reader reads the access list of the private directory through `ctypes` calls to `advapi32` (SDDL aliases, no new dependency). It requires a protected list with no inherited entry, allow entries only, and trustees limited to the current user, OWNER RIGHTS, SYSTEM and Builtin Administrators, with none for Everyone, Authenticated Users, Builtin Users or Builtin Guests. An enumeration error fails the check. It records the elevation state (BE1-7) and fails with `UNSUPPORTED_PYTHON_PATCH`, not a skip, on Python 3.12.0 to 3.12.3 (DD8-6, TR-18: the floor is 3.12.4, or an equivalent runtime that the owner approved through OA-08). The same module provides ACL-K for a signing-key file and ACL-T for a Trust_Store file (D10.11 TR-10, TPR-M-4), and no POSIX permission bit is accepted as Windows evidence.
    - Acceptance tests: D8-AC-5 and D3-AC-22. The directory from `mcp_server._workdir()` passes. Three negative controls each fail the helper: an Everyone allow entry, an inherited allow entry, a Builtin Users entry (BE1-6). Output holds aliases and classes only, no account name or SID. The Python patch version and elevation state are recorded. The test passes on Windows with Python 3.12.4 or later. D10-AC-20: the function that the test calls is the function that `_workdir()` calls (a code check). ACL-K fails on a key file that Users can read and ACL-T fails on a Trust_Store that Users can write (negative controls). A test that passes only because of `os.chmod` fails. The full Python version of the run is recorded (13.29).
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_mcp_server.py` (exit 0), the helper's negative-control run, and `uv run --no-sync ruff check .`. D8-AC-5, D3-AC-22 and D10-AC-20 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-04, PH1-04a
    - Findings: L-3, M-4, TPR-M-4, TPR-M-8, TPR-L-4
    - _Requirements: 13.11, 13.25, 13.13, 13.29, 13.30, 10.37_

  - [ ] 1.6 PH1-06 MCP private working directory self-check on Windows
    - Objective: In `core/src/verdictkit/mcp_server.py` make `_workdir()` check the directory it just created, through the private-directory enforcement of PH1-04a and the production access-list reader of PH1-05 (the function that the BE-1 test calls), on Windows and refuse to start with `PRIVATE_DIR_UNSAFE` when the check fails (fail closed, DD8-6). POSIX behaviour is unchanged.
    - Acceptance tests: D8-AC-5. A test that makes the check fail (a directory with an added Everyone entry) ends in a refused start with `PRIVATE_DIR_UNSAFE`, with no path in the message. A safe directory starts normally. On POSIX the self-check is not run and the original `0o700` assertion still applies.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract -m "not isolation"` (HYPOTHESIS_PROFILE=ci) and `uv run --no-sync ruff check .`. D8-AC-5 (refusal case) SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-05
    - Findings: L-3
    - _Requirements: 13.25, 13.11_

  - 1.7 PH1-07 Timeboxed S-AUTHZ spike (AuthzAccessCheck) [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Optional spike (DD8-7, OD-D8-5): evaluate `AuthzAccessCheck` against a synthetic client context in a helper of at most 120 lines under `tests/contract/` or `tests/windows/`, with no new dependency. Adopt it only on exact agreement with O1 on six constructed access lists, including an Everyone entry and an inherited entry. Otherwise record `NOT_ADOPTED` with the reason.
    - Acceptance tests: Agreement with O1 on 6 of 6 constructed lists, helper at most 120 lines, 0 added dependencies, or a recorded `NOT_ADOPTED` with the reason. Its absence does not block BE-1 closure (13.25).
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, commit SHA, UTC start, recorded_utc within 5 s) for the six-list comparison run and `git diff --stat` of the helper (line count), or the `NOT_ADOPTED` record. D8-AC-5 spike clause recorded as adopted or not adopted.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-05
    - Findings: L-3
    - _Requirements: 13.25_

  - [ ] 1.8 PH1-08 BE-2 instrumentation and run-time closed port
    - Objective: Instrument the bridge `scripts/serve_judge_ui.py` (UTC and monotonic timestamps for bridge accept, upstream-connect start and end with exception class and errno, and response write) and add a new timing harness under `tests/ui/` (client send, first client byte, total duration). Run at least 30 Windows trials and report the minimum, median and maximum. The at least 30 Linux trials are the deferred row DLV-2 (D10.11 TR-1). Allocate the closed port at run time (`VK_TEST_CLOSED_PORT` override) and remove the hard-coded `65534` from `tests/ui/test_judge_preview.py` (DD8-8, 1.17). The only change to that existing test is the port hunk.
    - Acceptance tests: D8-AC-6 (Windows leg): at least 30 Windows trials, every field populated, minimum, median and maximum reported. 0 occurrences of `65534` in the test. The port is allocated at run time and can be overridden. The BE-2 text keeps "observed on Windows" and states no cause (1.19).
    - Environment: Windows. The Linux leg (a full checkout, since the image has no `ui/`) is the deferred row DLV-2 and needs the route of PH7-09a or OA-02.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the 30-trial instrumented run on Windows and `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/ui/test_judge_preview.py`. D8-AC-6 (Windows leg) SUCCEEDED. DLV-2 stays UNVERIFIED until its own record exists.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-03
    - Findings: TPR-C-1
    - _Requirements: 13.26, 13.12, 1.17_

  - [ ] 1.9 PH1-09 BE-2 diagnosis and fix
    - Objective: Run a standalone `connect_ex` probe to a closed loopback port and discriminate hypotheses H1 to H5 (DD8-8, OD-D8-6). Record the root cause. Apply the fix by rule: if H1 is confirmed, bound the bridge's upstream connect with a dedicated timeout `VK_BRIDGE_CONNECT_TIMEOUT` (default 1.0 s, below the client deadline) in `scripts/serve_judge_ui.py`, and keep the 10 s read timeout and the test's 2 s client timeout. A timeout increase alone is never the fix. If H1 is not confirmed, record the real cause and fix that.
    - Acceptance tests: D8-AC-7 (Windows leg): 30 of 30 Windows passes of `test_case_outcome_get_to_offline_backend` with the port allocated at run time. The probe result and the chosen hypothesis are recorded in a diagnosis note before the fix commit (1.11). Wording stays "observed on Windows" until a Linux run exists (1.19). The 30 of 30 Linux passes and the Linux confirmation of the cause are the deferred row DLV-2. A Linux result that contradicts the Windows diagnosis reopens this task.
    - Environment: Windows. The Linux leg is the deferred row DLV-2.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the probe, the 30-run loop (exit code read directly, unpiped) and `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/ui/test_judge_preview.py`. D8-AC-7 (Windows leg) SUCCEEDED. DLV-2 stays UNVERIFIED until its own record exists.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-08
    - Findings: L-4, TPR-C-1
    - _Requirements: 13.12, 13.13, 1.19, 1.17, 1.11_

  - [ ] 1.10 PH1-10 BE-1 and BE-2 Windows-leg closure records
    - Objective: Record the closure evidence for the Windows leg: a full `-rA` run with the pytest exit code read directly, 30 of 30 BE-2 passes, the contract suite and the core hook command no longer failing on BE-1. Record the Linux legs as the deferred rows DLV-1 and DLV-2, UNVERIFIED until a `SUCCEEDED` record that names a Linux source exists. The Windows closure never stands for the Linux closure (1.12, 13.13). No code change.
    - Acceptance tests: D8-AC-4, D8-AC-5 and D8-AC-7 Windows legs: `test_verify_replay_and_explain_roundtrip` and `test_case_outcome_get_to_offline_backend` listed PASSED in the `-rA` output, contract suite 0 failures on Windows, hook core command exit 0. The track record lists 13.12, 13.13 and 13.26 as UNVERIFIED (one leg only), and never `SUCCEEDED`, until DLV-1 and DLV-2 have records.
    - Environment: Windows. The Linux legs are the deferred rows DLV-1 and DLV-2.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code read directly, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract -m "not isolation"`, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/ui/test_judge_preview.py` and the core hook command text of the existing hook. Rows D8-AC-4, D8-AC-5, D8-AC-7 (Windows legs) SUCCEEDED. The Linux legs (DLV-1, DLV-2) and RB-1 stay open until their own records exist. They do not block this box or PH1-18.
    - Rollback: None (records are append-only; a wrong record is superseded, never edited).
    - Depends on: PH1-04, PH1-05, PH1-06, PH1-09
    - Findings: M-4, L-3, TPR-C-1
    - _Requirements: 13.13, 1.18, 1.13, 14.10_

  - [ ] 1.11 PH1-11 Vault key off the argument list
    - Objective: In `deploy/entrypoint.sh` (`as_custodian`, `serve`, `gate-http`, `gate-case`) write the vault key with shell builtins to a custodian-owned, mode-0400 file on tmpfs, unset `VK_VAULT_KEY`, start the examiner with the closed environment list of F8-2, and have the custodian read the file once through `VK_VAULT_KEY_FILE`, validate owner and mode on the opened object through the secure-open of PH1-04a, and remove it (DD8-2, OD-D8-1, CSI-1). The directory of the key file is private and is never owned by or writable for `vk-examiner`, so a precreated file or a symbolic link at the key path is refused (TPR-M-5). `VK_VAULT_KEY` in the environment stays supported for non-container runs. If tmpfs is absent, fall back to a mode-0400 file on another local filesystem and record the fallback (R-D8-2).
    - Acceptance tests: A start-up test shows the custodian reads the key from the file, rejects a wrong owner or mode, and removes the file. A precreated file at the key path, a symbolic link at the key path and a swap between the check and the open are each refused, and 0 key bytes reach the target (D10-AC-19, Linux). 0 occurrences of the key in the argument list of any process during start-up (full matrix is PH1-12). Non-container start with `VK_VAULT_KEY` still works. The four existing gates still exit 0 with `--network none` (D8-AC-8 start-up leg).
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the image build, `gate-startup`, `gate-isolation` (output file `isolation.xml`), `gate-http` and `gate-case`, each with `--network none`, and the tmpfs mount check. Rows D8-AC-8 (start-up leg) and D2-AC-1 key cases SUCCEEDED.
    - Rollback: RP-1 `git revert` of the entrypoint and reader changes. A failed rollback: OD-D10-3.
    - Depends on: PH1-03, PH1-04a, OA-08
    - Findings: M-1, TPR-M-5, TPR-L-5
    - _Requirements: 7.20, 7.9, 7.10, 13.16, 13.30_

  - [ ] 1.12 PH1-12 Key-channel tests KT-1 to KT-8
    - Objective: Add the KT-1 to KT-8 tests under `tests/security/` (marked `isolation`) with a canary vault key searched in raw, base64, hexadecimal and URL-encoded form: argument lists polled at 1 ms over 20 start-ups, the environment of every process other than the custodian and the root entrypoint, the descriptors the examiner inherits, files readable by `vk-examiner`, logs, the entrypoint run under `bash -x` in a test copy, and crash output. Add a mutation guard that makes a leak and shows a test fails (CP-11). The canary is a parameter, so that PH3-04 adds the signing-key variant KT-S of each case without a second test body (D10.11 TR-6, TPR-M-4). The node ids join the manifest of PH1-12a, and the examiner-identity and root-observer groups of the gate run these tests (D10.11 TR-3).
    - Acceptance tests: D8-AC-8 (vault-key leg): 0 matches in every case and encoding (13.16). The KT-S leg for the signing key is added in PH3-04 and run again in PH7-05. The mutation guard fails when the key is placed on an argument list. A test never prints its canary in its own failure message (PC-6).
    - Environment: Linux_Docker_Host (isolation).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the container run of `pytest -rA -m isolation` over the KT tests with `--network none`, and the mutation-guard run. D8-AC-8 and D2-AC-11 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-11
    - Findings: M-1
    - _Requirements: 13.16, 7.20, 7.9_

  - [ ] 1.12a PH1-12a Extended container isolation gate (identities, manifest, counts)
    - Objective: In `deploy/entrypoint.sh` (`cmd_gate_isolation`) keep the first step unchanged: the four original tests of `tests/contract/test_isolation.py` run as `vk-examiner` and write `<junit_xml>` with exactly those 4 test cases. Then run three groups from `tests/security/`, selected by identity markers (names chosen at implementation and registered in `pyproject.toml`) and by the committed manifest `tests/security/ISOLATION_MANIFEST.txt` (D10.11 TR-3, TPR-C-3). The examiner-identity group runs as `vk-examiner` (uid 901). The authorized root observer group runs as the root process of the entrypoint, only to read `/proc` and files and to start the processes under test. The secondary-uid group runs through `setpriv` as a numeric uid that is neither 0, 900 nor 901, with no account added to the image. Each group writes its own JUnit file beside `<junit_xml>`. The gate then writes `gate-isolation-counts.json` with the expected, collected, executed and skipped counts of each group, and exits non-zero when a group collects 0 tests, when the collected set differs from the manifest, when executed differs from collected, or when a test is skipped. Under `--network none` it first records the network-none negative control (only `lo` is present and a connection to a non-loopback address fails). The CI step keeps the same command `gate-isolation /out/isolation.xml`, so CI runs the same gate. The KT tests of PH1-12 are the first members of the manifest, and one probe test per group shows its identity. Each later task that adds an `isolation` test adds its node ids to the manifest.
    - Acceptance tests: D10-AC-13. `isolation.xml` holds exactly the 4 original tests with 0 failures. Each group has collected equal to the manifest, executed equal to collected and 0 skipped, and `gate-isolation-counts.json` is written. A removed test, an empty group and a skipped test each make the gate exit non-zero (negative controls). The probe tests show uid 901, uid 0 for the observer and a uid other than 0, 900 and 901 for the secondary group, assert that the vault directory is mode 0700 and owned by uid 900, and assert the examiner socket mode (2.7). The network-none negative control is recorded. The four original gates still exit 0 with `--network none`.
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the image build, `gate-isolation` (output files `isolation.xml`, the group files and `gate-isolation-counts.json`), `gate-startup`, `gate-http` and `gate-case`, each with `--network none`, and the negative-control runs. D10-AC-13 SUCCEEDED.
    - Rollback: RP-1 `git revert` of the entrypoint and manifest changes. A failed rollback: OD-D10-3.
    - Depends on: PH1-12
    - Findings: TPR-C-3, TPR-M-9
    - _Requirements: 13.8, 13.16, 13.17, 2.7, 1.5_

  - [ ] 1.13 PH1-13 Isolation_Mode fixed at start and fail-closed
    - Objective: Implement rules S1 to S7 of DD8-10 in `core/src/verdictkit/examiner/client.py` and the start-up and run path under `core/src/verdictkit/api/`. Isolation_Mode is read once at process start. A configured examiner that fails a request fails that request closed, with the mode unchanged and the request never examined in the calling process. Only an absent socket in the local profile gives UNENFORCED, always labelled. The public profile refuses UNENFORCED at start. A replay reports its own mode and never the Bundle's recorded mode. Add the IS-1 to IS-8 tests under `tests/security/`.
    - Acceptance tests: D8-AC-18 (IS part): IS-1 to IS-8, 8 of 8. IS-2 and IS-5 show the request fails closed with the mode unchanged and no in-process examination.
    - Environment: Linux_Docker_Host (isolation).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the extended `gate-isolation` run (the IS node ids are added to the manifest of PH1-12a; `-rA`, `--network none`) and the `gate-startup` marker. D8-AC-18 (IS-1 to IS-8) and D2-AC-1 (isolation cases) SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-12a
    - Findings: L-1, TPR-C-3
    - _Requirements: 2.13, 2.5, 2.6, 2.4_

  - [ ] 1.14 PH1-14 Custodian-only examiner socket
    - Objective: In `core/src/verdictkit/examiner/worker.py` check `SO_PEERCRED` against the uid of `vk-custodian`, resolved by name at worker start and never from a request or an environment value (DD8-11). Close any other peer unread with a fixed log code. Refuse to start if the account cannot be resolved. Refuse the connection when peer credentials are unavailable. Set the socket mode by umask before `bind`. Apply a per-connection read deadline. Add the CA-1 to CA-7 tests under `tests/security/`.
    - Acceptance tests: D8-AC-18 (CA part): CA-1 to CA-7, 7 of 7 (CP-16). The two cases that need a second uid run in the secondary-uid group of the extended `gate-isolation` (PH1-12a), a test shows that uid differs from 0, 900 and 901 (distinct-uid check, 2.7), and the CA node ids are in the manifest.
    - Environment: Linux_Docker_Host (isolation).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the container run of the CA tests (`-rA`, `--network none`) and `gate-isolation`. D8-AC-18 (CA-1 to CA-7) SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-13
    - Findings: L-2
    - _Requirements: 2.14, 13.17, 2.13_

  - [ ] 1.15 PH1-15 One Security_Profile resolver and fail-closed start-up
    - Objective: Add one Security_Profile resolver used by the custodian and the examiner (AM-D6-4, one function, no second mechanism). `deploy/entrypoint.sh` passes the profile to the examiner. At start-up the custodian compares the examiner-reported profile and claim-type digest (SHA-256 over sorted `type_id` and `schema_version`) with its own. An unknown value, `VK_JUDGE_MODE=1` with `VK_PROFILE=local`, or any mismatch refuses start with a `VK_STARTUP_ERROR` code. `serve` prints `VK_STARTUP_OK isolation=ENFORCED` exactly once, before the first request. Add the vault-key missing or malformed refusal and the FC-1 to FC-9 and FC-11 tests (FC-10 and FC-12 are in PH6-04, which is deferred) and property P-l.
    - Acceptance tests: D8-AC-17 for FC-1 to FC-9 and FC-11: non-zero exit, a `VK_STARTUP_ERROR` line with a code, no `VK_STARTUP_OK`, no open listener, no file written. D8-AC-19 and D2-AC-1, D2-AC-2: `VK_STARTUP_OK` count is 1 on the positive start. P-l: resolution is total and no other variable turns `public` into `local` (200 of 200 examples).
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the container run of the FC tests (`-rA`, `--network none`), the P-l run (HYPOTHESIS_PROFILE=ci) and the positive start capture. D8-AC-17 (FC-1 to FC-9, FC-11), D8-AC-19, D2-AC-1 and D2-AC-2 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-11, PH1-13, PH1-14
    - Findings: L-1, L-2
    - _Requirements: 7.19, 7.7, 7.8, 7.10, 2.5, 2.6, 13.24_

  - [ ] 1.16 PH1-16 Replay isolation from the trusted evidence root
    - Objective: Give each uploaded-Bundle replay a server-generated namespace (32 hex characters) under a separate replay root, removed in `finally`, with orphans swept at start. The examiner reads a namespace read-only through a validated namespace key and re-hashes on read. Apply a per-replay and a total replay byte quota (64 MiB, ASSUMED, OD-D8-4). Metadata stays in custodian-private scratch and the trusted evidence root is unchanged (DD8-3, OD-D8-2). Create, validate and read every namespace through the secure-filesystem module of PH1-04a (no-follow, identity checked on the opened object, a private replay root), with no containment code of its own (TPR-M-7). Touch `core/src/verdictkit/api/server.py` (`_replay`), `core/src/verdictkit/bundle.py` (`replay_bundle` evidence root), the evidence store and `examiner/worker.py`. Add RI-1 to RI-8 under `tests/security/`.
    - Acceptance tests: D8-AC-9: RI-1 to RI-8, 8 of 8. The file list and file hashes of the trusted evidence root are identical before and after a replay (0 differences). 0 cross-namespace reads. The namespace is gone after an injected mid-replay failure.
    - Environment: Linux_Docker_Host (isolation).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the extended `gate-isolation` run (the RI node ids are in the manifest; `-rA`, `--network none`) and `gate-http`. D8-AC-9 (CP-12) SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-04a, PH1-14, PH1-15, PH1-17, OA-08
    - Findings: M-2, TPR-M-7, TPR-M-11, TPR-L-5
    - _Requirements: 7.22, 13.17, 7.25, 13.30_

  - [ ] 1.17 PH1-17 Upload admission before buffering
    - Objective: In `core/src/verdictkit/api/server.py` (`SafetyMiddleware`) take a slot from `VK_MAX_CONCURRENT_UPLOADS` (default 2) before the first body byte. With no free slot answer 429 `RATE_LIMITED` with `Retry-After` after the headers only. Hold one buffered copy, apply a total body deadline, release the slot on disconnect and on error, and leave 0 partial files. Use the same mechanism for every upload route (DD8-4, OD-D8-4). In the public profile the slot is taken only after the request is authenticated from its headers, never before: this task adds an authenticate hook that is a no-op in the local profile, and PH5-11 completes it (TPR-M-6, D10.11 TR-11). This task starts after PH1-13, because both edit `core/src/verdictkit/api/server.py` (TPR-M-11). Add UA-1 to UA-8 and property P-i under `tests/security/`.
    - Acceptance tests: D8-AC-10: UA-1 to UA-8. At most `slots` uploads in flight, later requests get 429 before any body byte is read, peak extra memory at most `slots x cap + 2 MiB` in every trial, the slot is released on disconnect, 0 partial files. P-i: 200 of 200 examples. UA-9 (an unauthenticated upload in the public profile gets 401 with the slot count unchanged and 0 body bytes read) is added by PH5-11, where credentials exist.
    - Environment: CI/VM. The local Linux_Docker_Host stands in and each record names its source (DD9-7).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `pytest -q -p no:cacheprovider -rA` over the UA tests (HYPOTHESIS_PROFILE=ci) and `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/api`. D8-AC-10 (CP-13) SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-03, PH1-13, OA-08
    - Findings: L-7, TPR-M-6, TPR-M-11, TPR-L-5
    - _Requirements: 7.21, 13.18, 7.27_

  - [ ] 1.18 PH1-18 Phase 1 checkpoint
    - Objective: Run the targeted regression on Windows and on the Linux_Docker_Host that the agent reaches (the image, the extended `gate-isolation` and the container gates), `ruff check .`, the ledger lint, the publication scan, the frozen-ref and Submission_Artifacts check, write the track Execution_Record for Phase 1 (4.4) with one status per criterion, the rollback fields (4.5) and one attribution row for each Kiro feature (specs, steering, task execution, sub-agents, MCP tools, hooks) with `observed running inside Kiro` or `not observed running inside Kiro` (4.7), list the deferred rows DLV-1 and DLV-2 as UNVERIFIED with their routes (TPR-C-1), update the Phase 1 checkboxes in the same change (4.9), and name the verified checkpoint commit.
    - Acceptance tests: D8-AC-30 and D8-AC-29: each host's result recorded separately, 0 unexplained divergence, 0 changed lines in existing tests except the approved hunks (BE-1 Windows branch, the BE-2 port hunk). 13.12, 13.13 and 13.26 are `UNVERIFIED` in the track record (one leg only) and DLV-1 and DLV-2 are listed `UNVERIFIED` (D10-AC-28). No owner EVIDENCE item (OA-01 to OA-06) and no DLV record is among the dependencies of this task, directly or through another task, so no deferred Linux row and no owner evidence blocks it. The only owner items behind it are the GATE decisions OA-00 (the plan) and OA-08 (for PH1-11, PH1-16 and PH1-17), which the owner records before the tasks that name them start. The counts of `gate-isolation-counts.json` are recorded (D10-AC-13). `ruff check .` has 0 violations. The ledger lint and the scan exit 0. D9-AC-16: 4 of 4 ref values and 0 Submission_Artifacts differences.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the regression set on each host (`-rA`), `uv run --no-sync ruff check .`, the lint, the scan and the frozen-ref commands. The track record lists each criterion of Phase 1 as SUCCEEDED, FAILED or UNVERIFIED. The checkpoint commit is a verified checkpoint only when its regression set has a SUCCEEDED record.
    - Rollback: RP-1 `git revert` of the phase's commit range back to the previous verified checkpoint. If the rollback does not complete, the RP row is FAILED, the track is incomplete and RB-18 stays open until the branch is recovered to a verified checkpoint by a new commit that restores its tree and a rerun of the regression set (OD-D10-3, 4.6).
    - Depends on: PH1-01, PH1-02, PH1-02a, PH1-03, PH1-03a, PH1-04, PH1-04a, PH1-05, PH1-06, PH1-08, PH1-09, PH1-10, PH1-11, PH1-12, PH1-12a, PH1-13, PH1-14, PH1-15, PH1-16, PH1-17
    - Findings: TPR-C-1, TPR-C-3
    - _Requirements: 13.15, 13.10, 4.4, 4.5, 4.7, 4.9, 1.2, 14.14_

- [ ] 2. Phase 2: MCP interoperability, strict validation, sanitized errors and approved-root access
  - Goal: Make the four MCP tools diagnosable and fail-closed over a real stdio transport, with structured sanitized errors, a pinned `mcp` range and a single Approved_Root helper, without changing the existing tool names and success shapes.
  - _Requirements: 2.11, 4.4, 4.9, 8.19, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.9, 9.10, 9.13, 9.14, 9.15, 9.16, 9.17, 9.18, 9.19, 9.20, 9.21, 9.22, 13.15, 13.19, 13.28_

  - [ ] 2.1 PH2-01 Pin the `mcp` range and the lock
    - Objective: Set the `mcp` specifier in `core/pyproject.toml` to `>=2.3,<2.4` and keep exactly one `mcp` version inside that range in `uv.lock` (2.3.0 at design time, AM-D4-8). The installed version equals the locked version and the image build uses `uv sync --frozen`. The range widens only after a recorded stdio client run on the new upper version. No runtime package is added. This task starts after the PH1-18 checkpoint. That checkpoint depends on no owner EVIDENCE item and on no deferred Linux row (TPR-C-1), so the Linux full-checkout legs of Phase 1 never block it. The only owner items behind it are the GATE decisions OA-00 and OA-08.
    - Acceptance tests: D4-AC-18 as amended by AM-D4-8: the specifier equals the string above, `uv.lock` holds exactly 1 `mcp` entry inside the range, installed version equals locked version, `uv lock --check` exits 0, `mcp.server.mcpserver` imports. D8-AC-28: the `uv.lock` diff shows 0 added runtime packages.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv lock --check`, `uv sync --frozen --all-packages --all-extras --group dev`, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_mcp_server.py` and `git diff --stat 84df25c -- uv.lock`. D4-AC-18 and D8-AC-28 (lock part) SUCCEEDED.
    - Rollback: RP-6 revert `core/pyproject.toml` and `uv.lock` together; `uv lock --check` passes. A failed rollback: OD-D10-3.
    - Depends on: PH1-18
    - Findings: M-7
    - _Requirements: 9.22, 13.28_

  - [ ] 2.2 PH2-02 Approved_Root policy on the shared secure-filesystem module
    - Objective: Apply the Approved_Root policy of the MCP_Server through the shared secure-filesystem module of PH1-04a, and add no containment code of this task's own (TPR-M-7, D10.11 TR-10). Use the module in `mcp_server._bundle_path`. Roots come from `VK_MCP_BUNDLE_ROOTS` (default: the private working directory, OD-D8-3), resolved and pinned once. Reject NUL, relative, UNC and Windows device-path names, alternate data streams and aliases. The module opens components without following links, rejects a reparse point below the root and re-checks the final path of the opened handle on Windows. File type and size are verified on the opened handle. One `PATH_NOT_ALLOWED` code with one fixed message. The same module serves the replay namespaces (PH1-16) and the scaffold destination (PH6-02). Add PR-1 to PR-23 and property P-j, which holds the only Hypothesis test of P-j.
    - Acceptance tests: D8-AC-11: at least 20 disallowed cases return `PATH_NOT_ALLOWED`, the 1000-iteration race PR-21 finds 0 opens outside a root, Windows junction and reparse cases (PR-22, PR-23) are rejected, the positive control PR-20 opens. P-j: 200 of 200 examples (CP-26). The message contains no part of the path. A scan shows that `mcp_server` and the replay code import the same module and that this task adds no second containment implementation (D10-AC-19).
    - Environment: Both. Windows-only cases run on Windows and symlink cases on Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the PR tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci) and `uv run --no-sync ruff check .`. D8-AC-11 SUCCEEDED (Windows cases on Windows).
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-04a, PH1-06, PH2-01, OA-08
    - Findings: L-6, TPR-M-7, TPR-L-5
    - _Requirements: 9.21, 13.19, 9.1, 13.30_

  - [ ] 2.3 PH2-03 Structured MCP errors
    - Objective: In `core/src/verdictkit/mcp_server.py` return `isError` true with a structured `error` object for every execution error (invalid input, size limit, read-only refusal, missing bundle, tampered bundle with `BUNDLE_INTEGRITY_FAILED`, internal error): `error.code` from the closed documented list, a `message` of at most 500 characters with no path and no exception text, and the tool name. Sanitize errors raised before a tool runs (AM-D4-7). Success shapes stay unchanged. A legitimate `INDETERMINATE`, `BLOCKED` or `CONTRADICTED` verdict stays `isError` false (AM-D4-4). No existing contract test is edited, skipped or marked.
    - Acceptance tests: D4-AC-3: every error case has `isError` true, a code in the list, the right tool and a message of at most 500 characters, and 0 verdict results have `isError` true. D4-AC-4: 20 canary injections give 0 occurrences in text, `structuredContent` and stderr, and P-d holds for 200 of 200 examples (this task holds the only Hypothesis test of P-d, and PH2-08 only supplements it, TPR-M-3). D4-AC-2: 0 changed lines in the existing MCP and Texas test files except the approved hunks.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_mcp_server.py`, the new error-matrix tests (HYPOTHESIS_PROFILE=ci) and `git diff 84df25c -- tests/contract/test_mcp_server.py`. D4-AC-2, D4-AC-3 and D4-AC-4 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH2-01
    - _Requirements: 9.3, 9.13, 9.19, 2.11_

  - [ ] 2.4 PH2-04 SchemaError message and no relaxation of validation
    - Objective: Make a `SchemaError` result carry the claim type's own validation message (it names the offending field only), with no exception text, path or input value. Do not coerce a string to a boolean, treat a missing required list as empty, or otherwise relax claim validation (9.16).
    - Acceptance tests: D4-AC-9: removing or corrupting each required field of every registered claim type gives `CLAIM_INVALID`, a message that names the field, 0 exception text, 0 paths, 0 input values. D4-AC-10: a string for a boolean and a missing `addons`, `gov_fees` or `rebates` on the finance claim are each rejected with `CLAIM_INVALID` (0 accepted).
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the mutation test run with `-rA` and `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract`. D4-AC-9 and D4-AC-10 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH2-03
    - _Requirements: 9.14, 9.16_

  - [ ] 2.5 PH2-05 Strict arguments, size caps and read-only mode
    - Objective: An undeclared argument or an `allow_refetch` that is not a JSON boolean returns `INVALID_ARGUMENT` (AM-D4-5). A claim of exactly 262,144 bytes and a Bundle of exactly 8,388,608 bytes are accepted and one byte more returns `SIZE_LIMIT_EXCEEDED`. With `VK_MCP_READONLY=1` a refetching replay is refused with `READ_ONLY_MODE`, `verify_claim` returns `INDETERMINATE` findings, and no outbound connection is opened (OD-D4-3 recommendation).
    - Acceptance tests: D4-AC-11: `"yes"`, `"true"` and `1` for `allow_refetch` and an unknown argument give `INVALID_ARGUMENT`, and `list_claim_types` without `arguments` succeeds. D4-AC-7: 262,144 and 8,388,608 accepted, 262,145 and 8,388,609 rejected. D4-AC-8: a launcher that fails any non-Unix `connect` sees 0 outbound connections.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the boundary and read-only test runs with `-rA`. D4-AC-7, D4-AC-8 and D4-AC-11 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH2-03
    - _Requirements: 9.1, 9.6, 9.7_

  - [ ] 2.6 PH2-06 Diagnostics and version equality
    - Objective: Register `server_diagnostics` only when `VK_MCP_DIAGNOSTICS=1` (AM-D4-1). It returns exactly: server version (equal to the installed package metadata, also in the initialize response), contract version as pinned at that time (PH3-12 moves it with the lockstep change), Isolation_Mode, the read-only flag, whether an examiner socket is configured, whether it accepted a connection within 2 s, and whether `VK_EVIDENCE_DIR` is valid. It writes no file, opens no connection other than the configured Unix socket, and holds no secret and no path.
    - Acceptance tests: D4-AC-5: server version equals `importlib.metadata`, and a double that reports another version fails the same comparison. D4-AC-6: exactly 7 fields, 0 files written, 0 non-Unix connections, `examinerSocketReachable` true within 2 s and false within 2.5 s for a stalled socket, 0 secrets.
    - Environment: Windows. The Unix-socket cases run on Linux_Docker_Host in PH2-08.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the diagnostics test run with `-rA` and `uv run --no-sync ruff check .`. D4-AC-5 and D4-AC-6 (non-socket part) SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH2-03
    - _Requirements: 9.2, 9.4, 9.5, 9.18_

  - [ ] 2.7 PH2-07 `autoApprove` limited to no-write, no-network tools
    - Objective: Make `.kiro/settings/mcp.json` satisfy the effect table of D4.5: `autoApprove` lists only tools that write nothing outside the server's private temporary directory and use no network. Add the check as a test under `tests/contract/`. Do not set `VK_MCP_DIAGNOSTICS` there without an owner decision (AM-D4-1). The file is in the 8.19 pinned set, so any change voids any earlier hook-surface review until OA-06 records a renewed review.
    - Acceptance tests: D4-AC-12: every `autoApprove` entry is NO_WRITE_NO_NETWORK, and a copy that adds `verify_claim` fails the check. D10-AC-6: the file is a member of the pinned hook-surface set and its new hash is listed as pending review.
    - Environment: Windows. The renewed review is OA-06.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the effect-table test run with `-rA` and `git diff 84df25c -- .kiro/settings/mcp.json`. D4-AC-12 SUCCEEDED. The review state stays UNVERIFIED until OA-06.
    - Rollback: RP-1 `git revert`, which restores the file from the previous commit. A failed rollback: OD-D10-3.
    - Depends on: PH2-05, PH2-06
    - _Requirements: 9.9, 8.19_

  - [ ] 2.8 PH2-08 Real stdio MCP client test
    - Objective: Add the stdio client test under `tests/contract/`. It starts the server over stdio, lists the tools, calls each tool with one valid and one invalid input, validates each result against the schema snapshots stored with the test (published by PH2-09), and runs the negative paths for each tool (invalid, oversize, read-only, missing bundle, tampered bundle). It includes a finance claim with boolean fields and non-empty lists that must give `SUPPORTED`, a version-equality check and stdout hygiene. Each call has a 30 s limit. This task adds no property test of its own: P-d belongs to PH2-03, and the stdio negative cases here only supplement it with an example check (TPR-M-3).
    - Acceptance tests: D4-AC-3 and D4-AC-13: 100% of error cases `isError` true and 0 verdict results `isError` true, 0 non-protocol stdout lines, `§` and `—` identical on both hosts, exit 0 within 5 s of EOF. D4-AC-14: a stalled double is reported as a failure at 30 s. D4-AC-15: `tax_rate` is `SUPPORTED`. D4-AC-5 and D4-AC-6 socket cases pass on Linux_Docker_Host. P-d supplement: 0 host path separators in the 5 negative-path results over stdio (an example check, with no property test here).
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the stdio test run with `-rA` on each host (HYPOTHESIS_PROFILE=ci). D4-AC-3, D4-AC-13, D4-AC-14 and D4-AC-15 SUCCEEDED on both hosts.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH2-02, PH2-04, PH2-05, PH2-06
    - _Requirements: 9.10, 9.17, 9.18, 9.20, 9.3_

  - [ ] 2.9 PH2-09 MCP documentation and schemas
    - Objective: Write `docs/MCP_SERVER.md` and `docs/mcp/schemas/`: the error code list, the statement that the Kiro tool-call path was reported to drop empty arrays and objects, the affected `verify_claim` fields (finance `addons`, `gov_fees`, `rebates`), a valid finance example that passes through Kiro, the stricter argument rule and the Approved_Root rule. The Kiro-side behaviour stays labelled UNVERIFIED until a capture exists (PH4-09, OA-05).
    - Acceptance tests: D4-AC-17: a test extracts the finance example from the document and runs it over stdio with result `SUPPORTED`. The empty-array statement, the affected fields and the code list are present. The schema files equal the snapshots used by PH2-08. The wording check is `wording-scan` rule WS-7 (PH1-03a): 0 Kiro attribution without a captured artifact.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the document-content test run with `-rA` and the publication scan over the new files (counts per class). D4-AC-17 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH2-08
    - _Requirements: 9.15, 9.3, 9.21_

  - [ ] 2.10 PH2-10 Phase 2 checkpoint
    - Objective: Run the Phase 2 targeted regression on both host classes, `ruff check .`, the ledger lint, the publication scan and the frozen-ref check. Write the track Execution_Record for Phase 2 (4.4) with the rollback fields (4.5) and the Kiro attribution rows (4.7) as in PH1-18, update the Phase 2 checkboxes in the same change (4.9), and name the verified checkpoint commit.
    - Acceptance tests: D4-AC-1: 4 tool names, 0 `inputSchema` differences, 0 key-set differences against the baseline snapshot. D4-AC-2: 0 changed lines in existing tests except the approved hunks. D8-AC-30: each host recorded separately with 0 unexplained divergence. `ruff check .` has 0 violations.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the regression set on each host (`-rA`), `uv run --no-sync ruff check .`, the lint and the scan. The track record lists each Phase 2 criterion as SUCCEEDED, FAILED or UNVERIFIED. The checkpoint commit is verified only when its regression set has a SUCCEEDED record.
    - Rollback: RP-1 `git revert` of the phase's commit range back to the previous verified checkpoint. If the rollback does not complete, the RP row is FAILED, the track is incomplete and RB-18 stays open until the branch is recovered to a verified checkpoint (OD-D10-3, 4.6).
    - Depends on: PH2-01, PH2-02, PH2-03, PH2-04, PH2-05, PH2-06, PH2-07, PH2-08, PH2-09
    - _Requirements: 13.15, 9.1, 4.4, 4.5, 4.7, 4.9_

- [ ] 3. Phase 3: Ed25519 signing, signer trust, archive validation and historical replay compatibility
  - Goal: Add opt-in Ed25519 Bundle signing with explicit signer trust, keep unsigned and historical Bundles verifying and replaying unchanged, harden archive parsing, and move the API to contract 2.0.0 in one lockstep change.
  - _Requirements: 1.2, 1.8, 2.2, 4.4, 4.9, 7.20, 9.8, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13, 10.14, 10.15, 10.16, 10.17, 10.18, 10.19, 10.20, 10.21, 10.22, 10.23, 10.24, 10.25, 10.26, 10.27, 10.28, 10.29, 10.30, 10.31, 10.32, 10.33, 10.34, 10.35, 10.36, 12.23, 13.5, 13.6, 13.14, 13.15, 13.21, 13.22_

  - [ ] 3.1 PH3-01 Legacy corpus from the baseline commit
    - Objective: In a disposable detached worktree of `84df25c` write one Bundle for each of a Texas finding, a non-Texas finding, a Lease claim, a Reel claim and the stub claim type, from constructed inputs labelled synthetic and taken from existing fixtures (no invented number, OD-D6-7). Commit the Bundles as fixtures under a directory chosen at implementation, with each recorded Verdict_Hash and the SHA-256 of each zip and of every member (D5.9 DR-7 pre-change step, recorded on each host before any signing code changes). `examples/stub_claimtype/golden.vkb` joins the corpus.
    - Acceptance tests: D9.4 VM-9 precondition: 5 corpus Bundles plus `golden.vkb`, each with a recorded Verdict_Hash and SHA-256 values. Replay on each host class gives an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV` (the 14.24 pass condition). The observed status and `envMatch` are recorded and never relabelled (D9-AC-8). 0 `DIVERGED`, 0 `UNVERIFIABLE`.
    - Environment: Windows to write and hash. Replay runs on Both (Linux_Docker_Host in the built image).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, commit SHA, UTC start, recorded_utc within 5 s) for the worktree creation, each Bundle write, each hash command and `uv run --no-sync verdictkit replay` with `--json` on every corpus file on each host. D9-AC-8 (corpus leg) SUCCEEDED.
    - Rollback: RP-1 `git revert` of the fixture commit. The worktree is disposable and holds no ref. A failed rollback: OD-D10-3.
    - Depends on: PH2-10
    - _Requirements: 13.22, 12.23, 10.32_

  - [ ] 3.2 PH3-02 Examination_Semantics identifier in new Bundles
    - Objective: Record the Examination_Semantics identifier in every new Bundle inside integrity-covered bytes (AM-D7-3). The carrier is chosen at implementation under the AM-D7-3 constraints (OD-D7-9). A Bundle with no identifier is `legacy-1` and stays byte-identical to the baseline. Replay selects the semantics from the Bundle alone, never from the current registry or manifest. A claim cannot choose the identifier. It reaches the examiner inside the task. An unknown identifier gives `UNVERIFIABLE`. Touch `core/src/verdictkit/bundle.py` and the task path only as far as needed.
    - Acceptance tests: D8-AC-15 (DR-5 part) and D9-AC-8: every corpus Bundle replays with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`. D5-AC-1: 0 member-hash differences, 0 zip-hash differences on the same host, 0 edits to `tests/contract/test_bundle_replay.py` and `tests/integration/test_bundle_evidence_and_golden.py`. An unknown identifier gives `UNVERIFIABLE` (CP-40).
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract tests/integration` on each host (HYPOTHESIS_PROFILE=ci), the corpus replays and the DR-7 hash comparison. D5-AC-1 and D9-AC-8 SUCCEEDED.
    - Rollback: RP-1 `git revert`. Unsigned output returns to the baseline bytes. A failed rollback: OD-D10-3.
    - Depends on: PH3-01
    - _Requirements: 12.23, 10.5, 10.32, 2.2_

  - [ ] 3.3 PH3-03 Signing core
    - Objective: Add `core/src/verdictkit/signing.py` and the signing path of `write_bundle` in `core/src/verdictkit/bundle.py`. Ed25519 comes from the existing `cryptography` dependency with no new package. One envelope member `signature/envelope.json` sits apart from the manifest-listed content (OD-D5-2). The signing input is domain separated and binds the SHA-256 of the canonical manifest, the Bundle format version, protocol id and version, the algorithm id `ed25519` and the key id (SHA-256 of the raw public key). Signing is deterministic with an injected clock. The Verdict_Hash is computed without signature material. Unsigned output is unchanged.
    - Acceptance tests: D5-AC-3: two runs and two processes give 0 differing bytes. D5-AC-4: equal Verdict_Hash for signed and unsigned runs, and the signed replay is `REPRODUCED`. The envelope is canonical JSON with the exact key set and at most 2,048 bytes. A round trip with a test-side reference verifier is `VALID` (the production verifier and the rows D5-AC-2 and D5-AC-6 close in PH3-05, PH3-06 and PH3-09). D8-AC-28: 0 added runtime packages.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the signing tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci), `uv lock --check` and `git diff --stat 84df25c -- uv.lock`. D5-AC-3 and D5-AC-4 SUCCEEDED.
    - Rollback: RP-1 `git revert`. Signing is opt-in, so unsigned output stays baseline. A failed rollback: OD-D10-3.
    - Depends on: PH3-02
    - _Requirements: 10.1, 10.3, 10.4, 10.6, 10.7, 10.24, 10.26, 10.29_

  - [ ] 3.4 PH3-04 Signing key handling
    - Objective: Read the signing key only in the custodian, from an externally provisioned location (`VK_SIGNING_KEY_FILE`), reusing the PH1-11 key-file mechanism and the secure-open of PH1-04a (no-follow, identity checked on the opened object, a private directory; CSI-2). `deploy/entrypoint.sh` passes `VK_SIGNING_KEY_FILE` and `VK_TRUST_STORE_FILE` to `as_custodian` only, never to the examiner. A missing, empty, unreadable, directory, symlink, RSA, Ed448, encrypted or oversized (4,097 bytes) key, on POSIX a group-readable key, and on Windows a key file whose access list fails ACL-K of PH1-05 (an allow entry for a trustee outside the four allowed ones, or an access list that cannot be enumerated), aborts creation with a matching code, no `.vkb`, no `.tmp`, no ledger append, and no key bytes or path in any output. No production key is generated, stored, logged or committed. Tests use throwaway in-memory keys. Add the signing-key variant KT-S of each KT case of PH1-12, with a canary key created in memory (PC-7), to the manifest of PH1-12a (TPR-M-4).
    - Acceptance tests: D5-AC-9 (A-19, A-20): 0 files created on failure, 0 canary occurrences of the private key bytes in Bundles, API and MCP results, error text, stdout, stderr, logs and the examiner environment, and the examiner uid cannot read the key (container). `git ls-files` lists 0 key files and `*.pem` and `*.key` stay git-ignored. KT-S: 0 matches for the canary signing key in the channels of KT-1 to KT-8 (D8-AC-8, signing-key leg). On Windows, ACL-K refuses a key file that Users can read, and a POSIX mode bit is never accepted as Windows evidence (D10-AC-20).
    - Environment: Linux_Docker_Host for the container checks and Windows for the file-handling cases.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the key-handling tests with `-rA` on Windows, the container run (`--network none`) of the key-channel checks and `git ls-files`. D5-AC-9 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-03, PH1-11, PH1-04a, PH1-05
    - Findings: M-1, TPR-M-4, TPR-M-5
    - _Requirements: 10.2, 10.18, 10.25, 7.20, 10.37, 13.30_

  - [ ] 3.5 PH3-05 Verification rules
    - Objective: Implement verification in `core/src/verdictkit/bundle.py` and `core/src/verdictkit/signing.py`. Signature_Validity is exactly `VALID`, `INVALID`, `UNSIGNED` or `UNSUPPORTED_ALGORITHM`. Reject a duplicate archive path, an unknown signature member, several envelopes, a non-canonical or truncated envelope and a wrong algorithm. Validate member names in their stored form (`orig_filename`) before platform normalization (AM-D5-9). Exempt from the unlisted-member rule only the exact signature member names, with no prefix or wildcard. Validate the public key (32 bytes, SHA-256 equals `key_id`, not on the small-order or non-canonical table) and the signature (64 bytes, `S < L`). Verification is offline.
    - Acceptance tests: D5-AC-5: A-1 and A-2 on the stub bundle give 0 `ESTABLISHED`. D5-AC-6: A-3 to A-15 give 0 `VALID` where a row forbids it and the stated code in 100% of rows. D5-AC-7: the exact name passes and a mutated prefix-match copy fails A-8. D5-AC-10: 0 sockets and 0 clock reads other than `as_of`. A-7 and A-8 give identical results on Windows and Linux. Legacy replay gate (D10.11 TR-14, D10-AC-23): after this change the five corpus Bundles of PH3-01 and `examples/stub_claimtype/golden.vkb` replay with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, the SHA-256 of each corpus file is unchanged, and an unsigned Bundle is still accepted.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the attack-row tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci). D5-AC-5, D5-AC-6, D5-AC-7 and D5-AC-10 SUCCEEDED on both hosts.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-03, PH3-08
    - Findings: TPR-M-12
    - _Requirements: 10.8, 10.9, 10.15, 10.19, 10.30, 10.31, 13.22, 12.23_

  - [ ] 3.6 PH3-06 Trust_Store and Signer_Trust
    - Objective: Add the Trust_Store (D5.7): a versioned UTF-8 JSON file with a closed schema (at most 262,144 bytes and 1,024 keys, no BOM, duplicate keys and floats rejected) read only from `VK_TRUST_STORE_FILE` or `--trust-store`. Each key has a key id, a public key, a status of `ACTIVE`, `ROTATED` or `REVOKED`, and a validity interval. Signer_Trust is `TRUSTED`, `UNTRUSTED_SIGNER` or `NOT_EVALUATED`, evaluated against the verifier's explicit `as_of` (AM-D5-6). Reason codes include `KEY_ROTATED` and `KEY_REVOKED`. A malformed or unreadable store gives `NOT_EVALUATED` with a reason and leaves validity and integrity unchanged. The embedded key is never trusted. The file is opened through the secure-open of PH1-04a. On Windows ACL-T of PH1-05 applies: a Trust_Store file that a trustee outside the four allowed ones can write gives `NOT_EVALUATED` with a reason code (`TRUST_STORE_UNSAFE`, name chosen at implementation), never `TRUSTED` (TPR-M-4).
    - Acceptance tests: D5-AC-8: A-16 and A-17 and the 24-combination truth table give `ESTABLISHED` in exactly 1 combination and every failure keeps validity and integrity unchanged (CP-30). D5-AC-2: 200 of 200 round trips with generated keys give `VALID`, `TRUSTED` and `ESTABLISHED` for `ACTIVE` and `ROTATED` (with `KEY_ROTATED` added). ACL-T (D10-AC-20): on Windows a Trust_Store that Users can write gives `NOT_EVALUATED` and never `TRUSTED`, and a POSIX mode bit is never accepted as Windows evidence.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the trust tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci). D5-AC-2 and D5-AC-8 SUCCEEDED on both hosts.
    - Rollback: RP-5 (publish a Trust_Store file with a higher `serial`) and RP-1 `git revert` of the code. A failed rollback: OD-D10-3.
    - Depends on: PH3-05, PH1-04a, PH1-05
    - Findings: TPR-M-4, TPR-M-5
    - _Requirements: 10.10, 10.11, 10.12, 10.13, 10.16, 10.17, 10.27, 10.28, 10.37, 13.30_

  - [ ] 3.7 PH3-07 Separate results and the OD-D10-4 distinction
    - Objective: Report Signature_Validity, Signer_Trust, manifest integrity, authenticity (`ESTABLISHED` only when `VALID`, `TRUSTED` and integrity `VERIFIED`) and verdict correctness as separate results. Never report or describe complete archive-byte integrity as established, because no check inside the Bundle covers the zip container bytes outside the verified region (10.36, OD-D10-4). Show an embedded signing time or `written_at` only as a claimed time (AM-D5-7). Run `wording-scan` rules WS-1 and WS-2 of PH1-03a over docs, UI source, API descriptions, CLI strings and MCP results for any "byte-for-byte intact" claim. This task adds no scanner of its own (TPR-L-1).
    - Acceptance tests: D5-AC-8 (authenticity truth table, CP-30). D5-AC-13 wording part: 0 uses of "authenticated", "signed" or "verified" for an unsigned Bundle, and 0 "byte-for-byte intact" claims outside a documented negation. A test changes one container byte outside the verified region and shows no check claims complete archive-byte integrity.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the result-separation tests and the wording scan with `-rA` on each host. D5-AC-8 and the wording part of D5-AC-13 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-06
    - _Requirements: 10.8, 10.13, 10.14, 10.32, 10.33, 10.36_

  - [ ] 3.8 PH3-08 Archive validation checks Z-5 to Z-14
    - Objective: In `_check_zip_safety` of `core/src/verdictkit/bundle.py` add Z-5 (case-insensitive name collision), Z-6 (NFC collision), Z-10 and Z-11 (a colon in a name: drive letter and alternate data stream), Z-12 (reserved device names), Z-13 (trailing dot or space) and Z-14 (symbolic-link member through `external_attr`). Add regression tests for Z-1 to Z-4, Z-7 to Z-9, Z-15 and Z-16 that assert `BundleFormatError`, a mutation guard and property P-o.
    - Acceptance tests: D8-AC-14: each Z case is rejected or returns `UNVERIFIABLE`, never `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID`, with 0 files written outside the scratch directory. The mutation guard disables each added check in a copy and at least 1 test fails. P-o: 200 of 200 examples (CP-45). Results are identical on both hosts. Legacy replay gate (D10.11 TR-14, D10-AC-23): after this change the five corpus Bundles of PH3-01 and `examples/stub_claimtype/golden.vkb` replay with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, 0 `UNVERIFIABLE` comes from a new check, the SHA-256 of each corpus file is unchanged, and an unsigned Bundle is still accepted. A new check that rejects a baseline Bundle is a defect, and the check is fixed.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the archive tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci) and the mutation-guard run. D8-AC-14 SUCCEEDED on both hosts.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-01, PH3-02
    - Findings: TPR-M-12
    - _Requirements: 13.6, 13.21, 13.14, 13.22, 12.23_

  - [ ] 3.9 PH3-09 Cryptographic adversarial vectors and the Bundle properties
    - Objective: Add the vector suite: every small-order encoding, non-canonical encodings (including a `y` value at or above the field prime), 31- and 33-byte keys, the all-zero and identity keys, a small-order or non-canonical `R`, `S+L`, a universal signature, and truncated and wrong-algorithm signatures (AM-D5-3). Run it on both host classes and again after every `cryptography` change, with a mutation guard for each verifier check. Add properties P-a, P-b and P-c. P-a is stated over the verified region (the canonical manifest, every manifest-listed member, the signature envelope and the embedded public key, OD-D10-4). A byte of the zip container outside that region is outside the property.
    - Acceptance tests: D8-AC-13: 0 `VALID` where a vector forbids it, and the mutation guard finds a failure once a check is disabled. D5-AC-16 and D8-AC-2: P-a, P-b and P-c hold for 200 of 200 examples each (CP-29, CP-31). P-a excludes `REPRODUCED`, `REPRODUCED_ACROSS_ENV`, `VALID` and `ESTABLISHED` for a changed byte in the verified region.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the vector and property runs with `-rA` on each host (HYPOTHESIS_PROFILE=ci) and the mutation-guard run. D8-AC-13, D5-AC-16 and the P-a to P-c part of D8-AC-2 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-06, PH3-07, PH3-08
    - _Requirements: 13.21, 13.5, 13.6, 10.15, 10.22_

  - [ ] 3.10 PH3-10 Compatibility and determinism checks
    - Objective: Add the tests that show: unsigned Bundles are byte-identical to the baseline for the same case, clock and Examination_Semantics (DR-7 hashes); `golden.vkb` verifies and replays with `UNSIGNED` and `NOT_ESTABLISHED`; every legacy corpus Bundle replays with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`; signed Bundles are byte-identical with a fixed clock and key; the authenticity JSON is byte-identical on Windows and Linux (D5.9 DR-2). No source change unless a defect is found and recorded (13.9).
    - Acceptance tests: D5-AC-1: 0 member-hash differences, 0 zip-hash differences on the same host, 0 edits to the two named bundle test files. D5-AC-15: 0 differing bytes between Windows and Linux outputs. D8-AC-15 (DR-5 legacy corpus leg) and D9-AC-8: 0 `DIVERGED`, 0 `UNVERIFIABLE`.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the compatibility tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci) and the corpus replays. D5-AC-1, D5-AC-15 and D9-AC-8 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-09
    - _Requirements: 10.5, 10.7, 10.22, 10.32, 12.23, 13.22, 2.2_

  - [ ] 3.11 PH3-11 Signature fields in CLI, API presenter and MCP
    - Objective: In `core/src/verdictkit/cli.py`, `core/src/verdictkit/api/presenter.py` and `core/src/verdictkit/mcp_server.py` (`replay_bundle`, `explain_verdict`) show Signature_Validity, Signer_Trust, authenticity and the signer fingerprint as separate fields, with the Trust_Store `serial` and `sha256`. The API schema, the examples and the version constant change only in the PH3-12 lockstep commit, so the contract tests stay green in between.
    - Acceptance tests: D5-AC-13 (CLI and API parts): 4 separate results on 2 surfaces and 0 forbidden phrases. D5-AC-17 and D4-AC-19: `replay_bundle` and `explain_verdict` over stdio on a signed Bundle return `signatureValidity` and `signerTrust` as D5.3 defines, schema-valid.
    - Environment: Windows and Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the CLI, presenter and stdio tests with `-rA` on Windows and in the image. D5-AC-13 (CLI and API parts), D5-AC-17 and D4-AC-19 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-06, PH2-03
    - _Requirements: 10.20, 9.8, 10.33_

  - [ ] 3.12 PH3-12 Contract 2.0.0 in one lockstep change
    - Objective: Change every statement of the contract version in one commit (AM-D5-12): a dependency-free `CONTRACT_VERSION` module read by `api/server.py`, `api/presenter.py` and `mcp_server.py`; `info.version` and `ContractVersion` in `api/openapi.yaml`; the constant in `ui-kit/src/api.ts`; `contractVersion` in `api/examples/*.json`; the MCP replay result; the tests that pin `1.1.0`. Describe the D5.8 rows in the schema (authenticity fields, health `commitSha` and the 503 `unavailable` body, the owner cookie, 429 `RATE_LIMITED`). Classify the Examination_Semantics id that PH3-02 adds as COMPATIBLE or BREAKING in the same event (D5.12 form). The classification moved here from the deferred PH6-11, and the `as_of` key and the snapshot retrieval date are deferred with PH6-07 and PH6-11. Add a migration section to `docs/API_CONTRACT.md` with a before example, an after example and a client checklist for each BREAKING row, with COMPATIBLE and BREAKING labels (AM-D5-10). Change `ui/judge/app.js` (`CONTRACT`) and the visible label in `ui/judge/index.html` only.
    - Acceptance tests: D5-AC-11: examples and responses validate against `api/openapi.yaml` and every version constant is equal, with the old `VERIFIED` mutation row still failing. D5-AC-12: 0 schema errors including the 503 and 429 bodies. D5-AC-18: 0 unlabelled changes. D5-AC-19: only the constant and the label differ in `ui/judge`, `tests/ui/test_judge_preview.py` passes, 0 changed submission lines, 0 changed refs. D10-AC-7: a tolerant 1.1.0 client works, a strict 1.1.0 validator fails on exactly the BREAKING rows, each refusal names both versions, 1.1.0 Bundles verify and replay.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract tests/api tests/ui` on each host, `npm test` for `ui-kit`, `git diff 84df25c -- ui/judge` and the frozen-ref commands. D5-AC-11, D5-AC-12, D5-AC-18, D5-AC-19 and D10-AC-7 SUCCEEDED.
    - Rollback: RP-2 (one revert of the lockstep change, including the `ui/judge` constant; `GET /api/v1/health` shows the previous `contractVersion` and the contract tests pass). A failed rollback: OD-D10-3.
    - Depends on: PH3-11
    - _Requirements: 10.21, 10.34, 10.35, 1.2, 1.8_

  - [ ] 3.13 PH3-13 Signing documentation
    - Objective: Write `docs/SIGNING.md`: the three statements of 10.23 (a valid signature establishes who signed the bytes and does not establish that the claim is true, that the timestamp is trusted, or that the signer's key was not compromised), the OD-D10-4 limit statement (manifest integrity, signature authenticity and complete archive-byte integrity are three results, exact archive-byte verification needs an external trusted digest, container bytes outside the verified region are covered by no check), key provisioning, the Trust_Store format, rotation, revocation, reason codes and the named source of the small-order table (AM-D5-1).
    - Acceptance tests: D5-AC-14: 3 of 3 statements present. The OD-D10-4 limit statement is present. `wording-scan` rules WS-1 and WS-2 of PH1-03a find 0 forbidden phrases and 0 "byte-for-byte intact" claims.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the document-content test run with `-rA` and the publication scan over the new file (counts per class). D5-AC-14 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-07
    - _Requirements: 10.23, 10.36_

  - [ ] 3.14 PH3-14 Phase 3 checkpoint
    - Objective: Run the Phase 3 targeted regression on both host classes, `ruff check .`, the ledger lint, the publication scan and the frozen-ref check. Write the track Execution_Record for Phase 3 (4.4) with the rollback fields (4.5) and the Kiro attribution rows (4.7) as in PH1-18, update the Phase 3 checkboxes in the same change (4.9), and name the verified checkpoint commit.
    - Acceptance tests: D8-AC-30: each host recorded separately with 0 unexplained divergence. D8-AC-29: 0 changed lines in existing tests except the approved hunks. D9-AC-16: 4 of 4 ref values and 0 Submission_Artifacts differences. `ruff check .` has 0 violations and `uv.lock` shows 0 added runtime packages. The legacy corpus and `golden.vkb` replay again at this checkpoint with an equal Verdict_Hash (D10-AC-23).
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the regression set on each host (`-rA`), `uv run --no-sync ruff check .`, the lint, the scan and the frozen-ref commands. The track record lists each Phase 3 criterion as SUCCEEDED, FAILED or UNVERIFIED. The checkpoint commit is verified only when its regression set has a SUCCEEDED record.
    - Rollback: RP-1 `git revert` of the phase's commit range back to the previous verified checkpoint. If the rollback does not complete, the RP row is FAILED, the track is incomplete and RB-18 stays open until the branch is recovered to a verified checkpoint (OD-D10-3, 4.6).
    - Depends on: PH3-01, PH3-02, PH3-03, PH3-04, PH3-05, PH3-06, PH3-07, PH3-08, PH3-09, PH3-10, PH3-11, PH3-12, PH3-13
    - _Requirements: 13.15, 4.4, 4.5, 4.7, 4.9, 1.2_

- [ ] 4. Phase 4: Kiro automatic hooks, contained execution, genuine MCP invocation and attribution evidence (autonomous parts only)
  - Goal: Build and test everything the agent can build for verified hook execution: matchers, runner, hook files, evidence and attribution tooling, the review pin and the owner kits. Kiro-side captures and the contained environment are owner actions (OA-04, OA-05, OA-06), so every hook stays UNVERIFIED until those records exist.
  - _Requirements: 3.4, 3.6, 3.7, 3.8, 3.10, 3.13, 4.4, 4.9, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 8.13, 8.14, 8.15, 8.16, 8.17, 8.18, 8.19, 8.20, 9.11, 9.12, 9.15, 13.15, 16.1, 16.2_

  - [ ] 4.1 PH4-01 Hook matchers, corpus and matcher tests
    - Objective: Add the eight matcher expressions of D3.4 (HK-0 to HK-7) as the tested definitions in `tests/contract/test_hook_matchers.py`, the corpus `tests/contract/hook_matcher_corpus.json` (at least 2 matching and 2 non-matching paths per separator style for each hook), the real-tree property over `git ls-files` and path forms PF-1 to PF-7, the lint and sentinel tests (HM-T1 to HM-T4), and the JavaScript check `scripts/hooks/check_matchers.cjs`. The hook files take these expressions in PH4-03, where HM-T5 checks that they equal the tested text.
    - Acceptance tests: D3-AC-1: 100 percent of corpus rows classified as expected, and per hook at least 2 positive paths per separator style, 2 negative paths, 1 nested, 1 spaced, 1 absolute Windows and 1 absolute POSIX path. D3-AC-2: 0 mismatches over every tracked file and PF-1 to PF-7, the uncovered `.py` files equal the allowlist (17 at `84df25c`), and the counts of D3.4 are re-derived. D3-AC-3: 0 forbidden constructs, `search` equals `fullmatch` on every corpus row, the JavaScript result equals the Python result on every row, and each old core, reel and quote matcher fails at least one backslash positive.
    - Environment: Windows for the Python and Node parts. The Linux leg runs in the image on Linux_Docker_Host or in CI (dispatch needs OA-01).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_hook_matchers.py`, `node scripts/hooks/check_matchers.cjs` and the Linux leg of the Python test. D3-AC-1, D3-AC-2 and D3-AC-3 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-10, PH2-07
    - _Requirements: 8.3, 8.4, 8.9_

  - [ ] 4.2 PH4-02 Hook runner
    - Objective: Write `scripts/hooks/vk_hook.py` (stdlib only) and `tests/contract/test_hook_runner.py` per D3.6. The runner executes the reviewed argument list with no shell and a closed environment list by name (AM-D3-6). It has its own deadline shorter than the Kiro timeout (budget = timeout minus the larger of 5 s and 10 percent) that kills the process tree and prints `VK_HOOK_TIMEOUT` with the hook name and the timeout value. It uses a run lock, a recursion guard (`VK_HOOK_DEPTH`), a state directory under `artifacts/hooks` that must not be a symlink or junction, an output cap, and it opens no socket. It changes no tracked file and no git index entry.
    - Acceptance tests: D3-AC-5: on timeout the child is killed with no surviving process, exit 124 and a record within the budget plus 5 s. 4 simultaneous runners never overlap and each ends with a record. A killed lock holder lets the next runner start within 1 s. `VK_HOOK_DEPTH` gives exit 76 and no child. A child that prints 1 MiB gives at most 10,000 characters and hashes over all bytes. Absent, closed, oversized or non-JSON stdin never hangs beyond 3 s. A symlinked state directory gives exit 78. D3-AC-8: 0 tracked files change before and after each run, and the tests pass with the network disabled on Linux. D3-AC-26: a benign-named canary variable not on the list is absent in the child, a secret-named one is absent and listed by name only, and 0 variable values appear in records, stdout or stderr other than values the runner set.
    - Environment: Windows. The Linux leg runs in the image or in CI. D3-AC-15 (failure feedback shown in the Kiro session) is an owner row (OA-05).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_hook_runner.py` on Windows and in the image, the before and after `git status --porcelain` and tracked-file hash comparison, and `uv run --no-sync ruff check .`. D3-AC-5, D3-AC-8 and D3-AC-26 SUCCEEDED.
    - Rollback: RP-7 (a new commit restoring `scripts/hooks/` from `84df25c`, then the HM-T5 hash check and a renewed review, 8.17) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH4-01
    - _Requirements: 8.5, 8.6, 8.10, 8.18, 8.12_

  - [ ] 4.3 PH4-03 Hook files
    - Objective: Rewrite `.kiro/hooks/*.json` to the Hook_Set of D3.4: hooks HK-0 (marker) to HK-7 (matcher and runner tests), trigger `PostFileSave`, action type `command`, `enabled` true, each command exactly `uv run --no-sync --offline python scripts/hooks/vk_hook.py` followed by the runner id, with none of the forbidden shell characters and no `{{`. Each timeout is an integer from 1 to 600 that is at least the longest recorded duration of the exact command text. Commands are read-only verification commands. No hook argument contains `--deselect`, `-k` or `--ignore` for `test_mcp_server.py` (8.13). A failure of that test on Windows after PH1-10 is a new regression (1.13). Commands run under PowerShell and `cmd`.
    - Acceptance tests: D3-AC-4 (HM-T5 file checks): trigger, canonical command, forbidden characters, timeout range and floor, boolean `enabled`, no agent action, HK-0 equals the union of the other seven scopes. D3-AC-9: at least 3 runs per hook per host class, cold and warm, with the exact command text, and each timeout is at least the longest recorded duration and at least 4 times the slowest warm run (ASSUMED rule) and never 0. D3-AC-24: for matrix rows 1 to 17, wall time and the number of runs of each test file per save are recorded (command part, MANUAL records), each test file runs at most once per save or the record states why, and the median is at most 60 s (ASSUMED) or OD-D3-5 is reopened.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_hook_matchers.py tests/contract/test_hook_runner.py`, each hook command text run through the `record` form (3 runs per hook, cold and warm) and the matrix-row timings. D3-AC-4, D3-AC-9 and the command part of D3-AC-24 SUCCEEDED.
    - Rollback: RP-7 (a new commit restoring `.kiro/hooks/` and `scripts/hooks/` from `84df25c`, the HM-T5 hash check, a renewed review) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH4-02
    - _Requirements: 8.1, 8.5, 8.8, 8.9, 8.12, 8.13, 8.14_

  - [ ] 4.4 PH4-04 Evidence and attribution tooling
    - Objective: Extend `scripts/hooks/vk_hook.py` with the record form (EV-1 to EV-10: one JSON line per run in `artifacts/hooks/evidence.jsonl` with a `prev_sha256` and `record_sha256` chain), the marker line, `verify-chain` (reports "consistent" or the first break, never "authentic"), the `record` form that takes the child's exit code directly, the ledger entry form LE-1 to LE-11, status labels ST-1 to ST-5 and attribution AT-1 to AT-4. A hook counts as automatic only when a Kiro-side artifact shows the same hook firing for the same path (AT-1). Fields that Kiro neither shows nor logs are labelled runner-observed. Nothing is reconstructed. Credits come only from a Kiro usage record, else `NOT_AVAILABLE`. Output is truncated to 10,000 characters.
    - Acceptance tests: D3-AC-6: `verify-chain` over at least 20 generated records, with one changed byte, a deleted record and a reordering each detected at that record, all D3.7 fields present, `started_utc` and `ended_utc` in ISO 8601 UTC with Z, and `duration_s` not negative from a monotonic clock. D3-AC-7: `AUTOMATIC_VERIFIED` only when AT-1 (a) to (e) all hold, a missing condition gives a lower value, `--manual` or a terminal stdin gives MANUAL, and the runner writes no attribution field. D3-AC-25 (checked by `wording-scan` rule WS-3 of PH1-03a, with no scanner of this task's own): 0 uses of tamper-proof, secure, authentic or signed for the guard, the chain or the marker, and a rewritten file verifies as consistent with the limit stated. Owner rows D3-AC-12 and D3-AC-20 wait for OA-05.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_hook_runner.py`, the `verify-chain` run and the wording scan. D3-AC-6, D3-AC-7 and D3-AC-25 SUCCEEDED. D3-AC-12 and D3-AC-20 stay UNVERIFIED until OA-05.
    - Rollback: RP-7 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH4-03
    - Findings: L-5
    - _Requirements: 8.2, 8.15, 3.6, 3.7, 3.8, 3.13, 16.1, 16.2_

  - [ ] 4.5 PH4-05 Pin and review gate
    - Objective: Add the HM-T5 hash check over `.kiro/hooks/*.json`, `scripts/hooks/*`, `tests/contract/hook_matcher_corpus.json`, the runner's environment allowlist and `.kiro/settings/mcp.json`, over LF-normalized bytes, compared with the hashes in `docs/next-phase/hooks/HOOK_SECURITY_REVIEW.md` (AM-D3-7). Any added, removed or changed file, new or removed hook file, or changed `enabled` value fails with "renewed review required", keeps the affected hooks at ST-1, and stops dependent evidence from counting until a reviewer other than the agent records a renewed review. The agent cannot record or waive that review. The agent lists the hashes of the pinned files as `PENDING_REVIEW` rows with empty reviewer fields and never records a hash as reviewed, and the check counts a hash only from a row that names a reviewer who is not the agent (TPR-H-4). Add the pre-trust review record template with one row for each of PR-1 to PR-11 (verdict, reviewer, date, commit, file hashes).
    - Acceptance tests: D3-AC-27: a one-byte change in each pinned file, a new hook file, a removed hook file and a changed `enabled` value each fail with renewed review required, a Windows (CRLF) checkout and a Linux (LF) checkout give the same hashes, and the unchanged tree passes. D10-AC-6: 0 members of the 8.19 set missing from either hash set, an added file under `scripts/hooks/` changes the set hash and fails, and a renewed-review record whose reviewer is the agent is rejected. Owner rows D3-AC-10 and D3-AC-11 wait for OA-05 and OA-06.
    - Environment: Windows. The Linux leg runs in the image or in CI.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_hook_matchers.py` on Windows and in the image. D3-AC-27 and D10-AC-6 SUCCEEDED.
    - Rollback: RP-7 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH4-03, PH2-07
    - Findings: M-5
    - _Requirements: 8.17, 8.19_

  - [ ] 4.6 PH4-06 Untrusted-workspace, busy and skipped handling
    - Objective: In the evidence tooling map `hooks.v2.executionDisabledUntrustedWorkspace` to `UNVERIFIED` with that reason, never failed and never passing (8.11). Map `BUSY_TIMEOUT`, `RECURSION_BLOCKED`, `CONFIG_ERROR`, `RUNNER_ERROR`, `TIMEOUT`, a hook Kiro did not run and a hook whose child did not start to NOT_VALIDATED (AM-D3-3). A save is validated only when every hook that the reference matcher assigns to it has a PASSED record. A hook with no record is reported NOT_VALIDATED and never omitted. This task changes a pinned file (`scripts/hooks/vk_hook.py`) after PH4-05 pinned the set, so the pinned hashes stay `PENDING_REVIEW` until OA-06, which follows this task and PH4-10 (TPR-H-4).
    - Acceptance tests: D3-AC-23: a table-driven test over every outcome of D3.6 shows 0 outcomes other than PASSED map to SUCCEEDED or count as validation. A save with one hook held in BUSY_TIMEOUT by a held lock is reported NOT_VALIDATED. A hook assigned by the reference matcher with no record is reported NOT_VALIDATED (CP-19). Owner row D3-AC-13 (step S9 log and ledger) waits for OA-05.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_hook_runner.py`. D3-AC-23 SUCCEEDED.
    - Rollback: RP-7 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH4-04
    - _Requirements: 8.11, 3.7_

  - [ ] 4.7 PH4-07 Documentation labels and guarantee wording
    - Objective: Write the hook status table and wording in new files under `docs/next-phase/hooks/` (no Submission_Artifacts file is edited, 1.8). Each hook has a status from ST-1 to ST-5 per host class and is labelled `UNVERIFIED` unless it has ST-5. The text states that hooks are a development guardrail on the file operations that probe U-1 determines, that runtime guarantees come from code and CI, and that firing on a save by the user stays `UNVERIFIED` until a recorded Kiro observation shows it. The guard, the chain and the marker are never called tamper-proof, secure, authentic or signed.
    - Acceptance tests: D3-AC-19: each hook has a status from ST-1 to ST-5 per host class, each hook without ST-5 is labelled `UNVERIFIED`, and the guardrail statement is present. D3-AC-25: 0 forbidden wording uses in `docs/next-phase`, the runner source and its output strings (`wording-scan` rule WS-3 of PH1-03a).
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the document-content and wording test run with `-rA` and the publication scan over the new files (counts per class). D3-AC-19 and D3-AC-25 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH4-04
    - _Requirements: 8.7, 3.4, 3.10_

  - [ ] 4.8 PH4-08 Contained_Hook_Environment kit
    - Objective: Add the owner kit under `docs/next-phase/hooks/` for conditions CE-1 to CE-8: a session record template (environment class, virtual machine or restricted account, recorded without names), the tool-version pin record, the clone refresh from a reviewed commit, the hash-pin check of PH4-05, the evidence export as Private_Original plus Sanitized_Copy with hashes, and the record of the outbound-block state or the remaining exposure. The classifier rule: without a session record that meets CE-1 to CE-8 every hook stays at ST-3 or lower and nothing counts as automatic execution. The environment itself is OA-04.
    - Acceptance tests: D8-AC-25 (test side): a table test shows that without a complete session record the classifier gives at most ST-3 and 0 `AUTOMATIC_VERIFIED` for every hook, and each unmet condition keeps its dependent hooks `UNVERIFIED`. The template has class fields only, with no field for an account name, host name or SID. Owner rows D8-AC-25 (review of a real session record) and D3-AC-21 wait for OA-04.
    - Environment: Windows. The environment is OA-04.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the classifier test run with `-rA` and the publication scan over the kit files. The test-side rows SUCCEEDED. D8-AC-25 and D3-AC-21 stay UNVERIFIED until OA-04.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH4-05
    - Findings: M-5, L-5
    - _Requirements: 8.20, 8.16, 8.18, 3.13_

  - [ ] 4.9 PH4-09 Kiro MCP verification kit
    - Objective: Add the owner kit under `docs/next-phase/kiro-mcp/`: the capture protocol for the four tools called from inside Kiro (KM-1 to KM-8: one ledger row per call with the tool name, three hashes, the result, an ISO 8601 date and the label "captured from Kiro"), the controlled probes for the dropping of empty arrays and objects, the `UNVERIFIED` label for a missing capture (any stdio-client result is labelled as obtained outside Kiro), and the procedure for reading a Kiro usage record (credits only from that record, else `NOT_AVAILABLE`).
    - Acceptance tests: D4-AC-16 (kit side): a rule test shows that a row without a capture cannot be `SUCCEEDED`, and a stdio-client result carries the label obtained outside Kiro. D9-AC-10 (kit side): the Historical_Audit results H6 and H8 are never cited as evidence for the Release_Candidate. Owner-run KM-1 to KM-8 wait for OA-05.
    - Environment: Windows. The Kiro captures are OA-05.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the rule-test run with `-rA` and the publication scan over the kit files. The kit-side rows SUCCEEDED. D4-AC-16 stays UNVERIFIED until OA-05.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH2-09, PH4-04
    - Findings: L-5
    - _Requirements: 9.11, 9.12, 9.15, 3.6, 3.7, 16.1, 16.2_

  - [ ] 4.10 PH4-10 Phase 4 checkpoint
    - Objective: Run each hook command through the `record` form on Windows (exit code read directly), compare the tracked files and the git index before and after, run the Phase 4 targeted regression on both host classes, `ruff check .`, the ledger lint, the publication scan and the frozen-ref check. Write the track Execution_Record for Phase 4 (4.4) with each hook's status per host class, the rollback fields (4.5) and the Kiro attribution rows (4.7) as in PH1-18, update the Phase 4 checkboxes in the same change (4.9), and name the verified checkpoint commit. No hook is counted as automatic execution without OA-05 captures. The hashes of the pinned set are listed `PENDING_REVIEW`, and this checkpoint claims no review of them: OA-06 follows PH4-06 and this task, and OA-05 follows OA-04 and OA-06 (TPR-H-4).
    - Acceptance tests: Each hook command exits 0 on Windows and leaves the tracked-file and index diff empty (D3-AC-8). D3-AC-1 to D3-AC-9, D3-AC-19, D3-AC-23, D3-AC-25 to D3-AC-27 and D10-AC-6 SUCCEEDED. Every hook without an AT-1 record is labelled `UNVERIFIED`. D8-AC-30: each host recorded separately with 0 unexplained divergence. `ruff check .` has 0 violations.
    - Environment: Windows. The Linux leg runs in the image or in CI.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for each hook command through `record`, the regression set on each host (`-rA`), `uv run --no-sync ruff check .`, the lint and the scan. The track record lists each Phase 4 criterion as SUCCEEDED, FAILED or UNVERIFIED. The checkpoint commit is verified only when its regression set has a SUCCEEDED record.
    - Rollback: RP-7 and RP-1 `git revert` of the phase's commit range back to the previous verified checkpoint. If the rollback does not complete, the RP row is FAILED, the track is incomplete and RB-18 stays open until the branch is recovered to a verified checkpoint (OD-D10-3, 4.6).
    - Depends on: PH4-01, PH4-02, PH4-03, PH4-04, PH4-05, PH4-06, PH4-07, PH4-08, PH4-09
    - _Requirements: 13.15, 4.4, 4.5, 4.7, 4.9_

- [ ] 5. Phase 5: Professional UI, accessibility and local deployment hardening
  - Goal: Ship one design-token set, the unified landing page and onboarding, accessible and contract-2.0.0-aware UIs, and a hardened local deployment (headers, caps, case ownership, credentials, retention, readiness, reproducible image). Nothing is deployed publicly.
  - _Requirements: 1.17, 2.1, 2.3, 2.4, 2.5, 4.4, 4.9, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.11, 7.12, 7.13, 7.14, 7.15, 7.16, 7.17, 7.18, 7.23, 7.24, 7.25, 7.26, 10.20, 10.32, 10.33, 10.34, 10.36, 13.15, 13.17_

  - [ ] 5.1 PH5-01 Design tokens and contrast pairs
    - Objective: Add `ui-kit/src/tokens.css` and `ui-kit/src/tokens.ts` as the one token set (colour, type scale, spacing, focus style). `ui-kit/src/theme.css` imports the tokens and keeps its class names. Neither app defines its own colour, type-scale, spacing or focus-style value outside the set. Add the contrast test over the pairs of D1.4.
    - Acceptance tests: D1 AC-1: a Vitest scan finds 0 hex colours, `px` font sizes or raw spacing values outside `tokens.css`. D1 AC-2: 0 pairs below 4.5 (normal text) or 3 (large text and UI boundaries).
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm run typecheck`, `npm test` and `npm run build`. D1 AC-1 and D1 AC-2 SUCCEEDED.
    - Rollback: RP-1 `git revert` (the baseline UI is on `master`). A failed rollback: OD-D10-3.
    - Depends on: PH4-10
    - _Requirements: 5.1, 7.1_

  - [ ] 5.2 PH5-02 Status vocabulary, DecimalText and verdict view
    - Objective: Add `ui-kit/src/status.tsx` (status badges; an unknown value renders `UNRECOGNISED` with a neutral tone), `ui-kit/src/decimal.tsx` (`DecimalText`, `compareDecimalStrings`) and `ui-kit/src/chartGeometry.ts` (the one file allowed to use floats), and update the verdict view in `ui-kit/src/components.tsx`: headline, every finding with basis and status, the confidence scope sentence and Isolation_Mode visible without interaction. Put `SYNTHETIC_DEMO` and `ILLUSTRATIVE` labels in the same container as the content they qualify. Use the wording "verified at N grid points" and never "all values", "every value" or "any value". Show a historical Bundle isolation label apart from the current server label.
    - Acceptance tests: D1 AC-3 (the three `api/examples` outcomes show headline, findings, scope sentence and isolation with no click), AC-4 (0 empty labels, 0 positive tones for an unknown value), AC-5, D1 AC-6 (0 forbidden phrases, checked by `wording-scan` rule WS-4 of PH1-03a), AC-7 (a table of at least 50 fixed strings gives 0 mismatches and the scan finds 0 uses of `Number(`, `parseFloat`, `toFixed`, `toLocaleString` or `Intl` outside `chartGeometry.ts`). D2-AC-21: a Bundle recorded UNENFORCED on a server that is ENFORCED shows both labels, distinct. CP-1 and CP-2.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm run typecheck`, `npm test` and `npm run build`. D1 AC-3 to AC-7 and D2-AC-21 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-01
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 2.1, 2.4_

  - [ ] 5.3 PH5-03 AppShell, states and ErrorPanel
    - Objective: Add `ui-kit/src/shell.tsx` (`AppShell`, `SkipLink`, `SiteNav`) and `ui-kit/src/feedback.tsx` (`ErrorPanel`, `EmptyState`, `LiveStatus`, `LoadingNote`). Add `ApiUnavailableError` to `ui-kit/src/api.ts`. Update both apps' `App.tsx` for loading, empty, error and API-unavailable states and a layout from 320 to 1920 px without horizontal scroll. `ErrorPanel` shows the code, a reason and the next step. Submitted input is retained except sealed claimed-figure fields, which show empty with a visible note after the API accepts the case and are never re-populated from a response (DD-9). `describeError` keeps its output format so the `PRIVACY_REJECTED` E2E check passes.
    - Acceptance tests: D1 AC-9: `ErrorPanel` shows code, reason and next step for each contract error fixture and for a network failure, and form values remain after a failed `createCase`. D1 AC-8 (15 of 15 viewport and page combinations without horizontal scroll) needs a browser and stays UNVERIFIED until PH5-07 or PH7-17 runs it on Linux or CI. CP-4.
    - Environment: Windows for the jsdom tests. The browser leg runs on Linux or CI.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm run typecheck`, `npm test` and `npm run build`. D1 AC-9 SUCCEEDED. D1 AC-8 stays UNVERIFIED until a browser run exists.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-02
    - _Requirements: 5.7, 5.8_

  - [ ] 5.4 PH5-04 Landing page and Onboarding_Flow
    - Objective: Add the workspace `apps/landing/web/` (`package.json`, `tsconfig.json`, `vite.config.ts`, `index.html` with title "VerdictKit — Evidence Verification Workspace" and `lang="en"`, `src/main.tsx`, `src/App.tsx`, `src/Onboarding.tsx`, tests), the entry in the root `package.json` workspaces, `ui-kit/src/examples/` and `requestTimeoutMs` in `ui-kit/src/api.ts`. The page has a purpose text of 1 to 100 words, exactly one link each to Quote_App and Reel_App, the release boundaries in visible text, and no statistic, customer count, accuracy figure or testimonial. The Onboarding_Flow has five steps in order (freeze the claim, seal the outcome, examine blind, reveal and compare, download and replay), uses only labelled examples, and shows only the verdict returned by the API. If the API is unreachable the page shows a message within 10 s of the first failed request and keeps the static content and both links.
    - Acceptance tests: D1 AC-10 (never-resolving fetch with fake timers: message at or before 10000 ms, no verdict element, both links). D1 AC-11 (five steps in order, exactly 2 app anchors, purpose of 1 to 100 words, 0 statistic or testimonial matches, required title, verdict equals the mocked API response, fixture `expect` strings absent from the DOM). D1 AC-12 (failure keeps inputs, shows an alert and no verdict, retry works). CP-3.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm ci`, `npm run typecheck`, `npm test` and `npm run build` over all workspaces including the landing workspace. D1 AC-10, AC-11 and AC-12 SUCCEEDED.
    - Rollback: RP-1 `git revert`. The landing route can be removed while the app roots stay unchanged. A failed rollback: OD-D10-3.
    - Depends on: PH5-03
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11_

  - [ ] 5.5 PH5-05 Contract 2.0.0 display in the UI_Kit
    - Objective: Update `ui-kit/src/types.ts`, `ui-kit/src/status.tsx` and `ui-kit/src/components.tsx` to show Signature_Validity, Signer_Trust, authenticity and the signer fingerprint as separate fields. An unsigned Bundle is never described as authenticated. No text says or implies that a Bundle is byte-for-byte intact (OD-D10-4). A signing time is shown only as a claimed time. `ui-kit/src/api.ts` refuses another major contract version with an error that names both versions. `ui/judge` is not touched here.
    - Acceptance tests: D5-AC-13 UI part: 4 separate results, label text asserted by UI tests, and a scan (`wording-scan` rules WS-1 and WS-2 of PH1-03a) with 0 uses of "authenticated", "signed" or "verified" for an unsigned Bundle and 0 "byte-for-byte intact" claims. D10-AC-7 UI leg: the UI_Kit refuses a server of another major version with an error that names both versions.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm run typecheck`, `npm test` and `npm run build`. D5-AC-13 (UI part) and the UI leg of D10-AC-7 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH3-12, PH5-02
    - _Requirements: 10.20, 10.32, 10.33, 10.34, 10.36_

  - [ ] 5.6 PH5-06 Accessibility fixes and scans
    - Objective: Make the three pages and the onboarding steps conform to the WCAG_2_2_AA criteria of 7.1: skip link first in tab order, keyboard operation, visible focus, form labels, error identification, valid `lang`, status messages in live regions. Run axe-core scans of the three pages and each onboarding step and record the tool name, tool version, URL or step, timestamp, finding count and identifiers. A scan that cannot complete makes that page or flow UNVERIFIED. Manual keyboard-only and screen-reader checks need a human tester. Without a record each such criterion is labelled UNVERIFIED (7.4).
    - Acceptance tests: D1 AC-13: axe scans of the three pages and the onboarding steps give 0 violations, or UNVERIFIED if a scan cannot run. D1 AC-14: the skip link is first in tab order, every control is reachable and operable by keyboard (`userEvent`), and the focus style is present in the computed style (browser). The jsdom units run on Windows and the browser legs on Linux or CI.
    - Environment: Windows. The browser legs run on Linux or CI.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm test`, each axe scan (tool, version, target, timestamp, count) and the browser legs when available. D1 AC-13 and AC-14 jsdom parts SUCCEEDED. The browser parts and manual checks stay UNVERIFIED until a record exists.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-04, PH5-05
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 6.7_

  - [ ] 5.7 PH5-07 UI tests, ports and build gates
    - Objective: Add a unit test for each modernized component of D1 AC-15 that asserts its label and status text and fails when either is removed (mutation check). Add the source scan that finds 0 uses of `localStorage`, `sessionStorage`, `document.cookie`, `console`, `dangerouslySetInnerHTML`, `innerHTML` and `eval`. Make every port in `apps/*/web/vite.config.ts`, `scripts/ui_e2e.sh` and `tests/ui/e2e_browser.cjs` configurable with a documented default and no stop or reconfiguration of a process the run did not start (1.17). Update the browser E2E script additively (landing checks) with no baseline check removed or skipped.
    - Acceptance tests: D1 AC-15 (each test fails when its text is removed), AC-17 (0 matches), AC-18 (0 undocumented hard-coded 4173, 4174, 4175, 8000 or 5173), AC-16 (`typecheck`, `test`, `build` exit 0 for `ui-kit`, quote, reel and landing). The browser E2E passes 100 percent of the existing checks plus the landing checks and stays UNVERIFIED until it runs on Linux or CI. CP-5.
    - Environment: Windows. The browser E2E runs on Linux or CI.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm run typecheck`, `npm test`, `npm run build` and the two scans. D1 AC-15, AC-17, AC-18 and the npm part of AC-16 SUCCEEDED. The E2E part stays UNVERIFIED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-06
    - _Requirements: 5.9, 5.10, 2.3, 1.17, 6.10_

  - [ ] 5.8 PH5-08 Security headers, same-origin routing and CSRF rules
    - Objective: In `core/src/verdictkit/api/server.py` (`SafetyMiddleware` and every early return) and the edge configuration send `Content-Security-Policy` (no `*`, no `unsafe-inline`, no `unsafe-eval`), `X-Content-Type-Options: nosniff`, `Referrer-Policy` and `Cache-Control` on every response, including 401, 404, 405, 413, 429, 500 and early returns (gap G-6). Route same-origin with no CORS header. For POST, PATCH, PUT and DELETE apply AM-8: `Origin` equals `VK_PUBLIC_ORIGIN` when present and is required when the owner cookie is sent, `Sec-Fetch-Site` is `same-origin` when present, the declared content type is enforced (else 415), and the owner cookie is `SameSite=Strict`. HSTS `max-age` of at least 15552000 where TLS terminates.
    - Acceptance tests: D2-AC-5: 0 missing headers on every response class. D2-AC-6: no `*`, `unsafe-inline` or `unsafe-eval`, and 0 `securitypolicyviolation` events in the browser E2E on 3 pages. D2-AC-18: 0 absolute external URLs and 0 asset paths outside each base. D2-AC-27: a foreign `Origin`, a missing `Origin`, a cross-site `Sec-Fetch-Site` and a `text/plain` body each get 403 or 415 and change nothing, and the valid same-origin request succeeds. CP-10.
    - Environment: CI/VM. The local Linux_Docker_Host stands in and each record names its source (DD9-7).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the header, CSRF and route-check tests with `-rA` against a local stack (`--network none` where it permits). D2-AC-5, D2-AC-18 and D2-AC-27 SUCCEEDED. The browser leg of D2-AC-6 stays UNVERIFIED until a browser run exists.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-17, PH3-12
    - _Requirements: 7.5, 7.6_

  - [ ] 5.9 PH5-09 Request caps, rate limit, expiry and baseline measurement
    - Objective: Enforce the caps of 256 KiB for JSON and 8 MiB for Bundles with a 413 before processing and with no partial storage, the per-client rate limit (the 121st request in 60 s gets 429, with client-address handling behind the edge so that two clients are limited independently) and the 24 h case expiry. Measure p50 and p95 run latency and CPU per run at the target size and record them (D2-AC-14). The client address that the limits use is the socket peer, and `Forwarded`, `X-Forwarded-For` and `X-Real-IP` are honored only from a configured trusted proxy (7.27, D10.11 TR-11). Run the log-sentinel lifecycle of D2-AC-12 (a sentinel in a claimed figure and in a case id).
    - Acceptance tests: D2-AC-7: 256 KiB plus 1 byte of JSON and 8 MiB plus 1 byte for a replay give 413 and a stored-bytes delta of 0. D2-AC-8: 429 on the 121st request, and two clients limited independently. D2-AC-9: a clock-patched expiry test makes the case unreachable, removes evidence older than the expiry plus 1 h and keeps a blob a live case references (the real 24 h wait stays UNVERIFIED). D2-AC-14: the p50 and p95 values are recorded. D2-AC-12: the sentinel lifecycle leaves 0 sentinels in the logs (PH7-04 repeats the log sink across every entry point). D10-AC-21 (rate-limit leg): a spoofed `X-Forwarded-For` from an untrusted peer does not change which client is limited, rotating the header does not evade the limit, an absent trusted-proxy setting ignores every forwarded header, and a header from the trusted proxy is honored (negative tests).
    - Environment: CI/VM. The local Linux_Docker_Host stands in and each record names its source (DD9-7).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the cap, rate-limit and expiry tests with `-rA` and the measurement run. D2-AC-7, D2-AC-8, the clock-patched leg of D2-AC-9 and D2-AC-14 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-08
    - Findings: TPR-M-1, TPR-M-6
    - _Requirements: 7.11, 7.27, 2.3_

  - [ ] 5.10 PH5-10 Case ownership
    - Objective: Every route that carries a case id (read, change, stream, export; runs, evidence, outcome, events, Bundle, Bundle metadata) checks ownership against the server-set owner cookie, and trusts no client-supplied owner id (AM-6). A non-owner gets the same 404 `NOT_FOUND` as a nonexistent case, in status, body and headers. No deletion endpoint exists. A client abort leaves the server run in a terminal state, and there is no automatic retry. Add a route-enumeration test that fails when a route that carries a case id has no ownership check, and CU-1 to CU-8 under `tests/security/`. In the public profile a request is authenticated, and its ownership is checked, before a run slot, a replay namespace or an examination is allocated (D10.11 TR-11, CSI-5).
    - Acceptance tests: D2-AC-10 and D2-AC-25: 0 routes answer anything other than the nonexistent-case 404 for a foreign cookie and for no cookie, and 0 routes lack a check. D2-AC-19: the edge and the API each receive exactly 1 request, with 0 duplicates, when the upstream is slowed or reset. D2-AC-20: a client abort ends the server run in a terminal state and the UI text has no "cancelled". D8-AC-20: CU-1 to CU-8, 8 of 8. CP-7. D10-AC-21 (run leg): a request with no valid credential, or with a foreign cookie, allocates 0 run slots, 0 replay namespaces and 0 examinations.
    - Environment: CI/VM. The local Linux_Docker_Host stands in and each record names its source (DD9-7).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the route-enumeration and CU tests with `-rA`. D2-AC-10, D2-AC-19, D2-AC-20, D2-AC-25 and D8-AC-20 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-09
    - Findings: TPR-M-6
    - _Requirements: 7.23, 2.3, 2.4, 13.17, 7.27_

  - [ ] 5.11 PH5-11 Invitation credential policy and failed-attempt limit
    - Objective: Accept only invitation credentials that are each issued to one invitee out of band, carry at least 128 bits from the operating-system CSPRNG, and are stored only as a hash with a label, an expiry inside the demonstration window and a revocation flag (AM-7). The mechanism (edge entries with a graceful reload, or an API-side table in the custodian-only data directory with mode 0700) is chosen at implementation. Revoking one credential takes effect without a redeploy within a documented bound and leaves the others valid. No credential value appears in any log. No HTTP route lists, decrypts or deletes cases. Failed attempts are limited to 5 per 15 minutes per source and account (OD-D10-1), configurable within documented bounds. A value outside the bounds is rejected at start-up and not clamped. Over the limit the answer is 429 `RATE_LIMITED` with `Retry-After`. Authentication from the headers happens before an upload slot is taken (the hook of PH1-17), before a body byte is read, and before any run slot, replay namespace or examination is allocated (D10.11 TR-11, 7.27). The failed-attempt limit keys on the socket peer and the account, and forwarded-address headers count only from a configured trusted proxy. The storage rows of this task are CSI-4 and CSI-5 of the one credential inventory, and this task writes no second table of credential handling (TPR-L-2).
    - Acceptance tests: D2-AC-26: of 3 issued credentials the revoked one gets 401 within 60 s (ASSUMED) and the other 2 still work. D10-AC-25: the credential rows of this task cite CSI-4 and CSI-5 and no second table of credential handling exists. D10-AC-1: each issued value has at least 16 random bytes, each stored record holds a hash, a label, an expiry and a revocation flag and no value, a search of records, container output and logs for each issued value finds 0 matches, and a never-issued value gets 401 before any body byte is read. D10-AC-2: the limit of OD-D10-1 gives 429 over the limit while a valid credential from another source still works, and an out-of-range setting is rejected at start. D10-AC-3: 0 routes list, decrypt or delete cases. CP-8. UA-9 and D10-AC-21: an unauthenticated upload gets 401 with the slot count unchanged and 0 body bytes read, and the same holds for `POST /runs`. A spoofed `X-Forwarded-For` from an untrusted peer does not evade the limit of 5 failed attempts per 15 minutes, and rotating its value does not either. An absent trusted-proxy setting ignores every forwarded header, and a header from the trusted proxy is honored.
    - Environment: CI/VM. The local Linux_Docker_Host stands in and each record names its source (DD9-7).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the credential tests with `-rA`, the route enumeration and the log search. D2-AC-26, D10-AC-1, D10-AC-2 and D10-AC-3 SUCCEEDED. Credential issuance on a deployed instance is CD-05.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-10
    - Findings: TPR-M-6, TPR-L-2
    - _Requirements: 7.24, 2.3, 2.4, 7.27, 7.21_

  - [ ] 5.12 PH5-12 Retention and sweeper
    - Objective: In the API run service, draft store and evidence store delete an evidence blob only when no live case references it, no examination in flight uses it, and its age exceeds the case expiry plus 1 h. References are derived from live cases at each sweep under a lock that excludes put, freeze and run start. An unreadable or unparseable record deletes nothing, and a failed sweep is non-fatal. Replay namespaces are included. Cleanup never deletes or re-owns the vault, draft or socket directories. Add the stateful property P-h.
    - Acceptance tests: D2-AC-28: random interleavings, including a crash between put and freeze, delete 0 blobs that a live case references or an in-flight examination uses, in every one of 200 examples under the `ci` profile. D8-AC-21: the same test with replay namespaces added deletes 0 referenced blobs or namespaces. CP-6.
    - Environment: CI/VM. The local Linux_Docker_Host stands in and each record names its source (DD9-7).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the stateful property run with `-rA` and `HYPOTHESIS_PROFILE=ci`. D2-AC-28 and D8-AC-21 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH1-16, PH5-10
    - _Requirements: 7.25, 7.11, 13.17_

  - [ ] 5.13 PH5-13 Liveness, readiness and health
    - Objective: Add an internal liveness probe with no public route that confirms the API answers on the loopback interface and both child processes exist. `GET /api/v1/health` answers 200 only when the examiner socket re-attests its peer credentials, the custody store opens, free disk space is above the documented threshold (15 percent, ASSUMED) and run-slot accounting is not wedged, with each result reused for at most 5 s. Otherwise it answers 503 with the same body shape and `status` `unavailable`, refuses new runs and keeps `isolationMode`. The body holds only `contractVersion`, `status`, `isolationMode`, `judgeMode`, `engineVersion` and `commitSha` (from the `VK_COMMIT_SHA` build argument, `unknown` if absent).
    - Acceptance tests: D2-AC-13: the key set equals the allowed set, and replacing the socket with a non-examiner uid gives 503. D10-AC-4: the probe exits 0 only with both processes alive and non-zero with the examiner stopped and with the custodian stopped, and 0 public liveness routes exist. D10-AC-5: failing each of the four checks in turn gives 503 with the key set of the 200 body, `isolationMode` unchanged, a refused `POST /runs`, no failed-check name in the body, and no new check inside 5 s but a new one after 5 s. CP-9.
    - Environment: CI/VM. The local Linux_Docker_Host stands in and each record names its source (DD9-7).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the readiness and liveness tests with `-rA` and the container run of the four failure cases. D2-AC-13, D10-AC-4 and D10-AC-5 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-12, PH3-12
    - _Requirements: 7.26, 7.13_

  - [ ] 5.14 PH5-14 Image reproducibility, scan, SBOM and capability set
    - Objective: In `Dockerfile` and `.dockerignore`: keep the base image pinned by sha256 digest, build with `uv sync --frozen` so that a stale `uv.lock` fails the build, exclude `.kiro`, `docs`, `.github`, `.hypothesis` and `.ruff_cache`, add the build argument `VK_COMMIT_SHA` and the image label `org.opencontainers.image.revision`. The build argument equals `git rev-parse HEAD` locally and `github.sha` in CI, and a check compares the image label, the build argument and the `commitSha` that `GET /api/v1/health` returns (D10.11 TR-12). Validate the other provenance labels (the base image digest and, once PH6-04 exists, the plugin provenance manifest hash). A build step fails when the Python of the image is older than 3.12.4 and records the full version (TR-18, 13.29). The four gates include the extended `gate-isolation` of PH1-12a with its group counts. Run the four container gates on the exact image digest. Scan the image and fail on a HIGH or CRITICAL finding that has a fix. Store an SBOM with the release record. Measure the minimum capability set by running the four gates under `--cap-drop ALL` plus recorded additions (never `SYS_PTRACE` or `SYS_ADMIN`), and record it.
    - Acceptance tests: D2-AC-3: the four gates exit 0 on the image digest. D2-AC-15: a build with a stale `uv.lock` fails. D2-AC-16: 0 unwaived fixable HIGH or CRITICAL findings. D2-AC-24: the gates exit 0 under the recorded capability set, the examiner `CapEff` is 0 and the recorded set equals the deployed set. D10-AC-22 and D10-AC-27 (image leg): the label, the build argument and `commitSha` agree and a mismatch fails, the group counts of `gate-isolation-counts.json` equal the manifest, and an image whose Python is 3.12.3 or earlier fails the build.
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `docker build` with `--build-arg VK_COMMIT_SHA`, the stale-lock build, `gate-isolation`, `gate-startup`, `gate-http` and `gate-case` with `--network none`, the scanner run (tool and version recorded), the SBOM command and the capability-set runs, plus `docker image inspect` read before the first and after the last gate. D2-AC-3, D2-AC-15, D2-AC-16 and D2-AC-24 SUCCEEDED.
    - Rollback: RP-3 (run the previous image; `gate-startup` marker and `GET /api/v1/health` show the previous `commitSha`) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH5-13
    - Findings: TPR-M-9, TPR-L-4
    - _Requirements: 7.12, 2.5, 14.17, 13.29_

  - [ ] 5.15 PH5-15 Examiner per-examination budget, egress probe and PID 1 handling
    - Objective: In `core/src/verdictkit/examiner/worker.py` and `deploy/entrypoint.sh` give each examination its own bounded CPU and wall-clock budget that resets for the next one (AM-4, mechanism chosen at implementation), keeping `RLIMIT_AS`, the per-task deadline, the container limits and fail-closed `RUN_FAILED` on overrun, and use a recycle policy in place of the 300 s lifetime cap (values from the D2-AC-14 measurement). Run a negative egress probe from the examiner uid in a container that has network access. If it is not blocked, record R-2 as accepted with the reason (T8-35). Document `docker run --init` and add a SIGTERM trap in `serve` that stops both children.
    - Acceptance tests: D2-AC-22: many short examinations whose cumulative CPU exceeds 300 s leave the worker alive, an overrun ends in `RUN_FAILED` and the next examination succeeds, and `RLIMIT_AS` still applies. D2-AC-23: the connection to a local canary listener from the examiner uid fails, or R-2 is recorded as accepted with a reason. SIGTERM stops both children within 10 s (ASSUMED).
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the container run of the budget tests (`-rA`, `--network none`), the egress probe run on a network that allows connections to the canary listener, and the SIGTERM test. D2-AC-22 and D2-AC-23 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH5-14
    - _Requirements: 7.11, 2.3, 2.5_

  - [ ] 5.16 PH5-16 Local deployment documentation
    - Objective: Write local deployment documentation as new files under `docs/next-phase/` (no Submission_Artifacts file is edited). It states that the portable image runs unchanged on any Linux_Docker_Host and depends on no single provider's service for isolation, how the previous image is identified (local image ID, or digest where a registry exists) and how a rollback is confirmed through `GET /api/v1/health` `commitSha`, and that no hosted demonstration is available. Record the AWS ECS Fargate evaluation as decision text only (cost estimate, security posture, whether it can give `ENFORCED`), with nothing provisioned. A target that cannot give `ENFORCED` is rejected for judge mode.
    - Acceptance tests: D2-AC-17 local rehearsal leg: redeploying the previous image locally shows the previous `commitSha` on health within 10 minutes (ASSUMED). The document scan (`wording-scan` rule WS-6 of PH1-03a) finds the no-hosted-demonstration statement and 0 public URLs presented as live. The Fargate section is labelled UNVERIFIED and records no charge.
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the two local image runs with health reads, the document scan and the publication scan (counts per class). The local rehearsal leg of D2-AC-17 SUCCEEDED. The rehearsal on a deployed target is CD-07.
    - Rollback: RP-3 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH5-14
    - _Requirements: 7.14, 7.15, 7.16, 7.17, 7.18_

  - [ ] 5.17 PH5-17 Phase 5 checkpoint
    - Objective: Run the Phase 5 targeted regression on both host classes, `npm run typecheck`, `npm test`, `npm run build`, `ruff check .`, the ledger lint, the publication scan and the frozen-ref check. Write the track Execution_Record for Phase 5 (4.4) with the rollback fields (4.5) and the Kiro attribution rows (4.7) as in PH1-18, update the Phase 5 checkboxes in the same change (4.9), and name the verified checkpoint commit.
    - Acceptance tests: D8-AC-30: each host recorded separately with 0 unexplained divergence. D1 AC-16 npm legs exit 0. D8-AC-29: 0 changed lines in existing tests except the approved hunks. D9-AC-16: 4 of 4 ref values and 0 Submission_Artifacts differences. Browser E2E, the real 24 h expiry wait and manual accessibility checks are listed UNVERIFIED unless a record exists.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the regression set on each host (`-rA`), the three npm commands, `uv run --no-sync ruff check .`, the lint, the scan and the frozen-ref commands. The track record lists each Phase 5 criterion as SUCCEEDED, FAILED or UNVERIFIED. The checkpoint commit is verified only when its regression set has a SUCCEEDED record.
    - Rollback: RP-1 `git revert` of the phase's commit range back to the previous verified checkpoint. If the rollback does not complete, the RP row is FAILED, the track is incomplete and RB-18 stays open until the branch is recovered to a verified checkpoint (OD-D10-3, 4.6).
    - Depends on: PH5-01, PH5-02, PH5-03, PH5-04, PH5-05, PH5-06, PH5-07, PH5-08, PH5-09, PH5-10, PH5-11, PH5-12, PH5-13, PH5-14, PH5-15, PH5-16
    - _Requirements: 13.15, 4.4, 4.5, 4.7, 4.9_

- [ ] 6. Phase 6: Legacy replay checkpoint (Plugin SDK and regulatory expansion DEFERRED)
  - Goal: Replay the legacy corpus on the retained code and close the phase at a checkpoint (PH6-12). The Claim_Plugin_SDK, the Conformance_Suite, the scaffolding command, the loader rules, the fail-closed public loader, Texas completion and the California, Florida and New York adapters are DEFERRED by the owner scope freeze: they are not queued, not implemented and not verified. The existing Texas adapter and historical replay stay intact (12.13, 12.23).
  - _Requirements: 4.4, 4.9, 12.13, 12.23, 13.15_

  - 6.1 PH6-01 Claim_Plugin_SDK surface and Conformance_Suite [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Add `core/src/verdictkit/sdk/` (`__init__.py`, `__main__.py`, `validate.py`, `conformance.py`) and `docs/SDK.md`. Document the `ClaimType` protocol, its optional hooks, the entry-point group `verdictkit.claim_types`, `VK_CLAIM_TYPES`, the trust model, the public rule and the exit codes. `run_suite` runs checks CS-01 to CS-10 (blinding, disjoint fields, determinism across `PYTHONHASHSEED` values, no float, `CLAIMANT` forbidden, golden replay `REPRODUCED`), continues after a failure, names the failed check and the offending field and never a claim value, and `python -m verdictkit.sdk check` exits 0, 1, 2 or 3 as D6.7 states. The protocol and existing contracts are not changed. The Examiner process never imports `sdk.conformance` or `sdk.scaffold`. Add `tests/contract/test_sdk_fence.py`.
    - Acceptance tests: D6-AC-1: 10 of 10 checks pass for each of `quote.finance.v1`, `quote.lease.v1`, `reel.mechanical.v1` and `example.receipt.v1`. A `NO_VALID_OUTCOME_VARIANT` result is resolved by a recorded maintainer decision and never by weakening a check. D6-AC-10: each of 5 mutants fails its check, the suite continues and exits 1. D6-AC-11: 0 parameters or returns carry outcomes, the vault, a key or a socket, and the two modules are absent from `sys.modules` after importing `verdictkit.examiner.worker`. D6-AC-12: 0 changed lines in `plugin.py`, `test_blinding.py` and `test_llm_fence.py`. D6-AC-13: 0 violations in `sdk/` and scaffold output and equal banned-name sets. D6-AC-14: the 4 `list_claim_types` entries are unchanged and `docs/SDK.md` holds the group, `VK_CLAIM_TYPES`, protocol, trust model, public rule and exit codes. `test_llm_fence.py` passes with 0 failures (2.12).
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/sdk tests/contract/test_sdk_fence.py tests/contract/test_llm_fence.py` on each host, the `python -m verdictkit.sdk check` runs and `git diff --stat 84df25c` over the three protected files. D6-AC-1 and D6-AC-10 to D6-AC-14 SUCCEEDED.
    - Rollback: RP-1 `git revert` (delete the SDK package and scaffolding command; core modules were not edited). A failed rollback: OD-D10-3.
    - Depends on: PH2-02, PH3-10
    - _Requirements: 11.1, 11.7, 11.8, 11.9, 11.10, 11.11, 11.13, 11.14, 11.15, 2.9, 2.12_

  - 6.2 PH6-02 Scaffolding command [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Add `core/src/verdictkit/sdk/scaffold.py` and `templates.py` and the `new` subcommand (`python -m verdictkit.sdk new` with a `type_id`, `--dest` and an optional `--package`). With a valid identifier and a destination that does not exist or is empty it writes the 5 files of D6.6 and exits 0. A non-empty destination exits 3 and changes nothing. An invalid identifier exits 2 and creates nothing. A forbidden destination or an injected failure exits 4 or 5 and leaves the repository tree unchanged. It writes only inside the destination through the shared secure-filesystem module of PH1-04a (the module that PH2-02 applies to MCP), with no containment code of its own and edits nothing under `core/src/verdictkit/`. Generated `examine` and `findings` hold no float, no LLM client import and no wall-clock read, and output is deterministic (LF, no timestamp, path or random value). Add property P-e.
    - Acceptance tests: D6-AC-2: a fresh scaffold of `example.line_total.v1` passes 10 of 10 checks with no edit, exits 0, and the 5 files exist. D6-AC-4: uppercase, dash, keyword, stdlib name, device name, 41 characters, control characters, path separators and reserved namespace each exit 2 with 0 files and a message of at most 80 echoed characters. D6-AC-5: 0 differing bytes across the four trees (two runs on each host). D6-AC-6: exit 3 and the existing file byte-identical. D6-AC-7: exit 4 or 5 with the repository tree unchanged. P-e: 200 of 200 examples (CP-37).
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/sdk` on each host (HYPOTHESIS_PROFILE=ci) and the scaffold end-to-end run. D6-AC-2 and D6-AC-4 to D6-AC-7 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH6-01
    - _Requirements: 11.2, 11.3, 11.4, 11.5, 11.6, 11.12, 13.5_

  - 6.3 PH6-03 Loader rules [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Add `core/src/verdictkit/sdk/loader.py` (`discover(policy)` returns the loaded types and issues `(code, entry_point, distribution)`) and make `cli.py` `_load_registry` delegate to it. A duplicate `type_id` rejects every colliding registration in every mode, so the result never depends on load order (AM-D6-2). Local mode reports the collision and leaves the types unregistered. Public mode refuses start with a `VK_STARTUP_ERROR` code (wired in PH6-04). A reserved `type_id` namespace (`quote`, `reel`, `verdictkit`, `vk`) from another distribution is rejected. A failing entry point between two good ones does not stop the good ones in local mode. Messages carry a code, the entry-point name and the distribution name and never exception text, a path or a claim value. Add property P-m.
    - Acceptance tests: D6-AC-3: with fake distributions, both duplicates and the reserved id are rejected, both good plugins load and each issue is one line. P-m: for all orderings of the same entry points the loader registers the same types and rejects the same duplicates (200 of 200 examples, CP-35). PD-1, PD-9 and PD-11 are asserted again in PH6-04.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/sdk` on each host (HYPOTHESIS_PROFILE=ci) and `uv run --no-sync ruff check .`. D6-AC-3 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH6-01
    - _Requirements: 11.17, 13.20_

  - 6.4 PH6-04 Public plugin loading fails closed [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: In the `public` Security_Profile import a plugin only when an allowlist entry names it, and bind that entry to its Plugin_Provenance: distribution name, exact version, entry-point name, entry-point value and `provenance_sha256` (AM-D6-3). The image build writes a root-owned, read-only provenance manifest (installed files with SHA-256, `RECORD` checked against disk, `__pycache__` excluded, kind `workspace-tree`) in the `Dockerfile`, and its hash goes into an image label. The loader verifies the files before any import and checks afterwards that the module file belongs to the verified set and that no other module claims the plugin's top-level name, else it refuses with `PLUGIN_PROVENANCE_MISMATCH`. An unlisted entry point is never imported and is only counted (`PLUGIN_NOT_ALLOWLISTED`). `VK_CLAIM_TYPES` in the public profile, a failing allowlisted plugin, an unreadable manifest or a duplicate `type_id` refuse start with `VK_STARTUP_ERROR`, a non-zero exit and no listener. Add PD-1 to PD-12 and the start-up cases FC-10 and FC-12.
    - Acceptance tests: D8-AC-12: PD-1 to PD-12 each end in the result 11.16 to 11.18 require (CP-36). D8-AC-17 for FC-10 and FC-12: non-zero exit, a `VK_STARTUP_ERROR` line with a code, no `VK_STARTUP_OK`, no open listener, no written file. D6-AC-8: a fake distribution whose module writes a canary file on import leaves 0 canary files and `PLUGIN_NOT_ALLOWLISTED` in public mode, and 1 canary file in local mode. D6-AC-9: `VK_JUDGE_MODE=1` with `VK_CLAIM_TYPES` set, and one allowlisted type made to fail, each give a non-zero exit and a `VK_STARTUP_ERROR` line with no key value in the output.
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the image build, the container run of the PD and FC tests (`-rA`, `--network none`) and the manifest read. D8-AC-12, D8-AC-17 (FC-10, FC-12), D6-AC-8 and D6-AC-9 SUCCEEDED.
    - Rollback: RP-9 (revert the allowlist constant and the provenance manifest build step; the public profile then loads 0 third-party plugins) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-03, PH1-15
    - _Requirements: 11.16, 11.18, 7.19, 13.20, 13.24_

  - 6.5 PH6-05 Texas completion [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Retrieve the text of 7 TAC section 84.205 from the Texas Secretary of State by a read-only HTTPS GET to a host on the reviewed official-domain list, with no authentication, payment, new account or cloud provisioning, or record it `UNVERIFIED` with the reason (the registry of PH6-06 must exist and OA-07a must have reviewed the host entry, otherwise retrieve nothing). Record each retrieval (tool and version, HTTP status, byte count, SHA-256). Keep the $225 documentary-fee treatment and every Texas finding unchanged. The retrieved text is `UNREVIEWED` material: it is stored and hashed, and it changes no rule value, finding or UI text until OA-07b records its independent review (TPR-H-6). A change that the reviewed text supports is a separate step after that record. A text that contradicts the amount makes the sidecar entry `AMBIGUOUS`, stops Phase 6 and goes to the maintainer. Write the sidecar `rules/v2/US-TX.legacy-evidence.json` for the four sources of `TX.json` (URI, `sha256_of_source`, media type, excerpt, class, stated effective date or `UNVERIFIED`). The verdict path never reads the sidecar.
    - Acceptance tests: D7-AC-15: the 4 URIs and hashes match `TX.json` or are flagged, 84.205 is retrieved or `UNVERIFIED`, and no Texas finding changes. D7-AC-17: every `VERIFIED` value matches its excerpt, and a scan of documents and UI text (`wording-scan` rule WS-5 of PH1-03a) finds 0 support statements without a `SUCCEEDED` record.
    - Environment: Windows. Official HTTPS GET only.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, commit SHA, UTC start, recorded_utc within 5 s) for each retrieval (tool, HTTP status, byte count, SHA-256) and `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration/test_quote_b7_texas.py`. D7-AC-15 and D7-AC-17 SUCCEEDED. Review of the retrieved text is OA-07b.
    - Rollback: RP-4 (move the active pointer back; the sidecar is not read by the verdict path) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH3-10, PH6-06, OA-07a
    - Findings: TPR-H-6
    - _Requirements: 12.11, 12.17, 12.15, 12.22_

  - 6.6 PH6-06 Snapshot loader v2 and storage [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Add `apps/quote-autopsy/src/quote_autopsy/rules_v2.py` and `sources_v2.py`, `scripts/rules_snapshot.py`, `rules/v2/` (including `official_hosts.json`) and the `.gitattributes` entry that keeps stored bytes unchanged. This task establishes the official-host registry before any retrieval: every entry names its `basis` and starts `UNREVIEWED`, OA-07a records its review, and no retrieval (PH6-05, PH6-08, PH6-09, PH6-10) happens from a host whose entry has no such record (TPR-H-6). Accept a source only from an exact official host of the registry (else `HOST_NOT_OFFICIAL`), record URI, retrieval date, SHA-256, media type and an excerpt of 1 to 2,000 characters, check excerpt containment, reject a script shell or error page and identical content under two URIs, recompute every hash on load, record effective dates, and store the bytes and headers where the terms permit (else only the hash, the excerpt and `rights: NOT_ESTABLISHED` with the dependent rules `UNVERIFIED`). Verification runs offline. The update script is deterministic. No Texas file is edited. Fixtures use the fictional jurisdiction `US-ZZ` and are labelled constructed.
    - Acceptance tests: D7-AC-1: 0 changed lines in `TX.json`, `rules/MANIFEST.json`, `rules.py` and `sources.py`, and an equal Verdict_Hash for a Texas claim. D7-AC-3, D7-AC-4, D7-AC-5 (7 of 7 host cases give `HOST_NOT_OFFICIAL`), D7-AC-6, D7-AC-7 (a flipped byte in any stored file gives `evidence_integrity` or no use, 0 `SUPPORTED`, 0 `REFUTED`), D7-AC-8 (0 differing bytes, manifest unchanged), D7-AC-9, D7-AC-13 (equal findings and 0 outbound connections) and D7-AC-14 (`STALE` listed, verdict bytes unchanged).
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration`, the update script run twice with a patched clock and the offline connection-guard run. D7-AC-1, D7-AC-3 to D7-AC-9, D7-AC-13 and D7-AC-14 SUCCEEDED.
    - Rollback: RP-4 (move the active manifest pointer back; Bundles embed their evidence so replay is unaffected) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH3-02, PH3-10
    - Findings: TPR-H-6
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.13, 12.14, 12.15, 12.16, 12.19, 12.24_

  - 6.7 PH6-07 Rule semantics [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: In `apps/quote-autopsy/src/quote_autopsy/claim_type.py` and `rules_v2.py` (no Texas function is edited) give an unsupported jurisdiction `INDETERMINATE` with reason `unsupported_jurisdiction` and 0 evidence items, give a rule that needs a filing the system cannot obtain `INDETERMINATE` with a `missing_filing` reason and never `REFUTED`, sweep an unstated locality over the full official published range from minimum to maximum inclusive as a `DEFAULT_POLICY` assumption with the swept bounds listed, and state no speculative legal conclusion. The new unsupported-jurisdiction wording applies only under a newer Examination_Semantics id, and the `legacy-1` text stays (AM-D7-3). Add the `as_of` key and four-outcome tests (`SUPPORTED`, `REFUTED`, `CONDITIONAL`, `INDETERMINATE`) for each added jurisdiction, with expected values computed with `Decimal` from the snapshot. Where a real jurisdiction cannot produce an outcome use a `US-ZZ` fixture and say why (OD-D7-7).
    - Acceptance tests: D7-AC-2: `ZZ`, an absent code, a `SUSPENDED` and a `WITHDRAWN` jurisdiction and claims with no `ACTIVE` snapshot give `INDETERMINATE` with `unsupported_jurisdiction` and 0 evidence items, and `C`, `CAL` and `C1` give `SchemaError` at intake. D7-AC-10: 4 of 4 outcomes with 0 `float`. D7-AC-11: sweep over the full range with bounds listed, an exact rate when the locality is in the table, and `unknown_locality` when it is absent. D7-AC-12: a missing filing never gives `REFUTED`.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration tests/api` (HYPOTHESIS_PROFILE=ci) and the `float` scan. D7-AC-2, D7-AC-10, D7-AC-11 and D7-AC-12 SUCCEEDED.
    - Rollback: RP-4 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-06
    - _Requirements: 12.8, 12.9, 12.10, 12.12, 12.20_

  - 6.8 PH6-08 California retrieval and build (snapshots `PENDING_REVIEW`) [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Only after Texas completion (PH6-05) and with the host entries of the registry reviewed by OA-07a, retrieve the California official sources by read-only HTTPS GET, build the snapshots and run the jurisdiction gate on the build (criteria 12.1 to 12.16 and the four outcome tests, with `US-ZZ` fixtures and the retrieved excerpts). Every snapshot built here is `PENDING_REVIEW`. None is `ACTIVE`, and the material changes no finding, UI text or test expectation until OA-07c records an independent review (TPR-H-5, TPR-H-6). Promotion is PH6-08a.
    - Acceptance tests: D7-AC-1: equal Verdict_Hash for a Texas claim and `TX.json` unchanged. Every California snapshot is `PENDING_REVIEW` and 0 are `ACTIVE`. The jurisdiction gate of 12.1 to 12.16 runs on the build and its result is recorded. D8-AC-29: 0 changed lines in existing tests.
    - Environment: Windows. Official HTTPS GET only.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for each retrieval (tool, HTTP status, byte count, SHA-256), `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration tests/api` and the corpus replays. D7-AC-1 SUCCEEDED, and each snapshot is recorded `PENDING_REVIEW`.
    - Rollback: RP-4 (the jurisdiction returns to `unsupported_jurisdiction`) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-07, PH6-05, OA-07a
    - Findings: TPR-H-5, TPR-H-6
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.13, 12.18, 12.22_

  - 6.8a PH6-08a California promotion (after the independent review) [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Only after OA-07c has recorded an independent review of the California snapshots that PH6-08 built, promote each reviewed snapshot to `ACTIVE`. The promotion step checks the review record's hash and that its reviewer is not the agent, and it refuses a snapshot without such a record (TPR-H-5). Where the record is absent, `NOT_PROVIDED` or negative, the jurisdiction is recorded `BLOCKED` and its rules `UNVERIFIED`. When California becomes supported, change the literal `CA` to `ZZ` only in `test_non_tx_external_findings_unsupported_jurisdiction` (`tests/integration/test_quote_b7_texas.py`), `test_external_only_claim_is_indeterminate` (`tests/api/test_http_run_lifecycle.py`) and any other test that a search shows uses `CA` only as an unsupported-jurisdiction example. Name, purpose and every assertion stay, and the ledger records a fixture-data change and not a loosening. Add a guard test that fails if `ZZ` ever appears among the supported jurisdictions. The Bundles of the legacy corpus keep replaying unchanged.
    - Acceptance tests: D7-AC-1: equal Verdict_Hash for a Texas claim and the Texas test file differs from the baseline only by the AM-D7-1 hunk. D7-AC-16: marking a later jurisdiction `ACTIVE` while an earlier one is neither `ACTIVE` nor `BLOCKED` is refused. Promotion of a snapshot with no review record, or with a record whose reviewer is the agent, is refused (negative control). D8-AC-29: 0 changed lines in existing tests except the approved hunks. The legacy corpus replays with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV` (P-g).
    - Environment: Windows. Official HTTPS GET only.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the promotion check, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration tests/api`, the corpus replays and `git diff 84df25c` over the two edited test files. D7-AC-1, D7-AC-16 and D8-AC-29 SUCCEEDED, or the jurisdiction is recorded `BLOCKED` with the reason.
    - Rollback: RP-4 (the jurisdiction returns to `unsupported_jurisdiction`) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-08, OA-07c
    - Findings: TPR-H-5
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.18, 12.21, 12.13, 12.23_

  - 6.9 PH6-09 Florida retrieval and build (snapshots `PENDING_REVIEW`) [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Only after PH6-08a has recorded California `ACTIVE` or `BLOCKED`, and with the Florida host entries reviewed by OA-07a, repeat the retrieval and build of PH6-08 for Florida: official-host retrieval, snapshots recorded `PENDING_REVIEW`, the jurisdiction gate on the build, four outcome tests with `US-ZZ` fixtures, and replay of the legacy corpus. Promotion is PH6-09a, after OA-07d. The retrieved material is unreviewed and is used for nothing until that record exists.
    - Acceptance tests: D7-AC-16: the order gate refuses Florida while California is neither `ACTIVE` nor `BLOCKED`. The jurisdiction gate (12.1 to 12.16) and 4 of 4 outcome tests pass on the build, every snapshot is `PENDING_REVIEW` and 0 are `ACTIVE`, or the result is `BLOCKED`. The legacy corpus replays with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`.
    - Environment: Windows. Official HTTPS GET only.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for each retrieval, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration tests/api` and the corpus replays. D7-AC-16 SUCCEEDED, or `BLOCKED` with the reason. Each snapshot is recorded `PENDING_REVIEW`.
    - Rollback: RP-4 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-08a, OA-07a
    - Findings: TPR-H-5, TPR-H-6
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.18, 12.23_

  - 6.9a PH6-09a Florida promotion (after the independent review) [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Only after OA-07d has recorded an independent review of the Florida snapshots that PH6-09 built, promote each reviewed snapshot to `ACTIVE`, with the checks and the refusal rule of PH6-08a. Without such a record the jurisdiction is recorded `BLOCKED` and its rules `UNVERIFIED`.
    - Acceptance tests: D7-AC-16: promotion of a snapshot with no review record, or with a record whose reviewer is the agent, is refused (negative control), and a later jurisdiction cannot become `ACTIVE` while Florida is neither `ACTIVE` nor `BLOCKED`. The legacy corpus replays with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the promotion check, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration tests/api` and the corpus replays. D7-AC-16 SUCCEEDED, or `BLOCKED` with the reason.
    - Rollback: RP-4 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-09, OA-07d
    - Findings: TPR-H-5
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.18, 12.23_

  - 6.10 PH6-10 New York retrieval and build (snapshots `PENDING_REVIEW`) [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Only after PH6-09a has recorded Florida `ACTIVE` or `BLOCKED`, and with the New York host entries reviewed by OA-07a, repeat the retrieval and build of PH6-08 for New York. Every snapshot is `PENDING_REVIEW`, and the retrieved material is used for nothing until OA-07e records its review. Promotion is PH6-10a.
    - Acceptance tests: D7-AC-16: the order gate refuses New York while Florida is neither `ACTIVE` nor `BLOCKED`. The jurisdiction gate (12.1 to 12.16) and 4 of 4 outcome tests pass on the build, every snapshot is `PENDING_REVIEW` and 0 are `ACTIVE`, or the result is `BLOCKED`. The legacy corpus replays with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`.
    - Environment: Windows. Official HTTPS GET only.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for each retrieval, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration tests/api` and the corpus replays. D7-AC-16 SUCCEEDED, or `BLOCKED` with the reason. Each snapshot is recorded `PENDING_REVIEW`.
    - Rollback: RP-4 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-09a, OA-07a
    - Findings: TPR-H-5, TPR-H-6
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.18, 12.23_

  - 6.10a PH6-10a New York promotion (after the independent review) [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Only after OA-07e has recorded an independent review of the New York snapshots that PH6-10 built, promote each reviewed snapshot to `ACTIVE`, with the checks and the refusal rule of PH6-08a. Without such a record the jurisdiction is recorded `BLOCKED` and its rules `UNVERIFIED`.
    - Acceptance tests: D7-AC-16: promotion of a snapshot with no review record, or with a record whose reviewer is the agent, is refused (negative control). The legacy corpus replays with an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the promotion check, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/integration tests/api` and the corpus replays. D7-AC-16 SUCCEEDED, or `BLOCKED` with the reason.
    - Rollback: RP-4 and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH6-10, OA-07e
    - Findings: TPR-H-5
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.18, 12.23_

  - 6.11 PH6-11 Regulatory display and documentation [DEFERRED]
    - Status: DEFERRED by the owner scope freeze (OA-00, design D10.12). Not queued, not implemented, not verified. The text below is kept as the specification of a later release.
    - Objective: Show the retrieval date next to each finding that relies on a snapshot in the UI_Kit, state in the UI and in `docs/REGULATORY_SNAPSHOTS.md` that each snapshot is a point-in-time copy, and classify the contract-visible fields (the `as_of` key, the snapshot retrieval date on the evidence DTO and the Examination_Semantics id) as COMPATIBLE or BREAKING inside the 2.0.0 event in `docs/API_CONTRACT.md`, `api/openapi.yaml` and `api/examples/` (D5.12 form). The contract version stays 2.0.0.
    - Acceptance tests: D7-AC-18: a UI test asserts the label text and the retrieval date next to a finding, and every added field has a classification. D5-AC-18: 0 unlabelled contract changes.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `npm test`, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_api_schema.py` and the publication scan over the new document. D7-AC-18 and D5-AC-18 SUCCEEDED.
    - Rollback: RP-2 for the contract part and RP-1 for the rest. A failed rollback: OD-D10-3.
    - Depends on: PH6-08a, PH5-05
    - _Requirements: 12.14, 12.16, 10.34_

  - [ ] 6.12 PH6-12 Phase 6 checkpoint (legacy replay checkpoint)
    - Objective: Replay the legacy corpus on the retained code (P-g). Phase 6 adds no code and no jurisdiction, so the replay checks that the changes of Phases 1 to 5 leave every historical Bundle at an equal Verdict_Hash. Record the Threat_Model inputs for rows T8-16, T8-17, T8-22 and T8-23 of D8.4 as `UNTESTED` with the reason `deferred scope` for PH7-01 (their controls and tests belong to the deferred PH6-01, PH6-03, PH6-04 and PH6-06). Run the targeted regression on both host classes, `ruff check .`, the ledger lint, the publication scan and the frozen-ref check. Write the track Execution_Record for Phase 6 (4.4) with the rollback fields (4.5) and the Kiro attribution rows (4.7) as in PH1-18. List every criterion of Requirements 11 and 12 except 12.13 and 12.23 as `UNVERIFIED` with the reason `deferred scope`, never as `SUCCEEDED`. Update the Phase 6 checkbox in the same change (4.9) and name the verified checkpoint commit.
    - Acceptance tests: D8-AC-15 (DR-5): every legacy corpus Bundle has an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, with 0 `DIVERGED` and 0 `UNVERIFIABLE`. P-g: 200 of 200 examples (CP-40). D7-AC-1: equal Texas Verdict_Hash. D8-AC-30: each host recorded separately with 0 unexplained divergence. D8-AC-29: 0 changed lines in existing tests except the approved hunks. D8-AC-1 input: rows T8-16, T8-17, T8-22 and T8-23 carry `UNTESTED` and a non-empty reason. 0 criteria of Requirements 11 and 12 other than 12.13 and 12.23 are listed `SUCCEEDED`.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the corpus replays on each host, the regression set on each host (`-rA`), `uv run --no-sync ruff check .`, the lint and the scan. The track record lists each Phase 6 criterion as SUCCEEDED, FAILED or UNVERIFIED. The checkpoint commit is verified only when its regression set has a SUCCEEDED record.
    - Rollback: RP-1 `git revert` of the phase's commit range back to the previous verified checkpoint (the phase adds no code, so the range holds only its evidence commit). RP-4 and RP-9 do not apply, because this release adds no rules manifest and no plugin allowlist. If the rollback does not complete, the RP row is FAILED, the track is incomplete and RB-18 stays open until the branch is recovered to a verified checkpoint (OD-D10-3, 4.6).
    - Depends on: PH3-14, PH5-17
    - _Requirements: 13.15, 12.13, 12.23, 4.4, 4.5, 4.7, 4.9_

- [ ] 7. Phase 7: Complete integration, property tests, regression tests, security gates and release verification
  - Goal: Complete the Threat_Model and the property, adversarial, canary and replay suites, build the release tooling, verify one Release_Candidate S on both host classes with counts taken only from its runner output, and write the final release report and blocker list. No tag, merge, publication or provisioning happens in this plan.
  - _Requirements: 1.2, 1.3, 1.14, 2.2, 2.3, 2.8, 2.11, 2.13, 2.14, 3.2, 3.8, 3.11, 3.12, 3.13, 3.14, 4.1, 4.2, 4.3, 4.6, 4.8, 4.9, 7.13, 7.14, 7.20, 12.21, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.14, 13.22, 13.23, 13.24, 13.28, 14.1, 14.2, 14.3, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10, 14.11, 14.12, 14.13, 14.14, 14.15, 14.16, 14.17, 14.18, 14.19, 14.20, 14.21, 14.22, 14.23, 14.24, 14.25, 14.26, 14.27, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10, 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 7.1 PH7-01 Threat_Model
    - Objective: Write `docs/next-phase/THREAT_MODEL.md` from the rows T8-1 to T8-35 of D8.4, with the inputs recorded at the PH6-12 checkpoint. It has one row per threat, a non-empty value in every column, `UNTESTED` with a non-empty reason where no automated test exists (T8-34, the residual risk of T8-35 where the egress probe cannot block, and T8-16, T8-17, T8-22 and T8-23 with the reason `deferred scope`), and it covers the 17 threats that 13.2 names. Map every new control (the key-file mechanism, replay isolation, upload admission, the Approved_Root helper, the profile resolver, the peer check, plugin provenance and the sanitizer) to at least one row, and remove a control that has none. No new runtime dependency.
    - Acceptance tests: D8-AC-1: one row per threat, 0 empty cells, a reason on every `UNTESTED` row, and each of the 17 named threats present. D8-AC-28: `uv.lock` shows 0 added runtime packages and every D8.3 control maps to a D8.4 row.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the document check test with `-rA` on each host, `uv lock --check` and `git diff --stat 84df25c -- uv.lock`. D8-AC-1 and D8-AC-28 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH6-12
    - Findings: M-7
    - _Requirements: 13.1, 13.2, 13.3, 13.28_

  - [ ] 7.2 PH7-02 Property suite completeness
    - Objective: Add a meta-test under `tests/` that finds each of the 13 properties P-a to P-d, P-f to P-l, P-n and P-o as exactly one Hypothesis test, in the task that owns the property in the Notes (a second test of the same property fails the meta-test, TPR-M-3), whose docstring cites the property statement and at least one requirement id (13.4) and carries the comment "Feature: verdictkit-next-phase, Property P-x". Check that the `ci` profile is derandomized with `max_examples` of 200 (13.7) and that each property has a mutation guard for its underlying check. P-a is stated over the verified region (OD-D10-4). The new tests are collected by the existing CI workflow (wired in PH7-11).
    - Acceptance tests: D8-AC-2: P-a to P-d hold for 200 of 200 examples and the mutation guard shows a failure once a check is disabled. The meta-test finds 13 of 13 properties with docstring, tag and guard, and 0 properties that run under another profile. P-e and P-m belong to the deferred PH6-02 and PH6-03, are listed `DEFERRED` and are not counted.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the property run with `-rA` and `HYPOTHESIS_PROFILE=ci` on each host and the meta-test. D8-AC-2 SUCCEEDED on both hosts.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-01
    - _Requirements: 13.4, 13.5, 13.7_

  - [ ] 7.3 PH7-03 Malformed-input kinds, adversarial surfaces and profile matrix
    - Objective: Add a coverage test that maps each of the seven malformed-input kinds of 13.6 (malformed zip entry, duplicate zip name, absolute member name, parent-directory member name, truncated signature, wrong-algorithm signature, malformed Trust_Store file) and each of the five retained adversarial surfaces of 13.14 (API, MCP_Server, Bundle parsing, Trust_Store, signature envelopes; plugin scaffolding and regulatory snapshots are deferred) to at least one negative test that asserts a rejection, `INDETERMINATE` or `UNVERIFIABLE`. Fail when a kind or surface has no test. Mark every test that needs a container `isolation` (13.8). Add the profile propagation matrix (D2-AC-1 cases extended by AM-D6-4, plus FC-3 and FC-4). Add the grid-cap negative control of criterion 2.10 (TPR-M-2): a grid one point above the configured cap is rejected whole with an error that names the cap and the observed size, evaluates 0 grid points and does not subsample, and a mutant that subsamples the grid fails the test.
    - Acceptance tests: D8-AC-3: each kind is rejected or gives `UNVERIFIABLE`, with 0 `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID` and existing stored data unchanged. D8-AC-19: every profile combination resolves per AM-D6-4 or refuses to start. Criterion 2.10: the grid-cap negative control passes with 0 evaluated grid points and the subsampling mutant fails.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the coverage and negative-test run with `-rA` on each host (HYPOTHESIS_PROFILE=ci). D8-AC-3 and D8-AC-19 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-02
    - Findings: TPR-M-2
    - _Requirements: 13.6, 13.14, 13.8, 2.10_

  - [ ] 7.4 PH7-04 Privacy and secret canary tests PC-1 to PC-6
    - Objective: Add canary tests under `tests/security/` for the vault key, a claimed figure, a user-profile path, an access token, a hook environment variable and a canary signing key created in memory (PC-7, TPR-M-4). Inject each through every applicable entry point (environment variable, argument, claim field, evidence body, file name, MCP argument) and search every sink the Threat_Model prohibits (standard output, standard error, log files, error bodies, diagnostics, Bundles, the evidence index, process listings, pytest failure output) in raw, base64, hexadecimal, URL-encoded and JSON-escaped form. No test prints its canary in its own failure message (PC-6). Add property P-n. P-k belongs to PH1-03, which holds its only Hypothesis test: this task adds example checks that run each canary through the sanitizer and the scan of PH1-03 and expect 0 residual matches, as a supplement and not as a second property test (TPR-M-3). Each canary maps to a row of the credential inventory CSI-1 to CSI-7. The log sink repeats the sentinel lifecycle of D2-AC-12 across every entry point.
    - Acceptance tests: D8-AC-16: 0 matches for PC-1 to PC-5 and PC-7 in every entry point, sink and form, and PC-6 holds for every test in the suite (a meta-test fails a test whose failure text holds its canary). P-n: 200 of 200 examples (CP-43). The P-k supplement (CP-44) is the example check over the PH1-03 sanitizer, and the property itself is verified in PH1-03. D2-AC-12 (log sink, all entry points): 0 sentinels.
    - Environment: Linux_Docker_Host (isolation).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the container run of the canary tests (`-rA`, `--network none`, `HYPOTHESIS_PROFILE=ci`). D8-AC-16 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-02, PH1-12
    - Findings: TPR-M-1, TPR-M-3, TPR-M-4
    - _Requirements: 13.23, 7.20, 2.3, 10.25_

  - [ ] 7.5 PH7-05 Final security matrix (after the last security-relevant change)
    - Objective: Run the whole extended `gate-isolation` (D10.11 TR-3 and TR-6, TPR-H-2) on a tree that holds the last change of `deploy/entrypoint.sh`, `Dockerfile`, `examiner/worker.py` and the signing path, and that is after PH5-14, PH5-15, PH5-17 and PH7-10. The matrix is KT-1 to KT-8 for the vault key and, as the variant KT-S of each case, for a canary signing key, then FC-1 to FC-9 and FC-11 (ten start-up cases, because FC-10 and FC-12 belong to the deferred PH6-04), IS-1 to IS-8, CA-1 to CA-7, RI-1 to RI-8 and property P-l. Add no new code unless a defect is found. A defect is recorded with its failing input, fixed, and the test is kept (13.9). The results of PH1-12 to PH1-15 and PH3-04 are development results, and they do not establish the security of the final candidate. PH7-17 runs the gate again on S.
    - Acceptance tests: D8-AC-17: 10 of 10 start-up cases (FC-1 to FC-9 and FC-11) give a non-zero exit, a `VK_STARTUP_ERROR` line with a code, no `VK_STARTUP_OK`, no listener and no written file. D8-AC-18: 15 of 15. D8-AC-19 and P-l: 200 of 200 examples (CP-14 to CP-17). D10-AC-15: KT-1 to KT-8 for the vault key and for the canary signing key give 0 matches, the counts of `gate-isolation-counts.json` equal the manifest (collected equals executed, 0 skipped), and the record names the commit of the tree that it ran on.
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the extended `gate-isolation` run (`-rA`, `--network none`), the P-l run (HYPOTHESIS_PROFILE=ci) and `gate-isolation-counts.json`. D8-AC-8 (both keys), D8-AC-17, D8-AC-18, D8-AC-19 and D10-AC-15 SUCCEEDED.
    - Rollback: RP-1 `git revert` of any fix commit. A failed rollback: OD-D10-3.
    - Depends on: PH1-15, PH3-04, PH5-14, PH5-15, PH5-17, PH7-10
    - Findings: TPR-H-2
    - _Requirements: 13.24, 2.13, 2.14, 13.16, 7.20, 10.25_

  - [ ] 7.6 PH7-06 Deterministic replay DR-1 to DR-6 on both hosts
    - Objective: Add the DR-1 to DR-6 tests of D8.10. Two replays of the same Bundle, signed and unsigned, give byte-identical reports (P-f). The committed corpus gives equal Verdict_Hash values on Windows and Linux. The clock is patched to two dates and `PYTHONHASHSEED` is 0, 1 and random, with unchanged results. A signed and an unsigned Bundle written in the test environment each replay `REPRODUCED`. Every legacy corpus Bundle replays to an equal Verdict_Hash with `REPRODUCED` or `REPRODUCED_ACROSS_ENV`. A replay makes no network connection (socket guard). `DIVERGED` is reported only when integrity is `VERIFIED` and the hashes differ.
    - Acceptance tests: D8-AC-15: 6 of 6 cases on both hosts, with 0 `DIVERGED` and 0 `UNVERIFIABLE` for the corpus. D5-AC-15: 0 differing bytes between the Windows and Linux outputs (D5.9 DR-2). P-f: 200 of 200 examples (CP-32).
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the replay tests with `-rA` on each host (HYPOTHESIS_PROFILE=ci), with each Windows and Linux corpus replay recorded separately. D8-AC-15 and D5-AC-15 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH6-12
    - _Requirements: 13.22, 2.2, 2.8_

  - [ ] 7.7 PH7-07 Existing tests unmodified, lint and steering
    - Objective: Check that `git diff 84df25c` over the test tree shows only the approved hunks: the BE-1 Windows branch and guard, the BE-2 port hunk that 13.26 and D5-AC-19 require, and the contract-version literal changes from `1.1.0` to `2.0.0` that 10.34 and D5-AC-1 require. The `CA` to `ZZ` hunks (AM-D7-1) are not applied, because California stays unsupported (deferred) and criterion 12.21 is not triggered. Check that `ruff check .` has 0 violations for all new code, that `.kiro/steering` changed only by added files, and that no existing check was weakened, skipped or deleted (13.9). `tests/contract/test_llm_fence.py` passes.
    - Acceptance tests: D8-AC-29: 0 changed lines in existing tests except the approved hunks, and 0 `ruff` violations on new code. D10-AC-9: `git diff --name-status 84df25c` over `.kiro/steering` shows only added files, 0 modified and 0 deleted, and each added file is a new rule.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `git diff 84df25c` over the test tree, `git diff --name-status 84df25c` over `.kiro/steering`, `uv run --no-sync ruff check .` and `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/contract/test_llm_fence.py` on each host. D8-AC-29 and D10-AC-9 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-02
    - _Requirements: 13.9, 13.10, 2.9, 2.11, 2.12, 4.8_

  - [ ] 7.8 PH7-08 Release tooling
    - Objective: Extend `scripts/release_verify.py` (stdlib only, DD9-10) with tests under `tests/release/`: the exact-commit and clean-tree check (`git rev-parse HEAD` equals S, `git status --porcelain` empty before and after each run, every record carries the same 40-character S); per-step Execution_Record writing by the recorder `run` of PH1-02, with counts copied from the runner output; the baseline comparison (each step whose passing count is lower than its baseline count is listed with both counts); `check-run` (the run record's `headSha`, `headBranch`, `event` and `status` against S, the Phase_Branch, `workflow_dispatch` and `completed`); `frozen`; and `report-lint`. `report-lint` checks the exact command text, the Execution_Index id, counts equal to the runner line, `recorded_utc` within 5 s (OD-D10-2), that each Evidence_Commit names the full tested SHA S (OD-D9-1) and is never described as S, with `check-evidence-commit --base S --tip E` (D10.11 TR-2) as the only route to accept a later commit and with both SHAs named in the report, the open blockers RB-18 (OD-D10-3), RB-19 and RB-20, the checkbox rule (4.9), and the separation of the two readiness results. Add `check-evidence-commit` (only Evidence_Output_Set paths, only the two checkbox lines of `tasks.md`, 0 deleted ledger lines, no record that names E), `check-checkpoints` (the six checkpoint records of PH1-18, PH2-10, PH3-14, PH4-10, PH5-17 and PH6-12 are `SUCCEEDED`, or `UNVERIFIED` with an accepted reason, else exit non-zero and list RB-19) and `collect-check` (D10.11 TR-12). `report-lint` runs its S-time checks (VM-15a) without a report, and its report checks (VM-15b) only once the report exists (TPR-M-10).
    - Acceptance tests: D9-AC-1: HEAD equals S and the status is empty, 2 of 2 checks per run on each host class, every record carries the same S, and a clone with one untracked file fails. D9-AC-3: 0 counts differ from the runner line, and a count changed by 1 fails. D9-AC-9 controls: records with another SHA, another branch, event `push` and status `in_progress` each fail `check-run` (4 of 4). D9-AC-14 control: an uncited capability statement is reported with its file and line. A combined "ready" line and a `VERIFIED` level with an open blocker are rejected. Rows of D9-AC-2 are checked structurally. D10-AC-12: `check-evidence-commit` fails on a change to each Test_Input class. D10-AC-16: `check-checkpoints` fails when any one of the six records is missing, and starts nothing. D10-AC-22: `collect-check` fails on an emptied directory, a missing manifest node id and pytest exit code 5.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release` on each host and `uv run --no-sync ruff check .`. D9-AC-1, D9-AC-3 and the tooling parts of D9-AC-2, D9-AC-9, D9-AC-14 and D10-AC-8 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3 (the RP row is FAILED and RB-18 stays open until recovery to a verified checkpoint).
    - Depends on: PH1-02, PH1-02a, PH1-03a, PH7-01
    - Findings: TPR-C-2, TPR-H-3, TPR-M-9, TPR-M-10
    - _Requirements: 14.1, 14.8, 14.9, 14.16, 14.21, 3.2, 4.6, 4.9, 14.10, 14.26, 14.11, 13.7, 13.8, 14.17_

  - [ ] 7.9 PH7-09 No-loss inventory (tooling and Windows preparation)
    - Objective: Add the `inventory` and `diff-inventory` subcommands to `scripts/release_verify.py` and do the Windows preparation (TPR-H-9). At `84df25c` in a disposable detached worktree on Windows run `uv run --no-sync pytest --collect-only -q`, keep the sorted lines that start with `tests/`, and write `docs/next-phase/baseline/TEST_INVENTORY.windows.txt`. Keep the raw output as a Private_Original and record the SHA-256 of the file (3.11). The Linux inventory `TEST_INVENTORY.linux.txt` and the Linux node outcomes come from a Linux full checkout (the image has no `ui/`), through the autonomous route of PH7-09a or through OA-02, and they are the deferred row DLV-3. At S the same command runs on each host class and `diff-inventory` lists missing and added node ids. Every baseline node id is collected unless a recorded maintainer decision names its rename or removal. Each node that passed or skipped at the baseline passes or skips at S, BE-1 and BE-2 pass, and no `--deselect`, `-k` or `--ignore` is added to the baseline selectors of E-004, E-009 and E-012.
    - Acceptance tests: D9-AC-4 (Windows leg): 0 baseline node ids missing without a recorded decision, BE-1 and BE-2 `PASSED`, 0 added selection flags, and a deleted test is reported missing (negative control). The Linux leg is the deferred row DLV-3. Until its record exists the Linux check stays UNVERIFIED (R-D9-5), and the inventory file `TEST_INVENTORY.linux.txt` does not exist.
    - Environment: Windows. The Linux inventory and the Linux outcomes are PH7-09a or OA-02 (DLV-3).
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the Windows collection run at `84df25c`, the SHA-256 command for the file and `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release`. D9-AC-4 (Windows leg) SUCCEEDED. DLV-3 stays UNVERIFIED until its own record exists.
    - Rollback: RP-1 `git revert`. The worktree is disposable. A failed rollback: OD-D10-3.
    - Depends on: PH7-08
    - Findings: TPR-H-9, TPR-C-1
    - _Requirements: 14.22, 13.9_

  - [ ] 7.9a PH7-09a Autonomous Linux full-checkout route and the deferred Linux rows
    - Objective: Add the `linux-run` subcommand to `scripts/release_verify.py` (D10.11 TR-9, TPR-H-9). It verifies a commit on a Linux_Docker_Host without a bind mount. (1) `git bundle create` of an existing ref that resolves to the commit; no ref is created, moved or deleted. (2) A preparation stage with network access builds a verification image from pinned bases (CPython 3.12.4 or later, Node, git, uv) and fills the `uv` cache and the npm cache from the committed lock files only, and runs no repository code. (3) A run stage starts a container with `--network none`, copies the bundle in with `docker cp`, clones it inside the container file system, checks that `git rev-parse HEAD` equals the commit and that `git status --porcelain` is empty, runs `uv sync --frozen --offline` and `npm ci --offline` (the UI development dependencies), then runs the listed commands unpiped with `-rA`, and copies the outputs out with `docker cp`. (4) It records the network-none negative control, `docker inspect` showing 0 mounts, a POSIX mode probe, the Python version and the exit codes, labelled `LINUX_CONTAINER_FULL_CHECKOUT` and `DIRECT`. (5) It removes only the container that it created. It never reports `SUCCEEDED` unless every step succeeded, and a missing Docker engine gives `UNVERIFIED` with the reason. Use the route on `84df25c` for `--collect-only` and the `-rA` run (the Linux baseline, DLV-3, and the file `docs/next-phase/baseline/TEST_INVENTORY.linux.txt` with its SHA-256). Use it on the then-current tip for the Linux legs of BE-1 (DLV-1), of BE-2 with at least 30 Linux trials (DLV-2), and of the five cases that skip on Windows (DLV-4). The tip runs are early feedback and are never evidence for S, because PH7-17 runs every deferred row again on S. Browser E2E stays a CI row unless the image holds Playwright browsers.
    - Acceptance tests: D10-AC-18. HEAD equals the commit and the status is empty. `docker inspect` shows 0 mounts. A directory created with mode 0700 reads back as 0700. The network-none negative control is recorded. `uv sync --frozen --offline` and `npm ci --offline` succeed. The `-rA` listings and the direct exit codes are captured (1.16). A run that uses a bind mount is refused, and a failed step is never `SUCCEEDED`. D9-AC-4 (Linux leg), the Linux legs of D8-AC-4, D8-AC-6 and D8-AC-7, and D10-AC-28: each deferred row is `SUCCEEDED` only with a record that names this route or OA-02, and stays `UNVERIFIED` otherwise. A Linux result that contradicts a Windows diagnosis reopens PH1-04, PH1-08 or PH1-09.
    - Environment: Linux_Docker_Host (the Docker Desktop Linux engine on the Windows host, or a Linux VM). The preparation stage needs network access and runs no repository code. The run stage is offline.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for each `linux-run` stage, the mount read, the negative-control probes, the baseline `--collect-only` and `-rA` runs at `84df25c`, the SHA-256 command for `TEST_INVENTORY.linux.txt`, and the tip runs of DLV-1, DLV-2 and DLV-4. D10-AC-18 SUCCEEDED. Each deferred row is recorded `SUCCEEDED`, `FAILED` or `UNVERIFIED` with its own record. If the Docker engine cannot run the route, the rows stay `UNVERIFIED` with that reason and OA-02 is the owner route.
    - Rollback: RP-1 `git revert`. The container, bundle and image are disposable and hold no ref. A failed rollback: OD-D10-3.
    - Depends on: PH7-09
    - Findings: TPR-H-9, TPR-C-1, TPR-L-4
    - _Requirements: 13.13, 14.22, 1.12, 1.16, 13.29, 14.3_

  - [ ] 7.10 PH7-10 gate-e2e scenario and replay matrix
    - Objective: Add `scripts/gate_e2e.py` and a `gate-e2e` subcommand in `deploy/entrypoint.sh`, which passes `VK_SIGNING_KEY_FILE` and `VK_TRUST_STORE_FILE` to `as_custodian` only. `scripts/gate_http.py` is not edited. For each of `quote.finance.v1`, `quote.lease.v1` and `reel.mechanical.v1` it runs, with Isolation_Mode `ENFORCED` and constructed inputs labelled synthetic (existing fixtures only): submit, freeze, run through the authenticated examiner, download a signed Bundle, and replay it offline in a separate `--network none` container on the same image. It stops at the first failed step, keeps earlier records and exits non-zero. The signing key is a throwaway created in memory in the container, and no key is committed. It writes a public Trust_Store and a tampered copy (one byte of the stored `manifest.json` data changed). The replay matrix covers the unsigned Bundle, the signed Bundle with and without a Trust_Store entry, the tampered copy and the legacy corpus.
    - Acceptance tests: D9-AC-6: 3 of 3 types pass the 5 steps in order, the run record, outcome and Bundle record `ENFORCED`, the replay is `REPRODUCED`, and 5 of 5 injected failures (one per step) give scenario `FAILED`, name the failing step and keep earlier records. D9-AC-7: unsigned gives `UNSIGNED` and `NOT_ESTABLISHED`; signed with the entry gives `VALID`, `TRUSTED` and `ESTABLISHED`; the same Bundle without a Trust_Store gives `VALID`, `NOT_EVALUATED` and `NOT_ESTABLISHED`; the tampered copy gives `UNVERIFIABLE` or `INVALID` with `NOT_ESTABLISHED`; 0 outbound connections and 0 key files in the output directory or the repository. D9-AC-8: the legacy corpus has an equal Verdict_Hash and `REPRODUCED` or `REPRODUCED_ACROSS_ENV`. D9-AC-5: the five container commands exit 0 with `--network none` and the image ID is equal before the first and after the last (development run, repeated in PH7-17). Each of these container runs records the network-none negative control (only `lo`, and a failing outbound connection), and a gate record without it is not `SUCCEEDED` (1.5, 14.4).
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the image build, `gate-isolation`, `gate-startup`, `gate-http`, `gate-case`, `gate-e2e`, each `verdictkit replay` run with `--network none`, the injected-failure runs and `docker image inspect` read before the first and after the last. D9-AC-5, D9-AC-6, D9-AC-7 and D9-AC-8 SUCCEEDED (VM-6 to VM-9 on the current tree).
    - Rollback: RP-3 and RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-08, PH3-12, PH6-12
    - _Requirements: 14.5, 14.6, 14.7, 14.18, 14.23, 14.24_

  - [ ] 7.11 PH7-11 CI workflow changes
    - Objective: Edit `.github/workflows/p0-integration.yml` to add one step for each ledger row E-001 to E-028 that the workflow lacks, `-rA` on every pytest step, steps that record `git rev-parse HEAD`, `git status --porcelain` and the image ID, the `gate-e2e` step, the HK-7 matcher and runner tests, output under the runner temp directory, longer `timeout-minutes` (the change is recorded), and an optional `windows-latest` job as extra evidence only (OD-D9-3). Also add (D10.11 TR-12, TR-18): `docker build --build-arg VK_COMMIT_SHA=${{ github.sha }}` followed by a step that compares the image label `org.opencontainers.image.revision`, the build argument and the `commitSha` of `GET /api/v1/health` with `github.sha` and validates the other provenance labels; explicit steps that collect and run `tests/security`, `tests/sdk` and `tests/release`, each preceded by `collect-check`, so that a directory that collects 0 tests, a missing manifest node id or pytest exit code 5 fails the step, and a step that reads `gate-isolation-counts.json`; and a step that fails when the Python of the runner is older than 3.12.4 and records the full version. Edit `scripts/gate_nov22.sh` to take an output-directory variable (default `gate`) so a run leaves a clean tree (R-D9-2). Open no pull request and make no merge for CI. The dispatch itself (VM-10) runs in PH7-17 after OA-01 authorizes the push.
    - Acceptance tests: A workflow lint finds a step for every ledger row, `-rA` on every pytest step, `timeout-minutes` on both jobs, and the output directory outside the clone. D10-AC-22 and D10-AC-27: the lint also finds the `VK_COMMIT_SHA` argument, the label comparison, the `collect-check` steps for the three directories, the counts step and the Python floor step, and a copy of the workflow without any one of them fails the lint. D9-AC-9 negative controls pass through `check-run` of PH7-08 (4 of 4 fail the check). D8-AC-26 precondition: the `workflow_dispatch` trigger is present in the workflow file on the default branch (read locally).
    - Environment: CI. The dispatch needs OA-01. The workflow lint and the local reads run on Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the workflow lint run, `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release` and `git show master:.github/workflows/p0-integration.yml` (trigger read). The run-level check of D9-AC-9 and D8-AC-26 stays UNVERIFIED until the dispatch record exists.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-10
    - Findings: M-3, TPR-M-9, TPR-L-4
    - _Requirements: 14.20, 14.1, 14.3, 14.17, 13.7, 13.8, 13.29_

  - [ ] 7.12 PH7-12 Provenance and release report generator
    - Objective: Add the `provenance` subcommand to `scripts/release_verify.py` and the report generator for `docs/next-phase/RELEASE_REPORT.md`. The provenance block holds the commit S, the image ID (local and CI runs listed separately, with the image label equal to S), the `uv.lock` and `package-lock.json` hashes from the committed blobs, the tool versions including the Python patch, the host class of each run, the plugin provenance manifest hash (the value `NOT_BUILT` while PH6-04 is deferred, never an invented hash) and the contract version. The report has the two readiness lines, the Outcome_Class of every acceptance criterion for each of the nine tracks with its record id, the baseline comparison, every UNVERIFIED item with its reason (Browser E2E, `gate_nov22.sh`, the five skipped Linux cases, automatic hook execution), every FAILED step and unremediated Baseline_Exception, blockers RB-1 to RB-20 with level (RB-18 per OD-D10-3, RB-19 and RB-20 per D10.11) and each unresolved owner decision with the tasks that it blocks, the known limitations (always including KL-1, the baseline entry-point loading in the public profile), RP-1 to RP-9 with confirmations (RP-9 is listed `NOT_APPLICABLE`, because no plugin allowlist exists while PH6-04 is deferred) and the no-hosted-demonstration statement.
    - Acceptance tests: D9-AC-13: 7 of 7 provenance fields present and the recomputed hashes equal the recorded ones. D9-AC-11: an unrun item is `SUCCEEDED` with a record of S or `UNVERIFIED` with a reason, and a `VERIFIED` level with an open blocker is rejected. D9-AC-14: every criterion of the nine tracks listed with its Outcome_Class and record id. D9-AC-18: 2 separate readiness lines, 0 combined, and 0 release records containing `aws`, `terraform`, `certbot`, `docker push`, `gh release`, `gh pr create`, a tag-creating `git tag` or a `git merge` other than `git merge-base`. D9-AC-19: 9 of 9 RP rows with a confirmation check.
    - Environment: Both.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release` on each host, the generator run on a sample ledger and `uv run --no-sync ruff check .`. D9-AC-11, D9-AC-13, D9-AC-14, D9-AC-18 and D9-AC-19 SUCCEEDED for the generator and its negative controls. The final report is PH7-18.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-08
    - Findings: M-6
    - _Requirements: 14.10, 14.11, 14.12, 14.17, 14.19, 14.25, 14.26, 14.27, 7.14_

  - [ ] 7.13 PH7-13 Third-party reproduction document
    - Objective: Write `docs/next-phase/REPRODUCING_VERIFICATION.md`: how a third party reproduces the Release_Candidate verification from a clean checkout of S on both host classes. It lists the tools with their versions, the clean-checkout steps (clone, detached checkout of S, `uv sync --frozen --all-packages --all-extras --group dev`, `npm ci`), every command of the D9.4 matrix as exact text, the `linux-run` route of PH7-09a with its offline constraints, the dispatch procedure of VM-10 (an owner step) and the publication rule. The comparison with the command texts of the S records is completed in PH7-18, because those records exist only after PH7-17. That comparison is read-only. A mismatch is a `FAILED` row and a new Release_Candidate, because this document is a Test_Input and is never edited in an Evidence_Commit (D10.11 TR-2).
    - Acceptance tests: D9-AC-17 structural legs: every tool named in a documented command has a version field, both host classes are covered, and every command of VM-1 to VM-19 appears as exact text with no placeholder. The leg "every command text of the S records appears in the document" runs in PH7-18.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for the `report-lint` run on the document and the publication scan over it (counts per class). The structural legs of D9-AC-17 SUCCEEDED.
    - Rollback: RP-1 `git revert`. A failed rollback: OD-D10-3.
    - Depends on: PH7-12
    - _Requirements: 14.15_

  - [ ] 7.14 PH7-14 Release evidence hygiene and historical re-checks
    - Objective: Before every evidence commit, run the publication scan over each file to be published (counts per class, 0 hits), record the Private_Original and Sanitized_Copy hashes separately, and run the ledger lint. Run the whole `wording-scan` catalog (WS-1 to WS-8 of PH1-03a, TPR-L-1) over README, `docs/` and UI text, and for an Evidence_Commit also `check-evidence-commit` (D10.11 TR-2). Add the `audit-scan` subcommand and recompute H1 to H8 read-only from the Historical_Audit directories without copying any file. The source directories must be unchanged (file count, bytes and tree hash) and the repository must hold 0 files whose SHA-256 equals a Historical_Audit file and 0 tracked `messages.jsonl`. A differing value is recorded with both values, a value that cannot be recomputed is `UNVERIFIED` and unused, and each result carries its host label. Credits stay `NOT_AVAILABLE` unless read from a Kiro usage record, and the entries U-001 to U-005 are never summed.
    - Acceptance tests: D9-AC-20: 0 hits in each class of 3.14 for every file to be published, hashes recorded separately, 0 command fields with an ellipsis or placeholder, each record cites its Execution_Index id, and 0 reconstructed items. D9-AC-21: the source directories are unchanged, H1 to H8 are recomputed or `UNVERIFIED`, and 0 audit-based statements lack an H citation. D9-AC-22: 0 estimated or back-filled credit figures, 0 sums of U-001 to U-005, and no cost per task, test or requirement without a Credit_Record for that exact unit. If the Historical_Audit directories are unavailable the re-check is `UNVERIFIED` (R-D9-7). D8-AC-24 (Kiro evidence preservation): 0 reconstructed items, each Private_Original hash recorded, and every usage figure traces to a Kiro usage record or is `NOT_AVAILABLE`. The Kiro-side originals come from OA-05, and a row without them stays `UNVERIFIED`.
    - Environment: Windows. Credit_Records come from OA-05.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, runner counts, commit SHA, UTC start, recorded_utc within 5 s) for `uv run --no-sync pytest -q -p no:cacheprovider -rA tests/release`, the scan, the lint, the read-only recomputation of H1 to H8 and the before and after tree hashes of the source directories. D9-AC-20 and D9-AC-21 SUCCEEDED, or `UNVERIFIED` with the reason. D9-AC-22 needs the Credit_Records of OA-05, otherwise the figures are `NOT_AVAILABLE`.
    - Rollback: RP-8 (supersede with a new Sanitized_Copy and a new hash, never rewrite history) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH7-12
    - Findings: H-1, L-5, TPR-M-1, TPR-L-1
    - _Requirements: 3.8, 3.11, 3.12, 3.13, 3.14, 1.14, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10, 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 7.15 PH7-15 Frozen refs, Submission_Artifacts and coverage check
    - Objective: At the end of the phase run `frozen`: the four ref values (tag object, peeled commit, `master`, `verified-quote-e2e-20261118`) and the diff of each Submission_Artifacts file against `84df25c`, including any file the owner added before S (OA-09). Run the coverage and register check of D10-AC-8 over `requirements.md`, `design.md` and this `tasks.md` with a script under `scripts/` (name chosen at implementation): every criterion has a section and a row in D10.5, every task cites at least one criterion (4.3), every checkbox follows its record (4.9), and the Track register has 9 of 9 entries (P0 to P8). The same check reads the graph: every `Depends on` id exists, there is no cycle, and no two tasks of one wave name the same source file (D10-AC-30, TPR-M-11).
    - Acceptance tests: D9-AC-16: 4 of 4 values equal those of 1.2 and the Submission_Artifacts diff is empty. D10-AC-8: 0 criteria without a section and a row, 0 components without a requirement, 0 unresolved identifiers in D10.5, 9 of 9 register entries, 0 untraced tasks and 0 checkboxes that do not follow their record. D10-AC-30: 0 cycles and 0 same-file conflicts in one wave. D10-AC-17: the owner items keep the order of D10.11 TR-8 (OA-00 before every implementation task, PH4-08 before OA-04, OA-06 after PH4-06 and PH4-10, OA-05 after OA-04 and OA-06, registry review and retrieval before promotion, and OA-09, OA-01, PH7-17, OA-03, PH7-18 in that order).
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, commit SHA, UTC start, recorded_utc within 5 s) for the `git rev-parse` reads of the four refs, `git diff --quiet 84df25c HEAD` over each Submission_Artifacts file and the coverage check run. D9-AC-16 (phase-end leg) and D10-AC-8 SUCCEEDED.
    - Rollback: None (records are append-only; a wrong record is superseded, never edited).
    - Depends on: PH7-12
    - _Requirements: 1.2, 1.3, 14.14, 4.1, 4.2, 4.3, 4.9_

  - [ ] 7.16 PH7-16 Local demonstration run
    - Objective: Run `serve` of the built image on a loopback-only published port chosen at run time (1.17) with a run-time vault key. Run SM-1 (`GET /api/v1/health` answers within 10 s with 200, the exact key set, `isolationMode` `ENFORCED`, `judgeMode` true and `commitSha` equal to the built commit) and SM-7 (the synthetic Reel lifecycle completes with a verdict and `isolationMode` `ENFORCED`) against it. Publish no other port and stop only the container this run started. Nothing is public: no DNS record, certificate, public listener or announcement (14.26).
    - Acceptance tests: VM-12: SM-1 and SM-7 pass, and `docker ps` shows 0 other published ports. OD-D9-6: `serve` plus SM-1 and SM-7 is the meaning of "runs the demonstration locally". The release run repeats this on S in PH7-17.
    - Environment: Linux_Docker_Host.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, commit SHA, UTC start, recorded_utc within 5 s) for `docker run` of `serve`, the SM-1 and SM-7 requests and `docker ps`, and the stop command. VM-12 SUCCEEDED on the current tree.
    - Rollback: RP-3 (stop the container this run started; run the previous image) and RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH7-10, PH5-13
    - _Requirements: 14.26, 7.13, 7.14_

  - [ ] 7.17 PH7-17 Release_Candidate verification run
    - Objective: Start only after `check-checkpoints` shows the six checkpoint records PH1-18, PH2-10, PH3-14, PH4-10, PH5-17 and PH6-12 as `SUCCEEDED` (or `UNVERIFIED` with an accepted reason), after OA-09 has selected S and frozen the code, and after OA-01 has recorded the authorization of the push of S and of the dispatch, or its refusal. A checkpoint that is missing, `FAILED` or unexplained `UNVERIFIED` starts nothing and is listed as RB-19 (TPR-H-3). Then run D9.4 VM-1 to VM-18 in a clean checkout of the full 40-character S on both host classes. That covers the rerun set E-001 to E-028 with `-rA` (E-005 as the 30-trial BE-2 loop on each host, E-025a and E-025b as the Linux full-checkout `-rA` run), the new-capability tests, the four container gates (the extended `gate-isolation` included, with its counts) and the offline replay with `--network none`, each with its network-none negative control, the final security matrix of PH7-05 on S, the enforced end-to-end scenario and replay matrix, the legacy corpus, the deferred Linux rows DLV-1 to DLV-4 on S through the route of PH7-09a or OA-02, the CI dispatch with the head-SHA check (VM-10), the local demonstration, the frozen refs, provenance, the S-time checks of `report-lint` (VM-15a), the publication scans, and the owner rows VM-11, VM-17 and VM-18 as supplied. VM-19 and the `report-lint` of the report itself belong to PH7-18, because the review of the exact S (OA-03) and the report come after this task (TPR-H-8, TPR-M-10). Every count comes only from the S runner output. A new commit that is not an Evidence_Commit is a new Release_Candidate and every verification runs again (D10.11 TR-2). Each Evidence_Commit names the full tested SHA S (OD-D9-1) and is never described as S. Windows observations and Linux results stay in separate rows (1.12, 1.16). Push, tag, merge, deploy and provision nothing.
    - Acceptance tests: D9-AC-1 and D9-AC-2: HEAD equals S and the status is empty before and after each run, and each ledger row E-001 to E-028 has one record per host class with S, step, Outcome_Class, passed and failed counts, start and end, or `UNVERIFIED` with a reason. D9-AC-5 to D9-AC-9 as in PH7-10 on S. D9-AC-3 and D9-AC-4: 0 counts from another commit and 0 baseline node ids missing without a decision. D9-AC-10 (TPR-M-1): each hook and each of the four tools is `SUCCEEDED` with a cited Kiro capture (id and SHA-256) or `UNVERIFIED`, H6 and H8 are not cited for S, and U-001 to U-005 are unchanged. D10-AC-16: all six checkpoint records are present, and a missing one starts nothing. D10-AC-13 and D10-AC-15 on S: the counts of the extended gate equal the manifest. D10-AC-28: each deferred row has a `SUCCEEDED` record that names a Linux source and S, or stays `UNVERIFIED` with RB-1 or RB-3 open. D10-AC-29: the criteria 1.4, 1.5, 1.6, 1.7, 1.10, 1.11, 1.15, 1.16, 2.7 and 14.4 are checked as the table "TPR-M-2 mapping" of the Notes states. Rows that need an owner stay `UNVERIFIED` with the reason.
    - Environment: Both. The Linux full-checkout runs use the route of PH7-09a or OA-02, the CI dispatch needs OA-01, and the owner rows need OA-05 and OA-06. The review of the exact S (OA-03) comes after this task.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code read directly with no pipe, runner counts, full 40-character commit SHA S, UTC start and end, recorded_utc within 5 s) for every VM row on each host class, `git rev-parse HEAD` and `git status --porcelain` before and after each run, and `docker image inspect` read before the first and after the last gate. D9-AC-1 to D9-AC-10 SUCCEEDED or `UNVERIFIED` with the reason, the output of `check-checkpoints`, and the DLV-1 to DLV-4 records on S.
    - Rollback: None for the records (records are append-only; a wrong record is superseded, never edited). A defect fix is a new commit, which makes a new Release_Candidate, and is reverted by RP-1. A failed rollback: OD-D10-3.
    - Depends on: PH1-18, PH2-10, PH3-14, PH4-10, PH5-17, PH6-12, PH7-01, PH7-02, PH7-03, PH7-04, PH7-05, PH7-06, PH7-07, PH7-08, PH7-09, PH7-09a, PH7-10, PH7-11, PH7-12, PH7-13, PH7-14, PH7-15, PH7-16, OA-09, OA-01, OA-02, OA-05, OA-06
    - Findings: TPR-H-3, TPR-H-8, TPR-M-10, TPR-C-1, TPR-C-2
    - _Requirements: 14.1, 14.2, 14.8, 14.16, 14.21, 14.3, 14.4, 14.10, 14.11, 1.4, 1.5, 1.6, 1.7, 1.10, 1.11, 1.15, 1.16, 2.7, 4.4_

  - [ ] 7.18 PH7-18 Final release report and blocker list
    - Objective: Run after PH7-17 and after OA-03 has recorded the review of the exact S, or has recorded it `NOT_PROVIDED` (TPR-H-8). Generate `docs/next-phase/RELEASE_REPORT.md` from the S records with the generator of PH7-12 and commit it as an Evidence_Commit. Compare every command text of the S records with `docs/next-phase/REPRODUCING_VERIFICATION.md` read-only, because that document is a Test_Input and is never edited here. Then run VM-19 (the External_Review_Record reference against the hashes of the reviewed files at S, D9-AC-12 and D8-AC-27) and VM-15b (`report-lint` of the report, which can run only now that the report exists, TPR-M-10). The report names S as the tested commit and names the Evidence_Commit that holds it, with `check-evidence-commit` (D10.11 TR-2, OD-D9-1). It gives Local_Readiness and Public_Deployment_Readiness as two separate lines, each `VERIFIED` only when no blocker of that level is open. It lists every blocker RB-1 to RB-20 with its level (RB-18 stays open after a failed rollback until recovery to a verified checkpoint, OD-D10-3; RB-19 and RB-20 per D10.11), every unresolved owner decision, every `UNVERIFIED` item and every `FAILED` step. Its Kiro usage is a Credit_Record or `NOT_AVAILABLE`. It states that no hosted demonstration is available until criterion 7.13 is met. The ticks of PH7-17 and PH7-18 are the only change of `tasks.md` in these commits. No tag, merge, publication or provisioning happens, and every such action is an owner decision (OA-10).
    - Acceptance tests: D9-AC-11: each `FAILED` step, each unremediated Baseline_Exception and each RB row with its level is listed, and a `VERIFIED` level with an open blocker is rejected. D9-AC-15: 0 pushes without a cited authorization, each push is of `feature/kiro-next-phase` without force with the ref values before and after, and remote `master` and both tags equal their recorded values. D9-AC-17: every command text of the S records appears in the reproduction document. D9-AC-18: 2 separate readiness lines and 0 provisioning commands in the release records. D9-AC-12 and D8-AC-27 (TPR-M-1): a reference with its 7 fields exists, is attributed `OWNER_ATTESTED` and not to the agent, every reviewed-file hash equals that file's hash at S, and the report quotes the verdict. With no record, RB-4 is listed and Local_Readiness stays `NOT_VERIFIED`. D10-AC-12: `check-evidence-commit` passes for the report commit and for each ledger commit, and fails on its negative controls. `report-lint` (VM-15b) finds 0 violations in the report.
    - Environment: Windows.
    - Completion evidence: Execution_Records (3.2, 3.12, OD-D10-2: exact command, exit code, commit SHA, UTC start, recorded_utc within 5 s) for `report-lint` over the report and the reproduction document, `check-evidence-commit`, VM-19, `git ls-remote origin refs/heads/feature/kiro-next-phase` where a push occurred (values before and after) and the frozen-ref commands. D9-AC-11, D9-AC-15, D9-AC-17, D9-AC-18 and D10-AC-12 SUCCEEDED. D9-AC-12 and D8-AC-27 are `SUCCEEDED` only with the OA-03 record, and `UNVERIFIED` with the reason when OA-03 is `NOT_PROVIDED`. The verification of the last Evidence_Commit is run before it is created and by the documented command afterwards, and a later Evidence_Commit, if there is one, records it.
    - Rollback: RP-1 `git revert` of the report commit. A published report is superseded by a new commit and never edited. If a rollback does not complete, RB-18 stays open until recovery to a verified checkpoint (OD-D10-3).
    - Depends on: PH7-17, OA-03
    - Findings: M-6, TPR-H-8, TPR-M-1, TPR-M-10, TPR-C-2
    - _Requirements: 14.10, 14.11, 14.12, 14.13, 14.26, 14.27, 13.27, 14.16, 14.21, 4.5, 4.7_

## Owner-only actions

These items need the repository owner, a reviewer or a maintainer. They have no checkbox, so a task runner never queues them. "Blocks" names the tasks whose owner rows or capability statements stay UNVERIFIED until the owner's record exists. A task's box depends on an OA item only where that task names it in Depends on. The agent records what the owner supplies and never writes, alters or waives an owner record. Each item has a Kind and a Depends on line (D10.11 TR-8). A GATE item must be `PROVIDED` before a task that names it starts. An EVIDENCE item may be recorded `NOT_PROVIDED` by the owner, which keeps its rows `UNVERIFIED` and its blockers open. Statuses: OA-00 is `PROVIDED` (`ACCEPTED_WITH_CONDITIONS`) and OA-08 is `PROVIDED` for OD-D8-1 to OD-D8-4. The agent transcribed both from the owner's request of 2026-11-26 into `docs/next-phase/OWNER_DECISIONS.md` and made no decision of its own. OA-02 is `NOT_PROVIDED`, OA-07a to OA-07e are `DEFERRED`, and every other item is `OPEN`: no record exists for it, and none was inferred.

### OA-00 Owner acceptance of D8 to D10 and of the corrected task plan

- Purpose: Record that the repository owner has reviewed and accepted the design sections D8, D9 and D10 (including D10.11), the canonical sections and this task plan after the task-plan review remediation, as `ACCEPTED`, `ACCEPTED_WITH_CONDITIONS` or `REJECTED` (4.10, TPR-H-7). The remediation that wrote this plan is documentation work and is not this acceptance. PH1-01, which only read the repository and wrote the Evidence_Ledger, is the single completed task that predates it. No task that adds or changes an application file, a test, a script, a configuration file or a lock file starts without it.
- Kind: GATE
- Depends on: none
- Blocks: PH1-02 and, through it, every implementation task of every phase.
- Requirements: 4.10, 4.2, 4.3
- Findings: TPR-H-7
- Owner provides: A record with its identifier, its date, its verdict, the commit of `tasks.md` that it covers and the SHA-256 of `design.md`, `requirements.md` and `tasks.md` at that commit. The agent never writes, alters or waives it.
- Status: PROVIDED. Verdict `ACCEPTED_WITH_CONDITIONS`, recorded 2026-11-26 in `docs/next-phase/OWNER_DECISIONS.md`, which holds the covered commit and the SHA-256 values of the three documents.

### OA-01 Authorize each Phase_Branch push and CI dispatch

- Purpose: Each push of the Phase_Branch and each CI workflow dispatch needs the owner's explicit authorization in the request that asks for it, and a push is never a force push (DD9-4, DD9-5, OD-D9-4). CI runs by dispatch on the Phase_Branch with a head-SHA check, with no pull request and no merge.
- Kind: EVIDENCE (a refusal is recorded `NOT_PROVIDED`, and the CI result is then `UNVERIFIED`)
- Depends on: OA-09
- Blocks: PH7-17 (CI run record, VM-10). For the release, OA-01 follows OA-09, which selects S, and precedes PH7-17 (TPR-H-8).
- Requirements: 14.13, 14.20
- Findings: M-3, TPR-H-8
- Owner provides: The authorization text of the request that asks for the push. For each push, the remote value of `refs/heads/feature/kiro-next-phase` before and after. For each dispatch, the saved run record (`headSha`, `headBranch`, `event`, `status`, `conclusion`, `createdAt`) and the run logs as Private_Originals.
- Status: OPEN

### OA-02 Linux_Docker_Host full-checkout runs

- Purpose: Supply the Linux evidence that needs a full checkout: the BE-1 and BE-2 Linux legs with `-rA` and the directly captured pytest exit codes, the Linux per-test baseline run and collection at `84df25c`, and the Linux security cases and the five cases that skip on Windows (B-D8-1). The container image has no `ui/`, so an image run cannot stand in for these runs.
- Kind: EVIDENCE. This is the owner route for the deferred Linux rows DLV-1 to DLV-4. The autonomous route is PH7-09a (TPR-C-1, TPR-H-9), and a record names which route produced it.
- Depends on: PH7-09
- Blocks: No box. It supplies the deferred rows that PH7-09a cannot supply, and PH7-17 uses it as supplied. The Windows-leg boxes of PH1-04, PH1-08, PH1-09 and PH1-10 never wait for it. RB-1 and RB-3 stay open until a record that names a Linux source exists.
- Requirements: 13.13, 14.22, 1.12, 1.16
- Owner provides: For each run, the exact command text, the `-rA` per-test listing, the pytest exit code captured directly (no pipe), the full commit SHA, the UTC time, the host class, and the output of `git rev-parse HEAD` and `git status --porcelain`. For the baseline, the `--collect-only` output as a Private_Original with its SHA-256.
- Status: NOT_PROVIDED. The owner supplies no separate owner-host Linux execution (recorded 2026-11-26 in `docs/next-phase/OWNER_DECISIONS.md`). This is not a waiver: DLV-1 to DLV-4 stay `UNVERIFIED`, and RB-1, RB-3 and RB-13 stay open until PH7-09a, or a later record, supplies a `SUCCEEDED` record that names a Linux source.

### OA-03 External_Review_Record kept outside the repository

- Purpose: A security review of the Threat_Model, the key-handling controls, the hook configuration and the release surface, made by the owner or an independent reviewer (DD8-13, B-D8-2). The repository holds only a reference. A change to a reviewed file voids the record. The agent cannot create, alter or waive it.
- Kind: EVIDENCE. The review is of the exact S that OA-09 selected, and it is made after PH7-17 has verified S (TPR-H-8).
- Depends on: OA-09, PH7-17
- Blocks: PH7-18 (VM-19, D9-AC-12 and D8-AC-27; RB-4: Local_Readiness stays NOT_VERIFIED without it).
- Requirements: 13.27, 14.27
- Findings: M-6, TPR-H-8, TPR-M-1
- Owner provides: A reference labelled OWNER_ATTESTED with the record identifier, its SHA-256, the date, the verdict (`ACCEPTED`, `ACCEPTED_WITH_CONDITIONS` or `REJECTED`), the reviewed commit and the hashes of the reviewed files. The storage location is the owner's choice (OD-D8-7).
- Status: OPEN

### OA-04 Contained_Hook_Environment

- Purpose: Provide a dedicated virtual machine or a restricted operating-system account that meets conditions CE-1 to CE-8 (DD8-15, B-D8-3): no cloud, signing or `VK_VAULT_KEY` credential and no access to the owner's profile, a push-disabled clone with a closed environment list, pinned tool versions, an outbound block (firewall rule, OD-D8-9) or a recorded remaining exposure, hash-pinned hook files, a clone refreshed only from a reviewed commit, and evidence that leaves only as Private_Original plus Sanitized_Copy. Without it no hook counts as automatic execution and each hook stays UNVERIFIED.
- Kind: EVIDENCE
- Depends on: PH4-08
- Blocks: The owner rows D8-AC-25 and D3-AC-21 of PH4-08, and PH7-17 (VM-11). OA-04 follows PH4-08, which prepares the session template, and precedes OA-05 (TPR-H-5).
- Requirements: 8.20
- Findings: M-5, TPR-H-5
- Owner provides: The session record from the PH4-08 template with each of CE-1 to CE-8 marked met or not met with the reason, the environment class stated without account names, host names or SIDs, the tool-version pin record and the firewall decision.
- Status: OPEN

### OA-05 Kiro sessions in the disposable trusted checkout

- Purpose: Run the Kiro sessions that only the owner can capture, inside the Contained_Hook_Environment: hook firing in the disposable checkout (trust granted to that folder only), the four VerdictKit MCP tools called from inside Kiro (KM-1 to KM-8), sub-agent capture, preserved authoring and execution evidence (spec files, the `.config.kiro` identifier, session exports) and the Kiro usage records. Nothing is reconstructed.
- Kind: EVIDENCE
- Depends on: PH4-04, PH4-06, PH4-09, OA-04, OA-06
- Blocks: The owner rows D3-AC-12, D3-AC-13, D3-AC-14, D3-AC-16, D3-AC-20 and D4-AC-16 of PH4-04, PH4-06 and PH4-09, PH7-14 (D9-AC-22 and D8-AC-24) and PH7-17 (VM-11 and VM-18). OA-05 follows OA-04 and OA-06 (TPR-H-4, TPR-M-1).
- Requirements: 8.15, 8.16, 8.17, 9.11, 9.12, 3.13, 16.1, 16.2
- Findings: L-5, TPR-H-4, TPR-M-1
- Owner provides: The Kiro-side artifacts (KA-1, KA-2, KA-3) with their SHA-256 values, the session record, the `verify-chain` output, and for credits the Kiro usage record (credits, unit, request identifier count, session identifier, date) or the value `NOT_AVAILABLE`. Never an estimate.
- Status: OPEN

### OA-06 Renewed review of hook and MCP configuration changes

- Purpose: A change to a file of the 8.19 pinned set (`.kiro/hooks/*.json`, `scripts/hooks/`, `tests/contract/hook_matcher_corpus.json`, the environment allowlist of the hook runner, `.kiro/settings/mcp.json`) voids the review of the changed surface (D10-AC-6). A reviewer other than the agent records the renewed review.
- Kind: EVIDENCE. The reviewer records the hashes. The agent lists them only as `PENDING_REVIEW` and never approves them (TPR-H-4).
- Depends on: PH2-07, PH4-05, PH4-06, PH4-10
- Blocks: The review state of PH2-07 and PH4-05 (rows D3-AC-11 and D10-AC-6), OA-05 and PH7-17 (VM-11). OA-06 follows the last change of a pinned file: PH4-06 changes the runner after PH4-05 pinned the set, and PH4-10 is the checkpoint. A later change of a pinned file voids the review.
- Requirements: 8.17, 8.19
- Findings: TPR-H-4
- Owner provides: The renewed review record in `docs/next-phase/hooks/HOOK_SECURITY_REVIEW.md` with one row for each of PR-1 to PR-11 (verdict, reviewer class, date, reviewed commit, file hashes).
- Status: OPEN

### OA-07a Official-host registry review

- Purpose: Review the entries of the official-host registry that PH6-06 establishes (the `basis` of each host, and the rule that only an exact registry host is a source), with a human record that the agent cannot write (B-D7-2). No retrieval of regulatory material happens from a host whose entry has no such record (TPR-H-6). The single owner item that the earlier plan held for this is split into OA-07a to OA-07e: retrieval and build are tasks (PH6-05, PH6-08, PH6-09, PH6-10), independent review is OA-07b to OA-07e, and promotion is a task (PH6-08a, PH6-09a, PH6-10a). An unreviewed snapshot is never promoted to `ACTIVE`.
- Kind: GATE
- Depends on: PH6-06
- Blocks: PH6-05, PH6-08, PH6-09 and PH6-10 (retrieval).
- Requirements: 12.4, 12.22
- Findings: TPR-H-5, TPR-H-6
- Owner provides: A review record for each registry host entry (reviewer, date, host, `basis`, decision).
- Status: DEFERRED (owner scope freeze, OA-00). Not queued.

### OA-07b Review of the Texas 7 TAC section 84.205 text

- Purpose: An independent review of the text that PH6-05 retrieved, with the decisions on identical content under two URIs and on rights where a source's terms permit storing a copy. The text is `UNREVIEWED` material until this record exists, and it changes no rule value, finding or UI text before it (TPR-H-6).
- Kind: EVIDENCE
- Depends on: PH6-05
- Blocks: Any change of a Texas rule value or finding that the text supports.
- Requirements: 12.22, 12.24
- Findings: TPR-H-5, TPR-H-6
- Owner provides: A review record (reviewer, date, source URI, SHA-256, the rule values read against the excerpt, stated effective dates, rights decision).
- Status: DEFERRED (owner scope freeze, OA-00). Not queued.

### OA-07c California snapshot review

- Purpose: An independent review, by a reviewer other than the agent, of the California snapshots that PH6-08 built: the rule values read against the excerpt, the stated effective dates, identical content under two URIs and the rights decision (B-D7-2). Promotion to `ACTIVE` needs this record. Without it the jurisdiction is `BLOCKED` and its rules `UNVERIFIED`.
- Kind: EVIDENCE
- Depends on: PH6-08
- Blocks: PH6-08a (promotion).
- Requirements: 12.4, 12.22, 12.24
- Findings: TPR-H-5
- Owner provides: For each snapshot a review record (reviewer, date, source URI, SHA-256, the rule values read against the excerpt, stated effective dates, rights decision) that the loader's review-record hash check accepts.
- Status: DEFERRED (owner scope freeze, OA-00). Not queued.

### OA-07d Florida snapshot review

- Purpose: The same independent review as OA-07c, for the Florida snapshots that PH6-09 built.
- Kind: EVIDENCE
- Depends on: PH6-09
- Blocks: PH6-09a (promotion).
- Requirements: 12.4, 12.22, 12.24
- Findings: TPR-H-5
- Owner provides: A review record for each snapshot, in the form of OA-07c.
- Status: DEFERRED (owner scope freeze, OA-00). Not queued.

### OA-07e New York snapshot review

- Purpose: The same independent review as OA-07c, for the New York snapshots that PH6-10 built.
- Kind: EVIDENCE
- Depends on: PH6-10
- Blocks: PH6-10a (promotion).
- Requirements: 12.4, 12.22, 12.24
- Findings: TPR-H-5
- Owner provides: A review record for each snapshot, in the form of OA-07c.
- Status: DEFERRED (owner scope freeze, OA-00). Not queued.

### OA-08 Maintainer decision records for assumed open decisions

- Purpose: Record maintainer decisions for the open decisions that tasks consume (D10.8). OD-D8-1 to OD-D8-4 must be resolved before the tasks that implement them start, because their values change the implementation (TPR-L-5). The other decisions that tasks assume by recommendation (OD-D8-5, OD-D8-6, OD-D9-3 and OD-D9-6) stay visible: a decision that differs from the assumed value reopens the tasks that name it.
- Kind: GATE for OD-D8-1 to OD-D8-4. EVIDENCE for the others.
- Depends on: none
- Blocks: PH1-11 (OD-D8-1, the key file mechanism), PH1-16 (OD-D8-2 and OD-D8-4, the replay namespace and the quotas), PH1-17 (OD-D8-4, the upload slots) and PH2-02 (OD-D8-3, the default Approved_Root). A recommendation that a task assumes without a record is PH1-09 (OD-D8-6), PH7-11 (OD-D9-3) and PH7-16 (OD-D9-6). OD-D8-5 belongs only to the deferred PH1-07. An unresolved decision is a visible blocker (RB-20) and is listed in the release report.
- Requirements: 7.20, 7.21, 7.22, 9.21, 13.12, 13.25
- Findings: TPR-L-5
- Owner provides: One decision record for each open decision (identifier, chosen option, date), which the agent writes into a new file under `docs/next-phase/` from the maintainer's message.
- Status: PROVIDED for OD-D8-1 to OD-D8-4 (approved as designed, recorded 2026-11-26 in `docs/next-phase/OWNER_DECISIONS.md`). The recommendations for OD-D8-5, OD-D8-6, OD-D9-3 and OD-D9-6 are retained and stay visible. A numeric total replay quota is not part of the approved decision (see the record).

### OA-09 Select the Release_Candidate S

- Purpose: Select S, the full 40-character SHA of the Phase_Branch tip, once PH7-01 to PH7-16 have their records. Freeze the code so that no code, test, configuration, tooling or Test_Input file changes after S (TPR-C-2). Add any further Submission_Artifacts file to the list before S is selected (OD-D9-5). Confirm that the checkpoint records PH1-18, PH2-10, PH3-14, PH4-10, PH5-17 and PH6-12 are SUCCEEDED or accepted as UNVERIFIED with their reasons.
- Kind: GATE
- Depends on: PH1-18, PH2-10, PH3-14, PH4-10, PH5-17, PH6-12, PH7-01, PH7-02, PH7-03, PH7-04, PH7-05, PH7-06, PH7-07, PH7-08, PH7-09, PH7-09a, PH7-10, PH7-11, PH7-12, PH7-13, PH7-14, PH7-15, PH7-16
- Blocks: OA-01 and PH7-17. The release order is OA-09, OA-01, PH7-17, OA-03, PH7-18 (TPR-H-8).
- Requirements: 14.16, 14.21
- Findings: TPR-H-3, TPR-H-8, TPR-C-2
- Owner provides: S in the request that starts PH7-17, the confirmation of the code freeze, and the final list of Submission_Artifacts files.
- Status: OPEN

### OA-10 Any release tag, merge or publication

- Purpose: Decision only. A release tag, a merge, a publication and a push of any ref other than the Phase_Branch are explicit owner actions that lie outside this plan (14.13). No task in this plan creates a tag, merges a branch, publishes an artifact or pushes a ref other than the Phase_Branch.
- Kind: EVIDENCE (a decision only)
- Depends on: none
- Blocks: None. No task depends on it.
- Requirements: 14.13
- Owner provides: A recorded decision. If the owner acts, the owner records the action and the ref values before and after.
- Status: OPEN

## Conditional public deployment tasks

These items are not authorized by this work. Nothing here provisions infrastructure, spends money, creates a DNS record or certificate, opens a public listener or announces a deployment. They have no checkbox. Each stays closed until the owner authorizes it by a separate recorded decision. Scope freeze: all nine items are DEFERRED by the owner (OA-00) and are not authorized. Until every blocker RB-15, RB-16 and RB-17 is clear, Public_Deployment_Readiness is NOT_VERIFIED and the documentation states that no hosted demonstration is available (7.14).

### CD-01 Hosting, domain, certificate, budget, monitoring and credential-distribution decisions

- Purpose: Record the decisions of D2.11 B-6: the hosting target (the preferred initial architecture is one Linux VM running portable Docker and Caddy, AM-1), the region preference and budget target (AM-2), the domain name, the certificate owner, the monthly cap for the budget alarm, the destination of logs and metrics, and how invitation credentials are distributed. Recording a decision authorizes no spending.
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only, RB-16).
- Requirements: 7.17
- Owner provides: A decision record for each item.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-02 Fargate probe task

- Purpose: Run the four container gates on AWS ECS Fargate as a probe, or record Fargate as `REJECTED` for judge mode (D2-AC-4). AM-1 states that no cloud probe, account action or provisioning is authorized, so this item stays unscheduled until the owner authorizes it.
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only).
- Requirements: 7.17, 7.18
- Owner provides: The probe record with gate exit codes, or the `REJECTED` record with its reason.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-03 Deployment, secret store, TLS and HSTS check

- Purpose: Deploy the image on the chosen host with the vault key supplied from the deployment secret store, so that a search of the repository, image layers, logs and the examiner environment finds 0 matches (D2-AC-11), and check TLS 1.2 or later, a valid certificate and HSTS with a `max-age` of at least 15552000 seconds (SM-3).
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only, RB-15).
- Requirements: 7.6, 7.9
- Owner provides: The deployment record, the canary search result with counts, and the SM-3 result.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-04 Deployment security gates and smoke tests on a deployed instance

- Purpose: Run the security gates SG-1 to SG-9 and the post-deploy smoke tests SM-1 to SM-14 on a deployed instance. Public_Deployment_Readiness needs a SUCCEEDED Execution_Record for each gate (RB-15).
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only).
- Requirements: 14.26, 7.13
- Owner provides: One Execution_Record for each gate and smoke test, with the exact command text, exit code, commit SHA and UTC times.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-05 Invitation credential issuance out of band

- Purpose: Issue one invitation credential to each invitee out of band, with at least 128 bits of entropy, stored only as a hash, with a label, an expiry inside the demonstration window and a revocation flag, and rehearse the revocation of one credential (D10-AC-1, SM-6).
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only).
- Requirements: 7.24
- Owner provides: The issuance record without any credential value, and the revocation rehearsal record.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-06 Monitoring, alarms and budget alarm

- Purpose: Put the alarms of D2.8 in place: target unhealthy or `/health` 503, 5xx rate, 429 rate, container restarts above 1 per hour, examiner re-attestation failures, disk free below 25 percent, memory above 80 percent, certificate expiry within 14 days, and a monthly spend threshold (RB-17).
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only).
- Requirements: 14.26
- Owner provides: The monitoring configuration record and a test alarm record.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-07 Rollback rehearsal on the deployed target

- Purpose: Redeploy the previous image digest on the deployed target and confirm the previous `commitSha` on `GET /api/v1/health` within 10 minutes (ASSUMED limit, D2-AC-17).
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only).
- Requirements: 7.15
- Owner provides: The rehearsal record with both `commitSha` values and the elapsed time.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-08 Public-URL Execution_Record

- Purpose: Record that the public URL answers `GET /api/v1/health` within 10 seconds with a success response whose `commitSha` equals the commit of the release being reported. Only then may any documentation present a hosted demonstration (7.14).
- Blocks: PH7-12 and PH7-18 (the no-hosted-demonstration statement and RB-14).
- Requirements: 7.13, 7.14
- Owner provides: The Execution_Record with the response time, the status and the `commitSha`.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

### CD-09 Owner go decision

- Purpose: Record the repository owner's go decision. Public_Deployment_Readiness additionally needs SUCCEEDED records for SG-1 to SG-9, the recorded hosting, domain, certificate and budget decisions, monitoring, a rehearsed rollback and this decision (RB-17).
- Blocks: PH7-12 and PH7-18 (the Public_Deployment_Readiness line only).
- Requirements: 14.26, 14.13
- Owner provides: The recorded decision with its date and the commit it applies to.
- Status: DEFERRED (owner scope freeze, OA-00). Not authorized.

## Notes

- Untraced tasks: none. Each of the 107 tasks (92 queued and 15 deferred) cites at least one criterion of `requirements.md` (4.3). The task-plan review round appended the criteria 3.15, 4.10, 7.27, 10.37, 13.29 and 13.30 and changed 13.11, 13.13, 14.16 and 14.21 in place.
- Optional task: PH1-07 only, marked `- [ ]*` before the scope freeze. It is now DEFERRED and has no checkbox, so the 92 queued tasks are all mandatory. Tests are not split into separate optional tasks. Each task carries the tests that verify it, and their rows are required for its box. This follows the request that overrides the default template.
- Execution_Records and boxes: a box changes in the same commit as the Execution_Record that supports it (4.9). The Evidence_Ledger is append-only, so a wrong record is superseded and never edited, and the ledger is excluded from the same-file placement rule below.
- Verified checkpoint: a Phase_Branch commit whose phase regression set has a SUCCEEDED Execution_Record. Before the first checkpoint the verified checkpoints are the design commit `aea7d06d11cf32f9f5abba7cbd3f33a3472c935a` (documentation only) and the code baseline `84df25c68198e496889b5892a03555ec7d2d860a` with BE-1 and BE-2 accepted.
- Forbidden actions: no task may push, tag, merge, reset history, force-push, deploy or provision. A task that needs a push asks OA-01. Every rollback is a forward commit (RP-1 `git revert`), never a reset or a force push.
- Same-file placement: waves follow the Depends on lines. Where those lines leave two tasks unordered and both name one source file, the later wave is used. The orderings added for this are PH2-03 before PH2-02 before PH2-04 before PH2-05 before PH2-06 (`core/src/verdictkit/mcp_server.py`), PH3-07 before PH3-11 (replay report fields), PH5-11 before PH5-12 (`core/src/verdictkit/api/server.py`) and PH7-09 before PH7-12 (`scripts/release_verify.py`). They do not change any Depends on line. After the task-plan review three orderings are explicit Depends on lines instead (TPR-M-11): PH1-13 before PH1-17 (the start-up and run path and `SafetyMiddleware` share `core/src/verdictkit/api/server.py`), PH1-15 and PH1-17 before PH1-16 (`deploy/entrypoint.sh`, `core/src/verdictkit/examiner/worker.py` and `api/server.py`), and PH3-08 before PH3-05 (`core/src/verdictkit/bundle.py`). The PH1-02 to PH1-03a chain and PH1-11, PH1-12a and PH1-15 are likewise ordered by Depends on lines, because they edit `scripts/release_verify.py` and `deploy/entrypoint.sh` in turn.
- Evidence sources: rows marked CI/VM run on the local Linux_Docker_Host or on CI, and each record names its source. One source never stands in for another in the release run (DD9-7). A "container run" of isolation-marked tests means `gate-isolation`, or the same pytest command inside the image, with a `-rA` listing and `--network none`. Docker commands are issued as `docker` with the Docker Desktop client directory on the session path, so no command field holds an absolute path (3.14).
- Property ownership (TPR-M-3): each property has one authoritative task, which holds its only Hypothesis test. P-a, P-b and P-c in PH3-09. P-d in PH2-03 (PH2-08 adds an example check over stdio and no property test). P-e in PH6-02 (deferred). P-f in PH7-06. P-g in PH6-12. P-h in PH5-12. P-i in PH1-17. P-j in PH2-02. P-k in PH1-03 (PH7-04 adds example checks over the sanitizer and no property test). P-l in PH1-15 (PH7-05 reruns it and adds no second test). P-m in PH6-03 (deferred). P-n in PH7-04. P-o in PH3-08. PH7-02 checks that the 13 queued properties exist exactly once with their tags and guards (P-e and P-m are deferred).
- Plan readings to confirm: (1) The pre-change hash step DR-7 belongs to D5.9, and the replay matrix DR-1 to DR-6 belongs to D8.10, so PH3-01 cites D5.9 DR-7. (2) D8-AC-29 lists two approved test hunks, while 13.26, D5-AC-19 and 10.34 also require the BE-2 port hunk and the contract-version literal changes, so PH7-07 lists all four, of which the AM-D7-1 hunk is not applied (California is deferred). (3) PH7-17 depends on the six phase checkpoints PH1-18, PH2-10, PH3-14, PH4-10, PH5-17 and PH6-12, on PH7-01 to PH7-16 including PH7-09a, and on OA-09, OA-01, OA-02, OA-05 and OA-06, so a missing checkpoint starts nothing and is listed as RB-19 (TPR-H-3).
- Criteria that a task and an owner item both cite: 1.12 (PH7-09a and OA-02) and 13.27 (PH7-18 and OA-03). In earlier versions of this plan only the owner items cited them.

TPR-M-2 mapping. The criteria 1.4, 1.5, 1.6, 1.7, 1.10, 1.11, 1.15, 1.16, 2.7, 2.10, 4.5, 4.7 and 14.4 were cited by no task in earlier versions of this plan. Each is now cited by the tasks below, with a measurable rule (D10-AC-29). The table also holds the design rows that the review found unmapped (TPR-M-1).

| Criterion or design row | Tasks and owner items | Measurable rule |
|---|---|---|
| 1.4 | PH1-18, PH7-17 (VM-2, VM-3) | One canonical record per Baseline_Run step and host class, each with an Outcome_Class, and no second record for one execution (a duplicate is superseded, 1.15) |
| 1.5 | PH1-12a, PH5-14, PH7-10, PH7-17 | The four container gates run only on a Linux_Docker_Host, each with `--network none` and a recorded network-none negative control (only `lo` present, a failing outbound connection) |
| 1.6 | PH7-17 | On a host that is not a Linux_Docker_Host each of the four gates has a record `UNVERIFIED` with a reason and never `SUCCEEDED`, and Windows observations stay in rows apart from Linux results |
| 1.7 | PH7-17, the phase checkpoints | A `FAILED` step keeps its name and its captured output in the ledger and in the report, and no step passes by omission |
| 1.10 | PH1-02, PH1-02a, PH7-17 | Each record holds the exact command, the process exit code, a duration from monotonic readings that differs from UTC end minus UTC start by at most 1 s, the UTC start, the passed, failed, skipped and deselected counts, and the name and reason of every failed and skipped test (D10-AC-10) |
| 1.11 | PH1-02a, PH1-09, PH7-09a | A `FAILED` record has a diagnosis note with its cause and host attribution before the next commit that changes application code |
| 1.15 | PH1-02, PH1-02a | A command with a pipe to `tail` or `head` is refused, an exit code is never inferred from a pipeline, and a duplicate or lock-collision record is an Execution_Error and not a counted failure |
| 1.16 | PH7-09a, PH7-17 | A Linux record is `DIRECT` only if it holds the per-test listing and the pytest exit code captured directly, and otherwise it carries the label indirect |
| 2.7 | PH1-12a, PH5-14, PH7-05, PH7-17 | The gate asserts distinct uids (custodian 900, examiner 901, the observer 0 and a secondary uid that is none of them), the vault directory mode 0700 owned by uid 900, and the examiner socket mode and peer check |
| 2.10 | PH7-03 | A grid one point over the cap is rejected whole, the error names the cap and the observed size, 0 grid points are evaluated, and a subsampling mutant fails the test |
| 4.5 | the phase checkpoints, PH1-02a, PH7-12, PH7-18 | A rollback record holds the track id, the risk that occurred, the action taken and its outcome, and the lint rejects a record that lacks one |
| 4.7 | the phase checkpoints, PH1-03a (WS-7), PH4-04, PH4-09, PH7-14 | Each checkpoint has one row for each of specs, steering, task execution, sub-agents, MCP tools and hooks, with `observed running inside Kiro` or `not observed running inside Kiro` and the captured artifact id, and never an inferred value |
| 14.4 | PH7-10, PH7-17 | A gate that cannot take `--network none`, or a host that is not a Linux_Docker_Host, gives `UNVERIFIED` with the reason, and a record that claims `SUCCEEDED` without the network-none control fails `report-lint` |
| D8-AC-24 | PH7-14, OA-05 | 0 reconstructed Kiro items, and every usage figure comes from a Kiro usage record or is `NOT_AVAILABLE` |
| D8-AC-27 and D9-AC-12 | PH7-18, OA-03 | The reference has its 7 fields, is attributed `OWNER_ATTESTED`, and its reviewed-file hashes equal those at S |
| D2-AC-12 | PH5-09, PH7-04 | 0 log sentinels after the lifecycle run, repeated across all entry points |
| D3-AC-14 and D3-AC-16 | OA-05 | A recorded value or `NOT_DETERMINED` for each of U-1 to U-10, and the per-save wall time over 3 saves |
| D3-AC-18 | OA-00, PH4-03 | The D3 and D8 design review is accepted through OA-00, no hook is attached to the judge-preview test and no timeout is changed |
| D9-AC-10 | PH7-17 | Each hook and each tool is `SUCCEEDED` with a cited Kiro capture or `UNVERIFIED`, and H6 and H8 are not cited for S |
| D7-AC-19 | none | Superseded by AM-D7-3 (D7.11), so it has no task |

Deferred Linux verification register (TPR-C-1, D10.11 TR-1). Each row is `UNVERIFIED` until a `SUCCEEDED` record that names a Linux source and the commit exists. A Windows result never sets a row. The route is PH7-09a or OA-02. An early record on the then-current tip is feedback and never evidence for S, and PH7-17 records every row on S.

| ID | Deferred row | Originating tasks | Criteria and design rows | Release effect |
|---|---|---|---|---|
| DLV-1 | BE-1 Linux leg: full-checkout `-rA` of `tests/contract/test_mcp_server.py` with the direct exit code, and the POSIX negative control (a `0o755` directory fails the original expression) | PH1-04, PH1-10 | 13.11, 13.13, 2.11; D8-AC-4, D3-AC-17 | RB-1 |
| DLV-2 | BE-2 Linux leg: at least 30 instrumented Linux trials, the Linux confirmation of the cause, and 30 of 30 passes with the port allocated at run time | PH1-08, PH1-09, PH1-10 | 13.12, 13.13, 13.26; D8-AC-6, D8-AC-7 | RB-1 |
| DLV-3 | The Linux per-test baseline at `84df25c` (`--collect-only` and `-rA`, direct exit code) and `TEST_INVENTORY.linux.txt` | PH7-09 | 14.22, 13.9; D9-AC-4 | RB-3 |
| DLV-4 | The five cases that skip on Windows (the symlink case and four peer-credential cases) and the other Linux cases that need a full checkout (B-D8-1) | PH7-17 | 14.19, 1.12; D9-AC-2 | RB-13 |

Requirement coverage. The table lists the queued tasks that cite at least one criterion of each requirement. The deferred tasks are not listed, and a requirement with no queued task is marked.

| Requirement | Tasks |
|---|---|
| R1 | PH1-01, PH1-02, PH1-02a, PH1-03, PH1-08, PH1-09, PH1-10, PH1-12a, PH1-18, PH3-12, PH3-14, PH5-07, PH7-09a, PH7-14, PH7-15, PH7-17 |
| R2 | PH1-04, PH1-12a, PH1-13, PH1-14, PH1-15, PH2-03, PH3-02, PH3-10, PH5-02, PH5-07, PH5-09, PH5-10, PH5-11, PH5-14, PH5-15, PH7-03, PH7-04, PH7-05, PH7-06, PH7-07, PH7-17 |
| R3 | PH1-02, PH1-02a, PH1-03, PH1-03a, PH4-04, PH4-06, PH4-07, PH4-08, PH4-09, PH7-08, PH7-14 |
| R4 | PH1-02, PH1-02a, PH1-03a, PH1-18, PH2-10, PH3-14, PH4-10, PH5-17, PH6-12, PH7-07, PH7-08, PH7-15, PH7-17, PH7-18 |
| R5 | PH5-01, PH5-02, PH5-03, PH5-07 |
| R6 | PH5-04, PH5-06, PH5-07 |
| R7 | PH1-11, PH1-12, PH1-15, PH1-16, PH1-17, PH3-04, PH5-01, PH5-06, PH5-08, PH5-09, PH5-10, PH5-11, PH5-12, PH5-13, PH5-14, PH5-15, PH5-16, PH7-04, PH7-05, PH7-12, PH7-16 |
| R8 | PH1-04, PH2-07, PH4-01, PH4-02, PH4-03, PH4-04, PH4-05, PH4-06, PH4-07, PH4-08 |
| R9 | PH1-04a, PH2-01, PH2-02, PH2-03, PH2-04, PH2-05, PH2-06, PH2-07, PH2-08, PH2-09, PH2-10, PH3-11, PH4-09 |
| R10 | PH1-03a, PH1-05, PH3-01, PH3-02, PH3-03, PH3-04, PH3-05, PH3-06, PH3-07, PH3-09, PH3-10, PH3-11, PH3-12, PH3-13, PH5-05, PH7-04, PH7-05 |
| R11 | none (every criterion of this requirement is deferred, and no queued task cites one) |
| R12 | PH3-01, PH3-02, PH3-05, PH3-08, PH3-10, PH6-12 |
| R13 | PH1-04, PH1-04a, PH1-05, PH1-06, PH1-08, PH1-09, PH1-10, PH1-11, PH1-12, PH1-12a, PH1-14, PH1-15, PH1-16, PH1-17, PH1-18, PH2-01, PH2-02, PH2-10, PH3-01, PH3-04, PH3-05, PH3-06, PH3-08, PH3-09, PH3-10, PH3-14, PH4-10, PH5-10, PH5-12, PH5-14, PH5-17, PH6-12, PH7-01, PH7-02, PH7-03, PH7-04, PH7-05, PH7-06, PH7-07, PH7-08, PH7-09, PH7-09a, PH7-11, PH7-18 |
| R14 | PH1-01, PH1-10, PH1-18, PH5-14, PH7-08, PH7-09, PH7-09a, PH7-10, PH7-11, PH7-12, PH7-13, PH7-15, PH7-16, PH7-17, PH7-18 |
| R15 | PH7-14 |
| R16 | PH4-04, PH4-09, PH7-14 |
