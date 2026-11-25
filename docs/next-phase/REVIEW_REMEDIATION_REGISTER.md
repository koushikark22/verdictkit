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