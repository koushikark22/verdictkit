# Owner decision records

Status: written 2026-11-26 (UTC date of the system clock). These records transcribe decisions that the repository owner stated in the request of 2026-11-26 that asked for the approval and the scope freeze. The agent made no decision and approved nothing. The text of the request is not stored in this repository, so every record below is attributed OWNER_STATED. Nothing in this file is IMPLEMENTED or VERIFIED. The plan reading of each decision is design section D10.12 and the section "Scope freeze" of `tasks.md`.

## OA-00 Owner acceptance of D8 to D10 and of the corrected task plan

| Field | Value |
|---|---|
| Identifier | OA-00 |
| Date | 2026-11-26 |
| Verdict | `ACCEPTED_WITH_CONDITIONS` |
| Branch | `feature/kiro-next-phase` |
| Covered commit | `fff6db49fb6f7f51080ca4fdb5e0ee7c1d37a581` |
| Accepted | Design sections D8 to D10 (including D10.11) and the corrected task plan at the covered commit, subject to the reduced enhanced-release scope below |
| Owner statement about the review | The independent final review confirms that all 31 task-plan findings (TPR-C-1 to TPR-L-5) are resolved, with no outstanding critical or high finding and no dependency cycle. The review text is not stored in this repository, and the agent has not verified this statement. |

Conditions of the acceptance:

1. The scope is the reduced enhanced-release scope of the section "Scope" below. Deferred items are never marked implemented or verified.
2. Requirement 4.9 is read as follows. The autonomous acceptance rows decide an autonomous task's completion. A deferred Linux verification row (DLV-1 to DLV-4) stays a mandatory release gate, stays `UNVERIFIED` until a `SUCCEEDED` record that names a Linux source exists, and is never represented as passed.
3. All prior evidence is preserved, and PH1-01 keeps its completed status.
4. Specification planning is frozen. No further broad specification refinement or architecture expansion is authorized. Implementation begins at PH1-02 in a Spec execution session.
5. Public deployment is not authorized. The known limitation KL-1 (baseline entry-point loading in the public profile, design D10.12) is recorded. If the retained plugin-loading behavior prevents secure public operation, public deployment stays blocked.
6. No security acceptance criterion is weakened, and the genuine security dependencies and the release-integrity gates are preserved.

SHA-256 of the three documents at the covered commit `fff6db49fb6f7f51080ca4fdb5e0ee7c1d37a581`:

| File | SHA-256 | Bytes |
|---|---|---|
| `.kiro/specs/verdictkit-next-phase/requirements.md` | `77bb7c1ed5bc0ea1172b519635421998dd3064e5f3b10465932498b866b8fdb0` | 126458 |
| `.kiro/specs/verdictkit-next-phase/design.md` | `00e299d1f1f4414b54a61f02f85f21d2256a90e6151e7d165051f2224cb3db35` | 639828 |
| `.kiro/specs/verdictkit-next-phase/tasks.md` | `8a133d4fe0ab1705943d1645bf37a77f61462db7c2712c3fa2a2b941a43ace13` | 256818 |

SHA-256 of the three documents as frozen, in the commit that holds this record (the scope-freeze commit). This is the text after the scope reconciliation that the acceptance names. A commit cannot contain its own id, so the id of that commit is named by the first ledger update after it.

| File | SHA-256 | Bytes |
|---|---|---|
| `.kiro/specs/verdictkit-next-phase/requirements.md` | `fb6859145a1b91cf21237966440c847f75ad56cbe0eea7a0debf46d57a0b9ead` | 129672 |
| `.kiro/specs/verdictkit-next-phase/design.md` | `3763f525ea166bcfbc39bc53cff1dc55664b7a5960fb2596b3c6ddb6b5f08e2c` | 647382 |
| `.kiro/specs/verdictkit-next-phase/tasks.md` | `dbd0b499177f9ca07345a299a80c08397ff4f9892fb2756a181f9b1264ef2853` | 266363 |

Method. Each value is the SHA-256 of the file as stored in the commit, read with `git show <commit>:<path>`, with LF line endings. A working copy that Git converted to CRLF (the working copy of `design.md` is one) gives another digest, so the check must read the committed blob. The two values of the covered commit were read twice by different routes and agree.

## OA-08 Maintainer decision records

