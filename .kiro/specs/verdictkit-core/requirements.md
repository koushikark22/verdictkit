# Requirements Document — VerdictKit Core

## Introduction

VerdictKit Core is the reusable skeleton for forensic claim verification. It freezes a
claim into a canonical executable specification, seals the claimed outcomes away from the
evaluator, acquires policy-checked evidence, evaluates the claim deterministically across a
bounded assumption grid, and emits a reproducible verdict bundle. Domain knowledge lives
exclusively in claim-type plugins. The core contains no domain logic and no LLM calls.

Glossary: *Custodian* — the process that holds sealed outcomes, the ledger and the
comparator. *Examiner* — the separate process that evaluates blinded tasks. *Claim type* —
a plugin describing one kind of claim.

## Requirements

### Requirement 1: Canonical claim freezing

**User Story:** As a verifier, I want every claim frozen into one canonical form, so that
the exact thing being judged is fixed and identifiable before any evaluation starts.

#### Acceptance Criteria

1. WHEN a claim is submitted THE Core SHALL validate it against the claim type's parameter, outcome, assumption and tolerance schemas before freezing.
2. WHEN a claim contains a floating-point number, NaN, Infinity, a duplicate key, or a non-string object key THE Core SHALL reject it with a `CanonicalizationError` naming the offending path.
3. THE Core SHALL serialise frozen claims as UTF-8 JSON with sorted keys, no insignificant whitespace, Decimals as strings and integers as JSON integers.
4. THE Core SHALL compute `spec_hash` as the SHA-256 of the canonical bytes of claim type, schema version, parameters, assumptions and tolerances, excluding claimed outcomes.
5. WHEN any parameter, assumption or tolerance changes THE Core SHALL produce a different `spec_hash`.
6. WHEN only claimed outcomes change THE Core SHALL produce the same `spec_hash`.

### Requirement 2: Parameter/outcome partition and blinding

**User Story:** As a judge, I want proof that the evaluator never saw the claimed answer,
so that its result cannot have been anchored to that answer.

#### Acceptance Criteria

1. THE Core SHALL partition every submitted claim into parameters and outcomes using the claim type's declared `outcome_fields`.
2. THE Core SHALL construct a `BlindedTask` through a function whose input type does not contain outcomes.
3. WHEN two claims differ only in outcome values THE Core SHALL produce byte-identical `BlindedTask` serialisations and byte-identical examination results.
4. THE Core SHALL never include outcome values in any message sent to the Examiner.

### Requirement 3: Sealed outcomes and commitment

**User Story:** As a judge, I want the claimed outcome locked before evaluation, so that the
order of events is verifiable from the bundle.

#### Acceptance Criteria

1. WHEN a claim is frozen THE Custodian SHALL generate a 32-byte random salt and compute `commitment = SHA256("vk-commit-v1" ‖ salt ‖ canonical(outcomes))`.
2. THE Custodian SHALL store outcomes encrypted with AES-GCM under a key held only in Custodian process memory, in a directory with mode 0700 owned by the Custodian OS user.
3. WHEN outcomes are revealed THE Custodian SHALL verify them against the commitment and SHALL abort the case if verification fails.
4. THE Core SHALL record the salt and plaintext outcomes in the bundle only after reveal.

### Requirement 4: Examiner process isolation

**User Story:** As a judge, I want the blinding enforced by the operating system, not just
by code convention.

#### Acceptance Criteria

1. WHILE `isolation_mode` is `ENFORCED` THE Examiner SHALL run as a distinct OS user with no read permission on the vault directory.
2. THE Custodian SHALL start the Examiner with a scrubbed environment containing only an allowlisted set of variables, excluding the vault key.
3. THE Examiner SHALL accept only `BlindedTask` messages over a local socket, rejecting messages larger than 8 MiB.
4. THE Examiner SHALL run under CPU-time and address-space resource limits.
5. WHEN the Core runs on a platform without OS-user separation THE Core SHALL set `isolation_mode` to `UNENFORCED` and stamp it in the ledger, bundle manifest, API responses and UI.
6. IF judge mode is enabled AND `isolation_mode` is not `ENFORCED` THEN THE Core SHALL refuse to start.

### Requirement 5: Evidence provenance and policy

**User Story:** As a verifier, I want every piece of evidence traceable and independent of
the claimant, so that refutations rest on sources I can check.

#### Acceptance Criteria

