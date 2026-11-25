# Requirements Document

## Introduction

This spec governs the next improvement phase of VerdictKit, the claim-autopsy engine in this repository. It is organised as nine prioritised, independently testable tracks P0 to P8: the unified landing page with professional UI/UX (P0), a secure and publicly accessible demonstration deployment (P1), actual agent-hook execution with Windows compatibility (P2), MCP interoperability and diagnostics (P3), signed evidence bundles with explicit signer trust (P4), a reusable claim-plugin SDK (P5), expanded regulatory verification from official sources (P6), threat-model-driven security and property testing (P7), and integration and release verification (P8). Working product behaviour and measurable improvement take priority over documentation volume.

The frozen release is the verified recovery baseline. This phase builds only on branch `feature/kiro-next-phase`. The release tag `v1.0.0-submission`, the `master` branch (both at commit `84df25c`), the tag `verified-quote-e2e-20261118`, and the existing submission artifacts stay unchanged.

The frozen release documentation predates later Kiro integration validation. A separate historical Kiro audit lives outside this checkout (`%USERPROFILE%\Desktop\KIROWEEN\submission-evidence` and `%USERPROFILE%\Desktop\KIROWEEN\KIRO_LOG_EXPORT`). Requirement 15 governs how that evidence is reconciled before any claim from it is recorded as verified. The reconciliation and the Baseline_Run for this phase are recorded in `docs/next-phase/HISTORICAL_EVIDENCE_RECONCILIATION.md`, `docs/next-phase/BASELINE_REPORT.md` and `docs/next-phase/EXECUTION_EVIDENCE.md`.

### Baseline assessment (read-only repository review)

The following facts were read from the repository at commit `84df25c`. Items marked UNVERIFIED were not executed in this assessment.

| Area | Observed state | Source |
|---|---|---|
| Core | Python 3.12 `uv` workspace: `core`, `apps/reel-autopsy`, `apps/quote-autopsy`, `examples`. Modules: `canonical`, `model`, `plugin`, `sweep`, `pipeline`, `bundle`, `envprint`, `cli`, `mcp_server`, packages `custody`, `examiner`, `evidence`, `api`. | `pyproject.toml`, `core/src/verdictkit/` |
| Tests | 39 Python test files under `tests/`; Vitest unit tests in `ui-kit` and both app UIs; a Playwright browser E2E script. Baseline_Run on this phase (Windows host, 2026-11-24): `pytest -m "not isolation"` with `HYPOTHESIS_PROFILE=ci` gave 444 passed, 2 failed, 5 skipped, 4 deselected; the two failures are Windows-host failures (see Baseline_Run findings). UI: 19 Vitest tests passed. | `docs/next-phase/BASELINE_REPORT.md` |
| CI | `p0-integration.yml` (lockfile check, ruff E9/F/B, regression with `-m "not isolation"`, Docker build, isolation gates, `gate_nov22.sh`, web-ui job with browser E2E) and `m3b-api-checks.yml`. | `.github/workflows/` |
| Isolation | Two OS users `vk-custodian` (uid 900) and `vk-examiner` (uid 901) in one Docker image, started through `setpriv` by `deploy/entrypoint.sh`. Gates: `gate-isolation`, `gate-startup`, `gate-http`, `gate-case`. Docker Desktop 29.9.3 (Linux engine, WSL2) is installed on the development host but its `docker.exe` is not on `PATH`. In the Baseline_Run all four gates and an offline replay exited 0 with `--network none`. | `Dockerfile`, `deploy/entrypoint.sh`, `docs/next-phase/BASELINE_REPORT.md` |
| Bundles | Deterministic `.vkb` zip. Integrity, reproducibility and authenticity are reported separately; authenticity is the constant `NOT_ESTABLISHED` ("Bundles are unsigned in v1"). No signing code exists. | `core/src/verdictkit/bundle.py` |
| MCP | `.kiro/settings/mcp.json` registers `verdictkit` (`python -m verdictkit.mcp_server`, `VK_MCP_READONLY=1`, autoApprove `list_claim_types`, `explain_verdict`). Four tools. Application errors are returned as normal results with `isError=false`. Error text for validation failures is the bare class name (`verification failed (SchemaError)`). The server version string is hard-coded as `0.1.0`. The historical audit records Kiro calling all four tools; Requirement 15 governs reconciling that record. Kiro's tool-call path was reported to drop empty arrays and objects from arguments. | `.kiro/settings/mcp.json`, `mcp_server.py`, historical audit |
| Hooks | Three hook files with four hook entries (`PostFileSave`, command actions, path-regex matchers written with forward slashes, timeouts of 60 and 180 seconds). The Kiro log export shows `hooks.reload.loaded {"read":4,"registered":4}` and the event `hooks.v2.executionDisabledUntrustedWorkspace`. No hook execution event was found in the Kiro logs or session transcripts. Execution is therefore UNVERIFIED. | `.kiro/hooks/`, `docs/next-phase/HISTORICAL_EVIDENCE_RECONCILIATION.md` |
| Steering | Six files: `product`, `tech`, `structure`, `verdict-integrity`, `money-math`, `testing`. | `.kiro/steering/` |
| UI | `ui-kit` (React 18, shared theme `theme.css`, components, contract-checked API client), two Vite apps (`apps/quote-autopsy/web`, `apps/reel-autopsy/web`), and a static read-only judge preview (`ui/judge`). There is no landing page that unifies the two apps. A limited number of ARIA attributes exist (3 in `ui-kit/src/components.tsx`, 9 across both `App.tsx` files). No accessibility audit has been recorded. | `ui-kit/`, `apps/*/web/`, `ui/judge/` |
| HTTP API | FastAPI, contract 1.1.0 (`api/openapi.yaml`). Observed response headers: `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`. In-process rate limiter, 256 KiB JSON cap, 8 MiB bundle cap, 24 h TTL. No `Content-Security-Policy` header was found. | `core/src/verdictkit/api/server.py` |
| Plugin system | `ClaimType` Protocol, `Registry`, entry-point group `verdictkit.claim_types`, `VK_CLAIM_TYPES` environment loading, and a third-domain stub (`examples/stub_claimtype`) with a golden bundle. No scaffolding command exists. | `plugin.py`, `examples/` |
| Regulatory | Texas only (decision B7). Four official Texas sources are hashed in `rules/TX.json` and `MANIFEST.json`. The text of 7 TAC §84.205 was not retrieved. Other states return `INDETERMINATE(unsupported_jurisdiction)`. A first attempt to fetch statutes produced identical hashes because each URL served a JavaScript shell (see `docs/KIRO_USAGE.md`). | `apps/quote-autopsy/src/quote_autopsy/rules/`, `docs/RELEASE_READINESS.md` |
| Reel data | Only labelled synthetic OHLCV. Live data is blocked pending a documented rights basis (decision B1, task 5.0 open). | `.kiro/specs/reel-autopsy/tasks.md` |
| Kiro evidence | The frozen docs record one Kiro session. The historical export records six sessions with transcripts, four `spec-task-execution` sub-agent runs, 417 unique tool calls, 318 request identifiers and 92.9518 credits, plus 23 MCP calls to the four VerdictKit tools. These figures were recomputed read-only in this phase (Requirement 15). | `docs/KIRO_USAGE.md`, historical export |

### Track register: dependencies, implementation risks and rollback

Requirement 4 makes this register a controlled deliverable. Each track's acceptance criteria are the numbered criteria of the requirements named in the table. Tracks were originally numbered T1 to T10; the mapping is T1 and T2 to P0, T3 to P1, T4 to P2, T5 to P3, T6 to P4, T7 to P5, T8 to P6, T9 to P7, T10 to P8.

| Track | Requirements | Depends on | Principal implementation risks | Rollback procedure |
|---|---|---|---|---|
| P0 Landing page and professional UI/UX | 5, 6 | Baseline (R1), ui-kit, API contract 1.1.0 | Visual change hides labels such as `SYNTHETIC_DEMO` or `ILLUSTRATIVE`; copy overstates capability; browser E2E breaks. | Revert the UI commits on the Phase_Branch; the baseline UI is on `master`. Remove the landing route; app roots are unchanged. |
| P1 Secure public demonstration deployment | 7 | P0, a Linux Docker host, baseline gates | Isolation not enforced on the hosting target; new headers break the UIs; no host available for verification. | Redeploy the previous image digest; disable the deployment workflow; documentation states that no hosted demonstration is available. |
| P2 Actual hook execution and Windows compatibility | 8 | Kiro IDE session (owner-run), trusted workspace | Hooks fire only on agent saves; workspace trust disables execution; Windows backslash paths; the core hook command fails on Windows because of one POSIX mode assertion. | Restore `.kiro/hooks/*.json` from `84df25c`. |
| P3 MCP interoperability and diagnostics | 9 | Existing tool contracts, `mcp` SDK | Tool schema changes break clients; diagnostics leak paths or exception text; changing error signalling breaks contract tests. | Revert `mcp_server.py` and `.kiro/settings/mcp.json`; keep the four tool names and result fields. |
| P4 Signed bundles and signer trust | 10 | `cryptography` (already a core dependency), bundle format, API contract | Signature changes bundle bytes or `verdict_hash`; key handling mistakes; trust confused with validity. | Signing is opt-in; unsigned output is byte-identical to baseline; disable the signing option and remove the signature member. |
| P5 Claim-plugin SDK | 11 | `plugin.py`, stub example, contract tests | Scaffold template drifts from the protocol; templates encourage floats. | Delete the SDK package and scaffolding command; core modules were not edited. |
| P6 Expanded regulatory verification | 12 | Network access to official sites, B7 loader | Official page is a script shell; rule text changes; wrong rule asserted as fact. | Remove the added snapshot and its manifest entry; the jurisdiction returns to `unsupported_jurisdiction`. |
| P7 Threat model and property testing | 13 | P3, P4, P5, P6 designs, `tests/contract` | Tests weakened to pass; non-deterministic tests. | Revert the new test files; no production code depends on them. |
| P8 Integration and release verification | 14 | P0 to P7, CI, Linux Docker host | Gates skipped; counts taken from memory; evidence claimed without a run. | Do not tag a release; keep results as UNVERIFIED records. |

