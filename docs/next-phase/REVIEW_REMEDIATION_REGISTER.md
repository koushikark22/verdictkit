# Independent-review remediation register

Written 2026-11-25 with the design checkpoint that added D8 and D9 and amended `requirements.md`. D10 and the seven canonical design sections were not part of that checkpoint. They were written afterwards, in the commit that finalizes the design, and D10.6 of `design.md` holds the short form of this register. The independent review text is not stored in this repository. The 15 summaries below are the maintainer's one-line wording, carried unchanged. Where a summary names no concrete defect, the response states the design's interpretation, and the mapping to a code defect stays UNVERIFIED.

Status words. DECIDED: a maintainer decision is recorded. DESIGNED: written in `design.md`, nothing implemented. AMENDED: `requirements.md` text changed. APPLIED (documentation): a documentation-only change was made in this checkpoint, with no Execution_Record. IMPLEMENTED and VERIFIED: none in this checkpoint. The only SUCCEEDED, FAILED and UNVERIFIED results in the repository are the 26 canonical baseline executions of `EXECUTION_EVIDENCE.md`. Every row below is UNVERIFIED for Requirement 3 until an Execution_Record exists.

## Findings (15)

| ID | Maintainer summary | Response | Criteria | Rows | Status |
|---|---|---|---|---|---|
| H-1 | Preserve originals privately; publish sanitized evidence with separate hashes and redaction methodology | DD8-9. Rules RR-1 to RR-3 in `EVIDENCE_REDACTION.md`, applied once to the raw baseline records. Zero-hit scan before publishing | 1.14, 3.11, 3.14 | D8-AC-22 | DESIGNED, AMENDED, APPLIED (documentation) |
| M-1 | Eliminate vault-key exposure through process arguments. Test cmdline, environ, inherited descriptors, accessible files and logs | DD8-2 key file on tmpfs, tests KT-1 to KT-8 | 7.20, 13.16 | D8-AC-8 | DESIGNED, AMENDED |
| M-2 | Isolate uploaded replay metadata from shared trusted evidence | DD8-3 per-replay namespace, trusted root unchanged | 7.22, 13.17 | D8-AC-9, D8-AC-20 | DESIGNED, AMENDED |
| M-3 | Use feature-branch workflow_dispatch where supported | D9 exact-commit rule: dispatch `p0-integration.yml` at the Phase_Branch, check the run head SHA, no pull request or merge for CI | 14.20 | D8-AC-26, D9-AC-9 | DESIGNED, AMENDED |
| M-4 | Explicitly resolve BE-1 requirement contradictions. Preserve POSIX assertions and require equivalent Windows ACL security assertions | D8.5 BE-1 closure. 13.11 rewritten, 8.13 scoped to hook configuration while BE-1 is open, 2.11 kept. D3.9 design stands | 13.11, 8.13, 2.11 | D8-AC-4, D8-AC-5 | DESIGNED, AMENDED |
| M-5 | Define a contained environment for genuine ongoing Kiro hook execution | DD8-15 CE-1 to CE-8, on top of AM-D3-1, AM-D3-6, AM-D3-7 | 8.19, 8.20 | D8-AC-25 | DESIGNED, AMENDED |
| M-6 | Require external owner-controlled security review records | DD8-13 External_Review_Record, reference only in the repository | 13.27, 14.27 | D8-AC-27 | DESIGNED, AMENDED |
| M-7 | Reduce unnecessary implementation complexity | DD8-14 complexity budget: one mechanism per surface, no new runtime dependency, control without threat row removed | 13.28 | D8-AC-28 | DESIGNED, AMENDED |
| L-1 | Correct isolation downgrade semantics | DD8-10 rules S1 to S7, fixed mode, fail closed | 2.13, 13.24 | D8-AC-18 | DESIGNED, AMENDED |
| L-2 | Authenticate the custodian from the examiner side | DD8-11 peer credential check in the worker | 2.14, 13.24 | D8-AC-18 | DESIGNED, AMENDED |
| L-3 | Evaluate AuthzAccessCheck and supported Python patch versions | DD8-6 Python 3.12.4 minimum on Windows. DD8-7 evaluation: structural oracle required, `GetEffectiveRightsFromAcl` dropped, `AuthzAccessCheck` as a timeboxed spike. Spike not run | 13.25 | D8-AC-5 | DESIGNED, AMENDED, spike UNVERIFIED |
| L-4 | Reconcile ledger commands, traceability and BE-2 attribution | D8.5 ledger lint. Baseline reconciled in `baseline/LEDGER_COMMAND_RECONCILIATION.md`. Corrections C-006 to C-008. BE-2 read as "observed on Windows" | 1.19, 3.12 | D8-AC-23 | DESIGNED, AMENDED, APPLIED (documentation) |
| L-5 | Preserve genuine Kiro authoring and execution evidence | DD8-15 and D9 Kiro evidence rule. No reconstruction. Usage only from a Kiro usage record | 3.13, 14.25 | D8-AC-24 | DESIGNED, AMENDED |
| L-6 | Restrict MCP bundle access to approved roots, including symlink, traversal and reparse-point protections | DD8-5 Approved_Root, shared safe-open helper, `PATH_NOT_ALLOWED` | 9.1, 9.21, 13.19 | D8-AC-11 | DESIGNED, AMENDED |
| L-7 | Bound concurrent uploads before full-body buffering | DD8-4 admission before the first body read | 7.21, 13.18 | D8-AC-10 | DESIGNED, AMENDED |