1. THE Core SHALL record for each evidence item: source id, source class, URI, retrieval time, SHA-256, media type and license class (`REDISTRIBUTABLE`, `REFETCH_ONLY`, `DOCUMENT`, `USER_SUPPLIED`).
2. THE Evidence Broker SHALL fetch only from sources on the claim type's permitted-source list.
3. IF an evidence item's source class is forbidden by the claim type's policy (including `CLAIMANT`) THEN THE Core SHALL mark every finding that depends on it `INDETERMINATE` with reason `policy_violation`.
4. THE Evidence Store SHALL be content-addressed and SHALL recompute the SHA-256 on every read, raising `EvidenceIntegrityError` on mismatch.
5. THE Core SHALL distinguish findings that use no external evidence (`INTERNAL_ARITHMETIC`) from findings that use external evidence (`EXTERNAL_EVIDENCE`).
6. WHILE a case's data mode is `LIVE_EVIDENCE` THE Core SHALL forbid `SYNTHETIC_FIXTURE` evidence regardless of plugin policy (`effective_policy`).
7. IF a configured source's rights basis is `UNVERIFIED` AND the data mode is `LIVE_EVIDENCE` THEN THE Core SHALL block the case with `EVIDENCE_RIGHTS_UNVERIFIED` before acquisition.

### Requirement 6: Verdict model

**User Story:** As a reader of a verdict, I want each finding to state what kind of
certainty it carries, so that arithmetic contradictions and external refutations are not
confused.

#### Acceptance Criteria

1. THE Core SHALL accept only these basis/status pairs: `INTERNAL_ARITHMETIC` with `CONSISTENT|CONTRADICTED|CONDITIONAL|INDETERMINATE` (`CONDITIONAL` only when the result varies across swept document facts or formula conventions); `EXTERNAL_EVIDENCE` with `SUPPORTED|REFUTED|CONDITIONAL|INDETERMINATE`; `MECHANICAL_BOUND` with `WITHIN_BOUND|IMPOSSIBLE|INDETERMINATE`.
2. THE Core SHALL attach the fixed confidence-scope sentence for the finding's basis.
3. THE Core SHALL compute the headline status as the worst finding status in the order `IMPOSSIBLE > CONTRADICTED > REFUTED > CONDITIONAL > INDETERMINATE > SUPPORTED = CONSISTENT = WITHIN_BOUND`.
4. THE Core SHALL compute `verdict_hash` over spec hash, evidence hashes, examination result, revealed outcomes and findings, excluding timestamps, salts, ledger entries and diagnostics.
5. WHEN a finding is `CONTRADICTED`, `REFUTED`, `CONDITIONAL` or `IMPOSSIBLE` THE Core SHALL include at least one concrete counterexample with expected value, observed value, difference and tolerance.

### Requirement 7: Assumptions and bounded sensitivity analysis

**User Story:** As a verifier, I want missing assumptions handled explicitly, so that
verdicts never silently depend on values nobody stated.

#### Acceptance Criteria

1. THE Core SHALL represent each assumption as `fixed`, `range(min,max,step)`, `set`, or `missing`, with origin `CLAIMANT`, `USER_CONFIRMED` or `DEFAULT_POLICY`.
2. WHEN an assumption is missing AND the claim type provides a policy range THE Core SHALL sweep that range and disclose its origin as `DEFAULT_POLICY`.
3. WHEN an assumption is missing AND no policy range exists THE Core SHALL mark only findings that declare a dependency on it `INDETERMINATE` with reason `missing_assumption:<name>`.
4. IF the assumption grid exceeds the configured cap (default 1000, maximum 1000) THEN THE Core SHALL reject the claim at intake and SHALL NOT subsample.
5. THE Core SHALL enumerate grid points deterministically: assumptions sorted by name, values ascending.
6. WHEN results differ across grid points THE Core SHALL report `CONDITIONAL` with the first failing point, the first passing point and the worst point by margin.
7. THE Core SHALL describe swept results as "verified at N grid points" and never as holding for all values.

### Requirement 8: Ledger

**User Story:** As a judge, I want a tamper-evident record of the case's order of events.

#### Acceptance Criteria

1. THE Ledger SHALL accept entries only in the order `CASE_OPENED, CLAIM_FROZEN, OUTCOMES_COMMITTED, EVIDENCE_ACQUIRED, EXAMINATION_COMMITTED, OUTCOMES_REVEALED, VERDICT_SEALED, DIAGNOSTICS_APPENDED*, BUNDLE_WRITTEN`.
2. IF an entry is appended out of order THEN THE Ledger SHALL raise `LedgerOrderError` and leave the ledger unchanged.
3. THE Ledger SHALL chain entries with `entry_hash = SHA256("vk-ledger-v1" ‖ seq ‖ kind ‖ payload_hash ‖ prev_hash)` and SHALL exclude `recorded_at` from the hash.
4. WHEN any entry is modified THE Ledger verification SHALL fail and identify the first invalid sequence number.