Cross-cutting requirements 1 to 4, 15 and 16 apply to every track.

### Requirement numbering and review history

The first draft contained Requirements 1 to 14. Requirements 1 to 14 keep their numbers. Requirement 15 (historical evidence reconciliation) and Requirement 16 (Kiro credit and usage tracking) were added after the historical Kiro audit, so the document now has 16 requirements. Track labels changed from T1 to T10 to P0 to P8, and the mapping is in the track register, so every earlier reference stays traceable. After the independent review, the following were amended without renumbering: Requirements 1, 2, 6, 7, 8, 9, 10, 11, 12, 13 and 14. Each amendment appends criteria at the end of its requirement, except the in-place changes to criteria 1.2, 1.7, 1.12, 2.11, 14.10 and 14.14.

### Accepted baseline exceptions

Two documented Windows baseline failures are accepted for baseline continuation only: BE-1 (`test_verify_replay_and_explain_roundtrip`, POSIX mode `0o700` assertion) and BE-2 (`test_case_outcome_get_to_offline_backend`, timeout, root cause not established). Both must be remediated before the final next-phase release. No other failure is permitted.

## Glossary

- **VerdictKit_System**: The complete repository at the phase baseline, comprising the core, both apps, UIs, API, MCP server, CLI, deployment assets and `.kiro` configuration.
- **Core**: The Python package `verdictkit` under `core/src/verdictkit/`.
- **Quote_App**: Quote Autopsy, `apps/quote-autopsy`, with its web UI `apps/quote-autopsy/web`.
- **Reel_App**: Reel Autopsy, `apps/reel-autopsy`, with its web UI `apps/reel-autopsy/web`.
- **UI_Kit**: The shared React component library and theme in `ui-kit/`.
- **Landing_Page**: The new unified entry page that links to Quote_App and Reel_App.
- **Onboarding_Flow**: The guided sequence that introduces the claim lifecycle using labelled examples.
- **API_Server**: The FastAPI service in `core/src/verdictkit/api/`, contract version 1.1.0.
- **MCP_Server**: The stdio server `verdictkit.mcp_server` exposing `list_claim_types`, `verify_claim`, `replay_bundle` and `explain_verdict`.
- **Hook_Set**: The JSON hook files in `.kiro/hooks/`.
- **Frozen_Release**: The three git refs `v1.0.0-submission` (annotated tag, object `e9ca8d2bac4a65483f3a7357e00600a1210a6f4f`, peeled commit `84df25c68198e496889b5892a03555ec7d2d860a`), `master` (commit `84df25c68198e496889b5892a03555ec7d2d860a`) and `verified-quote-e2e-20261118` (lightweight tag, commit `407478be97a8979a8e3555bba3b3ab302229f91d`, an ancestor of `84df25c`). Each ref is protected against its own recorded value.
- **Baseline_Exception**: A Baseline_Run failure that the maintainer has accepted, by its identifier, for baseline continuation only. The accepted exceptions are BE-1 and BE-2. A Baseline_Exception does not permit a release.
- **Execution_Error**: A recorded execution that produced no command result because of a runner fault (log-file lock collision or wrong invocation). It is not a test failure and not an Outcome_Class.
- **Execution_Index**: `docs/next-phase/baseline/EXECUTION_INDEX.md`, which maps every raw record to a canonical execution, a superseded duplicate or an Execution_Error.
- **Submission_Artifacts**: `docs/SUBMISSION_DRAFT.md`, `docs/SUBMISSION_READINESS.md`, `docs/JUDGE_DEMO.md`, `docs/RELEASE_READINESS.md`, `docs/KIRO_USAGE.md`, and any other file tracked at the Frozen_Release that describes the submission.
- **Phase_Branch**: The git branch `feature/kiro-next-phase`.
- **Baseline_Run**: The first complete execution of all regression gates on the Phase_Branch before any implementation change, recorded in the Evidence_Ledger.
- **Evidence_Ledger**: The file `docs/next-phase/EXECUTION_EVIDENCE.md`, which records every execution result of this phase.
- **Execution_Record**: One Evidence_Ledger entry containing command, working directory, commit SHA, UTC timestamp, host operating system, exit code, and outcome class.
- **Outcome_Class**: One of `SUCCEEDED`, `FAILED` or `UNVERIFIED`. `SUCCEEDED` requires a recorded exit code of 0 from a run in this phase. `FAILED` requires a recorded run with a non-zero exit code. `UNVERIFIED` applies to any capability that was not run.
- **Isolation_Mode**: `ENFORCED` (two OS users, authenticated socket, encrypted vault, Linux container) or `UNENFORCED`.
- **Bundle**: A `.vkb` zip verdict bundle written by `write_bundle`.
- **Verdict_Hash**: The hash defined in core requirement 6.4. It excludes timestamps, salts, ledger entries and diagnostics.
- **Bundle_Signature**: A detached digital signature over the Bundle manifest, stored in a separate Bundle member.
- **Signer_Identity**: The public key, and its fingerprint, that verifies a Bundle_Signature.
- **Trust_Store**: A local, operator-supplied list of Signer_Identity fingerprints that the verifier accepts.
- **Signature_Validity**: Whether a Bundle_Signature verifies mathematically against the signed bytes.
- **Signer_Trust**: Whether the Signer_Identity is present in the Trust_Store. It is evaluated separately from Signature_Validity.
- **Claim_Plugin_SDK**: The documented package, conformance suite and scaffolding command used to create new claim types.
- **Conformance_Suite**: A reusable set of automated checks that every claim type must pass (blinding, Decimal-only, canonical inputs, LLM fence, determinism).
- **Official_Source**: A document published by a government or statutory regulator for the stated jurisdiction, retrieved from the regulator's own domain.
- **Source_Snapshot**: A retrieved Official_Source with URI, retrieval date, SHA-256 of the exact bytes, and a verified excerpt of the relied-upon text.
- **Threat_Model**: The document `docs/next-phase/THREAT_MODEL.md` listing assets, trust boundaries, threats, controls and the test that exercises each control.
- **Fail_Closed**: An error or missing input may produce `INDETERMINATE` or a rejection, and never `SUPPORTED`, `CONSISTENT` or `WITHIN_BOUND`.
- **Answer_Blind**: The Examiner never receives claimed outcomes.
- **WCAG_2_2_AA**: Web Content Accessibility Guidelines 2.2, conformance level AA.
- **Release_Candidate**: The Phase_Branch commit selected for final verification in Requirement 14.
- **Linux_Docker_Host**: A host whose Docker Engine reports `Server.Os` equal to `linux`, including Docker Desktop with WSL2. The executable need not be on `PATH`.
- **Historical_Audit**: The pre-phase Kiro audit held outside this checkout in `%USERPROFILE%\Desktop\KIROWEEN\submission-evidence` and `%USERPROFILE%\Desktop\KIROWEEN\KIRO_LOG_EXPORT`.
- **Pre_Existing_Defect**: A Baseline_Run failure that exists at commit `84df25c` on the stated host, has been diagnosed or reproduced, and is documented with its host attribution. A Pre_Existing_Defect becomes a Baseline_Exception only when the maintainer accepts it by identifier.
- **Reconciliation_Record**: An entry in `docs/next-phase/HISTORICAL_EVIDENCE_RECONCILIATION.md` that compares one Historical_Audit claim with the recomputed value and assigns a status of `CONFIRMED`, `CONFIRMED_WITH_CORRECTION`, `CONTRADICTED` or `UNVERIFIED`.
- **Credit_Record**: A Kiro credit figure that is read from a Kiro usage record, with its source and date.

## Requirements

### Requirement 1: Verified baseline and Frozen_Release protection

**User Story:** As the maintainer, I want a recorded passing baseline and a protected frozen release, so that every later change can be compared with a known-good state and the recovery point cannot be damaged.

#### Acceptance Criteria