The owner approved the designed defaults of OD-D8-1 to OD-D8-4 (design D8.15, section D10.12).

| Decision | Approved value | Design reference | Tasks that consume it |
|---|---|---|---|
| OD-D8-1 | The vault key is passed through the protected tmpfs key-file mechanism | DD8-2 | PH1-11 |
| OD-D8-2 | The replay namespace is a server-generated token of 32 hexadecimal characters | DD8-3 | PH1-16 |
| OD-D8-3 | The default MCP Approved_Root is the private working directory only | DD8-5 | PH2-02 |
| OD-D8-4 | 2 concurrent uploads and at most 64 MiB per replay | DD8-3, DD8-4 | PH1-16, PH1-17 |

The owner retained the documented recommendations for the following decisions. They are not decided, they stay visible, and a decision that differs reopens the task that names it.

| Decision | Retained recommendation | Task |
|---|---|---|
| OD-D8-5 | Run the timeboxed S-AUTHZ spike and adopt it only on exact agreement with O1. PH1-07 is deferred, so the spike is not run in this release and O1 stays the only BE-1 oracle (DD8-7). | PH1-07 (deferred) |
| OD-D8-6 | Run the `connect_ex` probe first, because it is the cheapest discriminator | PH1-09 |
| OD-D9-3 | Add a `windows-latest` job as extra evidence. The fresh-clone run on the owner's Windows host stays the Windows record. | PH7-11 |
| OD-D9-6 | "Runs the demonstration locally" means `serve` on a loopback port plus SM-1 and SM-7 (VM-12). `gate-http` alone does not start the service. | PH7-16 |

Open item, not decided by this record. The design (DD8-3, RI-7, RI-8) requires a per-replay byte quota and a total replay byte quota. The approved OD-D8-4 gives the per-replay value only. No value for the total replay quota appears in the design or in the owner's request, and the agent did not choose one. PH1-16 lists the missing value as an unresolved decision (RB-20) until the owner records it. The design allows at most 2 uploads in flight, each of at most 64 MiB, so 128 MiB would follow from the approved values. That figure is a suggestion for the owner and is not approved.

## OA-02 Linux_Docker_Host full-checkout runs

Status: `NOT_PROVIDED`. The owner supplies no separate owner-host Linux execution. This is not a waiver. The deferred Linux rows DLV-1 to DLV-4 stay `UNVERIFIED`, and RB-1, RB-3 and RB-13 stay open until PH7-09a, or a later record, supplies a `SUCCEEDED` record that names a Linux source and the commit. PH7-09a stays responsible for the actual Linux verification.

## Owner items that stay pending

OA-01 (authorization of each push of S and of the dispatch), OA-03 (External_Review_Record of the exact S), OA-04 (Contained_Hook_Environment), OA-05 (Kiro sessions in the disposable checkout), OA-06 (renewed review of the hook and MCP configuration) and OA-09 (selection of S) stay `OPEN`. No evidence or decision for them exists, and none was inferred. OA-10 (any tag, merge or publication) stays `OPEN` as a decision only, and no task depends on it.

## Scope

| Retained and queued | Deferred, not queued, not implemented, not verified |
|---|---|
| Phase 1 security remediation | PH1-07 (optional S-AUTHZ spike) |
| Phase 2 MCP hardening | PH6-01 to PH6-11, including PH6-08a, PH6-09a and PH6-10a (plugin SDK expansion, Texas completion, snapshot loader v2, California, Florida and New York adapters) |
| Phase 3 signed Bundles and signer trust | OA-07a to OA-07e (registry and snapshot reviews) |
| Phase 4 Kiro hooks and evidence tooling | CD-01 to CD-09 (public cloud deployment) |
| Phase 5 Judge UI and local deployment hardening | |
| PH6-12, the legacy replay checkpoint (P-g retained) | |
| Phase 7 final release verification | |

The existing Texas adapter and the supported historical replay stay intact. The reduced plan has 92 queued tasks (1 complete, 91 remaining), 10 owner items in the graph and 15 deferred tasks.

## Kiro credits

Kiro credits for this work: `NOT_AVAILABLE` (no Kiro usage record was read, criterion 16.2). The owner's request states that nearly 2,000 credits have been consumed in total. That statement is approximate, carries no unit, session identifier or request-identifier count, and is not a Credit_Record, so no figure is added to the usage tables (16.2, 16.5).