### Requirement 9: Bundles and offline replay

**User Story:** As a sceptic, I want to rerun a verdict on my own machine without trusting
the server.

#### Acceptance Criteria

1. THE Core SHALL write bundles as zip files with sorted entries, fixed timestamps and a manifest listing every file's SHA-256, the engine version, the environment fingerprint and the isolation mode.
2. THE Core SHALL embed evidence bytes only for license classes `REDISTRIBUTABLE`, `DOCUMENT` and `USER_SUPPLIED`, and SHALL embed URI and hash only for `REFETCH_ONLY`.
3. WHEN replaying THE Core SHALL perform no network access unless `--allow-refetch` is given.
4. WHEN replaying THE Core SHALL report `REPRODUCED` if the verdict hash matches and the environment fingerprint matches, `REPRODUCED_ACROSS_ENV` if only the verdict hash matches, `DIVERGED` if the verdict hash differs, and `UNVERIFIABLE` if required evidence is absent or fails its hash.
5. WHEN the same case is bundled twice with an injected fixed clock THE Core SHALL produce byte-identical bundles.

### Requirement 10: Claim-type plugin API

**User Story:** As a developer, I want to add a domain without touching the core.

#### Acceptance Criteria

1. THE Core SHALL load claim types through a registry keyed by `type_id`.
2. THE Core SHALL call plugin code only through the `ClaimType` protocol methods.
3. THE repository SHALL include a third stub claim type under `core/examples/` that runs end-to-end without any change to core modules.
4. THE Core SHALL run post-reveal diagnostics only after `VERDICT_SEALED` and SHALL exclude them from `verdict_hash`.

### Requirement 11: Determinism and the LLM fence

**User Story:** As a judge, I want verdicts computed only by deterministic code.

#### Acceptance Criteria

1. THE Core SHALL perform all monetary and rate arithmetic with `Decimal` inside an explicit local context.
2. THE Core SHALL not use wall-clock time as an input to any evaluator or comparator.
3. THE modules `verdictkit.custody`, `verdictkit.examiner`, `verdictkit.evidence`, `verdictkit.sweep` and each app's evaluator modules SHALL NOT import any LLM client library, enforced by an automated test in CI.
4. WHERE an assist feature drafts a claim from free text THE Core SHALL mark the draft `EXTRACTED` and SHALL require explicit user confirmation before freezing.

### Requirement 12: MCP server and judge mode

**User Story:** As a judge or agent, I want to verify and replay claims without signing up.

#### Acceptance Criteria

1. THE Core SHALL expose MCP tools `list_claim_types`, `verify_claim`, `replay_bundle` and `explain_verdict`, all without side effects outside a temporary directory.
2. WHILE judge mode is enabled THE API SHALL require no account, SHALL rate-limit per client, SHALL cap request bodies at 256 KiB, and SHALL expire cases after 24 hours.
3. THE frozen claim schemas SHALL contain no fields for personal names, addresses, VINs or free text. Intake MAY accept transient pasted text per docs/API_CONTRACT.md §8, which SHALL never be persisted, logged, frozen or bundled.

### Requirement 13: Presentation adapter and HTTP API

**User Story:** As the frontend, I want one stable contract that separates whether the engine
could conclude from what it concluded.

#### Acceptance Criteria

1. THE API SHALL implement the routes and schemas in `api/openapi.yaml`; every response SHALL validate against its schema.
2. THE adapter SHALL report `executionStatus` (`COMPLETED`, `BLOCKED`, `INDETERMINATE`) separately from finding statuses, per docs/API_CONTRACT.md §2.
3. THE adapter SHALL set `confidenceClass` to null for INDETERMINATE findings, non-COMPLETED runs and `SYNTHETIC_DEMO` cases.
4. THE adapter SHALL never mark a `TRADE` or `EQUITY_SERIES` key record as `COUNTEREXAMPLE`.
5. THE API SHALL persist each progress event to the run record before emitting it, and ledger-bound stages SHALL carry the matching ledger sequence number.
6. THE API SHALL report bundle integrity, reproducibility and authenticity as separate fields; authenticity SHALL be `NOT_ESTABLISHED`.

### Requirement 14: Command line

#### Acceptance Criteria

1. THE Core SHALL provide `verdictkit run` and `verdictkit replay` as specified in `core/src/verdictkit/cli.py`.
2. WHEN `verdictkit replay` runs THE CLI SHALL perform no network access unless `--allow-refetch` is given, and SHALL exit 0 only for a reproduced verdict with integrity VERIFIED.