1. THE VerdictKit_System SHALL create and modify commits only on the Phase_Branch.
2. THE VerdictKit_System SHALL keep each Frozen_Release ref and every Submission_Artifacts file unchanged against its own recorded value: tag `v1.0.0-submission` with tag object `e9ca8d2bac4a65483f3a7357e00600a1210a6f4f` and peeled commit `84df25c68198e496889b5892a03555ec7d2d860a`; branch `master` at `84df25c68198e496889b5892a03555ec7d2d860a`; tag `verified-quote-e2e-20261118` at `407478be97a8979a8e3555bba3b3ab302229f91d`; and each Submission_Artifacts file byte-identical to its content at `84df25c68198e496889b5892a03555ec7d2d860a`. For an annotated tag the VerdictKit_System SHALL record both the tag object SHA and the peeled commit SHA.
3. IF an operation would push, merge, force-update, delete or re-point a Frozen_Release ref, THEN THE VerdictKit_System SHALL refuse the operation, leave the ref unchanged, and record the refusal in the Evidence_Ledger with the refused operation and the ref name.
4. WHEN implementation work is about to begin, THE VerdictKit_System SHALL complete a Baseline_Run that executes each of the following steps once and records an Outcome_Class for each: Python lockfile check, `ruff check .`, `pytest -m "not isolation"` with `HYPOTHESIS_PROFILE=ci`, the three Hook_Set commands, the UI typecheck, the UI unit tests, the UI build, and the browser E2E script.
5. WHERE the host is a Linux_Docker_Host, THE VerdictKit_System SHALL run the container gates `gate-isolation`, `gate-startup`, `gate-http` and `gate-case` as part of the Baseline_Run, and SHALL NOT run them on any other host.
6. IF the host is not a Linux_Docker_Host, THEN THE VerdictKit_System SHALL record each of the four container gates as `UNVERIFIED` in the Evidence_Ledger, with a reason stating why the host cannot run it.
7. IF any Baseline_Run step has Outcome_Class `FAILED`, THEN THE VerdictKit_System SHALL record the step name and its captured output in the Evidence_Ledger, and SHALL NOT begin implementation until that failure is either resolved (the step re-run with a non-`FAILED` Outcome_Class) or recorded as a Baseline_Exception that the maintainer has accepted by identifier. The only Baseline_Exceptions are BE-1 and BE-2.
8. THE VerdictKit_System SHALL write every phase document that describes new results into a new file under `docs/next-phase/`, and SHALL leave every Submission_Artifacts file unmodified.
9. WHEN the Baseline_Run begins, THE VerdictKit_System SHALL record the current branch, the commit identifier, the commit that each Frozen_Release ref resolves to, and the `git status` output, and SHALL confirm that the only working-tree changes are new files for this phase's specification and `docs/next-phase/`.
10. THE VerdictKit_System SHALL record for every Baseline_Run step the exact command, the exit code, the duration in seconds, the start timestamp in UTC, the passed, failed, skipped and deselected counts, and the name of every failed and skipped test with its reason.
11. IF a Baseline_Run step fails, THEN THE VerdictKit_System SHALL report the failure, its diagnosed cause, and its host attribution before any application code is changed, and SHALL NOT modify application code to resolve the failure until that report exists.
12. WHERE a Baseline_Run failure is attributable to the host operating system, THE VerdictKit_System SHALL record it as a Baseline_Exception with the evidence for the attribution, and SHALL classify the same check as `UNVERIFIED` for the other host class until it is run there with a per-test listing and a captured pytest exit code.
13. IF a test that is not BE-1 or BE-2 fails on any host after the Baseline_Run, THEN THE VerdictKit_System SHALL treat the failure as a new regression, SHALL record it as `FAILED`, and SHALL NOT accept it as a Baseline_Exception without a new maintainer decision recorded by identifier.
14. THE VerdictKit_System SHALL maintain the Execution_Index, SHALL preserve every raw record file and log byte for byte with their SHA-256 values, and SHALL take every reported test count only from a canonical execution in the Execution_Index.
15. THE VerdictKit_System SHALL classify a duplicate or lock-collision execution record as an Execution_Error or superseded duplicate, SHALL NOT count it as a test failure, and SHALL NOT infer a test result from the exit code of a pipeline command such as `tail`.
16. WHEN a Linux per-test result is reported from a combined run, THE VerdictKit_System SHALL state that the evidence is indirect unless the run captured the pytest exit code and a per-test listing.
17. THE VerdictKit_System SHALL make every network port used by a local test, server or browser E2E run configurable through an environment variable or command-line option with a documented default, and SHALL NOT stop, kill or reconfigure a process it did not start, including the process listening on port 8000 on the development host.
18. THE VerdictKit_System SHALL remediate BE-1 and BE-2 before the final next-phase release, as specified in Requirement 13.

### Requirement 2: Preserved system invariants

**User Story:** As a reviewer, I want the core guarantees stated as testable requirements for this phase, so that no improvement weakens what the first release promised.

#### Acceptance Criteria

1. THE VerdictKit_System SHALL compute all monetary, rate and metric values with `Decimal` inside an explicit local context, and SHALL contain no `float` type annotation, `float` literal or `float()` call in the modules that implement claims, evidence parsing, evaluators, comparators or findings.
2. WHEN the VerdictKit_System is run twice on identical frozen claims, identical evidence bytes and an identical injected clock, THE VerdictKit_System SHALL produce findings that are byte-identical across the two runs and an identical Verdict_Hash.
3. THE VerdictKit_System SHALL keep Examiner inputs free of claimed outcomes, so that two claims differing only in outcome values produce byte-identical `BlindedTask` serializations.
4. IF a security control, policy check, evidence check or startup gate encounters an error or a missing input, THEN THE VerdictKit_System SHALL apply Fail_Closed behaviour by denying the guarded action, reporting an error indication to the caller, and leaving prior state unchanged.
5. WHILE `VK_JUDGE_MODE=1`, THE VerdictKit_System SHALL start only when Isolation_Mode is `ENFORCED`.
6. IF `VK_JUDGE_MODE=1` and Isolation_Mode is not `ENFORCED` at startup, THEN THE VerdictKit_System SHALL refuse to start and SHALL exit with the existing code and marker defined in core requirement 4.7.
7. WHERE Isolation_Mode is `ENFORCED`, THE VerdictKit_System SHALL run inside a Linux container with distinct `vk-custodian` and `vk-examiner` OS users, an authenticated examiner socket, and an encrypted vault whose directory mode is 0700.
8. WHEN the VerdictKit_System replays a Bundle, THE VerdictKit_System SHALL make zero outbound network connections unless `--allow-refetch` is given.
9. THE VerdictKit_System SHALL contain no import of an LLM client library in `verdictkit.custody`, `verdictkit.examiner`, `verdictkit.evidence`, `verdictkit.sweep` or any app evaluator module.
10. IF an assumption grid exceeds the configured cap, THEN THE VerdictKit_System SHALL reject the whole grid with an error indication naming the cap and the observed size, SHALL evaluate zero grid points, and SHALL NOT subsample the grid.
11. THE VerdictKit_System SHALL pass every test in the existing `tests/contract/` suite with zero failures on a Linux_Docker_Host, and on a Windows host with zero failures other than BE-1 until BE-1 is remediated. No contract test SHALL be modified to loosen an assertion, marked `xfail`, or marked `skip`.
12. WHEN new code changes any file covered by `.kiro/steering/verdict-integrity.md`, THE VerdictKit_System SHALL pass the LLM-fence test `tests/contract/test_llm_fence.py` with zero failures.

### Requirement 3: Honest execution evidence

**User Story:** As a reviewer, I want every claim of success backed by a recorded run, so that successful, unsuccessful and unverified capabilities are never confused.

#### Acceptance Criteria

1. THE Evidence_Ledger SHALL contain exactly one Execution_Record for each command whose result is reported as a result of this phase, and SHALL contain no Execution_Record for a command that was not run.
2. WHEN a command finishes running, THE VerdictKit_System SHALL record in its Execution_Record the command text, the actual exit code, the start timestamp and the actual passed, failed and skipped test counts printed by the test runner, within 5 seconds of the command finishing.
3. IF a command finishes without a test runner printing test counts, THEN THE VerdictKit_System SHALL record the test counts as absent in its Execution_Record and SHALL NOT enter any numeric count.
4. IF a capability was not executed in this phase, THEN THE Evidence_Ledger SHALL label it `UNVERIFIED` and SHALL NOT describe it as working.
5. IF a command exits with a non-zero exit code or is terminated before finishing, THEN THE Evidence_Ledger SHALL record the Outcome_Class `FAILED` together with the failing output, and the record SHALL remain unchanged and present after any later successful rerun, which is recorded as a separate Execution_Record.
6. WHEN a Kiro hook fires, an MCP tool is called or a sub-agent runs, THE VerdictKit_System SHALL attribute the event in the Evidence_Ledger only to an output captured inside the Kiro environment, and the Execution_Record SHALL reference that captured output.
7. IF no output was captured inside Kiro for a hook, an MCP call or a sub-agent run, THEN THE Evidence_Ledger SHALL label that capability `UNVERIFIED`.
8. THE VerdictKit_System SHALL NOT fabricate, reconstruct or back-date any log, screenshot, session export, test count, timestamp, external data value or Source_Snapshot.
9. WHEN a document, UI text or README states a capability, THE VerdictKit_System SHALL state it only if the Evidence_Ledger holds an Execution_Record with Outcome_Class `SUCCEEDED` for the current Release_Candidate that supports it.
10. IF a document, UI text or README states a capability that has no supporting `SUCCEEDED` Execution_Record for the current Release_Candidate, THEN THE VerdictKit_System SHALL report each such statement as a violation, identifying the file and the line containing it.

### Requirement 4: Track planning and use of Kiro features

**User Story:** As the maintainer, I want each track to carry its dependencies, acceptance criteria, risks and rollback plan, so that the phase can be executed and unwound in a controlled way.