## Maintainer decisions recorded with the D6 and D7 review

| Decision | Record | Criteria | Status |
|---|---|---|---|
| MCP `>=2.3,<2.4` with one exact pin in `uv.lock` | AM-D4-8 (D4.13), confirms AM-D4-6 | 9.22 | DECIDED, DESIGNED |
| API contract 2.0.0 for breaking changes, with migration and compatibility strategy | AM-D5-12 (D5.13), resolves OD-D5-1 | 10.21, 10.34 | DECIDED, DESIGNED |
| Targeted CA to ZZ unsupported-jurisdiction fixture edits, purpose and assertions preserved | AM-D7-1 (D7.11), resolves B-D7-1 | 12.13, 12.21 | DECIDED, DESIGNED |
| Read-only retrieval of official regulatory sources, no paid service, no cloud provisioning | AM-D7-2 (D7.11) | 12.22 | DECIDED, DESIGNED. No retrieval was made |
| Historical bundle replay through version-aware examination semantics | AM-D7-3 (D7.11), replaces G-D7-2 and D7-AC-19 | 10.5, 12.23 | DECIDED, DESIGNED |
| Regulatory source artifacts preserved where permitted, with hashes, dates, provenance, offline verification | AM-D7-4 (D7.11), resolves OD-D7-1 | 12.24 | DECIDED, DESIGNED |
| Public plugin loading fails closed, rejects duplicate type ids, binds to package or artifact provenance | AM-D6-1 to AM-D6-3 (D6.11) | 11.16 to 11.18 | DECIDED, DESIGNED |
| Public security profile propagated and validated in custodian and examiner | AM-D6-4 (D6.11), closes G-D6-1 | 7.19 | DECIDED, DESIGNED |
| Minimal judge UI compatibility changes on the Phase_Branch, frozen references immutable | AM-D5-13 (D5.13), confirms AM-D5-11 | 1.8, 10.35 | DECIDED, DESIGNED |

## Final maintainer decisions (recorded 2026-11-25)

Recorded in `design.md` section D10.10, which governs the earlier text it names (D10.2, rows 23 to 27). Status words as above. Each decision is DECIDED and DESIGNED. Nothing is implemented, and no Execution_Record exists for any of them (Requirement 3). The tasks that carry them are in `tasks.md`.

| Decision | Record | Criteria | Status |
|---|---|---|---|
| Evidence commits reference the exact tested Release_Candidate SHA. A different commit is not automatically the same tested candidate. | OD-D9-1 (D10.10) | 14.16, 14.21 | DECIDED, DESIGNED |
| Manifest integrity, signature authenticity and complete archive-byte integrity are three separate results. Exact archive-byte verification requires an external trusted digest. | OD-D10-4 (D10.10) | 10.36 (new), 13.5(a), 14.24 | DECIDED, DESIGNED, AMENDED |
| The initial failed-authentication threshold is five attempts per 15 minutes per source and account, configurable and bounded. | OD-D10-1 (D10.10) | 7.24 | DECIDED, DESIGNED |
| The five-second recording target of 3.2 is retained. A recording failure is visible and cannot create a successful evidence claim. | OD-D10-2 (D10.10) | 3.2 | DECIDED, DESIGNED |
| A failed rollback blocks the release and requires recovery to a verified checkpoint (blocker RB-18). | OD-D10-3 (D10.10) | 4.6, 14.10 | DECIDED, DESIGNED |

## Requirement gaps and contradictions resolved

| Item | Resolution |
|---|---|
| G-1 case ownership | 7.23 (AM-6) |
| G-2 access policy | 7.24 (AM-7) |
| G-3 retention, sweeper | 7.25 (AM-9) |
| G-4 liveness, readiness, health disclosure | 7.26 (D2.6) |
| G-5 startup line not printed by `serve`, G-6 headers missing on 429 and 413 | Requirements 7.7 and 7.5 stand. They are code gaps tracked by D2 acceptance rows. No new text |
| G-7 to G-13 hook criteria | 8.8, 8.1 and 8.7, 8.2, 8.5, 8.6, 8.16 with 8.19, 8.10 amended |
| G-D6-1 profile reaches the examiner | 7.19 |
| G-D7-1 contract-visible D7 fields | Classified in the 2.0.0 event (AM-D5-12) |
| OD-6 criterion 5.8 against DD-9 | 5.8 and 6.9 except sealed claimed figures |
| BE-1 contradictions (13.11, 8.13, 2.11) | See M-4 |
| 1.14 byte-for-byte preservation against private publication | 1.14 amended (see H-1) |
| 13.5(a), 13.6, 13.21 forbade only `REPRODUCED` and `VALID` for tampered input | `REPRODUCED_ACROSS_ENV` added. `ReplayStatus` has two success values |
| 12.23, 13.22, 14.24 required `REPRODUCED` for historical bundles | Equal verdict hash with `REPRODUCED` or `REPRODUCED_ACROSS_ENV`. Same-image replay stays `REPRODUCED` |
| `### Requirement numbering and review history` read as a malformed requirement heading | Renamed `### Numbering and amendment history` |
| `mcp>=1.2` declared, 2.x API imported (F4-6) | 9.22 and AM-D4-8 |
| AM-D3-2 relied on `GetEffectiveRightsFromAclW`, which Microsoft documents as unreliable for this use | Replaced by the structural oracle (DD8-7) |
| D8 finding F8-12 stated the CPython versions wrongly | Corrected in the design |