#### Acceptance Criteria

1. THE VerdictKit_System SHALL maintain the Track register in this document, with one entry for each of the nine tracks P0 to P8, and each entry SHALL list at least one dependency (or the explicit value "none"), exactly one governing requirement, at least one implementation risk, and a rollback procedure for each listed risk.
2. WHEN `design.md` is written, THE VerdictKit_System SHALL map every design component to at least one requirement of this document, and SHALL list any design component with no mapped requirement as an unmapped component for the maintainer to resolve before `design.md` is accepted.
3. WHEN `tasks.md` is written, THE VerdictKit_System SHALL trace every task to at least one acceptance criterion of this document, and SHALL list any task with no traced criterion as an untraced task for the maintainer to resolve before `tasks.md` is accepted.
4. WHEN a track completes, THE VerdictKit_System SHALL add one Execution_Record for that track that shows each acceptance criterion of that track's governing requirement with exactly one status from `SUCCEEDED`, `FAILED` or `UNVERIFIED`, and SHALL mark a criterion `UNVERIFIED` where no evidence of its verification exists in the Evidence_Ledger.
5. IF a track's listed implementation risk occurs, THEN THE VerdictKit_System SHALL execute the rollback procedure listed for that risk in the Track register and SHALL record in the Evidence_Ledger the track identifier, the risk that occurred, the rollback action taken and its outcome (completed or failed).
6. IF a rollback procedure does not complete, THEN THE VerdictKit_System SHALL mark the track as incomplete in its Execution_Record, SHALL record the failure in the Evidence_Ledger, and SHALL leave the prior Execution_Record entries and Evidence_Ledger entries unmodified.
7. WHERE a Kiro feature (specs, steering, task execution, sub-agents, MCP tools, or hooks) fits the work of a track, THE VerdictKit_System SHALL use that feature and SHALL record in the Evidence_Ledger, for each feature used, one of the values `observed running inside Kiro` or `not observed running inside Kiro`.
8. WHEN new durable rules are needed for this phase, THE VerdictKit_System SHALL add them as new steering files and SHALL NOT remove or weaken any existing steering rule, where a rule is weakened if its text is changed so that any behavior it previously prohibited or required becomes permitted or optional.
9. WHEN an Execution_Record is added or changed, THE VerdictKit_System SHALL update the corresponding `tasks.md` checkboxes in the same change so that a checkbox is checked only if the Execution_Record for its task shows every linked acceptance criterion as `SUCCEEDED`, and is unchecked otherwise.

### Requirement 5: Professional UI/UX modernization (P0)

**User Story:** As a user of Quote Autopsy or Reel Autopsy, I want a clear, consistent and professional interface, so that I can submit a claim and understand its verdict without confusion.

#### Acceptance Criteria

1. THE UI_Kit SHALL provide one design-token set (colour, type scale, spacing, focus style) used by both Quote_App and Reel_App, and neither app SHALL define its own colour, type-scale, spacing or focus-style values outside that set.
2. WHEN a verdict is displayed, THE UI_Kit SHALL show the headline status, every finding with its basis and status, the confidence scope sentence, and the Isolation_Mode, with all of these visible on the verdict view without requiring the user to expand, hover or navigate to another view.
3. WHERE a case has data mode `SYNTHETIC_DEMO` or an `ILLUSTRATIVE` key record, THE UI_Kit SHALL display a text label naming that state (`SYNTHETIC_DEMO` or `ILLUSTRATIVE`) adjacent to the affected content, in the same container as the content it qualifies.
4. THE UI_Kit SHALL convey every status through a visible text label, so that the status remains identifiable when the page is rendered in greyscale.
5. WHEN swept-assumption results are displayed, THE UI_Kit SHALL present them with the wording "verified at N grid points", where N is the integer grid-point count supplied by the API_Server, and SHALL NOT use wording that claims a result holds for all values, every value, or any value.
6. THE UI_Kit SHALL render every monetary and rate value as the exact Decimal string supplied by the API_Server, without converting it to a binary floating-point number, so that the displayed digits equal the supplied digits (no digits added, dropped or rounded).
7. WHEN the viewport width is between 320 and 1920 CSS pixels inclusive, THE Quote_App and THE Reel_App SHALL present all content and controls without horizontal scrolling of the page, so that the document scroll width does not exceed the viewport width.
8. IF the API_Server returns an error response or an `INDETERMINATE` or `BLOCKED` execution status, THEN THE UI_Kit SHALL display the error code, a reason, and the next step available to the user, and SHALL retain the user's submitted input in the form.
9. WHEN the modernization is complete, THE Quote_App and THE Reel_App SHALL each exit with status 0 on `npm run typecheck`, `npm test` and `npm run build`, and SHALL pass 100% of the baseline browser E2E checks with no check removed or skipped.
10. THE UI_Kit SHALL keep each modernized component covered by at least one unit test that asserts the component's label text and status text, and that test SHALL fail if either text is removed.

### Requirement 6: Unified landing page and guided onboarding (P0)

**User Story:** As a first-time visitor, I want a single entry point that explains what VerdictKit does and walks me through a verification, so that I can reach the correct app and understand the result.

#### Acceptance Criteria

1. THE Landing_Page SHALL present VerdictKit's purpose in a text block of 1 to 100 words, and SHALL provide exactly one link to Quote_App and exactly one link to Reel_App, each of which navigates to the respective app's entry page.
2. THE Landing_Page SHALL state the release boundaries in visible text without requiring user interaction: Reel data is synthetic, external regulatory checks cover only the jurisdictions with a verified Source_Snapshot, and bundle authenticity is stated according to Requirement 10.
3. WHEN a visitor starts the Onboarding_Flow, THE Onboarding_Flow SHALL present exactly five lifecycle steps in this order: freeze the claim, seal the outcome, examine blind, reveal and compare, download and replay.
4. THE Onboarding_Flow SHALL use only examples that the engine computes or that are labelled as constructed worksheets or `SYNTHETIC_DEMO`, and SHALL display the applicable label next to each example.
5. WHEN a visitor completes an onboarding example, THE Onboarding_Flow SHALL display the verdict returned by the API_Server and SHALL NOT display a precomputed substitute.
6. THE Landing_Page SHALL display no statistic, customer count, accuracy figure or testimonial.
7. THE Landing_Page and Onboarding_Flow SHALL meet the accessibility criteria of Requirement 7.
8. IF the API_Server is unreachable, THEN THE Landing_Page SHALL display a visible message indicating the API_Server is unreachable within 10 seconds of the first failed request, SHALL keep the static explanatory content and the Quote_App and Reel_App links available, and SHALL NOT display any verdict.
9. IF the API_Server becomes unreachable or returns an error while a visitor is in an onboarding example, THEN THE Onboarding_Flow SHALL display an error message indicating the verdict could not be retrieved, SHALL retain the visitor's entered inputs, SHALL NOT display a verdict, and SHALL allow the visitor to retry.
10. THE Landing_Page SHALL be built, typechecked and tested by the same `npm` workspace commands as the existing UIs.
11. THE Landing_Page SHALL carry the title "VerdictKit — Evidence Verification Workspace" and SHALL keep the names "Quote Autopsy" and "Reel Autopsy" for the two apps.

### Requirement 7: Accessible and secure demonstration deployment (P1)

**User Story:** As a judge or evaluator, I want a demonstration I can reach and use with assistive technology, which is deployed with the same isolation guarantees as the tests, so that I can trust what I see.

#### Acceptance Criteria

1. THE Landing_Page, Quote_App and Reel_App SHALL conform to every WCAG_2_2_AA success criterion that applies to keyboard operation, visible focus, text contrast (minimum 4.5:1 for normal text and 3:1 for large text), form labels, error identification, page language (a valid `lang` value on each page), and status messages, with 0 unresolved violations of those criteria.
2. WHEN an automated accessibility scan is run against each page and the Onboarding_Flow, THE VerdictKit_System SHALL record the tool name, the tool version, the scanned URL or step, the scan timestamp, and the count and identifiers of findings (including a count of 0) in the Evidence_Ledger.
3. IF an automated accessibility scan fails to complete for a page or for the Onboarding_Flow, THEN THE VerdictKit_System SHALL record the failure in the Evidence_Ledger and SHALL label that page or flow `UNVERIFIED`.
4. WHERE a criterion of WCAG_2_2_AA cannot be checked automatically, THE VerdictKit_System SHALL either record a manual keyboard-only check and a manual screen-reader check in the Evidence_Ledger, each with the tester, date, assistive technology name and version, and pass/fail result, or label the criterion `UNVERIFIED`.
5. THE deployed API_Server SHALL send the `Content-Security-Policy`, `X-Content-Type-Options` (value `nosniff`), `Referrer-Policy` and `Cache-Control` headers on every response, including error responses, with a Content-Security-Policy whose source lists contain only the origins that the Landing_Page, Quote_App and Reel_App load resources from and no wildcard (`*`) source.
6. WHERE the deployment terminates TLS, THE deployed service SHALL send `Strict-Transport-Security` with a `max-age` of at least 15552000 seconds (180 days) on every HTTPS response.
7. WHILE the deployed service runs in judge mode, THE deployed service SHALL have Isolation_Mode `ENFORCED` and SHALL print the line `VK_STARTUP_OK isolation=ENFORCED` exactly once at startup, before accepting its first request.
8. IF the deployment target cannot provide Isolation_Mode `ENFORCED`, THEN THE deployment SHALL refuse to start in judge mode, SHALL exit with a non-zero status, SHALL NOT print `VK_STARTUP_OK`, and SHALL write a message to standard error stating that isolation is unavailable.
9. THE deployment SHALL supply `VK_VAULT_KEY` from the deployment secret store, and SHALL keep its value out of the repository, container images, logs and the Examiner environment, such that a search of those four locations for the value finds 0 matches.
10. IF `VK_VAULT_KEY` is absent or empty at startup, THEN THE deployment SHALL refuse to start, SHALL exit with a non-zero status, and SHALL write a message to standard error stating that the key is missing without printing any key value.
11. THE deployment SHALL enforce the same request caps as the test environment: 256 KiB for JSON requests and 8 MiB for bundles, with requests above the cap rejected before processing and without partial storage. It SHALL also keep the same per-client rate limit and the same 24 hour case expiry.
12. THE deployment SHALL pin the container base image by sha256 digest and SHALL be built from the committed `uv.lock` with `--frozen`, so that the build fails if `uv.lock` does not match the project dependencies.
13. WHEN the deployment is reported as available, THE VerdictKit_System SHALL record an Execution_Record that shows the public URL answering `GET /api/v1/health` within 10 seconds with a success response that contains the commit SHA of the deployed image, and that SHA SHALL equal the commit SHA of the release being reported.
14. IF no deployment has been verified by an Execution_Record under criterion 13, THEN THE documentation SHALL state that no hosted demonstration is available and SHALL NOT present any public URL as a live demonstration.
15. THE deployment SHALL ship a documented rollback procedure that redeploys the previous image digest, and the documentation SHALL name how that digest is identified and how the rollback is confirmed through `GET /api/v1/health` returning the previous commit SHA.
16. THE deployment SHALL be defined as a portable Docker image that runs unchanged on any Linux_Docker_Host, and SHALL NOT depend on a single provider's proprietary service for its isolation guarantees.
17. THE VerdictKit_System SHALL evaluate AWS ECS Fargate as one candidate hosting target against recorded criteria (cost estimate, security posture, and whether it can provide Isolation_Mode `ENFORCED` with distinct OS users, an authenticated socket and the same entrypoint), and SHALL record the evaluation as a design decision without provisioning any infrastructure or incurring any charge.
18. IF a candidate hosting target cannot provide Isolation_Mode `ENFORCED`, THEN THE VerdictKit_System SHALL reject that target for judge mode, and SHALL NOT downgrade, bypass or disable any isolation control to make a deployment work.
### Requirement 8: Verified agent-hook execution (P2)

**User Story:** As the maintainer, I want to know which hooks actually run in Kiro, so that guardrails are real and are not assumed.

#### Acceptance Criteria