## Remaining genuine blockers (none is an agent action)

| ID | Blocker | Who |
|---|---|---|
| B-D8-1 | Linux_Docker_Host full-checkout runs (BE-2 Linux leg, Linux security cases) | Owner |
| B-D8-2 | External_Review_Record | Owner or independent reviewer |
| B-D8-3 | Dedicated VM or restricted account for hook evidence | Owner |
| D2 B-1, B-6, B-8, hosting, domain, certificate, budget | Public deployment readiness. Not authorized by this work | Owner |


## Task-plan review remediation (TPR), recorded 2026-11-26

An independent review of `tasks.md` reported 31 findings: 4 critical (TPR-C-1 to TPR-C-4), 10 high (TPR-H-1 to TPR-H-10), 12 medium (TPR-M-1 to TPR-M-12) and 5 low (TPR-L-1 to TPR-L-5). The review text is not stored in this repository. The ids are used as given, and the TPR prefix keeps them apart from the architecture-review ids H-1, M-1 to M-7 and L-1 to L-7 above, which are unchanged. The design rules are in `design.md` D10.11 (TR-1 to TR-19, rows D10-AC-10 to D10-AC-30, inventory CSI-1 to CSI-7). The task changes are in `tasks.md`.

Status words. RESOLVED IN PLAN: the rule is written in `requirements.md`, `design.md` and `tasks.md`, and a mechanical check of the documents passes (see "Validation of this revision"). It does not mean implemented or verified. Every row is DESIGNED and UNVERIFIED for Requirement 3, because no Execution_Record exists for any rule. Every row is also not accepted until the owner records OA-00 (4.10). This remediation is documentation work and is not that acceptance. PH1-01 stays complete, and records E-201 to E-222 are unchanged.