1. WHEN a Kiro agent saves a file whose path matches a Hook_Set matcher, THE Hook_Set SHALL run its configured command once for that save.
2. WHEN a hook fires inside Kiro, THE Evidence_Ledger SHALL record one entry containing the hook name, the saved file path, the command output (truncated to at most 10,000 characters if longer), the exit code and the date in ISO 8601 format, all captured from Kiro.
3. THE Hook_Set SHALL define matchers that match file paths written with `/` separators and file paths written with `\` separators.
4. WHEN a matcher is changed, THE VerdictKit_System SHALL include an automated test that checks the matcher against at least 2 example paths per separator style that must match and at least 2 paths that must not match, and the test SHALL fail if any path is classified incorrectly.
5. THE Hook_Set SHALL set each hook's timeout to at least the longest duration of its command recorded in the Baseline_Run, in seconds.
6. IF a hook command exits with a non-zero code, THEN THE Hook_Set SHALL show the command's standard output, standard error and exit code in the agent session, and SHALL leave the saved file unchanged.
7. WHERE a hook has no Evidence_Ledger entry showing it fired inside Kiro, THE documentation SHALL label that hook `UNVERIFIED`. THE documentation SHALL also state that Kiro hooks run on agent file operations and are a development guardrail, and that runtime guarantees are enforced by code and CI.
8. WHEN a new hook is added, THE Hook_Set SHALL configure it to run only read-only verification commands. THE Hook_Set SHALL NOT configure any command that deletes, moves, renames or publishes files, makes network requests, or runs `git push`.
9. WHEN a `.kiro/hooks/*.json` file is saved, THE Hook_Set SHALL run the Hook_Set matcher test.
10. IF a hook command runs longer than its configured timeout, THEN THE Hook_Set SHALL stop the command and show a timeout indication, the hook name and the timeout value in the agent session.
11. WHEN hook execution is attempted, THE VerdictKit_System SHALL record whether Kiro reported the workspace as trusted, and IF Kiro reports `hooks.v2.executionDisabledUntrustedWorkspace` THEN THE Evidence_Ledger SHALL record the hook execution as `UNVERIFIED` with that reason and SHALL NOT report the hook as failed or as passing.
12. THE Hook_Set SHALL run correctly on a Windows host, so that each hook command is a form that PowerShell and `cmd` both execute without a POSIX-only construct.
13. WHEN a hook command is run on Windows and its tests fail only on a POSIX file-mode assertion (Baseline_Exception BE-1, `test_verify_replay_and_explain_roundtrip`), THE Hook_Set SHALL report the failure unchanged and SHALL NOT suppress, skip or loosen the test.
14. THE Hook_Set SHALL provide a marker hook whose command writes a visible line, so that a Kiro hook firing is distinguishable from the output of the tests it triggers.
15. THE VerdictKit_System SHALL record hook-execution evidence only from a Kiro session whose log or transcript shows the hook firing, and SHALL record which workspace (the repository or a separate clone) the session used.
16. THE VerdictKit_System SHALL verify hook execution in a separate disposable checkout that the maintainer opens as a trusted workspace, and SHALL NOT mark the main repository workspace as trusted for this purpose.
17. BEFORE any hook is run in the disposable checkout, THE VerdictKit_System SHALL review every configured hook command and record the review, and SHALL run only commands that are read-only verification commands.
18. THE disposable checkout SHALL contain no production credential, signing key, `VK_VAULT_KEY` value or deployment secret, and SHALL grant the Kiro session no permission beyond reading the checkout and running the reviewed commands.

### Requirement 9: MCP interoperability and diagnostics (P3)

**User Story:** As a Kiro or other MCP client user, I want the VerdictKit tools to be discoverable, callable and diagnosable, so that an agent can verify and replay claims reliably.

#### Acceptance Criteria

1. THE MCP_Server SHALL keep the tool names `list_claim_types`, `verify_claim`, `replay_bundle` and `explain_verdict`, with their existing argument names and success result fields, so that a client test written against the pre-change tool list and result fields passes without modification.
2. THE MCP_Server SHALL report its version, in the diagnostic tool result and in the MCP initialize response, equal to the version string in the installed package metadata.
3. IF a tool call fails, THEN THE MCP_Server SHALL return an object containing `error.code` (a value from the documented list of error codes), a `message` of at most 500 characters that contains no file-system paths and no exception text, and the name of the tool, and SHALL leave any previously stored evidence and Bundle unchanged.
4. WHEN the diagnostic tool is called, THE MCP_Server SHALL return the server version, the contract version, the Isolation_Mode, a boolean for whether `VK_MCP_READONLY` is set, a boolean for whether an examiner socket is configured, a boolean for whether a configured examiner socket accepted a connection within 2 seconds, and a boolean for whether `VK_EVIDENCE_DIR` is valid, without writing any file or opening any network connection other than to the configured examiner socket.
5. THE MCP_Server SHALL keep the diagnostic tool result free of secrets, so that the result never contains the value of `VK_VAULT_KEY`, the contents of the vault path, or the value of any environment variable other than the documented flags.
6. WHILE `VK_MCP_READONLY=1`, THE MCP_Server SHALL refuse network evidence acquisition and refetching replays, return a failure object with an `error.code` from the documented list indicating read-only mode, and open no outbound network connection.
7. IF a claim exceeds 262,144 bytes (256 KiB) or a Bundle exceeds 8,388,608 bytes (8 MiB), THEN THE MCP_Server SHALL reject the call with an `error.code` from the documented list indicating the size limit exceeded, and SHALL accept a claim or Bundle of exactly the cap size.
8. WHEN a Bundle carries a Bundle_Signature, THE MCP_Server SHALL include Signature_Validity and Signer_Trust in the `replay_bundle` and `explain_verdict` results, as defined in Requirement 10.
9. THE `.kiro/settings/mcp.json` SHALL list in `autoApprove` only tools that perform no write outside the server's private temporary directory and no network access.
10. WHEN an MCP client test is run, THE VerdictKit_System SHALL start the server over stdio, list the tools, call each tool with one valid input and one invalid input, validate each result against a documented schema, and report a failure for any tool whose result does not validate or whose call does not return within 30 seconds.
11. WHEN a VerdictKit MCP tool is called from inside Kiro, THE Evidence_Ledger SHALL record the tool name, the arguments, the result and the call date in ISO 8601 format, captured from Kiro.
12. IF the tools are not exposed to the Kiro session, THEN THE Evidence_Ledger SHALL record the Kiro MCP integration as `UNVERIFIED`, together with any stdio-client result labelled as obtained outside Kiro.
13. WHEN a tool call fails, THE MCP_Server SHALL set the MCP result flag `isError` to true and SHALL keep the structured `error` object in the result, and SHALL implement this without changing the return shape that the existing contract tests assert and without editing, loosening, skipping or marking any existing contract test.
14. IF claim validation raises `SchemaError`, THEN THE MCP_Server SHALL return the claim type's own validation message, which contains the offending field name and no exception text, no file-system path and no input value from the claim.
15. THE MCP_Server documentation SHALL state that the Kiro tool-call path was reported to drop empty arrays and empty objects from arguments, SHALL state which `verify_claim` fields that affects (for example the finance `addons`, `gov_fees` and `rebates` lists), and SHALL give a valid finance example that passes through Kiro.
16. THE MCP_Server SHALL NOT coerce a string to a boolean, treat a missing required list as empty, or otherwise relax claim validation to accommodate a client.
17. WHEN an MCP client test is run, THE VerdictKit_System SHALL include a finance claim with boolean fields and non-empty lists, delivered over a real stdio transport and checked for `SUPPORTED`, because the baseline contains no test that drives `verify_claim` over a stdio transport.
18. IF the MCP version in the initialize response differs from the package metadata, THEN the MCP client test SHALL fail.
19. WHEN a tool call fails because of an execution error (invalid input, size limit, read-only refusal, missing bundle or internal error), THE MCP_Server SHALL return an MCP result with `isError` true and the structured `error` object, and WHEN a tool call completes and the verdict is `INDETERMINATE`, `BLOCKED`, `CONTRADICTED` or any other verdict, THE MCP_Server SHALL return `isError` false with the same successful response shape as the baseline.
20. THE MCP client test SHALL run over a real stdio transport and SHALL include negative-path cases for each tool (invalid input, oversize input, read-only refusal, missing bundle, tampered bundle), and SHALL assert `isError` true for each execution error and `isError` false for a legitimate `INDETERMINATE` verdict.

### Requirement 10: Signed evidence bundles with signer trust evaluation (P4)

**User Story:** As a recipient of a bundle, I want to verify who produced it and whether I trust that signer, so that authenticity is established by evidence instead of assumed.

#### Acceptance Criteria

1. WHERE signing is enabled, THE Core SHALL create a Bundle_Signature over the SHA-256 of the canonical bytes of the Bundle manifest, using a private key supplied by the operator.
2. IF signing is enabled AND the operator-supplied private key is missing, unreadable, or of an unsupported algorithm, THEN THE Core SHALL abort bundle creation, SHALL write no Bundle, and SHALL report an error indicating the key problem without including key material.
3. THE Core SHALL use a signature algorithm provided by the `cryptography` package already declared in `core/pyproject.toml`, and SHALL add no new runtime dependency.
4. THE Core SHALL store the Bundle_Signature, the signature algorithm identifier and the public key of the Signer_Identity in members separate from the manifest-listed content.
5. WHERE signing is not enabled, THE Core SHALL write Bundles that are byte-identical to the baseline output for the same case and injected clock.
6. THE Core SHALL compute the Verdict_Hash without including any signature material.
7. WHEN the same case is bundled twice with an injected fixed clock and the same signing key, THE Core SHALL produce byte-identical signed Bundles.
8. WHEN a signed Bundle is verified, THE Core SHALL evaluate Signature_Validity separately from Signer_Trust and from bundle integrity and reproducibility, and SHALL report each as its own field.
9. THE Core SHALL report Signature_Validity as exactly one of `VALID`, `INVALID`, `UNSIGNED` or `UNSUPPORTED_ALGORITHM`.
10. THE Core SHALL report Signer_Trust as exactly one of `TRUSTED`, `UNTRUSTED_SIGNER` or `NOT_EVALUATED`.
11. WHEN a Trust_Store is supplied AND Signature_Validity is `VALID`, THE Core SHALL report `TRUSTED` if the Signer_Identity fingerprint is in the Trust_Store, and `UNTRUSTED_SIGNER` otherwise.
12. WHILE no Trust_Store is supplied, THE Core SHALL report Signer_Trust as `NOT_EVALUATED`.
13. IF Signature_Validity is not `VALID` THEN THE Core SHALL report Signer_Trust as `NOT_EVALUATED` and SHALL NOT report authenticity as established.
14. THE Core SHALL report authenticity as `ESTABLISHED` only when Signature_Validity is `VALID`, Signer_Trust is `TRUSTED` and bundle integrity is `VERIFIED`, and SHALL report `NOT_ESTABLISHED` in every other case, including every unsigned Bundle.
15. IF any byte of the manifest, a manifest-listed member, the signature or the embedded public key is altered THEN THE Core SHALL report Signature_Validity as `INVALID` or bundle integrity as failed, and SHALL report authenticity as `NOT_ESTABLISHED`.
16. THE Core SHALL read the Trust_Store only from a local operator-supplied file, and SHALL NOT trust the public key embedded in a Bundle without a Trust_Store entry.
17. IF the Trust_Store file is malformed or unreadable THEN THE Core SHALL report Signer_Trust as `NOT_EVALUATED` with a reason code, SHALL NOT report `TRUSTED`, and SHALL still report Signature_Validity and bundle integrity unchanged.
18. THE Core SHALL read the signing private key only in the Custodian process, and SHALL NOT place it in the Examiner environment, a Bundle, a log line, an API response or an MCP result.
19. THE Core SHALL perform signature verification offline, with no network access.
20. THE API_Server, THE CLI and THE UI_Kit SHALL display Signature_Validity, Signer_Trust and the authenticity result as separate fields, with the signer fingerprint.
21. THE OpenAPI document `api/openapi.yaml` SHALL describe the new fields, and the API contract version SHALL be incremented according to the contract's compatibility rules, with every existing field preserved.
22. FOR ALL Bundles produced by the signing function with a generated key, verifying the Bundle with the corresponding public key in the Trust_Store SHALL produce `VALID` and `TRUSTED` (round-trip property).
23. THE documentation SHALL state that a valid signature establishes who signed the bytes and that it does not establish that the claim is true, that the timestamp is trusted, or that the signer's key was not compromised.
24. THE Core SHALL sign with Ed25519 and SHALL record the algorithm identifier `ed25519` in the signature envelope, and any other identifier SHALL produce Signature_Validity `UNSUPPORTED_ALGORITHM`.
25. THE Core SHALL read the signing private key only from an externally provisioned location supplied by the operator, and SHALL NOT generate, store, log or commit a production signing key.
26. THE Core SHALL record in the signature envelope a stable key identifier, defined as the SHA-256 of the raw public key bytes, for each signing key.
27. THE Trust_Store SHALL be a versioned file that lists, for each key, the key identifier, the public key, a status of `ACTIVE`, `ROTATED` or `REVOKED`, and a validity interval, and THE Core SHALL report Signer_Trust `UNTRUSTED_SIGNER` for a key whose status is `REVOKED`.
28. IF a key has status `ROTATED`, THEN THE Core SHALL report Signer_Trust `TRUSTED` together with the reason code `KEY_ROTATED`, and SHALL report the reason code `KEY_REVOKED` for a `REVOKED` key.
29. THE signature envelope SHALL bind the SHA-256 of the complete canonical Bundle manifest, the Bundle format version, a signature-protocol identifier and version, the algorithm identifier and the key identifier, and THE signing input SHALL be a domain-separated byte string built from those fields.
30. IF a Bundle contains a duplicate archive path, an unknown signature member, a malformed or truncated signature, an unsupported algorithm, more than one signature envelope, a non-canonical envelope, or any other ambiguous signature representation, THEN THE Core SHALL reject the signature as `INVALID` or `UNSUPPORTED_ALGORITHM` and SHALL NOT report authenticity as `ESTABLISHED`.
31. THE Core SHALL exempt from the existing unlisted-member integrity rule only the signature members that the design names explicitly, and SHALL NOT apply a wildcard, a prefix match or any other general exemption.
32. THE Core SHALL keep verifying unsigned historical Bundles as before with Signature_Validity `UNSIGNED` and authenticity `NOT_ESTABLISHED`, and no document, UI text or API response SHALL describe an unsigned Bundle as authenticated.
33. THE VerdictKit_System SHALL present cryptographic validity, signer trust, bundle integrity and verdict correctness as four separate results, and SHALL NOT present a valid signature from a trusted signer as evidence that the verdict is correct.

### Requirement 11: Reusable claim-plugin SDK and scaffolding (P5)

**User Story:** As a developer, I want to create a new claim type from a template and check it against the platform's rules, so that a new domain preserves the blinding, determinism and Decimal guarantees.

#### Acceptance Criteria

1. THE Claim_Plugin_SDK SHALL document the `ClaimType` protocol, its optional hooks, the registration entry-point group `verdictkit.claim_types`, and the `VK_CLAIM_TYPES` mechanism.
2. WHEN the scaffolding command is run with a valid identifier and a target directory that does not exist or is empty, THE Claim_Plugin_SDK scaffolding command SHALL generate a new claim-type package containing a `pyproject.toml` entry point in group `verdictkit.claim_types`, a claim type class, one golden example claim, and one test module, and SHALL exit with code 0.
3. IF the target directory already exists and is not empty, THEN THE scaffolding command SHALL exit with a non-zero code, SHALL write an error message indicating that the directory is not empty, and SHALL leave every existing file in the directory byte-identical and create no new file.
4. IF the scaffolding command receives an identifier that is not a valid Python package name or not a valid `type_id`, THEN THE scaffolding command SHALL exit with a non-zero code, SHALL create no files or directories, and SHALL write a message that names the identifier and the specific naming rule that failed.
5. THE scaffolding command SHALL generate code in which `examine` and `findings` contain no `float` type, literal or conversion, no import of an LLM client library, and no wall-clock time read.
6. THE scaffolding command SHALL create files only inside the target directory and SHALL modify no file under `core/src/verdictkit/`.
7. THE Claim_Plugin_SDK SHALL provide a Conformance_Suite that accepts any registered claim type, identified by its `type_id`, and reports a pass or fail result for each check.
8. WHEN a claim type is run through the Conformance_Suite, THE Conformance_Suite SHALL check that two claims differing only in their `outcome_fields` values produce byte-identical blinded tasks and byte-identical examination results.
9. WHEN a claim type is run through the Conformance_Suite, THE Conformance_Suite SHALL check that the declared `outcome_fields` and `param_fields` share no field name, that `examine` called 2 times on the same claim returns identical results, that no `float` value appears in its examination output, and that its evidence policy forbids the `CLAIMANT` source class.
10. WHEN a claim type is run through the Conformance_Suite, THE Conformance_Suite SHALL check that a bundle produced for the golden example claim replays with status `REPRODUCED`.
11. WHEN the Conformance_Suite is run against each of the existing Quote_App, Reel_App and stub claim types, THE Conformance_Suite SHALL report every check as passed for each of them.
12. WHEN the Conformance_Suite is run against a freshly scaffolded claim type with no edits to the generated files, THE Conformance_Suite SHALL report every check as passed.
13. IF a claim type fails a Conformance_Suite check, THEN THE Conformance_Suite SHALL report that check as failed, SHALL name the failed check and the offending field name or value, SHALL continue running the remaining checks, and SHALL exit with a non-zero code.
14. THE Claim_Plugin_SDK SHALL leave the `ClaimType` protocol signatures unchanged, or SHALL update `.kiro/specs/verdictkit-core/design.md` before any signature change.
15. THE Claim_Plugin_SDK SHALL keep every claim type behind the Answer_Blind Examiner boundary, so that a plugin cannot read outcomes, the vault, the signing key or the network through any SDK interface, and SHALL leave all existing contracts unchanged.

### Requirement 12: Expanded regulatory verification from official sources (P6)

**User Story:** As a Quote Autopsy user in a jurisdiction beyond Texas, I want external tax and fee checks that rest on official published rules, so that a refutation or support can be traced to a source I can check.

#### Acceptance Criteria

1. WHEN a jurisdiction is added to Quote_App external checks, THE Quote_App SHALL base each rule only on a Source_Snapshot whose URI host is a domain published by that jurisdiction's government or statutory regulator, and SHALL reject a Source_Snapshot whose URI host is not on that jurisdiction's list of official domains.
2. THE Quote_App SHALL record for each Source_Snapshot the URI, the retrieval date (ISO 8601 calendar date, UTC), the SHA-256 of the retrieved bytes (64 lowercase hexadecimal characters), the media type, and the excerpt of text relied upon (1 to 2,000 characters).
3. WHEN a source is retrieved, THE Quote_App SHALL verify that the retrieved bytes contain the excerpt relied upon, and IF the body is an application shell or error page, or does not contain the excerpt, THEN THE Quote_App SHALL reject the retrieval, SHALL NOT create a Source_Snapshot from it, and SHALL record the rule as `UNVERIFIED`.
4. IF two distinct source URIs return byte-identical content THEN THE Quote_App SHALL reject both snapshots, SHALL mark the affected rules as `UNVERIFIED`, and SHALL NOT use those rules until a reviewer has recorded an approval.
5. IF an Official_Source cannot be retrieved within 30 seconds, returns a non-success HTTP status, or does not contain the rule text, THEN THE Quote_App SHALL record the rule as `UNVERIFIED` and SHALL NOT add a numeric rule value for it.
6. THE Quote_App SHALL NOT derive a rule value from memory, a secondary website, a model response or an unofficial summary.
7. WHEN the loader reads a rules snapshot, THE Quote_App SHALL recompute each source hash, and IF a recomputed hash differs from the recorded hash THEN THE Quote_App SHALL treat that source as unavailable evidence, SHALL NOT use any rule that depends on it, and SHALL return `INDETERMINATE` for any finding that depends on that rule.
8. IF a jurisdiction has no verified Source_Snapshot THEN THE Quote_App SHALL return `INDETERMINATE` with reason `unsupported_jurisdiction`.
9. IF a rule can only be satisfied by a filing or document that VerdictKit cannot obtain THEN THE Quote_App SHALL return `INDETERMINATE` with a reason code identifying the missing filing or document, and SHALL NOT return `REFUTED`.
10. WHERE a jurisdiction's tax rate varies by locality, WHILE the locality is not stated in the input, THE Quote_App SHALL sweep the full official published range, from minimum to maximum inclusive, as a `DEFAULT_POLICY` assumption, and SHALL list the swept bounds in the finding.
11. THE Quote_App SHALL retrieve the text of 7 TAC §84.205 from the Texas Secretary of State or label it `UNVERIFIED`, and SHALL NOT change the $225 documentary-fee treatment unless that text supports the change.
12. WHEN a jurisdiction's rules are added, THE Quote_App SHALL add at least one acceptance test for each of the outcomes `SUPPORTED`, `REFUTED`, `CONDITIONAL` and `INDETERMINATE`, with each expected value computed from the snapshot with Decimal arithmetic and no floating-point values.
13. THE Quote_App SHALL keep the Texas findings of `docs/B7_TEXAS_SPEC.md` unchanged, and the existing `tests/integration/test_quote_b7_texas.py` SHALL continue to pass with zero failures.
14. THE Quote_App SHALL state in its UI and documentation that each snapshot is a point-in-time copy, and SHALL display the retrieval date of the snapshot next to each finding that relies on it.
15. WHEN a retrieval is performed, THE Evidence_Ledger SHALL record the command or tool, the HTTP status, the byte count and the SHA-256, so that the retrieval is reproducible.
16. THE rules snapshot SHALL be packaged in the repository so that verification runs with no network access and produces the same outcomes as a run with network access.
17. THE Quote_App SHALL complete Texas regulatory coverage, including the retrieval of 7 TAC §84.205 or its recording as `UNVERIFIED`, before it adds any other jurisdiction.
18. THE Quote_App SHALL add jurisdictions in this priority order after Texas: California, Florida, New York, and SHALL add a jurisdiction only when its rules meet criteria 1 to 16.
19. THE Quote_App SHALL record for each rule the effective date stated by the Official_Source, and IF the effective date is not stated THEN THE Quote_App SHALL record the rule as `UNVERIFIED`.
20. THE Quote_App SHALL NOT state a speculative legal conclusion, and SHALL return an explicit `INDETERMINATE` or `UNVERIFIED` outcome for any rule that no Source_Snapshot supports.

### Requirement 13: Threat-model-driven security and property testing (P7)

**User Story:** As a security reviewer, I want a threat model whose every control has a test, so that security claims are demonstrated by tests and are not asserted.

#### Acceptance Criteria

1. THE Threat_Model SHALL list assets, principals, trust boundaries, entry points, threats, the control for each threat, and the test identifier that exercises that control, with exactly one row per threat and a non-empty value in every column.
2. THE Threat_Model SHALL cover at least these threats, each as its own row: outcome leakage to the Examiner, vault key exposure, ledger tampering, evidence substitution, bundle zip bombs, bundle path traversal, malformed API input, oversized API input, rate-limit evasion, replay of uploaded bundles consuming storage, signature forgery, key substitution, Trust_Store tampering, MCP path leakage, MCP error leakage, plugin code reaching outcomes, and regulatory snapshot substitution.
3. IF a threat has no automated test, THEN THE Threat_Model SHALL label that threat `UNTESTED` and SHALL state the reason in a non-empty reason field on the same row.
4. WHEN a property test is added, THE VerdictKit_System SHALL cite the property statement and at least one requirement identifier in the test docstring, as required by `.kiro/steering/testing.md`.
5. THE VerdictKit_System SHALL add one Hypothesis property test for each of these five properties: (a) changing any single byte of a Bundle never yields `REPRODUCED` or `VALID`; (b) unsigned Bundles remain byte-identical to the baseline; (c) signature material never changes the Verdict_Hash; (d) MCP error results never contain a host path separator (`/` or `\`) taken from the host filesystem path; (e) every generated claim type passes the Conformance_Suite.
6. IF a Bundle input has a malformed zip entry, a duplicate zip name, an absolute member name, a parent-directory member name, a truncated signature, a wrong-algorithm signature, or a malformed Trust_Store file, THEN THE VerdictKit_System SHALL reject the input or return `UNVERIFIABLE`, SHALL NOT return `REPRODUCED` or `VALID`, and SHALL leave existing stored data unchanged. Each of the seven input kinds SHALL have at least one negative test.
7. THE VerdictKit_System SHALL run the new tests under the `ci` Hypothesis profile with derandomization enabled, and SHALL run them in the existing CI workflow, which SHALL fail when any new test fails.
8. WHERE a security test requires a container, THE VerdictKit_System SHALL mark it `isolation` and SHALL run it in the container gate.
9. IF a test finds a defect, THEN THE VerdictKit_System SHALL record the failing input in the Evidence_Ledger, fix the code, and keep the test. THE VerdictKit_System SHALL NOT weaken, skip, or delete an existing check to make the test pass.
10. THE VerdictKit_System SHALL produce zero violations from `ruff check .` for all new Python code.
11. THE VerdictKit_System SHALL remediate BE-1 by keeping the Linux POSIX mode assertion unchanged and adding platform-appropriate Windows security handling (for example a verified access-control check) that tests the same security property, and SHALL NOT remove, weaken, skip or mark the original assertion.
12. THE VerdictKit_System SHALL remediate BE-2 by adding instrumentation that records the connection and response timing, establishing the root cause on Windows and on Linux, and fixing that cause, and SHALL NOT treat an increased timeout alone as a verified fix.
13. WHEN BE-1 or BE-2 is reported as remediated, THE VerdictKit_System SHALL record per-test listings (`-rA`) and the captured pytest exit code on Windows and on a Linux_Docker_Host from a full checkout.
14. THE VerdictKit_System SHALL add adversarial input tests for the API, the MCP_Server, Bundle parsing, the Trust_Store, signature envelopes, plugin scaffolding and regulatory snapshots, and each SHALL assert a rejection, `INDETERMINATE` or `UNVERIFIABLE` result.
15. THE VerdictKit_System SHALL run a targeted regression set on both host classes (Windows and Linux_Docker_Host) for every change that touches a security control, and SHALL record each host's result separately.

### Requirement 14: Complete end-to-end regression and release verification (P8)

**User Story:** As the release owner, I want one complete verified run of everything on the final commit, so that the release candidate is supported by evidence and not by earlier results.

#### Acceptance Criteria

1. WHEN a Release_Candidate is selected, THE VerdictKit_System SHALL rerun every Baseline_Run step on the Release_Candidate commit and SHALL record one Execution_Record per step, each containing the commit identifier, the step name, the Outcome_Class, the passing count, the failing count, and the start and end timestamps.
2. WHEN a Release_Candidate is selected, THE VerdictKit_System SHALL run the following on the Release_Candidate commit and record an Execution_Record for each: the signing and trust tests, the MCP client test, the Conformance_Suite, the accessibility scan, the regulatory snapshot tests, the new property tests, and the scaffolding end-to-end test.
3. WHEN the container gates are run for the Release_Candidate, THE VerdictKit_System SHALL run them on a Linux_Docker_Host with `--network none` for every gate that permits it.
4. IF a container gate does not permit `--network none` or no Linux_Docker_Host is available, THEN THE VerdictKit_System SHALL record that gate's Outcome_Class as `UNVERIFIED` with the reason, and SHALL NOT record it as passed.
5. WHEN the end-to-end scenario is run, THE VerdictKit_System SHALL perform these steps in order: submit a claim, freeze it, run it through the authenticated examiner, download a signed Bundle, and replay the Bundle offline with no network access.
6. WHEN the offline replay completes, THE VerdictKit_System SHALL pass the end-to-end scenario only if the replay status equals `REPRODUCED` and the signature and trust fields equal the expected values defined for the scenario.
7. IF any step of the end-to-end scenario fails, or the replay status differs from `REPRODUCED`, THEN THE VerdictKit_System SHALL record the scenario Outcome_Class as `FAILED`, identify the failing step, and retain the Execution_Records of the steps completed before the failure.
8. WHEN the final test counts are reported, THE VerdictKit_System SHALL take every count from the runner output of the Release_Candidate run, and SHALL NOT use counts from earlier runs or other commits.
9. WHEN the Release_Candidate's Baseline_Run steps are compared with the baseline, THE VerdictKit_System SHALL report each step whose passing count is lower than its baseline passing count, with both counts shown.
10. IF any required step has Outcome_Class `FAILED`, or BE-1 or BE-2 is not remediated, THEN THE VerdictKit_System SHALL NOT mark the Release_Candidate verified, and SHALL list each failed step and each unremediated Baseline_Exception in the release report.
11. IF any required step has Outcome_Class `UNVERIFIED`, THEN THE VerdictKit_System SHALL list it in the release report as `UNVERIFIED` with the reason, and SHALL NOT mark the Release_Candidate verified for that capability.
12. THE VerdictKit_System SHALL produce a release report under `docs/next-phase/` that lists for each of the nine tracks the Outcome_Class of every acceptance criterion, the known limitations, and the rollback procedure.
13. THE VerdictKit_System SHALL leave the creation of any release tag and any merge, push or publication to an explicit action by the repository owner.
14. THE VerdictKit_System SHALL verify at the end of the phase that each Frozen_Release ref and each Submission_Artifacts file is unchanged against its own recorded value in Requirement 1.2, including both the tag object and the peeled commit of `v1.0.0-submission`.
15. THE VerdictKit_System SHALL document how a third party reproduces the Release_Candidate verification from a clean checkout, including the tools required.
16. THE VerdictKit_System SHALL verify the exact head commit of the Release_Candidate, so that the commit that is tested, built and described in the release report is the same commit, and SHALL record that commit's full SHA in every Execution_Record of the release run.
17. THE VerdictKit_System SHALL record release provenance: the commit SHA, the container image digest built from it, the `uv.lock` hash, the `package-lock.json` hash, the tool versions, and the host class of each run.
18. THE VerdictKit_System SHALL run the signed-bundle end-to-end scenario so that it asserts `ESTABLISHED` authenticity only with a Trust_Store entry for the signing key, and asserts `NOT_ESTABLISHED` for the same Bundle verified without that entry.
19. THE VerdictKit_System SHALL list Browser E2E, `scripts/gate_nov22.sh`, the five skipped Linux cases and automatic Kiro hook execution in the release report as `UNVERIFIED` unless each has a `SUCCEEDED` Execution_Record for the Release_Candidate.

### Requirement 15: Historical evidence reconciliation

**User Story:** As a reviewer, I want every figure from the Historical_Audit checked against the actual files before it is recorded as verified, so that the frozen documentation, which predates later Kiro validation, is corrected by evidence and not by assertion.

#### Acceptance Criteria

1. THE VerdictKit_System SHALL read the Historical_Audit directories in read-only mode, and SHALL NOT modify, move, rename or delete any file in them.
2. THE VerdictKit_System SHALL NOT copy a raw Kiro session log, transcript, `messages.jsonl` file, log file or archive from the Historical_Audit into the repository.
3. THE VerdictKit_System SHALL record in the repository only derived values (counts, sums, hashes, event names and short non-sensitive excerpts) together with the path of the source outside the repository.
4. THE VerdictKit_System SHALL recompute each of these claims from the Historical_Audit files and record a Reconciliation_Record for each: 92.9518 credits consumed; 318 request identifiers; 417 unique tool calls; four `spec-task-execution` sub-agent runs; six sessions with conversation transcripts; all four VerdictKit MCP tools invoked from inside Kiro; all four registered claim types exercised through Kiro MCP; automatic hook execution unverified.
5. IF a recomputed value differs from a claimed value, THEN THE VerdictKit_System SHALL record the Reconciliation_Record as `CONTRADICTED` or `CONFIRMED_WITH_CORRECTION` with both values, and SHALL use the recomputed value.
6. IF a claim cannot be recomputed from the files, THEN THE VerdictKit_System SHALL record it as `UNVERIFIED` and SHALL NOT use it as evidence.
7. WHERE two Historical_Audit documents disagree, THE VerdictKit_System SHALL record both statements, SHALL identify the document that is later or better supported, and SHALL record the earlier statement as corrected.
8. THE VerdictKit_System SHALL NOT edit the frozen documentation to apply a correction, and SHALL record each correction in a new file under `docs/next-phase/`.
9. THE VerdictKit_System SHALL label each Historical_Audit result with the host on which it was obtained (Windows or Linux image) and SHALL NOT merge a Windows result and a Linux result into one claim.
10. WHEN an UI text, README or documentation statement relies on the Historical_Audit, THE VerdictKit_System SHALL cite the Reconciliation_Record that supports it.

### Requirement 16: Kiro credit and usage tracking

**User Story:** As the maintainer, I want the real Kiro credit consumption of this phase recorded where Kiro reports it, so that cost is visible without inventing numbers.

#### Acceptance Criteria

1. WHERE Kiro provides a usage record for a session of this phase, THE Evidence_Ledger SHALL record the credits, the unit, the request identifiers count, the session identifier and the date, read from that record.
2. IF Kiro provides no usage record for a task, sub-agent run or session, THEN THE Evidence_Ledger SHALL record the credit figure as `NOT_AVAILABLE` and SHALL NOT estimate, interpolate or back-fill it.
3. THE Evidence_Ledger SHALL record a credit figure for each track only as the sum of Credit_Records attributable to that track, and SHALL record the unattributed remainder separately.
4. THE VerdictKit_System SHALL keep the Historical_Audit credit total separate from the credit total of this phase.
5. THE Evidence_Ledger SHALL NOT report a cost per task, per test or per requirement unless a Credit_Record exists for that exact unit.