| ID | Severity | Finding | Files changed | Task ids | Acceptance rows | Resolution | Status |
|---|---|---|---|---|---|---|---|
| TPR-C-1 | Critical | Linux verification dependency deadlock | `tasks.md`, `design.md` (D8-AC-4, D8-AC-6, D8-AC-7, D10.2 row 30, D10.11 TR-1), `requirements.md` (13.13) | PH1-04, PH1-08, PH1-09, PH1-10, PH1-18, PH2-01, PH7-09, PH7-09a, PH7-17, OA-02 | D10-AC-28, D8-AC-4, D8-AC-6, D8-AC-7 | Windows legs are autonomous completion rows and decide the boxes. Linux full-checkout legs are the deferred rows DLV-1 to DLV-4, `UNVERIFIED` until a `SUCCEEDED` record that names a Linux source exists, and a Windows result never sets one. PH1-08, PH1-09, PH1-10, PH1-18 and PH2-01 depend on no owner EVIDENCE item (OA-01 to OA-07e) and no deferred row, directly or through another task. The only owner items behind them are the GATE items OA-00 (all five tasks) and OA-08 (PH1-18 and PH2-01), which are decisions that start tasks. PH1-08 and PH1-09 require at least 30 Windows trials. PH7-17 runs every deferred row on S, so 13.12, 13.13 and 13.26 stay a mandatory final gate (RB-1, RB-3). | RESOLVED IN PLAN |
| TPR-C-2 | Critical | Exact release-candidate SHA integrity | `requirements.md` (14.16, 14.21, Glossary), `design.md` (DD9-2, OD-D9-1, D9-AC-1, D9.3, D10.10, D10.2 row 28, D10.11 TR-2), `tasks.md` | PH7-08, PH7-12, PH7-17, PH7-18, OA-09 | D10-AC-12, D9-AC-1 | The path rule over `docs/next-phase/**` and `tasks.md` is removed. An Evidence_Commit changes only the Evidence_Output_Set (plus the two final checkboxes), names S and is never S. Code, tests, configuration, tooling and Test_Inputs (task specifications, review hashes, the Execution_Index, inventories, the Threat_Model, the Kiro MCP configuration) make a new Release_Candidate. Evidence commits are verified separately by `check-evidence-commit`, the scan, the lint and the report lint. 14.16 and 14.21 are reconciled with design and tasks. | RESOLVED IN PLAN |
| TPR-C-3 | Critical | Missing security tests in the actual isolation gate | `tasks.md`, `design.md` (D10.11 TR-3, D10-AC-13) | PH1-12a (new), PH1-12, PH1-13, PH1-14, PH1-16, PH5-14, PH7-05 | D10-AC-13 | `gate-isolation` keeps the four original tests and the same command. It adds an examiner-identity group, an authorized root observer group and a distinct secondary-uid group, a committed manifest, and a counts file with expected, collected, executed and skipped counts. An empty group, a missing node id or a skipped test fails the gate. CI runs the same command. | RESOLVED IN PLAN |
| TPR-C-4 | Critical | Evidence recorder bootstrap defect | `requirements.md` (3.15), `design.md` (D10.11 TR-4, D10-AC-10, D10-AC-11), `tasks.md` | PH1-02 (recorder, first tooling task), PH1-02a (lint), PH1-03, PH7-08 | D10-AC-10, D10-AC-11 | PH1-02 creates `release_verify.py run -- <command>` with the process exit status, atomic records and `recorded_utc`. The lint (PH1-02a) was PH1-02 before the split. `ingest` keeps `source_recorded_utc` apart from `ingested_utc`, and the 5 s bound applies only to recorder records. PH1-01 stays completed bootstrap evidence (E-201 to E-222, `BOOTSTRAP`). | RESOLVED IN PLAN |
| TPR-H-1 | High | Windows permission assertion preservation | `requirements.md` (13.11), `design.md` (BE1-1, BE1-5, D3-AC-17, D8-AC-4, D10.11 TR-5), `tasks.md` | PH1-04 | D10-AC-14, D8-AC-4 | The POSIX assertion is preserved by equal `ast.dump`, with indentation excluded. The guard also fails on an early return, a skip or a replay or explain assertion that is moved under the POSIX branch. The Windows branch runs the replay and explain assertions first and fails after them. | RESOLVED IN PLAN |
| TPR-H-2 | High | Final security matrix sequencing | `tasks.md`, `design.md` (D10.11 TR-6, D8.11 PC-7, D8-AC-8, D8-AC-16) | PH7-05, PH3-04, PH5-14, PH5-15, PH5-17, PH7-10 | D10-AC-15 | PH7-05 depends on PH5-14, PH5-15, PH5-17 and PH7-10 and runs the whole extended gate: KT-1 to KT-8 for the vault key and, as KT-S, for a canary signing key, with FC, IS, CA and RI. Earlier results are development results and never evidence for S. | RESOLVED IN PLAN |
| TPR-H-3 | High | Phase checkpoint completeness | `tasks.md`, `design.md` (D9.6 RB-19, D10.11 TR-7) | PH7-17, OA-09, PH7-08 | D10-AC-16 | PH7-17 and OA-09 depend on the six checkpoints PH1-18, PH2-10, PH3-14, PH4-10, PH5-17 and PH6-12. `check-checkpoints` exits non-zero when one is missing, `FAILED` or unexplained `UNVERIFIED`. PH7-17 then starts nothing and the report lists RB-19. | RESOLVED IN PLAN |
| TPR-H-4 | High | Hook review sequencing | `tasks.md` | PH4-05, PH4-06, PH4-10, OA-05, OA-06 | D10-AC-17 | OA-06 follows PH2-07, PH4-05, PH4-06 and PH4-10. OA-05 depends on OA-04 and OA-06. The agent lists pinned hashes as `PENDING_REVIEW` and never approves them. | RESOLVED IN PLAN |
| TPR-H-5 | High | Owner-action dependencies | `tasks.md`, `design.md` (D10.11 TR-8) | PH4-08, OA-04, PH6-08, PH6-08a, PH6-09, PH6-09a, PH6-10, PH6-10a, OA-07a to OA-07e | D10-AC-17 | OA-04 depends on PH4-08. OA-07 is split into the registry review (OA-07a), the Texas text review (OA-07b) and one review per jurisdiction (OA-07c to OA-07e). Each jurisdiction has a retrieval and build task and a separate promotion task, and an unreviewed snapshot is never promoted to `ACTIVE`. | RESOLVED IN PLAN |
| TPR-H-6 | High | Official-source registry sequencing | `tasks.md` | PH6-06, PH6-05, OA-07a, OA-07b | D10-AC-17 | PH6-06 establishes the registry before any retrieval. PH6-05 now depends on PH6-06 and OA-07a. Retrieved material is `UNREVIEWED` and changes no rule value, finding or UI text until its review record exists. | RESOLVED IN PLAN |
| TPR-H-7 | High | Explicit maintainer approval | `requirements.md` (4.10), `design.md` (D9.6 RB-20, D10.8), `tasks.md` | OA-00, PH1-02 | D10-AC-17 | OA-00 is a GATE item that PH1-02 and, through it, every implementation task depends on. PH1-01 stays a completed read-only exception. The remediation is not the acceptance, and the status of OA-00 is `OPEN`. | RESOLVED IN PLAN |
| TPR-H-8 | High | Exact candidate and independent review | `tasks.md`, `design.md` (D9.4 VM-19, D10.11 TR-8) | OA-09, OA-01, PH7-17, OA-03, PH7-18 | D9-AC-12, D8-AC-27, D10-AC-17 | The order is OA-09, OA-01, PH7-17, OA-03, PH7-18, enforced by Depends on lines. VM-19 moves to PH7-18. D9-AC-12 and D8-AC-27 map to PH7-18 and OA-03. | RESOLVED IN PLAN |
| TPR-H-9 | High | Agent-runnable Linux verification | `tasks.md`, `design.md` (D10.11 TR-9) | PH7-09, PH7-09a (new), OA-02 | D10-AC-18 | PH7-09 holds the tooling and the Windows preparation. PH7-09a adds `linux-run`: a Git bundle copied into the Linux container file system with no bind mount, UI development dependencies from an offline cache, `--network none` for the run stage, and no `SUCCEEDED` before every step has succeeded. OA-02 stays the owner route. | RESOLVED IN PLAN |
| TPR-H-10 | High | Publication scan ordering | `tasks.md` (EG-1), `design.md` (D10.11 TR-4) | PH1-02, PH1-03 and every later task | D10-AC-26 | Every task except PH1-01 (already complete), PH1-02 and PH1-03 depends on PH1-03, directly or through another task (checked: 0 exceptions among the 104 other tasks). A disclosed scratch scan covers only the evidence commits of PH1-02 and PH1-03. The PH1-01 scan is preserved. This checkpoint was scanned by a scratch script before staging, and the production scanner is not implemented. | RESOLVED IN PLAN |
| TPR-M-1 | Medium | Missing design acceptance mappings | `tasks.md` (table "TPR-M-2 mapping") | PH7-14, OA-05, PH7-18, OA-03, PH5-09, PH7-04, PH7-17, OA-00, PH4-03 | D8-AC-24, D8-AC-27, D9-AC-12, D2-AC-12, D3-AC-14, D3-AC-16, D3-AC-18, D9-AC-10 | The five mappings that the review named are made, and the coverage check found two more unmapped rows: D3-AC-18 (mapped to OA-00 and PH4-03) and D7-AC-19 (superseded by AM-D7-3, so it has no task). | RESOLVED IN PLAN |
| TPR-M-2 | Medium | Requirement traceability and measurable criteria | `tasks.md`, `design.md` (D10.11 TR-13, D10-AC-29) | PH1-02, PH1-02a, PH1-09, PH1-12a, PH1-18, PH2-10, PH3-14, PH4-10, PH5-14, PH5-17, PH6-12, PH7-03, PH7-09a, PH7-10, PH7-12, PH7-17, PH7-18 | D10-AC-29 | 1.4, 1.5, 1.6, 1.7, 1.10, 1.11, 1.15, 1.16, 2.7, 2.10, 4.5, 4.7 and 14.4 are cited by tasks, each with a measurable rule: direct exit codes, accurate durations, skipped and deselected reasons, one record per execution, separate Windows and Linux rows, an actual network-none negative control, distinct uids, vault 0700 and socket checks, a grid-cap rejection with no subsampling, the four rollback fields and the Kiro attribution rows. | RESOLVED IN PLAN |
| TPR-M-3 | Medium | Single authoritative verification owner | `tasks.md` (Property ownership), PH1-03, PH2-03, PH2-08, PH7-04 | PH1-03, PH7-04, PH2-03, PH2-08, PH7-02 | D10-AC-30 | P-k belongs to PH1-03 and P-d to PH2-03. PH7-04 and PH2-08 add supplementary example checks and no second property test. PH7-02 checks that each property has exactly one test. | RESOLVED IN PLAN |
| TPR-M-4 | Medium | Signing-key secrecy | `requirements.md` (10.37), `design.md` (D8.11 PC-7, D8-AC-8, D10.11 TR-6, TR-10), `tasks.md` | PH1-05, PH1-12, PH3-04, PH3-06, PH7-04, PH7-05 | D10-AC-15, D10-AC-20 | Signing-key canaries run through KT-S and PC-7. ACL-K (the signing-key file) and ACL-T (the Trust_Store file) define the Windows checks. POSIX permission bits are never Windows evidence. | RESOLVED IN PLAN |
| TPR-M-5 | Medium | Secure file opening | `requirements.md` (13.30), `design.md` (D10.11 TR-10), `tasks.md` | PH1-04a (new), PH1-11, PH1-16, PH2-02, PH3-04, PH3-06 | D10-AC-19 | One production module does no-follow open, identity validation on the opened object, exclusive create and private-directory enforcement. Negative tests cover a symbolic link, a precreated file and a swap race on POSIX, and a junction and a reparse point on Windows. | RESOLVED IN PLAN |
| TPR-M-6 | Medium | Authentication before resource allocation | `requirements.md` (7.27), `design.md` (D10.11 TR-11), `tasks.md` | PH1-17, PH5-09, PH5-10, PH5-11 | D10-AC-21 | In the public profile a request is authenticated before a slot, a body read, a run slot, a replay namespace or an examination. The client address is the socket peer, and forwarded headers count only from a configured trusted proxy. Negative tests cover a spoofed header and rotating values. | RESOLVED IN PLAN |
| TPR-M-7 | Medium | Shared path containment | `design.md` (D10.11 TR-10), `tasks.md` | PH1-04a, PH1-16, PH2-02, PH6-02 | D10-AC-19 | PH1-16 and PH2-02 reuse the PH1-04a module and add no containment code. A source scan finds 0 other implementation. | RESOLVED IN PLAN |
| TPR-M-8 | Medium | Production ACL helper | `requirements.md` (13.30), `design.md` (BE1-4, D10.11 TR-10), `tasks.md` | PH1-05, PH1-06 | D10-AC-20 | The access-list reader is in the Core production module. The test calls the same function as `_workdir()`. A helper that exists only under `tests/` is not accepted. | RESOLVED IN PLAN |
| TPR-M-9 | Medium | CI provenance and test collection | `design.md` (D10.11 TR-12), `tasks.md` | PH5-14, PH7-08, PH7-11, PH1-12a | D10-AC-22, D10-AC-13 | `VK_COMMIT_SHA` equals `github.sha`, the image label, build argument and health `commitSha` are compared, and `collect-check` collects `tests/security`, `tests/sdk`, `tests/release` and the gate counts. An empty directory, a missing node id or pytest exit code 5 fails. | RESOLVED IN PLAN |
| TPR-M-10 | Medium | Report validation ordering | `design.md` (D9.4 VM-15), `tasks.md` | PH7-17, PH7-18, PH7-08 | D10-AC-12 | VM-15 is split: VM-15a runs at S without a report, VM-15b runs in PH7-18 after the report exists. | RESOLVED IN PLAN |
| TPR-M-11 | Medium | Same-file task conflicts | `tasks.md` (graph, Notes), `design.md` (D10.11 TR-19) | PH1-13, PH1-17, PH1-16, PH1-15, PH3-05, PH3-08 | D10-AC-30 | PH1-17 depends on PH1-13, PH1-16 depends on PH1-14, PH1-15 and PH1-17, PH3-05 depends on PH3-08. The validator finds 0 same-file conflicts in any of the 55 waves. | RESOLVED IN PLAN |
| TPR-M-12 | Medium | Historical bundle compatibility | `tasks.md`, `design.md` (D10.11 TR-14) | PH3-05, PH3-08, PH3-14 | D10-AC-23 | After each archive-validation change the five corpus Bundles and `golden.vkb` replay with an equal Verdict_Hash, `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, unchanged corpus hashes, and unsigned Bundles still accepted. | RESOLVED IN PLAN |
| TPR-L-1 | Low | Consolidated wording scan | `design.md` (D10.11 TR-15), `tasks.md` | PH1-03a (new), PH2-09, PH3-07, PH3-13, PH4-04, PH4-07, PH5-02, PH5-05, PH5-16, PH6-05, PH7-14 | D10-AC-24 | One `wording-scan` catalog (WS-1 to WS-8). Other tasks cite rule ids and add no scanner. | RESOLVED IN PLAN |
| TPR-L-2 | Low | Credential inventory consistency | `design.md` (D10.11 TR-16, CSI-1 to CSI-7), `tasks.md` | PH1-11, PH3-04, PH5-10, PH5-11, PH7-04 | D10-AC-25 | One authoritative inventory. No other table restates credential handling, and tasks cite CSI rows. | RESOLVED IN PLAN |
| TPR-L-3 | Low | Linux redaction fixtures | `design.md` (D10.11 TR-17), `tasks.md` | PH1-03 | D10-AC-26 | Automated redaction and scan tests use synthetic fixtures on every host. The Private_Original reproduction runs only on the authorized host and is `UNVERIFIED` elsewhere. | RESOLVED IN PLAN |
| TPR-L-4 | Low | Runtime patch requirements | `requirements.md` (13.29), `design.md` (D10.11 TR-18), `tasks.md` | PH1-05, PH5-14, PH7-09a, PH7-11 | D10-AC-27 | CPython 3.12.4 or later, or an owner-approved equivalent, is enforced in the production module, at image build, in CI and in the Linux verification container, and the full version is recorded. | RESOLVED IN PLAN |
| TPR-L-5 | Low | Owner decisions before affected tasks | `tasks.md` (OA-08), `design.md` (D9.6 RB-20) | OA-08, PH1-11, PH1-16, PH1-17, PH2-02 | D10-AC-17 | OA-08 is a GATE item for OD-D8-1 to OD-D8-4, and the tasks that consume them depend on it. An unresolved decision is a visible blocker (RB-20). | RESOLVED IN PLAN |

Requirement changes of this round: criteria 3.15, 4.10, 7.27, 10.37, 13.29 and 13.30 were appended, criteria 13.11, 13.13, 14.16 and 14.21 were changed in place, and the Glossary gained Test_Input, Evidence_Output_Set and Evidence_Commit. The "Numbering and amendment history" paragraph of `requirements.md` lists them.

Plan changes of this round. Tasks: 99 before and 107 now (106 mandatory and 1 optional, PH1-07), of which 1 is complete (PH1-01). Eight tasks were added by a split: PH1-02a, PH1-03a, PH1-04a, PH1-12a, PH6-08a, PH6-09a, PH6-10a and PH7-09a. PH1-02 now holds the recorder and the former PH1-02 content is PH1-02a. PH6-08 to PH6-10 now hold retrieval and build and the new "a" tasks hold promotion. Owner items: 10 before and 15 now (OA-00, OA-01 to OA-06, OA-07a to OA-07e, OA-08 to OA-10). Conditional deployment items: 9, unchanged. Waves: 40 before and 55 now. Blockers: RB-19 and RB-20 were added.

### Validation of this revision (2026-11-26)

Method. No specification validator exists in the repository or in Kiro's command line that this session could run, so the checks were scratch Python scripts that were run from a directory outside the repository and are not committed. They parse `tasks.md`, `requirements.md` and `design.md` with regular expressions. This is documentation checking and not an Execution_Record, and it implements none of the future scripts of PH1-02, PH1-02a, PH1-03 or PH7-15. The scripts checked: the task line format, field presence and unique ids and numbers; every `Depends on` id exists in the task or owner-item set; no cycle; every id in the waves block exists once and every dependency sits in an earlier wave; no two tasks of one wave name the same source file in their Objective; the explicit ordering rules of TPR-H-2 to TPR-H-9, TPR-L-5 and TPR-M-11; that the only owner items behind PH1-08, PH1-09, PH1-10, PH1-18 and PH2-01 are the GATE items OA-00 and OA-08, followed through the `Depends on` lines (TPR-C-1); that each of the 104 tasks other than PH1-01, PH1-02 and PH1-03 depends on PH1-03, directly or through another task (TPR-H-10); every criterion of `requirements.md` cited by a task or an owner item; every design acceptance row cited by `tasks.md`; table column counts in the three files; PH1-01 still ticked and the only ticked box; and the stale sentence "Every box is unchecked" removed. `git diff` confirmed that the PH1-01 block of `tasks.md` is byte-identical to HEAD.

| Check | Before (HEAD) | After |
|---|---|---|
| Tasks, mandatory, optional, ticked | 99, 98, 1, 1 | 107, 106, 1, 1 (PH1-01) |
| Owner items, conditional deployment items | 10, 9 | 15, 9 |
| Waves | 40 | 55 |
| Dependency cycles | 0 | 0 |
| Unknown ids in `Depends on` or in the text | 0 | 0 |
| Same-file conflicts inside one wave | 2 (see the note below the table) | 0 |
| Criteria of `requirements.md` cited by tasks or owner items | 280 of 293 | 299 of 299 |
| Design acceptance rows cited by `tasks.md` | 182 of 190 | 212 of 212 |
| Malformed table rows in the three files | 0 | 0 |

The "Before" column was produced by running the same scripts on copies of the three files at HEAD. The same-file check found 2 candidates in one wave there. PH1-13 and PH1-17 both name `core/src/verdictkit/api/server.py` in wave 1, which is the TPR-M-11 finding. PH6-02 and PH6-03 in wave 25 are a false positive, because PH6-02 names `core/src/verdictkit/` only to say that it edits nothing there. Both pairs are in different waves after this revision. The "Before" counts of criteria (280 of 293) and design rows (182 of 190) are the same run. Its other hard failures at HEAD, such as the stale status sentence and the missing ordering rules, are the findings themselves.

Publication scan (3.14). It was run before staging by a scratch script that is not part of the repository, because the permanent scan is task PH1-03 and is not implemented. The script read the local checkout path, the temporary directory path, the user-profile path, the user names and the host name at run time, and they are not written in any file. It was first run on a planted sample built in memory: 10 of 10 classes detected, 0 hits on a clean sample. Counts below are hits per class, never matched values.

| Scope | Added lines | Whole files compared with HEAD |
|---|---|---|
| `requirements.md`, `design.md`, `tasks.md` | 0 hits in all 10 classes | No file has more hits in any class than at HEAD. The hits that exist at HEAD are unchanged: the documented constructed example paths of `design.md` and the environment-variable placeholders of `requirements.md` |

The final counts for the register, the ledger and the staged blobs are recorded in the ledger subsection "Push of the PH1-01 record commit and the task-plan remediation" of `EXECUTION_EVIDENCE.md`.

### Owner decisions still open and blockers still outstanding

No owner record was written, inferred or assumed in this checkpoint. Every owner item below has the status `OPEN`.

| Item | What is open | Blocks |
|---|---|---|
| OA-00 | Owner acceptance of D8 to D10, including D10.11, and of the corrected task plan (4.10) | Every implementation task from PH1-02 |
| OA-08 | OD-D8-1 (key mechanism), OD-D8-2 (replay namespace), OD-D8-3 (default Approved_Root) and OD-D8-4 (upload slots and replay quotas) | PH1-11, PH1-16, PH1-17, PH2-02 |
| OA-08 | OD-D8-5, OD-D8-6, OD-D9-3 and OD-D9-6 are assumed by recommendation and stay visible | A decision that differs reopens PH1-07, PH1-09, PH7-11, PH7-16 |
| D10.8 | The open decisions of D2 to D9 that the table of D10.8 lists are not changed by this checkpoint | Per section |
| OA-02, PH7-09a | The Linux full-checkout rows DLV-1 to DLV-4. PH7-09a is not built, and OA-02 has no record | RB-1, RB-3, RB-13 at release |
| OA-03 | The External_Review_Record of the exact S, after PH7-17 | RB-4 and Local_Readiness |
| OA-04, OA-05, OA-06 | The contained environment, the Kiro captures and the renewed review of the pinned hook set | Automatic hook execution stays `UNVERIFIED` |
| OA-07a to OA-07e | The registry review and the independent reviews of the retrieved snapshots | Retrieval and promotion of regulatory snapshots |
| OA-01, OA-09 | The authorization of the push of S and of the dispatch, and the selection of S | PH7-17 |
| CD-01 to CD-09, OA-10 | Public deployment decisions. Not authorized by this work | Public_Deployment_Readiness |

## Scope freeze and owner decisions (2026-11-26)

Written after the task-plan remediation, and appended. It changes no text above it. The table "Owner decisions still open and blockers still outstanding" describes the state before the owner's decisions and is not edited. This section gives the state now. The records are in `docs/next-phase/OWNER_DECISIONS.md` and the design reading is D10.12. Nothing here is IMPLEMENTED or VERIFIED.

| Item | State now |
|---|---|
| OA-00 | `PROVIDED`, verdict `ACCEPTED_WITH_CONDITIONS`, covered commit `fff6db49fb6f7f51080ca4fdb5e0ee7c1d37a581` |
| OA-08 | `PROVIDED` for OD-D8-1 to OD-D8-4 (approved as designed). The recommendations for OD-D8-5, OD-D8-6, OD-D9-3 and OD-D9-6 are retained and visible. The total replay quota has no approved value (open item in the record). |
| OA-02 | `NOT_PROVIDED`. DLV-1 to DLV-4 stay `UNVERIFIED` and RB-1, RB-3 and RB-13 stay open until PH7-09a supplies a record that names a Linux source. |
| OA-01, OA-03, OA-04, OA-05, OA-06, OA-09 | `OPEN` |
| OA-10 | `OPEN`, a decision only |
| OA-07a to OA-07e, CD-01 to CD-09, PH1-07, PH6-01 to PH6-11 | `DEFERRED` by the scope freeze. Not queued, not implemented, not verified. |

The 31 findings keep the status `RESOLVED IN PLAN`. The scope freeze neither reopens nor verifies any of them.

Changes that the deferral made necessary beyond the items that the owner listed. Each keeps a security dependency or a release-integrity gate that a deferred task would otherwise have carried.

| Change | Reason |
|---|---|
| PH6-12 depends on PH3-14 and PH5-17, and cites 12.13 | It named only deferred tasks. Without a retained dependency it had no path to PH1-03 (EG-1) and ran before the code that it replays. |
| Row T8-1 names the baseline `tests/contract/test_blinding.py` | It cited only D6-AC-10 and D6-AC-11, which belong to the deferred PH6-01. Its status is unchanged. |
| PH3-12 classifies the Examination_Semantics id in the 2.0.0 event | PH6-11 carried that classification, and PH3-02 adds the id. D5-AC-18 needs an owner. |
| PH7-07 cites 2.9 and 2.12 and applies no `CA` to `ZZ` hunk | PH6-01 was the only task that cited 2.9 and 2.12 (the LLM fence), and PH7-07 runs the fence. California stays unsupported. |
| PH7-12 and D9-AC-13, D9-AC-19: the plugin manifest hash is `NOT_BUILT` and RP-9 is `NOT_APPLICABLE` | Both rows would otherwise demand a deferred artifact or invite an invented value. |
| KL-1 recorded (baseline entry-point loading in the public profile) | The owner asked for it. It is read from `core/src/verdictkit/cli.py`. No blocker row was added, because RB-16 and RB-17 stay open while CD-01 to CD-09 are deferred. |

Validation of the scope freeze (2026-11-26). Method: a scratch Python script run from a directory outside the repository, not committed. It parses `tasks.md` (task headers, `Depends on` lines, owner items, the wave list, the `_Requirements_` lines and the coverage table) and checks the following.

| Check | Result |
|---|---|
| Tasks in the file, queued, deferred, queued complete, queued remaining, queued optional | 107, 92, 15, 1, 91, 0 |
| Queued tasks per phase | PH1 21, PH2 10, PH3 14, PH4 10, PH5 17, PH6 1, PH7 19 |
| Owner items: in the graph, deferred, conditional items deferred | 10, 5, 9 |
| Nodes in the wave list, waves, contiguous wave ids | 102, 52, yes |
| Dependency edges checked, edges to a deferred item, wave-order violations, cycle members | 272, 0, 0, 0 |
| Queued tasks (other than PH1-01, PH1-02, PH1-03) that do not reach PH1-03 (EG-1) | 0 |
| Queued tasks (other than PH1-01, PH1-02) that do not reach PH1-02, which depends on OA-00 | 0 |
| PH7-17 and OA-09 depend on all six phase checkpoints | yes |
| Queued tasks that cite no criterion, or cite a deferred criterion | 0 |
| Coverage table rows that differ from the rows derived from the `_Requirements_` lines | 0 of 16 |
| Queued tasks that cite a criterion of Requirement 11, of Requirement 12 | 0, 6 |

Before the freeze the same parser read 107 tasks, 55 waves, 131 nodes in the wave list and 0 cycles, so the figures of the earlier plan are reproduced.