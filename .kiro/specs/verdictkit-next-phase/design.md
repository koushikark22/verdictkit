# Design Document: VerdictKit Next Phase

## Document status

This design is complete in text. It has the seven canonical sections (Overview, Architecture, Components and Interfaces, Data Models, Correctness Properties, Error Handling and Testing Strategy), the foundations D0, the track designs D1 to D9 and the reconciliation D10. D1 (P0 UI/UX, decisions in D1.16), D2 (P1 secure public deployment, D2.12), D3 (P2 agent hooks and Windows compatibility, D3.13), D4 (P3 MCP, D4.12 and D4.13), D5 (P4 signing, D5.12 and D5.13), D6 (P5 plugin SDK, D6.11) and D7 (P6 regulatory verification, D7.11) are conditionally approved by the maintainer. D8 (P7 security and property testing, open decisions in D8.15) and D9 (P8 release verification, open decisions in D9.10) are written and await maintainer review. D10 and the canonical sections are the last part to be written and also await maintainer review. Nothing is IMPLEMENTED or VERIFIED: every statement about the future in this file is DESIGNED or DECIDED. The open decisions and the blockers that only the owner can clear are summarized in D10.8. The table of contents at the end of this file gives the status of every section. The final maintainer decisions of 2026-11-25 (OD-D9-1 and OD-D10-1 to OD-D10-4) are recorded in D10.10. The task-plan review remediation of 2026-11-26 (31 findings, TPR-C-1 to TPR-L-5) is recorded in D10.11. It is DESIGNED and UNVERIFIED. The owner recorded OA-00 as `ACCEPTED_WITH_CONDITIONS` on 2026-11-26 and froze the scope of the enhanced release (D10.12). D6 and D7 are DEFERRED except the Texas adapter and the replay semantics of AM-D7-3, and the acceptance changes nothing to IMPLEMENTED or VERIFIED.

## Overview

This design covers the next improvement phase of VerdictKit, the claim-autopsy engine in this repository. Work happens only on the Phase_Branch `feature/kiro-next-phase`, from the frozen baseline at commit `84df25c68198e496889b5892a03555ec7d2d860a`. The aim is a Release_Candidate in which every capability statement rests on a recorded run, the public surface is secure by construction, and each security claim is checked by a test that can fail. This file is the plan. No code, test, gate, key or infrastructure exists for it.

**Scope.** Nine prioritised tracks, each with a governing requirement and a design section. Requirements 1 to 4, 15 and 16 apply to every track.

| Track | Subject | Requirements | Design |
|---|---|---|---|
| P0 | Landing page, onboarding, UI_Kit modernization, accessibility | 5, 6, 7.1 to 7.4 | D1 |
| P1 | Secure public demonstration deployment | 7 | D2 |
| P2 | Agent hooks and Windows compatibility | 8 | D3 |
| P3 | MCP interoperability and diagnostics | 9 | D4 |
| P4 | Signed bundles and signer trust | 10 | D5 |
| P5 | Claim-plugin SDK | 11 | D6 |
| P6 | Expanded regulatory verification from official sources | 12 | D7 |
| P7 | Threat model, property and adversarial tests, BE-1 and BE-2 remediation | 13 | D8 |
| P8 | Integration and release verification | 14 | D9 |
| All | Baseline, invariants, evidence, track control, history, credits | 1 to 4, 15, 16 | D0, D8, D9, D10 |

**Status vocabulary.** DESIGNED: written here, with no code or test. DECIDED: a maintainer decision is recorded, and the decision is still only designed. IMPLEMENTED: code exists on the Phase_Branch and has not been run to a recorded result. VERIFIED: an Execution_Record with Outcome_Class SUCCEEDED exists for the current Release_Candidate (3.9). UNVERIFIED: not run, or run without captured evidence (3.4). The Outcome_Classes are SUCCEEDED, FAILED and UNVERIFIED. An Execution_Error is not an Outcome_Class. A credit figure is NOT_AVAILABLE unless it is read from a Kiro usage record (16.2). D0.1 defines the labels.

**Invariants.** Every track preserves these (D0.4): Decimal arithmetic (2.1), determinism (2.2, 10.7), answer-blind examination (2.3), Fail_Closed controls (2.4, 2.13), enforced Linux isolation (2.5 to 2.7, 2.14), offline replay (2.8), the LLM fence (2.9, 2.12), the Frozen_Release (1.2, 14.14) and honest evidence (3, 15, 16).

**The ten decisions that shape the design.**

| # | Decision | Governing record | Section |
|---|---|---|---|
| 1 | One Security_Profile, resolved by one function and checked in both processes. An unknown value or a conflict refuses start-up. | AM-D6-4 | D6.11, D8.12 |
| 2 | The vault key is never a process argument. It travels as a mode-0400 file on tmpfs that the custodian reads once. | DD8-2 | D8.3, D8.5 |
| 3 | Uploaded replay content never enters the trusted evidence root, and an upload takes a slot before its first body byte is read. | DD8-3, DD8-4 | D8.3, D8.5 |
| 4 | Isolation_Mode is fixed at start. The examiner serves only the `vk-custodian` account. | DD8-10, DD8-11 | D8.3, D8.5 |
| 5 | Signatures are Ed25519 in one envelope member. Signature validity, signer trust, integrity and verdict correctness stay four separate results, and unsigned bundles stay byte-identical. | D5.3, D5.4, AM-D5-1 to AM-D5-9 | D5 |
| 6 | The API contract moves to 2.0.0 in one lockstep change. One version is served, and bundles written under 1.1.0 keep replaying. | AM-D5-12, AM-D5-13 | D5.13 |
| 7 | Public plugin loading fails closed. Approval binds to Plugin_Provenance and not to a module name. | AM-D6-1 to AM-D6-3 | D6.11 |
| 8 | Official-source snapshots keep their bytes where the terms permit. A bundle records the Examination_Semantics under which it was produced, so older bundles keep replaying. | AM-D7-3, AM-D7-4 | D7.11 |
| 9 | Hooks count as evidence only from a Contained_Hook_Environment, with hash-pinned hook files and Kiro-captured artifacts. | AM-D3-1, AM-D3-7, DD8-15 | D3.13, D8.3 |
| 10 | One exact commit is verified on both host classes, with a no-loss rule and two separate readiness results. The agent never tags, merges, publishes or provisions. | D9.3, D9.8 | D9 |

**Out of scope.**

- Implementation, `tasks.md`, and the running of any test, gate or build.
- Cloud provisioning, spending, DNS records, certificates, a public listener and any announcement (D9.8).
- A push other than the Phase_Branch, a tag, a merge and a publication (14.13).
- Rule values for California, Florida and New York. No source was retrieved while writing this design (D7.1). Read-only retrieval is authorized for implementation by AM-D7-2.
- A plugin sandbox, online key revocation, MCP signing, dual contract serving, a replay queue, an ACL framework and a second evidence service (DD8-14).
- PDF text extraction (OD-D7-2), trusted timestamps (R-D5-2), image signing (D2.7) and a Linux Kiro session (B-H3).
- The content of an External_Review_Record or of a Kiro capture. Both are owner actions.

**How to read this file.**

- The canonical sections summarize and point. The decisions and the tests live in D1 to D9.
- Each track section has scope and status, inspected findings (F-n), design decisions (DD-n), acceptance rows, traceability and open items. D1 to D7 end with a decision record that governs the text it names.
- A later decision record governs the earlier text it names. D10.2 lists each case.
- Row identifiers: `AC-n` in D1.13, `Dn-AC-n` in D2 to D10, and the named matrices of D3, D5, D6, D8 and D9.
- D10 holds the reconciliation, the criterion-level traceability, the status ledger and the open items.

## Architecture

D0.2 holds the diagram of the baseline at `84df25c`. The diagram below shows the target state in the public profile, with the verification path and the readiness gates. Dashed borders mark components that are new or changed in this design. Every dashed element is DESIGNED.

```mermaid
flowchart TB
  subgraph EXT[Outside the image]
    CLIENT[Browser user or API client]
    OPS[Operator: vault key, credentials, signing key, Trust_Store, allowlist]
    OWNER[Owner: Kiro captures, review record, push authorization]
  end

  subgraph PUB[Public profile runtime]
    EDGE[Edge: TLS, headers, body caps, no retries, access policy]:::added
    subgraph IMG[API image: one task, no HA]
      ENT[Root entrypoint: resolves profile, writes key file, starts both children]:::added
      subgraph CUST[vk-custodian, uid 900]
        API[API_Server contract 2.0.0: ownership, admission, health]:::added
        LOAD[Profile resolver and plugin loader with provenance check]:::added
        SIGN[Signing, verification and Trust_Store reader]:::added
        MCPS[MCP_Server and CLI with the Approved_Root helper]:::added
      end
      subgraph EXA[vk-examiner, uid 901]
        WRK[Examiner worker: serves only the vk-custodian uid]:::added
      end
      SOCK[(Authenticated socket: profile and registry digest checked at start)]:::added
      KEYF[(Key file on tmpfs, mode 0400, read once, then removed)]:::added
      PROV[(Plugin provenance manifest: root-owned, read-only)]:::added
      VLT[(Vault and drafts, mode 0700)]
      EVT[(Trusted evidence root)]
      RPL[(Replay root: one namespace per replay)]:::added
    end
  end

  subgraph VER[Verification of one Release_Candidate S]
    WIN[Windows host: fresh clone of S]:::added
    LDH[Linux_Docker_Host: image, gates, end-to-end, replay matrix]:::added
    CI[CI: dispatch on the Phase_Branch, head SHA check]:::added
    LED[(Evidence_Ledger and release report)]
  end

  CLIENT --> EDGE
  EDGE --> API
  OPS -.supplies.-> ENT
  OPS -.supplies.-> SIGN
  ENT -.starts.-> API
  ENT -.starts.-> WRK
  ENT -.writes.-> KEYF
  KEYF -.read once.-> API
  API <--> SOCK
  SOCK <--> WRK
  API --> VLT
  API --> EVT
  API --> RPL
  WRK --> EVT
  WRK -.reads own namespace.-> RPL
  LOAD -.verifies.-> PROV
  MCPS --> LOAD
  LDH -.runs.-> IMG
  WIN --> LED
  LDH --> LED
  CI --> LED
  OWNER -.supplies.-> LED
  LED --> LOCALR[Local_Readiness]:::added
  LOCALR --> PUBLICR[Public_Deployment_Readiness]:::added
  GATES[SG-1 to SG-9, hosting decisions, rehearsed rollback, owner go decision]:::added
  GATES --> PUBLICR

  classDef added stroke-dasharray: 5 5,stroke:#b45309,color:#78350f;
```

**Process and trust boundaries in the public profile.**

| Boundary | What crosses | Control | Section |
|---|---|---|---|
| Client to edge | HTTPS requests | TLS ends at the terminator in front of the edge (Caddy on the VM path), HSTS at least 15552000 s, security headers on every response, size caps, no retries, same-origin routes, no CORS header, invitation credentials for case routes | D2.3, D2.5, D2.12 |
| Edge to API | Same-origin API calls on a port that only the edge can reach | The edge mounts no vault, draft, evidence or socket volume and holds no `VK_VAULT_KEY` | D2.3 |
| Requester to case | Case id and the `vk_owner` cookie | Ownership on every case route. A foreign requester gets the response of a nonexistent case. | D2.12 (AM-6), D8.9 |
| Root entrypoint to children | Closed environment lists, the profile, the key file | `setpriv --no-new-privs` and `env -i`. The key is a file and never an argument. The profile reaches both processes. | D2.2, D8.3, D6.11 |
| Custodian to examiner | Blinded task, examination result, profile, registry digest | Authenticated socket. The custodian checks the examiner uid. The worker serves only the `vk-custodian` uid. A profile or digest mismatch refuses start-up. | D8.3, D6.11 |
| Uploaded bundle to evidence | Bundle bytes and embedded evidence | A slot is taken before the first body byte. Embedded evidence goes to a replay namespace, never to the trusted root. Re-hash on read. Quotas. | D8.5 |
| Entry points to the loader | Installed distribution files | The allowlist applies before import. Provenance is verified before import. A mismatch refuses start-up. | D6.4, D6.11 |
| MCP path to the file system | A bundle path argument | The Approved_Root helper opens component by component and returns one fixed `PATH_NOT_ALLOWED` message. | D8.5, D4.5 |
| Operator to signer and verifier | Signing key file, Trust_Store file | The key is read only in the custodian. The verifier names the store and `as_of`. Verification is offline. | D5.5 to D5.7 |
| Regulatory sources to Quote_App | Retrieved bytes | Registry host, stored bytes, recomputed hash and a human review record | D7.5, D7.6 |
| Hook environment to evidence | Runner records and Kiro captures | Contained_Hook_Environment, hash-pinned hook surfaces, two-key attribution | D3.7, D3.8, D8.3 |
| Repository to published evidence | Records, logs and documents | Private_Original kept private, Sanitized_Copy published, zero-hit scan before a commit | D8.3 (DD8-9) |

**Verification architecture.** Each source is labelled in every record, and one source never stands in for another (DD9-7). A step that cannot run on a host class is UNVERIFIED there, with the reason (1.6, 14.4).

| Source | Role | Provides | Does not provide |
|---|---|---|---|
| Windows host, fresh clone of S | The Windows record | Lock check, sync, `ruff`, `pytest -rA`, Vitest, `npm` typecheck and build, native replay under a socket guard, the BE-1 Windows branch, the hook runner tests | Container gates, Browser E2E, `gate_nov22.sh`, the Linux-only cases |
| Linux_Docker_Host (the Docker Desktop Linux engine on the Windows host, or a Linux VM) | The container record | Image build, four gates, offline replay, the end-to-end scenario for three claim types, the replay matrix, the legacy corpus, the local demonstration, a Linux full checkout for BE-2 and the per-test baseline | The CI run and Kiro captures |
| CI (`ubuntu-latest`, dispatched on the Phase_Branch) | The Linux record of the workflow | Full-checkout `-rA`, Browser E2E, `gate_nov22.sh`, the skipped Linux cases, the head SHA check | A Windows result (a Windows job is OD-D9-3) |
| Owner | Actions the agent cannot take | Kiro hook and MCP captures, the External_Review_Record, push authorization, a Linux host, access to the Historical_Audit | Nothing is simulated for it |

**Release gate structure.** The two results are reported on separate lines and never combined (14.26). Blocker levels are LOCAL, PUBLIC and CLAIM (D9.6).

| Result | Requires | Section |
|---|---|---|
| Local_Readiness | Every LOCAL blocker clear on S, the evidence of Requirement 14 complete with every UNVERIFIED item listed, and the image running the demonstration locally on loopback | D9.6, D9.8 |
| Public_Deployment_Readiness | Local_Readiness, SG-1 to SG-9 each SUCCEEDED, recorded hosting, domain, certificate and budget decisions, monitoring, a rehearsed rollback and the owner's go decision | D2.8, D2.12 (AM-11), D9.8 |
| Capability statement | A SUCCEEDED Execution_Record for S. Otherwise the statement is UNVERIFIED. | D9.5, 3.9, 3.10 |

No design in this file authorizes a cloud resource, spending, a DNS record, a certificate, a public listener or an announcement. The documentation keeps saying that no hosted demonstration is available until an Execution_Record per 7.13 exists (7.14).

## Components and Interfaces

Every component maps to at least one requirement (4.2). Names marked "chosen at implementation" are not fixed by this design.

| Component | Responsibility | Interface | Contract or version | Track | Section | Req |
|---|---|---|---|---|---|---|
| API_Server | Same-origin HTTP boundary for cases, runs, evidence, bundles, replays and health | `/api/v1/*`. In the public profile: cookie `vk_owner`, 429 `RATE_LIMITED` with `Retry-After`, health 503 | Contract 2.0.0 (1.1.0 at the baseline) | P1, P4, P7 | D2.5, D2.6, D5.8 | 7.5 to 7.8, 7.23, 7.26, 10.21, 10.34 |
| Security profile resolver | Resolves `local` or `public` from `VK_PROFILE` and `VK_JUDGE_MODE` in one function, in both processes. Refuses an unknown value or a conflict. | Start-up. The custodian asks the examiner for its profile and a registry digest over the authenticated socket. | A `VK_STARTUP_ERROR` code and a non-zero exit (names chosen at implementation) | P5, P7 | D6.11 (AM-D6-4), D8.12 | 7.19, 11.16 |
| Key-file loader | Reads the vault key once from a custodian-owned mode-0400 file on tmpfs, validates owner and mode, removes the file | `VK_VAULT_KEY_FILE`. `VK_VAULT_KEY` in the environment stays for non-container runs. | Environment | P7 | D8.3 (DD8-2), D8.5 | 7.20, 13.16 |
| Peer authentication in the worker | Checks `SO_PEERCRED` on every connection against the uid of `vk-custodian`, closes other peers unread, sets the socket mode before the first accept, applies a read deadline | Unix socket in group `vk-ipc` | Fixed log codes | P7 | D8.3 (DD8-11) | 2.14 |
| Upload admission | Takes a slot before the first body byte, keeps one buffered copy, frees slow slots on a total body deadline and on disconnect | `VK_MAX_CONCURRENT_UPLOADS` (default 2, ASSUMED). 429 `RATE_LIMITED` with `Retry-After`. | Contract 2.0.0 (429 rows) | P7, P1 | D8.3 (DD8-4) | 7.21 |
| Replay namespace | Restores embedded evidence into a separate replay root, one namespace per replay (`^[0-9a-f]{32}$`), removed in `finally`, orphans swept at start, byte quotas | A server-generated namespace key that the examiner reads read-only | Internal | P7 | D8.3 (DD8-3) | 7.22 |
| Case ownership and access policy | Owner cookie, `case_owners` table, the same 404 for a foreign case, invitation credentials, no administrative route | Cookie `vk_owner`. Edge entries or an API-side table. `VK_OWNER_BINDING`, `VK_PUBLIC_ORIGIN`. | Contract 2.0.0 (cookie documented) | P1 | D2.5, D2.12 (AM-6, AM-7, AM-8) | 7.23, 7.24, 2.3 |
| Health and liveness | Public readiness with four checks and a six-field body. Internal liveness with no public route. | `GET /api/v1/health`. `python -m verdictkit.api --probe-live` (DESIGNED). | Contract 2.0.0 (`commitSha`, 503 body) | P1 | D2.6 | 7.13, 7.26 |
| Retention sweeper | Background expiry loop every 60 s. Never deletes a blob or a replay namespace that a live case or an examination in flight uses. | Internal loop, no HTTP route | Internal | P1, P7 | D2.5 (DD2-10), D2.12 (AM-9) | 7.11, 7.25 |
| Safe-open helper | One shared containment helper for the MCP tools, the scaffold destination and the replay scratch. Opens a file only inside an Approved_Root and checks type and size on the opened handle. | `VK_MCP_BUNDLE_ROOTS`. Error `PATH_NOT_ALLOWED`. Name chosen at implementation. | MCP error list | P3, P7 | D8.3 (DD8-5), D4.5 | 9.21, 11.6 |
| MCP_Server | Four tools, structured errors with `isError`, strict arguments, optional diagnostics | stdio. `list_claim_types`, `verify_claim`, `replay_bundle`, `explain_verdict`, and `server_diagnostics` only when `VK_MCP_DIAGNOSTICS=1`. `mcp` `>=2.3,<2.4`. | Tool surface frozen (D4.3). Contract 2.0.0 value in results. | P3 | D4.3 to D4.7 | 9.1 to 9.22 |
| CLI | Runs a claim, replays a bundle, scaffolds and checks plugins, starts the API | `verdictkit run`, `verdictkit replay [--allow-refetch] [--json] [--trust-store]`, `python -m verdictkit.sdk new` and `check`, `python -m verdictkit.api [--check-startup]` | Exit codes in Error Handling | P4, P5 | D5.8, D6.6, D6.7 | 10.20, 11.2, 11.7 |
| Signing and verification | Signs the manifest bytes with Ed25519 inside the custodian, verifies offline, builds one `authenticity_dict(...)` for the API, the CLI and MCP | `VK_SIGNING_KEY_FILE` (a path, never key bytes). New module `signing.py`. | Bundle member `signature/envelope.json`. Contract 2.0.0 fields. | P4 | D5.4 to D5.6 | 10.1 to 10.33 |
| Trust_Store reader | Evaluates ACTIVE, ROTATED and REVOKED keys and the validity interval against the verifier's `as_of` | `VK_TRUST_STORE_FILE`, `--trust-store`, optional `VK_TRUST_STORE_SHA256` | Format `vk-trust-store` 1 | P4 | D5.7 | 10.10 to 10.13, 10.16, 10.17, 10.27, 10.28 |
| Plugin loader and provenance | Lists entry points without importing, applies the public allowlist before import, verifies Plugin_Provenance before import, rejects every duplicate `type_id` | `sdk.loader.discover(policy)`. Allowlist constant. Provenance manifest built in the image. `PLUGIN_PROVENANCE_MISMATCH`. | `SDK_API_VERSION` 1 | P5, P7 | D6.4, D6.11 | 11.15 to 11.18 |
| Claim_Plugin_SDK | Scaffold, validation and the Conformance_Suite | `python -m verdictkit.sdk new <type_id> --dest <dir>`, `check <type_id> [--json]`, `run_suite(target, golden, registry)` | `ClaimType` Protocol unchanged | P5 | D6.5 to D6.7 | 11.1 to 11.14 |
| Rules v2 pipeline and loader | Fetch, verify, build, review, promote, freshness and gate for non-Texas jurisdictions. The loader reads snapshots with no network. | `scripts/rules_snapshot.py` (`fetch`, `verify`, `build`, `check-fresh`, `gate`). Loader in `rules_v2.py` and `sources_v2.py`. | Format `vk-rules/2`. The Texas tier is unchanged. | P6 | D7.3 to D7.8 | 12.1 to 12.20, 12.24 |
| Examination_Semantics selection | Records the semantics id in each new bundle and selects the semantics from the bundle alone on replay | Manifest key plus task key, or an adapter id (OD-D7-9) | `legacy-1` for a bundle with no id | P6, P4 | D7.11 (AM-D7-3) | 12.23, 10.5 |
| UI_Kit and web apps | Tokens, status badges, `DecimalText`, `ErrorPanel`, `AppShell`, `requestTimeoutMs`, and the landing workspace `apps/landing/web` | `ui-kit/src` components. npm scripts `typecheck`, `test`, `build`. | Reads contract 2.0.0 and refuses another major version | P0 | D1.3 to D1.12 | 5, 6, 7.1 to 7.4, 10.20 |
| Hook runner | One cross-platform runner for every hook, with a deadline, a run lock, output caps and an evidence record | `uv run --no-sync --offline python scripts/hooks/vk_hook.py <runner id>`, `--manual`, `verify-chain`, `record` | Exit codes in Error Handling | P2 | D3.3, D3.6, D3.7 | 8.1, 8.2, 8.5, 8.6, 8.10, 8.14, 8.18 |
| Hook matcher tests | Corpus and real-tree checks of the matchers, lint, command form and the hash pin of hook surfaces | `tests/contract/test_hook_matchers.py`, `test_hook_runner.py`, `hook_matcher_corpus.json` | Test files | P2 | D3.5, D3.13 (AM-D3-7) | 8.3, 8.4, 8.9, 8.17, 8.19 |
| BE-1 Windows helper | Structural access-list oracle O1 for the private directory of the MCP_Server, with an optional `AuthzAccessCheck` spike | Test helper under `tests/contract` or `tests/windows`. Errors `UNSUPPORTED_PYTHON_PATCH` and `PRIVATE_DIR_UNSAFE`. | Test code | P2, P7 | D3.9, D8.3 (DD8-6, DD8-7) | 13.11, 13.25 |
| Sanitizer and publication scan | Ordered exact-string rules, a rule-id and count manifest, and a zero-hit scan before a commit publishes evidence | Rules in `docs/next-phase/EVIDENCE_REDACTION.md`. Scan command chosen at implementation. | Redaction manifest | P7 | D8.3 (DD8-9) | 3.11, 3.14 |
| Ledger lint | Checks command fields, Execution_Index ids, counts and BE-2 wording | Lint command chosen at implementation (D8-AC-23). `release_verify.py report-lint` checks the release report. | Ledger format | P7, P8 | D8.5, D9.3 (DD9-10) | 3.12, 1.19 |
| Release verification procedure | Exact-commit runs on both host classes, the no-loss inventory, the enforced end-to-end scenario, the replay matrix, the CI run check, provenance and report lint | `scripts/release_verify.py` (`inventory`, `diff-inventory`, `check-run`, `frozen`, `provenance`, `report-lint`, `audit-scan`). `scripts/gate_e2e.py` through `gate-e2e <out_dir>`. Edits to `.github/workflows/p0-integration.yml`. | Standard library only | P8 | D9.3 to D9.5 | 14.1 to 14.27 |
| Threat_Model | One row per threat with its control and test id | `docs/next-phase/THREAT_MODEL.md`, built from D8.4 at implementation | Document | P7 | D8.4 | 13.1 to 13.3 |
| External_Review_Record reference | A reference to a review kept outside the repository | Evidence_Ledger entry of type `OWNER_ATTESTED` | Reference with the fields of D9-AC-12 | P7, P8 | D8.3 (DD8-13) | 13.27, 14.27 |
| Contract version constant | One dependency-free module that the server, the presenter and the MCP server read | `CONTRACT_VERSION`, value `2.0.0` | Lockstep list of D5.8 | P4 | D5.8, D5.13 | 10.21, 10.34 |

**External interfaces.**

| Surface | What changes | Compatibility | Section |
|---|---|---|---|
| HTTP | Contract 2.0.0, served alone. `AuthenticityReport` gains `signatureValidity`, `signerTrust`, `reasonCodes`, `signer` and `trustStore`. `Health` gains `commitSha` and the 503 `unavailable` body. The owner cookie is documented. 429 `RATE_LIMITED` gets `Retry-After`. The contract header is on every response. The D7 items `as_of`, the snapshot retrieval date and the Examination_Semantics id are classified in the same event. | BREAKING: the authenticity fields, the health body, and the owner cookie in the public profile (AM-D5-10). COMPATIBLE: the 429 rows and the contract header. Outside the contract: edge 401, 403 and 415. | D5.8, D5.13, D2.12 |
| MCP | Four tools unchanged by default. Optional `server_diagnostics`. `isError` and the error object `{code, message, tool}`. Strict arguments. `PATH_NOT_ALLOWED`. `replay_bundle` and `explain_verdict` return the `authenticity` object. | Frozen surface of D4.3, with the two exceptions of 9.1 | D4.3, D4.4, D8.5 |
| CLI | `verdictkit replay` prints validity, trust, authenticity and the fingerprint on separate lines. New `python -m verdictkit.sdk` and the liveness probe. | Exit rule of `replay` unchanged unless OD-D5-6 is accepted | D5.8, D6.6, D2.6 |
| File formats | `signature/envelope.json` in the bundle. Trust_Store `vk-trust-store`. Rules `vk-rules/2`, manifest and host registry. Plugin provenance manifest. Hook evidence JSON Lines. Test inventory files. | New members and files. Unsigned bundles and the Texas tier are unchanged. | D5.4, D5.7, D7.5, D6.11, D3.7, D9.4 |

**Environment variables added or changed.**

| Variable | Meaning | Section |
|---|---|---|
| `VK_PROFILE` | `local` (default) or `public`. `public`, or `VK_JUDGE_MODE=1`, selects public mode. | D6.11 |
| `VK_VAULT_KEY_FILE` | Path of the key file that the custodian reads once | D8.3 |
| `VK_OWNER_BINDING`, `VK_PUBLIC_ORIGIN` | Ownership binding (mandatory in the public profile) and the `https` origin for the CSRF rules | D2.5, D2.12 |
| `VK_MAX_CONCURRENT_UPLOADS` | Upload slots, default 2 (ASSUMED) | D8.3 |
| `VK_MCP_BUNDLE_ROOTS` | Approved_Root list. The private working directory is the default. | D8.3 |
| `VK_MCP_DIAGNOSTICS` | `1` registers `server_diagnostics` | D4.12 |
| `VK_SIGNING_KEY_FILE`, `VK_TRUST_STORE_FILE`, `VK_TRUST_STORE_SHA256` | Signing key path (custodian only), Trust_Store path, optional hash pin | D5.5, D5.7 |
| `VK_CLAIM_TYPES` | Existing. Refused in the public profile. | D6.4 |
| `VK_BRIDGE_CONNECT_TIMEOUT`, `VK_TEST_CLOSED_PORT` | BE-2: bridge connect timeout (default 1.0 s if H1 holds) and the closed port of the test | D8.5 |
| `VK_COMMIT_SHA` (build argument), `VK_IMAGE_DIGEST` | Commit and image identity on health and in bundles | D2.6 |
| `VK_BASE_LANDING`, `VK_BASE_QUOTE`, `VK_BASE_REEL`, `VK_*_DEV_PORT`, `VK_*_PREVIEW_PORT`, `VK_API_URL` | Build-time base paths and local ports | D1.3, D2.3 |
| `VK_HOOK_DEPTH`, `VK_HOOK_RUN_ID` | Hook runner loop guard and run identifier | D3.6 |

## Data Models

| Model | Fields | Canonical form or hash | Stored where | Compatibility label | Defined in |
|---|---|---|---|---|---|
| Bundle manifest | `engine_version`, `env_fingerprint`, `isolation_mode`, `data_mode`, `case_id`, `verdict_hash`, `files` (SHA-256 of every other member), `written_at` | Canonical JSON (`canonical_bytes`). The manifest bytes are the signed object. | `manifest.json` in the `.vkb` zip | An unsigned bundle is byte-identical to the baseline under the same Examination_Semantics (10.5). No format-version field. | D5.2 (F5-2), D5.4 |
| Signature envelope | `alg` (`ed25519`), `bundle_format` (`vkb/1`), `key_id` (SHA-256 of the 32 raw public-key bytes), `manifest_sha256`, `protocol` (`vk-bundle-sig`), `protocol_version` (`1`), `public_key` (64 hex characters), `signature` (128 hex characters) | Canonical JSON with exactly these keys, at most 2,048 bytes. Signing input: the tag `VerdictKit bundle signature v1`, one NUL byte, then the canonical bytes of the six signed fields. | `signature/envelope.json`, never listed in the manifest and the only member exempt from the unlisted-member rule | Additive member. Absent from unsigned bundles. | D5.4 |
| Examination_Semantics id | One identifier. `legacy-1` when a bundle records none. | Inside bytes that the integrity check covers. Assigned by the custodian, never by a claim. Reaches the examiner inside the task. | A manifest key plus a task key, or an adapter id (OD-D7-9, chosen at implementation) | A `legacy-1` bundle needs no new field and stays byte-identical. The field is contract-visible and is classified in the 2.0.0 event. | D7.11 (AM-D7-3) |
| Trust_Store | `format` (`vk-trust-store`), `format_version` (1), `serial`, `keys[]` with `key_id`, `public_key`, `status` (ACTIVE, ROTATED, REVOKED), `not_before`, `not_after` and an optional `note` | UTF-8 JSON, at most 262,144 bytes and 1,024 keys, closed schema, no BOM, duplicate keys and floats rejected. Optional pin `VK_TRUST_STORE_SHA256`. | Operator file. Read at each verification. | New format. A malformed store gives `NOT_EVALUATED`. | D5.7 |
| Rules snapshot v2 | A rule: family, `Decimal` value, window `[effective_from, superseded_on)`, authority class, status (VERIFIED, UNVERIFIED, AMBIGUOUS, UNSUPPORTED) and evidence ids | Canonical JSON, sorted lists, LF, no time read. Format `vk-rules/2`. | `rules/v2/<ID>.<seq>.json` under `apps/quote-autopsy/src/quote_autopsy/rules/` | New tier. `TX.json` and the legacy manifest entry are unchanged (DD7-1). | D7.3, D7.4 |
| Evidence record | `evidence_id`, `uri`, `retrieved_on`, `http_status`, `byte_count`, `sha256`, `media_type`, `excerpt`, `excerpt_sha256`, `rights`, `bytes_file`, and where permitted the final URI, response headers, effective dates and tool version | SHA-256 of the stored bytes, recomputed on load | Bytes at `rules/v2/bytes/<sha256>` when `REDISTRIBUTABLE`. Otherwise the hash and the excerpt only. | New. The retrieval date on the evidence DTO is classified in the 2.0.0 event. | D7.5, D7.11 (AM-D7-4) |
| Rules manifest and host registry | Manifest: `active` per jurisdiction, per snapshot its SHA-256, review file and hash and status (ACTIVE, SUPERSEDED, SUSPENDED, WITHDRAWN), the registry SHA-256. Registry: `jurisdiction`, `host`, `basis`, `reviewed_by`, `reviewed_on`. | Canonical JSON. The registry hash is pinned in the manifest. | `rules/v2/MANIFEST.json`, `rules/v2/official_hosts.json`, review record `<ID>.<seq>.review.json` | New | D7.5, D7.6 |
| Plugin allowlist entry and provenance manifest | Entry: distribution name, exact version, entry-point name, entry-point value, `provenance_sha256`. Manifest: for each allowlisted distribution, its installed files with SHA-256 (`RECORD` checked against disk, `__pycache__` excluded). | The SHA-256 of the manifest goes into release provenance and an image label | The allowlist is a code constant. The manifest is root-owned and read-only in the image. Kind `workspace-tree` is built. Kind `locked-wheel` is designed only. | New. No file or variable changes the allowlist. | D6.11 (AM-D6-3) |
| Execution_Record and Execution_Index | Record: exact command text, working directory, commit SHA, UTC timestamp, host, exit code, Outcome_Class, counts, Execution_Index id. A release record adds S, the step, and start and end times. | Counts come only from CANONICAL rows. Raw records are kept byte for byte with their SHA-256. | `docs/next-phase/EXECUTION_EVIDENCE.md`, `docs/next-phase/baseline/EXECUTION_INDEX.md` | Append-only in intent. A text correction goes to the corrections log. | Glossary, D8.5, D9.3 |
| Redaction manifest and hash table | Ordered exact-string rules with placeholders. Per rule: id and count, never a removed value. Per file: the Private_Original SHA-256 and the Sanitized_Copy SHA-256. | The Private_Original stays outside the published tree | `docs/next-phase/EVIDENCE_REDACTION.md`, `baseline/LOG_HASHES.txt`, `baseline/records.sanitized.jsonl` | One earlier application. History is not rewritten, and the residual is recorded. | D8.3 (DD8-9) |
| External_Review_Record reference | Record id, SHA-256 of the record, date, verdict (ACCEPTED, ACCEPTED_WITH_CONDITIONS, REJECTED), reviewed commit, hashes of the reviewed files, type `OWNER_ATTESTED` | A changed reviewed file voids the record | A reference in the Evidence_Ledger. The record is kept outside the repository. | New | D8.3 (DD8-13), D9-AC-12 |
| Hook evidence record | EV-1 to EV-10: identity, invocation, file, workspace, command, timing, result, output, host, and the chain fields `prev_sha256` and `record_sha256` | Canonical JSON per record. The chain is a consistency check and not authenticity (AM-D3-5). | `artifacts/hooks/evidence.jsonl`, JSON Lines, UTF-8, LF | New. The runner never writes an attribution. | D3.7 |
| Contract version constant | `CONTRACT_VERSION` = `2.0.0`, pinned in `api/openapi.yaml` (`info.version` and `ContractVersion`), the `ui-kit` constant, `api/examples/`, the MCP replay result and `ui/judge` | One dependency-free module. A test compares every pin. | The files named | BREAKING for strict 1.1.0 validators (AM-D5-10, AM-D5-12). Bundle format and contract are separate. | D5.8, D5.13 |
| Health body | `contractVersion`, `status` (`ok` or `unavailable`), `isolationMode`, `judgeMode`, `engineVersion`, `commitSha` | Exact key set, enforced by a test | `GET /api/v1/health` | `commitSha` and `unavailable` are BREAKING rows 2 and 3 | D2.6, D5.8 |
| Release provenance block | S, the image ID, the SHA-256 of `uv.lock` and of `package-lock.json`, tool versions, the host class of each run, the plugin provenance manifest hash, the contract version | Hashes of committed blobs (`git show <S>:<file>`) | `docs/next-phase/RELEASE_REPORT.md` | New | D9.5 |
| Test inventory | Sorted pytest node ids for each host class | SHA-256 of the file and of the raw output | `docs/next-phase/baseline/TEST_INVENTORY.windows.txt` and `TEST_INVENTORY.linux.txt` | New | D9.4 |

## Correctness Properties

The statements below are the correctness properties of the design. Each is a statement over all inputs of its kind, with the criteria it validates, the kind of test, the test identifiers, the host and the section that designs it. CP-n and the heading number are the same item. The CP numbers are new. They are distinct from the properties P1 to P17 of the core design, from P-a to P-o of D8.6 and from the track labels P0 to P8. Kinds: property (Hypothesis, `ci` profile), example (fixed or table-driven cases), scan (static or text scan) and gate (container gate or CI check). Every row is UNVERIFIED until an Execution_Record exists.

### Property 1: Decimal display identity

**CP-1.** For all decimal strings that the API_Server supplies for a money, rate or metric value, the digits that the UI_Kit displays equal the supplied digits, with no digit added, dropped or rounded and no binary float conversion outside `chartGeometry.ts`. Kind: example table and scan. Test: AC-7 (D1.13). Host: Windows and Linux. Section: D1.9.

**Validates: Requirements 5.6, 2.1**

### Property 2: Status fail-closed

**CP-2.** For all status values, known or unknown, the UI_Kit renders a non-empty text label, and an unknown value renders `UNRECOGNISED` with a neutral tone and never a positive one. Kind: example over the enums, with a mutation that removes the text. Test: AC-4, AC-15 (D1.13). Host: Windows and Linux. Section: D1.5.

**Validates: Requirements 5.4, 5.10, 2.4**

### Property 3: No verdict without an API outcome

**CP-3.** For all landing and onboarding states, a verdict is shown only if it is the verdict that the API_Server returned for that run. When the API_Server is unreachable or answers with an error, no verdict element is shown and the static content and both app links stay available. Kind: example with fake timers. Test: AC-10, AC-11, AC-12 (D1.13). Host: Windows and Linux. Section: D1.6, D1.8.

**Validates: Requirements 6.5, 6.8, 6.9**

### Property 4: Input retention except sealed claims

**CP-4.** For all failure states, every non-claimed input is retained. After the API_Server accepts a case, each sealed claimed-figure field is shown empty with a visible note, and no claimed figure is re-populated from any response. Kind: example. Test: AC-9, AC-12 (D1.13). Host: Windows and Linux. Section: D1.3 (DD-9), D1.8.

**Validates: Requirements 5.8, 6.9, 2.3**

### Property 5: No persistence of claimed values

**CP-5.** For all UI source files, no claimed outcome or pasted text reaches `localStorage`, `sessionStorage`, a cookie, a URL, console output or error text. Kind: scan. Test: AC-17 (D1.13). Host: Windows and Linux. Section: D1.11.

**Validates: Requirements 2.3**

### Property 6: Sweeper safety

**CP-6.** For all interleavings of put, deduplicated put, freeze, run start, purge, sweep and replay-namespace creation, the sweeper never deletes a blob or a replay namespace that a live case or an in-flight examination references, and a record that cannot be read or parsed makes it delete nothing. Kind: property (stateful, P-h). Test: D2-AC-28, D8-AC-21. Host: CI or VM. Section: D2.12 (AM-9).

**Validates: Requirements 7.25, 7.11, 13.17**

### Property 7: Case ownership

**CP-7.** For all routes that carry a case identifier and all requesters who do not own the case, the response equals, in status, body and headers, the response for a nonexistent case. Kind: example per route and a route-enumeration scan. Test: D2-AC-10, D2-AC-25, D8-AC-20 (CU-1 to CU-8). Host: CI or VM. Section: D2.12 (AM-6), D8.9.

**Validates: Requirements 7.23, 2.3, 13.17**

### Property 8: Credential policy

**CP-8.** For all invitation credentials, the stored record holds a hash and no credential value, a label, an expiry inside the demonstration window and a revocation flag. A revoked credential is rejected within the documented bound while every other credential stays valid, failed attempts are rate limited, and no route lists, decrypts or deletes cases. Kind: example and route scan. Test: D2-AC-26, D10-AC-1, D10-AC-2, D10-AC-3. Host: CI or VM. Section: D2.12 (AM-7).

**Validates: Requirements 7.24**

### Property 9: Health disclosure and readiness

**CP-9.** For all server states, `GET /api/v1/health` answers 200 only when the four readiness checks pass. Otherwise it answers 503 with the same body shape and `status` set to `unavailable`, refuses new runs and keeps `isolationMode`. The body holds exactly six fields, and each check result is reused for at most 5 s. Kind: example and key-set scan. Test: D2-AC-13, D10-AC-4, D10-AC-5. Host: CI or VM. Section: D2.6.

**Validates: Requirements 7.26, 7.13**

### Property 10: Headers on every response

**CP-10.** For all response classes of the edge and the API (200, 401, 404, 405, 413, 429, 500), the required security headers are present, including on early error returns. Kind: example. Test: D2-AC-5, SG-6, SM-4. Host: CI or VM. Section: D2.5 (DD2-5).

**Validates: Requirements 7.5, 7.6**

### Property 11: Key channels

**CP-11.** For all start-ups, a search for the vault key in raw, base64, hexadecimal and URL-encoded form finds 0 matches in any process argument list, in the environment of any process other than the custodian and the root entrypoint, in descriptors that the examiner inherits, in files that the `vk-examiner` user can read, in logs and in crash output. Kind: gate. Test: D8-AC-8 (KT-1 to KT-8). Host: Linux_Docker_Host. Section: D8.5.

**Validates: Requirements 7.20, 13.16**

### Property 12: Replay isolation

**CP-12.** For all replays, the file list and file hashes of the trusted evidence root are identical before and after, replay content is written only under the replay root, and the namespace is removed on exit, also after a failure. Kind: gate. Test: D8-AC-9 (RI-1 to RI-8). Host: Linux_Docker_Host. Section: D8.5.

**Validates: Requirements 7.22, 13.17**

### Property 13: Admission invariant

**CP-13.** For all sequences of concurrent upload requests, the bytes held for upload bodies never exceed the number of slots multiplied by the request cap plus 2 MiB, no body byte is read before a slot is taken, and a slot is released on disconnect and on error. Kind: property (P-i) and example. Test: D8-AC-10 (UA-1 to UA-8). Host: CI or VM. Section: D8.5.

**Validates: Requirements 7.21, 13.18**

### Property 14: Profile resolution

**CP-14.** For all combinations of `VK_PROFILE`, `VK_JUDGE_MODE` and an unrecognised value, profile resolution is total, no other variable turns `public` into `local`, and a profile or registry-digest mismatch between the custodian and the examiner refuses start-up. Kind: property (P-l) and gate. Test: D8-AC-19 (FC-3, FC-4), D8-AC-12 (PD-12). Host: CI or VM, Linux_Docker_Host. Section: D6.11 (AM-D6-4).

**Validates: Requirements 7.19, 13.24**

### Property 15: Isolation mode fixed at start

**CP-15.** For all combinations of profile, socket presence and examiner health, Isolation_Mode is read once at start. A configured examiner that fails a request fails that request closed with the mode unchanged and never serves it in the calling process, and the public profile refuses UNENFORCED. Kind: gate. Test: D8-AC-18 (IS-1 to IS-8). Host: Linux_Docker_Host. Section: D8.3 (DD8-10), D8.5.

**Validates: Requirements 2.13, 2.5, 13.24**

### Property 16: Custodian-only socket

**CP-16.** For all connecting uids, the examiner worker serves a connection only if the uid is that of `vk-custodian`, resolved by name at start, and closes every other connection unread. Kind: gate. Test: D8-AC-18 (CA-1 to CA-7). Host: Linux_Docker_Host. Section: D8.3 (DD8-11), D8.5.

**Validates: Requirements 2.14**

### Property 17: Fail-closed start-up

**CP-17.** For each start-up fault of FC-1 to FC-12, the process exits non-zero, prints a `VK_STARTUP_ERROR` line with a code, prints no `VK_STARTUP_OK`, opens no listener and writes no file. Kind: gate. Test: D8-AC-17, D2-AC-1. Host: Linux_Docker_Host. Section: D8.12.

**Validates: Requirements 13.24, 7.8, 7.10, 11.16**

### Property 18: Matcher classification

**CP-18.** For all tracked file paths and all path forms PF-1 to PF-7, the set of hooks that the Hook_Set matchers select equals the set that the reference function gives, and a search equals a full match. Kind: property over the real tree plus a corpus. Test: D3-AC-1 to D3-AC-3 (HM-T1 to HM-T4). Host: Windows and Linux CI. Section: D3.5.

**Validates: Requirements 8.3, 8.4**

### Property 19: Busy never validates

**CP-19.** For all hook outcomes other than PASSED, the outcome never maps to SUCCEEDED and never counts as validation. A save is validated only if every hook that the reference matcher assigns to it has a PASSED record. Kind: example (table-driven). Test: D3-AC-23. Host: Windows and Linux CI. Section: D3.13 (AM-D3-3).

**Validates: Requirements 8.1, 8.6, 8.11, 3.7**

### Property 20: Hook surface pinning

**CP-20.** For all additions, removals and changes of executable hook configuration (one changed byte, a new or removed hook file, a changed `enabled` value), the review of the changed surface is void and no hook evidence that depends on it counts until a reviewer other than the agent records a renewed review. LF and CRLF checkouts give the same hashes. Kind: example. Test: D3-AC-27, D3-AC-10, D10-AC-6. Host: Windows, Linux CI, Owner. Section: D3.8 (T-H1), D3.13 (AM-D3-7).

**Validates: Requirements 8.19, 8.17**

### Property 21: Attribution needs two keys

**CP-21.** For all hook executions, a firing counts as automatic execution only when the runner record, a Kiro-side artifact for the same hook and file path, the trusted-workspace state and the reviewed hashes agree (AT-1) inside a Contained_Hook_Environment. Otherwise the hook stays UNVERIFIED. Kind: example (table-driven) and owner review. Test: D3-AC-7, D8-AC-25. Host: Windows, Linux CI, Owner. Section: D3.7, D8.3 (DD8-15).

**Validates: Requirements 3.6, 3.7, 8.15, 8.20**

### Property 22: Read-only hook effect

**CP-22.** For all hook command runs, no tracked file and no git index entry changes, and every other write lies inside the documented allowlist. Kind: example (hashes before and after). Test: D3-AC-8. Host: Windows and Linux CI. Section: D3.3 (DD3-4).

**Validates: Requirements 8.6, 8.8**

### Property 23: BE-1 two-branch property

**CP-23.** For the private working directory of the MCP_Server, the POSIX assertion keeps its text and runs unskipped on every POSIX host. On Windows the directory has a protected access list with no inherited entry, only allow entries for the current user, OWNER RIGHTS, SYSTEM and Builtin Administrators, and none for Everyone, Authenticated Users, Builtin Users or Builtin Guests. Kind: example with negative controls and an AST guard. Test: D3-AC-17, D3-AC-22, D8-AC-4, D8-AC-5. Host: Windows, Linux_Docker_Host. Section: D3.9, D8.5.

**Validates: Requirements 13.11, 13.25, 2.11, 8.13**

### Property 24: Error model rule E1

**CP-24.** For all MCP tool calls, `isError` is true exactly when the result holds an `error` object with a code from the closed list. No verdict, including `INDETERMINATE` and `BLOCKED`, sets it. Kind: example matrix over stdio. Test: D4-AC-3. Host: Windows and Linux. Section: D4.4.

**Validates: Requirements 9.3, 9.13, 9.19, 9.20**

### Property 25: MCP error sanitizer

**CP-25.** For all MCP error results, the message has at most 500 characters and holds no host path separator taken from a file-system path, no exception text and no input value. Kind: property (P-d) and canaries. Test: D4-AC-4, D4-AC-9, D8-AC-2. Host: Windows and Linux. Section: D4.4.

**Validates: Requirements 9.3, 9.14, 13.5**

### Property 26: Approved_Root containment

**CP-26.** For all path strings that the MCP_Server receives, the helper opens a file only inside an Approved_Root or returns `PATH_NOT_ALLOWED`, and never opens a file outside every root. Kind: property (P-j), at least 20 cases and a race test of 1000 iterations. Test: D8-AC-11 (PR-1 to PR-23). Host: Windows and Linux. Section: D8.5.

**Validates: Requirements 9.21, 13.19**

### Property 27: Frozen MCP surface

**CP-27.** For all calls written against the pre-change tool list, the call and its success result fields pass unchanged, except the two exceptions of 9.1. Kind: example (snapshot). Test: D4-AC-1, D4-AC-2. Host: Windows and Linux. Section: D4.3.

**Validates: Requirements 9.1, 9.13**

### Property 28: Signature round trip

**CP-28.** For all Bundles produced by signing with a generated key, verification with a Trust_Store that holds the key gives `VALID`, `TRUSTED` and `ESTABLISHED`, with the reason `KEY_ROTATED` for a rotated key. Kind: property. Test: D5-AC-2, D5-AC-16. Host: Windows and Linux. Section: D5.9.

**Validates: Requirements 10.22, 10.28**

### Property 29: No single-byte change

**CP-29.** For all Bundles and all byte positions inside the manifest, a manifest-listed member or the signature envelope, changing one byte never yields `ESTABLISHED`, `VALID` or `REPRODUCED`. Bytes of the zip container that no check covers (timestamps, attributes, comments, extra fields) are outside this statement (F5-2, R-D5-4). The reading of 13.5(a) over those bytes is OD-D10-4. Kind: property (P-a) and exhaustive cases on the stub bundle. Test: D5-AC-5, D5-AC-16, D8-AC-2. Host: Windows and Linux. Section: D5.9.

**Validates: Requirements 10.15, 13.5**

### Property 30: Authenticity derivation

**CP-30.** For all combinations of signature validity, signer trust and integrity, `authenticity` is `ESTABLISHED` for exactly one combination (`VALID`, `TRUSTED`, integrity `VERIFIED`), and a failed result never changes the others. Kind: example (truth table). Test: D5-AC-8. Host: Windows and Linux. Section: D5.3.

**Validates: Requirements 10.9, 10.10, 10.13, 10.14, 10.17, 10.33**

### Property 31: Unsigned byte identity and hash independence

**CP-31.** For all cases and clocks, an unsigned Bundle is byte-identical to the baseline writer's output under the same Examination_Semantics, and the Verdict_Hash is equal with signing enabled and with signing disabled. Kind: property (P-b, P-c). Test: D5-AC-1, D5-AC-4, D8-AC-2. Host: Windows and Linux. Section: D5.4, D5.5.

**Validates: Requirements 10.5, 10.6**

### Property 32: Replay stability

**CP-32.** For all Bundles, two replays in the same environment give byte-identical reports whatever the clock and `PYTHONHASHSEED`, and a replay makes no network connection. Kind: property (P-f) and gate. Test: D8-AC-15 (DR-1 to DR-6), D5-AC-3, D5-AC-10, D5-AC-15. Host: Windows and Linux. Section: D5.9, D8.10.

**Validates: Requirements 13.22, 10.7, 2.8, 2.2**

### Property 33: Blinding

**CP-33.** For all claims that differ only in `outcome_fields` values, the blinded task serializations and the examination results are byte-identical. Kind: example (CS-03) and the existing blinding test. Test: D6-AC-1, D6-AC-10. Host: Windows and Linux. Section: D6.7.

**Validates: Requirements 2.3, 11.8**

### Property 34: Examination determinism

**CP-34.** For all claims, `examine` called twice, in one process and in child processes with different `PYTHONHASHSEED` values, gives identical canonical examination bytes. Kind: example (CS-04). Test: D6-AC-1, D6-AC-10. Host: Windows and Linux. Section: D6.7.

**Validates: Requirements 2.2, 11.9**

### Property 35: Loader order independence

**CP-35.** For all orderings of the same entry points, the loader registers the same claim types and rejects every registration that shares a `type_id`, so the result never depends on load order. Kind: property (P-m) and example. Test: D8-AC-12 (PD-1, PD-9), D6-AC-3. Host: Linux_Docker_Host, Windows and Linux. Section: D6.4, D6.11 (AM-D6-2).

**Validates: Requirements 11.17, 13.20**

### Property 36: Plugin provenance

**CP-36.** For all public-profile starts, an unlisted entry point is never imported. A plugin whose installed files, version, entry-point value or module origin differs from its Plugin_Provenance is refused with `PLUGIN_PROVENANCE_MISMATCH` and start-up stops. Kind: gate. Test: D8-AC-12 (PD-2 to PD-12), D6-AC-8, D6-AC-9. Host: Linux_Docker_Host. Section: D6.11 (AM-D6-1, AM-D6-3).

**Validates: Requirements 11.16, 11.18**

### Property 37: Scaffold conformance

**CP-37.** For all claim types that the scaffold generates with no edit, `run_suite` passes every check. Kind: property (P-e) and example. Test: D6-AC-2, D8-AC-2. Host: Windows and Linux. Section: D6.6, D6.7.

**Validates: Requirements 11.12, 13.5**

### Property 38: Window selection

**CP-38.** For all as-of dates and rule sets, exactly one rule applies at each boundary of a window, a date outside every window or inside a gap gives `rule_not_in_effect`, and two rules with different values give `conflicting_sources`. Kind: example (boundary table) and property. Test: D7-AC-4, D7-AC-3. Host: Windows and Linux. Section: D7.7.

**Validates: Requirements 12.19, 12.20**

### Property 39: Offline equality

**CP-39.** For all snapshot-backed examinations, a run in which every non-Unix connection is forbidden gives findings equal to an unrestricted run, and a changed byte in the snapshot, an evidence file, the review record, the host registry or the manifest never yields `SUPPORTED` or `REFUTED`. Kind: gate (connection guard) and example. Test: D7-AC-13, D7-AC-7. Host: Windows and Linux. Section: D7.6.

**Validates: Requirements 12.16, 12.7**

### Property 40: Historical replay

**CP-40.** For all Bundles of the legacy corpus produced at `84df25c`, replay with the Release_Candidate gives a Verdict_Hash equal to the recorded one and the status `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, never `DIVERGED` or `UNVERIFIABLE`. A Bundle that names an unknown Examination_Semantics id gives `UNVERIFIABLE`. Kind: property (P-g) and example. Test: D8-AC-15 (DR-5), D9-AC-8 (VM-9). Host: Windows and Linux. Section: D7.11 (AM-D7-3).

**Validates: Requirements 12.23, 13.22, 14.24**

### Property 41: Texas preservation

**CP-41.** For all Texas claims, the Verdict_Hash at the candidate equals the hash at `84df25c`, and the Texas files and tests differ from the baseline only by the approved fixture hunk. Kind: example and diff check. Test: D7-AC-1, D8-AC-29. Host: Windows and Linux. Section: D7.3 (DD7-1), D7.11 (AM-D7-1).

**Validates: Requirements 12.13, 12.21**

### Property 42: Official-source rule

**CP-42.** For all rule values, a value reaches `SUPPORTED` or `REFUTED` only if its source host is on the registry, the stored bytes contain the excerpt, the recomputed hash matches and a review record exists. Otherwise the finding is `INDETERMINATE`. Kind: example matrix. Test: D7-AC-5, D7-AC-6, D7-AC-7. Host: Windows and Linux. Section: D7.4, D7.5.

**Validates: Requirements 12.1, 12.3, 12.5, 12.7**

### Property 43: Sanitizer

**CP-43.** For all inputs, applying the sanitizer twice gives the output of applying it once, the output matches none of the defined sensitive classes, and a commit that publishes evidence is blocked on any hit. Kind: property (P-k) and scan. Test: D8-AC-22, D9-AC-20. Host: Windows and Linux. Section: D8.5.

**Validates: Requirements 3.14, 3.11, 13.23**

### Property 44: Canary non-leakage

**CP-44.** For all canary values, entry points and sinks, in raw, base64, hexadecimal, URL-encoded and JSON-escaped form, the canary does not appear in the sink's output, including a test's own failure message. Kind: property (P-n) and gate. Test: D8-AC-16 (PC-1 to PC-6). Host: Linux_Docker_Host. Section: D8.11.

**Validates: Requirements 13.23, 7.20**

### Property 45: Malformed archives

**CP-45.** For all malformed archive inputs of Z-1 to Z-16, the loader returns a rejection or `UNVERIFIABLE`, never `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID`, and writes no file outside the scratch directory. Kind: property (P-o) and example, with a mutation guard. Test: D8-AC-14. Host: Windows and Linux. Section: D8.7.

**Validates: Requirements 13.6, 13.21**

### Property 46: Ledger fidelity

**CP-46.** For all Execution_Records, the command text holds no ellipsis or placeholder, the record cites its Execution_Index id, the counts equal the canonical row, and no sentence states a cause for BE-2 before a diagnosis exists. Kind: scan. Test: D8-AC-23, D9-AC-20. Host: Windows and Linux. Section: D8.5.

**Validates: Requirements 3.12, 1.19, 1.14**

### Property 47: Exact commit

**CP-47.** For all verification runs of the release, `git rev-parse HEAD` equals S and `git status --porcelain` prints nothing before and after, every record carries the same S, and a new commit that changes a tested file starts a new Release_Candidate. Kind: example with a negative control. Test: D9-AC-1 (VM-1). Host: Windows and Linux. Section: D9.3.

**Validates: Requirements 14.16, 14.21**

### Property 48: No loss

**CP-48.** For all node identifiers collected at the baseline, the node is collected at S unless a recorded maintainer decision names it. Each node that passed or was skipped at the baseline passes or is skipped at S, and no selection flag hides a test. Kind: example with a negative control. Test: D9-AC-4 (VM-4). Host: Windows and Linux. Section: D9.4.

**Validates: Requirements 14.22, 13.9**

### Property 49: CI evidence

**CP-49.** For all CI runs used as evidence, `headSha` equals S, `headBranch` is the Phase_Branch, `event` is `workflow_dispatch` and `status` is `completed`. Otherwise the CI result is UNVERIFIED, and no pull request or merge is made to obtain a run. Kind: example with four negative controls. Test: D9-AC-9 (VM-10), D8-AC-26. Host: CI. Section: D9.3 (DD9-4).

**Validates: Requirements 14.20**

### Property 50: Readiness separation

**CP-50.** For all release reports, a level is `VERIFIED` only if no blocker of that level is open, Local_Readiness and Public_Deployment_Readiness are two separate lines, and no combined statement appears. Kind: scan with negative controls. Test: D9-AC-11, D9-AC-12, D9-AC-18. Host: Windows and Linux. Section: D9.6, D9.8.

**Validates: Requirements 14.26, 14.10, 14.27**

## Error Handling

Fail_Closed is the principle (2.4). An error or a missing input produces INDETERMINATE, UNVERIFIABLE or a rejection, and never SUPPORTED, CONSISTENT or WITHIN_BOUND. A failed control denies the guarded action, reports an error indication and leaves prior state unchanged. An infrastructure error is not an execution status: it is run state FAILED with an HTTP 5xx (`docs/API_CONTRACT.md`). A legitimate verdict, including INDETERMINATE and BLOCKED, is a result and not an error (9.19). A message never carries exception text, a file-system path, a claim value or key material (D4.4, D6.3, D8.5). The tables below collect the codes that the baseline code and the design define. No code is invented here, and a code whose name is chosen at implementation is marked so.

**HTTP.** `error.code` is an open string in `api/openapi.yaml` (`ErrorEnvelope`), so no `ErrorCode` list exists there. The values below are read from `api/server.py` at the baseline. The only closed list in the file is the set of `Blocker.code` values in the BLOCKED row.

| Code | Status | Meaning | Caller action | Section |
|---|---|---|---|---|
| `SCHEMA_INVALID` | 400, 422 | Invalid `Content-Length`, invalid JSON body, failed request validation, invalid draft update, unknown parameter, invalid `Last-Event-ID`. The intake boundary also returns it with a `field`. | Correct the named field and resend. Nothing changed. | D2.2, `docs/API_CONTRACT.md` |
| `BODY_TOO_LARGE` | 413 | JSON body over 256 KiB, or replay body over 8 MiB | Send a smaller body. Nothing is stored. | D2.5 (DD2-6) |
| `RATE_LIMITED` | 429 | Per-client limit (120 per minute), global run slots, a case or replay quota, or no upload slot. `Retry-After` is part of the design. | Wait for `Retry-After`. Never retry a POST or PATCH automatically. | D2.5 (DD2-6, DD2-7), D8.3 (DD8-4) |
| `NOT_FOUND` | 404 | The route, case, run, evidence or bundle is unavailable. Also the answer to a requester who does not own the case (7.23). | Treat as absent. Do not infer that the case exists. | D2.12 (AM-6) |
| `METHOD_NOT_ALLOWED` | 405 | The method is unavailable for the route | Use a documented method | Baseline |
| `HTTP_ERROR` | Framework status | Another framework rejection. No framework `detail` object is returned. | Read the status | Baseline |
| `STATE_CONFLICT` | 409 | The case is in the wrong state: already frozen, evidence already committed, or evidence needed before a run | Read the case state and follow the lifecycle order | Baseline |
| `POLICY_VIOLATION` | 422 | A bundled fixture claim cannot be edited, or an evidence class is not permitted | Change the input | Baseline |
| `TOO_EARLY` | 425 | No sealed verdict exists yet | Poll the run or the outcome later | Baseline |
| `CUSTODY_NOT_CONFIGURED` | 503 | Encrypted case custody is not configured | The operator sets the draft directory and the key | Baseline |
| `RUN_FAILED` | 500 | The run failed and produced no verdict. A lost or unauthenticated examiner fails the run closed. | Do not read it as a verdict. Check the run state. | D2.2 (F-3) |
| `BUNDLE_INTEGRITY` | 500 | A stored bundle failed its integrity check | Do not use the bundle | Baseline |
| `INTERNAL_ERROR` | 500 | An unexpected error, with no exception text | Report it. Do not retry blindly. | Baseline |
| BLOCKED response | 422 | A blocker stopped the case before examination. `executionStatus` is `BLOCKED` and there are no findings. Blocker codes: `SCHEMA_INVALID`, `MISSING_CRITICAL_PARAMETER`, `GRID_TOO_LARGE`, `PRIVACY_REJECTED`, `EVIDENCE_RIGHTS_UNVERIFIED`, `EVIDENCE_UNAVAILABLE`, `EVIDENCE_GAP`, `POLICY_VIOLATION`, `ISOLATION_NOT_ENFORCED`. | Resolve the named blocker | `docs/API_CONTRACT.md` section 2 |
| Health 503 | 503 | Designed. One of the four readiness checks failed. The body has the same shape with `status` set to `unavailable`, and never names the failed check. | Send no runs. Check health again later. | D2.6 |

**MCP.** The code list is closed (D4.4). Every error has `isError` true and the object `{code, message, tool}` with a message of at most 500 characters.

| Code | Meaning | Caller action | Section |
|---|---|---|---|
| `INVALID_ARGUMENT` | Wrong type, missing or unknown argument, `allow_refetch` not a JSON boolean, an empty or NUL-containing path | Fix the call | D4.4 |
| `UNKNOWN_TOOL` | The SDK reports an unknown tool. The name is not echoed. | Use a listed tool | D4.4 |
| `CLAIM_NOT_CANONICAL` | The claim is not an object, holds floats, NaN or duplicate keys, or is not canonical | Send a canonical claim with decimal strings | D4.4 |
| `CLAIM_INVALID` | `SchemaError`, or an unregistered claim type. The message names the field and never a value. | Correct the named field | D4.4 |
| `SIZE_LIMIT_EXCEEDED` | A claim over 262,144 bytes or a bundle over 8,388,608 bytes | Send a smaller input | D4.5 |
| `READ_ONLY_MODE` | `allow_refetch` is true while `VK_MCP_READONLY=1` | Do not request a refetch | D4.5 |
| `BUNDLE_NOT_FOUND` | The path is not a readable file. One message covers missing and unreadable. | Check the path | D4.4 |
| `BUNDLE_INTEGRITY_FAILED` | The file is not an intact bundle. The baseline `integrity` object stays at the top level. | Do not rely on the bundle | D4.4, D4.12 (AM-D4-3) |
| `ISOLATION_UNAVAILABLE` | A socket is configured but not authenticated, or `VK_EVIDENCE_DIR` is missing in socket mode | The operator repairs the isolation setup | D4.4 |
| `INTERNAL_ERROR` | Any other exception. The result carries `incidentId` and no exception text. | Report the incident id | D4.4 |
| `PATH_NOT_ALLOWED` | The path is relative, holds a NUL character, is a UNC or device path, names an alternate data stream, leaves every Approved_Root, or passes a link, junction or reparse point. One fixed message echoes nothing. | Use a path inside an Approved_Root | D8.3 (DD8-5), 9.21 |

**Start-up and exit codes.** A start-up fault stops the process before any listener opens.

| Output or code | Exit | When | Section |
|---|---|---|---|
| `VK_STARTUP_OK isolation=<mode>` | 0 | `--check-startup` prints it. In the public profile `serve` prints `isolation=ENFORCED` exactly once, before the first request. | Baseline, D2.5 (DD2-2) |
| `VK_STARTUP_ERROR=CONFIG_INVALID:VK_JUDGE_MODE` | 2 | `VK_JUDGE_MODE` is not the literal 0 or 1 | Baseline |
| `VK_STARTUP_ERROR=ISOLATION_NOT_ENFORCED` | 3 | Judge mode, and isolation is not ENFORCED | Baseline |
| `VK_STARTUP_ERROR=<exception class name>` | 3 | A start-up configuration or isolation error raised while the app is created | Baseline |
| `API dependencies unavailable` (standard error text) | 1 | An import failure | Baseline |
| `VK_STARTUP_ERROR=CONFIG_INVALID:VK_SIGNING_KEY_FILE` | 2 | `VK_SIGNING_KEY_FILE` is set but unusable. No unsigned bundle is written instead. | D5.5 |
| `VK_STARTUP_ERROR=plugin_loading_disabled` | Non-zero | `VK_CLAIM_TYPES` is set in the public profile | D6.4 |
| A `VK_STARTUP_ERROR` code (names chosen at implementation) | Non-zero | A missing or malformed vault key, an unknown profile, a profile conflict, UNENFORCED in the public profile, a missing examiner, a wrong examiner uid, a wrong socket mode, unavailable peer credentials, a failing allowlisted plugin, an invalid evidence directory, an unreadable provenance manifest, `PLUGIN_PROVENANCE_MISMATCH`, or a profile or registry-digest mismatch. No `VK_STARTUP_OK`, no listener, no written file. | D8.12 (FC-1 to FC-12), D6.11 |
| `VK_MCP_STARTUP_ERROR=VERSION_UNAVAILABLE` | 3 | The package metadata is missing | D4.6 |
| `PRIVATE_DIR_UNSAFE` | The MCP_Server refuses to start | The private working directory fails its access-list check on Windows | D8.3 (DD8-6) |
| `UNSUPPORTED_PYTHON_PATCH` | The Windows check fails and is not skipped | CPython 3.12.0 to 3.12.3 on Windows | D8.3 (DD8-6) |

**Bundle, replay and authenticity results.**

| Field | Values | Meaning | Caller action | Section |
|---|---|---|---|---|
| `integrity` | `VERIFIED`, `FAILED` | Members match the manifest, the ledger chain, the commitment and the spec hash | On `FAILED` do not re-execute and do not rely on the bundle | D5.3 |
| `reproducibility` | `REPRODUCED` | The replay gives the recorded verdict hash and the environment fingerprint is equal | Accept | D5.3, D9.4 |
| | `REPRODUCED_ACROSS_ENV` | The verdict hash is equal and the environment differs (engine, Python or lock hash) | Accept as reproduced and read `envMatch`. Expected for a legacy bundle (OD-D9-2). | D9.4 (VM-9) |
| | `DIVERGED` | Integrity is `VERIFIED` and the verdict hashes differ | Treat as a failed replay | D8.10 (DR-6) |
| | `UNVERIFIABLE` | A malformed or unsafe bundle, failed integrity, an unknown data mode, an unknown Examination_Semantics id, or a failed examination | Do not rely on the bundle | D7.11 (AM-D7-3) |
| | `NOT_RUN` | Bundle metadata before any replay | Replay to obtain a result | D5.3 |
| `signatureValidity` | `UNSIGNED`, `VALID`, `INVALID`, `UNSUPPORTED_ALGORITHM` | Whether the signature verifies. `UNSIGNED` is not an error and not tampering. | Do not trust an `INVALID` signature. An unsigned bundle is never called authenticated. | D5.3 |
| `signerTrust` | `NOT_EVALUATED`, `TRUSTED`, `UNTRUSTED_SIGNER` | Whether the verifier's Trust_Store accepts the key at `as_of` | Supply or repair the Trust_Store | D5.3, D5.7 |
| `authenticity` | `NOT_ESTABLISHED`, `ESTABLISHED` | `ESTABLISHED` only for `VALID`, `TRUSTED` and integrity `VERIFIED`. It says nothing about verdict correctness (10.33). | Read the four results separately | D5.3 |

**Signature reason codes.** The lists are closed and are sorted in every output (D5.3). A reason is a fixed string and never holds input text.

| Group | Codes | Meaning | Caller action |
|---|---|---|---|
| Validity, structure | `NO_ENVELOPE`, `ARCHIVE_UNREADABLE`, `DUPLICATE_ARCHIVE_PATH`, `UNKNOWN_SIGNATURE_MEMBER`, `ENVELOPE_LISTED_IN_MANIFEST`, `ENVELOPE_TOO_LARGE`, `ENVELOPE_MALFORMED`, `ENVELOPE_NON_CANONICAL` | `NO_ENVELOPE` gives `UNSIGNED`. The others give `INVALID`: the archive or the envelope is not in the one canonical form. | Reject the signature. Do not repair the bundle. |
| Validity, support | `ALGORITHM_UNSUPPORTED`, `PROTOCOL_UNSUPPORTED`, `BUNDLE_FORMAT_UNSUPPORTED` | `UNSUPPORTED_ALGORITHM`. The verifier lacks the means, and the signature is not shown to be forged. | Verify with a newer verifier |
| Validity, key and math | `KEY_ID_MISMATCH`, `PUBLIC_KEY_SMALL_ORDER`, `SIGNATURE_MALFORMED`, `MANIFEST_HASH_MISMATCH`, `SIGNATURE_MISMATCH` | `INVALID`. The key id, key, signature or manifest hash is wrong. | Treat the bundle as altered or forged |
| Trust, store | `TRUST_STORE_NOT_CONFIGURED`, `TRUST_STORE_UNREADABLE`, `TRUST_STORE_INVALID`, `TRUST_STORE_UNSUPPORTED_VERSION`, `TRUST_STORE_HASH_MISMATCH` | `NOT_EVALUATED`. Validity and integrity are reported unchanged, and the result is never `TRUSTED`. | Supply a valid store |
| Trust, key | `KEY_NOT_IN_TRUST_STORE`, `KEY_REVOKED`, `KEY_ROTATED`, `KEY_NOT_YET_VALID`, `KEY_EXPIRED` | `UNTRUSTED_SIGNER`, except `KEY_ROTATED`, which is `TRUSTED` with the reason | Replace the key or update the store |
| Authenticity | `INTEGRITY_NOT_VERIFIED` | `NOT_ESTABLISHED` because integrity failed | Do not rely on the bundle |
| Signing key, at creation | `SIGNING_KEY_MISSING`, `SIGNING_KEY_UNREADABLE`, `SIGNING_KEY_UNSUPPORTED`, `SIGNING_KEY_PERMISSIONS` | Bundle creation aborts. No `.vkb`, no ledger change and no key material in any output. | The operator fixes the key file |

All of these are defined in D5.3 and D5.5.

**Rules finding reasons.** A reason code accompanies an `INDETERMINATE` finding. An evidence-level code means that no snapshot is created from the failed step.

| Code | Meaning | Section |
|---|---|---|
| `unsupported_jurisdiction` | No `ACTIVE` snapshot for the jurisdiction. No evidence item. | D7.4 |
| `evidence_unavailable` | Evidence missing or refused at acquisition for a supported jurisdiction | D7.4 |
| `evidence_integrity` | Evidence reached the examination and failed its own check | D7.4 |
| `rule_unverified` | The rule is UNVERIFIED: host not official, status or timeout failure, an error page, excerpt absent, unsupported media type, no effective date, bytes not stored, guidance only, or identical bytes under two URIs | D7.4 |
| `conflicting_sources`, `rule_ambiguous` | Two readings, or two BINDING_LAW sources that disagree. Both excerpts are cited. | D7.4 |
| `missing_filing:<id>` | The rule needs a filing that VerdictKit cannot obtain. Never REFUTED. | D7.4 |
| `as_of_date_required`, `rule_not_in_effect` | No as-of date, or the date is outside every window or inside a gap | D7.4, D7.7 |
| `unknown_locality` | A stated locality is absent from the table | D7.9 (D7-AC-11) |
| `requires_regulator_filing`, `not_applicable_lease_tax_model` | Existing codes, unchanged | D7.4 |
| `HOST_NOT_OFFICIAL`, `media_type_unsupported`, `source_bytes_not_stored`, `source_changed`, `source_changed_since_snapshot` | Retrieval and verification results | D7.5, D7.6, D7.8 |

**Plugin loader and SDK.**

| Code or exit | Meaning | Caller action | Section |
|---|---|---|---|
| `ENTRY_POINT_LOAD_FAILED`, `NOT_A_CLAIM_TYPE`, `TYPE_ID_INVALID`, `TYPE_ID_RESERVED`, `TYPE_ID_DUPLICATE`, `SCHEMA_VERSION_INVALID`, `FIELDS_INVALID`, `SDK_API_UNSUPPORTED` | The entry point or object is rejected. One standard-error line `VKPLUGIN v1 code=<CODE> ep=<name> dist=<name>`. Local mode continues. In public mode a failure of an allowlisted plugin refuses start-up. | Fix the plugin | D6.4, D6.5 |
| `PLUGIN_NOT_ALLOWLISTED`, `PLUGIN_LOADING_DISABLED` | Public mode counted an unlisted entry point and never imported it. `VK_CLAIM_TYPES` in public mode refuses start-up. | Remove the variable | D6.4 |
| `PLUGIN_PROVENANCE_MISMATCH` | The installed files, the module origin or the top-level name differ from the Plugin_Provenance. The plugin is refused and public start-up stops. | Rebuild the image from the locked tree | D6.11 (AM-D6-3) |
| Conformance check ids CS-01 to CS-10 | A failed check names the check and the field and never a claim value. `NO_VALID_OUTCOME_VARIANT` means CS-03 could not derive a valid outcome variant. | Correct the claim type, or decide the variant rule (R-D6-3) | D6.7 |
| `python -m verdictkit.sdk new` | 0 success. 2 invalid identifier or usage. 3 destination not empty. 4 destination forbidden. 5 input or output error. | Read the message, which names the identifier and the rule | D6.6 |
| `python -m verdictkit.sdk check` | 0 all checks pass. 1 a check failed. 2 usage. 3 the type cannot be loaded. | Read the failed check | D6.7 |

**Hook runner outcomes.** Only PASSED validates a save (AM-D3-3). A hook that Kiro did not run is NOT_VALIDATED, and a missing record is reported and never omitted.

| Outcome | Exit | Meaning | Ledger mapping | Section |
|---|---|---|---|---|
| PASSED | 0 | The child exited 0 | SUCCEEDED for the command, never for automatic execution (DD3-10) | D3.6 |
| FAILED | The child's code, 1 to 123, except the reserved codes | The child exited non-zero | FAILED | D3.6 |
| BUSY_TIMEOUT | 75 | The run lock was not obtained in time | Execution_Error, NOT_VALIDATED | D3.6, D3.13 |
| RECURSION_BLOCKED | 76 | `VK_HOOK_DEPTH` was 1 or more | Execution_Error, NOT_VALIDATED | D3.6 |
| RUNNER_ERROR | 70 | A runner fault | Execution_Error, NOT_VALIDATED | D3.6 |
| CONFIG_ERROR | 78 | An unknown runner id or a bad state directory | Execution_Error, NOT_VALIDATED | D3.6 |
| TIMEOUT | 124 | The runner deadline was reached and the process tree was killed | FAILED, NOT_VALIDATED | D3.6 |

**Command exit codes.**

| Command | Exit codes | Section |
|---|---|---|
| `verdictkit run` | 0 on success. 1 on a usage error, an unknown data mode, a failed run or a failed bundle write. With signing enabled and an unusable key, the run aborts and writes no bundle. | Baseline, D5.5 |
| `verdictkit replay` | 0 only for a reproduced status (`REPRODUCED` or `REPRODUCED_ACROSS_ENV`) with integrity `VERIFIED`. 1 otherwise, with `REPLAY FAILED` on standard error. OD-D5-6 would add exit 1 for an `INVALID` signature. | Baseline, D5.8 |
| `python -m verdictkit.api` | 0 success. 1 dependencies unavailable. 2 invalid `VK_JUDGE_MODE`. 3 isolation not enforced or a start-up error. | Baseline |
| `python -m verdictkit.mcp_server` | 0 within 5 s after standard input closes. 3 with `VK_MCP_STARTUP_ERROR=VERSION_UNAVAILABLE`. | D4.6, D4.7 |
| Container gates | 0 only on pass | D9.4 |
| `release_verify.py check-run` | 0 only when the run record passes the checks of D9-AC-9 | D9.4 |

**Evidence statuses.**

| Value | Meaning | Section |
|---|---|---|
| SUCCEEDED, FAILED, UNVERIFIED | The Outcome_Classes. SUCCEEDED needs a recorded exit code 0 from a run in this phase. | Glossary |
| Execution_Error | A runner fault with no command result. It is not a test failure and not an Outcome_Class. | Execution_Index |
| NOT_VALIDATED | A save whose assigned hook has no PASSED record | D3.13 (AM-D3-3) |
| NOT_AVAILABLE | A credit figure with no Kiro usage record | 16.2 |
| Blocker levels LOCAL, PUBLIC, CLAIM | What an open blocker stops: Local_Readiness, Public_Deployment_Readiness, or only a capability statement | D9.6 |

## Testing Strategy

This section summarizes how the design is tested. The rows and thresholds live in D1 to D10. Every test is UNVERIFIED until an Execution_Record exists.

**Layers.**

| Layer | What it covers | Where | Hosts | Section |
|---|---|---|---|---|
| Unit | Python modules and UI components | `tests/` with pytest. Vitest in `ui-kit` and the apps. | Windows, Linux | D1.13, D6.9 |
| Contract | API schema and examples against `api/openapi.yaml`, the MCP tool surface, the hook matchers | `tests/contract`, `tests/api` | Windows, Linux | D4.10, D5.10, D3.10 |
| Property | CP-1 to CP-50 and P-a to P-o | Hypothesis, `ci` profile | Windows, Linux | Correctness Properties, D8.6 |
| Adversarial | Malformed archives, signature vectors, path cases, plugin discovery | `tests/adversarial`, `tests/security` | Windows, Linux. Plugin cases in the container. | D8.7, D8.8 |
| Integration | Texas and regulatory snapshots, the stdio MCP client, the scaffold end to end | `tests/integration` | Windows, Linux | D4.7, D7.9 |
| Container gates | `gate-isolation`, `gate-startup`, `gate-http`, `gate-case`, offline replay, `gate-e2e` | The image, with `--network none` | Linux_Docker_Host | D9.4 |
| Browser E2E | `scripts/ui_e2e.sh` with Playwright | Linux only | CI | D1.13 |
| Accessibility | axe-core scans and manual checks | jsdom units, browser scans in CI | Windows, Linux, CI | D1.10 |
| Owner-run Kiro | Hook firing and MCP calls from inside Kiro | A Contained_Hook_Environment | Owner | D3.8, D4.8 |

**Hosts.** The sources and what each provides are in the Architecture section. A step that cannot run on a host class is UNVERIFIED there. Windows is a fresh native clone. The Linux record has two labelled sources, CI and a local Linux_Docker_Host, and one never stands in for the other (DD9-7).

**Hypothesis profiles.** The project registers `ci` (derandomized, 200 examples) and `dev` (100 examples, no deadline) in `tests/conftest.py`. `HYPOTHESIS_PROFILE` selects one, with `dev` as the default. New tests and every release record use `ci`. A property test cites its statement and a requirement identifier in its docstring and carries the tag `Feature: verdictkit-next-phase, Property P-x` (13.4, D8.6). A test that needs the container carries the `isolation` marker (13.8).

**Evidence discipline.** One Execution_Record per command, with the exact command text, the commit S and the Execution_Index id (3.1, 3.12, 14.16). Every command runs unpiped. The exit code is read directly. Pytest runs with `-rA`. Counts are copied from the runner's summary line and are recorded as absent when the runner prints none (3.3, DD9-3). A capability that was not run is UNVERIFIED (3.4).

**No-loss rule.** At `84df25c`, on each host class, a collection-only run stores the sorted node ids with their SHA-256. At S, every baseline node id must still be collected unless a recorded maintainer decision names its rename or removal. Each node that passed or was skipped at the baseline must pass or be skipped. BE-1 and BE-2 must pass. No `--deselect`, `-k` or `--ignore` is added (13.9, 14.22, D9.4).

**Negative controls and mutation guards.** Every check that could pass silently has a control that makes it fail. Examples: BE1-6 (an Everyone entry), the mutation guard of D5.9 and D8.7 (each check is disabled in a copy and a test must fail), the mutants of D6-AC-10, the one-byte change of every pinned file in D3-AC-27, and the D9 controls (a clone with an untracked file, a count changed by 1, a deleted test, four altered CI run records).

**Constructed test data.** All data is constructed and labelled. Quote and Lease reuse existing constructed fixtures. Reel uses the bundled `SYNTHETIC_DEMO` fixture. Regulatory tests use the fictional jurisdiction `US-ZZ`, and the code `ZZ` is permanently unsupported. Keys are throwaway, created in memory, and no key file is committed (14.24). Canary values are unique per run. No invented real-world number appears (14.23).

**CI dispatch.** `gh workflow run p0-integration.yml --ref feature/kiro-next-phase`, after the workflow file exists on the default branch with `workflow_dispatch`. The saved run record must show the head SHA S, the Phase_Branch, the event `workflow_dispatch` and the status `completed` (D9-AC-9). If dispatch is unsupported, or the remote ref is not S and no push is authorized, the CI result is UNVERIFIED. No pull request and no merge is made to obtain a run (14.20).

**Order of execution.**

1. Once, at `84df25c` on each host class: the node-id inventory (OD-D9-7).
2. Implementation in the order of D0.6, with each track tested on the hosts of its rows.
3. Freeze the code and select S. A later change to a tested file starts a new Release_Candidate.
4. In a clean clone of S: VM-1, VM-2, VM-4, VM-5 and VM-9 on both host classes. VM-6, VM-7, VM-8 and VM-12 on a Linux_Docker_Host, with the native part of VM-8 on Windows. VM-3 and VM-10 on CI.
5. Owner steps: VM-11, VM-17, VM-18, VM-19 and the push authorization.
6. VM-13 at the start and at the end, then VM-14, VM-16 and VM-15.
7. The ledger and `RELEASE_REPORT.md` are committed as evidence commits (DD9-2).

**Acceptance rows by track.**

| Track | Section | Rows | Host | Note |
|---|---|---|---|---|
| P0 | D1 | AC-1 to AC-18 | Windows, Linux | Browser rows run on Linux CI and are UNVERIFIED on Windows |
| P1 | D2 | D2-AC-1 to D2-AC-28, SG-1 to SG-9, SM-1 to SM-14 | CI or VM, Probe, Owner | SM rows run after deployment and are at the PUBLIC level |
| P2 | D3 | D3-AC-1 to D3-AC-27 | Windows, Linux CI, Owner (Windows) | Owner rows need a Contained_Hook_Environment |
| P3 | D4 | D4-AC-1 to D4-AC-19 | Windows, Linux, Owner (Kiro) | Socket cases need Linux |
| P4 | D5 | D5-AC-1 to D5-AC-19 | Windows, Linux | The container check of D5-AC-9 runs on Linux |
| P5 | D6 | D6-AC-1 to D6-AC-14 | Windows, Linux | Symlink and container rows run on Linux |
| P6 | D7 | D7-AC-1 to D7-AC-18 | Windows, Linux | D7-AC-19 is replaced by AM-D7-3 |
| P7 | D8 | D8-AC-1 to D8-AC-30 | Windows, Linux_Docker_Host, Owner | Isolation rows run in the container |
| P8 | D9 | D9-AC-1 to D9-AC-22 | Windows, Linux sources, CI, Owner | Owner rows cannot be run by the agent |
| Gap rows | D10 | D10-AC-1 to D10-AC-9 | CI or VM, Windows, Linux, Owner | Added by the coverage check of D10.5 |

**Not tested, with reasons.**

| Item | Reason | Section |
|---|---|---|
| R-1: the root entrypoint holds the key (T8-34) | Accepted residual risk. No test can show that a process that must have the key lacks access to it. | D8.4 |
| R-2: the examiner shares the network namespace (T8-35) | The egress probe is negative evidence and not a guarantee. If it cannot show a block, R-2 stays accepted. | D8.4, D2-AC-23 |
| Hook firing inside Kiro on Linux | No Linux Kiro session is planned (B-H3) | D3.12 |
| Kiro's own behaviour at its timeout (U-7) | NOT_DETERMINED by design. No artificial timeout is provoked. | D3.8 |
| A strict TypeScript MCP client, MCP Inspector and Claude Desktop | No such client was available (R-D4-1) | D4.7, D4.11 |
| Signing key file permissions on Windows | Not checked (R-D5-1) | D5.11 |
| Rotated-key reuse and back-dating | No trusted timestamp exists (R-D5-2) | D5.11 |
| Bytes of the zip container that no check covers | Not covered by any check (R-D5-4). The reading of 13.5(a) is OD-D10-4. | D5.2, D10.8 |
| A plugin sandbox | Not built. CS-10 is a review aid (R-D6-1). | D6.10 |
| A reviewer's reading of a rule | The numeral check catches only typing (R-D7-1) | D7.10 |
| PDF excerpts | Not supported (OD-D7-2) | D7.10 |
| Fargate capability | No probe is authorized (B-1, D2-AC-4) | D2.11 |
| Bit-for-bit image reproducibility | Not claimed. Builds are dependency-reproducible only. | D2.7 |
| The `AuthzAccessCheck` spike (O3) | Timeboxed. Its absence does not block BE-1. | D8.3 (DD8-7) |
| Browser E2E, `gate_nov22.sh`, the five skipped cases, the Linux per-test baseline | Not run in this phase | D0.9, D9.2 |
| Deployment gates SG-1 to SG-9 | No deployment exists and none is authorized | D2.8, D9.8 |
| Completeness of the sanitizer | The rule list is finite. The scan reports counts and never completeness (R-D8-5). | D8.15 |

## D0. Foundations

### D0.1 Scope and status

**What D0 covers.** D0 fixes the shared ground for the nine tracks P0 to P8 in `requirements.md`: the existing architecture, the environments in which work can be run, the invariants that every track must preserve, the accepted baseline exceptions, the build order, the trust boundaries, the maintainer decisions already recorded, and the unresolved items. It makes no per-track design decisions. Those belong to D1 to D10.

**Status labels.** Every statement about the future in this design carries one of these labels, or is plain description of the existing repository.

| Label | Meaning |
|---|---|
| DESIGNED | Written in this design. No code or test exists for it. |
| IMPLEMENTED | Code exists on the Phase_Branch. It has not been run to a recorded result. |
| VERIFIED | An Execution_Record with Outcome_Class `SUCCEEDED` exists in `docs/next-phase/EXECUTION_EVIDENCE.md` for the current Release_Candidate (Requirement 3.9). |
| UNVERIFIED | Not run in this phase, or run without captured evidence (Requirement 3.4). |

**Current status.** Nothing in this phase is implemented. Every planned item in this document is DESIGNED at most. The baseline run on commit `84df25c68198e496889b5892a03555ec7d2d860a` (branch `feature/kiro-next-phase`) is the only recorded execution result. Its summary is in D0.5.

**Roles.** Kiro owns the engineering work: specs, implementation, tests and evidence. ChatGPT and Claude are independent reviewers only. They do not edit the repository and do not own any deliverable.

**Rules inherited from the requirements.** Commits only on the Phase_Branch (1.1). Frozen_Release refs and Submission_Artifacts files are not modified (1.2, 1.8). New phase documents go under `docs/next-phase/` (1.8). Release tags, merges, pushes and publication are left to the repository owner (14.13).

### D0.2 Architecture overview

The diagram shows components that exist at commit `84df25c`, taken from the Core module listing, the `Dockerfile`, `deploy/entrypoint.sh` and the track register. Planned additions are drawn with dashed borders and carry the track identifier. No component is added beyond those that the requirements name.

```mermaid
flowchart TB
  subgraph Clients
    BR[Browser user]
    KC[MCP client, for example Kiro]
    CL[CLI user]
  end

  subgraph UI[UI workspaces]
    UK[ui-kit: components, theme.css, API client]
    QW[Quote Autopsy web]
    RW[Reel Autopsy web]
    JP[Judge preview: ui/judge, static, read-only]
  end

  subgraph IMG[Docker image: python 3.12-slim pinned by digest]
    subgraph CUST[vk-custodian, uid 900]
      API[API_Server: FastAPI, contract 1.1.0]
      PIPE[pipeline, bundle, sweep, canonical, model, plugin, envprint]
      CUS[custody: vault 0700, drafts 0700]
      EVI[evidence]
      MCP[MCP_Server: stdio, 4 tools]
      CLI[CLI: verdictkit]
    end
    subgraph EXA[vk-examiner, uid 901]
      EW[examiner worker]
    end
    SOCK[(examiner socket, group vk-ipc)]
    EVD[(evidence dir 0750)]
  end

  APPQ[apps/quote-autopsy: Texas rules snapshot]
  APPR[apps/reel-autopsy: synthetic OHLCV]
  STUB[examples/stub_claimtype]

  BR --> QW
  BR --> RW
  BR --> JP
  QW --> UK
  RW --> UK
  UK --> API
  KC --> MCP
  CL --> CLI
  API --> PIPE
  MCP --> PIPE
  CLI --> PIPE
  PIPE --> CUS
  PIPE --> EVI
  PIPE <--> SOCK
  SOCK <--> EW
  EW --> EVD
  PIPE -.claim types.-> APPQ
  PIPE -.claim types.-> APPR
  PIPE -.claim types.-> STUB

  LP[P0 Landing_Page and Onboarding_Flow]:::planned
  DEP[P1 hosted deployment of the same image]:::planned
  HK[P2 hook matcher test and marker hook]:::planned
  DIAG[P3 diagnostic MCP tool and structured errors]:::planned
  SIGN[P4 Bundle_Signature, Trust_Store, signer fields]:::planned
  SDK[P5 Claim_Plugin_SDK, scaffolding command, Conformance_Suite]:::planned
  REG[P6 further jurisdictions: CA, FL, NY after Texas]:::planned
  TM[P7 Threat_Model, property tests, BE-1 and BE-2 remediation]:::planned
  REL[P8 release verification and release report]:::planned

  LP -.-> UK
  DEP -.-> IMG
  DIAG -.-> MCP
  SIGN -.-> PIPE
  SIGN -.-> API
  SDK -.-> PIPE
  REG -.-> APPQ
  TM -.-> IMG
  REL -.-> IMG

  classDef planned stroke-dasharray: 5 5,stroke:#b45309,color:#78350f;
```

Facts behind the diagram, each read from a repository file:

- The image runs two OS users, `vk-custodian` (uid 900) and `vk-examiner` (uid 901), plus the group `vk-ipc` (gid 902). The vault directory is mode 0700 owned by the custodian. The evidence directory is mode 750, owner custodian, group examiner (`Dockerfile`, `deploy/entrypoint.sh`).
- The entrypoint starts each process through `setpriv --no-new-privs` with `env -i` and an explicit environment. `VK_VAULT_KEY` is passed to the custodian and is not passed to the examiner (`deploy/entrypoint.sh`).
- The entrypoint subcommands are `gate-isolation`, `gate-case`, `gate-startup`, `gate-http`, `serve` and `verdictkit`. The `serve` subcommand requires `VK_VAULT_KEY` and fails if it is unset.
- The Core modules are `bundle`, `canonical`, `cli`, `envprint`, `mcp_server`, `model`, `pipeline`, `plugin`, `sweep` and the packages `api`, `custody`, `evidence`, `examiner`.
- `bundle.py` defines `AUTHENTICITY = {"status": "NOT_ESTABLISHED", "note": "Bundles are unsigned in v1."}`. No signing code exists.
- `mcp_server.py` registers the four tools with the server version string `0.1.0`. `api/server.py` sets `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`. The `/api/v1/health` response includes `contractVersion`, `status`, `isolationMode`, `judgeMode` and `engineVersion`. It does not include a commit SHA.
- The CI workflow `p0-integration.yml` has two jobs on `ubuntu-latest`. Its triggers are pull requests to `master`, pushes to `master` and manual dispatch. `m3b-api-checks.yml` triggers on pushes and pull requests to `master`. Neither triggers on a push to `feature/kiro-next-phase`.

### D0.3 Environment matrix

| Environment | What it provides | What can be run | UNVERIFIED or blocked |
|---|---|---|---|
| Windows development host | PowerShell. Python 3.12.10, uv 0.13.9, Node 24.14.1, npm 11.11.0, git 2.51.0. Docker Desktop 29.9.3 with the Linux engine (`linux/amd64`), executable at `C:\Program Files\Docker\Docker\resources\bin\docker.exe`, which is not on `PATH`. A WSL Ubuntu distribution exists and does not have `uv` installed. | Lockfile check, `ruff`, pytest, Vitest, `npm` typecheck and build, `docker build`, and the container gates through the full path to `docker.exe`. All of these were run in the baseline. | Browser E2E (`scripts/ui_e2e.sh` needs Linux tools and port 8000, which `splunkd.exe` holds). `scripts/gate_nov22.sh`. The five tests that skip on Windows. Per-test Linux pytest evidence for BE-1 and BE-2. Hook execution inside Kiro. |
| Linux container | The repository image. Isolation_Mode `ENFORCED` through two OS users, the authenticated socket and the 0700 vault. Run with `--network none` in the baseline. | `gate-isolation`, `gate-startup`, `gate-http`, `gate-case` and offline replay all exited 0 in the baseline. | The image does not contain `ui/`, so `tests/ui/test_judge_preview.py` cannot validly run in it (four named failures, `FileNotFoundError`). The pytest exit code of the combined MCP and preview run was not captured. |
| CI (`ubuntu-latest`) | Two workflows with the `security-and-regression`, `web-ui` and `intake-and-custody` jobs. The `web-ui` job installs Playwright 1.63.0 and runs `scripts/ui_e2e.sh`. | Nothing has been run on CI in this phase. | Every CI result is UNVERIFIED for this phase. The workflows trigger on `master`, so a pull request to `master` is needed before they run. Creating that pull request is an owner action (14.13). |

**Design rule: configurable test ports (1.17).** Every port used by a local test, server or browser E2E run is set through an environment variable or command-line option with a documented default. Nothing in this phase stops, kills or reconfigures a process that the phase did not start. The process holding port 8000 on the development host (`splunkd.exe`, PID 5780 at baseline) is left running. Any new test or script that needs a port reads it from configuration and does not assume 8000, 4173 or 4174. Changing the existing `scripts/ui_e2e.sh` to take its ports from configuration is DESIGNED work for D1 and D8, and is not done.

**Host-class rule (1.5, 1.6, 1.12).** Container gates run only on a Linux_Docker_Host. A check that fails for a host-specific reason is recorded as a Baseline_Exception for that host and stays UNVERIFIED for the other host class until it has a per-test listing (`-rA`) and a captured pytest exit code.

### D0.4 Invariant-protection matrix

The first column lists the invariants from Requirement 2 and the neighbouring requirements. The second lists how tracks could weaken each one. The third names the design guard, by requirement identifier. Each guard is DESIGNED. The mechanism for each is specified in D1 to D10.

| Invariant | How tracks could threaten it | Design guard |
|---|---|---|
| Decimal arithmetic (2.1) | P0 UI converts a decimal string to a binary float for display. P5 scaffold template emits `float`. P6 new jurisdiction rules computed with float. P4 or P7 test data uses float. | UI renders the supplied decimal string unchanged (5.6). Scaffold output contains no float type, literal or conversion (11.5), and the Conformance_Suite checks no float in examination output (11.9). Acceptance tests for P6 use Decimal expected values (12.12). |
| Determinism (2.2, 10.7) | P4 adds signature bytes or a timestamp to the verdict. P3 adds diagnostics to the verdict path. P5 plugin reads wall-clock time. P2 or P8 scripts introduce unseeded values. | The Verdict_Hash excludes signature material (10.6). Unsigned Bundles stay byte-identical to baseline (10.5). Signed Bundles are byte-identical under a fixed clock and key (10.7). Scaffold reads no wall-clock time (11.5). New tests run under the `ci` Hypothesis profile with derandomization (13.7). |
| Answer-blind examination (2.3) | P5 plugins that can read outcomes. P3 diagnostics or error text that echoes outcome values. P4 puts the signing key in the examiner environment. P1 deploys with a changed environment. | Plugins stay behind the Answer_Blind boundary (11.15) and the blinding check runs in the Conformance_Suite (11.8). Signing key is read only in the Custodian (10.18). MCP error messages exclude exception text and input values (9.3, 9.14). Deployment keeps `VK_VAULT_KEY` out of the Examiner environment (7.9). |
| Fail-closed controls (2.4) | P3 changes error signalling and a failure turns into a pass. P4 reports trust on a bad signature or bad Trust_Store. P6 asserts a rule from an unverified source. P1 downgrades isolation to deploy. P2 treats an untrusted workspace as passing. | Missing or ambiguous signature input yields `INVALID` or `UNSUPPORTED_ALGORITHM` (10.30). A bad Trust_Store gives `NOT_EVALUATED` and never `TRUSTED` (10.17). Unverified source gives `UNVERIFIED` and no numeric rule (12.5). A target that cannot provide `ENFORCED` is rejected (7.8, 7.18). Untrusted-workspace hook runs are recorded `UNVERIFIED` (8.11). Verdicts `INDETERMINATE` and `BLOCKED` stay normal results (9.19). |
| Enforced Linux isolation (2.5, 2.6, 2.7) | P1 hosting target without distinct OS users. P4 key handling. P0 or P1 headers or proxies that bypass the socket. P7 tests run outside the container. | Judge mode starts only with `ENFORCED` and prints `VK_STARTUP_OK isolation=ENFORCED` once (7.7, 2.5). Judge mode refuses to start otherwise (2.6, 7.8). Isolation tests are marked `isolation` and run in the container gate (13.8). |
| Offline reproducibility (2.8) | P4 verification fetches keys or revocation data. P6 loader fetches rules at verification time. P3 diagnostics open network connections. | Signature verification is offline (10.19). The rules snapshot is packaged in the repository and verification gives the same outcome with no network (12.16). Diagnostics open only the configured examiner socket (9.4). Offline replay is part of the release scenario (14.5, 14.6). |
| LLM fence (2.9, 2.12) | P5 scaffold or P3 tooling imports an LLM client library. P6 derives rule values from a model response. | Scaffold contains no LLM client import (11.5). Rule values come only from Official_Source snapshots, never from model responses (12.6). `tests/contract/test_llm_fence.py` runs on every change to files under `verdict-integrity.md` (2.12). |
| Frozen release (1.2, 1.3, 14.14) | Any track that commits, rebases or tags on the wrong ref. P1 deployment workflow that pushes. Edits to Submission_Artifacts to apply a correction. | Work only on the Phase_Branch (1.1). Refusals are recorded (1.3). Corrections go in new files under `docs/next-phase/` (1.8, 15.8). Start-to-end check of each ref against its own recorded value, including the tag object and the peeled commit of `v1.0.0-submission` (14.14). |
| Evidence integrity (3, 4.9, 15, 16) | Counts from memory. A duplicate or lock-collision record counted as a test result. A capability described without a `SUCCEEDED` record. Credits estimated. Checkboxes ticked without evidence. | Counts come only from CANONICAL rows of the Execution_Index (1.14, 1.15, 14.8). Capability statements need a `SUCCEEDED` record for the Release_Candidate (3.9, 3.10). Credits are `NOT_AVAILABLE` unless read from a Kiro usage record (16.2). A `tasks.md` checkbox is checked only if the record shows every linked criterion `SUCCEEDED` (4.9). |

### D0.5 Accepted baseline exceptions

The baseline run on commit `84df25c68198e496889b5892a03555ec7d2d860a`, Windows host, 2026-11-24, gave two failures in the full `pytest -m "not isolation"` run: 444 passed, 2 failed, 5 skipped, 4 deselected. The two failures are the only accepted exceptions. Neither permits a release (Glossary, Baseline_Exception).

| | BE-1 | BE-2 |
|---|---|---|
| Test | `tests/contract/test_mcp_server.py::test_verify_replay_and_explain_roundtrip` | `tests/ui/test_judge_preview.py::JudgePreviewTests::test_case_outcome_get_to_offline_backend` |
| Observed failure | Assertion at `test_mcp_server.py:30`: `oct(bundle.parent.stat().st_mode & 0o777) == "0o700"` gives `0o777` on Windows. | `TimeoutError: timed out` in `http.client`, client timeout 2 seconds. Reproduced when run alone (7 passed, 1 failed). |
| Established | Reproduced at the same assertion. `Path.chmod(0o700)` does not set POSIX permission bits on Windows. The failure also appears in the contract run, the MCP run and the core hook command run. The historical Linux audit recorded this test as passed in image `verdictkit:submission`. | Reproduced on Windows. It was not reported as failing in the historical audit. |
| Not established | Linux pass in this phase. No per-test listing and no pytest exit code were captured. A pass is inferred only from the test's absence in a failure list of 4 named failures in a combined run. | **The root cause.** No trace, timing instrumentation or Linux comparison exists. The closed-local-port hypothesis in the baseline report is a hypothesis only and is not asserted here. A longer timeout is not accepted as a verified fix. |
| Status | ACCEPTED_BASELINE_EXCEPTION, for baseline continuation only | ACCEPTED_BASELINE_EXCEPTION (provisional) |
| Mandatory remediation before the final release | Keep the Linux POSIX mode assertion unchanged. Add platform-appropriate Windows security handling that tests the same property. Do not remove, weaken, skip or mark the original assertion (13.11). | Add instrumentation that records connection and response timing. Establish the root cause on Windows and on Linux from a full checkout. Fix the cause (13.12). |
| Closing evidence | Per-test listing (`-rA`) and captured pytest exit code on Windows and on a Linux_Docker_Host (13.13). | Same (13.13). |

**No other failure is permitted.** Any other failing test on any host is a new regression, is recorded `FAILED`, and needs a new maintainer decision by identifier before it can be accepted (1.13). No contract test is modified to loosen an assertion, marked `xfail` or marked `skip` (2.11). Until BE-1 is remediated, Windows runs may show exactly that one contract failure and no other (2.11). The release is not marked verified while either exception stands (14.10).

**Linux evidence for BE-1 and BE-2 is indirect and UNVERIFIED.** The only Linux data in this phase is one combined run in the image with summary `4 failed, 10 passed`. The command ended in a pipe through `tail`, so the recorded exit code (0) belongs to `tail`. The four named failures are in the judge-preview file because `ui/` is absent from the image, which makes that run an invalid environment for BE-2. See `BASELINE_REPORT.md` section 7 and ledger records E-025a and E-025b.

### D0.6 Dependency ordering

**Build sequence (DESIGNED).**

1. **Baseline and evidence discipline.** Done for the baseline run (`BASELINE_REPORT.md`). Applies to every later step (R1 to R4).
2. **P7 foundations, part 1.** BE-1 and BE-2 remediation work starts early because later tracks need a clean contract suite on Windows. The Threat_Model skeleton is created here and is extended as each track lands.
3. **P0 UI and landing page.** Needs the existing API contract 1.1.0 only. No dependency on P4 at first.
4. **P5 plugin SDK.** Independent of P4. Needs `plugin.py`, the stub example and the contract tests.
5. **P4 signing.** Changes the Bundle, CLI output, API contract and UI fields. It comes before P3 diagnostics fields and P8.
6. **P3 MCP interoperability.** Needs P4 for the signature fields in `replay_bundle` and `explain_verdict` (9.8). The error-signalling and diagnostic work in P3 does not depend on P4 and can start earlier.
7. **P6 regulatory.** Texas completion (retrieve 7 TAC §84.205 or record it `UNVERIFIED`) first (12.11, 12.17). Then California, Florida and New York in that order (12.18).
8. **P1 deployment.** Needs P0 for what is served, P4 for the final API contract and headers, and a Linux_Docker_Host. Hosting provider choice is a decision inside D2.
9. **P2 hooks and Windows.** Matcher and marker work can be done in the repository early. Execution evidence is owner-run in a disposable checkout (8.15 to 8.18) and does not block other tracks.
10. **P7 completion.** Property and adversarial tests for P3, P4, P5 and P6 are added as each lands. Final Threat_Model rows close after P6.
11. **P8 release verification.** Last. Reruns every baseline step and every new test on the exact Release_Candidate head commit (14.1, 14.2, 14.16).

```mermaid
flowchart LR
  B[Baseline R1 to R4]
  P7a[P7 early: BE-1 and BE-2 remediation, Threat_Model skeleton]
  P0[P0 UI and landing]
  P5[P5 plugin SDK]
  P4[P4 signing]
  P3[P3 MCP]
  P6a[P6 Texas completion]
  P6b[P6 CA, FL, NY]
  P1[P1 deployment]
  P2[P2 hooks]
  P7b[P7 tests across tracks]
  P8[P8 release verification]

  B --> P7a --> P0
  B --> P5
  B --> P4
  P4 --> P3
  B --> P3
  B --> P6a --> P6b
  P0 --> P1
  P4 --> P1
  B --> P2
  P5 --> P7b
  P4 --> P7b
  P3 --> P7b
  P6b --> P7b
  P7a --> P7b
  P0 --> P8
  P1 --> P8
  P2 --> P8
  P7b --> P8
```

**Independently testable.** P0 (against the existing API), P2 (matcher test, marker hook), P5 (scaffold and Conformance_Suite on existing claim types), P6 Texas completion, and the BE-1 and BE-2 remediation in P7 can each be tested without another track. The error-signalling and diagnostic parts of P3 can be tested without P4. P4 is testable on its own through the Core functions, with CLI and API fields added after.

**Cross-track interfaces.**

| Interface | Producer | Consumer | Governing requirement |
|---|---|---|---|
| Signature members, `signature_validity`, `signer_trust`, authenticity fields | P4 | P3 (9.8), P0 UI display (10.20), P1 contract, P7, P8 | 10.4, 10.8, 10.20, 10.21 |
| API contract version and `api/openapi.yaml` | P4, P1 (health fields) | P0 UI client, P3, P8 | 10.21, 7.13 |
| `ClaimType` protocol and Conformance_Suite | P5 | P7 property (e), P8, existing apps | 11.7, 11.11, 13.5 |
| Rules snapshot and loader | P6 | Quote_App UI (retrieval date), P7 | 12.2, 12.7, 12.14 |
| Execution_Records and `tasks.md` checkboxes | all tracks | P8 release report | 4.4, 4.9, 14.12 |
| `/api/v1/health` with commit SHA | P1 | P8 provenance | 7.13, 14.17 |
| Port configuration for tests | P0, P7 | all browser and server tests | 1.17 |

### D0.7 Trust boundaries

Boundaries marked existing are present at `84df25c`. Boundaries marked DESIGNED come from the requirements and are not implemented.

| Principal or boundary | What crosses | Control | State |
|---|---|---|---|
| Maintainer to repository | Commits, documents, decisions | Phase_Branch only. Frozen_Release refs refused for push, merge, force-update, delete or re-point (1.1, 1.3). Tags, merges, pushes and publication are owner actions (14.13). | Rule DESIGNED. Tags verified at baseline start. |
| Kiro agent to repository and tools | File edits, shell commands, MCP calls, sub-agent runs | Attribution in the ledger only from output captured inside Kiro (3.6, 3.7). Hooks configured read-only (8.8). New durable rules as new steering files only (4.8). | DESIGNED |
| Custodian (uid 900) to Examiner (uid 901) | Blinded task out, examination result back, over the authenticated Unix socket | Examiner never receives claimed outcomes (2.3). Examiner environment is an explicit allowlist without `VK_VAULT_KEY`. Vault is 0700 custodian. `--no-new-privs`. | Existing. Enforced in the image. |
| Signing key to Custodian only | Ed25519 private key supplied by the operator | Read only in the Custodian. Never in the Examiner environment, a Bundle, a log, an API response or an MCP result. Never generated, stored, logged or committed for production (10.18, 10.25). | DESIGNED |
| Trust_Store (operator-supplied local file) to verifier | Key id, public key, status `ACTIVE`, `ROTATED` or `REVOKED`, validity interval | Read only from a local operator file. The public key embedded in a Bundle is not trusted without a Trust_Store entry. A malformed file gives `NOT_EVALUATED` (10.16, 10.17, 10.27). | DESIGNED |
| API client to API_Server | HTTP JSON, bundle upload | 256 KiB JSON cap, 8 MiB bundle cap, in-process rate limit, 24 h TTL, `Cache-Control: no-store`, `nosniff` (existing). CSP, Referrer-Policy and HSTS where TLS terminates are DESIGNED (7.5, 7.6, 7.11). | Part existing, part DESIGNED |
| MCP client to MCP_Server | stdio tool calls | Read-only mode refuses network acquisition (9.6). Size caps (9.7). Errors carry codes, no paths, no exception text (9.3). Only no-write, no-network tools in `autoApprove` (9.9). | Part existing (`VK_MCP_READONLY`), rest DESIGNED |
| Bundle recipient to Bundle | `.vkb` zip | Integrity, reproducibility and authenticity reported separately. Offline replay unless `--allow-refetch` (2.8). Unsigned Bundle never described as authenticated (10.32). Signature validity, signer trust, integrity and verdict correctness are four separate results (10.33). | Existing integrity and replay. Signing DESIGNED. |
| Regulatory sources to Quote_App | Retrieved bytes from official domains | Domain must be on the jurisdiction's official list. Retrieved bytes must contain the excerpt. Identical bytes from two URIs are rejected. Hash recomputed on load (12.1, 12.3, 12.4, 12.7). | Texas existing. Others DESIGNED. |
| Hosting provider to deployment | Image, secrets, network | Portable Docker image (7.16). `VK_VAULT_KEY` from the secret store (7.9). Targets that cannot give `ENFORCED` are rejected without weakening isolation (7.18). | DESIGNED. No deployment exists. |
| Disposable hook-test checkout to Kiro | Reviewed read-only hook commands, hook output | Separate checkout opened as trusted by the maintainer. The main workspace is not marked trusted for this. No credentials or keys in it. Commands reviewed before running (8.16 to 8.18). | DESIGNED. Owner-run. |
| Historical_Audit directories to repository | Derived counts, hashes, event names | Read-only. No raw logs copied. Corrections written to new files (15.1 to 15.3, 15.8). | Existing practice, recorded in `HISTORICAL_EVIDENCE_RECONCILIATION.md` |

### D0.8 Maintainer decisions recorded

These are decisions made in review. They are DESIGNED. None is implemented.

1. **Landing page title.** The Landing_Page carries the title "VerdictKit — Evidence Verification Workspace". The apps keep the names "Quote Autopsy" and "Reel Autopsy" (6.11).
2. **Deployment.** The deployment is a portable Docker image that runs unchanged on any Linux_Docker_Host and does not depend on one provider's proprietary service for isolation (7.16). AWS ECS Fargate is evaluated as one candidate only, as a recorded design decision, with no infrastructure provisioned and no charge incurred (7.17). A target that cannot give `ENFORCED` is rejected (7.18).
3. **Hook verification.** Hook execution is verified in a separate disposable checkout that the maintainer opens as trusted. The main repository workspace is not marked trusted for this (8.16). Hooks are a development guardrail. Runtime guarantees come from code and CI (8.7).
4. **MCP error behaviour.** Execution errors return `isError` true with a structured `error` object. A legitimate verdict, including `INDETERMINATE` and `BLOCKED`, returns `isError` false with the baseline success shape. Existing contract tests are not edited or loosened. Claim validation is not relaxed for any client (9.13, 9.16, 9.19).
5. **Signing.** Ed25519 with the identifier `ed25519`. Keys are externally provisioned. The envelope carries a key identifier (SHA-256 of the raw public key). The Trust_Store is versioned and records `ACTIVE`, `ROTATED` and `REVOKED` status. The envelope binds the manifest hash, bundle format version, protocol identifier and version, algorithm and key id, using a domain-separated signing input. Only the signature members the design names explicitly are exempt from the unlisted-member integrity rule, with no wildcard or prefix exemption (10.24 to 10.31).
6. **Plugin SDK.** A scaffolding command and a reusable Conformance_Suite. Scaffolding writes only inside its target directory and modifies nothing under `core/src/verdictkit/`. `ClaimType` signatures stay unchanged unless the core design is updated first (11.6, 11.14).
7. **Regulatory order.** Complete Texas first, including 7 TAC §84.205 or its recording as `UNVERIFIED`. Then California, Florida and New York in that order. A jurisdiction is added only when its rules meet criteria 12.1 to 12.16 (12.17, 12.18).
8. **P7 scope.** A Threat_Model with one row per threat and a test per control. Five Hypothesis properties (13.5). Adversarial tests for the seven named malformed-input kinds (13.6, 13.14). BE-1 and BE-2 remediation (13.11 to 13.13).
9. **P8 scope.** Rerun of every baseline step plus the new tests on the exact Release_Candidate head. Signed-bundle end-to-end scenario with `ESTABLISHED` asserted only with a Trust_Store entry. Release provenance recorded. No tag, merge, push or publication by the agent (14.1, 14.16 to 14.18, 14.13).

### D0.9 Open items and blockers

| Item | State | What would resolve it |
|---|---|---|
| Browser E2E (`scripts/ui_e2e.sh`) | UNVERIFIED. Linux-only script. Port 8000 is held by `splunkd.exe` and that process is not to be stopped. | Linux CI run, or a host with Linux tooling and the ports free or configurable (1.17). |
| `scripts/gate_nov22.sh` | UNVERIFIED. Not run. | Linux runner. |
| Five tests skipped on Windows (one symlink test, four Linux peer-credential tests) | UNVERIFIED as Linux pytest cases. | Linux pytest run from a full checkout. |
| Automatic Kiro hook execution | UNVERIFIED. Kiro logged four hooks registered and `hooks.v2.executionDisabledUntrustedWorkspace`. No execution event was found. | Owner-run test in the disposable trusted checkout, with output captured from Kiro (8.15). |
| Public deployment | None exists. No hosted demonstration is available. | P1 work and an Execution_Record per 7.13. |
| Kiro credits for this phase | `NOT_AVAILABLE`. No usage record is accessible to the agent. The historical total (92.95176173134327494 credits) belongs to the earlier work and is kept separate (16.4). | Maintainer reads the Kiro usage view. |
| BE-1 remediation | Open. | See D0.5 and 13.11. |
| BE-2 remediation | Open. Root cause NOT established. | See D0.5 and 13.12. |
| Per-test Linux evidence for BE-1 and BE-2 | UNVERIFIED. | `-rA` listing and captured pytest exit code on Linux from a full checkout (13.13). |
| CI on this branch | UNVERIFIED. Workflows trigger on `master`. | Owner opens a pull request to `master`. |
| Not established from the historical record | Which Kiro component removes empty arrays and objects from tool arguments. Whether any hook has fired. Per-claim-type successful verdict counts through Kiro. Isolation `ENFORCED` through Kiro MCP. | Controlled probes and Kiro-captured output in P3 and P2. |
| Hosting target and cost | Undecided. | D2 decision record (7.17). |

### D0.10 Requirement traceability for D0

| D0 section | Requirements supported |
|---|---|
| D0.1 Scope and status | 3.4, 3.9, 4.1, 1.1, 1.2, 1.8, 14.13 |
| D0.2 Architecture overview | 4.2, 2.7, 2.9, 7.16, 10.3 |
| D0.3 Environment matrix | 1.4, 1.5, 1.6, 1.12, 1.16, 1.17, 14.3, 14.4 |
| D0.4 Invariant-protection matrix | 2.1 to 2.12, 1.2, 3 and 4.9 |
| D0.5 Accepted baseline exceptions | 1.7, 1.12, 1.13, 1.18, 2.11, 13.11 to 13.13, 14.10 |
| D0.6 Dependency ordering | 4.1, 4.2, 4.3, 9.8, 12.17, 12.18, 14.1, 14.2 |
| D0.7 Trust boundaries | 2.3, 2.8, 7.9, 8.16 to 8.18, 9.3, 10.16 to 10.18, 12.1, 15.1 to 15.3 |
| D0.8 Maintainer decisions | 6.11, 7.16 to 7.18, 8.16, 9.13, 9.16, 9.19, 10.24 to 10.31, 11.6, 11.14, 12.17, 12.18, 13, 14 |
| D0.9 Open items | 1.17, 3.4, 8.11, 8.15, 14.19, 16.2 |

Every D0 component in the diagram maps to at least one requirement above. No D0 component is unmapped (4.2).

## D1. P0 Professional UI/UX modernization

### D1.1 Scope and status

**Covers.** The unified landing page and onboarding (R6), the shared UI_Kit modernization of Quote_App and Reel_App (R5), the accessibility criteria 7.1 to 7.4 of R7, and the UI side of invariants 2.1, 2.3, 2.4, 2.8, 2.9, port configuration (1.17) and the authenticity display rules (10.20, 10.32, 10.33).

**Does not cover.** Response headers 7.5 and 7.6 and hosting (D2). Signature fields and their values (D5). The `ui/judge` preview (DD-10). Any change to API contract 1.1.0, `core/`, `api/` or `tests/contract`.

**Notes for other tracks.** Quote findings that rely on a regulatory snapshot must show its retrieval date (12.14). That display is owned by D7. D1 only reserves the place in `FindingCard`.

**Status.** Everything in D1 is DESIGNED. Nothing is IMPLEMENTED. Nothing is VERIFIED. Every acceptance criterion in D1.13 is UNVERIFIED until an Execution_Record exists.

### D1.2 Inspected baseline and gaps

Files read at commit `84df25c`: `ui-kit/src/{index.ts, types.ts, api.ts, components.tsx, theme.css, api.test.ts, components.test.tsx}`, `ui-kit/package.json`, both apps' `src/App.tsx`, `intake.ts`, `intake.test.ts`, `index.html`, the quote app's `main.tsx`, `examples.json`, `vite.config.ts`, `package.json`, `ui/judge/*`, root `package.json`, `scripts/ui_e2e.sh`, `tests/ui/e2e_browser.cjs`, and the authenticity and reproducibility schemas in `api/openapi.yaml`.

**Existing structure.** Root npm workspaces: `ui-kit`, `apps/quote-autopsy/web`, `apps/reel-autopsy/web`, with `typecheck`, `test` and `build` run through `--workspaces --if-present`. The apps define no CSS of their own and import `@verdictkit/ui-kit/src/theme.css`. Both `index.html` files have `lang="en"` and a CSP meta tag. Preview ports are 4173 (quote) and 4174 (reel). Dev port 5173 is used by both apps. All are `strictPort` and hard-coded.

**Existing tests.** `ui-kit` has `api.test.ts` and `components.test.tsx` (three `VerdictView` tests and `statusTone`). Each app has `intake.test.ts` only. No package has accessibility tooling. Playwright exists only in the CI `web-ui` job.

| # | Component or file | Finding | Requirement |
|---|---|---|---|
| 1 | `EquityChart` | Converts decimal strings with `Number()` and prints min and max with `toFixed(2)`. It is the only float conversion found by searching `parseFloat`, `Number(`, `toFixed`, `toLocaleString`, `Intl`, `Math.round` in `ui-kit/src` and `apps/*/web/src`. The `intake.ts` files have none. | 5.6, 2.1 |
| 2 | `ReportView` | Shows integrity through `StatusBadge` by mapping VERIFIED to CONSISTENT and FAILED to CONTRADICTED. This reuses the verdict vocabulary for an integrity result. | 5.4, 2.4, 10.33 |
| 3 | `BundlePanel`, `types.ts` | Hard-codes "bundles are unsigned in v1". `types.ts` types authenticity as the literal `NOT_ESTABLISHED`. The text must come from the API authenticity object so P4 can extend it. The signed-case field set is PENDING D5. | 10.20, 10.32 |
| 4 | `SensitivityGrid` | Cells are colour-only spans with detail in a `title` attribute. Not identifiable in greyscale and not reachable by keyboard. | 5.4, 5.2, 7.1 |
| 5 | `DemoNotice`, `EquityChart` | `DemoNotice` shows the API notice text, but no component prints the literal `SYNTHETIC_DEMO` next to the content. `ILLUSTRATIVE` appears only in the `EquityChart` caption. | 5.3 |
| 6 | App error paragraphs | `state.error` is a plain paragraph with no role and no separate code, reason or next step. Apps print "API unavailable: ..." as plain text. The phase is printed as a raw enum ("Stage: freezing"). | 5.8, 7.1 |
| 7 | `theme.css`, apps | No `:focus-visible` style, no skip link, no header or nav landmark, no `aria-live` region, no `prefers-reduced-motion` rule. ARIA use: 3 in `ui-kit/src/components.tsx`, `role="group"` tabs and `aria-pressed` in the apps. The only landmark is `<main>`. | 7.1 |
| 8 | Apps | No empty state before the first verdict. The busy state is only the button label "Examining...". | 5.8, 6.9 |
| 9 | `api.ts` | No request timeout, so "unreachable within 10 seconds" cannot be asserted. | 6.8 |
| 10 | Both apps | No link to each other or to a landing page. | 6.1 |
| 11 | `theme.css` | Colours are custom properties. Font sizes, spacing, radii and line heights are literals inside rules. No focus token. Contrast has never been measured. Pairs to measure first: `--vk-muted` on `--vk-bg`, and white text on badge fills. | 5.1, 7.1 |
| 12 | Quote and Reel `App.tsx` | Quote clears the claimed-figure fields (`setStated({})`) after `onAccepted`. Reel clears claimed results and pasted text. This is the write-only privacy design (API contract section 0). It conflicts literally with 5.8 when a later stage returns BLOCKED or an error. Resolved by DD-9. | 5.8, 2.3 |
| 13 | `ui/judge` | Separate vanilla static preview with its own `style.css`, covered by `tests/ui/test_judge_preview.py`. Outside 5.1, which names Quote_App and Reel_App. | 5.1 |
| 14 | Reel `DEMO_FIXTURES` | Entries carry an `expect` field with the expected verdict. Onboarding must never display it as a result. | 6.5 |
| 15 | `tests/ui/e2e_browser.cjs` | Baseline assertions depend on frozen `data-testid` values and strings. See the frozen list below. | 5.9 |

**Frozen test hooks (5.9).** New markup may add elements. It must not rename or remove these.

| Hook | Asserted content |
|---|---|
| `isolation` | contains UNENFORCED or ENFORCED |
| `finding-<id>` | contains "point of failure" |
| `headline` | contains CONDITIONAL, COMPLETED, IMPOSSIBLE, NO VERDICT |
| progress `data-stage` attributes | stage order |
| `bundle-metadata` | contains VERIFIED |
| `repro-status`, `diagnostics` | present |
| `sensitivity` | contains "rounding_convention", "16 grid points" |
| `demo-notice` | count at least 2 on a synthetic verdict |
| `evidence` | contains SYNTHETIC_FIXTURE |
| `equity-chart` | contains ILLUSTRATIVE |
| `error` | contains PRIVACY_REJECTED |
| `blockers` | contains EVIDENCE_UNAVAILABLE |
| Form label "taxable base"; buttons with `data-example` and `data-fixture`; download filename ending `.vkb` | present |

### D1.3 Design decisions

| ID | Decision | Alternative rejected | Why |
|---|---|---|---|
| DD-1 | The landing page is a third npm workspace `apps/landing/web`, named `@verdictkit/landing-web`, with the same `typecheck`, `test` and `build` scripts as the apps (6.10). Root `package.json` workspaces gains one entry. | A page inside an existing app. | Keeps each app's build and E2E unchanged. |
| DD-2 | No client-side router. Landing, Quote and Reel stay three HTML documents joined by plain anchors in a shared `AppShell` header. | Single-page app with a router. | A router changes E2E URLs, adds a dependency and widens the blast radius. |
| DD-3 | Landing links come from build-time `VITE_QUOTE_URL` and `VITE_REEL_URL`, defaults `http://127.0.0.1:4173/` and `http://127.0.0.1:4174/`. The apps link back with `VITE_LANDING_URL`, default `http://127.0.0.1:4175/`. Exactly one anchor per app on the landing page (6.1). Hosted values are PENDING D2 (OD-1). | Hard-coded URLs. | Hosting paths are not decided. |
| DD-4 | Tokens live in new `ui-kit/src/tokens.css`, imported first by `theme.css`. Existing `--vk-*` names stay as aliases, so apps need no change. A mirrored `ui-kit/src/tokens.ts` holds breakpoints and the colour pairs used by the contrast test. | Rename tokens. | Renaming forces edits in every consumer. |
| DD-5 | Every status shows a visible text label, a decorative glyph (`aria-hidden`) and a tone. An unknown status renders neutral as `UNRECOGNISED <raw value>` and never takes a positive tone (2.4). | Default unknown values to a pass or fail tone. | Fail closed. |
| DD-6 | Integrity, reproducibility, authenticity and verdict are four separate labelled rows or panels. No combined "trusted" or "verified" indicator exists (10.32, 10.33). Authenticity text and tone come from the API authenticity object. Today only `NOT_ESTABLISHED` exists and renders neutral-warn with the API note. A positive tone for any other value is PENDING D5 (OD-7) and defaults to neutral. | One summary badge. | A summary would merge four different claims. |
| DD-7 | API decimals are rendered only through `DecimalText`, which prints the string unchanged. A string not matching `/^-?\d+(\.\d+)?$/` is still printed unchanged, with an adjacent "unparsed" marker. No component calls `Number`, `parseFloat`, `toFixed`, `toLocaleString` or `Intl` on an API value. Chart geometry is the one exception, in the allow-listed file `ui-kit/src/chartGeometry.ts`, which returns coordinates and never text. Chart min and max labels are chosen by the pure string helper `compareDecimalStrings` and printed as the original strings. A scan test enforces this. | Format numbers for display. | Display digits must equal supplied digits (5.6, 2.1). |
| DD-8 | `createClient` gains optional `requestTimeoutMs`, implemented with `AbortController`, default 10000 for health and unset for other calls unless a caller sets it. A timeout raises new `ApiUnavailableError`, distinct from `ApiError`. Contract 1.1.0, endpoints and shapes do not change. Existing exports stay. | Per-page `setTimeout`. | One tested mechanism for all callers (6.8). |
| DD-9 | Input retention. If the failure occurs before acceptance (`createCase` failed, `onAccepted` not called), all input is kept. After acceptance, every non-claimed field is kept, and the claimed-figure fields are shown EMPTY with a visible note that claimed figures are sealed and must be re-entered. Claimed values are never re-populated from any response. Flagged OD-6 for requirement wording. | Keep claimed values in client memory. | Claimed outcomes are write-only (2.3). |
| DD-10 | `ui/judge` is not modified. | Restyle it with the tokens. | Out of 5.1 scope. Covered by its own test. |
| DD-11 | The landing page calls `GET /api/v1/health` once on load and on explicit Retry. It shows API status, Isolation_Mode, contract version and engine version exactly as returned. The unavailable message appears within 10 seconds of the first failed request (6.8) and no verdict is ever shown. | Polling. | No hidden background traffic. |
| DD-12 | Vite configs read `VK_QUOTE_DEV_PORT`, `VK_QUOTE_PREVIEW_PORT`, `VK_REEL_DEV_PORT`, `VK_REEL_PREVIEW_PORT`, `VK_LANDING_DEV_PORT`, `VK_LANDING_PREVIEW_PORT` and `VK_API_URL`. Defaults: dev 5173 (quote), 5174 (reel), 5175 (landing); preview 4173, 4174, 4175. Reel dev port moves from 5173 to 5174, a deliberate change. `scripts/ui_e2e.sh` and `tests/ui/e2e_browser.cjs` read the same variables with unchanged defaults, and the landing preview is added to the readiness checks (1.17). The process on port 8000 is never stopped. | Keep hard-coded ports. | 1.17. |

```mermaid
flowchart LR
  L[Landing: apps/landing/web] -->|anchor| Q[Quote Autopsy]
  L -->|anchor| R[Reel Autopsy]
  Q -->|AppShell nav| L
  R -->|AppShell nav| L
  Q <-->|AppShell nav| R
  L -->|GET health| A[(API_Server)]
  Q --> A
  R --> A
```

### D1.4 Design tokens

Final colour values are not chosen in this design. The contract is: every foreground and background pair in the contrast table passes. Final values are chosen at implementation and recorded by the contrast test. Light theme only. A dark theme is out of scope.

| Group | Tokens | Rule |
|---|---|---|
| Colour | `surface`, `surface-raised`, `ink`, `ink-muted`, `line`, `accent`, status `pass`, `fail`, `warn`, `info`, `neutral`, `demo`, `focus` | Values in `tokens.css` only. |
| Type | `--vk-text-xs` 0.75rem, `sm` 0.875rem, `base` 1rem, `lg` 1.125rem, `xl` 1.375rem, `2xl` 1.75rem. Line height 1.5 body, 1.25 headings. Font stacks sans and mono. | Base size becomes 16px (from 15px). |
| Spacing | `--vk-space-1` to `--vk-space-8` on a 4px base | No raw spacing literals elsewhere. |
| Radius | `sm`, `md`, `pill` | |
| Focus | `--vk-focus-ring`: 3px solid, offset 2px, colour at least 3:1 against surface, raised surface and badge fills | Applied to every focusable element. |
| Motion | `--vk-motion-fast`, overridden to 0s under `prefers-reduced-motion` | |
| Breakpoints | `sm` 480, `md` 768, `lg` 1100 CSS px, in `tokens.ts` only. Max content width 1100px as today. | |

**Rules.** No hex colour, `px` font size or raw spacing literal outside `tokens.css` in `theme.css`, `apps/*/web/src` and `apps/*/web/index.html` (5.1). A scan test enforces it. The contrast test computes WCAG ratios in code from `tokens.ts` and fails below 4.5 for normal text, or below 3 for large text (24px, or 18.66px bold) and UI component boundaries (7.1).

**Contrast pairs to test.** `ink` on `surface`, `ink` on `surface-raised`, `ink-muted` on both, `accent` text on both, white or `ink` on each status fill, each status text on its tint, `demo` label on its background, focus ring against surface, raised surface and each badge fill, and `line` against `surface` for input boundaries.

### D1.5 Status vocabulary

A tone is an enhancement. The label text carries the meaning.

| Domain | Values | Label text | Tone | Glyph | Notes |
|---|---|---|---|---|---|
| Headline status | CONSISTENT, SUPPORTED, WITHIN_BOUND | the value | pass | check | `statusTone` behaviour is frozen. |
| | CONDITIONAL, INDETERMINATE | the value | warn | triangle | |
| | CONTRADICTED, REFUTED, IMPOSSIBLE | the value | fail | cross | |
| | null | NO VERDICT | none | dash | |
| Execution status | COMPLETED | COMPLETED | neutral | none | Not a verdict. |
| | BLOCKED, INDETERMINATE | the value | warn | triangle | Never pass tone. |
| Integrity | VERIFIED | VERIFIED | pass | check | New `IntegrityBadge`. No longer borrows verdict values. |
| | FAILED | FAILED | fail | cross | |
| Reproducibility | REPRODUCED | REPRODUCED | pass | check | |
| | REPRODUCED_ACROSS_ENV | REPRODUCED_ACROSS_ENV | pass | check | Adds the note "environment differs". |
| | DIVERGED | DIVERGED | fail | cross | |
| | UNVERIFIABLE | UNVERIFIABLE | warn | triangle | |
| | NOT_RUN | NOT_RUN | neutral | dash | |
| Authenticity | NOT_ESTABLISHED | the value plus the API note | neutral-warn | triangle | Other values PENDING D5 (OD-7). Unknown values render neutral. |
| Isolation mode | ENFORCED | ENFORCED | pass | check | |
| | UNENFORCED | UNENFORCED | warn | triangle | Keeps the existing development-mode sentence. |
| Data mode | LIVE_EVIDENCE | LIVE_EVIDENCE | neutral | none | |
| | SYNTHETIC_DEMO | literal `SYNTHETIC_DEMO` | demo | flask | |
| Key record role | ILLUSTRATIVE | literal `ILLUSTRATIVE` | demo | flask | |
| API availability | checking, available, unreachable | "Checking API...", "API available", "API unreachable" | neutral, pass, warn | dot | `ApiStatusBadge`. |
| Any other value | any | `UNRECOGNISED <raw value>` | neutral | dash | Fail closed (DD-5). |

### D1.6 Landing page and onboarding

**Landing contents, in order.**

1. Header with the title "VerdictKit — Evidence Verification Workspace" as the document title and the `h1` (6.11).
2. Purpose text block of 1 to 100 words. The implementation test counts words.
3. Exactly two app cards, Quote Autopsy and Reel Autopsy. Each has one anchor, one sentence, and a data-mode line. Quote: constructed worksheets and user-submitted figures. Reel: `SYNTHETIC_DEMO` data only, and a real claim is BLOCKED.
4. "Release boundaries" block, always visible (6.2): Reel data is synthetic; external regulatory checks cover only jurisdictions with a verified Source_Snapshot, today Texas finance only, as the Quote app text states; authenticity is shown from the API authenticity object, today `NOT_ESTABLISHED` (unsigned).
5. API status strip (DD-11).
6. Onboarding_Flow.
7. Footer: "INTEGRITY, REPRODUCIBILITY, AUTHENTICITY and VERDICT are reported separately."

No statistics, customer counts, accuracy figures or testimonials (6.6). A test scans landing text for a number followed by `%` and for the words customers, users, "trusted by" and accuracy.

**Onboarding_Flow.** A labelled region with exactly five steps in this order (6.3). Each has a heading, one sentence and the real stage it corresponds to, taken from `STAGE_LABEL` in `components.tsx`.

| Step | Heading | Corresponds to |
|---|---|---|
| 1 | Freeze the claim | `POST /cases` and `POST /cases/{id}/freeze`: the frozen case with `specHash` and `ledgerSeq` |
| 2 | Seal the outcome | the `commitment` in the freeze response; claimed figures are write-only and are not shown back |
| 3 | Examine blind | `TASK_BLINDED`, `EXAMINATION_STARTED`, `EXAMINATION_PROGRESS`, `EXAMINATION_COMMITTED` |
| 4 | Reveal and compare | `OUTCOMES_REVEALED`, `VERDICT_SEALED` |
| 5 | Download and replay | `BUNDLE_WRITTEN` and the bundle download and replay controls |

Steps 1 and 2 are explanatory text that cite the values the API returned for the example; whether the freeze response exposes anything beyond `specHash`, `commitment` and `ledgerSeq` for display is checked against `api/openapi.yaml` at implementation.

**Example sources (6.4).**

- Reel `SYNTHETIC_DEMO` fixture `fx_reel_supported_hold`, run through the existing `useCaseWorkflow`, labelled `SYNTHETIC_DEMO` beside the example.
- One constructed Quote example from `examples.json`, labelled "constructed worksheet, not a real dealer quote".

The verdict shown is only the API outcome rendered by `VerdictView` (6.5). Fixture `expect` strings are never rendered. Where the examples live is OD-2. D1 recommends moving `examples.json` and the minimal builders to `ui-kit/src/examples/`, with the apps re-exporting them, so no workspace imports another app.

**Failure (6.9).** If the API is unreachable or returns an error during an example, a `role="alert"` message "The verdict could not be retrieved" appears, entered inputs stay, no verdict is shown, and a Retry button is offered. The five steps are static text and stay visible when the API is down (6.8).

### D1.7 Navigation and responsive layout

**AppShell** (new, shared by all three pages):

- A skip link "Skip to main content" as the first focusable element.
- `header` landmark with brand text.
- `nav` landmark with links Overview, Quote Autopsy, Reel Autopsy, and `aria-current="page"` on the current page.
- `main` landmark with an id.
- `footer` landmark with the separation line.
- The header is not sticky (2.4.11).

**Layout rules.**

| Rule | Value |
|---|---|
| Below `md` | Single column |
| From `md` | Two columns for form and guidance where useful |
| Content max width | 1100px |
| Form grid | `minmax(min(100%, 220px), 1fr)` so nothing overflows at 320px |
| Tables | Stay inside their own overflow-x container, given `tabindex="0"`, `role="region"` and an `aria-label` so the scroll area is keyboard reachable |
| Long hashes | `word-break` |
| Touch targets below `md` | At least 44x44 CSS px for buttons and file inputs. This is a design target. The WCAG 2.2 minimum is 24x24 (2.5.8). |

**Measurement (5.7).** Widths 320, 375, 768, 1024 and 1920. Pass when `document.documentElement.scrollWidth <= clientWidth`.

**Section order in the apps** is unchanged: header, API status, mode tabs, form or demos, stage and progress, verdict, bundle, replay.

### D1.8 State handling (loading, empty, error, API unavailable)

| State | Where | Rendering | Role or announcement | Requirement |
|---|---|---|---|---|
| API checking | all pages | Neutral "Checking API..." | `role="status"`, polite | 6.8 |
| API available | all pages | Health fields as returned | `role="status"` | DD-11 |
| API unavailable | landing | Message within 10 s. Static content and both app links remain. No verdict. | `role="alert"` | 6.8 |
| API unavailable | apps | `ErrorPanel` code `API_UNAVAILABLE`, reason, next step "Check that the API server is running, then retry", Retry button | `role="alert"` | 5.8 |
| Contract mismatch | all pages | `ErrorPanel` code `CONTRACT_MISMATCH`, next step "Use a matching UI and API build" | `role="alert"` | 5.8 |
| Form initial | apps | Empty form | none | |
| Submitting or running | apps | `aria-busy` on the progress region, humanized stage text, button disabled with "Examining...", existing `RunProgress` list | polite live region | 5.8, 6.9 |
| Empty verdict area | apps | `EmptyState` "No verdict yet. Submit a claim to see one." No verdict-like markup. | none | 5.8 |
| Draft blocked | apps | `Blockers`, `ParameterLedger` and a next step | `role="alert"` | 5.8 |
| Execution BLOCKED | apps | `Blockers`, headline NO VERDICT, next step per blocker code. Reel keeps its real-claim sentence about licensed data. | `role="alert"` | 5.8 |
| Execution INDETERMINATE | apps | Headline INDETERMINATE (warn), reason, next step | `role="status"` | 5.8 |
| API error envelope | apps | `ErrorPanel`: code, reason (message), field if any, next step | `role="alert"` | 5.8 |
| Network or non-JSON failure | apps | `ErrorPanel` with code `API_UNAVAILABLE` | `role="alert"` | 5.8 |
| Replay or bundle metadata error | `BundlePanel`, `ReplayUpload` | `ErrorPanel`, uploaded file retained in the control | `role="alert"` | 5.8 |

**ErrorPanel.** Shows code, reason and next step. Next-step text comes from a static map keyed by error code, with the fallback "Review the highlighted field, then submit again" for unknown codes. Known contract codes:

| Code | Next step |
|---|---|
| `PRIVACY_REJECTED` | Remove links, handles, emails and phone numbers from the pasted text, then resubmit. |
| `EVIDENCE_UNAVAILABLE`, `EVIDENCE_RIGHTS_UNVERIFIED` | No action is possible without licensed data. The claim is recorded and no verdict is shown. |

Error text never includes stack traces, file paths or raw exception text. `describeError` keeps its current output format so the E2E check for `PRIVACY_REJECTED` still passes. The full code list is read from `api/openapi.yaml` at implementation. PENDING: the complete code-to-next-step map, because the code list was not enumerated in this design.

### D1.9 Decimal rendering and synthetic labelling

**Decimal rendering (5.6, 2.1).** `DecimalText` is used for:

- `FindingCard` numbers: Computed, Claimed, Difference, Tolerance. The `±` prefix is a separate text node.
- `ParameterLedger` values and sweep ranges (min to max, step).
- `EvidenceTable` values.
- `KeyRecords` payload strings, printed verbatim.
- `EquityChart` labels and its `aria-label`.

`EquityChart` keeps `Number()` only inside `chartGeometry.ts` for coordinates. Labels are the original strings.

**Labels (5.3, 5.5).**

- `DataModeBadge` prints the literal `SYNTHETIC_DEMO` or `LIVE_EVIDENCE` in the same container as the specimen header.
- `ILLUSTRATIVE` is printed in the `figcaption` and as a visible tag at the top of the chart container.
- The two existing `demo-notice` banners stay.
- The wording is "verified at N grid points", N being the integer from the API. The singular "grid point" for N equal to 1 is kept.
- The phrases "all values", "every value" and "any value" and similar claims never appear in UI copy. A scan over `ui-kit/src`, `apps/*/web/src` and the landing source, excluding test files, rejects them, except the existing negation "not a claim about all values", allow-listed by exact string.

### D1.10 Accessibility

| Area | Design | Requirement |
|---|---|---|
| Keyboard | Only native `button`, `a`, `input`, `select`, `textarea`. Tab order follows DOM order. No positive `tabindex`. The only `tabindex` is `"0"` on scroll regions. | 7.1 |
| Focus | Focus ring token on every focusable element. No `outline: none` without a replacement. Header is not sticky. | 7.1 |
| Labels | Every input has a visible label. The wrapped-label pattern, fieldset legends and `aria-pressed` on group buttons stay. | 7.1 |
| Status messages | `role="status"` (polite) for progress and API status. `role="alert"` for errors. | 7.1 |
| Page language | `lang="en"` on all three `index.html`. The landing file is new. | 7.1 |
| Contrast | Token contrast test (D1.4). | 7.1 |
| Error identification | `ErrorPanel` lists the field name from the API `field`. Setting `aria-invalid` on that field is DESIGNED. Matching a field by label is PENDING implementation. | 7.1 |
| Colour not sole means | Text labels and glyphs (D1.5), text `P` and `F` in `SensitivityGrid` cells with the detail visible as text. | 5.4 |
| Motion, resize, reflow | Reduced-motion override. Relative units so 200% text resize loses nothing. Reflow at 320px. | 7.1 |

**Automated scan (7.2, 7.3).** axe-core runs against each of the three pages and the Onboarding_Flow, with rule tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` and `wcag22aa`. Each scan is recorded in the Evidence_Ledger with tool name, version, URL or step, timestamp, finding count and rule ids. A scan that does not complete is recorded UNVERIFIED.

**Manual checks (7.4).** Keyboard-only and screen-reader checks are tester actions recorded with tester, date, assistive technology name and version, and result. They are UNVERIFIED until recorded.

**Tooling.** jsdom cannot evaluate colour contrast or layout. Contrast is covered by the token test and overflow by the browser E2E. Tool choice is OD-3, PENDING.

### D1.11 Security and privacy

| # | Control | Check |
|---|---|---|
| 1 | No change to API contract 1.1.0, endpoints or response shapes. The UI keeps rejecting any other `contractVersion`. | `api.test.ts` |
| 2 | Claimed outcomes and pasted text stay write-only: sent once, cleared on acceptance, never in URLs, `localStorage`, `sessionStorage`, cookies, console output, error text or analytics (2.3). D1 adds no persistence, analytics, telemetry, or fonts and scripts from other origins. | Scan test rejects `localStorage`, `sessionStorage`, `document.cookie`, `console.*` and `fetch` to absolute URLs in `ui-kit/src`, `apps/*/web/src` and the landing source. |
| 3 | Isolation is displayed, not implied. The banner shows the API `isolationMode`. The landing page never states ENFORCED unless `/health` returned it. | Component test |
| 4 | React text nodes only. No `dangerouslySetInnerHTML`, `innerHTML` or `eval`. API strings render as text. The only link built from API data is the bundle URL from `client.bundleUrl`, with `encodeURIComponent`. | Scan test |
| 5 | CSP: keep each `index.html` meta policy (`default-src 'self'`, `script-src 'self'`, `connect-src 'self'`, `object-src 'none'`, `base-uri 'none'`, `form-action 'none'`) and add the same to the landing page. The landing page has no cross-origin fetch. App links are navigation only. Health is fetched same-origin through `/api` (dev proxy now, hosting origin is D2). `'unsafe-inline'` for `style-src` exists today. Removing it is OD-4. Response headers are D2 (7.5). | Meta tag test |
| 6 | `rel="noopener noreferrer"` on any anchor with an absolute different-origin href. | Component test |
| 7 | Synthetic data is never presented as a real result: `DataModeBadge`, demo notices, onboarding labels (5.3, 6.4). | AC-5, AC-11 |
| 8 | The UI never computes a verdict, tolerance, status or pass. Tone mapping only classifies a status the API supplied (2.9). | Review and AC-4 |
| 9 | Replay semantics unchanged. The replay button text keeps "(no network)" (2.8). | Component test |

### D1.12 Files and components for future implementation

All entries are DESIGNED.

| Path | New or modify | Purpose | Requirement |
|---|---|---|---|
| `ui-kit/src/tokens.css`, `tokens.ts` | new | Tokens and contrast inputs | 5.1, 7.1 |
| `ui-kit/src/theme.css` | modify | Import tokens, focus, reduced motion, layout. Class names kept. | 5.1, 5.7 |
| `ui-kit/src/decimal.tsx` | new | `DecimalText`, `compareDecimalStrings` | 5.6 |
| `ui-kit/src/chartGeometry.ts` | new | Coordinates only. The one allow-listed float file. | 5.6 |
| `ui-kit/src/status.tsx` | new | `StatusBadge` (re-exported), `IntegrityBadge`, `ReproducibilityBadge`, `AuthenticityBadge`, `DataModeBadge`, `ApiStatusBadge`. `statusTone` unchanged. | 5.4, 10.33 |
| `ui-kit/src/shell.tsx` | new | `AppShell`, `SkipLink`, `SiteNav` | 6.1, 7.1 |
| `ui-kit/src/feedback.tsx` | new | `ErrorPanel`, `EmptyState`, `LiveStatus`, `LoadingNote` | 5.8, 6.9 |
| `ui-kit/src/components.tsx` | modify | `EquityChart`, `SensitivityGrid`, `ReportView`, `BundlePanel`, `VerdictView`, error rendering. No renamed test ids. | 5.2 to 5.6 |
| `ui-kit/src/api.ts` | modify | `requestTimeoutMs`, `ApiUnavailableError` | 6.8 |
| `ui-kit/src/types.ts` | modify | Authenticity widened to `{ status: string; note: string }`. Reproducibility status typed as the contract values plus a string fallback. | 10.20 |
| `ui-kit/src/index.ts` | modify | Export new modules | |
| `ui-kit/src/examples/` | new (per OD-2) | Shared example data and builders | 6.4 |
| `apps/quote-autopsy/web/src/App.tsx`, `apps/reel-autopsy/web/src/App.tsx` | modify | `AppShell`, `ErrorPanel`, `EmptyState`, humanized stage text, DD-9 | 5.8 |
| `apps/*/web/vite.config.ts` | modify | Ports from environment (DD-12) | 1.17 |
| `apps/*/web/index.html` | modify only if title or landmarks need it | | 7.1 |
| `apps/landing/web/` (`package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/Onboarding.tsx`, `src/App.test.tsx`, `src/Onboarding.test.tsx`) | new | Landing workspace. `index.html` has the required title, `lang="en"` and a CSP meta tag. Page-specific pieces (`HeroPurpose`, `ReleaseBoundaries`, `AppCard`, `LifecycleSteps`) live here (OD-5). | 6.1 to 6.11 |
| Root `package.json` | modify | Add `apps/landing/web` to workspaces | 6.10 |
| `scripts/ui_e2e.sh`, `tests/ui/e2e_browser.cjs` | modify, additive only | Configurable ports, landing checks. No baseline check removed or skipped. | 1.17, 5.9 |
| `ui-kit/src/{tokens,decimal,status,feedback,shell}.test.*`, `source-scan.test.ts`, extended `components.test.tsx` and `api.test.ts` | new and modify | Tests in D1.13 | 5.10 |

No file in `core/`, `api/`, `tests/contract`, `ui/judge` or the Submission_Artifacts is modified by D1.

### D1.13 Test plan and measurable acceptance

Nothing below is VERIFIED. Browser-dependent criteria (AC-8, the browser part of AC-13 and AC-14, and the E2E in AC-16) run on a Linux host or in CI, because the Windows host could not run `ui_e2e.sh` (D0.3). Criteria that use jsdom only can run on Windows.

| ID | Measurable criterion | Method | Pass threshold | Req | Environment |
|---|---|---|---|---|---|
| AC-1 | No hex colour, `px` font size or raw spacing outside `tokens.css` | Vitest scan | 0 matches | 5.1 | Windows, Linux |
| AC-2 | Contrast of every pair in D1.4 | Vitest, ratios computed from `tokens.ts` | 0 pairs below 4.5 (normal) or 3 (large, UI boundary) | 5.4, 7.1 | Windows, Linux |
| AC-3 | Verdict view shows headline, every finding, confidence scope sentence and isolation without interaction | Render the three `api/examples` outcomes, assert strings with no click | All present | 5.2 | Windows, Linux |
| AC-4 | Every status in D1.5 renders a non-empty text label. An unknown value renders `UNRECOGNISED` with neutral tone. | Iterate enum values | 0 empty labels, 0 positive tones for unknown | 5.4, 2.4 | Windows, Linux |
| AC-5 | `SYNTHETIC_DEMO` and `ILLUSTRATIVE` literals in the same container as the content they qualify | Component test | Present | 5.3 | Windows, Linux |
| AC-6 | "verified at N grid points" present, forbidden phrases absent | Component test and scan | 0 forbidden matches | 5.5 | Windows, Linux |
| AC-7 | Displayed text equals the supplied string in every money and rate path. No float conversion outside `chartGeometry.ts`. | Table of at least 50 fixed strings (leading and trailing zeros, 28 or more digits, negative, `0.10`, `-0.00`, one invalid string), or fast-check if OD-3 accepts it. Scan for `Number(`, `parseFloat`, `toFixed`, `toLocaleString`, `Intl`. | 0 mismatches, 0 scan matches | 5.6, 2.1 | Windows, Linux |
| AC-8 | No horizontal scroll at 320, 375, 768, 1024, 1920 on the three pages | Playwright, `scrollWidth <= clientWidth` | 15 of 15 combinations | 5.7 | Linux CI. UNVERIFIED on Windows unless a browser is available. |
| AC-9 | `ErrorPanel` shows code, reason and next step for each contract error fixture and for network failure. Form values remain after a failed `createCase`. | Component tests | All present | 5.8 | Windows, Linux |
| AC-10 | With a fetch that never resolves and fake timers, the landing page shows the unreachable message at or before 10000 ms, no verdict element, and both app links | Vitest fake timers | Met | 6.8 | Windows, Linux |
| AC-11 | Five onboarding steps in the required order. Exactly 2 app anchors. Purpose text of 1 to 100 words. 0 statistic or testimonial matches. Title equals the required title. Onboarding verdict equals the mocked API response. Fixture `expect` strings absent from the DOM. | Component tests | All met | 6.1 to 6.6, 6.11 | Windows, Linux |
| AC-12 | Onboarding failure keeps inputs, shows an alert and no verdict. Retry works. | Component test | Met | 6.9 | Windows, Linux |
| AC-13 | axe scans of three pages and onboarding steps | axe-core, tags in D1.10, recorded per 7.2 | 0 violations. If the scan cannot run, UNVERIFIED. | 7.1 to 7.3 | jsdom units: Windows, Linux. Browser: Linux CI. |
| AC-14 | Skip link is first in tab order. Every control reachable and operable by keyboard. Focus style present in computed style. | `userEvent` for order, Playwright for computed style | Met | 7.1 | Both, as noted |
| AC-15 | Each modernized component has a unit test asserting label text and status text that fails if either is removed. Components: `StatusBadge` and the new badges, `IsolationBanner`, `DemoNotice`, `Blockers`, `ParameterLedger`, `RunProgress`, `FindingCard`, `SensitivityGrid`, `EvidenceTable`, `EquityChart`, `KeyRecords`, `Diagnostics`, `VerdictView`, `BundlePanel`, `ReplayUpload`, `ErrorPanel`, `EmptyState`, `AppShell`. | Vitest, with a mutation check that removes the text | Each test fails when its text is removed | 5.10 | Windows, Linux |
| AC-16 | `typecheck`, `test`, `build` exit 0 for `ui-kit`, quote, reel and landing. Browser E2E passes 100% of existing checks with none removed or skipped, plus new landing checks. | npm scripts, `ui_e2e.sh` | Exit 0, all checks pass | 5.9, 6.10 | npm: Windows, Linux. E2E: Linux CI. |
| AC-17 | 0 uses of `localStorage`, `sessionStorage`, `document.cookie`, `console`, `dangerouslySetInnerHTML`, `innerHTML`, `eval` in UI source | Scan | 0 matches | 2.3 | Windows, Linux |
| AC-18 | No hard-coded 4173, 4174, 4175, 8000 or 5173 in scripts or Vite configs other than documented defaults | Scan | 0 undocumented matches | 1.17 | Windows, Linux |

**Correctness properties.** PENDING D10. Candidate names only: decimal-display-identity, status-fail-closed, no-verdict-without-API-outcome, input-retention-except-sealed-claims, no-persistence-of-claimed-values.

### D1.14 Requirement traceability

| D1 sub-section | Requirements |
|---|---|
| D1.1 | 5, 6, 7.1 to 7.4, 1.17, 10.20, 10.32, 10.33, 12.14 |
| D1.2 | 5.1 to 5.9, 6.1, 6.8, 6.9, 7.1, 2.1, 2.3, 2.4, 10.20, 10.32, 10.33 |
| D1.3 | 5.1, 5.6, 5.8, 6.1, 6.8, 6.10, 10.32, 10.33, 1.17, 2.1, 2.3, 2.4 |
| D1.4 | 5.1, 5.4, 7.1 |
| D1.5 | 5.2, 5.3, 5.4, 2.4, 10.32, 10.33 |
| D1.6 | 6.1 to 6.9, 6.11, 5.3, 10.32 |
| D1.7 | 5.7, 6.1, 7.1 |
| D1.8 | 5.8, 6.8, 6.9, 7.1 |
| D1.9 | 5.3, 5.5, 5.6, 2.1 |
| D1.10 | 7.1, 7.2, 7.3, 7.4, 5.4 |
| D1.11 | 2.3, 2.8, 2.9, 2.4, 10.32 |
| D1.12 | 5.1 to 5.10, 6.10, 1.17 |
| D1.13 | 5.1 to 5.10, 6.1 to 6.11, 7.1 to 7.4, 1.17, 2.1, 2.3, 2.4 |
| D1.15 | 6.1, 5.8, 7.5, 10.20 |

Coverage of R5 and R6: 5.1 (AC-1), 5.2 (AC-3), 5.3 (AC-5), 5.4 (AC-2, AC-4), 5.5 (AC-6), 5.6 (AC-7), 5.7 (AC-8), 5.8 (AC-9), 5.9 (AC-16), 5.10 (AC-15), 6.1 to 6.6 and 6.11 (AC-11), 6.7 (AC-13, AC-14), 6.8 (AC-10), 6.9 (AC-12), 6.10 (AC-16), 7.1 to 7.4 (AC-13, AC-14), 1.17 (AC-18). Every D1 component in D1.12 maps to at least one requirement (4.2).

### D1.15 Open decisions

All items are PENDING.

| ID | Decision | Options | Recommendation | Owner or dependency |
|---|---|---|---|---|
| OD-1 | Where the apps are served in hosting and the final `VITE_*_URL` values | Subpaths of one origin; separate origins | Decide with the hosting target | D2 |
| OD-2 | Location of shared onboarding examples | Import across workspaces; move to `ui-kit`; duplicate | Move to `ui-kit/src/examples/` and re-export from the apps | Maintainer |
| OD-3 | Accessibility and property-test tooling | `vitest-axe` or `jest-axe` for jsdom; `@axe-core/playwright` in CI; `fast-check`; Playwright in `package.json` or CI only | `@axe-core/playwright` in the Linux `web-ui` job plus `vitest-axe` for jsdom units. `fast-check` optional. All as pinned devDependencies with a lockfile update. | Maintainer approval, because `package-lock.json` changes |
| OD-4 | Remove `'unsafe-inline'` from `style-src` | Remove now; remove with D2 headers; keep | Remove with D2 headers | D2 (7.5) |
| OD-5 | Location of landing-specific components | `apps/landing/web/src`; `ui-kit` | `apps/landing/web/src`, with `ui-kit` only for reused parts | Maintainer |
| OD-6 | Wording of 5.8 against write-only claimed figures | Keep DD-9 reading; amend 5.8 to except sealed claimed fields | Keep DD-9 and confirm it in review. Do not edit requirements in this phase of the design. | Independent reviewer, maintainer |
| OD-7 | Authenticity positive tone and field names | Wait for D5; define now | Wait for D5. Render neutral until then. | D5 |
| OD-8 | Whether `ui/judge` links to the landing page | Link; leave unchanged | Leave unchanged (DD-10) | Maintainer |
| OD-9 | Final token colour values | Choose at implementation | Choose to pass the contrast test and record the ratios | Implementation, contrast results |

The maintainer's decisions on OD-1 to OD-9 are recorded in D1.16.

### D1.16 Maintainer decisions on open items (conditional approval)

The maintainer approved D1 conditionally. Each decision below is DECIDED and DESIGNED. None is implemented.

| ID | Decision | Effect on D1 text |
|---|---|---|
| OD-1 | Application paths are configurable and same-origin. They are finalized in D2 (see D2.3). | DD-3 hosted URL values come from D2. Local defaults in DD-3 and DD-12 are unchanged. |
| OD-2 | Public synthetic examples may be shared through `ui-kit/src/examples/`, as D1.6 recommended. | D1.6 and D1.12 stand. |
| OD-3 | Minimal accessibility and property-testing dev dependencies are approved. Versions are exact (no ranges). The reviewer inspects the `package-lock.json` diff before merge. | Package choice stays as D1.15 recommends. `fast-check` remains optional. |
| OD-4 | Prefer a CSP without `unsafe-inline`. Actual requirements are determined in D2 (see D2.5). | D1.11 item 5 is superseded by DD2-5 where they differ. |
| OD-5 | Shared components live in `ui-kit`. Landing-specific components live in `apps/landing/web/src`. | D1.12 stands. |
| OD-6 | Preserve write-only claimed-input boundaries. Sealed claimed figures and sensitive pasted text are cleared after server acceptance. They are never persisted and never exposed through logs or error messages. | DD-9 stands. The conflict of D1.2 finding 12 with 5.8 is resolved by keeping DD-9. `requirements.md` is not edited. |
| OD-7 | Authenticity field semantics are finalized in D5. | D1 keeps neutral rendering until then. |
| OD-8 | `ui/judge` stays unchanged. | DD-10 stands. D2 does not deploy it. |
| OD-9 | Professional design tokens are chosen subject to WCAG 2.2 AA verification. | The contrast test in D1.4 and AC-2 remains the gate. |

**Clarifications that bind D1 and later sections.**

- **(a) Historical bundle isolation and current server isolation are different facts.** A Bundle's manifest `isolation_mode` (surfaced as `isolationMode` in bundle metadata) is the value recorded when the Bundle was written. `isolationMode` from `/api/v1/health` is the server state at the time of that request. The UI labels them separately, for example "Isolation recorded in this bundle" and "Server isolation now", and never uses one to imply the other. A replay result reports the replaying server's isolation separately.
- **(b) Browser request cancellation is not server execution cancellation.** DD-8 `requestTimeoutMs` with `AbortController` only stops the browser waiting. The server has no cancel endpoint. `POST /cases/{id}/runs` runs synchronously in the request thread and continues after the client disconnects, and the examiner worker finishes the task it started. UI text says "stopped waiting" and never says "cancelled", "stopped" or "aborted" about the run. A timed-out run is checked by polling `GET /cases/{id}/runs/{runId}` or `GET /cases/{id}/outcome`.
- **(c) No automatic retry of state-changing requests without safe idempotency.** Read from `api/server.py`: `POST /cases` is not idempotent (each call creates a case), `PATCH /cases/{id}` mutates, `POST /freeze` and `POST /evidence` return 409 on repeat, `POST /replays` is stateless but expensive, and `POST /runs` is idempotent per case (an existing run for the case is returned). The UI client and any proxy or edge retry only GET and HEAD automatically. A Retry button is an explicit user action. Automatic retry of POST, PATCH and PUT is forbidden at the UI, the edge and the load balancer (D2.5, DD2-7).

Traceability: OD-1 to OD-9 map to 5.1, 6.1, 6.4, 7.5, 10.20, 1.17, 2.3 and 7.1.

## D2. P1 Secure public deployment

### D2.1 Scope and status

**Covers.** Requirement 7 criteria 7.5 to 7.18, and the security items below: access policy, case ownership, resource limits, retries, logging, retention, health disclosure and image reproducibility.

**Does not cover.** Criteria 7.1 to 7.4 (accessibility), which belong to D1. D2 does not change the semantics of Isolation_Mode `ENFORCED`. No target that cannot give `ENFORCED` is accepted. Nothing in D2 downgrades, bypasses or disables an isolation control (7.18, 2.5 to 2.7).

**Status.** Everything in D2 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. No infrastructure is provisioned and no charge is incurred. Every AWS figure is an ASSUMPTION to be re-checked at provisioning.

| Cross-track note | Owner | Content |
|---|---|---|
| D1 | D1 | Base-path support in the three UI builds, meta CSP no weaker than the header, 401 message, historical and current isolation labels (D2.11 B-11). |
| D5 | D5 | Owner cookie and `commitSha` and 503 health body against contract 1.1.0 (OD-D2-3). |
| D8 | D8 | Threat_Model rows for cross-owner access, resource exhaustion, log leakage and sweeper correctness. |
| D9 | D9 | Release provenance: commit, image digest, Execution_Record (7.13, 14.17). |

### D2.2 Inspected baseline and findings

Files read: `Dockerfile`, `.dockerignore`, `deploy/entrypoint.sh`, `core/src/verdictkit/api/{server.py, __main__.py, check_startup.py, draft_store.py, run_service.py}`, `core/src/verdictkit/examiner/{worker.py, client.py, identity.py}`, `core/src/verdictkit/{bundle.py, envprint.py, evidence/store.py}`, `core/pyproject.toml`, `.github/workflows/p0-integration.yml`, `ui-kit/src/api.ts`, `apps/*/web/{vite.config.ts, index.html}`, `ui/judge/index.html`, and requirements 7.1 to 7.18.

| ID | Finding (read from file) | Consequence for public deployment |
|---|---|---|
| F-1 | `Dockerfile`: base `python:3.12-slim` and the `uv` image are pinned by sha256. `uv sync --frozen --all-packages --all-extras --group dev` installs dev dependencies and `tests/` into the same image. `apt-get update` plus install of `util-linux procps ca-certificates` is unpinned (whether `util-linux` is already in the base: UNVERIFIED). `COPY uv.lock*` is optional but `--frozen` fails if the file is absent. No HEALTHCHECK, no OCI labels, no commit build argument. No web build output and no `ui/` in the image. | Dependency set is pinned. Apt layer is not. The image has no commit identity and no static pages (D2.7). |
| F-2 | Entrypoint `serve`: requires `VK_VAULT_KEY` (`${VAR:?}` also rejects empty). `VK_JUDGE_MODE` defaults to 0, so without it the API starts with Isolation UNENFORCED and an in-process examiner. `serve` never prints `VK_STARTUP_OK` (only `--check-startup` does). The root shell stays alive as parent in `wait -n`, which contradicts the comment "no long-lived root process remains", and holds `VK_VAULT_KEY` in its environment. No signal trap. uvicorn starts with `--host 0.0.0.0` and default access logging. Children start through `setpriv --no-new-privs` with `env -i` allowlists, and only the custodian receives `VK_VAULT_KEY`. | Default is the downgrade path a public deployment must close. 7.7 is not met by `serve`. Residual R-1 (D2.11). |
| F-3 | `check_startup.isolation_enforced`: Linux only. Checks euid is `vk-custodian`, uids differ, vault dir uid and mode 0700, socket owner, group `vk-ipc`, mode 0660, group membership and a live `SO_PEERCRED` connect. Evaluated once at app creation, so `/health` reports a fixed value. At run time `_make_examiner` builds a `SocketExaminer` that re-verifies the socket and peer UID, and every `examine` re-verifies peer credentials. Failure becomes `_Unavailable` and the run fails closed (`RUN_FAILED`). | Runs already fail closed. Health does not reflect later loss of isolation (DD2-2, D2.6). |
| F-4 | Examiner worker: single-threaded accept loop (backlog 16). `RLIMIT_CPU` 300 s and `RLIMIT_AS` 2 GiB are process-lifetime limits, so cumulative CPU over many tasks can reach 300 s and kill the worker (SIGXCPU). `wait -n` then ends the container (fail closed, state lost). No per-task deadline. Client timeout is 60 s, but the worker keeps computing after the client closes. The worker prints `examiner error: {exc}` to stderr. Per-run CPU cost is UNMEASURED. | Restarts are a capacity symptom. Exception text reaches logs (DD2-9, DD2-6). |
| F-5 | `SafetyMiddleware`: in-memory per-client limiter (120/min) keyed by `request.client.host`, so behind a proxy all users share one key (uvicorn proxy headers are not enabled). Caps 256 KiB JSON and 8 MiB for paths ending `/replays`. The body is fully buffered in memory before routing. Only `X-VerdictKit-Contract`, `Cache-Control: no-store` and `nosniff` are set, and only on responses that reach `call_next`. The 429, 413 and 400 early returns do not get them. 500 handling is outside the middleware (UNVERIFIED). No CSP, Referrer-Policy, HSTS or frame protection. | 7.5 is not met today. Rate limiting is wrong behind a proxy (DD2-5, DD2-6). |
| F-6 | No authentication, authorization or ownership anywhere in `api/`. Case ids are `case_` plus a uuid4 hex (random bearer ids). No listing endpoint. Any holder of an id can read the case, outcome, bundle and events. No CORS middleware. `docs` and `openapi` routes are disabled. | A public deployment needs an access policy and ownership (DD2-3, DD2-4). |
| F-7 | `POST /runs` executes the whole run inside the request (sync handler in the thread pool) with no global run limit. SSE streams poll SQLite every 0.25 s for up to 120 s each with no connection cap. `/replays` has a 2-slot semaphore, an 8 MiB body, zip limits (4096 entries, 16 MiB per entry, 64 MiB uncompressed) and writes verified embedded evidence into the shared evidence directory when ENFORCED. `EvidenceStore` has put, get and item only, so blobs are never deleted. No case-count, evidence or bundle quota. | Resource exhaustion and unbounded storage (DD2-6, DD2-10). |
| F-8 | `draft_store`: SQLite plus AES-256-GCM, TTL at most 86400 s. Judge mode (`expire_frozen`) expires frozen cases too. Purge runs only opportunistically (at most once per 60 s, and only when a request calls `store()`), so with no traffic expired data stays on disk. Purge removes bundle files but not evidence blobs. | Retention is traffic-dependent (DD2-10). |
| F-9 | `/api/v1/health` is a static dict computed at app creation: `contractVersion`, `status` "ok", `isolationMode`, `judgeMode`, `engineVersion` "0.1.0". No commit SHA (needed by 7.13). Status is always ok. | Health is not a readiness signal (D2.6). |
| F-10 | No logging module in `api/`. uvicorn's default access log records request paths that contain case ids. `__main__` prints only fixed codes. The examiner prints exception text (F-4). | Case ids reach logs unless changed (DD2-9). |
| F-11 | `createClient(base='/api/v1')` is same-origin relative. Vite dev and preview proxy `/api`. Each app `index.html` has a meta CSP with `style-src 'self' 'unsafe-inline'` and `img-src 'self' data:`. No `style=` attributes, `<style>` blocks, `<img>` or `url(` were found in `ui-kit/src` or `apps/*/web/src`, so `'unsafe-inline'` appears unnecessary in a production build (UNVERIFIED in a browser). A meta tag cannot set `frame-ancestors`. `ui/judge` has a stricter meta CSP and is not deployed. | CSP can be tightened (DD2-5). |
| F-12 | `p0-integration.yml` builds the image and runs `gate-isolation`, `gate-startup`, `gate-http` and `gate-case` with `--network none` on `ubuntu-latest`. No registry push, image scan, SBOM, deploy job or external smoke test. | Deployment gates are all new (D2.8). |
| F-13 | `envprint` reads `VK_IMAGE_DIGEST` but nothing sets it, so Bundles record `imageDigest` "unknown". | Digest injection is needed (D2.6). |

Each finding was read directly from the named file in the working tree on 2026-11-24 (branch `feature/kiro-next-phase`, based on commit `84df25c`). Reading is not execution: nothing in F-1 to F-13 was run, so behaviour claims such as the 500-response header handling and the worker CPU limit stay UNVERIFIED where marked.

### D2.3 Public architecture and same-origin routing

```mermaid
flowchart LR
  NET[Internet] --> TLS[TLS terminator: AWS Route 53 + ALB with ACM, or VM with Caddy ACME]
  TLS --> EDGE[Edge container: Caddy, non-root, static files, headers, body caps, no retries]
  EDGE -->|API port, edge only| API[API container: root entrypoint]
  API --> CUS[custodian uid 900]
  API --> EXA[examiner uid 901]
  CUS <-->|local socket| EXA
  VOL[(vault, drafts, evidence: local to API container)] --- CUS
```

**Topology rules.**

1. The edge container mounts no vault, draft, evidence or socket volume and receives no `VK_VAULT_KEY`.
2. The examiner socket and the vault never leave the API container.
3. Only the edge port is reachable from the internet. The API port is reachable only from the edge (security group or docker network).
4. There is one API task: `desiredCount` 1, no horizontal scaling, no HA (SQLite, in-memory limiter and local socket require it). Task replacement loses all cases. This is ephemeral by design (24 h TTL) and is documented to users.
5. The edge has retries off (Caddy `reverse_proxy` with `lb_try_duration` 0 and no retry). The ALB is not configured to retry. POST and PATCH are never replayed.

| Path | Served by | Notes |
|---|---|---|
| `/` | Edge static: landing | |
| `/quote/` | Edge static: Quote Autopsy | |
| `/reel/` | Edge static: Reel Autopsy | |
| `/api/v1/*` | API | Prefix is fixed by the contract and the `ui-kit` default base. Not configurable. |
| `/quote`, `/reel` | Edge redirect to the slash form | GET only. |
| anything else | Edge 404 with headers | No SPA fallback (D1 DD-2 has no router). `ui/judge` is not served. |

**Configuration (resolves OD-1).** Build-time `VK_BASE_LANDING` (default `/`), `VK_BASE_QUOTE` (default `/quote/`) and `VK_BASE_REEL` (default `/reel/`). Each starts and ends with `/`, and they are distinct and non-overlapping except for the root. A script validates them. They feed Vite `base`, the landing links and the Caddyfile template. The landing links become same-origin relative paths in place of the hosted values of `VITE_QUOTE_URL`, `VITE_REEL_URL` and `VITE_LANDING_URL`. Local defaults from D1 DD-3 and DD-12 are unchanged.

A route check script asserts that every built HTML file references only paths under its base and no absolute `http(s)` URL. No CORS header is ever sent. A POST, PATCH, PUT or DELETE with an `Origin` header that is not `VK_PUBLIC_ORIGIN` gets 403 at the edge and in the API. D1 UI files need base-path support. This is a coordination item for D1 and does not reopen D1.

### D2.4 Hosting feasibility

**(a) What the code needs from a host.**

| Isolation primitive the code uses | Where | What a host must provide |
|---|---|---|
| Two non-root OS users plus group `vk-ipc` in one container | `Dockerfile` `useradd`, `groupadd` | Image runs as built, no uid remapping. |
| Root entrypoint with `chown` and `install` | `deploy/entrypoint.sh` | Capabilities such as CAP_CHOWN, CAP_FOWNER, CAP_DAC_OVERRIDE. Minimal set UNVERIFIED. |
| `setpriv --reuid --regid --init-groups --no-new-privs` | `deploy/entrypoint.sh` | CAP_SETUID and CAP_SETGID. |
| AF_UNIX socket with `SO_PEERCRED` | `verify_connected_peer` | Real uids visible to the kernel, no user-namespace remapping. |
| Vault 0700 uid 900, evidence 0750 | `check_startup` stat checks | Writable storage that honours POSIX owner and mode. |
| `env -i` allowlist | entrypoint | No host-injected environment reaches children. |
| No cross-uid `/proc` reads | design | Never add SYS_PTRACE. No ECS Exec or `docker exec` for non-operators. |

**(b) AWS ECS Fargate evaluation (7.17).** Source: AWS developer guide and ECS best-practices guide pages read during this design. Content was rephrased for compliance with licensing restrictions.

| Criterion | Evidence | Status |
|---|---|---|
| Capabilities | Only SYS_PTRACE can be added. Defaults are Docker's. The exact default set on Fargate was not re-verified. | UNVERIFIED |
| Container security options | `privileged`, `dockerSecurityOptions`, `ipcMode`, `devices` and `sharedMemorySize` are unsupported. None is needed and none can weaken isolation. Container-level seccomp and no-new-privileges cannot be set, so hardening relies on `setpriv --no-new-privs`. | Documented |
| tmpfs | The developer guide says unsupported. A 6 Jan 2026 AWS announcement says supported. | CONFLICTING. Design does not depend on tmpfs. |
| Volumes | Bind-mount (task ephemeral) volumes only. `dockerVolumeConfiguration` is unsupported. `/var/lib/vk`, `/run/vk` and `/tmp` use ephemeral volumes with `readonlyRootFilesystem` true. The entrypoint's `install -d` sets modes and owners at start. Whether Fargate volume mounts honour the owner and mode that the entrypoint sets is not verified. | UNVERIFIED |
| Ephemeral storage | 20 GiB default, up to 200 GiB, encrypted with a Fargate-managed AES-256 key, not durable. | Documented |
| Secrets | ECS `secrets` injects from Secrets Manager into the container environment. The root PID holds `VK_VAULT_KEY`. Children get it only through the entrypoint allowlist. | Documented |
| Init process | `initProcessEnabled` for signal forwarding and zombie reaping. Not listed as restricted. | UNVERIFIED |
| Network | awsvpc. The examiner shares the network namespace with the custodian, so egress cannot be separated per user (R-2). The examiner needs no network, and the HTTP API evidence broker is `network=False`. Security-group egress is limited to what the agent needs. | Residual risk R-2 accepted |
| Replicas | One. The design does not rely on Fargate's per-task boundary. | Decided |

**DD2-1: Fargate is a CONDITIONAL candidate.** No documented blocker was found, but no needed primitive has been verified on Fargate. Fargate is NOT accepted for judge mode until an owner-authorized one-off probe task runs the four existing gates (`gate-isolation`, `gate-startup`, `gate-http`, `gate-case`) with captured output and a recorded Execution_Record. Any failure rejects Fargate for judge mode (7.18). Forbidden workarounds: running both roles as one uid, removing the `PEERCRED` check, setting isolation by flag only, setting `VK_JUDGE_MODE=0`, adding SYS_PTRACE, privileged mode, disabling no-new-privs, and sharing the vault with the edge.

**(c) Alternative and portable reference (Plan B, 7.16).** One Linux VM (EC2 or any provider) runs Docker Engine and docker compose with the same image digest and the same entrypoint.

- API container: `--read-only`, writable named volumes or tmpfs for `/var/lib/vk`, `/run/vk` and `/tmp`, `--pids-limit`, `--memory`, `--cpus`, Docker's default seccomp and AppArmor profiles.
- Not used: `--privileged`, host PID or network, a docker socket mount, user-namespace remap.
- Capabilities: run the gates with `--cap-drop ALL` and add back only what they need (which ones: UNVERIFIED).
- Caddy edge container terminates TLS with ACME and serves static files. The host firewall allows 80 and 443, and SSH only from the operator (or SSM instead of SSH).
- Trade-offs: more control and lower cost, against host patching and Docker upgrades as an operator duty, one host and no managed replacement. ECS on EC2 is acceptable only if it passes the same four gates.

**(d) Cost assumptions.** us-east-1, 730 h per month, on-demand. NOT a quote. Re-check at provisioning. Sources: AWS Fargate and Elastic Load Balancing pricing pages and third-party summaries retrieved during this design.

| Item | Assumption | Per month |
|---|---|---|
| Fargate 1 vCPU, 2 GiB | $0.04048 per vCPU-h plus $0.004445 per GiB-h = $0.04937 per h | about $36.0 |
| ALB | $0.0225 per h | about $16.4 |
| ALB LCU | 1 LCU assumed, $0.008 per h | about $5.8 |
| Public IPv4 | $0.005 per h each: ALB across 2 AZs, task public IP | about $7.3 and $3.7 |
| Secrets Manager | 2 secrets | about $0.8 |
| Route 53 | one hosted zone | about $0.5 |
| ECR and CloudWatch Logs | 14-day retention, assumed | about $2 to $4 |
| **Fargate variant total** | | **about $73** |
| Optional WAF | web ACL, 2 rules, requests, assumed | about $8 |
| NAT gateway alternative | adds, plus data | about $33 |
| VPC interface endpoint | each | about $7.3 |
| VM variant | one small VM and disk, assumed | about $15 to $30 |

A 14-day demonstration costs about half. A budget alarm is required. The monthly cap is chosen by the owner (PENDING).

### D2.5 Security decisions

| ID | Decision | Rejected alternative | Why |
|---|---|---|---|
| DD2-2 | Public profile `VK_PROFILE=public` makes judge mode mandatory (below). | Relying on the default `VK_JUDGE_MODE=0`. | The default is the downgrade path (F-2). |
| DD2-3 | Three access tiers (below). Default is fail-closed. | Open anonymous access to case routes. | No auth or ownership exists (F-6). |
| DD2-4 | Case ownership by owner cookie (below). | Case id as the only secret. | Ids are bearer tokens that can leak through logs, history and shared links. |
| DD2-5 | CSP without `unsafe-inline` and headers on every response (below). | Keep the meta CSP of D1.11. | No inline use found (F-11). Meta cannot set `frame-ancestors`. |
| DD2-6 | Layered resource limits (below). | Rely on the 120/min limiter alone. | It is keyed wrongly behind a proxy and does not bound runs or storage (F-5, F-7). |
| DD2-7 | No automatic retry of state-changing requests. | Edge or ALB retries for availability. | POST and PATCH are not idempotent (D1.16 c). |
| DD2-8 | Secrets only in the provider secret store. | Build-time or repo-stored secrets. | 7.9. |
| DD2-9 | Privacy-safe structured logging. | Default uvicorn access log. | Paths contain case ids (F-10). |
| DD2-10 | Retention sweeps independent of traffic. | Opportunistic purge only. | Expired data stays on disk with no traffic (F-8). |

**DD2-2 Judge mode in the public profile (DESIGNED change to `deploy/entrypoint.sh`, not made now).** The profile refuses to start, with a non-zero exit and a stderr message that states isolation is unavailable or the key is missing, and with no key value printed, unless all of these hold:

- `VK_JUDGE_MODE=1`, and `VK_VAULT_KEY` is non-empty and decodes as base64 to 32 bytes.
- `VK_OWNER_BINDING=1`, and `VK_PUBLIC_ORIGIN` is an `https` origin.
- `python -m verdictkit.api --check-startup`, run as the custodian, prints `VK_STARTUP_OK isolation=ENFORCED`.

`serve` then prints that line exactly once, before the API listens (7.7, 7.8, 7.10).

**DD2-3 Access policy.**

| Tier | Routes | Control |
|---|---|---|
| P, anonymous | Static pages, `GET /api/v1/health`, `GET /api/v1/claim-types` | None. |
| D, demo | `/api/v1/cases*`, `/api/v1/replays` | HTTP Basic authentication at the edge with bcrypt-hashed credentials issued by the operator. Unauthenticated requests get 401 before any body is read. Hashes live only in the edge secret, are distributed out of band and are rotated by redeploy. On AWS an ALB rule is optional. |
| A, admin | None | No HTTP admin surface exists and none is added (no listing, no decrypt, no delete-by-id). Administration is infrastructure-only: deploy role, secret store, log read. ECS Exec is disabled. The VM variant has no SSH key and uses SSM or operator-only SSH restricted by source address. |

An optional mode `OPEN_SYNTHETIC` allows anonymous access limited to `SYNTHETIC_DEMO` fixture cases, enforced server-side by rejecting `LIVE_EVIDENCE` cases. It is DESIGNED, OFF by default, and needs a maintainer decision (OD-D2-2). The browser handles Basic authentication and a 401 body is not contract JSON. D1 `api.ts` and `ErrorPanel` must map 401 to an "access credential required" message. The UI never stores the credential (coordination item).

**DD2-4 Case ownership (DESIGNED application change in `core/src/verdictkit/api`, gated by `VK_OWNER_BINDING=1`, mandatory in the public profile).**

- At case creation the server issues a random 256-bit owner secret as cookie `vk_owner` (HttpOnly, Secure, SameSite=Strict, Path=`/api/v1`, Max-Age 86400). It stores only SHA-256 of the secret in a new table `case_owners`, purged with the case.
- Every route under `/api/v1/cases/{id}` (get, patch, freeze, evidence, runs, run, events, outcome, bundle, bundle/metadata) requires a matching cookie, compared in constant time. A mismatch returns the same 404 `NOT_FOUND` body as a nonexistent case, so there is no existence oracle.
- Case ids never appear in logs or error messages. Bundle download and SSE use same-origin requests, so the cookie is sent. The Origin check in D2.3 and SameSite=Strict give CSRF protection.
- Response body shapes are unchanged. A `Set-Cookie` header and an authorization rule are added. Whether `api/openapi.yaml` needs a `securitySchemes` entry, and whether this is a contract-version event, is OD-D2-3 (coordinate with D5, 10.21).
- Residual: a stolen cookie is a stolen session. Cases are not shareable between users by design. Replay of a downloaded Bundle is the sharing mechanism.
- Test: two cookie jars. Jar B gets the random-id 404 on every route of jar A's case, compared on status, body and headers.

**DD2-5 Headers and CSP (resolves OD-4 using F-11).** The edge sets these on every edge response, including static files, redirects and edge-generated errors. The API sets them on every API response, including early-return errors. This needs header assignment moved into a pure ASGI middleware or a `finally` path, because 429, 413 and 400 do not carry them today.

| Header | Value | Applies to |
|---|---|---|
| `Content-Security-Policy` | `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; font-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'` | HTML |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | API responses |
| `X-Content-Type-Options` | `nosniff` | All |
| `Referrer-Policy` | `no-referrer` | All |
| `Cache-Control` | `no-store` for API, `no-cache` for HTML, `public, max-age=31536000, immutable` for content-hashed assets | By type |
| `Strict-Transport-Security` | `max-age=31536000`, no `includeSubDomains` or preload until the owner decides (7.6 needs at least 15552000) | Every HTTPS response |
| `X-Frame-Options` | `DENY` | All |
| `Permissions-Policy` | denies camera, microphone, geolocation, payment, usb | All |
| `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy` | `same-origin` | All |
| `Server` and framework version headers | removed | All |

No source list has a wildcard, `unsafe-inline` or `unsafe-eval`, and there is no nonce infrastructure (7.5). `img-src data:` is dropped because no image or data URI use was found. Re-add it only if a browser E2E violation shows it is needed. Plain HTTP only redirects to HTTPS (308).

The production build under this CSP runs in the browser E2E with a `securitypolicyviolation` listener, and any violation fails the gate. The fix is to change the source (D1), not to loosen the policy. A hash-based allowance needs a recorded decision. The meta CSP in the three `index.html` files must be no weaker than the header (coordination item for D1). `ui/judge` is unchanged and not deployed.

**DD2-6 Limits and resource exhaustion.** Every value except those marked existing is ASSUMED until measured on the target (D2-AC-14).

| Control | Layer | Initial value | State | Req |
|---|---|---|---|---|
| JSON body cap | Edge route matcher and API | 256 KiB | Existing | 7.11 |
| Replay body cap | Edge and API, `/api/v1/replays` only | 8 MiB | Existing | 7.11 |
| Oversize handling | Edge rejects on Content-Length and while streaming. The API buffers in memory only and stores nothing. | Rejected before processing, no partial storage | DESIGNED at edge | 7.11 |
| Bundle parse limits | `bundle.py` | 4096 entries, 16 MiB per entry, 64 MiB uncompressed | Existing | |
| Per-client rate limit | API | 120/min, keyed by the real client address. The edge sets a trusted client-address header. uvicorn trusts forwarded headers only from the edge address (explicit `forwarded-allow-ips`, never `*`). | Value existing, key DESIGNED | 7.11 |
| Route-class limits per client | API | `POST /cases` 10/min, `POST /runs` 6/min, `POST /replays` 3/min, SSE 2 concurrent per client and 20 global | DESIGNED, ASSUMED | |
| Global run slots | API | 2 (1 running, 1 waiting). Beyond that `POST /runs` returns 429 `RATE_LIMITED` with `Retry-After`. The per-case idempotent behaviour is kept. | DESIGNED, ASSUMED | |
| Connection limits | uvicorn | concurrency limit 64 (503 beyond), keep-alive 5 s | DESIGNED, ASSUMED | |
| Edge timeouts | Edge | header read 10 s, body read 30 s, idle 120 s, header size 16 KiB | DESIGNED, ASSUMED | |
| ALB idle timeout | ALB | at least 120 s, because SSE can be silent up to 120 s and the default is 60 s | DESIGNED | |
| Examination deadline | Worker | Client timeout 60 s exists. A per-task deadline of about 55 s (interval timer aborts the task, returns an error frame, worker survives) is DESIGNED. | DESIGNED | |
| Worker CPU supervision | Worker | The lifetime `RLIMIT_CPU` (F-4) is replaced or backed by restart after N tasks. PENDING measurement of per-run CPU (OD-D2-4). | PENDING | |
| Active cases | API | 20 per owner, 500 global, then `POST /cases` returns 429 | DESIGNED, ASSUMED | |
| Storage quotas | API | drafts DB and bundles 2 GiB, evidence 1 GiB. Readiness fails when free space on the data volume is below 15%. Replays and case creation return 429 over quota. | DESIGNED, ASSUMED | |
| Memory | Container | Container limit, with examiner `RLIMIT_AS` below it so the API keeps headroom. Sizing PENDING measurement. | PENDING | |

The per-task deadline is server-side execution control. It is distinct from browser abort (D1.16 b).

**DD2-7 No automatic retries.** The edge and the load balancer never retry POST, PATCH, PUT or DELETE. Health checks use GET only. Client retry is an explicit user action (D1.16 c). Orphan cases from user retries are bounded by the per-owner case quota and the 24 h TTL.

**DD2-8 Secrets.**

- `VK_VAULT_KEY` is 32 random bytes in base64, generated out of band by the operator with a CSPRNG. The build and the entrypoint never generate it for production.
- The key and the edge credential hashes live only in the provider secret store (AWS Secrets Manager, or on the VM a root-owned 0600 env file outside the repo and images). The key goes only to the API container environment and the hashes only to the edge container.
- They never appear in the image, repo, build args, logs, the Examiner environment (the `env -i` allowlist and the worker's own refusal stay), CI logs or plaintext task definitions. The task execution role reads only those secrets. Humans have no routine read access.
- Rotation: a new key makes all current cases undecryptable. This is acceptable with a 24 h TTL and ephemeral storage. Rotation is by redeploy and is documented.
- Startup refuses empty, malformed or wrong-length keys without printing them (7.10).
- Verification: a canary search of image layers, repo, container output and the examiner process environment finds 0 matches for a test key (7.9).
- Accepted residual R-1: the root entrypoint process holds the key in its environment. Mitigations: ECS Exec and `docker exec` restricted to the operator, no SYS_PTRACE, `--no-new-privs` children with an allowlisted environment.

**DD2-9 Privacy-safe logging.**

- Logs are structured JSON with an allowlisted field set: timestamp, level, event code, request id, method, route template (not the raw path), status, duration and size class.
- The uvicorn access log is disabled and replaced by a route-template access log. Edge logs drop the Cookie, Authorization and Set-Cookie headers and the query string, and replace the case id (regex `case_[0-9a-f]{32}`) with `case_[redacted]`.
- Client addresses are not logged in clear. An HMAC with a rotating salt is kept only if abuse forensics need it (OD-D2-5).
- Never logged: request or response bodies, claimed figures, pasted text, Bundle bytes, owner or access credentials, exception messages and stack traces. Logs carry the exception class and error code only.
- The examiner's `examiner error: {exc}` print is replaced by an error code (DESIGNED change). Log retention is 14 days.
- Verification: a canary lifecycle with sentinel values (claimed figure, pasted text, case id, owner cookie, Basic credential, vault key), then a scan of all container output and edge logs finds 0 sentinels.

**DD2-10 Retention and cleanup.**

| Data | Location | Retention | Mechanism | State |
|---|---|---|---|---|
| Cases, drafts, freezes, runs | SQLite | 24 h | Judge mode applies it to frozen cases (existing). Purge becomes a background loop every 60 s independent of traffic. | Expiry existing, loop DESIGNED |
| Bundle files | Data volume | With the case | Deleted with the case | Existing |
| Evidence blobs and metadata | Evidence directory | TTL plus 1 h | Sweeper. `put` refreshes modification time on deduplicated writes so a blob needed by a live case is never swept. | DESIGNED core change |
| Replay temp dirs | Temp | Request | `TemporaryDirectory` | Existing |
| `/tmp/vk-*` homes | Temp | Empty | | Existing |
| Owner cookie | Browser | Max-Age 24 h | | DESIGNED |
| Ephemeral task storage | Provider | Task stop | | Provider |
| Logs | Log store | 14 days | | DESIGNED |

There is no on-demand deletion endpoint (OD-D2-6). Cleanup never deletes the vault, draft or socket directories or changes their owner or mode. The entrypoint re-asserts ownership and modes at every start (existing `setup_vault`). Sweeper correctness is a property-test target for D8.

### D2.6 Liveness, readiness, attestation, commit identity, disclosure

- **Startup attestation.** As DD2-2. `VK_STARTUP_OK isolation=ENFORCED` is printed exactly once, before the first request, by `serve` in the public profile. Failure prints `VK_STARTUP_ERROR=...` and a plain stderr sentence that isolation is unavailable, then exits non-zero (7.7, 7.8).
- **Liveness.** Internal only, no public route. A container health command (`python -m verdictkit.api --probe-live`, DESIGNED) checks that the API answers on loopback and that both child PIDs exist. Docker HEALTHCHECK or the ECS container health check uses it. Failure restarts the container.
- **Readiness and public health.** `GET /api/v1/health` stays the single public endpoint. It returns 200 only when ready, otherwise 503 with the same minimal body and `status: "unavailable"`. Ready means, cached at most 5 s: the examiner socket re-attests (the live peer-credential check of `verify_examiner_socket`, so a replaced worker is detected), the custody store opens, free space is above the threshold, and run-slot accounting is not wedged. A failed re-attestation never flips `isolationMode` to a weaker value. It yields 503 and refuses new runs. Reasons are logged as codes and never returned.
- **Commit identity.** Build argument `VK_COMMIT_SHA` (40 hex, validated, build fails otherwise) is baked as `ENV VK_COMMIT_SHA` and OCI label `org.opencontainers.image.revision`. `VK_IMAGE_DIGEST` is injected at deploy from the digest the deployment references (task definition `image@sha256:`), so Bundles stop recording "unknown" (F-13). Health adds `commitSha` (7.13), read from the environment and never from running git. The image is built only from a clean checkout of that commit. The release record lists commit, image digest and Execution_Record.

| Field or fact | Public health | Reason |
|---|---|---|
| `contractVersion`, `status`, `isolationMode`, `judgeMode`, `engineVersion`, `commitSha` | Allowed. The key set is exact and enforced by a test. | Needed by 7.7, 7.13 and clients. |
| Image digest, hostnames, IPs, uids and gids, file paths | Never | Reconnaissance value. |
| Vault or draft state, case counts, queue depth, disk usage | Never | Operational detail. |
| Key presence or id, dependency versions | Never | Reconnaissance value. |
| Error reasons, stack traces, which check failed | Never | A failure does not reveal which check failed. |
| `claim-types` | Public, names and outcome field names only (existing) | Needed by the UI. |

### D2.7 Image and reproducibility

**DD2-11: tested equals deployed.** The deployed API image is the exact digest on which `gate-isolation`, `gate-startup`, `gate-http` and `gate-case` passed in CI, because `gate-isolation` needs pytest and `tests/`. A slimmer runtime target (no dev group, no tests, no uv) is allowed only if it passes the same four gates or a pytest-free isolation probe is added first (OD-D2-7).

| Input | Pinned today | Design |
|---|---|---|
| Base image | digest (existing) | Unchanged. |
| `uv` image | digest (existing) | Unchanged. |
| Python dependencies | `uv.lock` with `--frozen` (existing, 7.12) | Unchanged. |
| apt packages | No | Remove the apt layer if `util-linux`, `procps` and `ca-certificates` are not needed at runtime or are already in the base (verify). Otherwise install from a dated `snapshot.debian.org` mirror or pin versions. |
| Node build stage for the edge image | Not present | Digest-pinned Node image, `npm ci` from `package-lock.json`, build output copied into the edge image, build fails on lockfile drift. |
| Edge image base | Not present | Digest-pinned Caddy. |
| Build args | None | `VK_COMMIT_SHA` only. |
| Timestamps | Unset | `SOURCE_DATE_EPOCH` set to the commit time. |

This gives dependency-reproducible images: the same inputs give the same package set. It does NOT give bit-for-bit identical image digests. The digest is recorded and not recomputed, and no claim of byte reproducibility is made.

Further decisions:

- The API image runs with a read-only root filesystem and named writable volumes, and defines a HEALTHCHECK.
- An image scan fails the gate on HIGH or CRITICAL findings that have a fix. An SBOM is generated and stored with the release record.
- The image is pushed to a private registry by digest, with immutable tags `sha-<commit>`.
- `.dockerignore` is extended to exclude `.kiro`, `docs`, `.github`, `.hypothesis` and `.ruff_cache` from the API image context (DESIGNED).
- Image signing (cosign) is not in scope and is not claimed.
- PID 1: use `initProcessEnabled` (Fargate) or `docker run --init` or compose `init: true`. Add a SIGTERM trap to `serve` that stops both children (DESIGNED). In-flight runs are abandoned on shutdown because runs are not resumable. This is documented.

### D2.8 Smoke tests, security gates, monitoring, rollback

**Pre-deploy security gates.**

| ID | Gate | Pass |
|---|---|---|
| SG-1 | Build from `uv.lock` with `--frozen` | Build succeeds, and fails on a stale lockfile |
| SG-2 | The four container gates on the exact image | All exit 0 |
| SG-3 | Image scan | 0 unwaived fixable HIGH or CRITICAL |
| SG-4 | SBOM present | File stored with the release record |
| SG-5 | Secret canary: build with a canary in the build job environment | 0 matches in layers, history and labels |
| SG-6 | Header test on a local compose stack for 200, 401, 404, 405, 413, 429, 500 on edge and API | 0 missing headers |
| SG-7 | CSP browser E2E with violation listener | 0 violations |
| SG-8 | Caddyfile and compose lint, route check script, `docker compose config` | No vault, draft, evidence or socket volume and no `VK_VAULT_KEY` on the edge service |
| SG-9 | Log canary lifecycle | 0 sentinels |

**Post-deploy smoke tests** run from outside against the public URL, over HTTPS only.

| ID | Check |
|---|---|
| SM-1 | `GET /api/v1/health` answers within 10 s with 200, the exact key set, `isolationMode` ENFORCED, `judgeMode` true and `commitSha` equal to the release commit (7.13). |
| SM-2 | Plain HTTP redirects to HTTPS and serves no content. |
| SM-3 | TLS 1.2 or later only, valid certificate not expiring within 14 days, HSTS `max-age` at least 15552000 (7.6). |
| SM-4 | Security headers present on 200, 401, 404, 405, 413 and 429 responses. |
| SM-5 | Landing, `/quote/` and `/reel/` return 200 on the same origin with no external hosts in HTML, CSS or JS references. |
| SM-6 | A Tier D route without credential returns 401 with no API body. |
| SM-7 | With credential, the synthetic Reel lifecycle (create, freeze, evidence, run, outcome, bundle, metadata, replay) completes with a verdict and `isolationMode` ENFORCED in the outcome. |
| SM-8 | A second cookie jar gets a 404 identical to the random-id 404 on every case route. |
| SM-9 | A 257 KiB JSON body and a 9 MiB replay body return 413, and stored size is unchanged. |
| SM-10 | A burst of 130 requests per minute from one client yields 429 with headers and recovers within 60 s. |
| SM-11 | A connection to the API port on the public address fails. The examiner socket is not reachable. |
| SM-12 | No response contains a stack trace, filesystem path or `Server` version header. |
| SM-13 | After the run, the log canary scan finds 0 sentinels. |
| SM-14 | Results are recorded as an Execution_Record, SUCCEEDED only if all pass (3.9, 7.13). |

**Monitoring (no case data).** Alarms: target unhealthy or `/health` 503, 5xx rate, 429 rate, container restarts above 1 per hour (also the symptom of the worker CPU limit, F-4), examiner re-attestation failures, disk free below 25%, memory above 80%, certificate expiry within 14 days, and a monthly spend threshold. An alert on isolation re-attestation failure has the highest priority. Log and metric destinations are PENDING (D2.11 B-6).

**Rollback (7.15).**

1. Deployments always reference an image by digest. The release record keeps the previous digest and commit.
2. Rollback redeploys the previous digest. On ECS this registers a task definition revision with the previous digest and updates the service. On the VM it runs `docker compose` with the previous digest. The previous task definition revision is kept.
3. Confirm that `GET /api/v1/health` returns the previous `commitSha` and that SM-1 to SM-5 pass.
4. Rollback loses live cases (ephemeral). No schema migration exists because SQLite is created fresh. A future schema change must be backward-compatible or ship with a documented reset.
5. A rollback rehearsal is recorded before the release is called available. Deploy and rollback are owner actions (14.13).

### D2.9 Measurable acceptance criteria

All rows are UNVERIFIED. Environments: CI/VM is a Linux host with Docker, Probe is a Fargate probe task, Owner is owner-run.

| ID | Criterion | Method | Pass threshold | Req | Environment |
|---|---|---|---|---|---|
| D2-AC-1 | Public profile refuses to start for each of: `VK_JUDGE_MODE` unset or 0, empty key, malformed key, wrong-length key, missing owner binding, non-https origin, examiner socket absent | 7 negative start tests | Exit non-zero, no `VK_STARTUP_OK`, stderr message, no key value in output | 7.8, 7.10 | CI/VM |
| D2-AC-2 | Positive start prints the startup line | Capture output | `VK_STARTUP_OK isolation=ENFORCED` count is 1, before the first request | 7.7 | CI/VM |
| D2-AC-3 | Four existing gates on the deployed digest | Run gates | All exit 0 | 7.12, 2.5 | CI/VM |
| D2-AC-4 | Fargate probe | Run four gates on Fargate | Exit 0, or Fargate recorded REJECTED | 7.17, 7.18 | Probe, Owner |
| D2-AC-5 | Headers on every response class in SM-4 | Header test | 0 missing | 7.5 | CI/VM |
| D2-AC-6 | CSP quality and runtime | Parse header, browser E2E on 3 pages | No `*`, `unsafe-inline` or `unsafe-eval`. 0 `securitypolicyviolation` events. | 7.5 | CI/VM |
| D2-AC-7 | Size caps | 256 KiB + 1 byte JSON, 8 MiB + 1 byte replay | 413 and stored-bytes delta 0 | 7.11 | CI/VM |
| D2-AC-8 | Rate limit and client address | 121st request in 60 s, two clients behind the edge | 429 on the 121st. Clients limited independently. | 7.11 | CI/VM |
| D2-AC-9 | Expiry | No-traffic wait of 24 h + 60 s. Evidence older than TTL + 1 h. Blob referenced by a live case. | Case unreachable. Old evidence gone. Referenced blob remains. | 7.11 | CI/VM, Owner |
| D2-AC-10 | Cross-owner | Foreign cookie on all case routes | 0 of N routes return anything but the random-id 404 | 2.3 | CI/VM |
| D2-AC-11 | Secret canary | Search repo, image layers, logs, examiner `/proc/<pid>/environ` | 0 matches | 7.9 | CI/VM |
| D2-AC-12 | Log canary | Sentinel lifecycle | 0 sentinels | 2.3 | CI/VM |
| D2-AC-13 | Health disclosure and readiness | Compare key set. Replace the socket with a non-examiner uid. | Key set equals the allowed set. 503 after replacement. | 7.7, 2.5 | CI/VM |
| D2-AC-14 | Baseline measurement | p50 and p95 run latency and CPU per run on the target size | Recorded. DD2-6 values revised from it. | 7.11 | Probe, Owner |
| D2-AC-15 | Stale lockfile | Build with a stale `uv.lock` | Build fails | 7.12 | CI/VM |
| D2-AC-16 | Image scan | Scanner | 0 unwaived fixable HIGH or CRITICAL | 7.12 | CI/VM |
| D2-AC-17 | Rollback rehearsal | Redeploy previous digest | Previous `commitSha` on health within 10 minutes (limit ASSUMED) | 7.15 | Owner |
| D2-AC-18 | Same-origin | Route check script | 0 absolute external URLs, 0 asset paths outside each base | 7.5, 7.16 | CI/VM |
| D2-AC-19 | No automatic retry | Slow or reset the upstream during a client POST | Edge and API each receive exactly 1 request, 0 duplicates | 2.4 | CI/VM |
| D2-AC-20 | Browser abort | Client aborts a run request | Server run reaches a terminal state. UI text has no "cancelled". | 2.4 | CI/VM |
| D2-AC-21 | Historical and current isolation labels | UI test with a Bundle recorded UNENFORCED and a server ENFORCED | Both labels shown and distinct | 2.4, 2.5 | CI/VM |

### D2.10 Requirement traceability

| D2 section | Requirements |
|---|---|
| D2.1 | 7.16, 7.17, 7.18 |
| D2.2 | 7.5 to 7.15, 2.5 to 2.7 |
| D2.3 | 7.5, 7.6, 7.16, 6.1, 1.17 |
| D2.4 | 7.16, 7.17, 7.18, 2.5, 2.6, 2.7 |
| D2.5 | 7.5, 7.6, 7.9, 7.10, 7.11, 2.3, 2.4, 2.8 |
| D2.6 | 7.7, 7.8, 7.13, 2.5 |
| D2.7 | 7.12, 7.16, 14.17 |
| D2.8 | 7.13, 7.14, 7.15, 3.9 |
| D2.9 | 7.5 to 7.18 |

Every D2 component maps to a requirement: edge container (7.5, 7.6, 7.16), API container and entrypoint profile (7.7, 7.8, 7.10, 2.5), secret store (7.9), size and rate limits (7.11), image and lockfile (7.12), health and commit identity (7.13), documentation of absent demo (7.14), rollback (7.15), hosting evaluation (7.17, 7.18), owner cookie and logging (2.3), retention (7.11, 2.3) (4.2).

**Requirement gaps found (`requirements.md` not edited).** They are proposed for D10 reconciliation and need maintainer approval before any requirements change.

| ID | Gap |
|---|---|
| G-1 | No criterion for case ownership and cross-user protection (traced to 2.3). |
| G-2 | No criterion for an access policy or administrative boundary for the public demo. |
| G-3 | No criterion for evidence and temporary-file retention beyond the 24 h case expiry in 7.11. |
| G-4 | No criterion for readiness against liveness, or for health disclosure limits. |
| G-5 | 7.7 requires the startup line from the deployed service, but `serve` does not print it today. |
| G-6 | 7.5 says "every response including error responses", but today 429 and 413 skip headers. |

### D2.11 Open decisions and blockers

| ID | Item | State | What resolves it |
|---|---|---|---|
| B-1 | Fargate capability, volume and `PEERCRED` behaviour | UNVERIFIED | Owner-authorized probe task (DD2-1, D2-AC-4). |
| B-2 | tmpfs documentation conflict on Fargate | CONFLICTING | Design avoids dependence. No action. |
| B-3 | Worker lifetime `RLIMIT_CPU` and per-run CPU unmeasured | PENDING | OD-D2-4 and D2-AC-14. |
| B-4 | Contract implications: owner cookie, health `commitSha` and 503 body, edge 401, 429 reuse | PENDING | OD-D2-3, coordinate with D5. |
| B-5 | Minimal capability set for the entrypoint | UNVERIFIED | Gate runs with `--cap-drop ALL` plus additions. |
| B-6 | Domain name, region, certificate owner, budget cap, credential distribution, log and metric destinations | PENDING | Owner decisions. |
| B-7 | Single task, no HA, cases lost on redeploy | Accepted | Document for users. |
| B-8 | Whether `OPEN_SYNTHETIC` is wanted | PENDING | OD-D2-2. |
| B-9 | R-1: root PID holds the key. R-2: examiner shares the network namespace with the custodian, so egress is not separable per user. | Accepted residual risks | Record in the Threat_Model (D8). |
| B-10 | Slimmer runtime image needs a pytest-free isolation probe | PENDING | OD-D2-7. |
| B-11 | D1 coordination: base paths, meta CSP, 401 message, historical and current isolation labels | PENDING | D1 implementation items. |
| B-12 | Hosted demonstration status | "No hosted demonstration is available" (7.14) | An Execution_Record under 7.13. |

| ID | Decision needed | Options | Recommendation |
|---|---|---|---|
| OD-D2-1 | Primary hosting target | Fargate, VM with compose | Build the VM path first as the portable reference. Run the Fargate probe only if the owner wants AWS. |
| OD-D2-2 | Enable `OPEN_SYNTHETIC` | On, off | Off. Keep Tier D credentials. |
| OD-D2-3 | Is the owner cookie a contract-version event | Contract 1.2.0, 1.1.0 with documented header | Decide with D5. Recommend documenting the header and bumping the minor version. |
| OD-D2-4 | Worker CPU supervision | Restart after N tasks, raise limit, per-task limit | Per-task deadline plus restart after N tasks, N set from measurement. |
| OD-D2-5 | Client address in logs | Omit, rotating-salt HMAC | Omit. |
| OD-D2-6 | On-demand case deletion endpoint | Add, do not add | Do not add. Rely on the 24 h TTL. |
| OD-D2-7 | Slimmer runtime image | Keep one image, add runtime target | Keep one image until a pytest-free probe exists. |

### D2.12 Maintainer decisions on open items (conditional approval)

The maintainer approved D2 conditionally. Each decision below is DECIDED and DESIGNED. None is implemented, no infrastructure is provisioned and no charge is incurred. Text in D2.1 to D2.11 is unchanged. Where a decision here differs from that text, this section governs.

| ID | Decision | Effect on D2 text |
|---|---|---|
| AM-1 | Hosting. The preferred initial architecture is one Linux VM running portable Docker and Caddy (Plan B, D2.4(c)). AWS Fargate stays an unverified alternative under DD2-1. No cloud probe, account action or provisioning is authorized. | OD-D2-1 is decided: build the VM path first. B-1 and D2-AC-4 stay UNVERIFIED and the Fargate probe is not scheduled. D2-AC-14 is measured on the VM path (CI/VM or Owner), because no Fargate probe is scheduled. |
| AM-2 | Region and budget. A United States region is preferred. The initial budget target is $30 per month of recurring hosting cost. No spending is authorized: no purchase, subscription, domain, certificate or paid service is created. | B-6 is partly decided (region preference, budget target). Domain name, certificate owner, credential distribution, and log and metric destinations stay PENDING. The monthly cap for the budget alarm stays the owner's choice, with the $30 target as its initial value. The VM variant in D2.4(d) (about $15 to $30, ASSUMED) fits the target, with no margin at its upper end. The Fargate variant (about $73, ASSUMED) exceeds it. The budget alarm in D2.4(d) still applies. |
| AM-3 | BE-1 and BE-2 remain mandatory remediation items before the final release (1.18, 13.11 to 13.13). D2 neither waives nor defers them. | D2 rows that need a clean Windows contract run stay UNVERIFIED until the closing evidence in 13.13 exists. The BE-1 design is in D3.9. The BE-2 design is in D8, and the P2 and P7 interface for it is in D3.9. |
| AM-4 | Examiner CPU. The process-lifetime CPU limit no longer acts as the exhaustion mechanism. Each examination runs under its own bounded CPU and wall-clock budget that resets for the next examination. No protection is weakened: the memory limit (`RLIMIT_AS`), the per-task deadline of DD2-6, the container CPU, memory and process limits, and fail-closed `RUN_FAILED` on overrun all stay. A recycle policy (restart the worker after N examinations or M cumulative CPU seconds, with N and M taken from the D2-AC-14 measurement) replaces the 300 s lifetime cap as the backstop against a wedged or leaking worker. The mechanism (for example one short-lived child per examination with its own limits, or an equivalent) is chosen at implementation, and the properties above are the contract. | The lifetime CPU limit described in F-4 and the "Worker CPU supervision" row of DD2-6 are replaced. OD-D2-4 is decided. B-3 stays PENDING only for the values of N and M. New row D2-AC-22. |
| AM-5 | Examiner egress and capabilities. Verify, do not assume. (a) A negative test shows that the examiner uid cannot open an outbound connection when the container has network access. If no control can guarantee that, R-2 stays an accepted residual risk that the Threat_Model (D8) records with a reason. (b) The minimum Linux capability set of the entrypoint is measured by running the four gates under `--cap-drop ALL` plus additions, and is recorded. No capability beyond the recorded set is added without a recorded decision: never `SYS_PTRACE` or `SYS_ADMIN`, and `NET_ADMIN` only inside an entrypoint root phase that drops it before the children start, which is possible on the VM path only (Fargate allows adding only `SYS_PTRACE`, D2.4(b)). The examiner process holds no effective capability. | B-5 now has verification row D2-AC-24. The R-2 part of B-9 now has verification row D2-AC-23. |
| AM-6 | Case ownership. Ownership is enforced on the server for every operation that reads, changes, streams or exports a case, its runs, evidence, outcome, events or bundle. That includes the SSE stream, run polling, bundle download and bundle metadata. No on-demand deletion endpoint exists (OD-D2-6), and the expiry sweeper has no request owner (AM-9). A foreign owner and a nonexistent case get the same 404 `NOT_FOUND` response (same status, body and headers). No client-supplied owner identifier is trusted. A test enumerates the application routes and fails when a route that carries a case identifier has no ownership check. | DD2-4 now covers all case-related operations and not only the listed routes. G-1 has a decision but its requirement text is still missing. New row D2-AC-25 extends D2-AC-10. |
| AM-7 | Restricted demonstrations. Prefer individually revocable invitation credentials. Each invitee gets one credential with at least 128 bits of entropy, issued out of band and stored only as a hash, with a label, an expiry inside the demonstration window and a revocation flag. Revoking one credential takes effect without a redeploy and does not affect the others. The mechanism (per-user edge entries with a graceful reload, or an API-side invitation table) is chosen at implementation. Failed attempts are rate limited and credentials never reach logs (DD2-9). | DD2-3 tier D is replaced. DD2-8 keeps credential hashes in the edge secret only for the edge-entry mechanism. An API-side table keeps them in the custodian-only data directory (mode 0700), never in a directory the examiner can read. A shared credential set rotated by redeploy is no longer the design. `OPEN_SYNTHETIC` stays OFF (OD-D2-2 unchanged). G-2 has a decision. New row D2-AC-26. |
| AM-8 | CSRF. Foreign-Origin rejection alone is not enough, because a request without an `Origin` header would pass. For POST, PATCH, PUT and DELETE, the edge and the API both require: (a) `Origin` equals `VK_PUBLIC_ORIGIN` when present, and `Origin` is mandatory when the owner cookie is sent; (b) `Sec-Fetch-Site`, when present, is `same-origin`; (c) the content type declared for the route, with any other content type rejected (415); (d) the owner cookie is `SameSite=Strict`. No CORS header is ever sent, so a cross-origin page cannot add custom headers. GET and HEAD never change state. | The Origin rule in D2.3 and the CSRF sentence in DD2-4 are extended. Browsers send `Origin` on unsafe requests, so no new request header is required from them and the contract text is unchanged. Scripted and test clients that keep the owner cookie must send `Origin` (the SM-7 smoke script, and any `TestClient` use against the public profile). New row D2-AC-27. |
| AM-9 | Evidence cleanup. The sweeper never deletes a blob that a live case references or that an examination in flight uses. Candidates are blobs with no live reference and an age over TTL plus 1 hour. References are derived from live cases at each sweep, under a lock that excludes put, freeze and run start. Any read error or unparseable record means delete nothing. A failed sweep is non-fatal. | The evidence row of DD2-10 is extended. The sweeper property for D8 becomes a stateful test over random interleavings of put, deduplicated put, freeze, run start, purge and sweep. D2-AC-9 stays. G-3 has a decision. New row D2-AC-28. |
| AM-10 | API contract and D5. D2 edits no contract file and bumps no version. Every contract-visible D2 change is a proposal for D5, which owns the single contract-version decision together with the P4 authenticity fields. Until D5 is approved, the D2 rows that depend on a contract-visible change (D2-AC-13 and SM-1) stay UNVERIFIED. | OD-D2-3 is deferred to D5 and B-4 becomes a coordination item. Implications are listed in the table after this one. |
| AM-11 | No public deployment yet. No public listener, DNS record, certificate issuance or announcement is allowed until all of these hold: SG-1 to SG-9 and every D2 acceptance row that applies to the VM path have SUCCEEDED Execution_Records; the P8 integration gates pass on the Release_Candidate; and the owner records a go decision (14.13). Until then the documentation keeps saying that no hosted demonstration is available (7.14). | The D2.8 gates are entry conditions and not recommendations. |
| AM-12 | Requirement gaps G-1 to G-6 (D2.10) are recorded for reconciliation in D10. `requirements.md` is not edited, and any requirement change needs maintainer approval. | See the requirement gap coverage table below the contract table. |

**Contract coordination with D5 (AM-10).**

| # | D2 change | Compatibility | What was read in the files | Coordination |
|---|---|---|---|---|
| 1 | Owner cookie `vk_owner` and the ownership rule (AM-6) | Additive on the wire. Breaking in behavior, in the public profile only (`VK_OWNER_BINDING=1`), for any client that does not keep cookies and for any non-browser client that keeps the cookie but does not send `Origin` (AM-8). Unchanged when the binding is off. | `api/openapi.yaml` declares no cookie and no `securitySchemes`. Its info text says "Judge mode requires no authentication". | D5 decides how the cookie and header are documented and whether this item joins the version event (OD-D2-3 recommends a minor bump). The info text needs a later edit. |
| 2 | `commitSha` on `GET /health` | Breaking at schema level | The `Health` schema sets `additionalProperties` false and lists five required fields. The health example, the TypeScript `Health` type and the contract test validators must change together. Tolerant JSON clients are unaffected. | Batch into the D5 version event. |
| 3 | Health 503 with `status` "unavailable" | Breaking at schema level | `Health.status` is const "ok" and `/health` declares only a 200 response. | Batch into the D5 version event. |
| 4 | Edge 401 for tier D, edge 403 for CSRF checks and 415 for content type | Outside the contract (not JSON) | `ui-kit/src/api.ts` turns a non-JSON body into `NON_JSON_RESPONSE`. | D1 maps the messages (B-11). No contract edit. |
| 5 | 429 `RATE_LIMITED` with `Retry-After` for runs and cases | Schema-compatible. Behavior change for clients that assume `POST /runs` is accepted. | `ErrorEnvelope.error.code` is an open string, and no code named `RATE_LIMITED` appears in `api/openapi.yaml`. Only `POST /cases` declares a 429 response (line 59). `POST /runs` and the other routes declare none. | D5 adds the 429 responses and the `RATE_LIMITED` code to the paths that need them. |
| 6 | Contract header on every response (G-6) | Compatible | Today the header is missing on 400, 413 and 429 responses (F-5). | None. |
| 7 | Contract version value | Any bump is a lockstep change | 1.1.0 is pinned in `api/openapi.yaml` (`info.version` and the `ContractVersion` constant), in `ui-kit/src/api.ts` (`CONTRACT_VERSION`; any other value raises `ContractMismatchError`), in `core/src/verdictkit/mcp_server.py` (replay result), in `core/src/verdictkit/api/server.py` (`VERSION`) and in tests such as `tests/api/test_m3b_http_drafts.py`. | D5 owns one minor-version event for items 2, 3 and the P4 fields, and decides whether items 1 and 5 join it. Items 4 and 6 stay outside it. |

**Requirement gap coverage (G-1 to G-6).**

| Gap | Decision after review | Requirement text |
|---|---|---|
| G-1 | AM-6 | still missing |
| G-2 | AM-7 | still missing |
| G-3 | AM-9 | still missing |
| G-4 | none, D2.6 stands | still missing |
| G-5 | none, DD2-2 stands | still missing |
| G-6 | AM-10 item 6 and DD2-5 | still missing |

**Acceptance rows added by this amendment (all UNVERIFIED).**

| ID | Criterion | Method | Pass threshold | Req | Environment |
|---|---|---|---|---|---|
| D2-AC-22 | Per-examination budget | Run many short examinations whose cumulative CPU exceeds 300 s, then one examination that exceeds the per-examination limit | The worker survives the first set. The overrun ends in `RUN_FAILED` and the next examination succeeds. `RLIMIT_AS` still applies. | 2.5, 7.11 | CI/VM |
| D2-AC-23 | Examiner egress | From the examiner uid in a container that has network access, connect to a local canary listener | The connection fails, or R-2 is recorded as accepted with a reason | 2.3, 2.5 | CI/VM |
| D2-AC-24 | Capability set | Run the four gates under `--cap-drop ALL` plus the recorded additions, and read the effective capabilities of the examiner and custodian processes | Gates exit 0. The examiner `CapEff` is 0. The recorded set equals the deployed set. | 2.5, 7.12 | CI/VM |
| D2-AC-25 | Ownership completeness | Enumerate the application routes. Call each route that carries a case identifier with a foreign cookie and with no cookie | 0 routes answer anything other than the nonexistent-case 404 (status, body, headers). 0 routes lack a check. | 2.3 | CI/VM |
| D2-AC-26 | Invitation credentials | Issue 3 credentials, use each, revoke 1 | The revoked credential gets 401 within 60 s (ASSUMED). The other 2 still work. 0 credentials appear in logs. | 2.3 | CI/VM |
| D2-AC-27 | CSRF | For each unsafe route, send: cookie plus foreign `Origin`; cookie and no `Origin`; cookie plus `Sec-Fetch-Site` cross-site; cookie plus a `text/plain` body; and one valid same-origin request | The first four get 403 or 415 and change nothing. The valid request succeeds. | 2.3, 2.4 | CI/VM |
| D2-AC-28 | Sweeper safety | Stateful property test with random interleavings, including a crash between put and freeze | 0 deleted blobs that a live case references or an in-flight examination uses, in every example of a stateful run under the `ci` Hypothesis profile (200 examples; a per-test setting may raise the count) | 7.11, 2.3 | CI/VM |

## D3. P2 Agent hooks and Windows compatibility

### D3.1 Scope and status

**Covers.** Requirement 8 (8.1 to 8.18). The P2 side of 1.18 and 13.11 to 13.13: the BE-1 design and the BE-2 interface to P7 (D3.9). The evidence rules 3.6 to 3.8 and 4.7 as they apply to hooks. Criterion 16.2 for hook-related usage.

**Does not cover.** The BE-2 root cause (D8). MCP (D4). Running Kiro on Linux. Any edit to `.kiro/hooks`, tests or code in this stage.

**Definitions used in D3.**

- A registered hook is not an executed hook.
- A manually executed hook command is not proof of automatic hook execution.
- Hooks are a development guardrail. Runtime guarantees come from code and CI (8.7).
- This stage is design only: no hook was triggered, no workspace was trusted, no hook file was modified, and no test was run for D3.

**Status.** Everything in D3 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. Hook execution inside Kiro stays UNVERIFIED (reconciliation H8, ledger E-103).

| Track | Owner | Content |
|---|---|---|
| D8 | D8 | The BE-1 design and the BE-2 interface to P7 are in D3.9. The BE-2 root cause and its instrumentation belong to D8. |
| D2 | D2 | HK-5 and HK-6 run the API contract tests and the `tests/api` suite on a save. They guard the API behavior that the D2 gates check and the decisions amended in D2.12. They do not replace the container gates (D2.8). |
| D9 | D9 | 14.19 lists automatic hook execution as UNVERIFIED unless it has a SUCCEEDED Execution_Record for the Release_Candidate. |
| D10 | D10 | Requirement gaps G-7 to G-13 (D3.11) are proposed for reconciliation. `requirements.md` is not edited. |

### D3.2 Inspected baseline and findings

**Repository files read.** `.kiro/hooks/core-contract-tests.json`, `app-contract-tests.json` and `llm-fence.json`; `.kiro/settings/mcp.json`; the six files in `.kiro/steering`; `pyproject.toml`; `.gitignore`; `tests/conftest.py`; `tests/contract/test_mcp_server.py`, `test_llm_fence.py` and `test_api_schema.py`; the file listings of `tests/api`, `tests/contract`, `tests/integration`, `tests/ui` and `scripts`; `scripts/serve_judge_ui.py`; `core/src/verdictkit/mcp_server.py`; `tests/ui/test_judge_preview.py`; `.github/workflows/p0-integration.yml` and `m3b-api-checks.yml`; parts of `api/openapi.yaml`; the hook lines of `docs/ARCHITECTURE.md`; and `docs/next-phase/BASELINE_REPORT.md`, `EXECUTION_EVIDENCE.md`, `HISTORICAL_EVIDENCE_RECONCILIATION.md`, `baseline/EXECUTION_INDEX.md` and `baseline/records.jsonl`.

**Historical_Audit (read only, derived values only, nothing copied).** In the log export: `verification/hook_configuration_and_demo.md`, `hook_command_terminal_preflight.txt`, `hook_files_sha256.txt` and `hook-execution/README.txt`. In the audit folder: `collect_hook_logs.ps1`. Event-name counts from the Kiro logs.

**Host.** A listing of the user-level Kiro folder by names only, the IDE `product.json` version, two small user-level settings files, and the user settings keys that mention trust or hooks.

**Sources outside the repository.** The Kiro hook, privacy and security pages (links in the next table), AWS security bulletin 2026-117-AWS, the Python 3.12 `os.mkdir` documentation, the `uv run` help text, the uv documentation page on automatic locking and syncing, and the installed Hypothesis source.

**Commands run.** Directory and file listings, `git status` and `git rev-parse`, file hashing, text search, `uv --version`, `uv run --help` (help text only), and scratch evaluation of candidate regular expressions in a throwaway interpreter. No repository code, no repository test and no hook was run. None of this is an Execution_Record. A second read-only pass in this design step re-derived the file counts and the matcher counts of D3.4 with `git ls-files` and the regular expression engine of Windows PowerShell 5.1. It gave the same numbers.

**Kiro documentation read.** The last column lists what the pages leave open. Those points become the probes in D3.8.

| ID | What the documentation says | Source | Open point |
|---|---|---|---|
| K-1 | Hook JSON has `version`, `hooks[].name`, `trigger`, `matcher`, `action.type`, `action.command`, an optional `description`, `timeout` (seconds, default 60, 0 disables the timeout) and `enabled` (default true). | [Hooks](https://kiro.dev/docs/hooks/) | None. |
| K-2 | For file events the matcher is a regular expression against the file path, and no matcher means always match. A best-practices page shows a glob example. | [Hooks](https://kiro.dev/docs/hooks/) and [Hook best practices](https://kiro.dev/docs/hooks/best-practices/) | Grammar, anchoring, relative or absolute path and separator style are not documented: UNVERIFIED. |
| K-3 | Command actions run in the project root and receive session context as JSON on STDIN, including the saved file path. A `{{filePath}}` template variable exists for file triggers. | [Hooks](https://kiro.dev/docs/hooks/) and [IDE 1.0 hooks](https://kiro.dev/docs/ide/whats-new-v1/hooks/) | Key names of the stdin JSON for file events are not documented: UNVERIFIED. |
| K-4 | `PostFileSave` fires when a file is saved or modified by the agent, and it cannot block. | [IDE 1.0 hooks](https://kiro.dev/docs/ide/whats-new-v1/hooks/) and [Hook types](https://kiro.dev/docs/hooks/types/) | The reconciliation record lists a conflicting wording ("a user saves a code file"). Whether editor saves by the user fire it is UNVERIFIED. |
| K-5 | Exit 0: stdout is added to the agent context. Any other exit code: stderr is sent to the agent and the agent is told the hook returned an error. Only exit 2 on `PreToolUse`, `UserPromptSubmit` and `PreTaskExec` blocks. | [Hook actions](https://kiro.dev/docs/hooks/actions/) and [IDE 1.0 hooks](https://kiro.dev/docs/ide/whats-new-v1/hooks/) | Whether stdout of a failing run is shown anywhere is UNVERIFIED. The two pages differ on whether every non-zero exit blocks a `PreToolUse` hook. A `PostFileSave` hook cannot block, so the difference does not change this design. |
| K-6 | Hooks activate when a session starts. Hook execution logs are in the Kiro output panel. | [Hooks](https://kiro.dev/docs/hooks/) and [Hook troubleshooting](https://kiro.dev/docs/hooks/troubleshooting/) | Log event names for an execution are unknown (F-H12). |
| K-7 | Global hooks in the user `.kiro/hooks` folder run alongside workspace hooks (documented for CLI V3 and mentioned for the IDE). | [Hooks](https://kiro.dev/docs/hooks/) | Absent on this host on 2026-11-24. |
| K-8 | Kiro runs hooks only in folders the user has trusted. | A third-party enforcement document ([Obot device management](https://docs.obot.ai/device-management/enforcement/)) and the logged event `hooks.v2.executionDisabledUntrustedWorkspace` | No official Kiro page was found. The trust prompt wording and scope are UNVERIFIED. |
| K-9 | Agent writes to these paths need approval: `.vscode/`, `.git/`, the `.code-workspace` pattern, `mcp.json` (basename), `.kiroignore` and two backup patterns. `.kiro/hooks` is not listed. | [Privacy and security](https://kiro.dev/docs/privacy-and-security/) (updated 2026-11-20) | Behavior for a hook-file edit is UNVERIFIED. |
| K-10 | Security guidance: use a clean environment or dedicated account, keep AWS credentials out of the environment, use workspace trust. AWS bulletin 2026-117-AWS (CVE-2026-95985): before IDE 1.0.242 an agent in an untrusted workspace could write to global configuration. Review the user `.kiro` folder for entries you did not create. | [Privacy and security](https://kiro.dev/docs/privacy-and-security/) and [AWS bulletin 2026-117-AWS](https://aws.amazon.com/security/security-bulletins/2026-117-aws/) | The installed IDE is 1.4.215 (`product.json`), above 1.0.242. The fix content was not verified. |

Content from the Kiro documentation was rephrased for compliance with licensing restrictions.

**Findings.** Each row was read from the named file, page or host listing.

| ID | Finding (read from file) | Consequence |
|---|---|---|
| F-H1 | Three of the four registered matchers are written with forward slashes only (`core/src/verdictkit/.*\.py$` style, for the core, reel and quote hooks) and do not match a path written with backslashes. The fourth, `\.py$`, is separator-neutral. Which path form Kiro supplies is UNVERIFIED. | On Windows up to three of four hooks may never fire (8.3). |
| F-H2 | The fence matcher `\.py$` fires for all 107 tracked Python files. The LLM fence scans 55 of them (counted from the `FENCED` list in `tests/contract/test_llm_fence.py` and the file listing). | 52 saves per full pass trigger an unrelated run, and there is no root anchor. |
| F-H3 | No hook runs the HTTP boundary suite (`tests/api`, 10 files), validates `api/openapi.yaml` or `api/examples`, or tests the hook files. A save to any of the 43 Python files under `tests/` (39 are named `test_*.py`) fires only the fence, which does not test them. A save to `api/openapi.yaml`, `api/examples/*.json` or `.kiro/hooks/*.json` fires nothing. | Contract validation and security regression have no automatic guard (8.9). |
| F-H4 | The registered commands use plain `uv run`. Per the [uv documentation](https://docs.astral.sh/uv/concepts/projects/sync/), `uv run` locks and syncs before it runs the command, so it can rewrite `uv.lock`, change `.venv` and use the network. CI and the baseline use `uv run --no-sync`. | The registered text is not read-only in the sense of 8.8. |
| F-H5 | The baseline runs of the hook commands (made from a terminal, not fired by Kiro) used `uv run --no-sync` with `-p no:cacheprovider` appended (`baseline/records.jsonl`). The registered text has neither. No run of the registered text exists. The recorded durations (fence 2.6 s, core 12.4 s, reel 13.2 s, quote 3.9 s, Windows host) belong to the modified text. The core run is partial: `-x` stopped it after 159 passed and 1 failed. | 8.5 has no evidence for the exact command text. |
| F-H6 | Registered timeouts are 60 s (fence) and 180 s (core, reel, quote), all above the longest recorded duration (13.2 s). | 8.5 holds provisionally. Re-measure the exact text. |
| F-H7 | On Windows, BE-1 plus `-x` stops the core command at test 160. Derived count: 239 tests selected (260 in E-006 minus 13 reel and 8 quote tests) minus 160 executed leaves about 79 not run. No per-test listing exists. | UNVERIFIED. The failure hides later tests. |
| F-H8 | Kiro sends stderr to the agent when a command exits non-zero and adds stdout to the agent context on exit 0 (K-5). pytest prints its report to stdout. | A failing hook may show the agent no failure detail (8.6). Stdout volume of passing hooks costs context. |
| F-H9 | There is no marker hook, no matcher test, no hook that runs a matcher test when a hook file changes, and no evidence mechanism. | 8.2, 8.4, 8.9 and 8.14 are unmet today. |
| F-H10 | Kiro semantics not documented or not observed: trigger (agent only or user saves too, K-4), matcher grammar and path form (K-2), stdin keys (K-3), the shell used on Windows, whether a timeout kills the child process tree, whether several matching hooks run in parallel, trust prompt scope (K-8), and the log event name of an execution. | Resolved only by the probes in D3.8 (U-1 to U-10). |
| F-H11 | Kiro offers `{{filePath}}` substitution in command text (K-3). A path containing `&`, `;`, `$(`, a backtick or `%` can inject shell syntax in `cmd`, PowerShell or `sh`. No registered hook uses it. | D3 forbids it (DD3-3). |
| F-H12 | Historical log export, counts only: `hooks.reload.loaded` with `{"read":4,"registered":4}` 16 times; "v2 hooks cache initialized (hooks load at session start)" 8 times; `hooks.v2.executionDisabledUntrustedWorkspace` 4 times; `fs.hooksReload.ok` 2; `fs.setHookEnabledRead.ok` 3; `fs.setHookEnabledWrite.ok` 2. No execution event. The session files hold 0 hook-typed events (H8). A historical demo plan (a clone of the frozen tag, manual IDE steps, README status `PENDING MANUAL IDE ACTION`) was never carried out. It proposed appending a comment line to `examples/stub_claimtype/__init__.py`. | The event vocabulary of an execution is unknown. D3 does not adopt a no-op edit as a trigger (DD3-11). |
| F-H13 | Trust and configuration: `.kiro/hooks` is not in the documented protected-path list (K-9). The user-level `.kiro` folder on this host has no `hooks` folder and no user `mcp.json`. User-level `sandbox.json` has `"enabled": false`, so no sandbox is known to confine hook commands. `.kiro/settings/mcp.json` registers a server started with plain `uv run python -m verdictkit.mcp_server`. Whether workspace trust governs starting it is UNVERIFIED. | An agent edit of a hook file may need no approval. The MCP entry belongs in the pre-trust review (D3.8). |
| F-H14 | Code reached by hook commands (static search of `tests`, `core/src` and the app sources): no import of `urllib.request`, `requests`, `aiohttp`, `ftplib` or `smtplib`; FastAPI `TestClient` is used for in-process calls; `run_case` calls in tests pass `network=False`; `mcp_server.verify_claim` passes `network=not _readonly()`, and tests in `tests/contract/test_mcp_server.py` call it without setting `VK_MCP_READONLY` (the stub claim type declares no evidence adapter, so no network use is expected); loopback `http.client` appears only in `tests/ui/test_judge_preview.py`, which no hook runs; `AF_UNIX` sockets appear in tests that skip off Linux; `tests/api/test_startup_gate.py` starts one child process with `os.environ` plus test values; `shutil.rmtree` is applied only to directories the code created (`mcp_server.py`), and the `unlink` calls in `api/draft_store.py` and `examiner/worker.py` act on the store's own bundle files and the examiner socket path. `scripts/reel_ohlcv_acquire.py` imports `urllib.request`. It is outside the searched scope and no hook runs it. Not verified by execution. | Network and deletion risk is low but not zero. Environment inheritance matters (DD3-6). |
| F-H15 | BE-1 is a portability defect in the test as far as read. `mcp_server._workdir()` calls `tempfile.mkdtemp` then `Path.chmod(0o700)`. The [Python 3.12 documentation](https://docs.python.org/3.12/library/os.html#os.mkdir) says that on Windows, since 3.12.4, `os.mkdir` with mode `0o700` restricts the directory to the current user and administrators, and other mode values are ignored. `chmod` cannot set POSIX bits on Windows and `stat` reports `0o777`. The project allows Python 3.12 and later, so 3.12.0 to 3.12.3 are admitted. Whether the directory is private on the baseline host (Python 3.12.10) is UNVERIFIED until its access list is read. | D3.9. |
| F-H16 | BE-2 facts relevant to P2: the test uses the hard-coded port 65534 (assumed closed, and against 1.17), its client timeout is 2 s, and the bridge script uses a 10 s upstream timeout. The cause is not established. No hook runs the test. | D3.9 interface with P7. |
| F-H17 | Host facts (Windows development host): Windows PowerShell 5.1 and `cmd` exist. `uv.exe` resolves from the user `PATH` (a Python 3.13 `Scripts` folder). `python` resolves to a real Python 3.12, not the Microsoft Store stub. The `PATH` and shell that Kiro gives a hook are unknown. No tracked path contains a space, but user folders often do. | Preflight checks in D3.8. Paths with spaces are covered in D3.5. |

Each finding was read from the named file, page or host listing on 2026-11-24 (branch `feature/kiro-next-phase`, based on commit `84df25c`). Reading is not execution: no finding in F-H1 to F-H17 comes from a run made for D3. F-H5, F-H6 and F-H7 quote Baseline_Run records (E-010 and E-012 to E-014), which are earlier runs and are not new Execution_Records. Behavior claims about Kiro stay UNVERIFIED where marked.

### D3.3 Design decisions

| ID | Decision | Rejected alternative | Why |
|---|---|---|---|
| DD3-1 | Only `PostFileSave` hooks with command actions. | Agent-prompt hooks. Aggregation on the `Stop` trigger. | Agent actions use credits and can loop. Aggregation conflicts with "once for that save" (8.1). Kept as OD-D3-5. |
| DD3-2 | One cross-platform runner, `scripts/hooks/vk_hook.py`, runs every hook. Standard library only, one file, target under 400 lines, no network, no new dependency. | Inline pytest commands in the JSON. Two scripts (PowerShell and `sh`). | Same behavior on Windows and Linux. A child started from an argument list needs no shell quoting. It enables a deadline, a lock, output limits and evidence. |
| DD3-3 | The command text in every hook is `uv run --no-sync --offline python scripts/hooks/vk_hook.py` followed by one runner id. No quotes, operators, variables or `{{filePath}}`. The file path is read from stdin as data. | Substituting the path into the command. | Injection (F-H11). Same text in PowerShell, `cmd` and `sh` (8.12). |
| DD3-4 | "Read-only verification command" is defined (proposed to D10 as G-7): the only writes allowed are git-ignored cache and evidence files in an allowlist (`__pycache__`, `artifacts/hooks`, the redirected Hypothesis directory, the OS temp directory). No change to tracked files or the git index, no deletion, move or rename of a file the command did not create, no network use started by the command or the runner. Flags that enforce it: `--no-sync`, `--offline`, `-p no:cacheprovider`, and `HYPOTHESIS_STORAGE_DIRECTORY` under `artifacts/hooks`. | Literal "no writes". | Test runners always write caches, so the literal reading cannot be met (8.8). |
| DD3-5 | Matchers are whole-string, separator-neutral regexes from a portable subset, with a tolerant root prefix until probe U-2 shows the path form (D3.5). | Globs. Lookahead exclusions. Case-insensitive flags. Relying on one path form. | F-H1 and F-H10. The subset has the same meaning in JavaScript, Python, PCRE and RE2 for a path without line breaks. |
| DD3-6 | The runner passes the child an allowlisted environment and records only the names of secret-like variables it dropped. | Inheriting the Kiro environment. | Kiro warns that the agent can reach environment credentials (K-10). 8.18. |
| DD3-7 | One run lock per checkout (OS file lock, RN-4), bounded wait, no ordering guarantee between waiting runs, no coalescing of saves. | Parallel runs. Dropping runs that a newer save supersedes. | The baseline had 3 log-file lock collisions (`EXECUTION_INDEX`). Dropping runs conflicts with 8.1. |
| DD3-8 | Two time bounds: an explicit Kiro timeout (never 0) and a runner deadline below it that kills the process tree and writes evidence. | Relying on the Kiro timeout. | Process-tree kill and log behavior are unknown (F-H10). A killed runner writes nothing. |
| DD3-9 | Failure output goes to stderr in a delimited, sanitized, capped block. A successful run prints at most 300 characters. | Passing tool output through. | F-H8. Output enters the agent context, which is a prompt-injection channel and a token cost. |
| DD3-10 | Attribution needs two keys: a runner record (facts the runner observed) and a Kiro-side artifact (what Kiro displayed or logged). The runner never writes an automatic-execution label. | A self-reported marker as proof. | A command can be run by hand with identical output (3.6, 3.7). |
| DD3-11 | Verification runs in a disposable trusted clone from a pre-registered plan, with legitimate edits only, a fixed edit budget and negative controls. No-op edits (an appended comment, whitespace, `touch`) are forbidden. | Synthetic trigger edits. | Maintainer instruction for D3 (2026-11-24, recorded here): do not generate artificial execution events to raise Kiro usage statistics. 8.15 to 8.18. |
| DD3-12 | BE-1: platform dispatch inside the same test, plus a preservation guard and a negative control (D3.9). | `skip`, `xfail` or a relaxed assertion on Windows. | 13.11 and 2.11. |
| DD3-13 | BE-2: no hook is attached to its test. P7 owns instrumentation and cause. D3 supplies the runner and the evidence schema. | A longer timeout. A hook on the judge-preview test. | 13.12. A hook on a failing test would fail for an unknown reason. |
| DD3-14 | Credits: hook runs are shell actions, which Kiro documents as not consuming credits ([best practices](https://kiro.dev/docs/hooks/best-practices/)). Their stdout enters the agent context, so output caps also bound that context (any effect on credit use is UNVERIFIED). Credits are read only from a Kiro usage record (16.2). Hook counts are never reported as usage. | Estimating credits from hook counts. | 16.2 and 3.8. |

### D3.4 Hook set and trigger matrix

Every row of the Hook_Set below is DESIGNED. Every hook command in the JSON is exactly `uv run --no-sync --offline python scripts/hooks/vk_hook.py <runner id>`. All hooks use trigger `PostFileSave`, action type `command` and `enabled` true. The "Runs" column is the argument list that the runner passes to the project interpreter (`python -m pytest ...`), never a shell string.

| ID | Hook name | Runner id | Runs | Purpose | Timeout s | Req |
|---|---|---|---|---|---|---|
| HK-0 | `hook-marker-on-agent-save` | `marker` | No child process. Prints one marker line and writes one evidence record. | Marker (8.14) and probe for path form and stdin keys | 30 (ASSUMED) | 8.14, 8.15 |
| HK-1 | `llm-fence-on-agent-save` | `fence` | `-q -p no:cacheprovider tests/contract/test_llm_fence.py` | LLM fence on the fenced paths (2.12) | 60 (existing) | 2.12, 8.1 |
| HK-2 | `core-contract-tests-on-agent-save` | `core` | `-q -p no:cacheprovider tests/contract -m "not isolation" --ignore=tests/contract/test_reel_contract.py --ignore=tests/contract/test_quote_contract.py` (no `-x`, see note b) | Core contract suite | 180 (existing) | 8.1, 8.13 |
| HK-3 | `reel-contract-tests-on-agent-save` | `reel` | `-q -p no:cacheprovider tests/contract/test_reel_contract.py` | Reel contract | 180 (existing) | 8.1 |
| HK-4 | `quote-contract-tests-on-agent-save` | `quote` | `-q -p no:cacheprovider tests/contract/test_quote_contract.py` | Quote contract | 180 (existing) | 8.1 |
| HK-5 | `api-contract-on-agent-save` | `api-contract` | `-q -p no:cacheprovider tests/contract/test_api_schema.py tests/api/test_http_run_lifecycle.py` | Contract validation: spec validity, examples, server responses against the spec | 120 (ASSUMED) | 8.1 |
| HK-6 | `api-security-regression-on-agent-save` | `api-security` | `-q -p no:cacheprovider tests/api` | Security regression: the HTTP boundary suite (intake, draft store, freeze, evidence, examination, examiner identity, startup gate, lifecycle) | 120 (ASSUMED) | 8.1 |
| HK-7 | `hook-matchers-on-agent-save` | `hook-matchers` | `-q -p no:cacheprovider tests/contract/test_hook_matchers.py tests/contract/test_hook_runner.py` | Matcher and runner tests when a hook file or the runner changes (8.9) | 120 (ASSUMED) | 8.4, 8.9 |

- **(a)** The four existing hook names are kept. Their matchers and commands change.
- **(b)** No `-x` on any hook: it hid about 79 tests on Windows (F-H7). The Hypothesis profile is the default `dev` profile, as `.kiro/steering/testing.md` prescribes for local runs. The baseline runs of the hook commands recorded no profile variable. The `ci` profile is for release evidence.
- **(c)** Timeouts: existing values stay until the exact command text is measured (at least 3 runs per host class, cold and warm). A timeout is never below the longest recorded duration (8.5) and never 0. Recorded durations to date: fence 2.6 s, core 12.4 s (partial), reel 13.2 s, quote 3.9 s. The `tests/api` suite ran as 8.6 s (9 files, E-007) plus 3.8 s (startup and attestation, E-008) in other commands. HK-5, HK-6, HK-7 and the marker are UNMEASURED.
- **(d)** The runner's inner deadline is the timeout minus the larger of 5 s and 10 percent of the timeout (D3.6).

**Matchers (decoded regular expressions; in the JSON file every backslash is doubled).**

```text
HK-0  ^(?:.*[\\/])?(?:core[\\/]src[\\/]verdictkit[\\/].*\.py|apps[\\/](?:reel|quote)-autopsy[\\/]src[\\/].*\.py|tests[\\/](?:contract|api)[\\/].*\.py|tests[\\/]conftest\.py|tests[\\/]contract[\\/]hook_matcher_corpus\.json|api[\\/]openapi\.yaml|api[\\/]examples[\\/].*\.json|\.kiro[\\/]hooks[\\/][^\\/]+\.json|scripts[\\/]hooks[\\/].*\.py)$
HK-1  ^(?:.*[\\/])?(?:core[\\/]src[\\/]verdictkit[\\/](?:(?:custody|examiner|evidence|api)[\\/].*|(?:sweep|model|canonical|plugin|pipeline|bundle|cli))|apps[\\/](?:reel|quote)-autopsy[\\/]src[\\/].*|tests[\\/]contract[\\/]test_llm_fence)\.py$
HK-2  ^(?:.*[\\/])?(?:core[\\/]src[\\/]verdictkit[\\/].*|tests[\\/]contract[\\/].*|tests[\\/]conftest)\.py$
HK-3  ^(?:.*[\\/])?(?:apps[\\/]reel-autopsy[\\/]src[\\/].*|tests[\\/]contract[\\/]test_reel_contract)\.py$
HK-4  ^(?:.*[\\/])?(?:apps[\\/]quote-autopsy[\\/]src[\\/].*|tests[\\/]contract[\\/]test_quote_contract)\.py$
HK-5  ^(?:.*[\\/])?(?:api[\\/]openapi\.yaml|api[\\/]examples[\\/].*\.json|core[\\/]src[\\/]verdictkit[\\/]api[\\/].*\.py|tests[\\/]contract[\\/]test_api_schema\.py|tests[\\/]api[\\/]test_http_run_lifecycle\.py)$
HK-6  ^(?:.*[\\/])?(?:core[\\/]src[\\/]verdictkit[\\/](?:api|custody|examiner|evidence)[\\/].*|tests[\\/]api[\\/].*|tests[\\/]conftest)\.py$
HK-7  ^(?:.*[\\/])?(?:\.kiro[\\/]hooks[\\/][^\\/]+\.json|tests[\\/]contract[\\/]test_hook_(?:matchers|runner)\.py|tests[\\/]contract[\\/]hook_matcher_corpus\.json|scripts[\\/]hooks[\\/].*\.py)$
```

HK-0 is the union of the other seven scopes. The JSON form of HK-7 is shown once as one entry of the `hooks` array. The timeout of 120 is the ASSUMED value from the table.

```json
{
  "name": "hook-matchers-on-agent-save",
  "trigger": "PostFileSave",
  "matcher": "^(?:.*[\\\\/])?(?:\\.kiro[\\\\/]hooks[\\\\/][^\\\\/]+\\.json|tests[\\\\/]contract[\\\\/]test_hook_(?:matchers|runner)\\.py|tests[\\\\/]contract[\\\\/]hook_matcher_corpus\\.json|scripts[\\\\/]hooks[\\\\/].*\\.py)$",
  "action": {
    "type": "command",
    "command": "uv run --no-sync --offline python scripts/hooks/vk_hook.py hook-matchers"
  },
  "timeout": 120,
  "enabled": true
}
```

**Trigger matrix.** `x` means the hook fires. A blank cell means it does not. Each row was checked against the matchers above (not an Execution_Record). HM-T1 and HM-T2 in D3.5 turn the check into tests.

| # | Save class and example path | HK-0 | HK-1 | HK-2 | HK-3 | HK-4 | HK-5 | HK-6 | HK-7 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `core/src/verdictkit/custody`, `examiner` or `evidence` (example `custody/ledger.py`) | x | x | x | | | | x | |
| 2 | `core/src/verdictkit/api` (example `api/server.py`) | x | x | x | | | x | x | |
| 3 | `core/src/verdictkit` modules `sweep`, `model`, `canonical`, `plugin`, `pipeline`, `bundle` or `cli` (example `canonical.py`) | x | x | x | | | | | |
| 4 | `core/src/verdictkit` other modules (examples `mcp_server.py`, `envprint.py`, `__init__.py`) | x | | x | | | | | |
| 5 | `apps/reel-autopsy/src` (example `claim_type.py`) | x | x | | x | | | | |
| 6 | `apps/quote-autopsy/src` (example `claim_type.py`) | x | x | | | x | | | |
| 7 | `tests/contract/test_llm_fence.py` | x | x | x | | | | | |
| 8 | `tests/contract/test_reel_contract.py` | x | | x | x | | | | |
| 9 | `tests/contract/test_quote_contract.py` | x | | x | | x | | | |
| 10 | `tests/contract/test_api_schema.py` | x | | x | | | x | | |
| 11 | `tests/contract/test_hook_matchers.py` and `tests/contract/test_hook_runner.py` | x | | x | | | | | x |
| 12 | other `tests/contract/*.py` | x | | x | | | | | |
| 13 | `tests/api/test_http_run_lifecycle.py` | x | | | | | x | x | |
| 14 | other `tests/api/*.py` | x | | | | | | x | |
| 15 | `tests/conftest.py` | x | | x | | | | x | |
| 16 | `api/openapi.yaml` and `api/examples/*.json` | x | | | | | x | | |
| 17 | `.kiro/hooks/*.json`, `scripts/hooks/*.py`, `tests/contract/hook_matcher_corpus.json` | x | | | | | | | x |
| 18 | Everything else, no hook fires: `tests/integration`, `tests/reel_evidence`, `tests/ui`, `scripts/*.py` outside `scripts/hooks`, `examples`, `docs`, UI sources, `artifacts`, `.venv`, `node_modules`, `.git` | | | | | | | | |

- Rows 8 and 9: HK-2 also fires. Its command ignores those two files, and a single regex cannot exclude them without lookahead (R-M5). The overlap is accepted.
- The worst case is 5 hooks for one save (row 2). The runner serializes them, so wall time is the sum. From recorded durations of similar commands the sum for row 2 is at least 23.6 s (2.6 + 12.4 + 8.6), UNVERIFIED for the exact commands. The budget rule is in D3-AC-16 (D3.10).
- Counts derived during design by counting the 209 tracked files at commit `84df25c` against these patterns (not an Execution_Record; D3-AC-2 re-derives them): HK-0 106, HK-1 56, HK-2 58, HK-3 14, HK-4 10, HK-5 26, HK-6 37, HK-7 3.
- Documented coverage gaps: 17 tracked Python files fire no hook (`examples/stub_claimtype` 2, `scripts` 4, `tests/integration` 9, `tests/reel_evidence` 1, `tests/ui` 1). They stay CI-only. `tests/ui` and `scripts/serve_judge_ui.py` stay unhooked until BE-2 is closed (DD3-13). A reserved hook for them is not defined.
- Hooks considered and not adopted: a lockfile hook (CI already runs `uv lock --check`), hooks for `Dockerfile` and `deploy/entrypoint.sh` (they need Docker and are not read-only), a hook for `tests/integration` (its duration was not measured separately and it holds the Hypothesis sweeps), and `Stop`-trigger aggregation (OD-D3-5).

### D3.5 Cross-platform path matching and matcher tests

**Matcher rules.**

| ID | Rule | Reason |
|---|---|---|
| R-M1 | Whole string: start with `^` and end with `$`. | `search`, `match` and `fullmatch` then agree, whichever the Kiro engine uses. |
| R-M2 | Every separator is the class `[\\/]` (JSON form `[\\\\/]`). A literal `/` or `\` outside a class is not used. | Windows backslash, POSIX slash, mixed separators. |
| R-M3 | A tolerant root prefix `(?:.*[\\/])?` accepts relative paths, drive-letter paths (`C:\` and `c:\`), POSIX absolute paths, `\\wsl$` and other UNC paths, and any directory name containing spaces. | The path form Kiro supplies is unknown (K-2). |
| R-M4 | Directory and file names are literal, dots are escaped, and an extension is part of the pattern. | `.pyc`, `.py.bak` and `.pyi` must not match. |
| R-M5 | Exclusion is by positive roots, not by lookahead. | Lookaround is not in the portable subset. |
| R-M6 | Allowed syntax only: `^`, `$`, `.`, `*`, `+`, `?`, character classes, `(?: )`, alternation, `\.` and the separator class. Forbidden: lookaround, backreferences, named groups, inline flags, `\b`, `\d`, `\s`, `\w`, `\A`, `\Z`. A test lints every matcher. | Same meaning in JavaScript, Python, PCRE and RE2. |
| R-M7 | Case: matchers are case-sensitive. A path such as `Core\Src\verdictkit\x.py` does not match (documented limitation, OD-D3-6). | A case-insensitive flag is not portable. Decide after probe U-2. |
| R-M8 | Strict mode: after probe U-2 shows relative paths, the tolerant prefix is removed and the "strict only" corpus rows become assertions (OD-D3-1). | Removes duplicate-root false positives. |

**Path forms.**

| ID | Form | Example |
|---|---|---|
| PF-1 | Relative, slash | `core/src/verdictkit/canonical.py` |
| PF-2 | Relative, backslash | `core\src\verdictkit\canonical.py` |
| PF-3 | Absolute Windows, lowercase drive | `c:\Users\dev\Desktop\KIROWEEN\verdictkit-kiro-next\core\src\verdictkit\canonical.py` |
| PF-4 | Absolute Windows with spaces | `C:\Users\Jane Doe\My Repo\core\src\verdictkit\canonical.py` |
| PF-5 | Absolute POSIX with a space | `/home/dev/my repo/core/src/verdictkit/canonical.py` |
| PF-6 | UNC or WSL | `\\wsl$\Ubuntu\home\dev\repo\core\src\verdictkit\canonical.py` |
| PF-7 | Mixed separators | `core/src\verdictkit\canonical.py` |

**Corpus.** Mode is ALWAYS unless noted. A STRICT ONLY row is asserted only after R-M8 is applied.

| ID | Path | Expected hooks | Mode |
|---|---|---|---|
| HM-P1 | `core/src/verdictkit/canonical.py` | HK-0, HK-1, HK-2 | ALWAYS |
| HM-P2 | `core\src\verdictkit\canonical.py` | HK-0, HK-1, HK-2 | ALWAYS |
| HM-P3 | `core/src/verdictkit/custody/ledger.py` (nested) | HK-0, HK-1, HK-2, HK-6 | ALWAYS |
| HM-P4 | `core\src\verdictkit\custody\ledger.py` (nested) | HK-0, HK-1, HK-2, HK-6 | ALWAYS |
| HM-P5 | `C:\Users\Jane Doe\My Repo\core\src\verdictkit\api\server.py` (spaces, nested) | HK-0, HK-1, HK-2, HK-5, HK-6 | ALWAYS |
| HM-P6 | `c:\Users\dev\Desktop\KIROWEEN\verdictkit-kiro-next\apps\reel-autopsy\src\reel_autopsy\claim_type.py` | HK-0, HK-1, HK-3 | ALWAYS |
| HM-P7 | `/home/dev/my repo/apps/quote-autopsy/src/quote_autopsy/claim_type.py` | HK-0, HK-1, HK-4 | ALWAYS |
| HM-P8 | `\\wsl$\Ubuntu\home\dev\repo\tests\api\test_m3b_draft_store.py` | HK-0, HK-6 | ALWAYS |
| HM-P9 | `core/src\verdictkit\sweep.py` (mixed) | HK-0, HK-1, HK-2 | ALWAYS |
| HM-P10 | `api/openapi.yaml` and `api\examples\health_judge.json` | HK-0, HK-5 | ALWAYS |
| HM-P11 | `.kiro/hooks/llm-fence.json` and `.kiro\hooks\llm-fence.json` | HK-0, HK-7 | ALWAYS |
| HM-P12 | `tests\contract\test_reel_contract.py` | HK-0, HK-2, HK-3 | ALWAYS |
| HM-P13 | `tests/conftest.py` | HK-0, HK-2, HK-6 | ALWAYS |
| HM-P14 | `core/src/verdictkit/mcp_server.py` | HK-0, HK-2 | ALWAYS |
| HM-N1 | `core/src/verdictkit/canonical.pyc` | none | ALWAYS |
| HM-N2 | `core/src/verdictkit/canonical.py.bak` | none | ALWAYS |
| HM-N3 | `core/src/verdictkit/README.md` | none | ALWAYS |
| HM-N4 | `core/src/verdictkit_extra/x.py` | none | ALWAYS |
| HM-N5 | `core/src/other/x.py` | none | ALWAYS |
| HM-N6 | `apps/reel-autopsy/web/src/App.tsx` | none | ALWAYS |
| HM-N7 | `docs/ARCHITECTURE.md` | none | ALWAYS |
| HM-N8 | `artifacts/hooks/evidence.jsonl` | none | ALWAYS |
| HM-N9 | `tests/ui/test_judge_preview.py` | none (documented gap) | ALWAYS |
| HM-N10 | `scripts/serve_judge_ui.py` | none (documented gap) | ALWAYS |
| HM-N11 | `Core\Src\verdictkit\x.py` | none (case limitation, R-M7) | ALWAYS |
| HM-N12 | `C:\Users\Jane Doe\My Repo\README.md` | none | ALWAYS |
| HM-N13 | `tests/integration/test_quote_sweeps.py` | none (documented gap) | ALWAYS |
| HM-S1 | `node_modules/pkg/core/src/verdictkit/x.py` | none | STRICT ONLY (matches HK-0 and HK-2 in tolerant mode) |
| HM-S2 | `.venv/Lib/site-packages/pkg/tests/api/x.py` | none | STRICT ONLY (matches HK-0 and HK-6 in tolerant mode) |
| HM-S3 | `docs/examples/core/src/verdictkit/x.py` | none | STRICT ONLY (matches HK-0 and HK-2 in tolerant mode) |

**Matcher tests.** DESIGNED files: `tests/contract/test_hook_matchers.py` (Python `re`), `tests/contract/hook_matcher_corpus.json` (the corpus), `scripts/hooks/check_matchers.cjs` (JavaScript `RegExp`, run by npm and in the CI web-ui job, and on the Windows host where Node exists) and `tests/contract/test_hook_runner.py` (D3.6).

| ID | Test | What it asserts | Runs on |
|---|---|---|---|
| HM-T1 | Corpus | Every row is classified as expected for every hook, 100 percent. The corpus rows together with the generated forms of HM-T2 give each hook at least 2 positive paths per separator style, at least 2 negative paths, and at least 1 nested, 1 spaced, 1 absolute Windows and 1 absolute POSIX path (8.4). The test fails on any misclassification. | Windows host, Linux CI |
| HM-T2 | Real-tree property | For every tracked file (`git ls-files`) and each path form PF-1 to PF-7, the set of firing hooks equals an independent reference function in the test (an oracle written as plain path rules, not as regexes). Every tracked `.py` file under a watched root fires at least one hook. The uncovered files are exactly an explicit allowlist with a reason each. | Windows host, Linux CI |
| HM-T3 | Lint and equivalence | No forbidden construct (R-M6). `search` equals `fullmatch` on every corpus path. The JavaScript engine gives the same result as Python on every corpus row. | Python part: Windows host, Linux CI. JavaScript part: Linux CI, and the Windows host where Node exists. |
| HM-T4 | Sentinels | The four old matchers (core, reel, quote, fence) are kept in the test as witnesses. The test asserts that each of core, reel and quote fails at least one backslash positive, and that the fence matcher fires for every tracked `.py` file (107 at commit `84df25c`), including files the fence does not scan. This proves the corpus detects the defects of F-H1 and F-H2. | Windows host, Linux CI |
| HM-T5 | Hook file checks | Every hook entry has trigger `PostFileSave`, action type `command`, a boolean `enabled`, an integer `timeout` from 1 to 600 that is at least the 8.5 floor, a command equal to the canonical text for its runner id, and no agent action. The command contains none of these characters: ampersand, vertical bar, semicolon, less-than, greater-than, backtick, dollar sign, percent sign, caret or a quote character. It also does not contain the sequence `{{`. HK-0 equals the union of the other seven scopes. | Windows host, Linux CI |

HK-7 runs the matcher test (HM-T1 to HM-T5, Python part) and the runner test when a hook file, the matcher test, the runner test or a runner script is saved (8.9). CI runs all of them on every change to `.kiro/hooks`, `scripts/hooks` or `tests/contract` (new CI step, owner-run pull request per D0.9).

### D3.6 Hook runner: failure handling, time bound, concurrency, recursion

The runner is DESIGNED, not written. Invocation: `uv run --no-sync --offline python scripts/hooks/vk_hook.py <runner id>`. Extra forms for people: `--manual <runner id>` (declares a manual run), `--print-env-names`, `verify-chain` (D3.7) and `record <label> -- <argument list>` (manual evidence capture of one reviewed command with its direct exit code, D3.9). The `record` form refuses to run when `VK_HOOK_DEPTH` is set, and no hook command can name it (HM-T5), so a hook cannot start it. It always writes mode MANUAL_DECLARED, also in CI, where stdin is not a terminal.

| ID | Concern | Mechanism | Outcome and exit code | Req |
|---|---|---|---|---|
| RN-1 | Unknown runner id or bad state directory | Reject before any child starts. The state directory is `artifacts/hooks` under the repository root found from the script location, never from the working directory or stdin. Refuse if the directory or a parent below the root is a symlink or junction or resolves outside the root. | CONFIG_ERROR, exit 78 | 8.8 |
| RN-2 | Recursion | The runner refuses to start when `VK_HOOK_DEPTH` is 1 or more and sets `VK_HOOK_DEPTH=1` for its child. No hook uses an agent action. The state directory and the evidence files match no matcher (HM-N8). The matcher test never executes hook commands. | RECURSION_BLOCKED, exit 76, no child | 8.1 |
| RN-3 | Stdin | Read only when stdin is not a terminal, at most 64 KiB and at most 2 s, in a reader thread. Record the status, byte count, SHA-256 and the top-level key names only. Parse errors are recorded and are never fatal. | No outcome change | 8.2, 8.15 |
| RN-4 | Concurrency | An exclusive OS lock on `artifacts/hooks/run.lock` (`msvcrt.locking` on Windows, `fcntl.flock` on POSIX) is taken by every hook except HK-0, polling every 100 ms. The lock is released by the OS if the process dies, so no stale-lock cleanup exists. The holder's pid and runner id are written inside the file for diagnosis only. Waiting counts against the runner's budget. Waiting is limited to 60 s (ASSUMED). Waiting runners take the lock in polling order, so a strict first in first out order is not guaranteed (DD3-7). | BUSY_TIMEOUT, exit 75, with a one-line stderr message that this run did not verify the change | 8.1 |
| RN-5 | Environment | The child gets an allowlist: `PATH`, `SystemRoot`, `COMSPEC`, `PATHEXT`, `TEMP`, `TMP`, `USERPROFILE`, `HOME`, `LOCALAPPDATA`, `APPDATA`, `LANG`, `LC_ALL`, `TZ`, plus `PYTHONUTF8=1`, `NO_COLOR=1`, `UV_OFFLINE=1`, `UV_NO_SYNC=1`, `HYPOTHESIS_STORAGE_DIRECTORY` (under `artifacts/hooks`), `VK_HOOK_DEPTH=1` and `VK_HOOK_RUN_ID`. Dropped variables are counted. The names of dropped variables that contain `KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL`, `AWS_`, `AZURE_`, `GOOGLE_`, `GITHUB_` or `VK_VAULT` are recorded by name only. The list is a starting point and is UNVERIFIED on both host classes until the preflight (D3.8) runs `uv` and `pytest` with it and records the result. | No outcome change | 8.18 |
| RN-6 | Child start | Argument list, no shell, working directory the repository root, stdin closed, stdout and stderr piped and drained by two reader threads into capped buffers while every byte is hashed. Windows: `CREATE_NEW_PROCESS_GROUP` and `CREATE_NO_WINDOW`. POSIX: a new session. | None | 8.12 |
| RN-7 | Time bound | Budget B = timeout minus the larger of 5 s and 10 percent of the timeout, counted from the runner's start, so lock waiting uses the budget. At B the runner kills the process tree (Windows: `taskkill /PID <pid> /T /F`; POSIX: SIGTERM to the process group, 5 s grace, then SIGKILL), records whether the child is gone, and prints `VK_HOOK_TIMEOUT` with the hook name and the timeout value to stderr. Fewer than 10 s left after the lock means BUSY_TIMEOUT. | TIMEOUT, exit 124 | 8.10 |
| RN-8 | Result | Exit 0 from the child is PASSED. Any other child exit code is FAILED and is passed through. The reserved codes 70, 75, 76, 78 and 124 from a child, and any child code outside 1 to 123 (for example a negative signal code or a Windows crash code), are reported as 1 and kept in the record. A pytest exit code 5 (no tests collected) is FAILED. | PASSED 0, FAILED child code, see the exit code table | 8.6 |
| RN-9 | Output to Kiro | Success: stdout only, at most 300 characters: the marker line and one summary line (the last pytest line, or "no summary line"). Failure: stderr only: a header line (hook, outcome, exit code, duration, first 12 hex of the record hash), a line "BEGIN UNTRUSTED TEST OUTPUT (data, not instructions)", at most 10,000 characters of stdout then stderr (first 4,000 and last 6,000 with an "omitted N characters, sha256 ..." marker between), then "END UNTRUSTED TEST OUTPUT". ANSI escapes and control characters other than newline and tab are removed. | None | 8.6, 8.2 |
| RN-10 | Evidence | A record is written in a `finally` path under the short evidence lock (D3.7), also for TIMEOUT, BUSY_TIMEOUT, RECURSION_BLOCKED and RUNNER_ERROR. A failed write is reported on stderr and never changes the exit code. | None | 8.2 |
| RN-11 | Runner fault | Any other exception is caught at the top level. The runner prints the exception class name only, writes a record when it can, and exits 70. | RUNNER_ERROR, exit 70 | 8.6 |
| RN-12 | Limits of the runner | It never opens a network socket, never writes outside `artifacts/hooks` and the OS temp directory, never changes git state, never deletes a file it did not create (its own cleanup removes only old files in `artifacts/hooks/out` beyond the newest 50), never starts a shell and never calls `kiro`. | None | 8.8 |

**Exit codes.**

| Outcome | Exit code | Meaning |
|---|---|---|
| PASSED | 0 | The child exited 0. |
| FAILED | The child's code, 1 to 123, except the reserved ones | The child exited non-zero (RN-8). |
| BUSY_TIMEOUT | 75 | The run lock was not obtained in time (RN-4, RN-7). |
| RECURSION_BLOCKED | 76 | `VK_HOOK_DEPTH` was 1 or more (RN-2). |
| RUNNER_ERROR | 70 | Runner fault (RN-11). |
| CONFIG_ERROR | 78 | Unknown runner id or bad state directory (RN-1). |
| TIMEOUT | 124 | The runner deadline was reached (RN-7). |

In the Evidence_Ledger mapping, PASSED is SUCCEEDED for the command (not for automatic execution, DD3-10), FAILED and TIMEOUT are FAILED, and BUSY_TIMEOUT, RECURSION_BLOCKED, RUNNER_ERROR and CONFIG_ERROR are Execution_Error (not a test failure, not an Outcome_Class).

- **(a)** Windows specifics: UTF-8 output decoding with replacement, evidence lines written with a plain `\n`, and no reliance on the console code page.
- **(b)** The runner is tested by `tests/contract/test_hook_runner.py` on both host classes (D3-AC-5): a child that sleeps past the deadline is killed with no surviving process and exit 124; two runners started together never overlap; a lock holder killed with SIGKILL or `taskkill` frees the lock at once; `VK_HOOK_DEPTH=1` gives exit 76 and starts no child; a child that prints 1 MiB gives at most 10,000 characters to Kiro and a hash over all bytes; stdin closed, absent, over 64 KiB or not JSON never hangs; a symlinked state directory is refused.
- **(c)** Why a runner and not plain commands: DD3-2, F-H8 and F-H5.

### D3.7 Evidence, marker and attribution

Each hook run writes one local record. The record states what the runner observed. It does not prove that Kiro started the process (DD3-10), so attribution needs a second key from Kiro (AT-1). The mechanism is small: one JSON line per run, written with the standard library only. Everything in D3.7 is DESIGNED. No record has been written and no marker line has been printed.

**Marker line (8.14).** The line has this format. The runner id is never `manual`. A run started with `--manual` prints `mode=MANUAL_DECLARED`.

```text
VK_HOOK_MARKER v1 hook=<runner id> seq=<n> utc=<ISO 8601 with Z> mode=<mode> rec=<first 12 hex of record_sha256>
```

- A run that exits 0 prints the line to stdout after its record is written. HK-0 prints it as its only output.
- The prefix differs from any pytest output, so a fired hook can be told apart from the output of the tests it starts (8.14).
- A run that exits non-zero sends only its stderr block to Kiro (RN-9, K-5). The header line of that block carries the hook name and the same first 12 hex characters of the record hash.

**Record fields (8.2).** One JSON object per run. The field `kind` is MARKER for a record written by HK-0 and RUN for a record written by any other runner id.

| ID | Field | Content | Why |
|---|---|---|---|
| EV-1 | Identity | `schema`, `seq`, `record_id` (UUID), `kind` (MARKER or RUN), `hook` (runner id and hook name) | Orders and names each record (8.2). |
| EV-2 | Invocation | `mode` (KIRO_STDIN when stdin is not a terminal and parses as one JSON object; MANUAL_DECLARED with `--manual`; NO_STDIN; STDIN_UNPARSED), `stdin_status`, `stdin_bytes`, `stdin_sha256`, `stdin_keys` (top-level key names only), terminal flags for stdin, stdout and stderr, `parent_chain` (names of up to four ancestor processes, best effort, may be empty) | Shows how the run was started (3.6, 8.15). |
| EV-3 | File | `path_as_received` and `source_key` (the stdin key it came from). The candidate keys `file_path`, `filePath`, `path`, `file` and `tool_input.path` are a guess and UNVERIFIED. The value is NOT_FOUND when none exists. | The saved file path, and the path form for probe U-2 (8.2, 8.3). |
| EV-4 | Workspace | `root` as seen by the runner, `git_head` (read-only, NOT_AVAILABLE when git is not found), `hook_files_sha256` (SHA-256 over the sorted list of name and SHA-256 of each `.kiro/hooks/*.json` file) | Which checkout and which hook files were in effect (8.15, 8.17). |
| EV-5 | Command | `argv`, `argv_sha256`, `env_dropped_count`, `env_dropped_secret_like_names`, resolved paths of `uv` and `python` | The command and its environment (8.18). |
| EV-6 | Timing | `started_utc` and `ended_utc` (ISO 8601 UTC with Z and microseconds, wall clock), `duration_s` (monotonic clock), `lock_wait_s`, `timeout_s`, `budget_s` | The date and the time bound (8.2, 8.5, 8.10). |
| EV-7 | Result | `outcome`, `exit_code`, `child_exit_code`, `timed_out`, `tree_killed`, `tree_gone` | The exit code and the timeout state (8.2, 8.10). |
| EV-8 | Output | `stdout_bytes`, `stderr_bytes`, `stdout_sha256` and `stderr_sha256` (over all bytes), `captured_text` (the same capped text that Kiro receives, at most 10,000 characters) and `truncated` | The command output with its cap (8.2). |
| EV-9 | Host | `os`, `os_release`, `machine`, Python version | The host class (D0.3). |
| EV-10 | Chain | `prev_sha256` and `record_sha256` | Tamper evidence (3.8). |

**Record rules.**

- The file is `artifacts/hooks/evidence.jsonl`: JSON Lines, UTF-8, `\n` line endings. Its path matches no hook matcher (HM-N8).
- `record_sha256` is the SHA-256 of the canonical JSON of the record without that field (sorted keys, no spaces). `prev_sha256` of the first record is 64 zeros.
- An append happens under a short evidence lock and is flushed and synced. The evidence lock is a second OS file lock, separate from the run lock of RN-4. It is held only while the runner reads the last hash and writes one line, so a runner that cannot get the run lock can still write its BUSY_TIMEOUT record (RN-10).
- The file rotates at 5 MiB, and the new file starts from the last hash.
- `verify-chain` recomputes every hash and reports the first break.
- A typical passing record is under 2 KiB (ASSUMED, not measured).
- The file is local. Anyone with file access can forge it, so it is a record of observation and not proof (R-H4).

**Attribution (3.6, 3.7, 8.15).** The runner never writes an attribution. A curation step does, by joining the records with Kiro-side artifacts. The first version is a manual join (OD-D3-10). Records are never merged or deleted.

| ID | Value | Conditions |
|---|---|---|
| AT-1 | AUTOMATIC_VERIFIED | All of these hold: (a) a runner record with mode KIRO_STDIN; (b) a Kiro-side artifact shows the same hook name firing for the same file path, and its Kiro timestamp is within 5 s (ASSUMED) of `started_utc`; (c) the workspace is the disposable clone recorded in the plan (`root` and `git_head`); (d) Kiro reports the workspace as trusted, with no `hooks.v2.executionDisabledUntrustedWorkspace` event after the trust grant; (e) `hook_files_sha256` equals the reviewed hash. |
| AT-2 | AUTOMATIC_UNCORROBORATED | Only (a) holds. The hook stays UNVERIFIED. |
| AT-3 | MANUAL | The mode is MANUAL_DECLARED, or stdin was a terminal, or the run belongs to a preflight. |
| AT-4 | UNKNOWN | Anything else. |

Records with the same hook and the same `stdin_sha256` within 1 s are flagged DUPLICATE_SUSPECT during curation. The flag tests the rule that a hook runs once for a save (8.1).

**Hook status ladder (8.7).** Each hook has one status per host class.

| ID | Status | Meaning |
|---|---|---|
| ST-1 | REGISTERED | Listed in the hook files and counted by Kiro as registered. This is not evidence of execution. |
| ST-2 | ENABLED_TRUSTED | The hook is enabled, and Kiro shows the workspace as trusted. |
| ST-3 | COMMAND_RUNS_MANUALLY | A preflight with `--manual` ran the command. It shows that the command is runnable, not that the hook fires. |
| ST-4 | FIRED_UNCORROBORATED | An AT-2 record exists. |
| ST-5 | FIRED_VERIFIED | At least one AT-1 record exists. |

Only ST-5 allows the documentation to drop the `UNVERIFIED` label (8.7). A contradiction, for example a changed hook file hash, lowers the status to the highest one that is still supported.

**Kiro-side artifacts (the second key).** The maintainer saves them. The agent never fabricates, reconstructs or back-dates one (3.8).

| ID | Artifact | Use |
|---|---|---|
| KA-1 | The hook result as Kiro displays it in the session (hook card or transcript export), with output, exit code and time | The source of the 8.2 fields. |
| KA-2 | Kiro log lines inside the session window that mention the hook name, a `hooks.` event or `VK_HOOK_MARKER`, extracted read-only as the historical `collect_hook_logs.ps1` did | Shows the firing and the trust state (8.15). The extract is kept outside the repository, as D0.7 does for the Historical_Audit, and is recorded by log file path, extract name, line numbers and SHA-256. |
| KA-3 | The session store, if it holds the marker line with a time written by Kiro | An optional second source. Whether Kiro stores hook output there is UNVERIFIED. |

**Ledger entry (8.2, 4.7).** One entry per firing. The maintainer or the Kiro agent appends it to `docs/next-phase/EXECUTION_EVIDENCE.md`. Earlier rows are never edited.

| ID | Field | Content |
|---|---|---|
| LE-1 | Hook name | The name of the hook that fired. |
| LE-2 | Saved file path | The path of the saved file. |
| LE-3 | Output and exit code | The command output, at most 10,000 characters, and the exit code, as Kiro showed them. |
| LE-4 | Date | The date in ISO 8601 format. |
| LE-5 | Attribution | AT-1 to AT-4. |
| LE-6 | Trust state | Whether Kiro reported the workspace as trusted (8.11). |
| LE-7 | Workspace | The disposable clone and its commit. |
| LE-8 | Record hash | The `record_sha256` of the runner record. |
| LE-9 | Kiro artifact | The reference to KA-1, KA-2 or KA-3, with its SHA-256. |
| LE-10 | Outcome_Class | The Outcome_Class of the command, by the mapping in D3.6. |
| LE-11 | Host class | Windows host or Linux_Docker_Host. |

If Kiro's display and the runner record differ, both are kept, the difference is flagged, and Kiro's values are used for the 8.2 fields. For Requirement 4.7, a hook is `observed running inside Kiro` only after an AT-1 record exists. Otherwise it is `not observed running inside Kiro`.

**Credits and usage (16.2).** Kiro documents that a command hook does not consume credits by itself (DD3-14). That is not observed here and stays UNVERIFIED. Credits for any session are read only from a Kiro usage record and are NOT_AVAILABLE otherwise. The number of hook runs or records is never reported as Kiro usage.

### D3.8 Security review and the disposable trusted-workspace procedure

This section designs the review and the owner-run session that tests whether the hooks fire inside Kiro (8.15 to 8.18). Everything in D3.8 is DESIGNED. No workspace was trusted, no clone was created and no hook was run. The agent cannot grant trust or capture Kiro-side artifacts, so the session is an owner action (B-H2).

**(A) Threats.**

| ID | Threat | Control | Check |
|---|---|---|---|
| T-H1 | A hook command, the runner or the MCP entry changes after review | SHA-256 pinning of `.kiro/hooks/*.json`, `scripts/hooks/*`, `tests/contract/hook_matcher_corpus.json` and `.kiro/settings/mcp.json` at review. The hashes are compared at start, after each edit and at end. A changed hash voids the evidence of that session. | D3-AC-10 |
| T-H2 | An agent edits a hook file in a trusted folder without a prompt (K-9, UNVERIFIED) | The plan forbids edits under `.kiro`, `scripts/hooks` and `artifacts` during the session. Supervised mode. Hash check. | D3-AC-10 |
| T-H3 | pytest runs repository code, including code the agent just edited, with the user's rights, and no sandbox is known to confine it (F-H13, F-H14) | Disposable clone with no remote and no secrets. A low-privilege account or a VM where possible (OD-D3-8). An optional outbound block for the clone's python (OD-D3-7). A time-boxed session. Review of the exported patch before any merge. | D3-AC-10, D3-AC-11 |
| T-H4 | Secrets in the Kiro environment reach the child (K-10) | Environment allowlist (RN-5), secret-like names recorded by name only, a canary variable test, and the checks in S4 | D3-AC-5, D3-AC-10 |
| T-H5 | Shell injection through a file name (F-H11) | Constant command text, argument-list execution, no `{{filePath}}` (DD3-3) | D3-AC-4 |
| T-H6 | Hook output carries instructions into the agent context (K-5) | Output capped, sanitized and labeled as untrusted data (RN-9). A passing run prints only runner text. | D3-AC-5 |
| T-H7 | Evidence is forged or edited | Hash chain and the two-key rule (DD3-10) | D3-AC-6, D3-AC-7 |
| T-H8 | A symlink or junction redirects the state directory | The refusal in RN-1 | D3-AC-5 |
| T-H9 | Lock or output floods slow the development loop | Bounded wait, caps and timeouts, and the retention of the newest 50 out files (RN-12) | D3-AC-5, D3-AC-16 |
| T-H10 | An untrusted workspace is reported as passing or failing (8.11, 2.4) | The run is recorded as UNVERIFIED with the logged reason | D3-AC-13 |
| T-H11 | Trust is granted to a parent folder, or the main workspace becomes trusted (8.16) | The trust scope in step S9 and a before and after comparison of the trust list | D3-AC-10 |
| T-H12 | If trust lets Kiro start the MCP server `verdictkit` (UNVERIFIED, F-H13), it runs plain `uv run`, which can sync and use the network | The entry is disabled in the clone for the session and is in the review table (PR-9) | D3-AC-11 |

**(B) Pre-trust review (8.17).** Every configured hook command and every other surface that trust could start is reviewed before the clone is trusted. The review is recorded.

| ID | Executable surface | Executes | Reads | Writes | Network | Verdict |
|---|---|---|---|---|---|---|
| PR-1 | Runner `scripts/hooks/vk_hook.py` (every hook) | Python standard library, then `python -m pytest` from an argument list | Repository files, stdin, environment | `artifacts/hooks` and the OS temp directory | None by design (`--offline`, no sockets) | ALLOW with controls (hash pinned) |
| PR-2 | HK-1 fence | pytest on one file, with an AST scan of 55 files | Source files | Caches | None | ALLOW |
| PR-3 | HK-2 core | pytest over `tests/contract`: runs test code, `conftest.py`, core code and app code | Repository | Caches and the OS temp directory (the MCP private directory is created and removed) | None expected (F-H14) | ALLOW with controls |
| PR-4 | HK-3 and HK-4 | pytest on one contract file each | Repository | Caches | None expected | ALLOW |
| PR-5 | HK-5 | pytest with the FastAPI `TestClient` in process | Repository | Caches and the OS temp directory | None expected | ALLOW |
| PR-6 | HK-6 | pytest over `tests/api`, including one test that starts a child Python process with the inherited environment, and AF_UNIX tests that skip off Linux | Repository | Caches and the OS temp directory | None expected beyond loopback (F-H14) | ALLOW with controls (allowlisted environment) |
| PR-7 | HK-7 | pytest on the matcher and runner tests, which start short-lived child processes | Repository | Caches, test copies in `artifacts/hooks`, and the OS temp directory | None | ALLOW |
| PR-8 | HK-0 marker | No child process | stdin and environment names | `artifacts/hooks` | None | ALLOW |
| PR-9 | `.kiro/settings/mcp.json` entry `verdictkit` | `uv run python -m verdictkit.mcp_server` (plain `uv run`, which can sync) with `VK_MCP_READONLY=1` | Repository | OS temp directory | Possible through sync (UNVERIFIED) | DENY for the session: set `"disabled": true` in the clone and re-hash |
| PR-10 | A global hooks folder in the user `.kiro` | None exists on 2026-11-24 (K-7) | n/a | n/a | n/a | Must be absent. If present, stop and review before trust. |
| PR-11 | Tools resolved from `PATH`: `uv`, `python`, `git`, `taskkill` (Windows) | Their own code | n/a | n/a | `uv`: none by design with `--offline` | ALLOW. The resolved paths are recorded. |

**Review record.** A new file `docs/next-phase/hooks/HOOK_SECURITY_REVIEW.md` (1.8) holds one row per surface with the reviewer, the date, the commit and the file hashes. The review binds to those hashes. A change to a reviewed file requires a new review of that surface.

**(C) Unknowns to measure.** Each unknown is determined by a legitimate observation and not by a synthetic one (DD3-11). These are the probes that D3.2 refers to.

| ID | Unknown | How it is determined | Recorded in |
|---|---|---|---|
| U-1 | Which saves fire `PostFileSave`: agent edit, editor save by the user, file creation, agent revert | One legitimate agent edit, one legitimate user save and one legitimate file creation, each observed with HK-0 | HK-0 records, KA-1 |
| U-2 | Matcher input: relative or absolute path, separators, drive letter case, canonical case | `path_as_received` in HK-0 records over edits in different folders | HK-0 records |
| U-3 | Matcher grammar and semantics: regex or glob, search or full match | Predicted firing from the reference function in HM-T2 against the observed firing of each hook, per save | A predicted-versus-observed table |
| U-4 | Stdin JSON keys for `PostFileSave` | `stdin_keys` in HK-0 records | HK-0 records |
| U-5 | Shell and `PATH` at hook time, and whether `uv` and `python` resolve | Resolved paths and `parent_chain` in the first records, and `--print-env-names` | The records |
| U-6 | Whether several matching hooks start together or in sequence | Overlap of `started_utc` and `ended_utc` across the records of one save | The records |
| U-7 | Kiro's own behavior at its timeout: does it kill the process tree | NOT_DETERMINED by design: no artificial timeout is provoked (DD3-11) | None |
| U-8 | What Kiro displays for a passing and a failing run, and where | KA-1 for one passing run and for the first naturally failing run | KA-1 |
| U-9 | The event names that Kiro logs for an execution | The KA-2 extract | KA-2 |
| U-10 | The trust prompt wording and scope, and whether a parent folder is offered | A screenshot of the prompt, and the trust list before and after | The session record |

Each unknown ends with a value or NOT_DETERMINED and a reason. An inconclusive probe never raises a hook status.

**(D) Procedure.** All steps are DESIGNED. The agent cannot grant trust or capture Kiro-side artifacts.

| ID | Who | Step | Stop if |
|---|---|---|---|
| S0 | Owner | Pick the commit to verify: a Phase_Branch commit that contains the implemented runner, matchers and tests and has D3-AC-1 to D3-AC-9 recorded SUCCEEDED. Without them only the existing hooks can be tested. | The runner and tests are not implemented |
| S1 | Owner | Record the Kiro IDE version from `product.json` (1.4.215 on 2026-11-24), the OS version and the shell. Confirm that the IDE is at least 1.0.242 (K-10). | The version is below 1.0.242 |
| S2 | Owner | Snapshot the user-level `.kiro` folder (names, sizes, SHA-256 of the files under `settings` and `agents`), confirm that it has no `hooks` folder, and record the Manage Workspace Trust list. | Unexpected entries |
| S3 | Owner | Create the clone outside the main repository: `git clone --no-hardlinks` from the main repository at the chosen commit, detached, into a folder whose path contains one space (Windows leg). Then remove the `origin` remote. | The remote is still present |
| S4 | Owner | Secrets check: the clone has no `.env` files, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `secrets` or `credentials` folders. The shell that starts Kiro has no `VK_VAULT_KEY` or cloud credentials (run `--print-env-names`). | Any hit |
| S5 | Owner | In a terminal (not a hook): `uv sync --frozen --all-packages --all-extras --group dev`, then `uv lock --check`, then `git status --short`, which must be empty. This is the only network step. | The status is not empty |
| S6 | Reviewer and owner | Complete the review table, record the hashes (T-H1), set `"disabled": true` for the MCP server in the clone and re-hash. | A hash mismatch |
| S7 | Owner | Manual preflight, labeled MANUAL: run every hook command with `--manual` in a terminal in the clone. Record the exit code, the duration, the resolved `uv` and `python`, and whether the environment allowlist works (RN-5). This is not hook execution. | A failure other than the BE-1 failure of HK-2 on Windows |
| S8 | Owner | Optional containment: an outbound-block rule for the clone's `python.exe` on Windows, a low-privilege user or a VM (OD-D3-7, OD-D3-8). | n/a |
| S9 | Owner | Open the clone in a NEW Kiro window. Before answering the trust prompt, read the Kiro log and record `hooks.reload.loaded` and `hooks.v2.executionDisabledUntrustedWorkspace` (expected while untrusted). That state is UNVERIFIED with that reason (8.11). Then trust this folder only, never a parent folder (8.16). The main repository stays untrusted. | Only a parent folder is offered |
| S10 | Owner | After trust, record the `hooks.reload.loaded` counts (8 registered expected), the absence of a new disabled event, and the Agent Hooks panel (screenshot). | The counts differ or the hooks are disabled |
| S11 | Agent and owner | Run the edit plan below in Supervised mode. The agent is told not to edit `.kiro`, `scripts/hooks` or `artifacts`. | A hook-file hash changes |
| S12 | Owner | After each edit: save KA-1 and KA-2, copy the new records, run `verify-chain`, and hash each artifact. | A chain break |
| S13 | Owner | At the end: compare the hashes of the hook files, the runner and `mcp.json`. Compare the user-level `.kiro` snapshot and the trust list. Export the agent's edits with `git format-patch` for review. Remove trust for the clone. | Any unexpected change |
| S14 | Owner and agent | Write the ledger entries (D3.7), the session record `docs/next-phase/hooks/HOOK_SESSION_RECORD.md` and the hook status table. Delete the clone only after the evidence is copied out (owner action, 14.13). | n/a |

**(E) Legitimate edits only (DD3-11, 8.15).** A hook fires on a real save, so every edit in the session is work that the repository needs.

| ID | Rule |
|---|---|
| LR-1 | Every trigger edit belongs to a tracked work item (a task once `tasks.md` exists, or an owner-approved fix written into the plan before the session) and would be acceptable in the repository history on its merits. |
| LR-2 | No-op edits are forbidden: an appended comment, a whitespace or line-ending change, `touch`, or a revert-and-redo cycle. |
| LR-3 | Budget: at most one trigger edit per matrix row that has a hook under test, plus one negative control and one editor save by the user, and at most 12 agent saves in the session as counted by HK-0. Going over the budget stops the session. |
| LR-4 | No instruction asks the agent to repeat an edit until a hook fires or passes N times. The target per hook is one AT-1 record. |
| LR-5 | Edits are made in the clone only. Patches return to the Phase_Branch after review as owner commits. A hook with no legitimate edit stays UNVERIFIED. There is no fallback to a synthetic edit. |

**Candidate plan.** The candidates are examples. The owner fixes the final plan in `docs/next-phase/hooks/HOOK_VERIFICATION_PLAN.md` before the session (OD-D3-11).

| ID | Edit | Candidate legitimate work | Expected hooks |
|---|---|---|---|
| TP-1 | Negative control, made by the agent | A real edit to a Markdown deliverable, for example the session record | None fire (HK-0 stays silent) |
| TP-2 | The agent edits `tests/contract/test_mcp_server.py` | The BE-1 remediation (D3.9). On Windows before the fix, HK-2 is expected to FAIL with the BE-1 signature, which is valid evidence for 8.13. After the fix it should pass. | HK-0, HK-2 |
| TP-3 | The agent edits a module under `core/src/verdictkit/api` | A tracked D2 implementation item, for example the response-header fix for G-6, made in the clone and exported as a patch | HK-0, HK-1, HK-2, HK-5, HK-6 (the five-hook case, which tests the serialization) |
| TP-4 | The agent edits a module under `apps/reel-autopsy/src` | A tracked fix in that app | HK-0, HK-1, HK-3 |
| TP-5 | The agent edits a module under `apps/quote-autopsy/src` | A tracked fix in that app | HK-0, HK-1, HK-4 |
| TP-6 | The agent edits `api/openapi.yaml` or a file in `api/examples` | Only if a D5 task needs it, because D2 edits no contract file (AM-10). Otherwise HK-5 is verified through its other scope or stays UNVERIFIED. | HK-0, HK-5 |
| TP-7 | The agent edits `tests/contract/test_hook_matchers.py` or the corpus | A real improvement to the matcher tests | HK-0, HK-2, HK-7 for the test file. HK-0, HK-7 for the corpus (matrix rows 11 and 17). |
| TP-8 | The maintainer saves a real edit by hand in a watched file | One real small fix. It answers U-1 for user saves. | Recorded as observed |
| TP-9 | The agent creates a new file in a watched folder | A real new file that the work needs, for example a new test. It answers whether creation fires `PostFileSave` (U-1). | Recorded as observed |

**(F) Linux leg and residual risks.** Firing inside Kiro on a Linux host is outside the environments of D0.3, so it is UNVERIFIED for the Linux host class. Linux CI (a Linux runner or a Linux_Docker_Host) runs the matcher, runner, lock, timeout, recursion and chain tests (D3-AC-1 to D3-AC-9), which do not need Kiro.

| ID | Residual risk |
|---|---|
| R-H1 | pytest runs agent-edited code with the user's rights, and no sandbox is known to confine it (T-H3, F-H13). |
| R-H2 | A hook-file edit may need no approval (K-9). The mitigation is hash checks, not prevention. |
| R-H3 | Test output enters the agent context. The mitigation is the cap and the label (RN-9). |
| R-H4 | The evidence file is forgeable by anyone with file access (DD3-10). |
| R-H5 | Outbound network is not blocked by default on Windows (OD-D3-7). |

### D3.9 BE-1 remediation and BE-2 coordination

**(A) BE-1 (13.11, 13.13, 1.18).** The failing line is line 30 of `tests/contract/test_mcp_server.py`: `assert oct(bundle.parent.stat().st_mode & 0o777) == "0o700"`. It guards the private directory that `mcp_server._workdir()` creates. The property is that the private working directory is accessible only to the current user and, on Windows, to the system accounts.

The Python documentation says that, since 3.12.4, `os.mkdir` with mode `0o700` applies an access list on Windows (F-H15, [os.mkdir](https://docs.python.org/3.12/library/os.html#os.mkdir)). That list grants the owner entry through OWNER RIGHTS ([CPython issue 128038](https://github.com/python/cpython/issues/128038)). From an elevated process the owner is the Administrators group ([CPython issue 157876](https://github.com/python/cpython/issues/157876)). The exact list on this host is UNVERIFIED until it is read. Content from the CPython documentation and issues was rephrased for compliance with licensing restrictions.

| ID | Element | Design | Why |
|---|---|---|---|
| BE1-1 | POSIX branch | The original assertion stays on the branch taken when `os.name` is `posix`, with the same abstract syntax tree as at `84df25c`. The indentation that the branch adds is not a change (TPR-H-1, D10.11 TR-5). It is not skipped, not marked `xfail` and not weakened. | 13.11, 2.11 |
| BE1-2 | Windows branch | In the same test, a helper reads the access list of the directory and asserts that the list is protected (no inherited entries), that every entry is an Allow entry, and that every trustee is the current user's SID, OWNER RIGHTS (S-1-3-4), SYSTEM (S-1-5-18) or Builtin Administrators (S-1-5-32-544). It also asserts that no entry exists for Everyone (S-1-1-0), Authenticated Users (S-1-5-11), Builtin Users (S-1-5-32-545) or any other SID. The test records whether the process is elevated. | The same property as POSIX 0700 (13.11) |
| BE1-3 | Reading the list | Preferred: `ctypes` calls to `advapi32` that return the security descriptor as a string with two-letter aliases (SY, BA, OW, WD, AU, BU). The aliases do not depend on the language of Windows. No new dependency. Alternatives are in OD-D3-3. | Locale-independent check (OD-D3-3) |
| BE1-4 | Where | The access-list reader is a Core production module (TPR-M-8, D10.11 TR-10), and the changed test calls that same function. `_workdir()` self-checks its directory with it (DD8-6). A helper that exists only under `tests/contract` is not accepted. | 13.11, 13.30 |
| BE1-5 | Preservation guard | A test parses `tests/contract/test_mcp_server.py` with `ast`. It compares `ast.dump` of the original comparison with the one at `84df25c`, asserts that it still exists on the POSIX branch, that the test has no `skip`, `skipif` or `xfail` mark, and that no early return, `pytest.skip` or branch bypasses the replay and explain assertions on Windows (D10.11 TR-5). It runs on both host classes. | Stops a later weakening (2.11) |
| BE1-6 | Negative controls | Windows: a temporary directory with an added allow entry for Everyone must make the helper fail. POSIX: a directory with mode `0o755` must fail the original expression. Both show that the checks can fail. | Non-vacuous checks |
| BE1-7 | Python version | The Windows leg records the exact Python version. A Python from 3.12.0 to 3.12.3 is expected to fail the access-list check. OD-D3-4 decides between declaring 3.12.4 as the minimum and an explicit access list in `_workdir()`. | F-H15 |
| BE1-8 | Closing evidence | The per-test listing (`-rA`) and the pytest exit code on Windows and on a Linux_Docker_Host from a full checkout, captured with the record form of the runner so that the exit code is the child's and not the exit code of a pipe (E-025a, E-025b). On Linux, `tests/` is in the image (D2.2 F-1), so the file can run there. | 13.13 |

**Record form.** `record <label> -- <argument list>` (D3.6) runs one reviewed command from a terminal. It takes the exit code of the child directly, so a pipe cannot replace it. It keeps the full child output in a file under `artifacts/hooks/out` (RN-12) and writes a D3.7 record with mode MANUAL_DECLARED, so the run is attributed MANUAL (AT-3). The owner copies the output file into the evidence folder before the retention rule of RN-12 removes it. The record shows what the command did. It is not evidence that a hook fired.

**Effect on hooks.**

- Until BE-1 closes, HK-2 on Windows is expected to fail with the BE-1 signature. The failure is reported unchanged (8.13). No hook deselects, ignores or loosens that test (D3-AC-4).
- After BE-1 closes, a failing HK-2 on Windows is a new regression (1.13).
- The Linux security guarantee is unchanged. The original assertion stays on the POSIX branch, so it runs on Linux in the image and in CI. The Linux per-test evidence for it stays indirect and UNVERIFIED until BE1-8 is met (D0.5).

**(B) BE-2 coordination with P7 (13.12, 13.13).** D3 gives P7 an interface only. The BE-2 root cause, the instrumentation and the fix belong to D8 (DD3-13).

| ID | Item | P2 (D3) provides or does | P7 (D8) owns |
|---|---|---|---|
| BE2-1 | Hook coverage | No hook runs `tests/ui/test_judge_preview.py` or `scripts/serve_judge_ui.py` until BE-2 closes with Windows and Linux evidence (13.13). D3 is then amended if a hook is wanted (OD-D3-9). | The decision to close BE-2. |
| BE2-2 | Evidence schema | The D3.7 record and the record form of the runner are available for timing and comparison runs: UTC timestamps, the direct exit code, hashes and host data. | The instrumentation fields (connect, send, first byte), the trials per host, the Windows and Linux comparison, the root cause and the fix (13.12). |
| BE2-3 | Capture discipline | The runner captures the pytest exit code directly and keeps the `-rA` listing. No pipe through `tail` (E-025a, E-025b). | Using it for BE-2 evidence. |
| BE2-4 | No timeout change | D3 changes no timeout in the test or the bridge. A longer timeout alone is not a fix (13.12). The closed-port delay on Windows stays a hypothesis (`BASELINE_REPORT.md` F2). | The diagnosis. |
| BE2-5 | Port configuration | None. The hard-coded port 65534 conflicts with 1.17. | How the port is configured. |
| BE2-6 | Linux comparison | The disposable clone procedure gives a full checkout on the Windows host. The Linux leg needs a Linux_Docker_Host or CI (owner action). | Running it and recording the result. |

### D3.10 Measurable acceptance criteria

All rows are UNVERIFIED. Environments: Windows host is the development host class. Linux CI is a Linux runner or a Linux_Docker_Host. Owner (Windows) is an owner-run Kiro session on the Windows host. No Linux Kiro session is planned (B-H3).

| ID | Criterion | Method | Pass threshold | Req | Environment |
|---|---|---|---|---|---|
| D3-AC-1 | Matcher corpus | HM-T1 | 100 percent of the corpus rows are classified as expected. Per hook: at least 2 positive paths per separator style, at least 2 negative paths, and at least 1 nested path, 1 path with spaces, 1 absolute Windows path and 1 absolute POSIX path. | 8.3, 8.4, 8.9 | Windows host, Linux CI |
| D3-AC-2 | Real-tree property | HM-T2 | 0 mismatches over every tracked file and the path forms PF-1 to PF-7. The uncovered `.py` files equal the allowlist (17 at commit `84df25c`). The counts in D3.4 are re-derived. | 8.1, 8.3, 8.4 | Windows host, Linux CI |
| D3-AC-3 | Lint, equivalence and sentinels | HM-T3, HM-T4 and `scripts/hooks/check_matchers.cjs` | 0 forbidden constructs. `search` equals `fullmatch` on every corpus row. The JavaScript result equals the Python result on every corpus row. Each old core, reel and quote matcher fails at least one backslash positive. | 8.3 | Python part: Windows host and Linux CI. JavaScript part: Linux CI and the Windows host with Node. |
| D3-AC-4 | Hook file and command form | HM-T5 | Each hook has trigger `PostFileSave`, a canonical command, none of the forbidden characters, an integer timeout from 1 to 600 that is at least the floor, a boolean `enabled` and no agent action. The arguments of HK-2 contain no `--deselect`, no `-k` and no `--ignore` of `test_mcp_server.py`. | 8.5, 8.8, 8.9, 8.12, 8.13 | Windows host, Linux CI |
| D3-AC-5 | Runner behavior | `tests/contract/test_hook_runner.py` | Timeout: the child is killed, no process survives, the exit code is 124 and a record exists, within the budget plus 5 s. Lock: 4 simultaneous runners never overlap and each ends with a record (PASSED, FAILED or BUSY_TIMEOUT), so none is lost. Crash: a killed lock holder lets the next runner start within 1 s. Recursion: exit 76 and no child. Output: a child that prints 1 MiB gives at most 10,000 characters and hashes over all bytes. Stdin absent, closed, over 64 KiB or not JSON: no hang beyond 3 s. A symlinked or junctioned state directory: exit 78. A canary variable named like a secret in the parent is absent in the child and is listed by name only. | 8.6, 8.10, 8.18 | Windows host, Linux CI |
| D3-AC-6 | Evidence integrity | `verify-chain` over at least 20 generated records, plus tamper tests | The chain verifies. Changing one byte, deleting a record or reordering records is detected at that record. All D3.7 fields are present. `started_utc` and `ended_utc` are ISO 8601 UTC with Z. `duration_s` is not negative and comes from a monotonic clock. | 3.8, 8.2 | Windows host, Linux CI |
| D3-AC-7 | Attribution rules | Table-driven tests of the classification, with synthetic inputs labeled as test data | AUTOMATIC_VERIFIED only when AT-1 (a) to (e) all hold. Any missing condition gives a lower value. `--manual` or a terminal stdin gives MANUAL. The runner writes no attribution field. | 3.6, 3.7, 8.15 | Windows host, Linux CI |
| D3-AC-8 | Read-only effect | `git status --porcelain` and the SHA-256 of all tracked files before and after each hook command run in the clone (preflight and automatic) | 0 tracked files change. Other changes are inside the DD3-4 allowlist. The runner source opens no socket, and its tests pass with the network disabled on Linux. | 8.8 | Windows host, Linux CI |
| D3-AC-9 | Timeout floor | At least 3 runs per hook per host class, cold and warm, with the exact command text | Each timeout is at least the longest recorded duration and at least 4 times the slowest warm run (ASSUMED rule), and is never 0. The runs and values are recorded in the Evidence_Ledger. | 8.5 | Windows host, Linux CI |
| D3-AC-10 | Disposable session integrity | Steps S1 to S13 | The Kiro version is recorded and is at least 1.0.242. The user-level `.kiro` folder has 0 new or changed entries and no `hooks` folder at start and at end. The hashes of the hook files, the runner and `mcp.json` are equal at start, after each edit and at end. The clone has 0 secret-pattern files and no remote. Trust was granted to the clone folder only. The trust state of the main workspace is unchanged. | 8.16, 8.17, 8.18 | Owner (Windows) |
| D3-AC-11 | Pre-trust review | The review record | One row for each of PR-1 to PR-11, each with a verdict and a reviewer. The MCP entry is disabled in the clone. The reviewed hashes equal the clone hashes. | 8.17 | Owner (Windows) |
| D3-AC-12 | Automatic execution | The edit plan | For each hook that has a legitimate trigger edit: at least 1 AT-1 record, with the Kiro artifact, the runner record hash, the file path, an ISO 8601 date, the exit code and an output of at most 10,000 characters. The negative control fires 0 hooks. Each hook has exactly 1 record per save (0 DUPLICATE_SUSPECT). A hook without evidence stays UNVERIFIED. | 8.1, 8.2, 8.14, 8.15, 3.6, 3.7 | Owner (Windows) |
| D3-AC-13 | Untrusted behavior | Step S9, before trust | The log shows the hooks registered and `hooks.v2.executionDisabledUntrustedWorkspace`. The ledger records UNVERIFIED with that reason. 0 runner records exist for the untrusted period. No hook is reported as failed or passing. | 8.11 | Owner (Windows) |
| D3-AC-14 | Probes | U-1 to U-10 | Each has a recorded value or NOT_DETERMINED with a reason. No hook status rises on an inconclusive probe. | 8.1, 8.3, 3.4 | Owner (Windows) |
| D3-AC-15 | Failure feedback | The first naturally failing run (HK-2 on Windows before BE-1 closes, or any real failure) | The Kiro artifact shows the failure text delivered in the session, with the exit code and a failure excerpt. Otherwise the row stays UNVERIFIED. | 8.6, 8.13 | Owner (Windows) |
| D3-AC-16 | Per-save cost | Wall time from the first `started_utc` to the last `ended_utc` of one save in the heaviest matrix row (row 2), over 3 saves | Recorded. If the median is over 60 s (ASSUMED), OD-D3-5 is reopened. | 8.1 | Owner (Windows) |
| D3-AC-17 | BE-1 | The changed test, the BE1-5 and BE1-6 tests, and the record form | The POSIX assertion (the same abstract syntax tree as at `84df25c`) is present and runs on Linux. The Windows check passes on the directory from `mcp_server._workdir()` and fails on a directory with an Everyone allow entry. The POSIX negative control fails the original expression for a `0o755` directory. A per-test listing and the exit codes exist for Windows and for a Linux_Docker_Host from a full checkout. | 13.11, 13.13, 8.13 | Windows host, Linux_Docker_Host |
| D3-AC-18 | BE-2 interface | Review with D8 | D8 accepts the D3.7 record schema and the record form. 0 hooks are attached to the judge-preview test. D3 changed 0 timeouts. | 13.12 | Design review |
| D3-AC-19 | Documentation labels | Document check | Each hook has a status from ST-1 to ST-5 per host class. The text says that hooks are a development guardrail that run on the file operations determined by U-1, and that runtime guarantees come from code and CI. Each hook without ST-5 is labeled UNVERIFIED. | 8.7, 3.4, 3.10 | Windows host, Linux CI |
| D3-AC-20 | Usage and evidence discipline | The Kiro usage record, the plan and a diff review | Hook-related credits come only from a Kiro usage record, otherwise NOT_AVAILABLE. At most 12 agent saves are counted by HK-0. 0 no-op edits. Hook counts are not reported as usage. A passing run prints at most 300 characters. | 16.2, 3.8, 8.15 | Owner (Windows) |

### D3.11 Requirement traceability

| D3 section | Requirements |
|---|---|
| D3.1 | 8.7, 3.4, 16.2 |
| D3.2 | 8.5, 8.8, 8.11, 8.12, 3.4 |
| D3.3 | 8.1, 8.5, 8.6, 8.8, 8.10, 8.12, 8.15 to 8.18, 3.6 to 3.8, 16.2 |
| D3.4 | 8.1, 8.4, 8.9, 8.14, 2.12 |
| D3.5 | 8.3, 8.4, 8.9 |
| D3.6 | 8.1, 8.2, 8.5, 8.6, 8.8, 8.10, 8.12, 8.18 |
| D3.7 | 8.2, 8.11, 8.14, 8.15, 3.5 to 3.8, 4.7, 16.2 |
| D3.8 | 8.11, 8.15 to 8.18, 2.4 |
| D3.9 | 8.13, 1.18, 1.13, 2.11, 13.11 to 13.13, 13.15 |
| D3.10 | 8.1 to 8.18 |

Each criterion of Requirement 8 maps to D3 elements and acceptance rows as follows.

| Criterion | D3 elements | Acceptance rows |
|---|---|---|
| 8.1 | The hook table, RN-2, RN-4, AT-1 | D3-AC-2, D3-AC-12, D3-AC-14, D3-AC-16 |
| 8.2 | The D3.7 record and the ledger entry | D3-AC-6, D3-AC-12 |
| 8.3 | R-M2, R-M3, PF-1 to PF-7 | D3-AC-1 to D3-AC-3, D3-AC-14 |
| 8.4 | HM-T1, HM-T2 | D3-AC-1, D3-AC-2 |
| 8.5 | DD3-8, D3.4 note (c) | D3-AC-4, D3-AC-9 |
| 8.6 | RN-8, RN-9 | D3-AC-5, D3-AC-15 |
| 8.7 | D3.1, ST-1 to ST-5 | D3-AC-19 |
| 8.8 | DD3-4, RN-12 | D3-AC-4, D3-AC-8 |
| 8.9 | HK-7 | D3-AC-1, D3-AC-4 |
| 8.10 | RN-7 | D3-AC-5 |
| 8.11 | D3.7, step S9 | D3-AC-13 |
| 8.12 | DD3-3 | D3-AC-4 |
| 8.13 | D3.9, HM-T5 | D3-AC-4, D3-AC-15, D3-AC-17 |
| 8.14 | HK-0, the marker line | D3-AC-12 |
| 8.15 | AT-1 to AT-4, the procedure | D3-AC-7, D3-AC-12, D3-AC-20 |
| 8.16 | S3, S9 | D3-AC-10 |
| 8.17 | PR-1 to PR-11 | D3-AC-10, D3-AC-11 |
| 8.18 | S4, RN-5 | D3-AC-5, D3-AC-10 |

Every D3 component maps to a requirement above, and none is unmapped (4.2).

**Requirement gaps found (`requirements.md` not edited).** They are proposed for D10 reconciliation and need maintainer approval before any requirements change.

| ID | Gap |
|---|---|
| G-7 | 8.8 asks for read-only verification commands, but test runners write caches. The literal reading cannot be met. DD3-4 proposes a definition. |
| G-8 | 8.1 and 8.7 say hooks fire on a Kiro agent save, and a conflicting wording exists (K-4). The wording may change after probe U-1. |
| G-9 | 8.2 requires fields "all captured from Kiro". What Kiro shows or logs for an execution is unknown (F-H12), so the criterion may be satisfiable only through the session display. |
| G-10 | 8.5 ties the timeout to the Baseline_Run duration, but the measured commands differ from the registered text and the core run was partial (F-H5). The wording should bind to the exact command text and a completed run. |
| G-11 | 8.6 "leave the saved file unchanged" is true by construction for `PostFileSave`, which cannot block or revert, so it is not a testable hook behavior. Propose a check that no hook changes tracked files (D3-AC-8). |
| G-12 | 8.16 does not require that trust is granted to the clone folder only, or that hook files stay unchanged during the session (K-9). Propose two criteria. |
| G-13 | 8.10 expects a timeout indication in the agent session, which depends on Kiro's behavior at its own timeout (U-7). The runner's deadline produces the indication (DD3-8). Propose wording that names the runner. |

### D3.12 Open decisions and blockers

| ID | Item | State | What resolves it |
|---|---|---|---|
| B-H1 | Kiro semantics: trigger, matcher, stdin keys, shell, concurrency, log vocabulary | UNVERIFIED | Probes U-1 to U-10. |
| B-H2 | Trust, clone creation, edits and evidence capture are owner actions. The agent cannot grant trust or save Kiro-side artifacts. | PENDING | Owner session (D3.8). |
| B-H3 | No Kiro session on Linux is planned | Linux firing UNVERIFIED | A Linux Kiro session, if the owner wants one. |
| B-H4 | BE-1 and BE-2 remediation | Open | D8, with the interface in D3.9. |
| B-H5 | Durations of the exact command texts | UNMEASURED | D3-AC-9. |
| B-H6 | The runner, matchers, tests and hook file changes are not implemented | DESIGNED only | Implementation tasks after approval. |
| B-H7 | The CI step for the matcher and runner tests needs a pull request to `master` | PENDING | Owner action (D0.9, 14.13). |

| ID | Decision needed | Options | Recommendation |
|---|---|---|---|
| OD-D3-1 | Matcher mode after U-2 | Tolerant prefix, or strict root-anchored | Tolerant until U-2 shows relative paths, then strict (R-M8). |
| OD-D3-2 | Runner location and language | Standard-library Python in `scripts/hooks`, a PowerShell and `sh` pair, or Node | Standard-library Python (DD3-2). |
| OD-D3-3 | How the Windows test reads the access list | `ctypes` on `advapi32`, `icacls /save`, or PowerShell `Get-Acl` | `ctypes` with SDDL aliases. `icacls /save` as the fallback. |
| OD-D3-4 | Minimum Python patch on Windows | Declare 3.12.4 or later, or an explicit access list in `_workdir()` | Declare 3.12.4 and let the test enforce it. Decide with D8. |
| OD-D3-5 | Per-save hooks or aggregation on `Stop` | Per save (8.1), or once per turn | Per save. Reopen if D3-AC-16 exceeds 60 s. Aggregation needs a change of 8.1. |
| OD-D3-6 | Case handling on Windows | Case-sensitive, or case-insensitive character-class roots | Case-sensitive until U-2 shows non-canonical case. |
| OD-D3-7 | Network containment of the clone | None, an outbound block for the clone's `python.exe`, or a VM | An outbound block (reversible). Owner decision. |
| OD-D3-8 | Account for the session | The current user, a separate low-privilege user, or a VM | A separate user or a VM if available. Owner decision. |
| OD-D3-9 | A hook for the judge preview after BE-2 | None, or a hook for `tests/ui` and `scripts/serve_judge_ui.py` | None by default. Revisit after D8. |
| OD-D3-10 | Curation of attribution | A manual join, or a read-only `curate` subcommand | Manual first. A script only if the join repeats. |
| OD-D3-11 | Where evidence summaries live | New files under `docs/next-phase/hooks/` | Yes (1.8): `HOOK_SECURITY_REVIEW.md`, `HOOK_VERIFICATION_PLAN.md`, `HOOK_SESSION_RECORD.md`. |

**Not done in this stage.**

- No hook was triggered.
- No workspace trust was enabled.
- No hook file or other file except this design was modified.
- No test was run for D3.
- No tasks were created.
- D4 to D10 are not written.
- Nothing was committed.

### D3.13 Maintainer decisions on open items (conditional approval)

The maintainer approved D3 conditionally. Each decision below is DECIDED and DESIGNED. None is implemented. No workspace was trusted, no hook was enabled or run, no test was run for D3 and no infrastructure was provisioned. Text in D3.1 to D3.12 is unchanged. Where a decision here differs from that text, this section governs. The statement "Nothing was committed" in D3.12 describes the authoring stage of D3 only.

| ID | Decision | Effect on D3 text |
|---|---|---|
| AM-D3-1 | Automatic hook verification (the owner session of D3.8, steps S9 to S14) runs only in a dedicated VM or under a restricted OS account, in addition to the disposable clone. A clone alone is not sufficient containment. A restricted account is a separate local non-administrator account that can read and write only its own profile, the clone folder and the installed tools, and holds no cloud, signing or `VK_VAULT_KEY` credential. A dedicated VM is used only for this session, shares no folder with the host and holds no stored credential. If neither exists, S9 to S14 are not run and no hook is promoted above ST-3. | OD-D3-8 is decided. S8 becomes required, and S5 to S8 run in the same VM or account so that the preflight describes the environment of the session (U-5, RN-5). T-H3 and R-H1 are restated: the clone limits what can be read, and the VM or account limits what pytest running agent-edited code can reach. New row D3-AC-21 (8.16, 8.18). |
| AM-D3-2 | The Windows check for BE-1 evaluates effective access and not only the listed entries. It asserts that (a) the access list is protected and no entry is inherited, (b) the effective access of the probe principals Everyone, Authenticated Users, Builtin Users and Builtin Guests is none, (c) a group trustee is accepted only if it is SYSTEM or Builtin Administrators, and (d) an error while enumerating group members fails the check. The current user's token groups and elevation state are recorded, so that access obtained through group membership is attributed. Results are reported by well-known alias and class, never as account names or SIDs of the user. | BE1-2 and BE1-3 gain these checks. Reading the access list as SDDL aliases (OD-D3-3) stays, and an effective-rights call is added (for example `GetEffectiveRightsFromAclW`, which counts rights granted through group membership and returns an error when it cannot enumerate a group; the choice is recorded under OD-D3-3). BE1-6 adds two negative controls: a directory with an inherited allow entry and a directory with an allow entry for Builtin Users. The POSIX assertion (BE1-1) is unchanged. New row D3-AC-22 (13.11). |
| AM-D3-3 | A busy, skipped, blocked or not-run hook never counts as successful validation. Only PASSED counts. BUSY_TIMEOUT, RECURSION_BLOCKED, CONFIG_ERROR, RUNNER_ERROR and TIMEOUT are NOT_VALIDATED, and so is a hook that Kiro did not run (untrusted workspace, disabled hook) or whose child command was not started. A save is validated only if every hook that the reference matcher (HM-T2) assigns to it has a PASSED record. A missing record is reported as NOT_VALIDATED and is never omitted. | RN-4, RN-7, RN-8 and the ledger mapping in D3.6 are unchanged and now carry this rule. None of these outcomes maps to SUCCEEDED, and a non-zero exit code stays visible to the agent (K-5). No document, marker or summary says validated, verified or passed for a save that has a NOT_VALIDATED hook. New row D3-AC-23 (8.1, 8.6, 8.11, 3.7). |
| AM-D3-4 | Per-save overhead is measured, and the same test file does not run more than once per save unless the record states why. For every matrix row 1 to 17 the record holds the wall time from the first `started_utc` to the last `ended_utc`, the duration of each hook, the lock wait and the number of times each test file runs, cold and warm, over at least 3 saves. Redundancy is reduced only by disjoint test sets or by a save-scoped selection that keeps each hook's own outcome. Result caching across saves and dropping or coalescing of saves stay rejected (DD3-7, 8.1). No `--deselect`, `-k` or `--ignore` of `test_mcp_server.py` is allowed (8.13). | Read from the D3.4 commands and not measured: in matrix row 2, `test_llm_fence.py` runs under HK-1 and HK-2, `test_api_schema.py` under HK-2 and HK-5, and `test_http_run_lifecycle.py` under HK-5 and HK-6. D3-AC-16 is extended from row 2 to every row. B-H5 stays UNMEASURED. OD-D3-5 is reopened if the median wall time of any row exceeds 60 s (ASSUMED). The mechanism is chosen at implementation. New row D3-AC-24 (8.1, 8.5). |
| AM-D3-5 | The recursion guard (`VK_HOOK_DEPTH`, RN-2) and the record hash chain (EV-10, `verify-chain`) are not security controls and not authenticity guarantees. The guard stops accidental loops only, because anyone who controls the environment can set or unset the variable. The chain detects accidental damage and reordering only, because it holds no secret and no signature, so anyone with write access to the file can recompute it. Documentation and runner output call them a loop guard and a consistency check, and never tamper-proof, secure, authentic or signed. | T-H7 and EV-10 are read as detection of accidental change. R-H4 and the two-key rule (DD3-10) stand. `verify-chain` reports consistent or the first break, and never authentic. D3 designs no signing of hook evidence. D3-AC-6 and D3-AC-19 gain a wording check. New row D3-AC-25 (3.8, 8.15). |
| AM-D3-6 | Every process that the runner starts gets its environment from a closed, explicit list of variable names (RN-5). The list works by name only: no pattern, and no rule that drops only secret-like names. A variable that is not on the list is dropped even if its name looks harmless. The secret-like name patterns are used only to report dropped names. The runner never writes the value of any variable to a record, to stdout or to stderr, except values that it sets itself. The runner and `uv` start with the Kiro environment, which the runner cannot restrict. The list does not restrict file access: `USERPROFILE`, `HOME`, `APPDATA` and `LOCALAPPDATA` point into a profile that can hold credential files, so AM-D3-1 is the control for that. | DD3-6 and RN-5 stand and gain these rules. Each entry of the list has a recorded reason. The list is part of the reviewed and hash-pinned files (T-H1, AM-D3-7). The canary test of D3-AC-5 adds a canary with a benign name. New row D3-AC-26 (8.18). |
| AM-D3-7 | A change to executable hook configuration voids the review of the changed surface, and a renewed review is required before the changed files are used for evidence. Executable hook configuration is every `.kiro/hooks/*.json` file (trigger, matcher, command, timeout, enabled, action type), `scripts/hooks/*`, `tests/contract/hook_matcher_corpus.json`, the environment allowlist (RN-5) and `.kiro/settings/mcp.json`. A new or removed hook file, a changed flag in a hook command and a changed `enabled` value are changes. The reviewer records the renewed review. The agent cannot record or waive it. | The rule in D3.8 (B) that a changed reviewed file requires a new review, and T-H1, become a check: HM-T5 compares the hashes of these files with the hashes in `HOOK_SECURITY_REVIEW.md`, and a mismatch fails with "renewed review required". Hashes are taken over LF-normalized bytes, because Windows checkouts convert line endings. While the check fails, the affected hooks stay at ST-1 and no AT-1 record counts (AT-1 (e)). Evidence from a session under the old hashes is not carried over. New row D3-AC-27 (8.17). |
| AM-D3-8 | The additional 94.1594 credits and 197 request identifiers reported by the maintainer are recorded in the Evidence_Ledger as separately observed usage evidence and not as a Credit_Record read by the agent. They are subject to deduplication by request identifier against the 318 identifiers of the Historical_Audit. The identifier values were not supplied, so deduplication is NOT_PERFORMED and no combined total is computed. The figures carry no session identifier or date, which are NOT_AVAILABLE. They are not attributed to a track or to hooks (16.3) and are kept apart from the Historical_Audit total (16.4). Usage of the current turn remains NOT_AVAILABLE (16.2). | New ledger entries U-001 to U-005 are recorded in `EXECUTION_EVIDENCE.md`. The existing row "Credits consumed in this phase" is unchanged. DD3-14 and the credits paragraph of D3.7 stand. No cost per hook, task or test is stated (16.5). D3-AC-20 applies (16.1 to 16.5). |

**Acceptance rows added by this amendment (all UNVERIFIED).**

| ID | Criterion | Method | Pass threshold | Req | Environment |
|---|---|---|---|---|---|
| D3-AC-21 | Session containment | Review of the session record for steps S5 to S14, and one probe read from inside the VM or account | The record names the type (VM or restricted account) and states by class that the account is not an administrator, can reach only its profile, the clone and the tools, and holds no cloud, signing or `VK_VAULT_KEY` credential. No account name, host name or SID is recorded. A probe read of the owner's profile fails. Without a VM or account, S9 to S14 have 0 records and each hook is reported at ST-3 at most. | 8.16, 8.18 | Owner (Windows) |
| D3-AC-22 | Windows access list, effective access | The BE-1 Windows helper (BE1-2, BE1-3) and its negative controls (BE1-6) | The directory from `mcp_server._workdir()` passes: protected access list, 0 inherited entries, no effective access for Everyone, Authenticated Users, Builtin Users and Builtin Guests, and only the current user, OWNER RIGHTS, SYSTEM and Builtin Administrators as trustees. Each negative control (Everyone entry, inherited allow entry, Builtin Users entry) fails the helper. An enumeration error fails the check. The output holds aliases and classes only. | 13.11, 13.13 | Windows host |
| D3-AC-23 | Busy and skipped never validate | A table-driven test over every outcome of D3.6, a check of the ledger mapping, and one multi-hook save in which one hook is held in BUSY_TIMEOUT by a held lock | 0 outcomes other than PASSED map to SUCCEEDED or count as validation. The save with a BUSY_TIMEOUT hook is reported NOT_VALIDATED. A hook that the reference matcher assigns to a save and that has no record is reported NOT_VALIDATED and is not omitted. | 8.1, 8.6, 8.11, 3.7 | Windows host, Linux CI |
| D3-AC-24 | Per-save overhead and redundancy | Wall time and the number of runs of each test file for every matrix row 1 to 17, cold and warm, over at least 3 saves per row (the Kiro-fired part in the owner session, the command part with the record form as MANUAL) | The values are recorded in the Evidence_Ledger. Each test file runs at most once per save, or the record states the reason. The set of unique tests that run for a row is the same before and after any de-duplication. The median wall time of each row is at most 60 s (ASSUMED), or OD-D3-5 is reopened. | 8.1, 8.5 | Owner (Windows), Windows host |
| D3-AC-25 | Guarantee wording | A text search over `docs/next-phase`, the runner source and its output strings, `verify-chain` output, and a test that rewrites one record and recomputes the later hashes | 0 uses of tamper-proof, secure, authentic or signed for the guard, the chain or the marker. `verify-chain` prints consistent or the first break. The rewritten file verifies as consistent, and the documentation states that limit. | 3.8, 8.15 | Windows host, Linux CI |
| D3-AC-26 | Closed environment allowlist | The canary test of D3-AC-5, extended | A canary variable with a benign name that is not on the list is absent in the child. A canary named like a secret is absent and is listed by name only. Every list entry has a recorded reason. 0 variable values appear in records, stdout or stderr other than values the runner set. The list hash equals the reviewed hash. | 8.18 | Windows host, Linux CI |
| D3-AC-27 | Renewed review trigger | The HM-T5 hash check on a temporary copy of the tree | A one-byte change in each pinned file, a new hook file, a removed hook file and a changed `enabled` value each fail with renewed review required. A Windows (CRLF) checkout and a Linux (LF) checkout give the same hashes. The unchanged tree passes. | 8.17 | Windows host, Linux CI |

## D4. P3 MCP interoperability and diagnostics

### D4.1 Scope and status

**Covers.** Requirement 9 (criteria 9.1 to 9.20): error signalling, size and read-only limits, diagnostics, schemas, the real-stdio client test, compatibility with existing clients and the verification of calls made from inside Kiro. It also covers the MCP side of invariants 2.3, 2.4 and 2.8.

**Does not cover.** Signing and signer trust (D5 owns the fields that 9.8 reports). The contract-version value (D5.8). The BE-1 edit to `tests/contract/test_mcp_server.py` (D3.9). The hash re-pin and renewed review of `.kiro/settings/mcp.json` (D3, AM-D3-7). Any transport other than stdio.

**Status.** Everything in D4 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. Facts marked OBSERVED come from a read-only stdio probe run while writing this design (Windows host, 2026-11-24, `mcp` 2.3.0). The probe is not an Execution_Record, so those facts are UNVERIFIED for Requirement 3 until a record exists. The notes are in `docs/next-phase/D4_D5_WORKING_NOTES.md`.

### D4.2 Inspected baseline and findings

Files read or searched at commit `c29d2fe`. `git diff --stat 84df25c c29d2fe` over `core`, `api`, `apps`, `tests`, `scripts`, `deploy`, `ui-kit`, `examples` and `.kiro/settings` is empty, so the code is the baseline code. Read: `core/src/verdictkit/mcp_server.py`, `tests/contract/test_mcp_server.py`, `.kiro/settings/mcp.json`, `core/pyproject.toml`, `uv.lock`, `pipeline.py`, `evidence/broker.py`, `examiner/client.py`, `bundle.py`, the `SchemaError` sites of both claim types, `docs/KIRO_USAGE.md`, `docs/TRACEABILITY.md`, the uses of `mcp_server` in `tests/integration/test_quote_b7_texas.py`, and the installed SDK files `server/mcpserver/{server.py,tools/base.py,utilities/func_metadata.py,exceptions.py}` and `client/{client.py,session.py}`.

| # | Finding | Requirement |
|---|---|---|
| F4-1 | Tool failures are plain dicts `{"error": "<string>"}` returned as normal results. OBSERVED: `replay_bundle` on a missing path gives `isError` false. | 9.13, 9.19 |
| F4-2 | SDK argument-validation failures do set `isError` true, but the text is the raw pydantic message, which includes `input_value=` (OBSERVED: a canary claim string was echoed) and a documentation URL. There is no structured object. An unknown tool name is echoed. | 9.3, 9.14, 2.3 |
| F4-3 | `SchemaError` is caught by `except Exception` and reported as `verification failed (SchemaError)`, so the field name is lost. | 9.14 |
| F4-4 | OBSERVED: `allow_refetch: "yes"` is accepted as true. Unknown extra arguments are ignored. A `claim` sent as a JSON string is parsed by the SDK before the tool runs. | 9.16, 9.6 |
| F4-5 | The version `"0.1.0"` and the contract version `"1.1.0"` are string literals. They equal the package metadata only by coincidence. | 9.2, 9.18 |
| F4-6 | `core/pyproject.toml` declares `mcp>=1.2`. The code imports `mcp.server.mcpserver`, which exists only in mcp 2.x (the 2.x `fastmcp` module raises `ModuleNotFoundError` on purpose). The lock holds 2.3.0. A fresh install can resolve to 1.x and fail at import. | 9.1 |
| F4-7 | `test_sdk_registers_exactly_the_four_tools` asserts exactly four tools. The tests assert only that the key `"error"` is present. `test_quote_b7_texas.py` asserts `"error" in result and "verdict" not in result` and calls the private `_registry` and `_workdir`. | 9.1, 9.13 |
| F4-8 | With `VK_MCP_READONLY=1`, `verify_claim` runs with `network=False`. The broker raises `EvidenceUnavailable`, `run_case` swallows it, and the findings become `INDETERMINATE` with reason `evidence_missing`. A verdict is returned, not an error. | 9.6, 9.19 |
| F4-9 | `autoApprove` is `list_claim_types` and `explain_verdict`. `explain_verdict` accepts any local path. "bundle not found" and "bundle exceeds 8 MiB" differ, which tells a caller that a large file exists. | 9.9 |
| F4-10 | `docs/KIRO_USAGE.md` records that no MCP call was made from inside Kiro in the B7 session. The historical export holds 23 Kiro MCP calls (E-101, historical, not counted for this Release_Candidate, 3.9). | 9.11, 9.12 |
| F4-11 | OBSERVED: the SDK writes one stderr line per rejected call with field names only. For an unexpected exception it calls `logger.exception`, which writes a traceback to stderr. Kiro shows server stderr in its MCP log. | 9.3, 9.5 |
| F4-12 | OBSERVED: `initialize` echoes protocol `2025-06-18`. `tools/list` returns four tools without annotations. The dict tools publish a permissive output schema. `list_claim_types` publishes `{"result": [...]}` and sends one content block per claim type. | 9.1 |

### D4.3 Compatibility with existing clients

**Frozen surface (DESIGNED).** A snapshot is captured from the unmodified server before the first D4 change and stored as test data (D4-AC-1). It holds the four tool names, the `inputSchema` of each tool, the top-level field names of each success result (`verify_claim`: `case_id`, `isolation_mode`, `verdict`, `bundle_path`; `replay_bundle`: `contractVersion`, `integrity`, `reproducibility`, `authenticity`, `notes`; `explain_verdict`: `integrity`, `headline`, `verdict_hash`, `summary`; `list_claim_types`: `type_id`, `schema_version`, `outcome_fields`) and the wire form of `list_claim_types`. The plain functions in `mcp_server.py` keep their names, parameters and return shapes, because the existing tests call them directly. Error signalling is applied where the tools are registered and by a small change to how the functions build the `error` value (D4.4).

| Change | Class | Effect on an existing client | Control |
|---|---|---|---|
| `isError` true for execution errors | Behaviour fix | A client that ignored `isError` and read `error` keeps working. A client that checks `isError` now sees failures. | D4-AC-3 |
| `error` becomes an object `{code, message, tool}` | Shape change, required by 9.3 | A client that treats `error` as a string breaks. The tests assert only that the key exists (F4-7). Documented in `docs/MCP_SERVER.md`. | D4-AC-2 |
| Argument errors lose the pydantic text | Behaviour fix | Messages change. Codes are stable. | D4-AC-4 |
| `serverInfo.version` read from package metadata | None today | Same value now. | D4-AC-5 |
| `contractVersion` value follows D5 (1.2.0) | Value change, field name kept | A client that pins `"1.1.0"` breaks. This is the one intended value change. | D5.8 lockstep check |
| Optional tool `server_diagnostics` | Additive | The default tool list stays exactly four. | D4-AC-1 |
| `allow_refetch` must be a JSON boolean, unknown arguments rejected | Stricter input (OD-D4-4) | A client that sends `"true"` or extra fields breaks. | D4-AC-11 |
| `mcp` bound changes to `>=2.3,<3` (OD-D4-5) | Dependency | Closes F4-6. | D4-AC-18 |

### D4.4 Execution-error model

**Rule E1 (DESIGNED).** A call is an execution error when the tool cannot produce its documented success object because of the input, a limit, the mode, the environment or an internal fault. A call is a result when the documented success object is produced, whatever it says. Every claim verdict (`CONSISTENT`, `SUPPORTED`, `CONDITIONAL`, `INDETERMINATE`, `CONTRADICTED`, `REFUTED`, `IMPOSSIBLE`, and `BLOCKED` where a claim type produces it) is a result. So are `DIVERGED` and `UNVERIFIABLE` for a bundle whose integrity is `VERIFIED`. `isError` is derived only from the presence of the `error` object. No code reads `headline`, `status` or `verdict` to decide it (9.19, D0.4).

**Error object (9.3).** `{"error": {"code", "message", "tool"}}`. `code` comes from the closed list below. `message` has at most 500 characters. `tool` is the registered tool name. `INTERNAL_ERROR` also carries `incidentId` (8 random hex characters), which also appears in the stderr receipt. `BUNDLE_INTEGRITY_FAILED` keeps the baseline `integrity` object at the top level, so a client that reads `result["integrity"]["status"]` still works. A failure leaves stored evidence and bundles unchanged. Nothing is written before validation succeeds.

| Code | When | Message source |
|---|---|---|
| `INVALID_ARGUMENT` | Wrong type, missing or unknown argument, `allow_refetch` not a boolean, empty or NUL-containing path | Fixed text plus the argument names |
| `UNKNOWN_TOOL` | The SDK reports an unknown tool | Fixed text, no echo of the name |
| `CLAIM_NOT_CANONICAL` | Claim is not an object, has floats, NaN or duplicate keys, or is not canonical | Fixed text |
| `CLAIM_INVALID` | `SchemaError`, or an unregistered claim type | The claim type's own message after the sanitizer (9.14). An unregistered claim type gets a fixed text. |
| `SIZE_LIMIT_EXCEEDED` | Claim over 262,144 bytes or bundle over 8,388,608 bytes | Fixed text with the cap, never the input size or path |
| `READ_ONLY_MODE` | `allow_refetch` true while `VK_MCP_READONLY=1` | Fixed text |
| `BUNDLE_NOT_FOUND` | Path is not a readable file. One message for missing and unreadable. | Fixed text |
| `BUNDLE_INTEGRITY_FAILED` | The file is not an intact bundle (not a zip, unsafe entries, hash or chain mismatch) | Fixed text |
| `ISOLATION_UNAVAILABLE` | Socket configured but not authenticated, or `VK_EVIDENCE_DIR` missing in socket mode | Fixed text |
| `INTERNAL_ERROR` | Any other exception | Fixed text plus `incidentId`. No exception class, no text. |

**Sanitizer (9.3, 9.14).** A `SchemaError` message passes only if it has at most 500 characters, no control character, no path-like token (drive letter, leading slash or backslash, `..`), and contains no leaf string value of the submitted claim. Otherwise the message is `claim validation failed` and the field is not named. A claim-type author rule backs this up: messages are built from fixed text and field names only. The canary test in D4-AC-4 enforces it for every registered claim type.

**Mechanism (DESIGNED).** `build_server` returns a subclass of `MCPServer` that overrides the public `call_tool`. It (1) checks the raw arguments before the SDK coerces them: unknown names, non-boolean `allow_refetch`, wrong types. Missing `arguments` means `{}`, so `list_claim_types` is unaffected by a client that drops empty objects. (2) It calls the SDK. (3) It converts `ToolError` into the error object, dropping the SDK text. (4) It returns `CallToolResult(is_error=True, structured_content=error_result, content=[canonical JSON text])` when the result holds an `error` object, and the unchanged dict otherwise, so success results stay identical on the wire. (5) It catches every other exception as `INTERNAL_ERROR` and never calls `logger.exception` or sets `exc_info`. The tools are registered through `functools.wraps` wrappers, so the published `inputSchema` is derived from the unchanged signatures. The override is used instead of the SDK middleware because the middleware API is marked provisional.

**Output schemas.** The dict tools publish a permissive object schema, so an error body validates. `list_claim_types` publishes a wrapped `result` array, so its error body would not validate in a client that validates `structuredContent` even when `isError` is true. The Python SDK client skips validation for `isError` results (read in `client.py`). The TypeScript client is UNVERIFIED (R-D4-1). The failure is visible either way.

**Tampered and malformed bundles (OD-D4-2).** Recommended: `explain_verdict` and `replay_bundle` return `BUNDLE_INTEGRITY_FAILED` with `isError` true whenever the integrity result is `FAILED`. A client that checks only `isError` then cannot treat a tampered bundle as replayed. `explain_verdict` already refuses in the baseline. The alternative keeps every `ReplayReport` a result, like `POST /replays`, and relies on the client to read `integrity.status`.

### D4.5 Inputs, schemas, limits and read-only mode

- **Documented schemas (9.10).** `docs/mcp/schemas/` holds the `tools/list` snapshot, one success schema and one error schema per tool, and the diagnostics schema (JSON Schema 2020-12). The error schema has `additionalProperties` false, the fields `code`, `message` and `tool` (plus `incidentId` for `INTERNAL_ERROR` only) and `error.code` limited to the list in D4.4. A test compares the files with the live `tools/list`, so drift fails. `jsonschema` is already a development dependency.
- **Size limits (9.7).** A claim is measured as the UTF-8 length of `json.dumps(claim, allow_nan=False)`. A bundle is measured by file size. A file of exactly the cap is accepted and one byte more is rejected. The checks run before any parsing. The zip limits of `bundle.py` (4,096 entries, 16 MiB per entry, 64 MiB uncompressed) stay.
- **Read-only mode (9.6).** F4-8 shows that the baseline refuses network acquisition by disabling it, and the verdict is returned. OD-D4-3 recommends keeping that: `allow_refetch` true gives `READ_ONLY_MODE`, and `verify_claim` returns its result with `INDETERMINATE` findings. A failure object for `verify_claim` would turn a legitimate `INDETERMINATE` into an error (9.19) and would contradict `test_readonly_refuses_refetch`. The refusal is checked by a socket guard (D4-AC-8).
- **Claim validation (9.16).** The server never turns a string into a boolean, never treats a missing list as empty and never fills a default. Claim validation stays exactly as the claim type defines it. The one pre-validation step the SDK performs, parsing a `claim` that arrives as a JSON string into an object, is kept for client compatibility. The parsed object then goes through the same validation as any object.
- **`autoApprove` (9.9).** Each tool has an effect class in a test fixture. `list_claim_types` and `explain_verdict` are NO_WRITE_NO_NETWORK. `replay_bundle` writes a private replay directory and uses the network only with `allow_refetch`. `verify_claim` writes a bundle and uses the network when not read-only. `server_diagnostics` is NO_WRITE and connects only to the configured Unix socket. `autoApprove` stays `list_claim_types` and `explain_verdict`. `server_diagnostics` is not added, so approval is requested for it. Tool annotations (`readOnlyHint`, `openWorldHint`) are published for clients and are never used as proof.
- **Path handling.** `path` is read, never written, never echoed. All path failures return one message (F4-9). The size check follows the existence check, so a large file is still distinguishable from a missing one. This is residual risk R-D4-3.

### D4.6 Diagnostics and privacy

**Tool `server_diagnostics` (9.2, 9.4, 9.5).** It takes no arguments. It is registered only when `VK_MCP_DIAGNOSTICS=1`, so the default `build_server()` still lists exactly four tools and `test_sdk_registers_exactly_the_four_tools` passes unmodified (OD-D4-1). The result has exactly these fields, with `additionalProperties` false:

| Field | Value |
|---|---|
| `serverVersion` | `importlib.metadata.version("verdictkit")`. If the metadata is missing the server exits with code 3 and writes `VK_MCP_STARTUP_ERROR=VERSION_UNAVAILABLE`. The same value goes into `serverInfo.version`. |
| `contractVersion` | The shared constant (D5.8). No literal remains in `mcp_server.py`. |
| `isolationMode` | `ENFORCED` only when the socket is configured, accepts a connection and passes the same owner check as `SocketExaminer(expected_peer_uid=...)`. Otherwise `UNENFORCED`. It is always `UNENFORCED` on Windows. |
| `readOnly` | Boolean for `VK_MCP_READONLY=1` |
| `examinerSocketConfigured` | Boolean |
| `examinerSocketReachable` | `true` only if a configured socket accepted a connection within 2 seconds. The probe connects, sends nothing and closes. `false` when not configured. |
| `evidenceDirValid` | Boolean, by the existing `_shared_evidence_dir` rule |

The tool writes no file and opens no connection except the Unix socket. The result never contains an environment value, the vault key or path, the socket path, a uid, or any path.

**Logging policy.** Stderr is the Kiro MCP log. The server writes one receipt line per call: `VKMCP v1 tool=<name> argsSha256=<16 hex> bytes=<n> outcome=ok|error code=<CODE|-> ms=<n> incident=<id|->`. The hash is the SHA-256 of the canonical JSON of the arguments. A log filter removes `exc_info` from records of the `mcp` logger. No argument value, path, exception text or traceback is logged. The tool name in a receipt is checked against the registry, so a client cannot inject text into the log.

### D4.7 stdio transport and the client test

**Harness (9.10, 9.17, 9.20).** The test starts `sys.executable -m verdictkit.mcp_server` as a real subprocess with an allowlisted environment (no host secrets). It uses the official SDK stdio client for the main cases and a raw JSON-RPC line client for framing cases. Each call has a 30 second limit, and a stall is a failure. The server must exit with code 0 within 5 seconds after stdin closes.

**Cases.** (1) `initialize`: `serverInfo.version` equals the metadata version, otherwise the test fails (9.18). (2) `tools/list` is the four names by default and five with `VK_MCP_DIAGNOSTICS=1`. (3) Each tool gets one valid and one invalid call, and every result is validated against the documented schema. (4) The negative paths of 9.20: invalid input, claim of 262,145 bytes, bundle of 8,388,609 bytes, read-only refusal, missing bundle and tampered bundle, each with the `isError` value that D4.4 defines. (5) A legitimate `INDETERMINATE`: the Texas finance claim with doc fee 499.00 under `VK_MCP_READONLY=1` returns `isError` false (the B7 record says `doc_fee_cap` is `INDETERMINATE`). (6) A finance claim with boolean fields and non-empty `addons`, `gov_fees` and `rebates` returns a `SUPPORTED` `tax_rate` finding (9.17). (7) Stdout hygiene: every stdout line is one JSON-RPC message, with no banner and no `print`. A non-ASCII statement (`§`, `—`) round-trips identically on Windows and Linux. (8) A garbage line and a `tools/call` without `arguments` leave the server answering later requests. The behaviour is recorded, not assumed.

**Client matrix.** Official Python SDK client: covered by this test. Raw JSON-RPC: covered. Kiro: D4.8. MCP Inspector, TypeScript SDK clients and Claude Desktop: UNVERIFIED, listed in the release notes as not tested. At least `2025-06-18` and the newest version that the SDK client offers are negotiated.

**Start-up.** The configured command is `uv run python -m verdictkit.mcp_server`. `uv run` can sync the environment before the server starts. The test measures time to the first `initialize` response with that exact command and fails above 30 seconds (9.10). The command is not changed by D4.

### D4.8 Verification of calls made from inside Kiro (9.11, 9.12)

This is owner-run (14.13). The agent records what the maintainer captured and cannot attest a call. It uses the disposable checkout of D3.8 (no credential or key in it, 8.18). Before the calls, the maintainer records the commit SHA, the LF-normalized SHA-256 of `.kiro/settings/mcp.json`, the Kiro version if shown, the Python and `uv` versions, the host and the date. The Kiro MCP panel must show `verdictkit` connected with its tools. A capture of the panel is kept.

| Call | Purpose | Expected |
|---|---|---|
| KM-1 `list_claim_types` | Server reachable. Arguments empty or dropped. | Success. The registered claim types (4 at design time) |
| KM-2 `verify_claim`, stub claim | Basic pass-through | Success, a bundle path |
| KM-3 `verify_claim`, finance claim with non-empty lists and booleans | The example given in the documentation | `tax_rate` `SUPPORTED` |
| KM-4 `verify_claim`, same claim with empty `addons`, `gov_fees` and `rebates` | Records the reported dropping of empty arrays (9.15) | Either success or `CLAIM_INVALID` naming the field. Both are recorded as observed. |
| KM-5 `replay_bundle` on the KM-2 bundle | Replay | `integrity` `VERIFIED` |
| KM-6 `explain_verdict` on the KM-2 bundle | Explanation | `NOT_ESTABLISHED` in the summary |
| KM-7 `replay_bundle`, missing path | Error signalling | `isError` true, `BUNDLE_NOT_FOUND` |
| KM-8 `server_diagnostics` (if enabled) | Diagnostics | Exact field set |

For each call the maintainer copies, from the Kiro tool-call display or export, the tool name, the arguments, the result and the date and time in ISO 8601. The capture file is stored under `docs/next-phase/kiro-mcp/` and its SHA-256 goes into the ledger row. Three hashes are recorded: the intended arguments, the arguments as captured from Kiro and the `argsSha256` of the server receipt in the Kiro MCP log. Captured and receipt hashes must be equal. A difference between intended and captured arguments is the observed dropping of arguments, and it is recorded as a finding.

**Outcome class.** SUCCEEDED requires, for every call, a matching tool name, equal captured and receipt hashes, a result that validates against the documented schema and the expected `isError`. FAILED applies if a call ran and any condition fails. UNVERIFIED applies if the tools are not exposed to the session, as in the B7 session, or if the calls were not made. The ledger then also records any stdio result and labels it "obtained outside Kiro" (9.12). Rows are added in the ledger numbering. The historical 23 calls stay historical (E-101).

**Documentation (9.15).** `docs/MCP_SERVER.md` states that the Kiro tool-call path was reported to drop empty arrays and empty objects. It names the affected `verify_claim` fields (finance `addons`, `gov_fees` and `rebates`) and gives a finance example with non-empty lists. It says "expected to pass through Kiro" until KM-3 is SUCCEEDED. The server does not accept the dropped form (9.16).

### D4.9 Threats and controls

| # | Threat | Control | Check |
|---|---|---|---|
| T-M1 | An injected agent reads arbitrary local files through an auto-approved tool | `explain_verdict` only parses bundles, never echoes content except verified bundle fields, one message for every path failure, size cap. Residual R-D4-3. | D4-AC-4, D4-AC-7 |
| T-M2 | Claimed figures or secrets leak through errors, stderr or diagnostics | Fixed messages, sanitizer, receipts without values, no `exc_info`, no env values | D4-AC-4, D4-AC-6 |
| T-M3 | A failure is read as success by an agent (fail-open) | `isError` and closed codes. Tampered bundles are errors (OD-D4-2). | D4-AC-3 |
| T-M4 | Refetch or network use in read-only mode | Strict boolean, `READ_ONLY_MODE`, socket guard | D4-AC-8, D4-AC-11 |
| T-M5 | A zip bomb through `path` | 8 MiB file cap and the existing entry, size and uncompressed limits | D4-AC-7 |
| T-M6 | `mcp.json` changed to run another command or auto-approve a write tool | HM-T5 hash check (AM-D3-7) and the `autoApprove` test | D4-AC-12 |
| T-M7 | Protocol corruption by output on stdout, or log injection | Hygiene test, receipt fields from a fixed charset | D4-AC-13 |
| T-M8 | SDK or dependency drift | Bound `>=2.3,<3`, snapshot test, `uv lock --check` | D4-AC-1, D4-AC-18 |

### D4.10 Acceptance criteria

All rows are UNVERIFIED until an Execution_Record exists. "Linux" means the container or CI host (the socket cases need Linux peer credentials).

| ID | Check | Method | Pass threshold | Req | Host |
|---|---|---|---|---|---|
| D4-AC-1 | Frozen surface | Compare `tools/list` and the success key sets with the baseline snapshot (default environment) | 4 tool names, 0 `inputSchema` differences, 0 key-set differences | 9.1 | Both |
| D4-AC-2 | Existing tests untouched | `git diff 84df25c -- tests/contract/test_mcp_server.py tests/integration/test_quote_b7_texas.py` | 0 changed lines except the BE-1 hunk of D3.9, whose AST guard BE1-5 passes. All existing MCP tests pass. | 9.1, 9.13 | Both |
| D4-AC-3 | Signalling | Stdio matrix: every execution error of D4.4, and every verdict headline | 100% of error cases have `isError` true, a code in the list, the right `tool` and a message of at most 500 characters. 0 verdict results have `isError` true. `INDETERMINATE` has `isError` false. | 9.3, 9.13, 9.19, 9.20 | Both |
| D4-AC-4 | No leakage | 20 canary injections (claim leaves, paths, argument names, env values) into every tool, plus a Hypothesis property on the sanitizer | 0 canary occurrences in text, `structuredContent` and stderr. 0 path-like tokens. Sanitizer output at most 500 characters. | 9.3, 9.5, 9.14, 2.3 | Both |
| D4-AC-5 | Version | Compare `serverInfo.version` with `importlib.metadata`. A double that reports another version must fail the same comparison. | Equal. The negative control fails. | 9.2, 9.18 | Both |
| D4-AC-6 | Diagnostics | Exact field set. Directory snapshots before and after. Connection guard. A reachable and a stalled socket. | Exact 7 fields, 0 files written, 0 non-Unix connections, `examinerSocketReachable` true within 2 s and false within 2.5 s for the stalled socket, 0 secrets | 9.4, 9.5 | Linux (socket cases), Windows (rest) |
| D4-AC-7 | Size limits | Boundary cases | 262,144 and 8,388,608 accepted. 262,145 and 8,388,609 give `SIZE_LIMIT_EXCEEDED`. | 9.7 | Both |
| D4-AC-8 | Read-only | Launcher that fails any non-Unix `connect` | `READ_ONLY_MODE` for refetch. `verify_claim` returns `INDETERMINATE` findings. 0 outbound connections. | 9.6 | Both |
| D4-AC-9 | `SchemaError` message | Remove or corrupt each required field of every registered claim type | `CLAIM_INVALID`, message names the field, 0 exception text, 0 paths, 0 input values | 9.14 | Both |
| D4-AC-10 | No relaxation | Mutations on the finance claim: string for a boolean, missing `addons`, `gov_fees` or `rebates` | 0 accepted. Each gives `CLAIM_INVALID`. | 9.16 | Both |
| D4-AC-11 | Strict arguments (if OD-D4-4 is accepted) | `allow_refetch` as `"yes"`, `"true"`, 1. An unknown argument. A tool call without `arguments`. | First two groups give `INVALID_ARGUMENT`. `list_claim_types` without `arguments` succeeds. | 9.16, 9.6 | Both |
| D4-AC-12 | `autoApprove` | Parse `.kiro/settings/mcp.json` against the effect table. Negative control on a copy that adds `verify_claim`. | Every entry is NO_WRITE_NO_NETWORK. The control fails. | 9.9 | Both |
| D4-AC-13 | stdio hygiene | Raw client over the full matrix | 0 non-protocol stdout lines. `§` and `—` identical on both hosts. Exit code 0 within 5 s of EOF. | 9.10 | Both |
| D4-AC-14 | Timeouts | A test double that stalls | Each call returns within 30 s. The stall is reported as a failure at 30 s. | 9.10 | Both |
| D4-AC-15 | Finance claim over stdio | Case (6) of D4.7 | `tax_rate` `SUPPORTED` | 9.17 | Both |
| D4-AC-16 | Kiro verification | Owner-run KM-1 to KM-8 | One ledger row per call with tool name, three hashes, result, ISO 8601 date and the "captured from Kiro" label. Outcome class by the rule in D4.8. | 9.11, 9.12 | Owner (Kiro) |
| D4-AC-17 | Documentation | A test extracts the finance example from `docs/MCP_SERVER.md` and runs it over stdio | `SUPPORTED`. The empty-array statement, the affected fields and the code list are present. | 9.15 | Both |
| D4-AC-18 | Dependency bound | Inspect `core/pyproject.toml` and the lock. Import `mcp.server.mcpserver`. | The specifier excludes 1.x and 3.x. The lock resolves inside it. | 9.1 | Both |
| D4-AC-19 | Signature fields (joint with D5) | `replay_bundle` and `explain_verdict` over stdio on a signed bundle | `signatureValidity` and `signerTrust` present as D5.3 defines | 9.8 | Both |

### D4.11 Open decisions, risks and traceability

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| OD-D4-1 | How `server_diagnostics` is exposed given the exact-four-tools test | Opt-in by `VK_MCP_DIAGNOSTICS=1`. Always on (needs an edit to a contract test that 9.13 forbids). A CLI mode instead of a tool (not a tool, so not 9.4). | Opt-in. The Kiro workspace enables it in `mcp.json`, which needs the renewed review of AM-D3-7. |
| OD-D4-2 | Tampered or malformed bundle: error or result | Error for both tools. Result for `replay_bundle`, error for `explain_verdict`. | Error for both (fail-closed, D4.4). |
| OD-D4-3 | Reading of 9.6 for `verify_claim` in read-only mode | Disabled network with a verdict. A failure object. | Disabled network with a verdict (F4-8, 9.19). |
| OD-D4-4 | Strict arguments | Reject unknown arguments and non-boolean `allow_refetch`. Keep the SDK behaviour. | Reject. Risk: a client that sends extras. |
| OD-D4-5 | `mcp` bound | `>=2.3,<3`. `>=2.3,<2.4`. | `>=2.3,<3`. Only 2.3.0 is exercised. The lowest bound is UNVERIFIED. |
| R-D4-1 | A strict TypeScript client may reject an error body for `list_claim_types` against its wrapped schema | UNVERIFIED. Failure stays visible. | Test when such a client is available. |
| R-D4-2 | Kiro behaviours (argument dropping, display of `structuredContent`, approval prompts) are unknown | UNVERIFIED until D4-AC-16 | Owner-run |
| R-D4-3 | `explain_verdict` is auto-approved, accepts any path and reveals whether a file over 8 MiB exists | Accepted residual. An opt-in bundle root is possible later. | Recorded for D8. |
| R-D4-4 | The provisional SDK middleware API is not used. `call_tool` is public, but a 2.x change could still affect it. | Snapshot test and bound | D4-AC-1, D4-AC-18 |

**Files for implementation (not changed now).** `core/src/verdictkit/mcp_server.py`; a dependency-free module for the contract-version constant (D5.8); `core/pyproject.toml`; `.kiro/settings/mcp.json` (environment flag, renewed review); new tests and schema snapshots; `docs/MCP_SERVER.md`; `docs/mcp/schemas/`; the Kiro capture folder.

**Traceability.** 9.1: D4.3, AC-1, AC-2, AC-18. 9.2: D4.6, AC-5. 9.3: D4.4, AC-3, AC-4. 9.4: D4.6, AC-6. 9.5: D4.6, AC-4, AC-6. 9.6: D4.5, AC-8. 9.7: D4.5, AC-7. 9.8: D4.3, AC-19 with D5. 9.9: D4.5, AC-12. 9.10: D4.7, AC-3, AC-13, AC-14. 9.11, 9.12: D4.8, AC-16. 9.13: D4.3, D4.4, AC-2, AC-3. 9.14: D4.4, AC-9. 9.15: D4.8, AC-17. 9.16: D4.5, AC-10, AC-11. 9.17: D4.7, AC-15. 9.18: D4.7, AC-5. 9.19: D4.4, AC-3. 9.20: D4.7, AC-3. Every criterion of Requirement 9 maps to at least one D4 section and one acceptance row.

### D4.12 Maintainer decisions on open items (conditional approval)

The maintainer approved D4 conditionally. Each decision below is DECIDED and DESIGNED. None is implemented and no test was run for D4. Text in D4.1 to D4.11 is unchanged. Where a decision here differs from that text, this section governs.

| ID | Decision | Effect on D4 text |
|---|---|---|
| AM-D4-1 | Diagnostics are opt-in and disabled by default. `server_diagnostics` is registered only when `VK_MCP_DIAGNOSTICS=1`. | OD-D4-1 decided as recommended. No change to `.kiro/settings/mcp.json` is made or implied. Setting the flag there is a separate change that needs the renewed review of AM-D3-7. |
| AM-D4-2 | The four existing default tools are preserved: names, `inputSchema`, success key sets and the wire form of `list_claim_types`. | D4.3, D4-AC-1 and D4-AC-2 stand. `test_sdk_registers_exactly_the_four_tools` passes unmodified. |
| AM-D4-3 | A tampered bundle (integrity `FAILED`) returns `isError` true with `BUNDLE_INTEGRITY_FAILED`, from `explain_verdict` and from `replay_bundle`. | OD-D4-2 decided as recommended. A malformed bundle stays an execution error under Rule E1. |
| AM-D4-4 | A legitimate verdict, including `INDETERMINATE`, is a successful result with `isError` false. | Rule E1 and D4-AC-3 stand. No code derives `isError` from `headline`, `status` or `verdict`. |
| AM-D4-5 | Arguments are validated strictly. An unknown argument, and an `allow_refetch` that is not a JSON boolean (`"yes"`, `"true"`, `1`), return `INVALID_ARGUMENT`. | OD-D4-4 decided: reject. D4-AC-11 no longer depends on "if OD-D4-4 is accepted". `docs/MCP_SERVER.md` states the stricter behaviour. Other argument handling in D4.5 is unchanged. |
| AM-D4-6 | The `mcp` dependency range is a tested 2.x range, and the lock file pins one exact version. A bound is claimed only if a recorded D4 run covers it. | OD-D4-5 decided differently from the recommendation. Only 2.3.0 is exercised, so the specifier is `>=2.3,<2.4`. It widens only after a recorded stdio run on the new upper version. The text `>=2.3,<3` in D4.3, T-M8 and D4-AC-18 is superseded. D4-AC-18 also requires `uv lock --check` to pass and the image build to use `uv sync --frozen`. |
| AM-D4-7 | Every error is structured and sanitised, and no sensitive input is echoed. | D4.4 and D4-AC-4 stand. The rule covers errors that the SDK raises before a tool runs: the D4 probe saw validation text that repeats `input_value`, and an unknown tool name echoed (working notes). The canaries of D4-AC-4 include those paths. |

**Not decided in this review.** OD-D4-3 (reading of 9.6 for `verify_claim` in read-only mode) and the risks R-D4-1 to R-D4-4 stay open with the recommendations of D4.11.

**Traceability.** AM-D4-1: 9.4, 9.1. AM-D4-2: 9.1, 9.13. AM-D4-3: 9.3, 9.19. AM-D4-4: 9.19, 9.20. AM-D4-5: 9.16, 9.6. AM-D4-6: 9.1. AM-D4-7: 9.3, 9.5, 9.14, 2.3.

### D4.13 Maintainer decision recorded with the D6 and D7 review (MCP bound)

The maintainer's D6 and D7 review also recorded this decision for D4. It is DECIDED and DESIGNED. Nothing is implemented and no test was run for D4. Text in D4.1 to D4.12 is unchanged. Where this decision differs from that text, this section governs.

| ID | Decision | Effect on D4 text |
|---|---|---|
| AM-D4-8 | The `mcp` dependency keeps the range `>=2.3,<2.4` with exactly one version pinned in `uv.lock` (`2.3.0` at design time). Confirms AM-D4-6. | D4.3's table row, T-M8 and the OD-D4-5 recommendation still read `>=2.3,<3`; that text is superseded. D4-AC-18 is amended: it now also requires the `core/pyproject.toml` specifier to equal the string above, `uv.lock` to hold exactly one `mcp` entry inside the range, the installed version to equal the locked version, `uv lock --check` to pass, and the image build to use `uv sync --frozen`. The range widens only after a recorded stdio client run on the new upper version. |

**Not decided in this review.** D4.11's open items and risks (OD-D4-3, R-D4-1 to R-D4-4) stay open with the recommendations of D4.11.

**Traceability.** AM-D4-8: 9.1, 9.22.

## D5. P4 Signed evidence bundles and signer trust

### D5.1 Scope and status

**Covers.** Requirement 10 (10.1 to 10.33): the signature envelope and signing protocol, creation of signed bundles, verification and replay, the Trust_Store, key provisioning, rotation and revocation, the four separate results, the single contract-version event that D2 handed to D5 (AM-10, OD-D2-3), the authenticity display rules that D1 left open (OD-7), adversarial tests and deterministic replay. It also supplies the fields that D4 reports through MCP (9.8).

**Does not cover.** Hardware or cloud key custody, trusted timestamps, transparency logs, signing individual evidence blobs, signing by the MCP server (OD-D5-4), and dual-version serving of two contract versions.

**Status.** Everything in D5 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. Facts marked OBSERVED come from a read-only probe of the locked `cryptography` 50.0.2 (OpenSSL 4.0.3) run while writing this design (Windows host, 2026-11-24). It is not an Execution_Record, so it is UNVERIFIED for Requirement 3 until a record exists. The evidence ledger entries U-001 to U-005 that D3 refers to exist in `docs/next-phase/EXECUTION_EVIDENCE.md` (lines 65 to 69). No ledger change is made for D5.

### D5.2 Inspected baseline and findings

Read at commit `c29d2fe` (code identical to `84df25c`): `core/src/verdictkit/bundle.py` (all), `canonical.py`, `mcp_server.py`, `cli.py` (replay), `api/server.py` (metadata and replay handlers), `api/run_service.py` (bundle write), `api/openapi.yaml` (authenticity, integrity, replay and health schemas), `docs/API_CONTRACT.md`, `core/pyproject.toml`, `uv.lock`, `tests/contract/test_bundle_replay.py`, `tests/integration/test_bundle_evidence_and_golden.py` and the D1, D2 and D3 contract notes.

| # | Finding | Requirement |
|---|---|---|
| F5-1 | No signing code exists. `bundle.py` holds the constant `AUTHENTICITY` with status `NOT_ESTABLISHED`. `cryptography` is declared `>=43`, locked at 50.0.2, so Ed25519 needs no new dependency. | 10.3 |
| F5-2 | The manifest has `engine_version`, `env_fingerprint`, `isolation_mode`, `data_mode`, `case_id`, `verdict_hash`, `files` (SHA-256 of every other member) and `written_at`. It has no format version. Signing the manifest bytes therefore binds every listed member. Container-level bytes (zip timestamps, attributes, comments, extra fields, compressed form, bytes before or after the archive) are not covered by anything. | 10.1, 10.29 |
| F5-3 | `_integrity` treats `names - listed - {"manifest.json"}` as a failure, so any new member fails integrity today. `_check_zip_safety` rejects duplicate names, `..`, backslashes, directories, a leading slash and more than 4,096 entries, but it tests `ZipInfo.filename`, which Python has already sanitised: truncated at a NUL byte and, on Windows, with `\` rewritten to `/`. `orig_filename` keeps the raw name. OBSERVED on Windows (Python 3.12.10): a member stored as `signature\envelope.json` reports `filename` `signature/envelope.json`, so the backslash test cannot fire there while it fires on Linux, and a raw name made of the envelope name, a NUL byte and more text reports the plain envelope name on both hosts. The same archive can pass on one host and fail on the other. | 10.30, 10.31, 2.2 |
| F5-4 | `write_bundle` is called by `cli.py`, `mcp_server.py` and `api/run_service.py`. `verify_bundle_integrity` is called by `api/server.py` (metadata) and `mcp_server.py` (explain). `replay_report_dict` serves the API, the CLI and MCP. The API metadata and the CLI print `NOT_ESTABLISHED` from a constant or a literal string. | 10.20, 9.8 |
| F5-5 | OpenAPI `AuthenticityReport` has `status` as the constant `NOT_ESTABLISHED` and `additionalProperties` false. `ui-kit/src/types.ts` mirrors the literal. `docs/API_CONTRACT.md`: any schema change requires a version bump, and the frontend refuses unknown versions. | 10.21 |
| F5-6 | OBSERVED: Ed25519 signing is deterministic (two signatures of one message are identical, 64 bytes). A signature with `S+L` is rejected. Small-order public keys (the identity point and 32 zero bytes) load, and a universal signature (R = identity, S = 0) VERIFIES for any message. An RSA PEM loads as an RSA key. An encrypted PEM without a password raises `TypeError`. | 10.2, 10.24, 10.30 |
| F5-7 | The value `1.1.0` is pinned in `api/openapi.yaml` (twice), `api/server.py` (`VERSION`), `api/presenter.py` (`CONTRACT_VERSION`), `mcp_server.py`, 10 of the 13 files in `api/examples/`, `ui-kit/src/api.ts` (line 11) and `ui-kit/src/api.test.ts`, `ui/judge/app.js` and `ui/judge/index.html`, `docs/API_CONTRACT.md` and tests such as `tests/api/test_m3b_http_drafts.py`. `RELEASE_READINESS.md`, `SUBMISSION_*.md` and `README.md` state 1.1.0 for the frozen release and are not edited (1.2, 1.8). | 10.21 |
| F5-8 | `examples/stub_claimtype/golden.vkb` is a committed, unsigned bundle that already replays in CI. It is the compatibility fixture. | 10.32 |

### D5.3 Separate results and the authenticity rule

| Result | Values | Says | Does not say |
|---|---|---|---|
| `integrity` (unchanged) | `VERIFIED`, `FAILED` | Members match the manifest, ledger chain, commitment and spec hash | Who wrote it |
| `reproducibility` (unchanged) | `REPRODUCED`, `REPRODUCED_ACROSS_ENV`, `DIVERGED`, `UNVERIFIABLE`, `NOT_RUN` | Re-execution gives the same verdict hash | That the verdict is correct about the world |
| `signatureValidity` | `UNSIGNED`, `VALID`, `INVALID`, `UNSUPPORTED_ALGORITHM` | The holder of key K signed these exact manifest bytes under this protocol | That K is trusted, or that the claim is true |
| `signerTrust` | `NOT_EVALUATED`, `TRUSTED`, `UNTRUSTED_SIGNER` | This operator's Trust_Store accepts K at the evaluation time | That K was not compromised |
| `authenticity` | `NOT_ESTABLISHED`, `ESTABLISHED` | `VALID` and `TRUSTED` and integrity `VERIFIED` all hold | That the verdict is correct (10.33) |

**Derivation (pure).** `signerTrust` is computed only when `signatureValidity` is `VALID` and the Trust_Store loaded. Otherwise it is `NOT_EVALUATED`. `authenticity` is `ESTABLISHED` for exactly one combination: `VALID`, `TRUSTED`, integrity `VERIFIED`. Every other combination, including every unsigned bundle, is `NOT_ESTABLISHED`. "Verdict correctness" is not a field. It stays visible as `reproducibility`, and the `note` of every `ESTABLISHED` result carries the 10.23 disclaimer.

**Reason codes (closed list, sorted in the output).** Validity: `NO_ENVELOPE`, `ARCHIVE_UNREADABLE`, `DUPLICATE_ARCHIVE_PATH`, `UNKNOWN_SIGNATURE_MEMBER`, `ENVELOPE_LISTED_IN_MANIFEST`, `ENVELOPE_TOO_LARGE`, `ENVELOPE_MALFORMED`, `ENVELOPE_NON_CANONICAL`, `ALGORITHM_UNSUPPORTED`, `PROTOCOL_UNSUPPORTED`, `BUNDLE_FORMAT_UNSUPPORTED`, `KEY_ID_MISMATCH`, `PUBLIC_KEY_SMALL_ORDER`, `SIGNATURE_MALFORMED`, `MANIFEST_HASH_MISMATCH`, `SIGNATURE_MISMATCH`. Trust: `TRUST_STORE_NOT_CONFIGURED`, `TRUST_STORE_UNREADABLE`, `TRUST_STORE_INVALID`, `TRUST_STORE_UNSUPPORTED_VERSION`, `TRUST_STORE_HASH_MISMATCH`, `KEY_NOT_IN_TRUST_STORE`, `KEY_REVOKED`, `KEY_ROTATED`, `KEY_NOT_YET_VALID`, `KEY_EXPIRED`. Authenticity: `INTEGRITY_NOT_VERIFIED`. Notes are fixed strings chosen by the tuple of results. They never hold input text.

**Display rules (answers D1 OD-7).** `VALID` pass, check. `INVALID` fail, cross. `UNSIGNED` neutral, dash. `UNSUPPORTED_ALGORITHM` warn, triangle. `TRUSTED` pass. `UNTRUSTED_SIGNER` fail when the reason is `KEY_REVOKED`, `KEY_EXPIRED` or `KEY_NOT_YET_VALID`, otherwise warn. `NOT_EVALUATED` neutral, dash. `ESTABLISHED` pass, check, with the label text "ESTABLISHED" and the note. `NOT_ESTABLISHED` stays neutral-warn. Each result is its own badge with its own label. The signer fingerprint (the `keyId`) is shown when the signature is `VALID` (10.20). An unknown value renders `UNRECOGNISED` (DD-5). No text calls an unsigned bundle authenticated, signed, verified or trusted (10.32).

### D5.4 Envelope and signing protocol

One new archive member, `signature/envelope.json`, is the only name exempt from the unlisted-member rule (10.31). It is never listed in the manifest (OD-D5-2 explains why there is one member).

| Envelope field | Value |
|---|---|
| `alg` | `ed25519` (exact, lowercase) |
| `bundle_format` | `vkb/1`: the layout in `docs/ARCHITECTURE.md` section 7 at `84df25c`. It is a constant of the protocol, not a manifest field, because the manifest of an unsigned bundle must not change (10.5). |
| `key_id` | SHA-256 of the 32 raw public-key bytes, lowercase hex. This value is also the signer fingerprint. There is one definition (10.26). |
| `manifest_sha256` | SHA-256 of the exact bytes of `manifest.json` |
| `protocol`, `protocol_version` | `vk-bundle-sig`, `1` |
| `public_key` | 32 raw bytes as 64 lowercase hex characters. Not signed directly. It is bound through `key_id`. |
| `signature` | 64 bytes as 128 lowercase hex characters |

The envelope is canonical JSON (`canonical_bytes`) with exactly these eight keys and at most 2,048 bytes. **Signing input** (10.29): the ASCII tag `VerdictKit bundle signature v1`, one NUL byte, then `canonical_bytes` of an object that holds the six signed fields (`alg`, `bundle_format`, `key_id`, `manifest_sha256`, `protocol`, `protocol_version`). Canonical JSON is unique for an object, so the encoding is injective. The tag separates this use of the key from any other. Ed25519 signs the message directly. Signing is deterministic (F5-6), so the same case, clock and key give identical bundle bytes (10.7). The verdict hash does not read the signature member (10.6).

**What the signature covers.** The manifest bytes, and through its `files` map every other member. It does not cover container bytes (F5-2). The `.vkb` file hash that the API shows stays a separate fact, and consumers must treat the verified member bytes as the signed object.

### D5.5 Creating signed bundles and provisioning keys

- **Signing is enabled** when `VK_SIGNING_KEY_FILE` is set in the environment of a Custodian entry point (`verdictkit run` and the API run service). Unset means unsigned, with the code path of `84df25c`. **Set but unusable is an error, never an unsigned bundle** (no silent downgrade).
- **Key source (10.2, 10.25).** The variable holds a path, never key bytes, so the key stays out of process listings and the environment dump. The file is an unencrypted PKCS#8 PEM Ed25519 key of at most 4,096 bytes. It must be a regular file and not a symlink. On POSIX it must have no group or other permission bits. On Windows no permission check is made, which is R-D5-1. Anything that loads as another key type, an encrypted key, an empty file or a directory is refused. The code never generates, stores, logs or commits a production key. Tests generate throwaway keys in a temporary directory.
- **Errors (10.2).** `SIGNING_KEY_MISSING`, `SIGNING_KEY_UNREADABLE`, `SIGNING_KEY_UNSUPPORTED`, `SIGNING_KEY_PERMISSIONS`. The message is a fixed text. It never holds key bytes, exception text or, in the API and MCP, a path.
- **Order of work.** The key is loaded and checked before the ledger entry `BUNDLE_WRITTEN` is appended and before any file is created. The signature is built in memory after the manifest bytes exist. A failure leaves no `.vkb`, no `.tmp` and no ledger change. In the API run service the run fails with a fixed code and no unsigned bundle is stored.
- **Start-up.** A judge-mode or public start with `VK_SIGNING_KEY_FILE` set and unusable stops with exit 2 and `VK_STARTUP_ERROR=CONFIG_INVALID:VK_SIGNING_KEY_FILE`, like the existing pattern.
- **Custodian only (10.18).** The container entrypoint passes `VK_SIGNING_KEY_FILE` to the custodian environment only. The examiner environment allowlist (D0.7, `as_examiner` in `deploy/entrypoint.sh`) does not contain it, and only `as_custodian` gains `VK_SIGNING_KEY_FILE` and `VK_TRUST_STORE_FILE`. The key file belongs to `vk-custodian` with mode 0600, so the examiner uid cannot read it (container gate). The MCP server does not sign (OD-D5-4), because it examines in the same process and because `.kiro/settings/mcp.json` is committed and hash-pinned.
- **Isolation.** The manifest already records `isolation_mode`, so a signature from an `UNENFORCED` run shows that fact. The CLI prints a warning when it signs with `UNENFORCED` (OD-D5-9).

### D5.6 Verification and replay

Verification is offline and a pure function of the member bytes, the Trust_Store bytes and an evaluation time `as_of` that the caller passes from its clock (10.19). It reads only `manifest.json`, the envelope and the list of member names, and it is independent of the integrity checks. Steps, in order, each stopping at its result:

1. **Archive.** The existing hardened reader, with every name test applied to the raw name (`orig_filename`) so that the result is the same on Windows and Linux. A raw name that contains NUL or `\`, starts with `/`, or has an empty, `.` or `..` segment makes the archive unsafe. A duplicate is judged on both the raw and the sanitised name. A structural failure gives `INVALID` (`ARCHIVE_UNREADABLE` or `DUPLICATE_ARCHIVE_PATH`) when the raw or sanitised form of any name falls in the reserved namespace, otherwise `UNSIGNED`. Integrity is `FAILED` in both cases. This tightens reading on Windows only. No baseline bundle is affected, because `write_bundle` emits fixed names, and `golden.vkb` with D5-AC-1 checks it.
2. **Reserved namespace.** Any name whose NFKC, case-folded form starts with `signature`, other than the exact envelope name, gives `INVALID` (`UNKNOWN_SIGNATURE_MEMBER`). This is detection, not exemption. A manifest that lists the envelope name or any reserved name gives `INVALID` (`ENVELOPE_LISTED_IN_MANIFEST`).
3. **No envelope.** `UNSIGNED`, `NO_ENVELOPE`.
4. **Envelope shape.** Size at most 2,048 bytes. `parse_canonical`. Exactly the eight keys with string values. Hex fields match `^[0-9a-f]{64}$` or `^[0-9a-f]{128}$`. Violations give `INVALID`. Then `alg` must equal `ed25519`, `protocol` and `protocol_version` must equal `vk-bundle-sig` and `1`, and `bundle_format` must equal `vkb/1`. A mismatch gives `UNSUPPORTED_ALGORITHM` with the matching reason (OD-D5-7). There is no fallback to another algorithm.
5. **Key binding.** SHA-256 of the embedded key equals `key_id`. The key is not on the small-order list (the eight small-order points and their non-canonical encodings, which F5-6 shows the library will not reject). Violations give `INVALID`.
6. **Manifest binding.** `manifest_sha256` equals the SHA-256 of the member bytes (constant-time compare).
7. **Math.** Ed25519 verify over the signing input. Failure gives `INVALID` (`SIGNATURE_MISMATCH`). Success gives `VALID`.
8. **Trust** (D5.7), then the derivation of D5.3.

**Integration with `bundle.py`.** The unlisted-member test becomes `names - listed - {"manifest.json", SIGNATURE_MEMBER}` where `SIGNATURE_MEMBER` is the one exact string. `IntegrityResult` and `ReplayReport` keep their fields. Signature data travels in a new result next to them, so existing constructors and tests are unaffected. A signature that is `INVALID` does not stop a replay whose integrity is `VERIFIED`. An integrity failure still stops re-execution, as in the baseline, and the signature result is still reported. All three consumers (API replay, API metadata, CLI and MCP) call one `authenticity_dict(...)`, which replaces the constant and the CLI literal.

**Report shape (camelCase, contract 1.2.0).** `authenticity`: `status`, `note`, `signatureValidity`, `signerTrust`, `reasonCodes` (sorted array), `signer` (`{keyId, algorithm}` when `VALID`, otherwise `null`) and `trustStore` (`{formatVersion, serial, sha256, evaluatedAt}` when a store was read successfully and the signature is `VALID`, otherwise `null`). A report for an unsigned bundle holds no timestamp, so it is byte-stable. The existing `status` and `note` fields stay, so every existing field is preserved (10.21). The MCP `explain_verdict` summary line is generated from this object. For an unsigned bundle it still contains `NOT_ESTABLISHED`, so the existing assertion holds.

### D5.7 Trust_Store, rotation and revocation

- **Location (10.16).** `VK_TRUST_STORE_FILE`, or `--trust-store` on the CLI. An optional `VK_TRUST_STORE_SHA256` pins the file. **No API parameter, MCP argument, bundle member or evidence item selects or changes the store.** An embedded public key is never trusted by itself.
- **Format (10.27).** UTF-8 JSON, at most 262,144 bytes, no BOM, duplicate keys and floats rejected, closed schema. `{"format":"vk-trust-store","format_version":1,"serial":<integer at least 1>,"keys":[{"key_id","public_key","status","not_before","not_after","note"?}]}` with at most 1,024 keys. `status` is `ACTIVE`, `ROTATED` or `REVOKED`. The times are `YYYY-MM-DDTHH:MM:SSZ` with `not_before` earlier than `not_after`. At load, `key_id` must equal the SHA-256 of `public_key`, a `key_id` may appear once, and small-order keys are refused. An unknown field, an unknown status or an unknown `format_version` makes the whole store unusable. The file is read at each verification, so a change takes effect without a restart.
- **Evaluation (10.10 to 10.13, 10.28).** No store: `NOT_EVALUATED`, `TRUST_STORE_NOT_CONFIGURED`. A store that cannot be read, parsed or validated, or whose hash differs from the pin: `NOT_EVALUATED` with the matching reason, never `TRUSTED`, and the validity and integrity results stay as computed (10.17). Entry found by `key_id`: `REVOKED` gives `UNTRUSTED_SIGNER` and `KEY_REVOKED` at any time. Otherwise the interval `[not_before, not_after]` (both inclusive) is checked against `as_of`: outside gives `UNTRUSTED_SIGNER` with `KEY_NOT_YET_VALID` or `KEY_EXPIRED`. `ACTIVE` inside the interval gives `TRUSTED`. `ROTATED` inside the interval gives `TRUSTED` with `KEY_ROTATED`. No entry gives `UNTRUSTED_SIGNER` with `KEY_NOT_IN_TRUST_STORE`.
- **Which time (OD-D5-3).** `as_of` is the verifier's clock. The manifest's `written_at` is chosen by the signer, so a holder of an expired or revoked key could back-date it. Verifier time means a bundle signed legitimately stays `TRUSTED` only while the operator keeps the key inside its interval.
- **Rotation.** The operator adds the new key as `ACTIVE`, raises `serial`, distributes the file, then marks the old key `ROTATED`. Both stay trusted inside their intervals. A rotated key used after the rotation cannot be told from an earlier use without a trusted timestamp (R-D5-2). A key that may be compromised is marked `REVOKED`, never `ROTATED`.
- **Revocation.** There is no online revocation (10.19). Revocation is a new store file with a higher `serial`. Every report shows the store `serial` and `sha256`, so an audit can see which store decided. Operators should pin the hash in deployment configuration. A stale store is R-D5-3.

### D5.8 Contract, versioning and compatibility (resolves OD-D2-3, AM-10, OD-7)

**Decision (OD-D5-1).** One minor event, **contract 1.2.0**, joint for the P4 fields and every contract-visible D2 change, in line with the rule of `docs/API_CONTRACT.md` (any schema change bumps the version) and with 10.21 (every existing field preserved). OD-D2-3 is decided: the owner cookie is documented and joins this event, because the info text "Judge mode requires no authentication" would otherwise stay false.

| # | Change | Compatibility | Where |
|---|---|---|---|
| 1 | `AuthenticityReport`: `status` becomes `NOT_ESTABLISHED` or `ESTABLISHED`. New required fields `signatureValidity`, `signerTrust`, `reasonCodes`, `signer`, `trustStore` | Additive on the wire for tolerant clients. Breaking for strict 1.1.0 validators (`additionalProperties` false). | `BundleMetadata`, `ReplayReport` |
| 2 | `Health`: `commitSha` (40 lowercase hex or `unknown`), `status` becomes `ok` or `unavailable`, and a 503 response with the same key set | Breaking for strict validators (D2 AM-10 rows 2 and 3) | `/health` |
| 3 | Owner cookie `vk_owner` as a documented cookie scheme, plus the rule that a mismatch is the same 404 | Behaviour change in the public profile only (AM-10 row 1) | `components.securitySchemes`, info text |
| 4 | 429 `RATE_LIMITED` with `Retry-After` on runs, replays, cases and events routes | Schema-compatible (AM-10 row 5) | the route responses |
| 5 | Contract header on every response (G-6) | Compatible, no schema change | `api/server.py` |
| 6 | Edge 401, 403, 415 | Outside the contract. No edit (AM-10 row 4). | none |

**Lockstep (AM-10 row 7).** One dependency-free constant `CONTRACT_VERSION` in a new core module is read by `api/server.py`, `api/presenter.py` and `mcp_server.py`, so the three literals disappear. A test compares it with `info.version` and the `ContractVersion` constant in `api/openapi.yaml`, with `CONTRACT_VERSION` in `ui-kit/src/api.ts`, and with `contractVersion` in every file in `api/examples/`. The same change updates `ui-kit` types and components, the examples, `docs/API_CONTRACT.md` and the tests that pin `1.1.0`. The existing mutation row that sets `authenticity.status` to `VERIFIED` still fails validation, unmodified.

**Clients.** Tolerant JSON clients keep working and see only the version value change. Strict 1.1.0 validators fail on the new fields, which is the stated effect of a bump. The server does not serve two versions. The frozen tag `v1.0.0-submission` is the supported 1.1.0 pair. The UI and the server refuse each other's other version, as today. `ui/judge` pins `1.1.0` in `app.js` and conflicts with DD-10 (OD-D5-5). MCP `replay_bundle` reports 1.2.0 and adds `authenticity` fields to `explain_verdict` (D4.3). The CLI prints the four results on separate lines with the fingerprint (10.20), and its exit code rule stays "0 only for reproduced and intact" (OD-D5-6 covers a present but `INVALID` signature).

**Documentation.** `docs/SIGNING.md` states that a valid signature establishes who signed the bytes and does not establish that the claim is true, that the timestamp is trusted, or that the key was not compromised (10.23). It also documents key provisioning, the Trust_Store format, rotation, revocation and the reason codes.

### D5.9 Adversarial tests and deterministic replay

Every row asserts the stated result and also that `authenticity` is never `ESTABLISHED` unless the row says so. A mutation guard flips each check off in a copy of the code and must see the matching row fail.

| # | Attack or fault | Expected |
|---|---|---|
| A-1 | One byte changed in each manifest-listed member (every member of the stub bundle) | Integrity `FAILED`, signature `VALID`, `NOT_ESTABLISHED`, `INTEGRITY_NOT_VERIFIED` |
| A-2 | One byte changed at every offset of `manifest.json` | `INVALID` (`MANIFEST_HASH_MISMATCH`) or malformed. Never `ESTABLISHED`. |
| A-3 | One hex digit changed in each envelope field. `alg` changed to `Ed25519`, `ED25519`, `ed448`, `none`, empty | `INVALID`, or `UNSUPPORTED_ALGORITHM` for `alg`. No fallback. |
| A-4 | Envelope removed | `UNSIGNED`, `NOT_ESTABLISHED`. No claim of tampering. |
| A-5 | Re-signed with an attacker key | `VALID`. `UNTRUSTED_SIGNER` with a store, `NOT_EVALUATED` without. Never `ESTABLISHED`. |
| A-6 | Envelope copied from bundle X into bundle Y | `INVALID` (`MANIFEST_HASH_MISMATCH`) |
| A-7 | Duplicate `signature/envelope.json`. Duplicate `manifest.json`. A raw name made of the envelope name, a NUL byte and more text, alone and next to the real envelope | `INVALID` (`DUPLICATE_ARCHIVE_PATH` or `ARCHIVE_UNREADABLE`), the same on both hosts |
| A-8 | Second envelope under `signature/envelope2.json`, `Signature/Envelope.json`, `signature/envelope.json ` (trailing space), a fullwidth `ｓignature/envelope.json`, `signature\envelope.json`, `./signature/envelope.json` | `INVALID` (`UNKNOWN_SIGNATURE_MEMBER` or `ARCHIVE_UNREADABLE`), the same on both hosts |
| A-9 | Manifest lists the envelope or another reserved name | `INVALID` (`ENVELOPE_LISTED_IN_MANIFEST`) |
| A-10 | Envelope with whitespace, other key order, uppercase hex, an extra or missing key, a duplicate key, a float, a BOM, a trailing newline, more than 2,048 bytes | `INVALID` |
| A-11 | Signature of 63 or 65 bytes, non-hex, truncated JSON | `INVALID` |
| A-12 | Small-order public keys (the full list) with a universal signature and a matching `key_id` | `INVALID` (`PUBLIC_KEY_SMALL_ORDER`) |
| A-13 | Signature with `S+L` (non-canonical S) | `INVALID` |
| A-14 | `key_id` that differs from the SHA-256 of the embedded key | `INVALID` (`KEY_ID_MISMATCH`) |
| A-15 | Signature made without the domain tag, or with another tag, or over only `manifest_sha256` | `INVALID` |
| A-16 | Trust_Store: malformed JSON, duplicate keys, unknown field, unknown status, `key_id` not equal to the key hash, duplicate `key_id`, 262,145 bytes, BOM, directory, unreadable, unknown `format_version`, pin mismatch | `NOT_EVALUATED` with the reason. Validity and integrity unchanged. Never `TRUSTED`. |
| A-17 | Store states: `REVOKED`, expired, not yet valid, `ROTATED`, `ACTIVE`, boundary instants of the interval | As D5.7. `as_of` equal to either bound is inside. |
| A-18 | Trust injection: a bundle member, an MCP argument, an HTTP parameter or header, a request body field | No effect on the store. The bundle member case is `UNKNOWN_SIGNATURE_MEMBER`. |
| A-19 | Signing key file: missing, empty, directory, symlink, RSA, Ed448, encrypted, 4,097 bytes, group-readable (POSIX) | Run or bundle creation aborts with the matching code. No `.vkb`, no `.tmp`, no ledger append, no key bytes or path in any output. |
| A-20 | Canary key: the private key bytes searched for in the bundle, API and MCP results, error text, stdout, stderr, logs and the examiner environment | 0 occurrences |
| A-21 | Zip bomb or oversized envelope | Existing limits apply. `ENVELOPE_TOO_LARGE`. |

**Deterministic replay requirements.** DR-1: the same case, clock and key give byte-identical bundles in one environment, and identical member hashes on both host classes (zip bytes can differ across zlib builds). DR-2: the same bundle, Trust_Store bytes and `as_of` give a byte-identical `authenticity` JSON on Windows and Linux. DR-3: verification reads no clock except `as_of`, opens no socket and reads no environment variable except the documented ones, and a test replaces `time`, `datetime` and `socket` with guards that raise. DR-4: signing and verification do not read the verdict hash inputs, so the verdict hash is equal for signed and unsigned runs and a signed bundle replays `REPRODUCED`. DR-5: the key order of a Trust_Store file does not change the result. DR-6: the reason codes and keys in a report are sorted. DR-7: before D5 code changes, a pre-change step records the SHA-256 of the zip and of every member for the fixed reference bundles on each host, and the post-change run must reproduce the member hashes everywhere and the zip hash on the same host. DR-8: Hypothesis properties under the `ci` profile cover the round trip, "no single-byte change of a signed region yields `ESTABLISHED`" and replay stability.

### D5.10 Acceptance criteria

All rows are UNVERIFIED until an Execution_Record exists.

| ID | Check | Pass threshold | Req | Host |
|---|---|---|---|---|
| D5-AC-1 | Unsigned compatibility: DR-7 hashes. `golden.vkb` verifies, replays and reports `UNSIGNED` and `NOT_ESTABLISHED`. All existing tests pass. | 0 member-hash differences, 0 zip-hash differences on the same host, 0 edits to `tests/contract/test_bundle_replay.py` and `tests/integration/test_bundle_evidence_and_golden.py`, and every other test diff is a `1.1.0` to `1.2.0` literal change | 10.5, 10.32 | Both |
| D5-AC-2 | Round trip with generated keys, each of `ACTIVE` and `ROTATED` | 200 of 200 examples `VALID`, `TRUSTED`, `ESTABLISHED`. `ROTATED` adds `KEY_ROTATED`. | 10.22, 10.28 | Both |
| D5-AC-3 | Deterministic signing | Two runs and two processes give 0 differing bytes | 10.7 | Both |
| D5-AC-4 | Verdict hash independence | Equal hash, signed against unsigned. Signed replay `REPRODUCED`. | 10.6 | Both |
| D5-AC-5 | A-1 and A-2 exhaustively on the stub bundle | 0 `ESTABLISHED`. Each case has the stated result. | 10.15 | Both |
| D5-AC-6 | A-3 to A-15 | 0 `VALID` where an attack row forbids it, and the stated code in 100% of rows | 10.24, 10.29, 10.30 | Both |
| D5-AC-7 | Exemption exactness, with a mutated prefix-match copy of the code | The exact name passes. The mutated code fails A-8. | 10.31 | Both |
| D5-AC-8 | Trust_Store rows A-16 and A-17 and the 24-combination truth table of validity, trust and integrity | `ESTABLISHED` in exactly 1 combination. Every failure keeps validity and integrity unchanged. | 10.9 to 10.14, 10.17, 10.27, 10.28, 10.33 | Both |
| D5-AC-9 | Key handling A-19 and A-20, the examiner environment check and the examiner-uid read check | 0 files created on failure, 0 canary occurrences, examiner cannot read the key (container) | 10.2, 10.18, 10.25 | Both, container on Linux |
| D5-AC-10 | Offline and time guards (DR-3) | 0 sockets, 0 clock reads other than `as_of` | 10.19 | Both |
| D5-AC-11 | Contract: examples and responses validate against `api/openapi.yaml` 1.2.0. The version constant equals every pin of F5-7 that is edited. | 0 mismatches. The old `VERIFIED` mutation row still fails. | 10.21 | Both |
| D5-AC-12 | D2 items 1 to 5 of D5.8 are described in `api/openapi.yaml` and validated, including the 503 and 429 bodies | 0 schema errors | 10.21 | Both |
| D5-AC-13 | Display: API, CLI and UI show validity, trust, authenticity and fingerprint as separate fields. UI tests assert label text. A scan rejects "authenticated", "signed" and "verified" applied to an unsigned bundle. | 4 separate results in 3 surfaces, 0 forbidden phrases | 10.20, 10.32, 10.33 | Both |
| D5-AC-14 | `docs/SIGNING.md` holds the three statements of 10.23 | 3 of 3 present | 10.23 | Both |
| D5-AC-15 | Cross-host determinism DR-2 | 0 differing bytes between Windows and Linux outputs | 10.7, 2.2 | Both |
| D5-AC-16 | Hypothesis properties of DR-8 | 0 failures in 200 examples per property | 10.15, 10.22 | Both |
| D5-AC-17 | MCP: `replay_bundle` and `explain_verdict` return the `authenticity` object (joint with D4-AC-19) | Present, schema-valid | 9.8 | Both |

### D5.11 Open decisions, risks and traceability

| ID | Decision | Recommendation |
|---|---|---|
| OD-D5-1 | Contract event: 1.2.0 joint, 1.1.0 with a documented header, or split events | 1.2.0 joint (D5.8). The maintainer confirms. |
| OD-D5-2 | One envelope member or separate signature, algorithm and key members | One member. Fewer names to exempt and to reject, one parse. 10.4 allows it. |
| OD-D5-3 | Interval checked against the verifier clock or the manifest time | Verifier clock. |
| OD-D5-4 | MCP signs bundles | No in this phase. Later only with an authenticated isolated examiner. |
| OD-D5-5 | `ui/judge` under the bump: leave it (refuses 1.2.0, DD-10 kept) or change its one constant | Leave it. D2 does not deploy it. Record the incompatibility in the release notes. |
| OD-D5-6 | CLI exit code for a present `INVALID` signature | Exit 1 when `signatureValidity` is `INVALID`. `UNSIGNED` and the rest unchanged. |
| OD-D5-7 | Unsupported protocol or format version | Map to `UNSUPPORTED_ALGORITHM` with its own reason code, because the verifier lacks the means and the signature is not shown to be forged. |
| OD-D5-8 | Encrypted private keys | Not supported now. A passphrase file would be one more secret. |
| OD-D5-9 | Signing while `UNENFORCED` | Allow with a CLI warning. The public profile already requires `ENFORCED`. |
| R-D5-1 | Key file permissions on Windows are not checked | UNVERIFIED. Operators use an ACL. |
| R-D5-2 | No trusted timestamp: rotated-key reuse and back-dating cannot be detected | Documented. Revoke on suspicion. |
| R-D5-3 | Offline revocation depends on distributing a new store | `serial` and hash are reported. Pin the hash. |
| R-D5-4 | Container bytes are not signed | Stated in `docs/SIGNING.md`. |
| R-D5-5 | The small-order list depends on the library's current behaviour | Test vectors run on every `cryptography` version bump. |

**Files for implementation (not changed now).** `core/src/verdictkit/bundle.py`; new `core/src/verdictkit/signing.py` and the contract-version module; `cli.py`; `api/server.py`, `api/presenter.py`, `api/run_service.py`; `mcp_server.py`; `api/openapi.yaml`, `api/examples/*.json`; `ui-kit/src/{api.ts,types.ts,components.tsx}` and tests; `docs/API_CONTRACT.md`, new `docs/SIGNING.md`; `deploy/entrypoint.sh` (environment pass-through for the custodian only); new tests and fixtures. `ui/judge` is not edited unless OD-D5-5 changes.

**Traceability.** 10.1: D5.4, AC-6. 10.2: D5.5, AC-9. 10.3: D5.2 F5-1. 10.4: D5.4. 10.5: D5.5, AC-1. 10.6: D5.4, AC-4. 10.7: D5.4, AC-3, AC-15. 10.8: D5.3, AC-8. 10.9, 10.10: D5.3, AC-8. 10.11, 10.12: D5.7, AC-8. 10.13, 10.14: D5.3, AC-8. 10.15: D5.9, AC-5. 10.16, 10.17: D5.7, AC-8. 10.18: D5.5, AC-9. 10.19: D5.6, AC-10. 10.20: D5.3, D5.8, AC-13. 10.21: D5.8, AC-11, AC-12. 10.22: D5.9, AC-2, AC-16. 10.23: D5.8, AC-14. 10.24: D5.4, AC-6. 10.25: D5.5, AC-9. 10.26: D5.4, AC-6. 10.27, 10.28: D5.7, AC-2, AC-8. 10.29: D5.4, AC-6. 10.30: D5.6, D5.9, AC-6. 10.31: D5.6, AC-7. 10.32: D5.3, AC-1, AC-13. 10.33: D5.3, AC-8, AC-13. Every criterion of Requirement 10 maps to at least one D5 section and one acceptance row. D2 coordination: AM-10 rows 1 to 7 map to D5.8 items 1 to 6 and the lockstep paragraph. D1 OD-7 maps to the display rules in D5.3. D4 criterion 9.8 maps to AC-17.

### D5.12 Maintainer decisions on open items (conditional approval)

The maintainer approved D5 conditionally. Each decision below is DECIDED and DESIGNED. None is implemented, no signing key was created and no test was run for D5. Text in D5.1 to D5.11 is unchanged. Where a decision here differs from that text, this section governs. The ledger entries U-001 to U-005 are confirmed present in `docs/next-phase/EXECUTION_EVIDENCE.md`, so this record makes no ledger change.

| ID | Decision | Effect on D5 text |
|---|---|---|
| AM-D5-1 | Signatures use Ed25519 through the maintained `cryptography` library with strict validation. The project writes no elliptic-curve or field arithmetic and no point decoding. | D5.4 stands. The small-order list of D5.6 step 5 is a constant table of byte encodings compared byte for byte. It is not curve code. Its entries are taken from a published list whose source is named in `docs/SIGNING.md`, and vectors check them (R-D5-5). |
| AM-D5-2 | Public keys, encodings and signature representations are validated before use. Public key: 32 bytes, SHA-256 equal to `key_id`, not on the small-order or non-canonical list. Envelope: canonical JSON, exact key set, lower-case hex of fixed length. Signature: 64 bytes with `S < L`. | D5.6 steps 4, 5 and 7 stand. Where the library accepts a form that A-12, A-13 or the vectors of AM-D5-3 forbid (F5-6 shows it accepts small-order keys), the verifier adds a table check. No library behaviour is assumed without a vector. |
| AM-D5-3 | Adversarial vectors are mandatory: every small-order encoding, non-canonical encodings (including a `y` value at or above the field prime), keys of 31 and 33 bytes, the all-zero and identity keys, a small-order or non-canonical `R` in an otherwise valid signature, `S+L`, and a universal signature. | D5-AC-6 gains these rows next to A-12 and A-13. They run on both hosts and on every `cryptography` version change. The mitigation of R-D5-5 becomes mandatory. |
| AM-D5-4 | Signing keys are provisioned outside the application. The application never generates, stores in the repository, logs or returns a private key. Tests use throwaway keys created in memory. | D0.8 item 5 and D5.5 stand. A-19 and A-20 stay the checks. |
| AM-D5-5 | MCP never signs bundles. | OD-D5-4 decided as recommended. `mcp_server.py` gains no signing path. |
| AM-D5-6 | Key validity and revocation are evaluated against an explicit verifier policy: the Trust_Store the verifier names and the `as_of` it passes. Nothing inside a bundle selects either. A missing or unreadable store gives `NOT_EVALUATED`. | OD-D5-3 decided: the verifier's explicit `as_of`, not the manifest time. D5.6 and D5.7 stand. |
| AM-D5-7 | An embedded signing time or `written_at` is not a trusted timestamp. It is never used to judge validity or revocation. If shown, it is labelled as a claimed time. | R-D5-2 stands and becomes a display rule. The wording scan of D5-AC-13 rejects text that presents such a value as the time of signing. |
| AM-D5-8 | Unsigned bundles stay compatible. `golden.vkb` and every unsigned bundle keep verifying and replaying and report `UNSIGNED`. They are never called invalid or tampered. | D5-AC-1 stands. |
| AM-D5-9 | Every archive member name is validated in its original stored form (`orig_filename`) before any platform normalisation. This covers the baseline `_check_zip_safety` checks as well as the signature checks. | F5-3 and D5.6 step 1 stand. A-7 and A-8 run on both hosts with identical results. |
| AM-D5-10 | Each contract change carries one label, COMPATIBLE or BREAKING, in a table in `docs/API_CONTRACT.md`. BREAKING means a client that validates strictly against the previous schema rejects the response, or documented behaviour changes. Breaking changes are listed apart in the release notes and are never described as additive. | The D5.8 table is labelled from its own Compatibility column: rows 1, 2 and 3 BREAKING (row 3 in the public profile only), rows 4 and 5 COMPATIBLE, row 6 outside the contract. OD-D5-1 stays open: whether the event keeps the label 1.2.0 is decided after the labels are approved, and no version literal is edited before then. New row D5-AC-18. |
| AM-D5-11 | Minimal next-phase compatibility changes to `ui/judge` are permitted: the constant `CONTRACT` in `app.js` and the version label in `index.html`, and nothing else. The frozen submission stays untouched: the Frozen_Release refs and the Submission_Artifacts are not edited. The existing judge preview tests keep passing, and this change edits none of them (a BE-2 remediation edit under D8 is separate). | OD-D5-5 decided differently from the recommendation. DD-10 now reads: `ui/judge` is not restyled, and the compatibility change of AM-D5-11 is allowed. `ui/judge` is application code and is not one of the named Submission_Artifacts. If the maintainer reads the catch-all of that definition as covering it, 1.8 needs a recorded exception. New row D5-AC-19. |

**Acceptance rows added by this record (all UNVERIFIED).**

| ID | Check | Pass threshold | Req | Host |
|---|---|---|---|---|
| D5-AC-18 | Contract labels: every row of the D5.8 table and every added field has one label, and the release-note section lists the BREAKING rows | 0 unlabelled changes | 10.21 | Both |
| D5-AC-19 | Judge UI: `git diff 84df25c -- ui/judge`, `tests/ui/test_judge_preview.py` passing and unmodified except a BE-2 remediation hunk, diff of the Submission_Artifacts and the three Frozen_Release refs | Only the constant and the label differ. 0 changed submission lines. 0 changed refs. | 10.21, 1.2, 1.8 | Both |

**Not decided in this review.** OD-D5-1 (see AM-D5-10), OD-D5-2, OD-D5-6, OD-D5-7, OD-D5-8 and OD-D5-9, and the risks R-D5-1 to R-D5-4, stay open with the recommendations of D5.11.

**Traceability.** AM-D5-1: 10.3, 10.24. AM-D5-2: 10.24, 10.29, 10.30. AM-D5-3: 10.15, 10.24, 10.30. AM-D5-4: 10.2, 10.18, 10.25. AM-D5-5: 10.2, 10.18. AM-D5-6: 10.9 to 10.14, 10.19. AM-D5-7: 10.19, 10.33. AM-D5-8: 10.5, 10.32. AM-D5-9: 10.29, 10.31. AM-D5-10: 10.21. AM-D5-11: 10.21, 1.2, 1.8.

### D5.13 Maintainer decisions recorded with the D6 and D7 review (contract 2.0.0 and judge UI)

The maintainer's D6 and D7 review also recorded these decisions for D5. Each is DECIDED and DESIGNED. Nothing is implemented, no signing key was created and no test was run for D5. Text in D5.1 to D5.12 is unchanged. Where a decision here differs from that text, this section governs.

| ID | Decision | Effect on D5 text |
|---|---|---|
| AM-D5-12 | OD-D5-1 is decided: the contract event is **2.0.0**, not 1.2.0. D5.8 rows 1 and 2 are BREAKING, and row 3 is BREAKING in the public profile (AM-D5-10); a strict 1.1.0 validator rejects them, so the major version changes, while every existing field is preserved (10.21). One version is served, with no dual serving. The D5.8 lockstep list (the `CONTRACT_VERSION` constant, `openapi.yaml` `info.version` and `ContractVersion`, the `ui-kit` constant, `contractVersion` in `api/examples/`, the MCP replay result, the tests) moves together in one change. `docs/API_CONTRACT.md` gains a migration section with a before and an after example for each BREAKING row and a client checklist. Compatibility tests show a tolerant 1.1.0 client working against 2.0.0, a strict 1.1.0 validator failing on exactly the documented BREAKING rows and nothing else, and the UI_Kit and API_Server each refusing the other's other major version with an error naming both versions. The frozen tag `v1.0.0-submission` stays the supported 1.1.0 pair; bundle format and API contract stay separate, so bundles written under 1.1.0 keep verifying and replaying. The D7 contract-visible items (`as_of`, the snapshot retrieval date, the Examination_Semantics id) are classified in this same event. Release notes list BREAKING rows apart, never as additive. Rollback is one revert of the lockstep change, including the judge-UI constant. | D5.8 and AM-D5-10 named only the label; OD-D5-1 now resolves to 2.0.0, not 1.2.0. D5-AC-18 is read with 2.0.0. No version literal is edited until implementation (10.34). D7's OD-D7-3 and G-D7-1 (the `as_of` key and the snapshot retrieval date) are classified here. |
| AM-D5-13 | Confirms AM-D5-11. Minimal compatibility changes to `ui/judge` are allowed on the Phase_Branch: the `CONTRACT` constant in `app.js` (now `2.0.0`) and the version label in `index.html`, nothing else. `ui/judge` is application code, not a Submission_Artifacts file. The Frozen_Release refs and the Submission_Artifacts files stay immutable. | DD-10 is read with this exception, as AM-D5-11 already stated. D5-AC-19 now expects the constant `2.0.0` rather than `1.2.0` (10.21, 10.35). |

**Not decided in this review.** OD-D5-2, OD-D5-6, OD-D5-7, OD-D5-8, OD-D5-9 and the risks R-D5-1 to R-D5-4 stay open with the recommendations of D5.11.

**Traceability.** AM-D5-12: 10.21, 10.34. AM-D5-13: 10.21, 10.35, 1.2, 1.8.

## D6. P5 Reusable claim-plugin SDK

### D6.1 Scope and status

**Covers.** Requirement 11 (11.1 to 11.15): documented protocol and registration, the scaffolding command, the Conformance_Suite, a synthetic example, and the guards that keep plugins behind the Answer_Blind boundary. It adds the rule that a public deployment never loads an untrusted plugin.

**Does not cover.** A sandbox for hostile code, plugin signing or publishing, loading in a request path, and any change to the HTTP contract or to the claim types it lists.

**Status.** Everything in D6 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. Facts marked (read) come from a read-only inspection at commit `c29d2fe` and are UNVERIFIED for Requirement 3 until a record exists. Notes: `docs/next-phase/D6_D7_WORKING_NOTES.md`.

### D6.2 Inspected baseline and findings

Read: `core/src/verdictkit/{plugin.py,cli.py,mcp_server.py}`, `api/{server.py,run_service.py}`, `examiner/worker.py`, `deploy/entrypoint.sh`, `Dockerfile`, `examples/pyproject.toml`, `examples/stub_claimtype/*`, `tests/contract/{receipt_claimtype,test_blinding,test_llm_fence,test_isolation}.py`, both app `pyproject.toml` files and `.kiro/steering/verdict-integrity.md`.

| # | Finding (read) | Req |
|---|---|---|
| F6-1 | `ClaimType` is a `runtime_checkable` Protocol: four attributes, nine methods, six optional hooks read with `getattr`. | 11.1, 11.14 |
| F6-2 | `Registry.register` overwrites a duplicate `type_id` silently. Any installed package can replace a built-in claim type. | 11.15 |
| F6-3 | `_load_registry` is the only discovery path (CLI, API, MCP, Examiner worker). The entry-point loop sits in one `try/except Exception: pass`, so one failing plugin silently stops every later one. `VK_CLAIM_TYPES` imports any named module. | 11.1 |
| F6-4 | `entrypoint.sh` passes `VK_CLAIM_TYPES` to the custodian and the Examiner. The image installs the example package (`uv sync --frozen --all-packages`). The API filters to `CONTRACT_CLAIM_TYPES` only after loading, so unlisted plugin code is already imported. | 11.15 |
| F6-5 | No `type_id` grammar exists. Intake uses `raw.get("schema_version", plugin.schema_version)` and nothing compares the two. The entry-point name need not equal `type_id`. | 11.4, 11.14 |
| F6-6 | Two receipt claim types exist, `examples/stub_claimtype/receipt.py` (installed, with `golden.vkb`) and `tests/contract/receipt_claimtype.py` (used by the blinding and replay tests). Their hashes differ. | 11.11 |
| F6-7 | First-party plugin sources contain no `float`, no `.now(` and no `os.environ` (text search). `reel_autopsy` imports `datetime`. | 11.5, 11.11 |
| F6-8 | `VK_PROFILE` exists only in the D2 design. `VK_JUDGE_MODE` exists in `api/server.py`. | 11.15 |

### D6.3 Design decisions

| ID | Decision | Alternative rejected | Why |
|---|---|---|---|
| DD6-1 | A plugin is trusted code that an operator admits. The SDK is a conformance and safety rail, not a sandbox. No request, API field, MCP argument or UI input names a plugin. | Claim that scans make a plugin safe. | A plugin runs in the Custodian after reveal and holds outcomes there. Checks cannot confine Python code. |
| DD6-2 | New package `core/src/verdictkit/sdk` (`loader`, `validate`, `conformance`, `scaffold`). `plugin.py` is unchanged. `cli._load_registry` keeps its name and calls the loader. | Edit `Registry` or the Protocol. | 11.14. Tests call both. |
| DD6-3 | Entry point `python -m verdictkit.sdk new` and `check`. The CLI parser is unchanged. | `verdictkit plugin` subcommands. | Smaller change (OD-D6-1). |
| DD6-4 | Local mode keeps both mechanisms: entry-point group `verdictkit.claim_types` and `VK_CLAIM_TYPES`. Public mode loads a closed allowlist, decided before any import. | Filter after loading, as the API does. | Import is code execution (F6-4). |
| DD6-5 | `type_id` grammar `NAMESPACE.NAME.vN`. The suffix is the compatibility generation. `schema_version` is the revision. | Free text. | F6-5. |
| DD6-6 | One function `run_suite` serves the command, the generated test and the repository tests. | Separate copies. | F6-6 shows copies drift. |
| DD6-7 | The synthetic example is the scaffold output for `example.line_total.v1`, generated in a temporary directory at test time. The stub stays the committed example. | Commit a second package. | One source of truth. |
| DD6-8 | Messages carry a code, the entry-point name and the distribution name. Never exception text, a path or a claim value. | Print the exception. | D4 sanitising rule, 2.3. |

### D6.4 Registration and discovery

**Loader `sdk.loader.discover(policy)`** returns the loaded types and a list of issues `(code, entry_point, distribution)`.

1. List the entry points of the group with `importlib.metadata`. Listing imports nothing. Sort by distribution name, then entry-point name, so the result does not depend on directory order.
2. In public mode drop every entry point whose `(distribution, value)` pair is not on the allowlist **before** `ep.load()`. Dropped entries are counted and logged by code (`PLUGIN_NOT_ALLOWLISTED`). They are not an error.
3. Load each remaining entry in its own `try` block. A failure records `ENTRY_POINT_LOAD_FAILED`, writes one stderr line `VKPLUGIN v1 code=<CODE> ep=<name> dist=<name>` and the loop continues.
4. Validate the object (D6.5). A `type_id` in namespace `quote` is accepted only from distribution `quote-autopsy`, in `reel` only from `reel-autopsy`, and `verdictkit` and `vk` from none (`TYPE_ID_RESERVED`).
5. Two registrations with one `type_id` are both rejected (`TYPE_ID_DUPLICATE`). There is no silent winner.
6. `VK_CLAIM_TYPES` runs after the entry points, in local mode only, and each item passes the same checks. An import error is an issue, not a crash.

| Mode | Sources | `VK_CLAIM_TYPES` set | Failed plugin |
|---|---|---|---|
| Local (default) | all entry points, then `VK_CLAIM_TYPES` | read | issue line, continue |
| Public: `VK_JUDGE_MODE=1` or `VK_PROFILE=public` | allowlist constant: distributions `quote-autopsy` and `reel-autopsy`, the three `CONTRACT_CLAIM_TYPES` values | start-up refuses, `VK_STARTUP_ERROR=plugin_loading_disabled` | start-up refuses if an allowlisted type fails |

Either variable selects public mode, so a missing profile cannot loosen it. The mode is read once at start-up. The allowlist is a code constant that no file, variable or request changes. The Examiner worker applies the same policy, so `deploy/entrypoint.sh` must pass the profile variable to it (G-D6-1). The example package stays installed and is ignored in public mode.

**Codes.** `ENTRY_POINT_LOAD_FAILED`, `NOT_A_CLAIM_TYPE`, `TYPE_ID_INVALID`, `TYPE_ID_RESERVED`, `TYPE_ID_DUPLICATE`, `SCHEMA_VERSION_INVALID`, `FIELDS_INVALID`, `SDK_API_UNSUPPORTED`, `PLUGIN_NOT_ALLOWLISTED`, `PLUGIN_LOADING_DISABLED`.

### D6.5 Validation and version compatibility

| Level | Rule | Code |
|---|---|---|
| Identifier | `type_id` is ASCII, at most 64 characters and matches `^[a-z][a-z0-9_]{1,31}(\.[a-z][a-z0-9_]{1,31}){1,3}\.v[1-9][0-9]{0,2}$`. | `TYPE_ID_INVALID` |
| Descriptor | Four attributes and nine methods present, each method with the Protocol's positional arity. `schema_version` is an `int` of at least 1 and not a `bool`. `param_fields` and `outcome_fields` are `frozenset[str]`, `outcome_fields` is not empty, and the sets are disjoint. | `NOT_A_CLAIM_TYPE`, `SCHEMA_VERSION_INVALID`, `FIELDS_INVALID` |
| Claim | `validate_params` and `validate_outcomes` raise `SchemaError` and nothing else for bad input (CS-09). D4 maps `SchemaError` to `CLAIM_INVALID` and any other exception to `INTERNAL_ERROR`. | suite check |

The four existing types must pass the identifier and descriptor levels, so `list_claim_types` over MCP keeps its four entries (D6-AC-14).

- **Generation.** The `vN` suffix. A change that alters verdicts of existing claims needs a new generation, registered beside the old one while old bundles must replay.
- **Revision.** `schema_version`. CS-07 checks that the golden claim states it. Core compares the two nowhere (F6-5). Enforcing it at intake and replay is OD-D6-3. D6 records the gap and changes no core behaviour.
- **SDK API.** `verdictkit.sdk.SDK_API_VERSION` is 1. A plugin may set the optional class attribute `sdk_api`. Absent means 1. Any other value gives `SDK_API_UNSUPPORTED`. The attribute is optional, so no Protocol signature changes (11.14).
- **Core.** The scaffold `pyproject.toml` pins `verdictkit` to a compatible range (`>=0.1,<0.2` at version `0.1.0`). Installers enforce it. The loader does not re-evaluate specifiers, because `packaging` is not a declared dependency.
- **HTTP contract.** Unchanged. A new plugin is reachable by the CLI and MCP only. Exposing it over HTTP needs a change to the `ClaimTypeId` enum in `api/openapi.yaml`, which is a contract event for D5.8 and out of scope (11.15).

### D6.6 Scaffolding command

**Command.** `python -m verdictkit.sdk new <type_id> --dest <dir> [--package <name>]`. The default package name joins namespace and name with `_` (`example_line_total` for `example.line_total.v1`). The distribution name is `verdictkit-claimtype-` plus the package name with `_` as `-`.

**Identifier rules (11.4).** The package name is lowercase ASCII, 2 to 40 characters, a valid identifier, not a keyword, not in `sys.stdlib_module_names`, not `verdictkit`, `quote_autopsy`, `reel_autopsy` or `stub_claimtype`, and not a Windows device name (`con`, `prn`, `aux`, `nul`, `com1` to `com9`, `lpt1` to `lpt9`, compared without case and with or without an extension). The `type_id` follows D6.5 and its namespace is not `quote`, `reel`, `verdictkit` or `vk`. The message names the identifier and the rule. The identifier is echoed with control characters escaped and at most 80 characters.

**Algorithm.** (1) Validate every identifier with no file access. (2) Resolve the destination. Refuse a file, a symlink, a path inside `core/src/verdictkit` (11.6) and a non-empty directory. (3) Render every file in memory by replacing validated tokens, then run `ast.parse` and CS-10 on the Python output. (4) Create the directory if absent and write each file with exclusive creation. (5) On any error remove only the files and the directory that this run created and exit non-zero. An existing file is never opened for writing (11.3).

**Output tree (11.2).** `pyproject.toml` (backend `hatchling`, entry point `<type_id> = "<package>.claim_type:<ClassName>"` in group `verdictkit.claim_types`, the range of D6.5), `<package>/__init__.py`, `<package>/claim_type.py`, `<package>/golden/claim.json`, `tests/test_conformance.py`.

**Template.** A line-total claim type: params `unit_price` and `quantity`, outcome `stated_total`, one assumption axis `discount_pct` fixed at 0 by policy. It uses `Decimal` inside `localcontext` with explicit precision and `ROUND_HALF_EVEN`, returns `format(value, "f")`, and has no `float`, clock, randomness or environment read. It sets `sdk_api = 1`. The golden claim states that its numbers are constructed (`verdict-integrity.md` rule 8). The generated test calls `run_suite` with the class and the golden file.

**Determinism.** Output uses LF and holds no timestamp, path or random value. Two runs with equal arguments give byte-identical trees on both hosts (D6-AC-5). **Exit codes.** 0 success, 2 invalid identifier or usage, 3 destination not empty, 4 destination forbidden, 5 input or output error.

### D6.7 Conformance suite

`run_suite(target, golden=None, registry=None)` takes a registered `type_id`, or a class with a golden path. It runs every check, continues after a failure and returns `(check, status, field, code)` rows. `python -m verdictkit.sdk check <type_id> [--json]` exits 0 only when all pass, 1 on any failure, 2 on usage error and 3 when the type cannot be loaded (11.13). A failure names the check and the field and never a claim value. The golden claim comes from `--golden`, else from the first `fixtures()` entry, else the type must ship one (OD-D6-7).

| ID | Check | Req |
|---|---|---|
| CS-01 | Registered under its `type_id`, descriptor level of D6.5. With a `pyproject.toml`, its entry point is in the group and names a class with that `type_id`. | 11.1, 11.7 |
| CS-02 | `param_fields` and `outcome_fields` share no name. | 11.9 |
| CS-03 | Blinding. The golden claim and two outcome variants (each decimal outcome changed in its last place, and a 10-digit sentinel) give identical `encode_task` bytes and identical examination bytes. A variant that `validate_outcomes` rejects gives `NO_VALID_OUTCOME_VARIANT`. | 11.8 |
| CS-04 | Determinism. `examine` twice in one process and twice in child processes with `PYTHONHASHSEED` 1 and 2 give identical canonical examination bytes. | 11.9 |
| CS-05 | No `float` in the examination payload, in `shared` or in finding numbers. | 11.9 |
| CS-06 | The evidence policy forbids `SourceClass.CLAIMANT`, and every request for the golden claim names a permitted source. | 11.9 |
| CS-07 | The golden file is canonical JSON (`parse_canonical`, decimals as strings) and states the plugin's `schema_version`. | 11.10 |
| CS-08 | `run_case`, `write_bundle` and `replay_bundle(allow_refetch=False)` on the golden claim give `REPRODUCED`. | 11.10 |
| CS-09 | `validate_params({})` and `validate_outcomes({})` raise `SchemaError`. A float in place of each decimal string raises `SchemaError`. No other exception type escapes. | 11.9, D4.4 |
| CS-10 | AST scan of the class's module and the modules it imports from its own package (excluding `sources` and `assist`): no banned LLM import (names of `test_llm_fence.py`), no `float` name or literal, no call to `now`, `utcnow` or `today`, no import of `time`, `random`, `secrets`, `uuid`, `socket`, `ssl`, `urllib`, `http`, `subprocess` or `ctypes`, no `os.environ` or `os.getenv`. | 11.5, 2.9 |

The suite runs `examine` through `InProcessExaminer`, as `test_blinding.py` does. It imports custody modules, so the Examiner process never imports `sdk.conformance` or `sdk.scaffold` (D6-AC-11). CS-10 is a review aid. A plugin can evade it with `getattr` or a hidden import (R-D6-1).

### D6.8 Threats and controls

| # | Threat | Control | Check |
|---|---|---|---|
| T-P1 | A package on the path runs code at start-up in the Custodian or Examiner | Public mode filters before `ep.load()`. Local mode is an operator choice. | D6-AC-8 |
| T-P2 | A plugin replaces `quote.finance.v1` | Duplicate rejection, reserved namespaces | D6-AC-3 |
| T-P3 | `VK_CLAIM_TYPES` names a hostile module in a public deployment | Start-up refuses. The variable is read in local mode only. | D6-AC-9 |
| T-P4 | The scaffold writes outside the destination, overwrites or follows a link | Destination checks, exclusive create, rollback of own files only | D6-AC-6, 7 |
| T-P5 | An identifier injects text into a template or the terminal | Grammar before any substitution, escaped and capped echo | D6-AC-4 |
| T-P6 | A plugin reads outcomes, the vault, the key or the network | `BlindedTask` has no outcome field (CS-03). The SDK exposes no such handle. Examiner process isolation stays the control for the rest (R-D6-1). | D6-AC-10, 11 |

### D6.9 Acceptance criteria

All rows are UNVERIFIED until an Execution_Record exists. Rows needing the container or a symlink run on Linux.

| ID | Criterion | Method | Pass threshold | Req |
|---|---|---|---|---|
| D6-AC-1 | Suite on the existing types | `run_suite` on `quote.finance.v1`, `quote.lease.v1`, `reel.mechanical.v1`, `example.receipt.v1` | 10 of 10 checks pass for each of the 4. A `NO_VALID_OUTCOME_VARIANT` result for a first-party type is a defect of the variant rule of CS-03, not of the plugin. It is resolved by a recorded maintainer decision on the rule, never by weakening the check (R-D6-3). | 11.11 |
| D6-AC-2 | Fresh scaffold | Generate `example.line_total.v1` into a temporary directory, run the suite with no edit | 10 of 10 pass, exit 0, the 5 files of D6.6 exist | 11.2, 11.12 |
| D6-AC-3 | Loader rules | Fake distributions: duplicate id, `quote.*` id from another distribution, a failing entry point between two good ones | Both duplicates and the reserved id rejected, both good plugins load, one issue line each | 11.1, 11.15 |
| D6-AC-4 | Identifier rejection | Uppercase, dash, keyword, stdlib name, device name, 41 characters, control characters, path separators, reserved namespace | Exit 2, 0 files or directories created, message names identifier and rule, at most 80 characters echoed | 11.4 |
| D6-AC-5 | Output determinism | Two runs into two directories on each host | 0 differing bytes across the four trees | 11.2, 2.2 |
| D6-AC-6 | Non-empty destination | Destination holding one file | Exit 3, file byte-identical, 0 new entries | 11.3 |
| D6-AC-7 | Containment | Destination inside `core/src/verdictkit`, a file, a symlink, an injected failure at the third file | Exit 4 or 5, repository tree unchanged, 0 files left by the failed run | 11.6 |
| D6-AC-8 | Public mode is import-free | Fake distribution whose module writes a canary file on import | Public mode: 0 canary files and `PLUGIN_NOT_ALLOWLISTED`. Local mode: 1 canary file. | 11.15 |
| D6-AC-9 | Public refusal | `VK_JUDGE_MODE=1` with `VK_CLAIM_TYPES` set. `VK_PROFILE=public` alone. One allowlisted type made to fail. | Non-zero exit and a `VK_STARTUP_ERROR` line each. `VK_PROFILE=public` alone selects public mode. No key value in output. | 11.15 |
| D6-AC-10 | Suite negative controls | Mutants: outcome copied into the task, `float` in `shared`, a `set` iterated into output, `diagnose` removed, `CLAIMANT` permitted | Each mutant fails its check, the suite continues and exits 1 | 11.8, 11.13 |
| D6-AC-11 | SDK surface and import graph | Public names of `verdictkit.sdk` and the Protocol types. Import `verdictkit.examiner.worker` in a clean interpreter. | 0 parameters or returns carrying outcomes, vault, key or socket. `sdk.conformance` and `sdk.scaffold` absent from `sys.modules`. | 11.15 |
| D6-AC-12 | No protocol change | `git diff --stat 84df25c` over `plugin.py`, `test_blinding.py`, `test_llm_fence.py` | 0 changed lines | 11.14, 11.15 |
| D6-AC-13 | Fence on SDK and output | New test reusing the banned names of `test_llm_fence.py`, plus a test that the two name sets are equal | 0 violations in `sdk/` and in scaffold output. Sets equal. | 11.5 |
| D6-AC-14 | Existing surface | `list_claim_types` over MCP and the API claim-type list with the new loader. `docs/SDK.md` content test. | 4 entries of D4-AC-1 unchanged. API list equals `CONTRACT_CLAIM_TYPES`. Group, `VK_CLAIM_TYPES`, protocol, trust model, public rule and exit codes present. | 11.1, 11.15 |

### D6.10 Open decisions, risks and traceability

| ID | Decision or risk | Recommendation |
|---|---|---|
| OD-D6-1 | `python -m verdictkit.sdk` or `verdictkit plugin` subcommands | Module entry now. |
| OD-D6-2 | Unlisted entry points in public mode: ignore or refuse start-up | Ignore and count. The image keeps the example package. |
| OD-D6-3 | Enforce `schema_version` equality at intake and replay (F6-5) | Record the gap. A small core change may follow if the maintainer decides. Not needed for 11.x. |
| OD-D6-4 | Duplicate `type_id`: reject all, or first wins by sort order | Reject all. A winner by sort order is a hidden rule. |
| OD-D6-5 | Local-mode failure: report and continue, or stop | Report and continue. |
| OD-D6-6 | Reserved namespaces `quote`, `reel`, `verdictkit`, `vk` | As written. `example` stays free. |
| OD-D6-7 | Golden claims for `quote.*`, which has no `fixtures()` hook | Reuse existing constructed worksheets from the integration tests. Invent no numbers. |
| G-D6-1 | The Examiner needs the profile variable from `entrypoint.sh`. D2-AC-1 gains a start-up case for a failing allowlisted type. | Coordination with D2. |
| R-D6-1 | CS-10 and the import checks are not a sandbox | Stated in `docs/SDK.md`. Admission control is the control. |
| R-D6-2 | Local mode runs any installed package | By design. Documented. |
| R-D6-3 | CS-03 varies decimal outcomes only, with two derived variants. A plugin whose `validate_outcomes` rejects both gets `NO_VALID_OUTCOME_VARIANT`. Whether the four existing types accept the derived variants is UNVERIFIED until D6-AC-1 runs. | Stated in `docs/SDK.md`. Other outcome types need SDK API 2. A rejected derivation is corrected by a recorded decision on the variant rule, and the check is not weakened. |
| R-D6-4 | Windows device-name and path behaviour and the symlink case are UNVERIFIED | D6-AC-4 and D6-AC-7 on both hosts. |

**Files for implementation (not changed now).** New `core/src/verdictkit/sdk/{__init__,__main__,loader,validate,conformance,scaffold,templates}.py`; `cli.py` (`_load_registry` delegates); new `docs/SDK.md`; new tests under `tests/sdk/` and `tests/contract/test_sdk_fence.py`. Not changed: `plugin.py`, existing tests, `examples/`, the API contract.

**Traceability.** 11.1: D6.4, D6.5, AC-3, AC-14. 11.2: D6.6, AC-2, AC-5. 11.3: D6.6, AC-6. 11.4: D6.5, D6.6, AC-4. 11.5: D6.6, CS-10, AC-13. 11.6: D6.6, AC-7. 11.7: D6.7, AC-1. 11.8: CS-03, AC-10. 11.9: CS-02 to CS-06, CS-09, AC-10. 11.10: CS-07, CS-08, AC-1. 11.11: AC-1. 11.12: AC-2. 11.13: D6.7, AC-10. 11.14: D6.3, D6.5, AC-12. 11.15: D6.4, D6.8, AC-3, AC-8, AC-9, AC-11, AC-12, AC-14. D0.4 rows for 2.1, 2.2, 2.3 and 2.9 map to D6.6, D6.7 and T-P6. Every criterion of Requirement 11 maps to at least one D6 section and one acceptance row.

### D6.11 Maintainer decisions on open items (conditional approval)

The maintainer approved D6 conditionally, with the decisions below recorded in the same D6 and D7 review. Each is DECIDED and DESIGNED. None is implemented, no plugin is loaded and no test was run for D6. Text in D6.1 to D6.10 is unchanged. Where a decision here differs from that text, this section governs.

| ID | Decision | Effect on D6 text |
|---|---|---|
| AM-D6-1 | OD-D6-2 is decided as recommended: public plugin loading fails closed. An unlisted entry point is never imported and is only counted. Any failure of an allowlisted plugin, a provenance mismatch, a duplicate `type_id`, `VK_CLAIM_TYPES` set, an unknown Security_Profile or an unreadable provenance manifest refuses start-up with a `VK_STARTUP_ERROR` code and a non-zero exit, and no listener opens. | D6.4's loader table is read with this rule. D6-AC-9 is extended to the provenance-manifest and plugin-failure cases in the public profile (11.15, 11.16). |
| AM-D6-2 | OD-D6-4 is decided as recommended: a duplicate `type_id` is rejected in every mode, and all colliding registrations are rejected, so the result does not depend on load order. In public mode this refuses start-up. OD-D6-5 is decided as recommended for local mode: the collision is reported and the colliding types are left unregistered. | D6.4 step 5 is read with this rule. D6-AC-3 already exercises both the duplicate and the reserved-id case (11.17). |
| AM-D6-3 | An approved plugin is bound to its Plugin_Provenance and not to a module name. An allowlist entry holds the distribution name, the exact version, the entry-point name, the entry-point value and `provenance_sha256`. The image build writes a root-owned, read-only provenance manifest from the locked tree (installed files with SHA-256, `RECORD` checked against disk, `__pycache__` excluded) for each allowlisted distribution; its own hash goes into release provenance (14.17) and an image label. The loader verifies the files before any import, and after import checks that the module file belongs to the verified set and that no other module claims the plugin's top-level name, refusing on mismatch with `PLUGIN_PROVENANCE_MISMATCH`. Only the `workspace-tree` provenance kind is built; a `locked-wheel` kind is designed and not built (YAGNI). | D6.4's allowlist description and D6.8's T-P6 row are read with this binding. D8 owns the provenance tests (PD-1 to PD-12) (11.18). |
| AM-D6-4 | G-D6-1 is closed: the Security_Profile is resolved by one function and validated in both processes. `VK_PROFILE` is `local` (default) or `public`; `public` or `VK_JUDGE_MODE=1` selects public mode, and a conflict (`VK_JUDGE_MODE=1` with `VK_PROFILE=local`) or an unknown value refuses start-up. `deploy/entrypoint.sh` passes the profile to the examiner. At start-up the custodian asks the examiner, over the authenticated socket, for its profile and a registry digest (SHA-256 over the sorted `type_id` and `schema_version` list); a mismatch refuses start-up. `VK_STARTUP_OK isolation=ENFORCED` is unchanged (7.7). | D6.4's note that `deploy/entrypoint.sh` must pass the profile variable to the examiner (G-D6-1) is resolved. D2-AC-1 gains these start-up cases (7.19, 11.15). |

**Not decided in this review.** OD-D6-1, OD-D6-3, OD-D6-6, OD-D6-7 and the risks R-D6-1 to R-D6-4 stay open with the recommendations of D6.10.

**Traceability.** AM-D6-1: 11.15, 11.16. AM-D6-2: 11.17. AM-D6-3: 11.18. AM-D6-4: 7.19, 11.15.

## D7. P6 Expanded regulatory verification from official sources

### D7.1 Scope and status

**Covers.** Requirement 12 (12.1 to 12.20): official-source and evidence-record rules, rule statuses, effective dates, deterministic snapshot updates, stale evidence, rollback, and the order Texas completion, then California, Florida and New York.

**Does not cover.** Retrieval of any source, naming of any official host, rule values for California, Florida or New York, lease tax rules, legal conclusions, and any edit to the Texas implementation.

**Status.** Everything in D7 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. No source was retrieved while writing this design, no host is named and no California, Florida or New York rule value appears in it. Facts marked (read) come from a read-only inspection at commit `c29d2fe` and are UNVERIFIED for Requirement 3 until a record exists. Notes: `docs/next-phase/D6_D7_WORKING_NOTES.md`.

### D7.2 Inspected baseline and findings

Read: `apps/quote-autopsy/src/quote_autopsy/{rules.py,sources.py,claim_type.py}`, `rules/{TX.json,MANIFEST.json}`, `docs/B7_TEXAS_SPEC.md`, `tests/integration/test_quote_b7_texas.py`, `tests/api/test_http_run_lifecycle.py` (the cases that use state codes), `core/src/verdictkit/model.py` (`compute_verdict_hash`), `api/openapi.yaml` (finding and evidence schemas) and `.gitattributes`.

| # | Finding (read) | Req |
|---|---|---|
| F7-1 | `TX.json` is canonical JSON with a closed key set. Each source has only `uri`, `retrieved_at` and `sha256_of_source`. No media type, excerpt or effective date. | 12.2, 12.19 |
| F7-2 | `load_rules` checks the file hash against `MANIFEST.json`, canonical form and the key set. `rules/` holds no source bytes, so no source hash can be recomputed offline. | 12.7 |
| F7-3 | `compute_verdict_hash` covers the sorted evidence hashes and, for every finding, `statement` and `reason`. Editing `TX.json`, or any Texas finding text, changes Texas verdict hashes. | 12.13 |
| F7-4 | A state other than `TX` gives `unsupported_jurisdiction` with the statement "No rules snapshot is available for {state}; only TX is supported". `TX` with no matching evidence gives `evidence_unavailable`. | 12.8 |
| F7-5 | Two existing tests use `CA` as the unsupported example: `test_non_tx_external_findings_unsupported_jurisdiction` and `test_external_only_claim_is_indeterminate`. | 12.13, 12.18 |
| F7-6 | `params.jurisdiction` accepts only `state` and `locality_code`. Finance requires two letters, lease checks only that the length is 2. Quote claims carry no date. | 12.19 |
| F7-7 | `Status` has no `UNVERIFIED` member. `Finding.reason` is a free string, also in OpenAPI. | 12.20 |
| F7-8 | The 225.00 documentary-fee amount rests on OCCC bulletin B16-5, an agency document. `docs/B7_TEXAS_SPEC.md` marks the amendment status of the rule as unchecked. The rule text is not a source. | 12.11 |
| F7-9 | The adapter returns bytes, a URI and a media type only, so `EvidenceDTO.retrievedAt` can only be the acquisition time (inferred). Showing the source retrieval date needs a contract-visible field. | 12.14 |

### D7.3 Design decisions

| ID | Decision | Alternative rejected | Why |
|---|---|---|---|
| DD7-1 | Two tiers. The legacy tier (`TX.json`, `MANIFEST.json` Texas entry, `rules.py`, `sources.py`, the Texas branches of `claim_type.py`, the Texas tests) keeps its bytes. New jurisdictions use format `vk-rules/2`. Texas gets an additive sidecar only. | Migrate `TX.json` to the new format. | F7-3: a new `TX.json` changes every Texas verdict hash (12.13). |
| DD7-2 | A reviewer enters each value, window and excerpt from the official text. Tools only verify. | Extract values with a tool or a model. | 12.6. |
| DD7-3 | Only `fetch` uses the network and a clock. `verify`, `build` and the loader are pure functions of files. | A build that stamps the time. | 12.16, 2.2. |
| DD7-4 | Rule statuses `VERIFIED`, `UNVERIFIED`, `AMBIGUOUS`, `UNSUPPORTED`. Authority classes `BINDING_LAW` and `AGENCY_GUIDANCE`. Only a `VERIFIED` rule of class `BINDING_LAW` reaches `SUPPORTED` or `REFUTED`. | Treat any official page as law. | Guidance is not binding law. |
| DD7-5 | `UNVERIFIED` is a rule status. The finding is `INDETERMINATE` with a reason code. | A new `Status` member. | F7-7. A new member is a contract event. |
| DD7-6 | The claim states an as-of date. A rule applies on `effective_from <= as_of < superseded_on`. No wall clock. | Default to the snapshot date. | A default can refute a quote from before the rule existed. |
| DD7-7 | Retrieval age is shown and gated in CI. It never changes a verdict. | Expire snapshots by wall clock. | Replay must give the same hash on any date. |
| DD7-8 | Snapshots are immutable and versioned. Rollback is a reviewed change to a pointer in the manifest. | Edit in place. | Bundles and history stay intact. |
| DD7-9 | Order: Texas completion, California, Florida, New York. A jurisdiction that fails the gate is recorded `BLOCKED`. | Add all at once. | 12.17, 12.18. |

### D7.4 Rule model, statuses and findings

**Jurisdiction identifier.** `US-` plus the two-letter code in upper case (`US-CA`). The claim keeps `jurisdiction.state`, and the loader maps `state.upper()`. **Rule families**, each only where an Official_Source states it: `STATE_TAX_RATE`, `LOCAL_TAX_RANGE` (minimum and maximum computed with `Decimal` from a published table, never typed), and `DOC_FEE` with the kinds of `rules.py` (`STATUTORY_MAXIMUM`, `PRESUMED_REASONABLE_AMOUNT`, `NO_STATUTORY_LIMIT`). Lease external findings stay `INDETERMINATE` with `not_applicable_lease_tax_model`, as for Texas.

**Authority class.** The reviewer sets it from the source text. The default is `AGENCY_GUIDANCE` unless the source shows that it is a statute or an adopted rule. A rule carries no `value` unless it is `VERIFIED` (12.5).

| Condition | Rule status | Finding |
|---|---|---|
| Every check of D7.5 passes, class `BINDING_LAW`, review recorded | `VERIFIED` | `SUPPORTED`, `REFUTED` or `CONDITIONAL` by `Decimal` comparison |
| Host not official, non-200, 30 s timeout, error page or app shell, excerpt absent, unsupported media type, no stated effective date, bytes not stored | `UNVERIFIED` | `INDETERMINATE`, `rule_unverified` |
| Only `AGENCY_GUIDANCE` supports the value | `UNVERIFIED` | `INDETERMINATE`, `rule_unverified` |
| Identical bytes under two URIs, no reviewer approval | `UNVERIFIED` (quarantined) | `INDETERMINATE`, `rule_unverified` |
| Recomputed hash, manifest or review does not match | unavailable | At acquisition the adapter serves no evidence and the finding is `INDETERMINATE`, `evidence_unavailable`, as for Texas. In the examination, a snapshot that fails its own check gives `evidence_integrity`. |
| Two readings, or two `BINDING_LAW` sources disagree on value or overlap in time | `AMBIGUOUS` | `INDETERMINATE`, `conflicting_sources` or `rule_ambiguous`, both excerpts cited |
| Guidance contradicts a `VERIFIED` rule | unchanged | The `VERIFIED` rule decides. The guidance is listed as a note. |
| The rule needs a filing or document VerdictKit cannot obtain | `VERIFIED` | `INDETERMINATE`, `missing_filing:<id>`, never `REFUTED` (12.9) |
| No snapshot or no `ACTIVE` snapshot for the jurisdiction | `UNSUPPORTED` | `INDETERMINATE`, `unsupported_jurisdiction`, no evidence item |
| No as-of date, or as-of outside every window | none | `INDETERMINATE`, `as_of_date_required` or `rule_not_in_effect` |
| Locality unstated and the rate varies (12.10) | `VERIFIED` | Sweep from minimum to maximum inclusive as `DEFAULT_POLICY`, bounds in the finding |

Existing codes stay: `unsupported_jurisdiction`, `evidence_unavailable`, `requires_regulator_filing`, `not_applicable_lease_tax_model`. Evidence missing or refused at acquisition for a supported jurisdiction gives `evidence_unavailable`. Evidence that reaches the examination and fails its own check gives `evidence_integrity`. No model output, memory or secondary site is a source (12.6, 12.20).

### D7.5 Official sources and evidence records

**Host registry** `rules/v2/official_hosts.json` (canonical JSON, empty at design time). Each entry: `jurisdiction`, exact `host`, `basis` (the page where that jurisdiction publishes or links the host), `reviewed_by`, `reviewed_on`. A host of another jurisdiction does not count. A contractor-operated host is accepted only if a page of the jurisdiction designates it, and `basis` cites that page. Accepted URIs use `https`, the default port, no userinfo and no IP literal. The host is compared in lower-case ASCII (IDNA applied) by exact match, never by suffix. A redirect is followed only to another registry host, at most 3 times, and the final URI is recorded. Otherwise the result is `HOST_NOT_OFFICIAL`, no snapshot is created and the rule is `UNVERIFIED` (12.1).

**Evidence record** (12.2, 12.15): `evidence_id`, `uri`, `retrieved_on` (UTC date), `http_status`, `byte_count`, `sha256` (64 lower-case hex), `media_type`, `excerpt` (verbatim, 1 to 2,000 characters), `excerpt_sha256`, `rights` (`REDISTRIBUTABLE` or `NOT_ESTABLISHED`) and `bytes_file`. Retrieved bytes are stored at `rules/v2/bytes/<sha256>` when `rights` is `REDISTRIBUTABLE`. Without stored bytes the rule is `UNVERIFIED` (`source_bytes_not_stored`), because 12.7 needs a recomputable hash (OD-D7-1).

**Verification (12.3).** 1. Status is 200 and the host check passes. 2. The media type is `text/html`, `application/xhtml+xml` or `text/plain`. Other types, including PDF, give `media_type_unsupported` (OD-D7-2). 3. Decode as UTF-8, reject invalid bytes. For HTML collect the text nodes outside `script` and `style` with `html.parser` and unescape entities. Normalise to NFC and collapse whitespace. Apply the same normalisation to the excerpt. 4. The excerpt must occur in the text. An error page or a script-rendered shell fails here. 5. Every value of the rule must equal, as `Decimal`, a numeral token in the excerpt. This catches typing errors only, not wrong meaning (R-D7-1). 6. Group the evidence of one jurisdiction by `sha256`. A group with two or more URIs rejects all of them (12.4) until a review record names the group. The loader repeats steps 3 to 6 on the stored bytes (12.7).

### D7.6 Snapshot update, review and rollback

| Stage | Command (`scripts/rules_snapshot.py`) | Network or clock | Result |
|---|---|---|---|
| Plan | A reviewer writes `rules/v2/plan/<ID>.plan.json`: per rule the uri, excerpt, value, window, class and rights. | none | Reviewed input |
| Fetch | `fetch <ID>` with a 30 s limit per source, no cookies, fixed request headers, at most 4 MiB (ASSUMED) | network and date | Evidence records and bytes. One Evidence_Ledger record per fetch: command, status, byte count, SHA-256 (12.15). |
| Verify | `verify <ID>` | none | D7.5 checks. Failures are listed with `rule_id` and code. |
| Build | `build <ID>` | none | `rules/v2/<ID>.<seq>.json` and manifest entry. Canonical JSON, sorted lists, LF, no time read. |
| Review | A person writes `<ID>.<seq>.review.json` with `snapshot_sha256`, `approved_by` and `approved_on`. | none | The agent cannot create or waive it. |
| Promote | A reviewed commit sets `active` in `rules/v2/MANIFEST.json`. | none | New runs use it. |

**Determinism.** Equal plan, evidence records and bytes give byte-identical output on both hosts. `build` takes `retrieved_on` from the fetch record and reads no clock. `.gitattributes` gains `apps/quote-autopsy/src/quote_autopsy/rules/v2/** -text`, because its present `-text` line for `quote_autopsy/rules/*.json` does not match subfolders.

**Manifest** `rules/v2/MANIFEST.json`: `active` per jurisdiction, and per snapshot its SHA-256, review file and hash, and status `ACTIVE`, `SUPERSEDED`, `SUSPENDED` or `WITHDRAWN`. Also the SHA-256 of the host registry. The adapter checks the manifest and the review record when a case acquires evidence. `examine` and `findings` read only the embedded evidence, so replay never consults the manifest.

**Rollback.** A new reviewed commit sets `active` to the earlier sequence number and marks the later one `WITHDRAWN` with a reason. No snapshot file is edited or deleted. A bundle embeds its evidence, so a bundle written under the withdrawn snapshot still replays offline (D7-AC-9). `SUSPENDED` stops new runs for a jurisdiction and gives `unsupported_jurisdiction`.

### D7.7 Effective dates and stale evidence

**Dates.** `YYYY-MM-DD` only, parsed with `datetime.date.fromisoformat` and a strict pattern, no zone, no time. The window of a rule is `[effective_from, superseded_on)`. A stated last day D is stored as `superseded_on` = D plus one calendar day. A rule with no stated effective date is `UNVERIFIED` (12.19). The claim states the date in the new optional key `params.jurisdiction.as_of` (OD-D7-3). Legacy Texas ignores it.

**Selection.** Among `VERIFIED` rules of one family whose window holds `as_of`: exactly one applies. Two with different values are `conflicting_sources`. Two with equal values apply once. None, because the date is before the first window, after the last without a successor, or inside a gap, gives `rule_not_in_effect`.

| Stale case | Behaviour |
|---|---|
| Hash, manifest, review or host registry mismatch at load | Source unavailable. `evidence_integrity`. No value is used (12.7). |
| Retrieval date old | Shown next to each finding that relies on it (12.14). `check-fresh --today <date> --max-age-days <N>` lists `STALE` snapshots. It reads no clock, because the date is an argument. The default `N` is 180 (ASSUMED, OD-D7-6). The verdict does not change. |
| Rule superseded | The successor applies by date. Without a verified successor the result is `rule_not_in_effect`. |
| Source page changed after retrieval | The stored bytes still decide. A new fetch that differs is recorded as `source_changed`, and a new snapshot follows the pipeline. |

### D7.8 Texas completion and jurisdiction order

1. **TX-1.** The owner retrieves the text of 7 TAC §84.205 from the Texas Secretary of State (12.11), or the sidecar records it `UNVERIFIED` with the reason. The 225.00 treatment and every Texas finding stay unchanged either way. A text that contradicts the amount makes the sidecar entry `AMBIGUOUS`, stops D7 and goes to the maintainer (12.11 and 12.13 conflict in that case).
2. **Texas sidecar** `rules/v2/US-TX.legacy-evidence.json`. For each of the four sources in `TX.json` it repeats `uri` and `sha256_of_source` and adds media type, excerpt, class and stated effective date, or marks the item `UNVERIFIED`. A newly fetched hash that differs is recorded as `source_changed_since_snapshot`. The verdict path never reads the sidecar. Texas rules rest on agency documents (F7-8), and the sidecar says so (R-D7-2).
3. **Order.** Texas completion, then California, Florida, New York. Each uses the pipeline and passes `gate <ID>`: criteria 12.1 to 12.16, plus the four outcome tests of 12.12. A jurisdiction with no verified rule in a family stays unsupported. A failed gate is recorded `BLOCKED`. The next jurisdiction starts only after the maintainer confirms (OD-D7-4).

### D7.9 Acceptance criteria

All rows are UNVERIFIED until an Execution_Record exists. Date and rule fixtures use a fictional jurisdiction `US-ZZ` and are labelled constructed (`verdict-integrity.md` rule 8).

| ID | Criterion | Method | Pass threshold | Req |
|---|---|---|---|---|
| D7-AC-1 | Texas preserved | `git diff 84df25c` over `TX.json`, `rules/MANIFEST.json`, `rules.py`, `sources.py`. The Texas test file. Verdict hash of one Texas claim at `84df25c` and at the candidate. | 0 changed lines in the four files. All Texas tests pass. Equal verdict hashes. The test file differs only by the hunk of B-D7-1, if approved. | 12.13 |
| D7-AC-2 | Unsupported jurisdictions | `ZZ`, a code absent from the manifest, a `SUSPENDED` and a `WITHDRAWN` jurisdiction, claims with no `ACTIVE` snapshot. `C`, `CAL` and `C1` in a finance claim at intake. | `INDETERMINATE` with `unsupported_jurisdiction`, 0 evidence items, internal findings equal to the plain run. Malformed finance codes give `SchemaError`. | 12.8, 12.20 |
| D7-AC-3 | Contradictory evidence | Overlapping windows with different values. Equal values. Identical bytes under two URIs. Guidance against a `VERIFIED` rule. | `conflicting_sources` with both evidence ids. One application for equal values. Both URIs rejected and no use until a review names the group. The `VERIFIED` rule decides and the guidance is a note. | 12.4, 12.20 |
| D7-AC-4 | Effective-date boundaries | Windows `[2025-01-01, 2026-07-01)` and `[2026-07-01, open)`. As-of 2024-12-31, 2025-01-01, 2026-06-30, 2026-07-01. A gap of one day. A stated last day 2027-12-31. Leap day 2028-02-29. Malformed dates. The clock patched to two dates. | `rule_not_in_effect`, old, old, new. Exactly one rule at each boundary. Gap gives `rule_not_in_effect`. `superseded_on` is 2028-01-01. Malformed dates, including 2027-02-29, give `SchemaError`. 2028-02-29 is accepted. 0 differing bytes between clock settings. | 12.19 |
| D7-AC-5 | Official host | Look-alike suffix, other jurisdiction's host, punycode, userinfo, IP literal, `http`, redirect to an unlisted host, exact registry host. A local fake fetcher. | 7 of 7 give `HOST_NOT_OFFICIAL` and no snapshot. The exact host passes. | 12.1 |
| D7-AC-6 | Retrieval verification | Excerpt present. Error body with status 200, script shell, status 404 and 500, a 30 s stall, PDF, a value not in the excerpt. | Only the first passes. The rest are `UNVERIFIED` with no value and no snapshot. One ledger record per fetch. | 12.2, 12.3, 12.5, 12.15 |
| D7-AC-7 | Load integrity | Flip one byte in the snapshot, each evidence file, the review record, the host registry and the manifest. Remove the review record. | `evidence_integrity` or no use, 0 `SUPPORTED` and 0 `REFUTED`. | 12.7 |
| D7-AC-8 | Deterministic update | Run `build` twice, on both hosts, with the clock patched. Rebuild with no input change. | 0 differing bytes. Manifest unchanged. | 12.16, 2.2 |
| D7-AC-9 | Rollback | Promote sequence 2, write a bundle, roll back to 1. | New runs use 1. Sequence 2 file unchanged. The bundle replays `REPRODUCED` offline. | 12.16 |
| D7-AC-10 | Four outcomes | For each added jurisdiction one test each for `SUPPORTED`, `REFUTED`, `CONDITIONAL`, `INDETERMINATE`, expected values computed with `Decimal` from the snapshot. A scan for `float`. | 4 of 4, 0 `float`. Where a jurisdiction cannot produce an outcome, the test uses a `US-ZZ` fixture and says why (OD-D7-7). | 12.12 |
| D7-AC-11 | Locality | Locality unstated, stated and in the table, stated and absent. | Sweep over the full range with bounds listed. Exact rate. `unknown_locality`. | 12.10 |
| D7-AC-12 | Missing filing | A rule that needs a filing. | `missing_filing:<id>`, never `REFUTED`. | 12.9 |
| D7-AC-13 | Offline equality | Launcher that fails any non-Unix `connect`, against an unrestricted run. | Equal findings. 0 outbound connections. | 12.16 |
| D7-AC-14 | Freshness | `check-fresh` with two dates and the clock patched. | `STALE` listed as expected. Verdict bytes unchanged. | 12.14 |
| D7-AC-15 | Texas sidecar | URIs and hashes against `TX.json`. 84.205 retrieved or `UNVERIFIED`. | 4 of 4 match or are flagged. No Texas finding changes. | 12.11, 12.17 |
| D7-AC-16 | Order gate | Mark a later jurisdiction `ACTIVE` while an earlier one is neither `ACTIVE` nor `BLOCKED`. | The gate refuses. | 12.17, 12.18 |
| D7-AC-17 | No invented fact | Every `VERIFIED` value against its excerpt. A scan of documents and UI text. | 0 values without a matching excerpt. 0 support statements without a `SUCCEEDED` record. | 12.6, 3.10 |
| D7-AC-18 | Display and contract | UI test for label text and the retrieval date next to a finding. The added fields classed as compatible or breaking. | Date shown. Classification present in D5.12 form. | 12.14 |
| D7-AC-19 | Replay of older bundles | A bundle that holds the legacy finding, produced from `84df25c` in a disposable worktree, replayed with the candidate | `DIVERGED`, integrity `VERIFIED`, and the release notes name the change (G-D7-2). A candidate-made bundle replays `REPRODUCED`. | 12.13, 2.8 |

### D7.10 Open decisions, blockers, risks and traceability

| ID | Item | Recommendation |
|---|---|---|
| B-D7-1 | Adding California conflicts with F7-5 and with 12.13. The first of the two tests fails once California is supported (no as-of date gives `as_of_date_required`), and the second may change (UNVERIFIED). D4-AC-2 forbids edits to the Texas test file. | Maintainer approval of a one-token edit `CA` to `ZZ` in each test that needs it, and an amended D4-AC-2. Otherwise California waits. |
| B-D7-2 | No source was retrieved. A jurisdiction cannot be `VERIFIED` until the owner approves network retrieval and a reviewer approves each snapshot. | Process blocker. D7 builds no snapshot. |
| OD-D7-1 | Store source bytes in the repository (12.7). Repository size and rights are UNVERIFIED. | Store them when `REDISTRIBUTABLE`. Otherwise the rule is `UNVERIFIED`. |
| OD-D7-2 | PDF excerpt checks. Raw PDF bytes cannot hold the excerpt. | Not supported now. A pinned text extractor is a later decision. |
| OD-D7-3 | As-of date input | New optional key `params.jurisdiction.as_of` and a UI field. Contract-visible, so classified under D5.12 (G-D7-1). |
| OD-D7-4 | Order handling after `BLOCKED` | Continue only with maintainer confirmation. |
| OD-D7-5 | The statement "only TX is supported" becomes false once any jurisdiction is added, and it is hashed (F7-3). Options: (a) new text without the clause, or (b) keep the text and accept a false sentence. | (a): "No rules snapshot is available for {state}", same reason. The release notes state the effect of G-D7-2. |
| OD-D7-6 | Default `N` for the freshness check and whether it fails a release gate | 180 days (ASSUMED). Report only, until the maintainer sets a gate. |
| OD-D7-7 | An outcome a real jurisdiction cannot produce | Use the `US-ZZ` fixture and record the reason. |
| OD-D7-8 | Later migration of Texas to the new format | Not in this phase. It changes hashes. |
| G-D7-1 | Contract-visible items for D5.12: `as_of` and a snapshot retrieval date on the evidence DTO | Classify each. Batch with the D5 event. |
| G-D7-2 | Under OD-D7-5 (a), every bundle written earlier that holds the legacy unsupported-jurisdiction finding replays `DIVERGED` with integrity `VERIFIED`, for every non-Texas state and not only the new ones, because `statement` is hashed. The earlier release published such bundles only if a user made them (no such bundle is committed). | Release notes and D7-AC-19. |
| R-D7-1 | A reviewer can mistype a value or misread a text. The numeral check catches only typing. | Review record. A second look is advised. |
| R-D7-2 | Texas rules rest on agency documents. The new tier is stricter. | The sidecar states it. Verdicts unchanged (12.13). |
| R-D7-3 | The host registry rests on a reviewer's judgement of `basis`. | Visible, reviewed and hash-pinned. |
| R-D7-4 | Snapshots are point-in-time copies. | Displayed (12.14) and checked for age. |

**Files for implementation (not changed now).** New `rules_v2.py` and `sources_v2.py` in `apps/quote-autopsy/src/quote_autopsy/`; `claim_type.py` (dispatch for non-Texas states, the `as_of` key, the new adapter and source id, the changed unsupported statement; no Texas function is edited); `scripts/rules_snapshot.py`; `rules/v2/` data; `.gitattributes`; `docs/REGULATORY_SNAPSHOTS.md`; new tests under `tests/integration/`. Not changed: `TX.json`, `rules/MANIFEST.json`, `rules.py`, `sources.py`, `docs/B7_TEXAS_SPEC.md`, the Texas tests (except B-D7-1 if approved).

**Traceability.** 12.1: D7.5, AC-5. 12.2, 12.3, 12.5: D7.5, AC-6. 12.4: D7.5, AC-3. 12.6: DD7-2, AC-17. 12.7: D7.5, D7.6, AC-7. 12.8: D7.4, AC-2. 12.9: D7.4, AC-12. 12.10: D7.4, AC-11. 12.11: D7.8, AC-15. 12.12: AC-10. 12.13: DD7-1, AC-1, AC-19. 12.14: D7.7, AC-14, AC-18. 12.15: D7.6, AC-6. 12.16: D7.6, AC-8, AC-9, AC-13. 12.17: D7.8, AC-15, AC-16. 12.18: D7.8, AC-16. 12.19: D7.4, D7.7, AC-4. 12.20: D7.4, AC-2, AC-3. Every criterion of Requirement 12 maps to at least one D7 section and one acceptance row.

### D7.11 Maintainer decisions on open items (conditional approval)

The maintainer approved D7 conditionally. Each decision below is DECIDED and DESIGNED. No source was retrieved, no snapshot was built and no test was run for D7. Text in D7.1 to D7.10 is unchanged. Where a decision here differs from that text, this section governs.

| ID | Decision | Effect on D7 text |
|---|---|---|
| AM-D7-1 | B-D7-1 is decided: a targeted fixture edit, `CA` to `ZZ`, in `test_non_tx_external_findings_unsupported_jurisdiction` (`tests/integration/test_quote_b7_texas.py`), in `test_external_only_claim_is_indeterminate` (`tests/api/test_http_run_lifecycle.py`), and in any other test that a search for the literal shows uses `CA` only as an unsupported-jurisdiction example. Only the jurisdiction code literal changes; name, purpose and every assertion stay. `ZZ` is permanently unsupported, guarded by a test that fails if `ZZ` ever appears in the supported set. | D7-AC-1 and D4-AC-2 are amended: the Texas test file and `test_quote_b7_texas.py` differ from the baseline only by this hunk, which is recorded as a fixture-data change and not a loosening (12.21, 12.13). |
| AM-D7-2 | Read-only retrieval of official regulatory sources is authorized for implementation: HTTPS GET only, hosts only from the reviewed registry, no authentication, payment, cloud provisioning or new account. Each retrieval is its own Execution_Record. The retrieval of 7 TAC §84.205 (TX-1) may be done under this authorization. Review and promotion of every snapshot stay human records the agent cannot write. | B-D7-2 is partly resolved: retrieval is approved, review stays pending. Nothing was retrieved while writing this design or this amendment (12.22). |
| AM-D7-3 | Historical replay is preserved by version-aware Examination_Semantics. A bundle records the Examination_Semantics id under which it was produced; a bundle with no id is `legacy-1`. Replay selects the semantics only from the bundle, never from the current registry or manifest. A `legacy-1` bundle needs no new field and stays byte-identical to the baseline; the id sits in integrity-covered bytes; it reaches the examiner inside the task so isolation holds; the custodian assigns it and a claim cannot choose it; an unknown id gives `UNVERIFIABLE`. The legacy unsupported-jurisdiction statement text stays under `legacy-1`; the new wording of OD-D7-5(a) applies only under a newer id. The carrier (a manifest key plus a task key, or an adapter id) is chosen at implementation under these constraints (new item OD-D7-9). | G-D7-2 and D7-AC-19 are replaced: every bundle of a corpus produced from `84df25c` replays with the candidate to a verdict hash equal to the hash recorded in that bundle and the status `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, never `DIVERGED` or `UNVERIFIABLE`, for Texas, a non-Texas legacy finding, Lease, Reel and the stub type. A replay in the image that wrote a bundle keeps the status `REPRODUCED`. The contract-visible Examination_Semantics field is classified under AM-D5-12's 2.0.0 event (12.23, 12.13). |
| AM-D7-4 | Regulatory source artifacts are preserved where the source's terms permit: bytes under `rules/v2/bytes/<sha256>`, SHA-256, retrieval date, stated effective dates, URI, final URI, HTTP status, media type, the `Content-Type`, `ETag` and `Last-Modified` headers when present, and the retrieval tool's name and version. Offline verification recomputes hashes, checks excerpt containment and checks date windows with no network. Where terms do not permit storage, only the hash, the verified excerpt and `rights: NOT_ESTABLISHED` are kept, the rule is `UNVERIFIED`, and the owner may hold the bytes privately. | OD-D7-1 is decided as recommended. OD-D7-2 (PDF extraction) stays undecided (12.24). |

**Not decided in this review.** OD-D7-2, OD-D7-4, OD-D7-6, OD-D7-7, OD-D7-8 and the risks R-D7-1 to R-D7-4 stay open with the recommendations of D7.10. OD-D7-1 and OD-D7-5 are decided above (AM-D7-4 and AM-D7-3). OD-D7-3 and G-D7-1 are classified under AM-D5-12.

**Traceability.** AM-D7-1: 12.21, 12.13. AM-D7-2: 12.22. AM-D7-3: 12.23, 12.13. AM-D7-4: 12.24.

## D8. P7 Threat-model-driven security and property testing, BE-1 and BE-2 remediation

### D8.1 Scope and status

**Covers.** Requirement 13 (13.1 to 13.28): the Threat_Model, the BE-1 and BE-2 remediation designs, and the property, adversarial, isolation, plugin-provenance, cross-user, replay-determinism, canary and fail-closed-start-up test designs. It also carries the detailed security design for criteria that Requirements 1, 2, 3, 7, 8, 9 and 11 gained in their final amendment round (1.19, 2.13, 2.14, 3.11 to 3.14, 7.19 to 7.22, 8.20, 9.21, 11.16 to 11.18), where those criteria are controls rather than product behaviour.

**Does not cover.** Implementation, infrastructure provisioning, cloud spending, the content of any External_Review_Record, the actual virtual machine or account behind a Contained_Hook_Environment (an owner action), release-verification mechanics (the P8 design, D9.3 to D9.9), and any California, Florida or New York rule value.

**Status.** Everything in D8 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. Facts marked F8-n come from a read-only inspection on 2026-11-25 (Windows host) and are UNVERIFIED for Requirement 3 until an Execution_Record exists. Source: `docs/next-phase/D8_D10_WORKING_NOTES.md`. No workspace was trusted, no hook ran, no container was built, no key was created and no network call was made while writing this section.

### D8.2 Inspected baseline and findings

Read: `deploy/entrypoint.sh`, `examiner/{worker.py,client.py}`, `api/server.py` (`SafetyMiddleware`, `_replay`), `core/src/verdictkit/{bundle.py,mcp_server.py}`, `.github/workflows/{p0-integration.yml,m3b-api-checks.yml}`, the Evidence_Ledger records and `core/pyproject.toml`.

| # | Finding (read) | Req |
|---|---|---|
| F8-1 | `as_custodian` runs `setpriv ... env -i ... ${VK_VAULT_KEY:+VK_VAULT_KEY="$VK_VAULT_KEY"} "$@"`; `serve`, `gate-http` and `gate-case` call `as_custodian env VK_VAULT_KEY="$vault_key" ...`, so the key is an argument of `env` processes. `serve` starts the examiner before the custodian. Container `/proc/<pid>/cmdline` is world-readable by default (UNVERIFIED, D8 tests it). No `set -x`. The root entrypoint holds the key for its lifetime (R-1). | 7.20 |
| F8-2 | The examiner's environment list is `PATH, HOME, LANG, PYTHONHASHSEED, PYTHONDONTWRITEBYTECODE, VK_EXAMINER_SOCKET, VK_EVIDENCE_DIR, VK_ISOLATION`, plus optional `VK_SOURCES_CONFIG` and `VK_CLAIM_TYPES`. No judge-mode or profile variable reaches the examiner (G-D6-1). The worker refuses to start only when `VK_VAULT_KEY` is present. | 7.19, 7.20 |
| F8-3 | `examiner/worker.py`: `conn, _ = srv.accept()` with no peer check, serial handling, no per-connection read timeout. The socket directory is mode 2750, owner `vk-examiner`, group `vk-ipc`; the entrypoint sets the socket to group `vk-ipc` mode 660 after bind. | 2.14 |
| F8-4 | `examiner/client.py`: `SocketExaminer(expected_peer_uid=None)` connects with no check and reports UNENFORCED; with a uid it checks `SO_PEERCRED` at construction and on each connection. `isolation_enforced()` is `False` off Linux. `startup_checks` refuses judge mode unless ENFORCED. | 2.13, 7.19 |
| F8-5 | `SafetyMiddleware.dispatch` reads the whole body into a bytearray (cap 8 MiB for `/replays`, 256 KiB otherwise), copies it into `request._body`, and only then does `replay_upload` try `replay_slots` (`BoundedSemaphore(2)`). | 7.21 |
| F8-6 | `_replay` passes the shared `evidence_dir` as `evidence_root` when isolation is ENFORCED; `bundle.replay_bundle` restores hash-checked embedded evidence there through `EvidenceStore`, so uploaded content enters the store that live cases use. | 7.22 |
| F8-7 | `mcp_server._bundle_path` accepts any path with `expanduser().is_file()` and size at most 8 MiB. Symlinks, `..`, UNC paths and reparse points are followed. No containment. | 9.21 |
| F8-8 | BE-2: `tests/ui/test_judge_preview.py` hard-codes `api_port = 65534` and a 2 s client timeout; `scripts/serve_judge_ui.py` opens an `HTTPConnection` with a 10 s timeout and maps `OSError`, `ValueError` and `HTTPException` to 502. A refused connection to a closed loopback port was observed to take about 2 s on Windows; this is a hypothesis, NOT established. | 13.12, 13.26 |
| F8-9 | `p0-integration.yml` has `workflow_dispatch` and two Ubuntu jobs (`security-and-regression`, `web-ui`); `security-and-regression` runs the lock check, `ruff`, the startup tests, the full non-isolation pytest, the Docker build, the four container gates, offline replay and `scripts/gate_nov22.sh`. No Windows job exists. | 13.15 |
| F8-10 | The raw record file `records.jsonl` held user-profile paths in 4 command fields. Raw logs are git-ignored; only their hashes are published. | 3.11, 3.14 |
| F8-11 | Ledger rows E-009, E-012 to E-014, E-020, E-023 and E-024 abbreviate their command field (`...`, `<gate>`, "Hook_Set command") and carry no Execution_Index identifier, although the canonical raw records hold the exact command text. | 3.12 |
| F8-12 | `requires-python >=3.12`; the Dockerfile pins `python:3.12-slim`; CI uses `setup-python 3.12`. `os.mkdir(mode=0o700)` applies a Windows access list only from CPython 3.12.4, and the same change landed in the 3.11 line at 3.11.10 and in the 3.13 line at 3.13.0 (python.org release notes); this project supports 3.12 and later only. | 13.11, 13.25 |
| F8-13 | BE-2 evidence is two Windows runs; no Linux per-test run exists. An image-based run is invalid because `ui/` is absent from the image. | 13.13, 1.19 |
| F8-14 | `mcp` is locked at `2.3.0`; `core/pyproject.toml` still states `mcp>=1.2`, superseded by AM-D4-6 and confirmed by AM-D4-8. | 9.22 |
| F8-15 | Earlier design text delegated to D8: the Threat_Model rows for cross-owner access, resource exhaustion, log leakage and sweeper correctness (D2.1); residual risks R-1 and R-2 (D2 B-9, AM-5); the BE-2 root cause, instrumentation and port configuration (D3.9 BE2-1 to BE2-6); the Python minimum (OD-D3-4); and the MCP bundle root (R-D4-3). | 13.1, 13.12, 13.19, 13.25 |
| F8-16 | `gh workflow run` against a branch needs the workflow file to exist on the default branch; `GITHUB_SHA` on a dispatched run is the tip of the dispatched ref. Relevant to the P8 design, which owns the dispatch procedure (D9.3 DD9-4, D9.4 VM-10) and the head-SHA check (D9-AC-9). Recorded here because it was read during this work. | 14.20 |

### D8.3 Design decisions

| ID | Decision | Rejected alternative | Why |
|---|---|---|---|
| DD8-1 | The Threat_Model (D8.4) has one row per threat; every row names a control and either a test id or `UNTESTED` with a reason. | A narrative threat list with no row-level test mapping. | 13.1 to 13.3 require it. |
| DD8-2 (M-1) | The vault key is never a process argument. The root entrypoint writes it with shell builtins to a custodian-owned, mode-0400 file on tmpfs, unsets the variable, starts the examiner with the closed list of F8-2, and the custodian reads the file once (`VK_VAULT_KEY_FILE`), validates owner and mode, and removes it. `VK_VAULT_KEY` in the environment stays supported for non-container runs. | Passing the key through the environment of every child, as today. | F8-1, F8-2: argv and non-custodian environ are readable through `/proc` by other local processes. |
| DD8-3 (M-2) | Uploaded replay content never enters the trusted evidence root. Each replay gets a server-generated namespace (`^[0-9a-f]{32}$`) under a separate replay root, removed in `finally`, with orphans swept at start. Metadata stays in custodian-private scratch. The examiner reads a namespace read-only through a validated namespace key and re-hashes on read. A per-replay and a total replay byte quota apply. | Restoring replay evidence directly into the shared `evidence_dir`, as today. | F8-6: uploaded content enters the same store live cases use. |
| DD8-4 (L-7) | Admission before buffering: a process-wide semaphore (`VK_MAX_CONCURRENT_UPLOADS`, default 2) is taken before the first body read. No slot gives 429 `RATE_LIMITED` with `Retry-After` after headers only. One buffered copy, not two. A total body deadline frees slow slots; the slot releases on disconnect and on error. | Checking the semaphore after the body is already buffered, as today. | F8-5: the body is fully buffered, with a second copy, before any slot check. |
| DD8-5 (L-6) | `VK_MCP_BUNDLE_ROOTS` plus the private working directory are resolved and pinned once. NUL, relative, UNC, `\\?\`/`\\.\`, alternate-data-stream and alias names are rejected. POSIX opens components with `O_NOFOLLOW` and `dir_fd`; Windows rejects a reparse point below the root and re-checks the final path of the opened handle. File type and size are verified on the opened handle, not the path. One `PATH_NOT_ALLOWED` code, one shared helper reused by the scaffold destination and the replay scratch. | Validating the path string, then opening by name, as today. | F8-7: symlinks, `..`, UNC paths and reparse points are followed (R-D4-3). |
| DD8-6 (L-3) | `requires-python` stays `>=3.12`. The BE-1 Windows helper fails with `UNSUPPORTED_PYTHON_PATCH` (not a skip) on 3.12.0 to 3.12.3. `mcp_server._workdir()` self-checks the new directory on Windows and refuses to start with `PRIVATE_DIR_UNSAFE` on failure. Elevation state is recorded. The resolved patch version joins release provenance. | Bumping `requires-python` to `>=3.12.4` (lock churn), or accepting a weaker ACL silently on an old patch release. | F8-12: the Windows ACL behaviour of `os.mkdir` only exists from 3.12.4; silent acceptance would violate the fail-closed intent of 13.11. |
| DD8-7 (L-3) | The Windows oracle for BE-1 is O1 (exact structural access-list allowlist), required and sufficient. O2 (`GetEffectiveRightsFromAclW`, AM-D3-2(b)) is dropped. O3 (`AuthzAccessCheck`) is a timeboxed spike, adopted only if it agrees with O1 on six constructed access lists in at most 120 lines with no new dependency. | Keeping AM-D3-2(b)'s effective-rights call as the check. | Microsoft's own reference for `GetEffectiveRightsFromAcl` (D8.5) documents the gaps O1 avoids. |
| DD8-8 | BE-2: instrumentation fields, hypotheses H1 to H5, a standalone `connect_ex` probe, and a fix rule that is never "raise the timeout" alone. | Raising the client or bridge timeout and calling BE-2 fixed. | 13.12 forbids treating a longer timeout alone as a verified fix. |
| DD8-9 (H-1) | Private_Original files stay outside the published tree, byte for byte, SHA-256 published. The Sanitized_Copy is published with its own SHA-256, produced by ordered exact-string rules with placeholders; the redaction manifest lists rule ids and counts, never values. A zero-hit scan over the defined classes gates every commit that publishes evidence or documents. | Scrubbing by rewriting git history. | A force push is not permitted; the one earlier application (`records.jsonl`, F8-10) stays a recorded residual. |
| DD8-10 (L-1) | Isolation_Mode is fixed at process start (S1 to S7): ENFORCED is mandatory once a socket is configured; only an absent socket in the local profile gives UNENFORCED, always labelled; the public profile refuses UNENFORCED at start; losing the examiner mid-run fails the request closed without changing the mode; a replay never overrides its own recorded mode. | A mid-run fallback to in-process examination on socket failure. | 2.13 forbids a runtime downgrade or upgrade and requires fail-closed on examiner failure. |
| DD8-11 (L-2) | The examiner authenticates the custodian: `SO_PEERCRED` is matched against the uid of `vk-custodian`, resolved by name at worker start, never from a request or environment value. A refused peer is closed unread, logged by a fixed code only. The worker refuses to start if the account cannot be resolved. The socket mode is set by umask before the first accept. A per-connection read deadline applies. | Accepting any peer (today's behaviour) or trusting a uid passed in the request. | F8-3: no peer check exists today; 2.14 requires a custodian-only service. |
| DD8-12 | Security_Profile propagation is AM-D6-4's design (D6.11); D8 owns only the tests for it (D8.12). | Redesigning profile propagation inside D8. | Avoids a second design for the same mechanism. |
| DD8-13 (M-6) | An External_Review_Record is kept outside the repository by the owner or an independent reviewer. The repository keeps only a reference (record id, SHA-256, date, verdict, commit, reviewed-file hashes), ledger type `OWNER_ATTESTED`. A changed reviewed file voids the record. The agent cannot create or waive it. | Letting the agent author or self-certify the review. | 13.27 requires a record the agent cannot write. |
| DD8-14 (M-7) | Complexity budget: no new runtime dependency; one shared containment helper, one profile resolver, one key mechanism, one upload-admission mechanism, one sanitizer rule list; every new control maps to a Threat_Model row or is removed. Not built: a plugin sandbox, online revocation, MCP signing, dual contract serving, a replay queue, an ACL framework, a second evidence service. | A bespoke mechanism per surface (for example separate path-safety code for MCP and for the scaffold). | 13.28 requires each mechanism once; the unbuilt items are YAGNI. |
| DD8-15 (M-5, L-5) | Contained_Hook_Environment, CE-1 to CE-8: a dedicated VM or restricted account with no cloud, signing or vault credential and no access to the owner's profile; a push-disabled clone with a closed environment list; pinned, recorded tool versions; blocked outbound traffic where the platform allows it, else a recorded residual; hash-pinned hook files, matcher corpus, environment list and `mcp.json`; the clone refreshed only from a reviewed commit; evidence leaves only as Kiro-captured originals plus sanitized excerpts with hashes; the environment's class recorded without names. Absent CE-1, hooks stay at ST-3 and nothing counts as automatic execution. | Firing hooks directly in the maintainer's main workspace or account. | 8.20 and 3.13 require a contained environment and preserved, non-reconstructed evidence. |

### D8.4 Threat_Model

One row per threat (13.1). `docs/next-phase/THREAT_MODEL.md` is built from this table at implementation and is not written now. Status is TESTED when a test id exercises the control; UNTESTED carries a non-empty reason (13.3). Test ids point to the matrices of D8.5 to D8.12 or to an existing acceptance row.

| ID | Asset, principal, entry point | Threat | Control | Test ID | Status | Reason |
|---|---|---|---|---|---|---|
| T8-1 | Outcome data; Examiner process; the task object | Outcome leakage to the Examiner | `BlindedTask` carries no outcome field (D6.7 CS-03) | `tests/contract/test_blinding.py` (P2 and P3, baseline, rerun in the baseline rerun set); D6-AC-10 and D6-AC-11 are deferred with PH6-01 | TESTED | — |
| T8-2 | Vault key; root entrypoint, custodian; env, argv, fd, files, logs | Vault key exposure | DD8-2 key-file mechanism | KT-1 to KT-8 | TESTED | — |
| T8-3 | Bundle ledger; any holder of a Bundle; `ledger/ledger.jsonl` | Ledger tampering | Hash-chain and manifest checks in `_integrity`; D8.7 mutation guard | D8-AC-14 | TESTED | — |
| T8-4 | Case evidence; replay client; uploaded Bundle | Evidence substitution | DD8-3 replay-namespace isolation and re-hash on read | RI-1 to RI-8 | TESTED | — |
| T8-5 | Bundle parser; any Bundle source; zip entries | Bundle zip bombs | `MAX_BUNDLE_ENTRIES`, `MAX_BUNDLE_UNCOMPRESSED`, `MAX_ENTRY_UNCOMPRESSED` (baseline) | Z-1, Z-2 | TESTED | — |
| T8-6 | Bundle parser; any Bundle source; zip member names | Bundle path traversal | `_check_zip_safety` name checks (baseline) | Z-7, Z-8, Z-9 | TESTED | — |
| T8-7 | API routes; any client; request body | Malformed API input | Schema validation, `SafetyMiddleware` (baseline) | D8-AC-19 | TESTED | — |
| T8-8 | API routes; any client; request body | Oversized API input | Body size caps (baseline); UA matrix | UA-2, UA-3 | TESTED | — |
| T8-9 | API routes; any client; request rate | Rate-limit evasion | Existing 429 limiter (D2 DD2-6) | D2-AC-8 | TESTED | — |
| T8-10 | Storage; replay client; uploaded Bundle | Replay of uploaded bundles consuming storage | DD8-3 per-replay and total replay byte quotas | RI-7, RI-8 | TESTED | — |
| T8-11 | Signature; any Bundle holder; signature envelope | Signature forgery | Ed25519 validation, small-order and non-canonical rejection (D5 AM-D5-1 to AM-D5-3) | D8-AC-13 | TESTED | — |
| T8-12 | Trust_Store; any Bundle holder; key id | Key substitution | `key_id = SHA-256(pubkey)`, Trust_Store lookup by id (D5.6, D5.7) | D5-AC-8 | TESTED | — |
| T8-13 | Trust_Store file; operator; file system | Trust_Store tampering | Malformed or unreadable store gives `NOT_EVALUATED` (D5.7) | D5-AC-8 | TESTED | — |
| T8-14 | MCP tool results; MCP client; `path` argument | MCP path leakage | Fixed `PATH_NOT_ALLOWED` message, no path echoed (DD8-5) | PR-1 to PR-23 | TESTED | — |
| T8-15 | MCP tool results; MCP client; error object | MCP error leakage | Sanitizer, fixed messages, no `exc_info` (D4.4, AM-D4-7) | D4-AC-4 | TESTED | — |
| T8-16 | Examination outcomes; a loaded plugin; the loader | Plugin code reaching outcomes | Examiner process isolation, `BlindedTask` (D6.8 T-P6); AM-D6-3 provenance binding | — | UNTESTED | Deferred scope (owner scope freeze, OA-00, D10.12): the plugin controls and their tests (D6-AC-10, PD-1 to PD-12) belong to the deferred PH6-01, PH6-03 and PH6-04, and no test exists. The baseline loader is the known limitation KL-1. |
| T8-17 | Regulatory snapshot; any Bundle holder; `rules/` files | Regulatory snapshot substitution | Snapshot and manifest hash checks, duplicate-URI rejection (D7.5, DD7-1) | — | UNTESTED | Deferred scope (owner scope freeze, OA-00, D10.12): the snapshot loader v2 and its test (D7-AC-7) belong to the deferred PH6-06, and no test exists. The Texas snapshot of the baseline is unchanged. |
| T8-18 | Replay metadata; replay client; index and URI fields | Replay metadata poisoning | DD8-3: metadata kept in custodian-private scratch, re-hashed on read | RI-5, RI-6 | TESTED | — |
| T8-19 | Upload buffer memory; any client; concurrent uploads | Concurrent upload exhaustion | DD8-4 admission-before-buffering semaphore | UA-1 to UA-8 | TESTED | — |
| T8-20 | Examiner socket; any local process; the connecting uid | Custodian impersonation | DD8-11 `SO_PEERCRED` check against the resolved `vk-custodian` uid | CA-1, CA-2, CA-6 | TESTED | — |
| T8-21 | Isolation_Mode; the running process; runtime state | Isolation downgrade | DD8-10 S1 to S7 (fixed at start, fail-closed) | IS-1, IS-2, IS-5 | TESTED | — |
| T8-22 | Plugin allowlist; the loader; installed files | Plugin provenance substitution | AM-D6-3 provenance manifest, verify-before-import | — | UNTESTED | Deferred scope (owner scope freeze, OA-00, D10.12): the provenance manifest and its tests (PD-2, PD-5) belong to the deferred PH6-04, and no test exists. KL-1 applies. |
| T8-23 | Claim-type registry; two distributions; `type_id` | Duplicate `type_id` | AM-D6-2 reject-all rule | — | UNTESTED | Deferred scope (owner scope freeze, OA-00, D10.12): the reject-all rule and its test (PD-1) belong to the deferred PH6-03 and PH6-04, and no test exists. KL-1 applies. |
| T8-24 | File system below an Approved_Root; MCP client; `path` | MCP root escape | DD8-5 safe-open helper | PR-1 to PR-23 | TESTED | — |
| T8-25 | Published evidence and documents; the publishing commit; files to publish | Evidence publication leak | DD8-9 Private_Original/Sanitized_Copy, sanitizer rule list | D8-AC-22 | TESTED | — |
| T8-26 | Evidence_Ledger; the agent; Execution_Record command field | Ledger command misreport | F8-11 ledger lint (no placeholder, Execution_Index id required) | D8-AC-23 | TESTED | — |
| T8-27 | Hook evidence; the hook runner; the firing environment | Hook execution containment | DD8-15 CE-1 to CE-8; absent containment forces `UNVERIFIED` | D8-AC-25 | TESTED | — |
| T8-28 | CI run; the dispatcher; the ref and head SHA | CI dispatch ref confusion | The run's `headSha`, `headBranch`, `event` and `status` are read from the CI service and must equal the Release_Candidate SHA, the Phase_Branch, `workflow_dispatch` and `completed`; a mismatch records `FAILED` and discards the run (DD9-4, VM-10) | D9-AC-9 | TESTED | — |
| T8-29 | Dependency versions; the maintainer; `uv.lock` | Dependency drift | Exact pin and `uv lock --check` (AM-D4-8); crypto-vector rerun on dependency change | D4-AC-18 | TESTED | — |
| T8-30 | Case data; another owner; routes carrying a case id | Cross-owner access | Ownership check on every case-related route (D2.12 AM-6) | D2-AC-25, CU-1 to CU-4 | TESTED | — |
| T8-31 | Evidence blobs; the sweeper; the sweep interleaving | Sweeper deleting a live blob | Lock and live-reference derivation (D2.12 AM-9) | D2-AC-28 | TESTED | — |
| T8-32 | Logs; any process; log output | Log leakage | DD8-2 key handling, DD8-9 sanitizer, privacy-safe logging (D2 DD2-9) | KT-5, PC-1 to PC-6 | TESTED | — |
| T8-33 | Security_Profile; custodian and examiner processes; start-up | Profile mismatch between processes | AM-D6-4 profile resolver and registry-digest check | FC-3, FC-4 | TESTED | — |
| T8-34 | Vault key; root entrypoint process; process lifetime | R-1: the root entrypoint process holds the key for its lifetime | None; the process that passes the key on must briefly hold it | — | UNTESTED | Accepted residual risk (D2 B-9): no test can show the absence of access by a process that must have access to do its job. |
| T8-35 | Network namespace; Examiner process; container networking | R-2: the Examiner shares the network namespace with the custodian, so egress is not separable per OS user | A negative egress test from the examiner uid (D2 AM-5) | D2-AC-23 | TESTED | Accepted residual risk (D2 B-9): the test is a negative probe, not a guarantee; if it cannot show the connection is blocked, R-2 stays accepted with this reason. |

### D8.5 Detailed designs

**BE-1 closure (resolves 13.11 and 13.25; reconciles 2.11 and 8.13 with 13.11).** D3.9 (BE1-1 to BE1-8) already designed a two-branch test: the POSIX assertion (BE1-1) keeps its exact text and runs on every POSIX host; a new Windows branch (BE1-2, BE1-3) asserts the same access-only-to-the-current-user-and-system-principals property with Windows ACL calls. Criteria 2.11 and 8.13 forbid loosening, skipping or `xfail`-marking the existing assertion; 13.11 requires adding a Windows assertion and forbids a skip on the platform branch. These do not conflict: the platform branch (`if os.name == "posix": ... else: ...`) is not a `skip` decorator and does not touch the POSIX line, so the unchanged POSIX text and the added Windows text each execute unconditionally on their own platform. The AST guard (BE1-5) and the new guard test that 13.11 requires both fail if the POSIX comparison is later removed, weakened or marked. Until the Windows branch is implemented and passing, the test keeps failing on Windows exactly as today, and 8.13 requires every hook to report that failure unchanged. After BE1-2 and BE1-3 land and D8-AC-5 passes, a further Windows failure of this test is a new regression under 1.13, not BE-1.

**Windows oracle (DD8-7, amends AM-D3-2(b), closes OD-D3-4 jointly with the next item).** AM-D3-2(b) directed an effective-rights call such as `GetEffectiveRightsFromAclW`. Microsoft's own reference states that this function may be altered or become unavailable in a later release and directs callers to the Authz API instead, and that it ignores implicit owner rights, privileges and logon-session groups such as Authenticated Users, and fails on an inherited deny entry ([Microsoft Learn, `GetEffectiveRightsFromAcl`](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-geteffectiverightsfromacla)). DD8-7 drops it. Three oracles were compared: **O1**, an exact structural allowlist over the access list itself (protected, no inherited entry, allow entries only, trustees limited to the owner SID, OWNER RIGHTS, SYSTEM and Builtin Administrators, none for Everyone, Authenticated Users, Builtin Users or Guests); **O2**, the dropped effective-rights call; **O3**, `AuthzAccessCheck` against a synthetic client context, Microsoft's documented method for effective-access evaluation ([Checking Access with the Authz API](https://learn.microsoft.com/en-us/windows/win32/secauthz/checking-access-with-authz-api)), built from `AuthzInitializeContextFromSid`, which may itself attempt an S4U logon or query the account object for group membership ([`AuthzInitializeContextFromSid`](https://learn.microsoft.com/en-us/windows/win32/api/authz/nf-authz-authzinitializecontextfromsid)). **Decision:** O1 is required and sufficient for BE-1 closure, because it is exact for a directory this project creates and needs only two `ctypes` calls. O3 is a timeboxed spike (`S-AUTHZ`, OD-D8-5), adopted only if it agrees with O1 on six constructed access lists, including an Everyone entry and an inherited entry, in at most 120 lines with no new dependency; otherwise the record states `NOT_ADOPTED` with the reason, and its absence does not block BE-1 closure. The negative controls of BE1-6 (an added Everyone entry; an inherited allow entry; a Builtin Users entry) must each fail O1.

**Python minimum (DD8-6, closes OD-D3-4, part of 13.25).** `requires-python` stays `>=3.12` (no lock churn). Windows needs CPython 3.12.4 or later before `os.mkdir(mode=0o700)` restricts the directory on Windows at all; this shipped as a security fix (CVE-2024-4030) on the 3.11 line at 3.11.10 ([Python 3.11.10 release notes](https://www.python.org/downloads/release/python-31110/)) and is the same fix D3.9 cites for 3.12.4. Content from the Microsoft and Python pages cited above was rephrased for compliance with licensing restrictions. The BE-1 Windows helper fails with `UNSUPPORTED_PYTHON_PATCH`, not a skip, on 3.12.0 to 3.12.3. `mcp_server._workdir()` self-checks the directory it just created on Windows and refuses to start with `PRIVATE_DIR_UNSAFE` if the check fails, so the fail-closed rule holds even on a host with an old patch release. Elevation state is recorded, because an elevated process's owner may resolve to Administrators (CPython issue 157876, cited in D3.9). The image's resolved Python patch version joins release provenance (14.17).

**BE-2 closure (DD8-8, closes 13.12, 13.13 and 13.26).** Instrumentation, with UTC and monotonic timestamps: client send, bridge accept, upstream-connect start and end with the exception class and errno, response write, client first byte, total duration; at least 30 trials per host class; the minimum, median and maximum are reported. **Hypotheses:** H1, a refused loopback connect takes about 2 s on Windows; H2, another process owns port 65534 or filtering software delays the connect; H3, the bridge's `ThreadingHTTPServer` thread model adds delay; H4, the client socket timeout accumulates connect and read time; H5, the delay is test-only. A standalone `connect_ex` probe to a closed loopback port on both hosts discriminates H1 without the rest of the bridge. The Linux leg needs a full checkout, because the container image has no `ui/` (F8-8), so it runs on a Linux_Docker_Host or in CI. **Fix rule:** if H1 is confirmed, bound the bridge's upstream connect with a dedicated timeout below the client's deadline (default 1.0 s, override `VK_BRIDGE_CONNECT_TIMEOUT`); keep the 10 s read timeout and the test's own 2 s client timeout unchanged; replace the hard-coded port 65534 with a port allocated at run time (override `VK_TEST_CLOSED_PORT`, which satisfies 1.17). If H1 is not confirmed, the actual root cause is recorded and a different fix follows. A longer timeout alone is never accepted as the fix (13.12). Closure needs 30 of 30 passes on both hosts with `-rA` and the direct exit code (13.13). **Attribution wording (1.19):** until the Linux run exists, every mention of BE-2 keeps the phrase "observed on Windows" and states no cause; D0.5's wording rule is unchanged by this closure design.

**Key channel (DD8-2, closes 7.20, part of 13.16).** Property: for all start-ups, a search of argv, non-custodian environ, inherited descriptors, examiner-readable files and logs for the vault key, in raw, base64, hex and URL-encoded form, finds 0 matches (P-n). Sequence, because order matters here: (1) the root entrypoint writes the key with shell builtins to a custodian-owned, mode-0400 file on tmpfs; (2) it unsets `VK_VAULT_KEY`; (3) it starts the examiner with the closed environment list of F8-2; (4) the custodian reads the file once through `VK_VAULT_KEY_FILE`; (5) it validates the file's owner and mode; (6) it removes the file. `VK_VAULT_KEY` in the environment stays supported for non-container runs.

| ID | Case |
|---|---|
| KT-1 | Poll `/proc/<pid>/cmdline` of every process at 1 ms resolution across 20 start-ups |
| KT-2 | Read the environ of every process other than the custodian and the root entrypoint |
| KT-3 | Read `/proc/<pid>/fd` of the examiner for an inherited descriptor |
| KT-4 | A bounded file-system search as the `vk-examiner` uid |
| KT-5 | Read the logs of every process |
| KT-6 | Run the entrypoint under `bash -x` in a test copy and read the trace |
| KT-7 | Trigger a crash and read its output |
| KT-8 | Aggregate: 0 matches across KT-1 to KT-7, each checked in raw, base64, hex and URL-encoded form |

Pass: 0 matches in every case (13.16, D8-AC-8).

**Replay isolation (DD8-3, closes 7.22, part of 13.17 and 13.18).** Properties: the trusted evidence root's file list and file hashes are identical before and after a replay (P-h's scope extended to replay namespaces); a replay namespace is removed in `finally` even on error.

| ID | Case |
|---|---|
| RI-1 | Trusted-root file list and hashes identical before and after one replay |
| RI-2 | Replay content is written only under the replay root, never under the trusted evidence root |
| RI-3 | The namespace is removed in `finally`, including on an injected mid-replay failure |
| RI-4 | An orphaned namespace from a killed process is swept at the next start |
| RI-5 | The examiner can read its own replay namespace through the namespace key, and cannot read another one |
| RI-6 | A re-hash on read that disagrees with the embedded hash rejects the replay |
| RI-7 | A replay beyond the per-replay byte quota is rejected |
| RI-8 | A sequence of replays beyond the total replay quota is rejected |

Pass: 0 differences in RI-1; 0 cross-namespace reads in RI-5 (7.22, 13.17, D8-AC-9).

**Upload admission (DD8-4, closes 7.21, part of 13.18).** Property: for all sequences of concurrent upload requests, the bytes held for upload bodies never exceed the number of slots multiplied by the request cap plus 2 MiB (P-i).

| ID | Case |
|---|---|
| UA-1 | No byte of the request body is read before a slot is taken |
| UA-2 | No free slot gives 429 `RATE_LIMITED` with `Retry-After` after headers only |
| UA-3 | Peak extra memory across N concurrent uploads is at most `slots x cap + 2 MiB` |
| UA-4 | A slot releases when the client disconnects mid-upload |
| UA-5 | A slot releases when the request fails after the slot is taken |
| UA-6 | A total body deadline frees a slot held by a slow sender |
| UA-7 | 0 partial files remain after a failed or aborted upload |
| UA-8 | The same admission mechanism serves every upload route, not only `/replays` |

Pass: the bound of UA-3 holds in every trial; 0 partial files in UA-7 (7.21, 13.18, D8-AC-10).

**Approved_Root (DD8-5, closes 9.21, part of 13.19).** Property: for all path strings submitted to the helper, it either opens a file inside an Approved_Root or returns `PATH_NOT_ALLOWED`, and never opens a file outside every Approved_Root (P-j). At least 20 cases per 13.19, plus a race test and Windows-only cases.

| ID | Case | ID | Case |
|---|---|---|---|
| PR-1 | `..` traversal segment | PR-11 | Alternate data stream name |
| PR-2 | Symbolic-link path component | PR-12 | Windows reserved device name |
| PR-3 | Embedded NUL character | PR-13 | Trailing dot or space |
| PR-4 | Relative path | PR-14 | Absolute path outside every root |
| PR-5 | UNC path (`\\host\share`) | PR-15 | Empty string |
| PR-6 | Device path (`\\.\`) | PR-16 | Mixed path separators |
| PR-7 | Device path (`\\?\`) | PR-17 | Case-variant of an allowed path |
| PR-8 | Drive-relative path (no root) | PR-18 | Unicode-normalization variant of an allowed path |
| PR-9 | Path exceeding the platform length limit | PR-19 | A symlink created after the check, before the open (TOCTOU, single case) |
| PR-10 | Name with a Windows alias (short 8.3 name) | PR-20 | The private working directory itself (positive control) |
| PR-21 | Race: 1000 iterations changing the path between the check and the open | | |
| PR-22 | Windows junction below the root | | |
| PR-23 | Windows reparse point below the root | | |

Pass: `PATH_NOT_ALLOWED` for every disallowed case; 0 opens outside an Approved_Root across all 1000 PR-21 iterations (9.21, 13.19, D8-AC-11).

**Isolation semantics (DD8-10, closes 2.13, part of 13.24).**

| ID | Case |
|---|---|
| IS-1 | Isolation_Mode is read once at start; a later attempt to change it has no effect |
| IS-2 | A configured examiner that fails a request fails the request closed; the mode is unchanged; the request is not served in-process |
| IS-3 | Local profile, no `VK_EXAMINER_SOCKET`: mode is UNENFORCED, and every output labels it |
| IS-4 | Public profile start-up with a resolved mode of UNENFORCED refuses to start |
| IS-5 | The examiner is lost mid-run (socket closed): the request fails closed, the mode is unchanged |
| IS-6 | `SocketExaminer` with no expected uid is refused in the public profile |
| IS-7 | Replaying a bundle recorded under one mode reports the replay's own mode, never the bundle's recorded mode, as the current mode |
| IS-8 | Combined matrix: every (profile, socket-present, examiner-health) combination yields the mode the rule of DD8-10 predicts |

Pass: 8 of 8 (2.13, 13.24, D8-AC-18).

**Custodian authentication (DD8-11, closes 2.14, part of 13.17.)**

| ID | Case |
|---|---|
| CA-1 | A connection from the `vk-custodian` uid is served |
| CA-2 | A connection from any other uid is closed unread, with a fixed log code only |
| CA-3 | The `vk-custodian` account cannot be resolved at worker start: the worker refuses to start |
| CA-4 | The socket mode is correct from the first accept (set by umask before `bind`, not adjusted afterward) |
| CA-5 | A per-connection read deadline disconnects a slow peer |
| CA-6 | The expected uid is resolved by name only, never taken from a request field or an environment value |
| CA-7 | `SO_PEERCRED` unavailable on the platform refuses the connection rather than accepting it |

Pass: 7 of 7 (2.14, 13.17, D8-AC-18).

**Publication rule (DD8-9, closes 3.11, 3.14).** The redaction methodology itself (the ordered exact-string rules, their placeholders and the rule-id/count-only manifest) is specified in `docs/next-phase/EVIDENCE_REDACTION.md`, a file this design does not create; it is written separately. D8's contract is the gate: 0 hits of the defined sensitive classes (user-profile paths, repository-root paths, user names, host names, e-mail addresses, non-loopback addresses, secrets, key blocks) before any commit publishes evidence or a document (3.14), with each Private_Original's SHA-256 published separately from its Sanitized_Copy's SHA-256 (3.11), and the Execution_Index mapping each pair (1.14). One past application exists already (`records.jsonl`, F8-10); because a force push is not permitted, that earlier published text is a recorded residual and not retroactively fixed.

**Ledger reconciliation (F8-11) and BE-2 attribution wording.** The lint that D8-AC-23 runs checks: (a) no Execution_Record command field contains an ellipsis, an angle-bracket placeholder or a descriptive stand-in (3.12); (b) every Execution_Record cites the Execution_Index identifier of its canonical raw record (3.12); (c) the counts a record states equal the counts of the canonical row it cites; (d) a sentence that attributes BE-2 to a cause uses "observed on `<host>`" only, never a cause, until the BE-2 closure above produces a diagnosis (1.19). Reconciliation of the specific rows F8-11 names (E-009, E-012 to E-014, E-020, E-023, E-024) is a text correction, not a re-run: each abbreviated command field is replaced by the exact command text taken from the canonical raw record identified by its Execution_Index id; no new Execution_Record is fabricated, because the command already ran and only its recorded text was abbreviated.

### D8.6 Property tests

Library: Hypothesis (Python), the project's existing choice; D8 adds no new PBT library. Settings for every property below: the `ci` profile, derandomized, `max_examples=200` (at least the 100 that 13.7 requires), one Hypothesis test per property. Each test's docstring cites the property statement and at least one requirement id (13.4, per `.kiro/steering/testing.md`), and carries the comment **Feature: verdictkit-next-phase, Property P-x: `<statement>`**. These tests live under the existing `tests/` tree already collected by `p0-integration.yml` (F8-9), so no workflow file changes; a test needing the container is marked `isolation` and runs only in the container gate (13.8).

| ID | Property ("for all ...") | Req |
|---|---|---|
| P-a | For all Bundles and all byte positions, flipping one byte and verifying the result never yields `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID`. | 13.5(a) |
| P-b | For all cases and clocks, a Bundle written with signing disabled is byte-identical to the baseline writer's output for the same case and clock. | 13.5(b), 10.5 |
| P-c | For all cases, the Verdict_Hash computed with signing enabled equals the Verdict_Hash computed with signing disabled. | 13.5(c), 10.6 |
| P-d | For all MCP error results, the message contains no host path separator (`/` or `\`) taken from the host file-system path. | 13.5(d) |
| P-e | For all claim types produced by the scaffold with no edit, `run_suite` passes every check. | 13.5(e), 11.11 |
| P-f | For all Bundles, replaying the same Bundle twice in the same environment produces byte-identical reports. | 13.22 |
| P-g | For all Bundles in the legacy corpus produced before this phase, replay under the candidate reports a verdict hash equal to the hash recorded in the Bundle and the status `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, never `DIVERGED` or `UNVERIFIABLE`. | 12.23, 13.22 |
| P-h | For all interleavings of put, deduplicated put, freeze, run start, purge, sweep and replay-namespace creation, the sweeper never deletes a blob or a replay namespace that a live case or an in-flight examination references. | 7.25, 13.17 |
| P-i | For all sequences of concurrent upload requests, the bytes held for upload bodies never exceed the number of admission slots multiplied by the request cap plus 2 MiB. | 7.21, 13.18 |
| P-j | For all path strings submitted to the Approved_Root helper, it opens a file only inside an Approved_Root or returns `PATH_NOT_ALLOWED`, and never opens a file outside every Approved_Root. | 9.21, 13.19 |
| P-k | For all inputs, applying the sanitizer twice gives the same output as applying it once, and the output matches none of the defined sensitive classes. | 3.14, 13.23 |
| P-l | For all combinations of `VK_PROFILE`, `VK_JUDGE_MODE` and an unrecognised value, profile resolution is total (it always resolves or refuses to start), and no variable other than the two documented ones changes a `public` resolution to `local`. | 7.19, 13.24 |
| P-m | For all orderings of the same set of entry points, the loader registers the same claim types and rejects the same duplicate `type_id`. | 11.17, 13.20 |
| P-n | For all canary values and all documented sinks, the canary does not appear in the sink's output, including a test's own failure message. | 13.23, 7.20 |
| P-o | For all malformed archive inputs of the Z-1 to Z-16 kinds (D8.7), the loader returns a rejection or `UNVERIFIABLE`, never `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID`, and writes 0 files outside the scratch directory. | 13.6, 13.21 |

### D8.7 Adversarial cryptographic and archive tests

**Cryptographic vectors.** D8 adds no new vector; it reuses D5-AC-6 and the AM-D5-3 list (every small-order encoding, non-canonical encodings including a `y` value at or above the field prime, 31- and 33-byte keys, the all-zero and identity keys, a small-order or non-canonical `R` in an otherwise valid signature, `S+L`, and a universal signature) and adds the run discipline: both host classes, rerun on every `cryptography` version change (13.21), and a mutation guard that disables each check in a copy of the verifier and shows that the vector set then finds at least one failure.

**Archive inventory.** `core/src/verdictkit/bundle.py` lines 261 to 305 (`_check_zip_safety`, `_read_bounded`) were read against the installed interpreter (`python 3.12.10`) together with a probe of the standard-library `zipfile` module's source for overlap, name-mismatch, normalisation and encryption handling. 16 cases, reduced from the longer list of threats by grouping the three stream-corruption cases into Z-16.

| ID | Case | Baseline coverage | New D8 item |
|---|---|---|---|
| Z-1 | Zip bomb by compression ratio | Covered: `MAX_ENTRY_UNCOMPRESSED` (16 MiB) is checked against the declared uncompressed size before any inflate; `_read_bounded` re-checks the actual bytes read | Regression test only |
| Z-2 | Zip bomb by total uncompressed size | Covered: the running total is checked against `MAX_BUNDLE_UNCOMPRESSED` (64 MiB) while scanning `infolist()` | Regression test only |
| Z-3 | Entry count above the limit | Covered: `len(infos) > MAX_BUNDLE_ENTRIES` (4096) | Regression test only |
| Z-4 | Duplicate names | Covered: `name in names` | Regression test only |
| Z-5 | Case-colliding names (`Foo.txt` vs `foo.txt`) | Not covered: `names` is a case-sensitive `set[str]`; both pass | New check: reject a name that matches an existing name case-insensitively |
| Z-6 | Unicode-normalization-colliding names (NFC vs NFD) | Not covered: no normalisation before the set check | New check: compare names after NFC normalisation |
| Z-7 | Absolute names | Covered: `name.startswith("/")` | Regression test only |
| Z-8 | Parent-directory names | Covered: `".." in name.split("/")` | Regression test only |
| Z-9 | Backslash separators | Covered: `"\\" in name` | Regression test only |
| Z-10 | Drive-letter names (`C:evidence/index.json`) | Not covered: no colon check | New check: reject a name containing `:` |
| Z-11 | Alternate-data-stream names (`evidence/index.json:hidden`) | Not covered: same colon gap as Z-10 | Covered by the Z-10 check |
| Z-12 | Reserved device names (`con`, `nul`, `aux`, `com1`, ...) | Not covered | New check: reject a component matching the Windows reserved-name list |
| Z-13 | Trailing dot or space in a component | Not covered | New check: reject a component ending in `.` or a space |
| Z-14 | Symbolic-link member (Unix `external_attr` bit) | Not covered: `_check_zip_safety` never reads `info.external_attr`; members are read in memory and never extracted to disk, which limits live risk, but the entry itself is not flagged | New check: reject an entry whose external attributes mark it a symlink |
| Z-15 | Central/local header name mismatch | Covered indirectly: `zf.open()` raises `BadZipFile` on a name mismatch between the local and central directory headers, caught by `_read_bounded`'s `except` clause (confirmed against the installed interpreter) | Regression test asserting `BundleFormatError`, not a silent pass |
| Z-16 | Overlapping entries, the encrypted flag, or a bad CRC | Covered indirectly: a corrupt or overlapping stream raises `BadZipFile`, `zlib.error` or `EOFError`; an encrypted entry with no password raises `NotImplementedError`; all are caught by `_read_bounded` | Regression test only |

Pass for every Z case: rejection or `UNVERIFIABLE`, never `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID`, 0 files written outside the scratch directory (13.6, 13.21, P-o).

**13.6's seven malformed-input kinds, mapped:** a malformed zip entry (Z-16), a duplicate zip name (Z-4), an absolute member name (Z-7), a parent-directory member name (Z-8), a truncated signature (crypto vectors, reused), a wrong-algorithm signature (crypto vectors, `UNSUPPORTED_ALGORITHM`), a malformed Trust_Store file (D5-AC-8, reused). Each kind has at least one negative test, satisfying 13.6 without duplicating the D5 design.

**13.14's seven adversarial surfaces, mapped:** the API (D2-AC-7 size caps, UA matrix), the MCP_Server (D4-AC-4, PR matrix), Bundle parsing (the Z matrix), the Trust_Store (crypto vectors, D5-AC-8), signature envelopes (crypto vectors), plugin scaffolding (the PD matrix, D8.8), regulatory snapshots (D7-AC-7). Each surface's test asserts a rejection, `INDETERMINATE` or `UNVERIFIABLE` result.

### D8.8 Plugin discovery and provenance tests

| ID | Case |
|---|---|
| PD-1 | Duplicate `type_id` registered by two distributions |
| PD-2 | A rogue distribution whose module name shadows an allowlisted module earlier on the import path |
| PD-3 | An entry-point value that differs from the allowlisted value |
| PD-4 | A version mismatch against the allowlist entry |
| PD-5 | One tampered installed file inside an allowlisted distribution |
| PD-6 | An extra entry point in the `verdictkit.claim_types` group, never imported; its import-canary file stays absent |
| PD-7 | `VK_CLAIM_TYPES` set while the Security_Profile is `public` |
| PD-8 | An import side-effect canary, checked in both the `local` and the `public` profile |
| PD-9 | A permuted order of the same entry points |
| PD-10 | An allowlisted plugin that fails to load |
| PD-11 | A reserved namespace (`quote`, `reel`, `verdictkit`, `vk`) claimed from the wrong distribution |
| PD-12 | A Security_Profile or claim-type registry-digest mismatch between the custodian and examiner processes |

Pass: each case ends in the result that 11.16 to 11.18 and 7.19 require — refused start-up in public mode, or a reported, unregistered collision in local mode, as D6.11 specifies per case (13.20, D8-AC-12).

### D8.9 Cross-user evidence isolation

| ID | Case |
|---|---|
| CU-1 | Owner B reads owner A's case, run, evidence, outcome or events: the same 404 `NOT_FOUND` as a nonexistent case |
| CU-2 | Owner B changes (PATCH-class operation on) owner A's case: the same 404 |
| CU-3 | Owner B opens the SSE stream of owner A's case: refused with the same 404 before any event is sent |
| CU-4 | Owner B downloads or exports owner A's Bundle: the same 404 |
| CU-5 | A replay started by one client cannot read the replay-namespace evidence of another client's replay |
| CU-6 | The `vk-examiner` OS user cannot read the vault, draft files, the key file or another replay's namespace |
| CU-7 | The examiner process cannot write to the trusted evidence root |
| CU-8 | Case ids are 128-bit random, and a route-enumeration test fails if any route carrying a case id lacks an ownership check |

Pass: 0 of N routes in CU-1 to CU-4 return anything but the nonexistent-case response; 0 unchecked routes in CU-8 (7.23, 13.17, D8-AC-9, D8-AC-20).

### D8.10 Deterministic replay

| ID | Case |
|---|---|
| DR-1 | The same Bundle, replayed twice in the same environment, gives byte-identical reports |
| DR-2 | Windows and Linux give equal verdict hashes for the committed corpus |
| DR-3 | The clock is patched to two different dates; the replay result is unchanged |
| DR-4 | `PYTHONHASHSEED` set to `0`, to `1` and to a random value all reproduce identically |
| DR-5 | A signed Bundle and an unsigned Bundle written in the test environment each replay `REPRODUCED`. Every Bundle of the legacy corpus replays to a verdict hash equal to its recorded hash with the status `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, never `DIVERGED` or `UNVERIFIABLE`. The replay makes no network connection (offline socket guard) |
| DR-6 | `DIVERGED` is reported only when integrity is `VERIFIED` and the hashes differ, never when integrity itself fails |

Pass: 6 of 6 (13.22, D8-AC-15).

### D8.11 Privacy and secret canaries

Five canary types, each injected through every applicable entry point (environment variable, argument, claim field, evidence body, file name, MCP argument) and searched for in every sink the Threat_Model names (standard output, standard error, log files, error bodies, diagnostics, Bundles, the evidence index, process listings, pytest failure output), in raw, base64, hex, URL-encoded and JSON-escaped form.

| ID | Canary type |
|---|---|
| PC-1 | The vault key |
| PC-2 | A claimed figure (a monetary or rate value from a claim) |
| PC-3 | A user-profile path |
| PC-4 | An access token |
| PC-5 | A hook environment variable |
| PC-6 | Meta-rule: no test prints its own canary in its failure message |
| PC-7 | The signing private key (a canary key created in memory, never a production key; TPR-M-4) |

Pass: 0 matches for PC-1 to PC-5 and PC-7 across every entry point, sink and form; PC-6 holds for every test in the suite (13.23, D8-AC-16).

### D8.12 Fail-closed start-up and isolation-semantics tests

All FC cases run on a Linux_Docker_Host. Each gives a non-zero exit, a `VK_STARTUP_ERROR=<CODE>` line, no `VK_STARTUP_OK` line, no open listener (port probe) and no file written.

| ID | Case |
|---|---|
| FC-1 | Missing vault key |
| FC-2 | Malformed vault key |
| FC-3 | Unknown Security_Profile value |
| FC-4 | `VK_JUDGE_MODE=1` conflicting with `VK_PROFILE=local` |
| FC-5 | Resolved mode UNENFORCED in the `public` profile |
| FC-6 | Examiner missing (socket not present) |
| FC-7 | Examiner uid mismatch (not `vk-custodian`'s expected peer) |
| FC-8 | Socket mode wrong |
| FC-9 | Peer credentials (`SO_PEERCRED`) unavailable |
| FC-10 | An allowlisted plugin fails to load |
| FC-11 | Invalid evidence directory |
| FC-12 | Unreadable plugin provenance manifest |

Pass: 12 of 12 (13.24, D8-AC-17). The isolation-semantics matrix IS-1 to IS-8 (D8.5, DD8-10) and the custodian-authentication matrix CA-1 to CA-7 (D8.5, DD8-11) cover the runtime side of the same two decisions; together with FC-1 to FC-12 they are the full test set for 13.24, 2.13 and 2.14 (D8-AC-18).

### D8.13 Acceptance criteria

All rows are UNVERIFIED until an Execution_Record exists. "Both" means Windows host and Linux_Docker_Host. "(isolation)" marks a test that needs the container and runs in the container gate (13.8).

| ID | Criterion | Method | Pass threshold | Req | Host |
|---|---|---|---|---|---|
| D8-AC-1 | Threat_Model completeness | Row-by-row check of D8.4 against the named threats | One row per threat, a non-empty value in every column, a reason on every UNTESTED row | 13.1, 13.2, 13.3 | Both |
| D8-AC-2 | Five properties of 13.5 | P-a to P-e under the `ci` profile; mutation guard disabling each underlying check | 200/200 examples hold, and P-a excludes `REPRODUCED`, `REPRODUCED_ACROSS_ENV` and `VALID`; the guard shows a failure once disabled | 13.5 | Both |
| D8-AC-3 | Seven malformed-input kinds | One negative test per kind (D8.7's mapping) | Each kind rejects or returns `UNVERIFIABLE`; 0 `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID` | 13.6 | Both |
| D8-AC-4 | BE-1 POSIX branch | `git diff -w` on the POSIX assertion; BE1-5 AST guard (equal `ast.dump`, no bypass of the replay and explain assertions); Linux run with `-rA` and the direct exit code | 0 changed tokens in the POSIX assertion (indentation excluded); AST guard passes on both hosts and fails on each mutant of D10-AC-14; exit code captured directly. The guard leg is autonomous (PH1-04). The Linux leg is a deferred row (DLV-1, D10.11 TR-1) | 13.11, 2.11 | Windows (guard), Linux_Docker_Host (Linux leg) |
| D8-AC-5 | BE-1 Windows helper | O1 check, BE1-6 negative controls, Python patch recorded, elevation recorded, S-AUTHZ (O3) outcome recorded if run | Passes on a safe directory, fails on each negative control; `UNSUPPORTED_PYTHON_PATCH` on 3.12.0 to 3.12.3 | 13.11, 13.25 | Windows |
| D8-AC-6 | BE-2 instrumentation | Timed trials per DD8-8 | At least 30 trials on each leg, every field populated, min/median/max reported. The Windows leg is autonomous (PH1-08). The Linux leg is a deferred row (DLV-2, D10.11 TR-1) | 13.26 | Both |
| D8-AC-7 | BE-2 root cause and fix | H1 to H5, fix applied per the rule, rerun | 30 of 30 passes on each leg with `-rA` and the direct exit code; port allocated at run time. The Windows leg is autonomous (PH1-09). The Linux leg is a deferred row (DLV-2, D10.11 TR-1) | 13.12, 13.13 | Both |
| D8-AC-8 | Key channels | KT-1 to KT-8 for the vault key and, as the variant KT-S of each case, for a canary signing key (TPR-M-4, D10.11 TR-6) | 0 matches, every case and encoding | 13.16, 7.20 | Linux_Docker_Host (isolation) |
| D8-AC-9 | Replay isolation | RI-1 to RI-8 | Trusted-root list and hashes identical before and after; 0 cross-namespace reads | 7.22, 13.17 | Linux_Docker_Host (isolation) |
| D8-AC-10 | Upload admission | UA-1 to UA-8 | At most `slots` uploads in flight; later requests get 429 before any body byte is read; peak extra memory at most `slots x cap + 2 MiB`; slot releases on disconnect; 0 partial files | 7.21, 13.18 | CI/VM |
| D8-AC-11 | MCP Approved_Root | PR-1 to PR-23 | At least 20 cases rejected with `PATH_NOT_ALLOWED`; 1000-iteration race finds 0 opens outside a root; Windows junction and reparse cases rejected | 9.21, 13.19 | Both (Windows cases: Windows) |
| D8-AC-12 | Plugin discovery and provenance | PD-1 to PD-12 | Each case ends in the result 11.16 to 11.18 require | 13.20, 11.16, 11.17, 11.18 | Linux_Docker_Host (isolation) |
| D8-AC-13 | Adversarial cryptographic vectors | D5-AC-6 and AM-D5-3 vectors, rerun on every `cryptography` change | 0 `VALID` where a vector forbids it; mutation guard finds a failure once disabled | 13.21 | Both |
| D8-AC-14 | Adversarial ZIP Z-1 to Z-16 | D8.7's inventory | Each case rejects or returns `UNVERIFIABLE`, never `REPRODUCED`, `REPRODUCED_ACROSS_ENV` or `VALID`; 0 files outside scratch; mutation guard finds a failure once a covered check is disabled | 13.6, 13.21 | Both |
| D8-AC-15 | Deterministic replay DR-1 to DR-6 | D8.10 | 6 of 6, with every legacy-corpus Bundle at an equal verdict hash and the status `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, never `DIVERGED` or `UNVERIFIABLE` | 13.22 | Both |
| D8-AC-16 | Canaries PC-1 to PC-7 (PC-7, the signing key, was added by TPR-M-4) | D8.11 | 0 matches, every type, entry point, sink and form; PC-6 holds | 13.23 | Linux_Docker_Host (isolation) |
| D8-AC-17 | Fail-closed start-up FC-1 to FC-12 | D8.12 | 12 of 12: non-zero exit, `VK_STARTUP_ERROR`, no `VK_STARTUP_OK`, no listener, no file written | 13.24 | Linux_Docker_Host |
| D8-AC-18 | Isolation semantics and custodian authentication | IS-1 to IS-8, CA-1 to CA-7 | 15 of 15 | 2.13, 2.14, 13.24 | Linux_Docker_Host (isolation) |
| D8-AC-19 | Profile propagation matrix | D2-AC-1's cases extended by AM-D6-4, plus FC-3 and FC-4 | Every combination resolves per AM-D6-4 or refuses to start | 7.19, 13.14 | CI/VM |
| D8-AC-20 | Cross-user isolation CU-1 to CU-8 | D8.9 | 8 of 8 | 7.23, 13.17 | CI/VM |
| D8-AC-21 | Sweeper stateful property, extended | D2-AC-28's stateful test with replay namespaces added | 0 deleted blobs or replay namespaces still referenced, across 200 examples under the `ci` profile | 7.25, 13.17 | CI/VM |
| D8-AC-22 | Evidence publication | Apply the sanitizer twice; scan the published tree; compare hashes with the Execution_Index | Idempotent; 0 class hits in the published tree; every Private_Original hash matches its Execution_Index entry; every Sanitized_Copy hash listed | 3.11, 3.14 | Both |
| D8-AC-23 | Ledger lint | Scan Execution_Record command fields; cross-check Execution_Index ids and counts; scan BE-2 sentences | 0 ellipsis or angle-bracket placeholders; every record cites its Execution_Index id; counts equal the canonical row; 0 BE-2 sentences imply a cause before DD8-8's diagnosis exists | 3.12, 1.19 | Both |
| D8-AC-24 | Kiro evidence preservation | Diff preserved spec files, `.config.kiro` id and session exports against any derived copy; check usage figures | 0 reconstructed items; each Private_Original hash recorded; every usage figure traces to a Kiro usage record or is `NOT_AVAILABLE` | 3.13, 16.2 | Owner (Kiro) |
| D8-AC-25 | Contained_Hook_Environment record | Review the session record against CE-1 to CE-8 | Each condition recorded met, environment class stated without names; an unmet condition keeps dependent hooks at ST-3 / `UNVERIFIED` | 8.20 | Owner (Windows) |
| D8-AC-26 | CI dispatch precondition | Check `workflow_dispatch` on the default-branch workflow file; check a dispatched run's head SHA | Trigger present on the default branch; head SHA equals the Release_Candidate. The run-level check is D9-AC-9 | 14.20 | CI |
| D8-AC-27 | External_Review_Record present | Compare reviewed-file hashes with the Release_Candidate; check authorship | Hashes equal; record attributed `OWNER_ATTESTED`, not the agent | 13.27 | Owner |
| D8-AC-28 | Complexity budget | `uv.lock` diff; map every new control to a Threat_Model row | 0 added runtime packages; every D8.3 control maps to a D8.4 row; an unmapped control is removed | 13.28 | Both |
| D8-AC-29 | Existing tests unmodified | `git diff 84df25c` over the test tree; `ruff check .` on new code | 0 changed lines except the approved BE1-2/BE1-3 hunk (D3.9) and the AM-D7-1 fixture hunks; 0 ruff violations on new code | 13.9, 13.10 | Both |
| D8-AC-30 | Targeted regression, both hosts | Run the regression set touching the changed control on Windows and on a Linux_Docker_Host | Each host's result recorded separately; 0 unexplained divergence | 13.15 | Both |

### D8.14 Independent review findings

The independent review text itself is not stored in this repository; the 15 finding ids below (H-1, M-1 to M-7, L-1 to L-7) are the maintainer's one-line summaries, carried only as ids here, and those summaries are recorded in `docs/next-phase/REVIEW_REMEDIATION_REGISTER.md`; the Response column answers those summaries. The Response column answers the maintainer's one-line summaries, and the mapping of a summary to a code defect stays `UNVERIFIED` where the summary names no concrete example.

| Finding | Response (section) | Rows | Requirement criteria | Mapping |
|---|---|---|---|---|
| H-1 | DD8-9: Private_Original/Sanitized_Copy publication, zero-hit scan | D8-AC-22 | 3.11, 3.14 | UNVERIFIED |
| M-1 | DD8-2: vault key never a process argument, key-file mechanism | D8-AC-8 | 7.20, 13.16 | UNVERIFIED |
| M-2 | DD8-3: replay evidence isolated from the trusted root | D8-AC-9, D8-AC-20 | 7.22, 13.17 | UNVERIFIED |
| M-3 | D8-AC-26's CI dispatch precondition; the full remediation is owned by D9 (DD9-4 and VM-10 for the dispatch procedure, D9-AC-9 for the head-SHA check) | D8-AC-26, D9-AC-9 | 14.20 | UNVERIFIED |
| M-4 | DD8-6, DD8-7: Python minimum and Windows oracle; D3.9's BE-1 design; the requirement reconciliation of 13.11 and 8.13 (D8.5) | D8-AC-4, D8-AC-5 | 13.11, 8.13 | UNVERIFIED |
| M-5 | DD8-15: Contained_Hook_Environment, CE-1 to CE-8 | D8-AC-25 | 8.20 | UNVERIFIED |
| M-6 | DD8-13: External_Review_Record kept outside the repository | D8-AC-27 | 13.27 | UNVERIFIED |
| M-7 | DD8-14: complexity budget, one mechanism per surface | D8-AC-28 | 13.28 | UNVERIFIED |
| L-1 | DD8-10: isolation semantics fixed at start, fail-closed | D8-AC-18 | 2.13, 13.24 | UNVERIFIED |
| L-2 | DD8-11: examiner authenticates the custodian by `SO_PEERCRED` | D8-AC-18 | 2.14, 13.24 | UNVERIFIED |
| L-3 | DD8-6, DD8-7: Python 3.12.4 floor and the O1 Windows oracle | D8-AC-5 | 13.25 | UNVERIFIED |
| L-4 | D8.5's ledger reconciliation (F8-11 lint) | D8-AC-23 | 3.12 | UNVERIFIED |
| L-5 | DD8-15: Kiro authoring and execution evidence preserved, not reconstructed | D8-AC-24 | 3.13 | UNVERIFIED |
| L-6 | DD8-5: MCP Approved_Root, safe-open helper | D8-AC-11 | 9.21, 13.19 | UNVERIFIED |
| L-7 | DD8-4: upload admission before buffering | D8-AC-10 | 7.21, 13.18 | UNVERIFIED |

### D8.15 Open decisions, risks, blockers and traceability

| ID | Item | Recommendation |
|---|---|---|
| OD-D8-1 | Final choice of key mechanism (DD8-2) | The tmpfs key-file, as designed. |
| OD-D8-2 | Replay-namespace carrier (DD8-3) | A server-generated 32-hex-character token, as designed. |
| OD-D8-3 | Default MCP Approved_Root when `VK_MCP_BUNDLE_ROOTS` is unset | The private working directory only. |
| OD-D8-4 | Value of `VK_MAX_CONCURRENT_UPLOADS` and the replay byte quotas | 2 concurrent uploads, 64 MiB per replay (ASSUMED); revisit after D8-AC-10 trial data. |
| OD-D8-5 | Whether to adopt O3 (`S-AUTHZ` spike, DD8-7) | Run the timeboxed spike; adopt only on exact agreement with O1. |
| OD-D8-6 | Which BE-2 hypothesis (H1 to H5) holds, and the resulting fix branch | Run the `connect_ex` probe first; it is the cheapest discriminator. |
| OD-D8-7 | Storage location of External_Review_Records | Owner-controlled, outside the repository; exact location is the owner's choice. |
| OD-D8-8 | Whether to publish sanitized logs alongside the release report | PENDING; no publication is designed here beyond the existing `LOG_HASHES.txt` pattern. |
| OD-D8-9 | Windows firewall rule for CE-4 (Contained_Hook_Environment outbound block) | Owner action; record the residual if not applied. |

| ID | Risk | Reason |
|---|---|---|
| R-D8-1 | An elevated test process's owner may resolve to Administrators rather than the current user (CPython issue 157876), changing the expected O1 trustee set. | Record elevation state in every BE-1 Windows run (BE1-7). |
| R-D8-2 | tmpfs may be absent on a host, affecting the DD8-2 key-file mechanism. | Record the mount check; fall back to a mode-0400 file on another local filesystem if tmpfs is absent, with the fallback recorded. |
| R-D8-3 | GitHub Actions dispatch availability or limits (read for F8-16, owned by D9, R-D9-4). | Recorded here only because it was read during this work; D9 owns the mitigation (DD9-4, R-D9-4). |
| R-D8-4 | The Windows development host may differ from a Windows runner used for CI, affecting BE-1/BE-2 generalisation. | Record the exact Windows version and build with every Windows Execution_Record. |
| R-D8-5 | The sanitizer's rule list (DD8-9) is necessarily finite; an unanticipated sensitive pattern could pass the zero-hit scan. | Scan result is a count, never a claim of completeness; review remains advised (as D7's R-D7-1 notes for its own numeral check). |

| ID | Blocker | What resolves it |
|---|---|---|
| B-D8-1 | A Linux_Docker_Host full-checkout run for BE-2's Linux leg (DD8-8) and for every D8-AC row marked "Both" or a Linux host class | Owner action: provision or use an existing Linux_Docker_Host. |
| B-D8-2 | An External_Review_Record (DD8-13) | Owner or independent-reviewer action; the agent cannot create or waive it. |
| B-D8-3 | A dedicated VM or restricted OS account for the Contained_Hook_Environment (DD8-15, CE-1) | Owner action; without it, hook-firing evidence stays `UNVERIFIED` (D8-AC-25). |

**Files for implementation (not changed now).** New `deploy/entrypoint.sh` key-file handling (DD8-2); new helper module(s) under `tests/contract` or `tests/windows` for the BE-1 Windows oracle (BE1-4, D3.9); edits to `examiner/worker.py` (DD8-11 peer auth) and `examiner/client.py`; edits to `api/server.py` (DD8-3 replay namespace, DD8-4 admission) and `core/src/verdictkit/mcp_server.py` (DD8-5 Approved_Root helper, shared with the scaffold destination); a new provenance-manifest build step and loader check under `core/src/verdictkit/sdk/` (AM-D6-3); new `docs/next-phase/THREAT_MODEL.md` (built from D8.4); new `docs/next-phase/EVIDENCE_REDACTION.md` (written separately, not by this task); new test files under `tests/security/`, `tests/adversarial/` and `tests/contract/` for the KT, RI, UA, PR, IS, CA, PD, CU, DR, PC, Z, FC matrices and the P-a to P-o properties. Not changed: existing passing tests, except the approved BE1-2/BE1-3 hunk (D3.9) and the AM-D7-1 fixture hunks; `examples/`; the API contract (owned by D5).

**Traceability.** 13.1 to 13.3: D8.4, D8-AC-1. 13.4: D8.6 (docstring and tag rule). 13.5: D8.6 P-a to P-e, D8-AC-2. 13.6: D8.7, D8-AC-3. 13.7: D8.6 (settings), D8-AC-2. 13.8: D8.13 Host column (isolation marker). 13.9: D8.14, D8-AC-29. 13.10: D8-AC-29. 13.11: D8.5 (BE-1 closure), D8-AC-4, D8-AC-5. 13.12: D8.5 (BE-2 closure), D8-AC-7. 13.13: D8.5, D8-AC-4, D8-AC-7. 13.14: D8.7 (surface mapping), D8-AC-19. 13.15: D8-AC-30. 13.16: D8.5 (KT), D8-AC-8. 13.17: D8.5 (RI, CA), D8.9 (CU), D8-AC-9, D8-AC-18, D8-AC-20. 13.18: D8.5 (UA), D8-AC-10. 13.19: D8.5 (PR), D8-AC-11. 13.20: D8.8 (PD), D8-AC-12. 13.21: D8.7, D8-AC-13, D8-AC-14. 13.22: D8.10 (DR), D8-AC-15. 13.23: D8.11 (PC), D8-AC-16. 13.24: D8.12 (FC, IS), D8-AC-17, D8-AC-18. 13.25: D8.5 (Windows oracle, Python minimum), D8-AC-5. 13.26: D8.5 (BE-2 instrumentation), D8-AC-6. 13.27: DD8-13, D8-AC-27. 13.28: DD8-14, D8-AC-28. 1.19: D8.5 (BE-2 attribution wording), D8-AC-23. 2.13: D8.5 (IS), D8-AC-18. 2.14: D8.5 (CA), D8-AC-18. 3.11: D8.5 (publication rule), D8-AC-22. 3.12: D8.5 (ledger reconciliation), D8-AC-23. 3.13: DD8-15, D8-AC-24. 3.14: D8.5 (publication rule), D8-AC-22. 7.19: D6.11 AM-D6-4 (mechanism), D8.12 FC-3/FC-4, D8-AC-19. 7.20: D8.5 (KT), D8-AC-8. 7.21: D8.5 (UA), D8-AC-10. 7.22: D8.5 (RI), D8-AC-9. 8.20: DD8-15, D8-AC-25. 9.21: D8.5 (PR), D8-AC-11. 11.16 to 11.18: D6.11 AM-D6-1 to AM-D6-3 (mechanism), D8.8 (PD), D8-AC-12. Every criterion of Requirement 13 and every cross-cutting criterion listed above maps to at least one D8 section and one row.

## D9. P8 Complete end-to-end regression and release verification

### D9.1 Scope and status

**Covers.** Requirement 14 (14.1 to 14.27), Requirement 15 (15.1 to 15.10) and Requirement 16 (16.1 to 16.5), plus the criteria that the release run must show: 1.5, 1.14, 2.8, 3.6 to 3.13, 7.14, 10.12, 10.14, 12.23, 13.9 and 13.27.

**Does not cover.** Implementation and the running of any verification. Any push, tag, merge, publication, cloud resource, spending, DNS record, certificate, public listener or announcement (D9.8). The deployment gates SG-1 to SG-9 and the smoke tests SM-1 to SM-14 of D2.8, which D9 names only as conditions of Public_Deployment_Readiness. The content of an External_Review_Record or of a Kiro capture, which are owner actions.

**Status.** Everything in D9 is DESIGNED and UNVERIFIED. Facts marked F9-n were read on 2026-11-25 (Windows host). No gate was run, no image was built, no CI run was dispatched and no ref was pushed while writing this section. The only network access was reading public documentation pages (the GitHub Docs pages cited in D9.3 and D9.4, and the python.org release notes behind the F8-12 correction). Source: `docs/next-phase/D8_D10_WORKING_NOTES.md`.

### D9.2 Inspected baseline and findings

Read: `.github/workflows/p0-integration.yml`, `scripts/gate_http.py`, `scripts/gate_nov22.sh`, `deploy/entrypoint.sh`, `Dockerfile`, `.gitignore`, `core/src/verdictkit/{bundle.py,envprint.py}`, `uv.lock`, `docs/next-phase/{BASELINE_REPORT.md,EXECUTION_EVIDENCE.md,HISTORICAL_EVIDENCE_RECONCILIATION.md}` and `docs/next-phase/baseline/EXECUTION_INDEX.md`.

| # | Finding (read) | Req |
|---|---|---|
| F9-1 | Baseline on `84df25c` (Windows host, 2026-11-24): ledger rows E-001 to E-026 are the 26 CANONICAL executions of the Execution_Index (45 raw records, 14 superseded duplicates, 5 execution errors; E-025a and E-025b share one run). `pytest -m "not isolation"` gave 444 passed, 2 failed (BE-1, BE-2), 5 skipped, 4 deselected, with 455 tests collected. | 1.14, 14.8, 14.9 |
| F9-2 | Not run at the baseline: Browser E2E (E-027) and `scripts/gate_nov22.sh` (E-028). The five skipped cases (the symlink case in `tests/api/test_m3b_draft_store.py` and four peer-credential cases in `tests/api/test_m3b_examiner_identity.py`) have no Linux result. No Linux per-test baseline exists (E-025a is indirect). No CI run, test inventory or release report exists. | 14.19, 14.22 |
| F9-3 | The four container gates and the offline replay ran on the Docker Desktop Linux engine with `--network none` and exited 0 (E-020 to E-024): 4 isolation tests passed, `VK_STARTUP_OK isolation=ENFORCED`, `GATE-HTTP PASSED`, an unsigned stub Bundle written, replay `REPRODUCED` with authenticity `NOT_ESTABLISHED`. | 14.23 |
| F9-4 | `p0-integration.yml` triggers on pull requests and pushes to `master` and on `workflow_dispatch`, with `permissions: contents: read`. Job `security-and-regression` (30 min): lock check, sync, ruff, startup tests, `pytest -q -m "not isolation"`, `docker build -t verdictkit:p0-ci`, the four gates, replay, `bash scripts/gate_nov22.sh`. Job `web-ui` (20 min): `npm ci`, typecheck, tests, build, Playwright 1.63.0, `bash scripts/ui_e2e.sh`. No Windows job. No step uses `-rA` or `--collect-only`, records `git rev-parse HEAD`, checks `git status --porcelain` or records an image ID. `gate/` is not git-ignored, and `gate_nov22.sh` writes into it inside the clone (`OUT=gate`). That script builds its own image `verdictkit:gate` and expects `REPRODUCED_ACROSS_ENV` for its host-side replay. `m3b-api-checks.yml` has no dispatch trigger. | 14.20, 14.21 |
| F9-5 | `scripts/gate_http.py` (run as `vk-custodian` by `gate-http`) drives `TestClient(create_app())` with isolation ENFORCED: a live-evidence `quote.finance.v1` case (`CONTRADICTED`), a `reel.mechanical.v1` case from the bundled synthetic fixture `fx_reel_impossible_sma` (`IMPOSSIBLE`), a refused live Reel case, and a server-side replay of each downloaded Bundle. No `quote.lease.v1` case exists in any gate or script. It signs nothing (no signing code exists yet), writes no Bundle to a mounted directory and replays inside its own process. `gate-case` and `verdictkit replay` write and replay an unsigned stub Bundle in two container runs. | 14.5, 14.23 |
| F9-6 | `deploy/entrypoint.sh`: `gate-http` and `gate-case` start the examiner under `as_examiner` (socket group `vk-ipc`, mode 660), then run the custodian under `as_custodian env VK_VAULT_KEY=<generated> ...` with `VK_EXAMINER_SOCKET` set. The `verdictkit` subcommand runs `cd /app` and then the installed CLI. Any other command runs as root through `exec "$@"`. `as_custodian` has no signing or Trust_Store variable yet (D5.5 adds them). | 14.5, 14.23 |
| F9-7 | `replay_bundle` reports `REPRODUCED` only if `engine_version`, `python_version` and the SHA-256 of `uv.lock` (read from the working directory) all equal the Bundle's `env_fingerprint`. With an equal verdict hash and any difference it reports `REPRODUCED_ACROSS_ENV`. `uv.lock` records the `mcp` specifier of the `verdictkit` member (`>=1.2` at the baseline) and 9.22 requires another specifier, so the lock hash at S will differ from the hash in a Bundle written at `84df25c`. The baseline tests that replay Bundles accept both statuses (for example `tests/integration/test_bundle_evidence_and_golden.py`). 12.23, 13.22 and 14.24 as amended accept `REPRODUCED` or `REPRODUCED_ACROSS_ENV` for a legacy Bundle with an equal verdict hash, and name `REPRODUCED` for a Bundle replayed in the image that wrote it. | 12.23, 14.24 |
| F9-8 | `Dockerfile`: the base image and the `uv` image are pinned by digest, and `apt-get install` is unpinned, so two builds of one commit give different image IDs. The image holds `core/`, `apps/`, `api/`, `scripts/`, `tests/`, `examples/` and `uv.lock`, not `ui/` or `docs/`. `envprint` reads `VK_IMAGE_DIGEST` and nothing sets it. | 14.17, 14.23 |

### D9.3 Exact-commit rule and design decisions

**Exact-commit rule.** S is the full 40-character SHA of the Phase_Branch tip when the owner selects the Release_Candidate. Every verification runs in a clean checkout of S, and `git rev-parse HEAD` prints S and `git status --porcelain` prints nothing before and after each run (14.21). Windows: `git clone <repo> <clone-w>`, `git -C <clone-w> checkout --detach <S>`, `uv sync --frozen --all-packages --all-extras --group dev`, `npm ci`. Linux: the CI checkout of `GITHUB_SHA`, and a clone of S on the local Linux_Docker_Host. Run output goes to `<out>`, outside every clone. A new commit that is not an Evidence_Commit (D10.11 TR-2) makes a new Release_Candidate, and every verification runs again (DD9-2, 14.21).

| ID | Decision | Rejected alternative | Why |
|---|---|---|---|
| DD9-1 | S is written first in the release run and in every Execution_Record, with the step, Outcome_Class, passed and failed counts, and start and end times (14.1, 14.16). | Verify a branch name or a short SHA. | A branch moves. 14.16 needs the tested, built and described commit to be one commit. |
| DD9-2 | Clean checkout per host and per run (rule above). A commit after S is either a new Release_Candidate or an Evidence_Commit (D10.11 TR-2). An Evidence_Commit changes only the Evidence_Output_Set (and, in `tasks.md`, only the checkbox of PH7-17 and of PH7-18) and is checked by `check-evidence-commit --base <S> --tip <E>`. That check replaces the former path rule over `docs/next-phase/**` and the spec `tasks.md`, which let Test_Inputs change after S (amended by TPR-C-2; OD-D9-1). | Test in the working tree where the code was written. Write run output under `gate/` in the clone. | Uncommitted files would be tested in place of S, and run output would make the tree dirty (F9-4). The ledger is in the repository, so a commit after S cannot be avoided. |
| DD9-3 | Every command runs unpiped. Pytest adds `-rA`. The exit code is read directly. Counts are copied from the runner's summary line. The command text is stored exactly (3.12). | A pipe through `tail`. Counts typed from memory. | E-025a ended in a pipe through `tail`, so its exit code was not pytest's (1.15). 14.8 and 3.12 forbid inferred counts and placeholder commands. |
| DD9-4 | CI by dispatch (VM-10). The run's `headSha`, `headBranch`, `event` and `status` are read from the CI service and must equal S, the Phase_Branch, `workflow_dispatch` and `completed`. A mismatch records `FAILED` and discards the run. Where dispatch is unsupported, or the remote ref is not S and no push is authorized, the CI result is `UNVERIFIED` with that reason. No pull request and no merge. This replaces the pull-request route of D0.3 and D0.9. | Open a pull request to `master` to get a run. | 14.20 forbids it. For a `pull_request` run `GITHUB_SHA` is a merge commit and not S ([GitHub Docs, events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)). |
| DD9-5 | Push rule (14.13). The agent pushes only the Phase_Branch, only when the request that asks for it carries the owner's explicit authorization, and never with force. The ledger cites that request and records `git ls-remote origin refs/heads/feature/kiro-next-phase` before and after. It never pushes `master`, a tag or an image. | A push made because verification needs it. | Authorization is per request. An implied permission is a silent publication. |
| DD9-6 | One image per run. Build once from the clean clone, record `docker image inspect --format '{{.Id}}' <image>`, run every gate and scenario on that image, and read the ID again after the last one. The recorded image digest is this local ID. | Rebuild per gate. Report a registry digest. | Builds are not bit-identical (F9-8). A registry digest needs an image push, which is a publication (14.13). |
| DD9-7 | Linux evidence has two labelled sources: CI (`ubuntu-latest`, full checkout, Linux `-rA`, Browser E2E, `gate_nov22.sh`) and the local Linux_Docker_Host (the Docker Desktop Linux engine on the Windows host, or a Linux VM: image build, gates, scenario, replay matrix). Windows is a separate native run in a fresh clone. One source never stands in for another. | One source for both host classes. | 14.17 records the host class of each run, and the sources differ (R-D8-4). |
| DD9-8 | The end-to-end scenario is one new script `scripts/gate_e2e.py` run by one new subcommand `gate-e2e <out_dir>` that reuses the `cmd_gate_http` set-up. `gate_http.py` is not edited. The signing key is created in memory in the container by the custodian script, written as a 0600 file in the custodian's private directory and removed with the container. `<out>` receives Bundles and a Trust_Store with the public key only. | Extend `gate_http.py`. Provision a key file from the host. | `gate_http.py` is a Baseline_Run step that 14.9 compares, and it has no signing key, mounted output or separate replay run. 14.24 forbids a committed key file (`*.pem` and `*.key` are also git-ignored). |
| DD9-9 | Kiro hook and MCP evidence comes only from output captured inside Kiro, in a Contained_Hook_Environment, by the owner (VM-11). Without a capture the capability is `UNVERIFIED`. | Count H6 or H8 of the Historical_Audit, or a hook command run by the agent. | 14.25 and 3.6. Historical results are not evidence for S (3.9). |
| DD9-10 | One stdlib-only helper `scripts/release_verify.py` with subcommands `inventory`, `diff-inventory`, `check-run`, `frozen`, `provenance`, `report-lint` and `audit-scan`, each with a unit test and a negative control. | One ad hoc script per check, or manual comparison. | 13.28 asks for each mechanism once and no new dependency. A negative control makes each check testable. |

### D9.4 Verification matrix

**Rerun set and hosts.** The rerun set is the Baseline_Run ledger rows E-001 to E-028. Each row runs on every host class where it can run, and its record on any other host class is `UNVERIFIED` with the reason (1.6, 14.4). E-005 reruns as the 30-trial BE-2 loop (D8-AC-7). E-025a and E-025b are replaced by the Linux full-checkout `-rA` run, their valid-environment form (F8-13). Hosts: Windows (native, fresh clone), Linux_Docker_Host (Docker Desktop Linux engine on the Windows host, or a Linux VM), CI (the dispatched run), Owner (owner action). `<clone-w>` and `<clone-l>` are clean clones of S, `<out>` is a directory outside every clone, and `<image>` is the tag `verdictkit:rc-<first 12 characters of S>`.

| ID | What | Host | Command or procedure | Expected | Record |
|---|---|---|---|---|---|
| VM-1 | Exact commit | Both | DD9-2 rule on a fresh clone: `git rev-parse HEAD` and `git status --porcelain`, before and after each run | HEAD prints S. Status prints nothing, 2 of 2 times per run | One per run |
| VM-2 | Rows E-001 to E-018 and E-026: lock check, sync, ruff, eight pytest rows, three hook-command rows, four UI rows, Playwright install | Both | Windows: the baseline command of each row, with `-rA` on each pytest command and `HYPOTHESIS_PROFILE=ci`. Linux: the same commands as steps of the CI jobs `security-and-regression` and `web-ui`, with a step added for each row that the workflow lacks | `SUCCEEDED` on each host. BE-1 and BE-2 nodes `PASSED` in the listing. Counts from the runner line | One per row and host |
| VM-3 | E-027 (`bash scripts/ui_e2e.sh`), E-028 (`bash scripts/gate_nov22.sh`) and the five skipped Linux cases | CI | Steps of the dispatched run (VM-10). The five cases are read from the Linux `-rA` listing, by the node names in the E-004 skip list. The Windows records of E-027 and E-028 are `UNVERIFIED`, Linux-only | `SUCCEEDED` for each row. 5 of 5 cases `PASSED` | One per row and case |
| VM-4 | No-loss inventory (below) | Both | `inventory`, then `diff-inventory` | 0 baseline node ids missing without a decision | One per host class |
| VM-5 | New-capability tests (14.2): signing and trust (D5), MCP stdio client run (D4), Conformance_Suite (D6), accessibility scan (D1), regulatory snapshot tests (D7), property tests P-a to P-o (D8) and scaffold end-to-end (D6) | Both | The command of each is fixed when its test file exists and is stored exactly (3.12). Property tests use the `ci` profile, derandomized, with `-rA` | `SUCCEEDED` | One per item and host |
| VM-6 | Four container gates and offline replay (E-019 to E-024) | Linux_Docker_Host | Commands 1 to 7 of the block below | Exit 0 each. `isolation.xml` has 4 tests and 0 failures. `VK_STARTUP_OK isolation=ENFORCED` once. `GATE-HTTP PASSED`. Replay `REPRODUCED`, integrity `VERIFIED`. Image ID unchanged | One per command |
| VM-7 | Enforced end-to-end scenario for `quote.finance.v1`, `quote.lease.v1` and `reel.mechanical.v1` (below) | Linux_Docker_Host | Command 8 of the block below | Per type: 5 ordered steps, `ENFORCED` in the run, the outcome and the Bundle | One per step and type |
| VM-8 | Replay matrix (below) | Linux_Docker_Host, Windows | Command 9 of the block, per type, with and without `--trust-store` and on the tampered copy. Windows: the same Bundles with `uv run --no-sync verdictkit replay`, under the socket guard of D5 DR-3 | As the matrix | One per case |
| VM-9 | Legacy corpus: the Bundles written at `84df25c` (a Texas finding, a non-Texas finding, a Lease claim, a Reel claim, the stub claim type and `examples/stub_claimtype/golden.vkb`), committed with their SHA-256 (D8 DR-2, P-g) | Both | `verdictkit replay <bundle> --json`, offline, on each host class | Each Bundle has an equal verdict hash and the status `REPRODUCED` or `REPRODUCED_ACROSS_ENV` (14.24), 0 `DIVERGED`, 0 `UNVERIFIABLE`. The observed status is recorded. See F9-7 and OD-D9-2 | One per Bundle and host |
| VM-10 | CI dispatch (below) | CI | `gh workflow run`, `gh run watch`, `gh run view`, `check-run` | `check-run` exits 0. The conclusion is recorded | One per run |
| VM-11 | Kiro hook firing and VerdictKit MCP tool call from inside Kiro | Owner | In the Contained_Hook_Environment the owner fires each hook of the pinned Hook_Set and calls each of the four tools once. The Kiro log and session export are the capture | Each capture cited by id and SHA-256, else `UNVERIFIED` | One per hook and tool |
| VM-12 | Local demonstration | Linux_Docker_Host | `docker run` of `<image>` `serve` with a run-time vault key, published only on `127.0.0.1` on a free port chosen at run time (1.17), then SM-1 and SM-7 of D2.8 against it | SM-1 (with `commitSha` equal to S) and SM-7 pass. No other port published | One per check |
| VM-13 | Frozen refs and Submission_Artifacts (14.14) | Both | `frozen`: `git rev-parse refs/tags/v1.0.0-submission`, `git rev-parse refs/tags/v1.0.0-submission^{commit}`, `git rev-parse refs/heads/master`, `git rev-parse refs/tags/verified-quote-e2e-20261118`, and `git diff --quiet 84df25c <S> -- <each Submission_Artifacts file>`, at the start and at the end of the phase | 4 of 4 values equal those of 1.2. Diff empty | One per check |
| VM-14 | Provenance (D9.5) | Both | `provenance` | Every field present. Hashes recomputed from committed blobs | One |
| VM-15 | Release report checks (D9.5), in two parts (TPR-M-10). VM-15a runs at S in PH7-17 and needs no report. VM-15b runs in PH7-18 only after `docs/next-phase/RELEASE_REPORT.md` exists | Both | `report-lint`. VM-15a: `docs/next-phase/REPRODUCING_VERIFICATION.md` (structural legs), README, `docs/` and UI text. VM-15b: `docs/next-phase/RELEASE_REPORT.md`, and the comparison of every command text of the S records with the reproduction document | 0 violations | One per part |
| VM-16 | Evidence publication | Both | The D8.5 sanitizer and zero-hit scan on each file to be published, and the hashes of each Private_Original and Sanitized_Copy | 0 hits in each class of 3.14 | One per commit |
| VM-17 | Historical reconciliation re-check (15) | Owner | `audit-scan`, and recomputation of H1 to H8 from the read-only Historical_Audit directories | D9-AC-21 | One per record |
| VM-18 | Credit records (16) | Owner | The owner reads the Kiro usage view. Record a Credit_Record or `NOT_AVAILABLE` | D9-AC-22 | One per session |
| VM-19 | External_Review_Record. Recorded after PH7-17, because the review is of the exact S (TPR-H-8). It is compared in PH7-18 | Owner | The owner or an independent reviewer (OA-03) reviews the exact S and supplies the reference. Compare the reviewed-file hashes with the hashes of those files at S | Hashes equal | One |

Container commands for VM-6 to VM-8. `docker image inspect` is repeated after the last command (DD9-6). `VK_COMMIT_SHA` is the build argument of D2.8.

```text
1  docker build --build-arg VK_COMMIT_SHA=<S> -t <image> <clone-l>
2  docker run --rm --network none -v "<out>:/out" <image> gate-isolation /out/isolation.xml
3  docker run --rm --network none <image> gate-startup
4  docker run --rm --network none <image> gate-http
5  docker run --rm --network none -v "<out>:/out" -v "<clone-l>/examples/stub_claimtype:/in:ro" <image> gate-case /in/claim.json /out/stub.vkb
6  docker run --rm --network none -v "<out>:/out:ro" <image> verdictkit replay /out/stub.vkb
7  docker image inspect --format '{{.Id}}' <image>
8  docker run --rm --network none -v "<out>:/out" <image> gate-e2e /out
9  docker run --rm --network none -v "<out>:/out:ro" <image> verdictkit replay /out/<type>.vkb --trust-store /out/trust-store.json --json
```

**No-loss rule (VM-4).** Once, at `84df25c` in a disposable worktree on each host class (Windows native; a Linux full checkout, not the image, which lacks `ui/`, F9-8): `uv run --no-sync pytest --collect-only -q`. `inventory` keeps the lines that start with `tests/`, sorts them and writes `docs/next-phase/baseline/TEST_INVENTORY.windows.txt` or `TEST_INVENTORY.linux.txt`. The raw output is a Private_Original. The ledger records the SHA-256 of both files (3.11, 14.22). At S the same command runs on each host class and `diff-inventory` lists the node ids that are missing and added. Rules: every baseline node id is collected unless a recorded maintainer decision names its rename or removal; each node that passed or skipped at the baseline passes or skips at S; BE-1 and BE-2 pass; no `--deselect`, `-k` or `--ignore` is added to the baseline selectors of E-004, E-009 and E-012 (13.9). Baseline outcomes per node: Windows from the E-004 counts and the named failures and skips (444 passed, 2 failed, 5 skipped, 4 deselected, of 455); Linux from one `-rA` run at `84df25c`, which does not exist yet (F9-2, OD-D9-7). Step passing counts are compared as in 14.9.

**Enforced end-to-end scenario (VM-7, DD9-8).** `gate-e2e <out_dir>` sets up the vault, the drafts directory, the examiner (`vk-examiner`, socket group `vk-ipc`, mode 660) and judge mode as `cmd_gate_http` does, then runs `scripts/gate_e2e.py` as `vk-custodian`. The script creates a throwaway Ed25519 key in memory and makes it available to the custodian only. For each claim type it records these steps in order, one Execution_Record each (14.5): (1) submit, `POST /api/v1/cases`; (2) freeze, `POST /api/v1/cases/{id}/freeze`; (3) run through the authenticated examiner, `POST .../evidence` then `POST .../runs`, which must end `COMPLETED` with `isolationMode` `ENFORCED` in the run record and in `GET .../outcome`; (4) download, `GET .../bundle` written to `<out>/<type>.vkb`, where `GET .../bundle/metadata` shows `ENFORCED`, integrity `VERIFIED` and `signatureValidity` `VALID`; (5) offline replay in a separate `--network none` container on the same image (VM-8). It also writes the public Trust_Store `<out>/trust-store.json` and a tampered copy `<out>/<type>.tampered.vkb`. It stops at the first failed step, keeps the records made so far and exits non-zero (14.7). Inputs are constructed and labelled `SYNTHETIC` in the scenario record: Quote and Lease reuse existing constructed test fixtures (the `PARAMS` of `gate_http.py` and `ITEMISED` of `tests/integration/test_quote_lease_itemised.py`), and Reel uses the bundled `SYNTHETIC_DEMO` fixture `fx_reel_impossible_sma`. The scenario adds no figure of its own, and each input names its source fixture.

**Replay matrix (VM-8, 14.18, 14.24).** Expected values, for a replay in the image that wrote the Bundle:

| Case | Trust_Store | Replay | Signature_Validity | Signer_Trust | Authenticity |
|---|---|---|---|---|---|
| Unsigned Bundle (the `gate-case` stub, written with no signing key) | none | `REPRODUCED` | `UNSIGNED` | `NOT_EVALUATED` | `NOT_ESTABLISHED` |
| Signed Bundle, each type | file with the public key | `REPRODUCED` | `VALID` | `TRUSTED` | `ESTABLISHED` |
| The same signed Bundle | none | `REPRODUCED` | `VALID` | `NOT_EVALUATED` | `NOT_ESTABLISHED` |
| Tampered copy (one byte of the stored `manifest.json` data changed) | file with the public key | `UNVERIFIABLE` | `INVALID` | `NOT_EVALUATED` | `NOT_ESTABLISHED` |

The tampered copy passes if the replay is `UNVERIFIABLE` or the validity is `INVALID`, with authenticity `NOT_ESTABLISHED` (14.24). The image that wrote a Bundle has the same `engine_version`, `python_version` and lock hash, so `REPRODUCED` is the expected status there. Natively on Windows the same Bundle may give `REPRODUCED_ACROSS_ENV`. That result passes if the verdict hash and the signature fields equal the container result (D8 DR-2).

**CI dispatch (VM-10, DD9-4).** Preconditions: the workflow file is on the default branch and has run at least once, because GitHub allows dispatch against another branch or tag only after that ([GitHub Docs, events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)); and `git ls-remote origin refs/heads/feature/kiro-next-phase` prints S. If it prints another value, a push follows DD9-5, or the CI result is `UNVERIFIED` with the reason. Steps: record the UTC time; `gh workflow run p0-integration.yml --ref feature/kiro-next-phase`; take the run id from the dispatch response ([GitHub Docs, create a workflow dispatch event](https://docs.github.com/en/rest/actions/workflows)) or from `gh run list --workflow p0-integration.yml --branch feature/kiro-next-phase --event workflow_dispatch --limit 1 --json databaseId,createdAt`; `gh run watch <id> --exit-status`; `gh run view <id> --json headSha,headBranch,event,status,conclusion,createdAt,url`, saved as the run record; `release_verify.py check-run <record> --sha <S> --branch feature/kiro-next-phase --after <time>`; `gh run download <id> --dir <out>` and `gh run view <id> --log`, both kept as Private_Originals. For a dispatched run `GITHUB_SHA` is the last commit of the dispatched ref, and the workflow file at that ref is the one that runs, so the added steps and the Windows job (OD-D9-3) belong to the run. The run's `conclusion` is the CI result. Content from the GitHub pages was rephrased for compliance with licensing restrictions.

### D9.5 Release report and provenance

`docs/next-phase/RELEASE_REPORT.md` is written after verification and committed as an evidence commit (DD9-2). Sections: (1) the candidate and the provenance block; (2) two result lines, Local_Readiness and Public_Deployment_Readiness, each `VERIFIED` or `NOT_VERIFIED` (D9.8); (3) for each of the nine tracks, every acceptance criterion of its requirement with its Outcome_Class and Execution_Record id (14.12); (4) the baseline comparison, one row per ledger row E-001 to E-028 with the baseline and S passing counts, flagged where the S count is lower (14.9); (5) every `UNVERIFIED` item with its reason, including Browser E2E, `gate_nov22.sh`, the five skipped Linux cases and automatic hook execution (14.11, 14.19); (6) every `FAILED` step, every unremediated Baseline_Exception and the blockers of D9.6 (14.10); (7) known limitations; (8) the rollback rows of D9.7; (9) Kiro usage (16) and Historical_Audit pointers (15); (10) the pointer to `docs/next-phase/REPRODUCING_VERIFICATION.md`, which lists the tools with versions, the clean-checkout steps for both host classes and the exact commands of the release run (14.15). Every count comes from the runner output of the S run (14.8). `report-lint` checks counts, commits, statuses and record ids against the ledger, the per-track table against the criteria of Requirements 5 to 14, each capability statement in README, `docs/` and UI text against a `SUCCEEDED` record of S (3.9, 3.10), the readiness wording, the credit figures and the citation of H records.

| Provenance field (14.17) | Source |
|---|---|
| Commit | S, 40 characters |
| Image ID | `docker image inspect --format '{{.Id}}' <image>` after the last gate, with the local run and the CI run listed separately. The image label `org.opencontainers.image.revision` (D2.8) equals S |
| `uv.lock` and `package-lock.json` SHA-256 | Hash of the committed blob (`git show <S>:<file>`), so a CRLF checkout cannot change it |
| Tool versions | Python patch version (host and image), uv, Node, npm, git, Docker engine, `gh`, Playwright, ruff, pytest, Hypothesis, locked `mcp` |
| Host class of each run | Windows build, Linux engine or runner image label, and the role (native, local Linux_Docker_Host, CI) |
| Plugin provenance manifest SHA-256 | Image label (D6.11 AM-D6-3) |
| Contract version | `2.0.0` (D5.8) |

### D9.6 Release blockers

Level: LOCAL blocks Local_Readiness, PUBLIC blocks only Public_Deployment_Readiness, CLAIM blocks only a capability statement (14.26). A row stays open until its record exists for S. The report lists every open row.

| ID | Blocker | Level | Req |
|---|---|---|---|
| RB-1 | BE-1 or BE-2 not remediated on S | LOCAL | 14.10, 1.18 |
| RB-2 | A required step has Outcome_Class `FAILED` | LOCAL | 14.10 |
| RB-3 | A baseline node id is missing without a decision, or a baseline node fails | LOCAL | 14.22, 1.13 |
| RB-4 | No External_Review_Record whose reviewed-file hashes equal those at S | LOCAL | 14.27, 13.27 |
| RB-5 | A container gate or the offline replay was not run on a Linux_Docker_Host with `--network none` | LOCAL | 14.3, 14.4, 14.23 |
| RB-6 | An enforced end-to-end examination is missing for `quote.finance.v1`, `quote.lease.v1` or `reel.mechanical.v1` | LOCAL | 14.23 |
| RB-7 | The replay matrix or the legacy corpus is missing or differs from D9.4 | LOCAL | 14.24 |
| RB-8 | A Frozen_Release ref or a Submission_Artifacts file changed | LOCAL | 14.14 |
| RB-9 | A publication scan hit | LOCAL | 3.14 |
| RB-10 | S is not the verified head, a tree was dirty, or a count is not from the S run | LOCAL | 14.8, 14.16, 14.21 |
| RB-11 | The provenance block is incomplete | LOCAL | 14.17 |
| RB-12 | A Kiro hook firing or MCP call from inside Kiro has no Kiro capture | CLAIM | 14.19, 14.25 |
| RB-13 | Browser E2E, `gate_nov22.sh`, a skipped Linux case or the CI run has no `SUCCEEDED` record for S | CLAIM | 14.19, 14.20 |
| RB-14 | No `SUCCEEDED` record per 7.13 for a deployed instance | CLAIM | 7.13, 7.14 |
| RB-15 | SG-1 to SG-9 or an applicable D2 acceptance row lacks a `SUCCEEDED` record | PUBLIC | 14.26 |
| RB-16 | Hosting, domain, certificate or budget decision not recorded | PUBLIC | 14.26, 7.17 |
| RB-17 | No monitoring, no rehearsed rollback or no recorded go decision of the owner | PUBLIC | 14.26, 14.13 |
| RB-19 | A phase checkpoint record that PH7-17 requires (PH1-18, PH2-10, PH3-14, PH4-10, PH5-17 or PH6-12) is missing, `FAILED` or `UNVERIFIED` without an accepted reason (TPR-H-3). RB-18 is defined in D10.10 | LOCAL | 14.10, 14.11, 4.4 |
| RB-20 | The OA-00 acceptance record, or a maintainer decision that a task consumed (OD-D8-1 to OD-D8-4 or another decision listed in OA-08), has no record (TPR-H-7, TPR-L-5) | LOCAL | 4.10, 14.10 |

### D9.7 Rollback

Every procedure adds commits or files. None resets history, force-pushes or touches `master` or a tag.

| ID | Artifact | Procedure | Confirmation |
|---|---|---|---|
| RP-1 | Phase_Branch commits | `git revert` the commit range on the Phase_Branch | `frozen` equals the values of 1.2. The Submission_Artifacts diff is empty |
| RP-2 | Contract version 2.0.0 | One revert of the lockstep change: server constant, `api/openapi.yaml`, UI_Kit constant, `api/examples/`, MCP replay result, tests and the `ui/judge` constant (AM-D5-12, AM-D5-13) | `GET /api/v1/health` shows the previous `contractVersion`. Contract tests pass |
| RP-3 | Container image | Run or redeploy the previous image: its ID locally, its digest where a registry exists (D2.8) | `gate-startup` marker. `GET /api/v1/health` shows the previous `commitSha` (7.15) |
| RP-4 | Rules manifest | Move the active pointer back to the previous manifest. Bundles embed their evidence, so replay is unaffected | Rule tests pass with the previous manifest. The legacy corpus replays as before |
| RP-5 | Trust_Store | Publish a file with a higher `serial` that restores or revokes the key | A replay shows the new `serial` and `sha256` (D5.7) |
| RP-6 | `mcp` pin | Revert `core/pyproject.toml` and `uv.lock` together | `uv lock --check` passes. The stdio client run passes |
| RP-7 | Hooks | A new commit that restores `.kiro/hooks/` and `scripts/hooks/` from `84df25c` | The HM-T5 hash check (D3). Renewed review (8.17) |
| RP-8 | Evidence publication | Supersede with a new Sanitized_Copy and a new hash. Never rewrite history | Publication scan has 0 hits. The Private_Original hash is unchanged |
| RP-9 | Plugin allowlist | Revert the allowlist constant and the provenance manifest build step | The public profile loads 0 third-party plugins (AM-D6-1) |

### D9.8 Local readiness and public deployment readiness

D9 authorizes no cloud provisioning, spending, DNS record, certificate, public listener, announcement, tag, merge or publication. The documentation keeps stating that no hosted demonstration is available until an Execution_Record per 7.13 exists (7.14). The local demonstration of VM-12 publishes on loopback only and is not a public listener.

| Condition | Local_Readiness | Public_Deployment_Readiness |
|---|---|---|
| Every LOCAL blocker of D9.6 clear on S | required | required |
| Evidence of 14.1 to 14.27 complete, with every `UNVERIFIED` item listed (14.11) | required | required |
| The image runs the demonstration locally (VM-12) | required | required |
| SG-1 to SG-9 each `SUCCEEDED` (D2.8) | not required | required |
| Hosting, domain, certificate and budget decisions recorded (D2.11) | not required | required |
| Monitoring in place and rollback rehearsed (D2.8) | not required | required |
| The owner's recorded go decision (14.13, D2.12 AM-11) | not required | required |

The report gives each result on its own line and never one combined "ready" line. `report-lint` rejects a combined statement, and rejects `VERIFIED` for a level that has an open blocker.

### D9.9 Acceptance criteria

All rows are UNVERIFIED until an Execution_Record exists. "Both" means the Windows host and a Linux source (Linux_Docker_Host or CI).

| ID | Criterion | Method | Pass threshold | Req | Host |
|---|---|---|---|---|---|
| D9-AC-1 | Exact commit and clean tree | VM-1 on each run. `provenance` reads S from every record and `check-evidence-commit` checks `git diff --name-status <S> <tip>` (TPR-C-2) | `HEAD` equals S and the status is empty, 2 of 2 checks per run on each host class. Every record of the release run carries the same 40-character S, 0 others. Every commit after S is an Evidence_Commit that `check-evidence-commit` accepts or a new Release_Candidate, and no Evidence_Commit appears in the Commit column of a release-run record. Negative controls: a clone with one untracked file fails, and a change to each Test_Input class (the Threat_Model, the review-hash record, the Execution_Index, a test inventory, `tasks.md` outside the two checkboxes, `.kiro/settings/mcp.json`, the reproduction document) fails the check | 14.16, 14.21 | Both |
| D9-AC-2 | Rerun completeness | VM-2, VM-3 and VM-5 | Each ledger row E-001 to E-028 (E-025a and E-025b through the Linux full-checkout run) has one record per host class with S, step, Outcome_Class, passed, failed, start and end. A row that cannot run on a host class is `UNVERIFIED` with a reason. Each of the 7 items of 14.2 has a record. 0 rows without a record | 14.1, 14.2, 14.19, 14.21 | Both |
| D9-AC-3 | Counts and baseline comparison | `report-lint` compares the report with the S records | 0 counts that differ from the runner line of the S record. Each row whose S passing count is below its baseline count is listed with both counts. 0 counts from another commit. Negative control: a count changed by 1 fails | 14.8, 14.9 | Both |
| D9-AC-4 | No-loss rule | VM-4 | Per host class: 0 baseline node ids missing without a recorded decision. Each node `PASSED` or `SKIPPED` at the baseline is `PASSED` or `SKIPPED` at S. BE-1 and BE-2 `PASSED`. 0 selection flags beyond those of E-004, E-009 and E-012. Negative control: a deleted test is reported missing | 14.22, 13.9 | Both |
| D9-AC-5 | Container gates | VM-6 | The five commands exit 0 with `--network none` on a Linux_Docker_Host, and the image ID is equal before the first and after the last. A gate that cannot take `--network none` is `UNVERIFIED` with the reason, never `SUCCEEDED` | 14.3, 14.4, 14.23, 1.5 | Linux_Docker_Host |
| D9-AC-6 | Enforced end-to-end | VM-7, plus one injected failure at each of the 5 steps | 3 of 3 types pass the 5 steps in order. The run record, the outcome and the Bundle record `ENFORCED`. The replay is `REPRODUCED`. 5 of 5 injected failures give scenario `FAILED`, name the failing step and keep the earlier records | 14.5, 14.6, 14.7, 14.23 | Linux_Docker_Host |
| D9-AC-7 | Replay matrix | VM-8: container replays with `--network none`, native replays under the socket guard | Each case gives the matrix values, for 3 types. 0 outbound connections. `<out>` and the repository hold 0 key files (scan for `*.pem`, `*.key` and key blocks). The Trust_Store holds public keys only | 14.18, 14.24, 10.12, 10.14, 2.8 | Both |
| D9-AC-8 | Legacy corpus | VM-9 | Every Bundle has an equal verdict hash, the status `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, 0 `DIVERGED`, 0 `UNVERIFIABLE`, and `envMatch` recorded (14.24). The record keeps the observed status and the pass condition in separate fields, and an observed status is never relabelled. `REPRODUCED_ACROSS_ENV` with an equal hash is not recorded `FAILED`. A different hash, `DIVERGED` or `UNVERIFIABLE` is `FAILED` | 14.24, 12.23, 13.22 | Both |
| D9-AC-9 | CI dispatch and head SHA | VM-10: `check-run` on the saved run record, with negative controls on a record with another SHA, another branch, `event` `push` and `status` `in_progress` | The run used has `headSha` equal to S, `headBranch` `feature/kiro-next-phase`, `event` `workflow_dispatch`, `status` `completed` and `createdAt` after the dispatch. 4 of 4 controls fail the check. The conclusion is recorded. 0 pull requests opened, 0 merges | 14.20 | CI |
| D9-AC-10 | Kiro evidence | VM-11 and `report-lint` | Each hook and each of the four tools is `SUCCEEDED` with a cited Kiro capture (id and SHA-256) or `UNVERIFIED`. 0 statements without a capture. H6 and H8 are not cited for S. U-001 to U-005 are unchanged (empty diff) | 14.25, 3.6, 3.7, 3.13 | Owner |
| D9-AC-11 | Unverified items and blockers | `report-lint` | Browser E2E, `gate_nov22.sh`, the five skipped cases, automatic hook execution and every other unrun item is `SUCCEEDED` with a record of S or `UNVERIFIED` with a reason. Each `FAILED` step, each unremediated Baseline_Exception and each RB row with its level is listed. A `VERIFIED` result for a level with an open blocker is rejected (negative control) | 14.10, 14.11, 14.19, 14.26 | Both |
| D9-AC-12 | External_Review_Record | VM-19 | A reference with its 7 fields (record id, SHA-256, date, verdict, commit, reviewed-file hashes, type `OWNER_ATTESTED`) exists, every reviewed-file hash equals that file's hash at S, and the report quotes the verdict | 14.27, 13.27 | Owner |
| D9-AC-13 | Provenance | VM-14 | 7 of 7 fields of D9.5 present. Hashes recomputed from committed blobs equal the recorded ones. The image ID equals the ID read after the last gate, and its revision label equals S | 14.17 | Both |
| D9-AC-14 | Report completeness and statements | `report-lint` | For each of the 9 tracks every criterion of its requirement is listed with its Outcome_Class and record id, 0 missing. Known limitations are present. Each capability statement in README, `docs/`, UI text and the report cites a `SUCCEEDED` record of S, with 0 violations. Negative control: an uncited statement is reported with its file and line | 14.12, 3.9, 3.10 | Both |
| D9-AC-15 | Push authorization | Ledger review and `git ls-remote origin` | 0 pushes without a cited authorization. Each push is of `feature/kiro-next-phase`, without force, with the ref value before and after. Remote `master` and both tags equal their recorded values | 14.13 | Owner |
| D9-AC-16 | Frozen refs and Submission_Artifacts | VM-13 at the start and at the end of the phase | 4 of 4 values equal those of 1.2 (tag object, peeled commit, `master`, `verified-quote-e2e-20261118`). The diff of each Submission_Artifacts file against `84df25c` is empty | 14.14 | Both |
| D9-AC-17 | Third-party reproduction | `report-lint` on `REPRODUCING_VERIFICATION.md` | Every tool named in a documented command has a version in the provenance block. Every command text of the S records appears in the document. Both host classes are covered | 14.15 | Both |
| D9-AC-18 | Readiness separation and no provisioning | VM-12 and a wording and command scan | 2 separate result lines and 0 combined. The no-hosted-demonstration statement is present where deployment is described, and 0 public URL is presented as live. 0 release records contain `aws`, `terraform`, `certbot`, `docker push`, `gh release`, `gh pr create`, a `git tag` that creates a tag, or `git merge` other than `git merge-base`. The local demonstration publishes on loopback only | 14.26, 7.14 | Both |
| D9-AC-19 | Rollback | `report-lint` | 9 of 9 RP rows are in the report, each with a confirmation check | 14.26 | Both |
| D9-AC-20 | Release evidence hygiene | VM-16 | 0 hits in each class of 3.14 in every file to be published, with the count per class recorded. Private_Original and Sanitized_Copy hashes recorded separately. 0 command fields with an ellipsis or placeholder, and each record cites its Execution_Index id. 0 reconstructed items | 3.8, 3.11, 3.12, 3.13, 3.14, 1.14 | Both |
| D9-AC-21 | Historical reconciliation re-check | VM-17 | Source directories unchanged (file count, bytes and tree hash equal before and after). 0 repository files with a SHA-256 equal to a Historical_Audit file and 0 tracked `messages.jsonl`. H1 to H8 recomputed, a differing value recorded with both values, and a value that cannot be recomputed `UNVERIFIED` and unused. Disagreements list both statements and the better supported one. Each result carries its host label. 0 audit-based statements without an H citation | 15.1 to 15.10 | Owner |
| D9-AC-22 | Credits | VM-18 and `report-lint` | Credits for the phase are `NOT_AVAILABLE` unless a Credit_Record exists. 0 estimated or back-filled figures. 0 sums of U-001 to U-005. The Historical_Audit total is in its own section. 0 cost per task, test or requirement without a Credit_Record for that exact unit | 16.1 to 16.5 | Owner |

### D9.10 Open decisions, risks and traceability

| ID | Item | Recommendation |
|---|---|---|
| OD-D9-1 | Evidence commits after S. The ledger and the report live in the repository, so they can only be committed after S (14.16, 14.21). | Superseded by TPR-C-2 (D10.11 TR-2). A commit after S is an Evidence_Commit only if it changes the Evidence_Output_Set (and the two final checkboxes of `tasks.md`) and passes `check-evidence-commit`. Every other change, including a Test_Input, is a new Release_Candidate. 14.16 and 14.21 are reconciled in `requirements.md`. |
| OD-D9-2 | Legacy corpus status (F9-7, R-D9-1). | DECIDED by the requirement amendment: 12.23, 13.22 and 14.24 accept `REPRODUCED` or `REPRODUCED_ACROSS_ENV` with an equal verdict hash, and `DIVERGED` and `UNVERIFIABLE` stay forbidden. The `envMatch` rule is unchanged and `envMatch` is recorded. Open point: `uv.lock` changes make `REPRODUCED_ACROSS_ENV` the likely status for the legacy corpus (F9-7). |
| OD-D9-3 | A Windows job in `p0-integration.yml`. | Add `windows-latest` (lock check, sync, ruff, `pytest -rA`, UI typecheck, tests, build) as extra evidence. The fresh-clone run on the owner's Windows host stays the Windows record. |
| OD-D9-4 | Who performs the owner steps: push authorization, `gh` dispatch, the Linux full-checkout host, Kiro captures and the External_Review_Record. | The owner. The agent prepares the exact command lists and records the outputs that the owner supplies. |
| OD-D9-5 | Completeness of the Submission_Artifacts list (14.14). | The five files named in the Glossary now. The owner adds any further file before S is selected, and the addition is recorded. |
| OD-D9-6 | What "runs the demonstration locally" means for Local_Readiness (14.26). | `serve` on a loopback port plus SM-1 and SM-7 (VM-12). `gate-http` alone does not start the service. |
| OD-D9-7 | The Linux per-test baseline at `84df25c` (F9-2). | One `-rA` run and one `--collect-only` run on a Linux full checkout of `84df25c` (B-D8-1). CI cannot run that commit without a pushed ref (14.13). |

| ID | Risk | Mitigation |
|---|---|---|
| R-D9-1 | A legacy Bundle replays as `REPRODUCED_ACROSS_ENV` when `uv.lock` differs (F9-7), which is likely at S. D8 P-g and DR-5 carry the same pass condition. | The row records the observed status and `envMatch` and is never relabelled. The pass condition accepts both statuses (OD-D9-2). |
| R-D9-2 | Run output inside the clone leaves `gate/` untracked, so the clean-tree check fails (F9-4). | An output-directory variable in `scripts/gate_nov22.sh` (default `gate`), and `$RUNNER_TEMP` in the workflow. |
| R-D9-3 | Image IDs differ per build, and the CI image differs from the local one (F9-8). | DD9-6. Both IDs are listed. |
| R-D9-4 | CI preconditions (R-D8-3): the workflow must be on the default branch and have run once, the remote must hold S, the push needs authorization, and the added steps may exceed the 30 and 20 minute limits. | The `UNVERIFIED` fallback of DD9-4. Raise `timeout-minutes` in the file and record the change. |
| R-D9-5 | No Linux per-test baseline exists, and CI cannot run `84df25c` (OD-D9-7). | Until it exists the Linux no-loss check covers collection only, and node outcomes stay `UNVERIFIED`. |
| R-D9-6 | The Windows development host and a Windows runner differ (R-D8-4). | Record the Windows build with each record. The fresh-clone run stays the Windows record. |
| R-D9-7 | Owner-only evidence may be missing at S: Kiro captures, the External_Review_Record, the Linux host (B-D8-1 to B-D8-3) and the Historical_Audit directories. | RB-4, RB-5 and RB-12 stay open, and the report says so. An unavailable Historical_Audit gives `UNVERIFIED` for the re-check and leaves the records of 2026-11-24 unchanged. |
| R-D9-8 | Any change to a tested file after S voids every record (14.21), so the whole run repeats. | Freeze the code before S is selected. Limit evidence commits (DD9-2). |

**Files for implementation (not changed now).** New: `scripts/gate_e2e.py` and a `gate-e2e` subcommand in `deploy/entrypoint.sh` (which also passes `VK_SIGNING_KEY_FILE` and `VK_TRUST_STORE_FILE` to `as_custodian` only, as D5.5 designs); `scripts/release_verify.py` with its tests under `tests/release/`; `docs/next-phase/RELEASE_REPORT.md`; `docs/next-phase/REPRODUCING_VERIFICATION.md`; `docs/next-phase/baseline/TEST_INVENTORY.windows.txt` and `TEST_INVENTORY.linux.txt`; appended ledger records. Edited: `.github/workflows/p0-integration.yml` (a step per ledger row, `-rA`, steps that record `git rev-parse HEAD`, `git status --porcelain` and the image ID, the `gate-e2e` step, output under `$RUNNER_TEMP`, longer `timeout-minutes`, and a Windows job if OD-D9-3 is accepted); `scripts/gate_nov22.sh` (an output-directory variable, default `gate`). Not changed: `scripts/gate_http.py`, existing tests, `m3b-api-checks.yml`, the Frozen_Release refs, the Submission_Artifacts files and `requirements.md`.

**Traceability.** 14.1: D9.4 (VM-2, VM-3), D9-AC-2. 14.2: VM-5, D9-AC-2. 14.3: DD9-7, VM-6, D9-AC-5. 14.4: VM-6, D9-AC-5. 14.5 to 14.7: VM-7, D9-AC-6. 14.8: DD9-3, D9.5, D9-AC-3. 14.9: D9.5, VM-15, D9-AC-3. 14.10: D9.6 (RB-1, RB-2), D9-AC-11. 14.11: D9.5, D9.6, D9-AC-11. 14.12: D9.5, D9-AC-14. 14.13: DD9-5, D9-AC-15. 14.14: VM-13, D9-AC-16. 14.15: D9.5, D9-AC-17. 14.16: DD9-1, DD9-2, D9-AC-1. 14.17: D9.5, VM-14, D9-AC-13. 14.18: VM-8, D9-AC-7. 14.19: D9.5, D9.6 (RB-12, RB-13), VM-3, VM-11, D9-AC-2, D9-AC-11. 14.20: DD9-4, VM-10, D9-AC-9. 14.21: DD9-2, DD9-7, VM-1, D9-AC-1, D9-AC-2. 14.22: VM-4, D9-AC-4. 14.23: VM-6, VM-7, D9-AC-5, D9-AC-6. 14.24: VM-8, VM-9, D9-AC-7, D9-AC-8. 14.25: DD9-9, VM-11, D9-AC-10. 14.26: D9.6, D9.7, D9.8, D9-AC-11, D9-AC-18, D9-AC-19. 14.27: D9.6 (RB-4), VM-19, D9-AC-12. 15.1 to 15.10: VM-17, D9-AC-21. 16.1 to 16.5: VM-18, D9-AC-22. 1.5: VM-6, D9-AC-5. 1.14: VM-16, D9-AC-20. 2.8: VM-8, D9-AC-7. 3.6 and 3.7: DD9-9, VM-11, D9-AC-10. 3.8: VM-16, D9-AC-20. 3.9 and 3.10: VM-15, D9-AC-14. 3.11 to 3.14: VM-16, D9-AC-20, and for 3.13 also VM-11 and D9-AC-10. 7.14: D9.8, D9-AC-18. 10.12 and 10.14: VM-8, D9-AC-7. 12.23: VM-9, D9-AC-8. 13.9: VM-4, D9-AC-4. 13.27: VM-19, D9-AC-12. Every criterion listed above maps to at least one D9 section and one row. Two readings are recorded and not closed here: the replay status that 12.23, 13.22 and 14.24 require for a legacy Bundle (F9-7, OD-D9-2), and the evidence commit after S under 14.16 and 14.21 (OD-D9-1). Both go to D10 for reconciliation, and `requirements.md` is not edited.

## D10. Traceability, reconciliation, status and open decisions

### D10.1 Scope and status

**Covers.** The seven canonical sections, and in D10: the decision precedence index (D10.2), the requirement reconciliation (D10.3), the resolution of the gaps (D10.4), the criterion-level traceability with a coverage check and the rows that close the gaps it found (D10.5), the remediation register (D10.6), the status ledger (D10.7), the open decisions and blockers (D10.8) and the files for implementation (D10.9).

**Does not cover.** Implementation, `tasks.md`, the run of any test or gate, any edit to `requirements.md`, any push other than the Phase_Branch, and any tag, merge, publication or provisioning.

**Status.** Everything in D10 is DESIGNED. Nothing is IMPLEMENTED or VERIFIED. D0 to D9 are used as committed at `1cb3e481439cf31d2a7ba45a1b98129e095a02fd`, and D10 changes none of their text. The status paragraph and the table of contents were rewritten because both were out of date, and the canonical sections were inserted before D0. D10 reads `requirements.md` as it stands and edits none of it. Facts marked (read) come from a read-only inspection of `api/server.py`, `api/__main__.py`, `cli.py`, `bundle.py`, `tests/conftest.py` and `api/openapi.yaml` while D10 was written. They are UNVERIFIED for Requirement 3 until a record exists.

### D10.2 Decision precedence index

A later record governs the earlier text it names. The earlier text is not edited. This table says which text is superseded and where the governing record is.

| # | Earlier text | Governing record | Reading |
|---|---|---|---|
| 1 | The bound `>=2.3,<3` in the D4.3 table row, in T-M8 (D4.9) and in the OD-D4-5 recommendation (D4.11), and the wording of D4-AC-18 | AM-D4-6 (D4.12), AM-D4-8 (D4.13) | The specifier is `>=2.3,<2.4` with one exact pin in `uv.lock` |
| 2 | OD-D5-1 and every text that says 1.2.0: D2.11 (OD-D2-3), D4.3, D5.6, D5.8, D5.10 (D5-AC-1, D5-AC-11), D5.11, D5.12 (AM-D5-10) | AM-D5-12 (D5.13) | Read 2.0.0 for 1.2.0 |
| 3 | DD-10 (D1.3), OD-D5-5 (D5.11) | AM-D5-11 (D5.12), AM-D5-13 (D5.13) | `ui/judge` changes only the `CONTRACT` constant (now 2.0.0) and the version label |
| 4 | AM-D3-2 item (b), the effective-rights call (O2) | DD8-7 (D8.3, D8.5) | O1 is required and sufficient. O2 is dropped. O3 is a timeboxed spike. |
| 5 | OD-D3-4, BE1-7 (D3.9) | DD8-6 (D8.3, D8.5) | `requires-python` is unchanged. Windows needs CPython 3.12.4. The helper fails with `UNSUPPORTED_PYTHON_PATCH`. |
| 6 | G-D6-1 and the profile note in D6.4 | AM-D6-4 (D6.11) | One resolver, validated in both processes |
| 7 | OD-D6-2 | AM-D6-1 (D6.11) | Public loading fails closed. An unlisted entry point is never imported. |
| 8 | OD-D6-4, OD-D6-5 | AM-D6-2 (D6.11) | A duplicate `type_id` is rejected in every mode. Local mode reports it and leaves the types unregistered. |
| 9 | The allowlist by distribution and value (D6.4), T-P6 (D6.8) | AM-D6-3 (D6.11) | Approval binds to Plugin_Provenance. `PLUGIN_PROVENANCE_MISMATCH` refuses a mismatch. |
| 10 | B-D7-1, D7-AC-1, D4-AC-2 | AM-D7-1 (D7.11) | The `CA` to `ZZ` hunks are the only permitted change to existing tests |
| 11 | B-D7-2 | AM-D7-2 (D7.11) | Read-only retrieval is authorized for implementation. Review stays a human record. |
| 12 | G-D7-2, D7-AC-19, OD-D7-5 | AM-D7-3 (D7.11) | Version-aware Examination_Semantics. A legacy bundle replays `REPRODUCED` or `REPRODUCED_ACROSS_ENV`. |
| 13 | OD-D7-1 | AM-D7-4 (D7.11) | Source artifacts are stored where the terms permit |
| 14 | OD-D7-3, G-D7-1 | AM-D5-12 (D5.13) | Classified in the 2.0.0 event |
| 15 | R-D4-3 (D4.11) | DD8-5 (D8.3) | The Approved_Root helper and `PATH_NOT_ALLOWED` |
| 16 | R-1 and R-2 (D2.11 B-9, AM-5) | T8-34, T8-35 (D8.4) | Recorded in the Threat_Model, each with a reason |
| 17 | BE2-1 to BE2-6 (D3.9), the BE-2 wording of D0.5 | DD8-8 (D8.5), 1.19 | Measure first. The wording stays "observed on Windows" until a Linux run exists. |
| 18 | D0.8 item 9 (no push by the agent), the pull-request route in D0.3 and D0.9, B-H7 (D3.12) | 14.13 as amended, DD9-4, DD9-5 (D9.3) | A Phase_Branch push needs the owner's explicit authorization in the request and a ledger record. CI runs by dispatch, with no pull request and no merge. |
| 19 | D1.13 "Correctness properties. PENDING D10" | The Correctness Properties section | The five D1 candidates are CP-1 to CP-5 |
| 20 | D1.15 and D1.16 OD-6 ("`requirements.md` is not edited") | RC-7 (D10.3) | 5.8 and 6.9 now carry the sealed-field exception that DD-9 reads |
| 21 | The gap tables of D2.10, D2.12 ("still missing") and D3.11, and the "proposed for D10" statements in D2.10, D3.1 and D3.11 | D10.4 | G-1 to G-4 are criteria 7.23 to 7.26. G-5 and G-6 stay code gaps. G-7 to G-13 are the amended 8.x criteria. |
| 22 | D3.12 "D4 to D10 are not written" | The Document status | It described the authoring stage of D3. D4 to D10 are written. |
| 23 | OD-D9-1 (D9.10) and RC-20 (D10.3) | D10.10 | Evidence commits reference S. A different commit is not automatically S. |
| 24 | OD-D10-1, and the words "value chosen at implementation" in D10-AC-2 and D10.5 | D10.10 | 5 failed attempts per 15 minutes per source and account, configurable and bounded |
| 25 | OD-D10-2 and the gap noted in D10.5 for 3.2 | D10.10 | The 5 s target stays. A recording failure is visible and never `SUCCEEDED`. |
| 26 | OD-D10-3, the gap noted in D10.5 for 4.6, and the blocker list of D9.6 | D10.10 | A failed rollback is blocker RB-18 and needs recovery to a verified checkpoint |
| 27 | OD-D10-4, RC-22, CP-29 and the reading of 13.5(a) | D10.10 and requirements 10.36, 13.5(a), 14.24 | Three separate results. Exact archive-byte verification needs an external trusted digest. |
| 28 | The path rule of DD9-2, OD-D9-1 (D9.10) and D10.10 for evidence commits, RC-20 (D10.3), D9-AC-1 | D10.11 TR-2 and requirements 14.16, 14.21 | A commit after S is an Evidence_Commit only if it changes the Evidence_Output_Set and passes `check-evidence-commit`. A Test_Input change is a new Release_Candidate. |
| 29 | BE1-1, BE1-4, BE1-5 (D3.9), D3-AC-17, D8-AC-4, and "textually unchanged" in 13.11 | D10.11 TR-5, TR-10 and requirement 13.11 | The POSIX assertion is preserved by AST equality. The access-list reader is a production module that the test and `_workdir()` both call. |
| 30 | D8-AC-6, D8-AC-7, the Linux legs of D3.9 (BE1-8), D8.5 (BE-1 and BE-2 closure), B-D8-1 | D10.11 TR-1, TR-9 | The Windows leg is autonomous. The Linux leg is a deferred row (DLV-1 to DLV-4) and a mandatory release gate. |
| 31 | The description of `gate-isolation` as four tests (D0, D2.7 DD2-11, D9.4 VM-6) | D10.11 TR-3 | The four original tests are preserved. Identity groups and a counts file are added, and CI runs the same command. |
| 32 | D9.4 VM-15 and VM-19, D9.5 (when `report-lint` runs) | D10.11 TR-2, TR-8 | VM-15a runs at S. VM-15b and VM-19 run in PH7-18, after the report and after OA-03. |
| 33 | The blocker list RB-1 to RB-18 (D9.6, D10.10) | D10.11 TR-7 | RB-19 (checkpoint records) and RB-20 (OA-00 and consumed decisions) are added. |
| 34 | DD8-14 (one shared containment helper) and DD8-5 (the Approved_Root helper), BE1-4 | D10.11 TR-10 and requirement 13.30 | One production module holds containment, secure open, private-directory enforcement and the Windows access-list reader. |
| 35 | OD-D8-1 to OD-D8-4 as assumed by tasks, and OA-08 "blocks no box" | D10.11 TR-8 | OA-08 is a gate for the tasks that consume OD-D8-1 to OD-D8-4. |
| 36 | PC-1 to PC-6 (D8.11), D8-AC-16, KT-1 to KT-8 (D8.5), D8-AC-8, the final run PH7-05 | D10.11 TR-6 | PC-7 and the KT-S variants add the signing key. The final matrix runs after the last security-relevant change. |
| 37 | The rows of D6 and D7, 13.5(e), 13.14, 13.20, 13.24 and 14.2, and every count that they fix (15 properties, 12 start-up cases, seven surfaces) | D10.12 | The owner scope freeze defers the plugin SDK and the regulatory expansion. D10.12 gives the reduced counts and the status of each affected row. |

### D10.3 Requirement reconciliation

The final round of amendments is in `requirements.md` as of the checkpoint `1cb3e48`, and D10 does not edit it. The numbering of existing criteria is unchanged. Each row records one change that the design reads, with its reason and source. RC-20, RC-21 and RC-23 are readings and not text changes. RC-20 is decided by OD-D9-1 and RC-22 by OD-D10-4 (D10.10), and RC-22 is reconciled in `requirements.md` by 10.36, 13.5(a) and 14.24. After the maintainer's final decisions of 2026-11-25, `requirements.md` was amended again as D10.10 lists: criterion 10.36 was appended, and criteria 13.5(a) and 14.24 were changed in place.

| RC | Requirement | Change | Reason | Source |
|---|---|---|---|---|
| RC-1 | Heading | `### Requirement numbering and review history` is renamed `### Numbering and amendment history`, with one sentence for the round | The old heading has the pattern of a requirement heading and was read as a malformed one | Register |
| RC-2 | Glossary | Added: Security_Profile, Approved_Root, Examination_Semantics, Plugin_Provenance, Private_Original, Sanitized_Copy, External_Review_Record, Contained_Hook_Environment, Local_Readiness, Public_Deployment_Readiness | New terms of 1.14, 3.11, 7.19, 8.20, 9.21, 11.16 to 11.18, 12.23, 13.27 and 14.26 | H-1, M-5, M-6, L-6, AM-D6-4, AM-D7-3 |
| RC-3 | Glossary and accepted exceptions | In place: API_Server (1.1.0 at the baseline, 2.0.0 after 10.34), Submission_Artifacts (`ui/judge/` application files are not Submission_Artifacts), and the BE-2 paragraph (observed on Windows, attribution unverified) | Contract 2.0.0, the judge UI constant and 1.19 | AM-D5-12, AM-D5-13, L-4 |
| RC-4 | R1 | In place 1.8 (exception for 10.35) and 1.14 (Private_Original, Sanitized_Copy, hashes). New 1.19. | Publish evidence without raw paths. The BE-2 cause is not established. | H-1, L-4, AM-D5-13 |
| RC-5 | R2 | New 2.13 (mode fixed at start, fail closed) and 2.14 (the examiner serves only the custodian account) | Isolation downgrade and custodian authentication | L-1, L-2 |
| RC-6 | R3 | New 3.11 to 3.14 (Sanitized_Copy publication, exact command text with the Execution_Index id, preserved Kiro evidence, zero-hit scan) | Evidence hygiene and ledger fidelity | H-1, L-4, L-5 |
| RC-7 | R5, R6 | In place 5.8 and 6.9: sealed claimed figures are the one exception to input retention | The UI keeps claimed outcomes write-only (DD-9). The literal text conflicted with it. | OD-6 (D1.16) |
| RC-8 | R7 | New 7.19 to 7.22 (profile in both processes, key channels, admission before buffering, replay isolation) and 7.23 to 7.26 (case ownership, access policy, retention and sweeper, liveness and readiness) | Findings M-1, M-2, L-7 and the gaps G-1 to G-4 and G-D6-1 | AM-D6-4, AM-6, AM-7, AM-9, D2.6 |
| RC-9 | R8 | In place 8.1, 8.2, 8.5, 8.6, 8.7, 8.8, 8.10, 8.13 and 8.16. New 8.19 (hook configuration unchanged in a session) and 8.20 (Contained_Hook_Environment). | Gaps G-7 to G-13. 8.13 constrains hook configuration while BE-1 is open. | D3.11, AM-D3-1, AM-D3-7, DD8-15, M-4, M-5 |
| RC-10 | R9 | In place 9.1 (two exceptions: strict arguments and the Approved_Root). New 9.21 and 9.22 (`mcp>=2.3,<2.4`). | L-6 and the dependency finding F4-6 | AM-D4-5, AM-D4-8, DD8-5 |
| RC-11 | R10 | In place 10.5 (byte-identical under the same Examination_Semantics) and 10.21 (BREAKING rule, new major version). New 10.34 (contract 2.0.0) and 10.35 (judge UI constant only). | A strict 1.1.0 validator rejects the new fields | AM-D5-10, AM-D5-12, AM-D5-13 |
| RC-12 | R11 | New 11.16 (public loading fails closed), 11.17 (duplicate `type_id`) and 11.18 (provenance binding) | A plugin runs in the custodian after the reveal | AM-D6-1 to AM-D6-3 |
| RC-13 | R12 | In place 12.13. New 12.21 (`CA` to `ZZ`), 12.22 (retrieval authorization), 12.23 (Examination_Semantics and historical replay) and 12.24 (source artifacts). | Adding a jurisdiction changes a hashed statement and the example of an unsupported jurisdiction | AM-D7-1 to AM-D7-4 |
| RC-14 | R13 | In place 13.11. New 13.16 to 13.28. `REPRODUCED_ACROSS_ENV` is added to 13.5(a), 13.6 and 13.21, and 13.22 accepts both success statuses for the legacy corpus. | `ReplayStatus` has two success values. The BE-1 criteria conflicted. | M-1, M-2, M-4, M-6, M-7, L-1, L-2, L-3, L-6, L-7, F9-7 |
| RC-15 | R14 | In place 14.13. New 14.20 to 14.27. 14.24 gives the expected statuses, with `REPRODUCED` for a bundle replayed in the image that wrote it. | Verification needs a dispatch on the Phase_Branch and a readiness split | M-3, DD9-4, DD9-5, OD-D9-2 |
| RC-16 | Track register | The P7 and P8 rows name the External_Review_Record, dispatch, the no-loss rule and the readiness split | D8 and D9 | M-6, D9.8 |
| RC-17 | 2.11, 8.13, 13.11 | The three statements are consistent. The platform branch is not a skip, the POSIX text is unchanged, and 8.13 constrains hook configuration only while BE-1 is open. | The BE-1 contradiction | M-4, D8.5 |
| RC-18 | 1.14 | Byte-for-byte preservation applies to the Private_Original. The published file is the Sanitized_Copy. | The original rule forbade private publication | H-1, DD8-9 |
| RC-19 | 12.23, 13.22, 14.24 | `REPRODUCED` is required only for a bundle replayed in the image that wrote it. A legacy bundle gives `REPRODUCED` or `REPRODUCED_ACROSS_ENV` with an equal verdict hash. `DIVERGED` and `UNVERIFIABLE` stay forbidden. | The lock hash differs once 9.22 changes `uv.lock`, so `REPRODUCED_ACROSS_ENV` is the likely status | F9-7, OD-D9-2 |
| RC-20 | 14.16, 14.21 | Reading, decided (OD-D9-1, D10.10). The ledger and the release report are in the repository, so they can only be committed after S. The reading is that S stays the Release_Candidate while the commits after S change only `docs/next-phase/**` and the spec `tasks.md`, and any other change is a new Release_Candidate. The literal text says "any new commit". | Without a decision the literal text applies, and each evidence commit would start a new Release_Candidate | OD-D9-1, DD9-2 (the path rule of this reading is superseded by TPR-C-2: D10.2 row 28, D10.11 TR-2) |
| RC-21 | 14.1 | Reading. Step E-025a and E-025b ran in an invalid environment, because the image has no `ui/`. Its valid form, a Linux full-checkout `-rA` run, is the step that is rerun. | The invalid step cannot be repeated as it was | F8-13, D9.4 |
| RC-22 | 13.5(a), 10.15 | Reading, decided (OD-D10-4, D10.10), reconciled in `requirements.md`. "Changing any single byte of a Bundle never yields REPRODUCED" cannot hold for bytes of the zip container that no check covers (timestamps, attributes, comments, extra fields). The property is tested over the manifest, the manifest-listed members and the signature envelope. | F5-2 and R-D5-4 say the container bytes are covered by nothing, and D5-AC-16 already says "signed region" | OD-D10-4, CP-29 |
| RC-23 | 7.5, 7.7 | Reading. The baseline `serve` prints no `VK_STARTUP_OK`, and the 429, 413 and 400 early returns carry no security headers. The criteria stand, and the two items are code gaps tracked by D2 rows. | G-5, G-6 | D2.2 (F-2, F-5), D2-AC-2, D2-AC-5 |

### D10.4 Gap resolution

| Gap | Resolution | Criteria | Status |
|---|---|---|---|
| G-1 | Case ownership becomes a criterion | 7.23 (AM-6) | AMENDED |
| G-2 | Access policy and administrative boundary become a criterion | 7.24 (AM-7) | AMENDED |
| G-3 | Retention and sweeper safety become a criterion | 7.25 (AM-9) | AMENDED |
| G-4 | Liveness, readiness and health disclosure become a criterion | 7.26 (D2.6) | AMENDED |
| G-5 | The start-up line that `serve` does not print | 7.7 stands. D2-AC-1 and D2-AC-2 track the code gap. | No new text |
| G-6 | Headers missing on 429, 413 and 400 | 7.5 stands. D2-AC-5 and SG-6 track the code gap. | No new text |
| G-7 | A read-only verification command cannot mean "no writes" | 8.8 amended (DD3-4) | AMENDED |
| G-8 | The trigger of a hook | 8.1 and 8.7 amended | AMENDED |
| G-9 | Fields "all captured from Kiro" | 8.2 amended | AMENDED |
| G-10 | Timeout tied to the baseline duration | 8.5 amended (exact command text, completed run) | AMENDED |
| G-11 | "Leave the saved file unchanged" | 8.6 amended (no tracked file or index change) | AMENDED |
| G-12 | Trust for the clone only, hook files unchanged in a session | 8.16 amended, 8.19 new | AMENDED |
| G-13 | The timeout indication depends on Kiro | 8.10 amended (the runner's own deadline) | AMENDED |
| G-D6-1 | The profile reaches the examiner | 7.19 (AM-D6-4) | AMENDED |
| G-D7-1 | Contract-visible D7 fields | Classified in the 2.0.0 event (AM-D5-12) | DECIDED |
| G-D7-2 | Older bundles replay `DIVERGED` | 12.23 (AM-D7-3) | AMENDED |
| B-D7-1 | California against the Texas tests | 12.13 and 12.21 (AM-D7-1) | AMENDED |
| OD-6 | 5.8 against DD-9 | 5.8 and 6.9 except sealed claimed figures | AMENDED |
| H-1, M-1 to M-7, L-1 to L-7 | Each finding maps to the criteria of D10.3 (RC-4 to RC-15) and to the rows of D10.6 | See D10.6 | DESIGNED |

### D10.5 Criterion-level traceability

Each entry reads `n.m: sections; rows`. A section is where the design handles the criterion. A row is a test, a matrix entry or a blocker that checks it. Row names follow their section: `AC-n` are the rows of D1.13, and every other prefix names its own section. The entries reuse D0.10, D1.14, D2.10, D3.11, D4.11, D5.11, D6.10, D7.10, D8.15 and D9.10, and add the criteria that those sections predate.

**R1.** 1.1: D0.7, D9.3 (DD9-5); D9-AC-15, D9-AC-16. 1.2: D0.4, D0.7, D9.4 (VM-13); D9-AC-16, D5-AC-19. 1.3: D0.7, D9.7 (RP-1); D9-AC-15, D9-AC-16. 1.4: D0.6, D9.4 (VM-2, VM-3); D9-AC-2. 1.5: D0.3, D9.4 (VM-6); D9-AC-5. 1.6: D0.3, D9.4; D9-AC-2, D9-AC-5. 1.7: D0.5, D9.6; RB-1, RB-2, D9-AC-11. 1.8: D0.1, D5.13 (AM-D5-13); D5-AC-19, D9-AC-16. 1.9: D0.1, D9.3 (exact-commit rule); VM-1, VM-13, D9-AC-1, D9-AC-16. 1.10: D0.5, D9.2 (F9-1), D9.3 (DD9-1, DD9-3); D9-AC-2, D9-AC-3. 1.11: D0.5, D8.5 (BE-1 and BE-2 closure); D8-AC-6, D8-AC-7, D9-AC-11. 1.12: D0.3, D0.5, D9.4; D9-AC-2, D8-AC-23. 1.13: D0.5, D3.9; RB-3, D9-AC-4. 1.14: D8.5 (publication rule), D9.4 (VM-16); D8-AC-22, D9-AC-20. 1.15: D9.3 (DD9-3), D8.5 (ledger reconciliation); D9-AC-2, D8-AC-23. 1.16: D0.5, D9.3 (DD9-3), D9.4; D9-AC-2, D9-AC-4. 1.17: D0.3, D1.3 (DD-12), D8.5 (BE-2 closure); AC-18, D8-AC-7. 1.18: D0.5, D3.9, D8.5; RB-1, D8-AC-4, D8-AC-5, D8-AC-7. 1.19: D0.5, D8.5 (attribution wording); D8-AC-23.

**R2.** 2.1: D0.4, D1.9 (DD-7); AC-7. 2.2: D0.4, D5.9 (DR-1), D6.6, D7.7; D5-AC-15, D6-AC-5, D7-AC-8. 2.3: D0.7, D1.11, D2.5 (DD2-4, DD2-9), D4.4, D6.7 (CS-03); AC-17, D2-AC-10, D2-AC-12, D2-AC-25, D4-AC-4, D6-AC-10. 2.4: D0.4, D1.3 (DD-5), D3.13 (AM-D3-3); AC-4, D2-AC-19, D3-AC-23. 2.5: D2.2 (F-3), D2.5 (DD2-2); D2-AC-1, D2-AC-3, D2-AC-13, D2-AC-24. 2.6: D2.5 (DD2-2), D8.12 (FC-5); D2-AC-1, D8-AC-17. 2.7: D0.2, D2.7; D2-AC-3, D2-AC-24, D9-AC-5. 2.8: D5.6, D7.6, D9.4 (VM-8); D5-AC-10, D7-AC-13, D9-AC-7. 2.9: D6.7 (CS-10), D3.4 (HK-1); D6-AC-13. 2.10: D0.4, D9.4 (VM-2); D9-AC-4, D8-AC-29. 2.11: D0.5, D3.9, D8.5 (BE-1 closure); D3-AC-17, D8-AC-4. 2.12: D3.4 (HK-1), D6.7; D6-AC-13, D9-AC-2. 2.13: D8.3 (DD8-10), D8.5 (IS); D8-AC-18. 2.14: D8.3 (DD8-11), D8.5 (CA); D8-AC-18.

**R3.** 3.1: D9.3 (DD9-1), D8.5 (ledger reconciliation); D9-AC-2, D9-AC-14, D8-AC-23. 3.2: D9.3 (DD9-3), D3.6 (record form); D9-AC-3, D8-AC-23. 3.3: D9.3 (DD9-3); D9-AC-3. 3.4: D0.1, D3.1; D3-AC-14, D3-AC-19, D9-AC-11. 3.5: D9.5, D9.6; D9-AC-11, D9-AC-10. 3.6: D3.7 (DD3-10, AT-1), D9.3 (DD9-9); D3-AC-7, D3-AC-12, D9-AC-10. 3.7: D3.7, D3.13 (AM-D3-3), D9.3 (DD9-9); D3-AC-7, D3-AC-12, D3-AC-23, D9-AC-10. 3.8: D3.7, D8.5; D3-AC-6, D3-AC-20, D3-AC-25, D9-AC-20. 3.9: D0.1, D9.5; D9-AC-14. 3.10: D9.5; D3-AC-19, D7-AC-17, D9-AC-14. 3.11: D8.5 (publication rule); D8-AC-22, D9-AC-20. 3.12: D8.5 (ledger reconciliation); D8-AC-23, D9-AC-20. 3.13: D8.3 (DD8-15), D9.3 (DD9-9); D8-AC-24, D9-AC-10, D9-AC-20. 3.14: D8.5 (publication rule), D9.4 (VM-16); D8-AC-22, D9-AC-20, RB-9.

**R4.** 4.1: D0.6, D9.7; D9-AC-19, D10-AC-8. 4.2: D0.10, D10.5, Components and Interfaces; D10-AC-8. 4.3: D10.9, D9.3 (DD9-2); D10-AC-8. 4.4: D9.5; D9-AC-14. 4.5: D9.7; D9-AC-19. 4.6: D9.6, D9.7; D9-AC-19, D9-AC-11. 4.7: D3.7 (ledger entry), D9.4 (VM-11); D3-AC-12, D9-AC-10. 4.8: D0.7, D10.9; D10-AC-9. 4.9: D0.4, D9.3 (DD9-2), D10.9; D10-AC-8.

**R5.** 5.1: D1.4, D1.12; AC-1. 5.2: D1.5, D1.12; AC-3. 5.3: D1.5, D1.9; AC-5. 5.4: D1.4, D1.5, D1.10; AC-2, AC-4. 5.5: D1.9; AC-6. 5.6: D1.3 (DD-7), D1.9; AC-7. 5.7: D1.7; AC-8. 5.8: D1.3 (DD-9), D1.8, D1.16 (OD-6); AC-9. 5.9: D1.12; AC-16. 5.10: D1.13; AC-15.

**R6.** 6.1: D1.6, D1.7; AC-11. 6.2: D1.6; AC-11. 6.3: D1.6; AC-11. 6.4: D1.6; AC-11. 6.5: D1.6; AC-11. 6.6: D1.6; AC-11. 6.7: D1.10; AC-13, AC-14. 6.8: D1.3 (DD-8, DD-11), D1.8; AC-10. 6.9: D1.8, D1.16 (OD-6); AC-12. 6.10: D1.3 (DD-1), D1.12; AC-16. 6.11: D1.6; AC-11.

**R7.** 7.1: D1.4, D1.10; D1 AC-2, D1 AC-13, D1 AC-14. 7.2: D1.10; D1 AC-13. 7.3: D1.10; D1 AC-13. 7.4: D1.10; D1 AC-13, D1 AC-14. 7.5: D2.3, D2.5 (DD2-5); D2-AC-5, D2-AC-6, D2-AC-18. 7.6: D2.5 (DD2-5), D2.8 (SM-3); D2-AC-5. 7.7: D2.6, D2.5 (DD2-2); D2-AC-2, D2-AC-13. 7.8: D2.5 (DD2-2); D2-AC-1. 7.9: D2.5 (DD2-8); D2-AC-11, SG-5. 7.10: D2.5 (DD2-2, DD2-8); D2-AC-1. 7.11: D2.5 (DD2-6, DD2-10); D2-AC-7, D2-AC-8, D2-AC-9, D2-AC-14, D2-AC-22, D2-AC-28. 7.12: D2.7; D2-AC-3, D2-AC-15, D2-AC-16, D2-AC-24. 7.13: D2.6, D2.8 (SM-1); SM-1, D9-AC-13, RB-14. 7.14: D2.12 (AM-11), D9.8; D9-AC-18, RB-14. 7.15: D2.8 (rollback), D9.7 (RP-3); D2-AC-17, D9-AC-19. 7.16: D2.3, D2.4; D2-AC-18, D2-AC-3. 7.17: D2.4; D2-AC-4, RB-16. 7.18: D2.4; D2-AC-4. 7.19: D6.11 (AM-D6-4), D8.12 (FC-3, FC-4); D8-AC-19, D2-AC-1. 7.20: D8.3 (DD8-2), D8.5 (KT); D8-AC-8. 7.21: D8.3 (DD8-4), D8.5 (UA); D8-AC-10. 7.22: D8.3 (DD8-3), D8.5 (RI); D8-AC-9. 7.23: D2.5 (DD2-4), D2.12 (AM-6), D8.9 (CU); D2-AC-10, D2-AC-25, D8-AC-20. 7.24: D2.5 (DD2-3, DD2-8, DD2-9), D2.12 (AM-7); D2-AC-12, D2-AC-26, D10-AC-1, D10-AC-2, D10-AC-3. 7.25: D2.12 (AM-9), D8.6 (P-h); D2-AC-28, D8-AC-21. 7.26: D2.6, D2.12 (AM-10); D2-AC-13, D10-AC-4, D10-AC-5.

**R8.** 8.1: D3.4, D3.6 (RN-2, RN-4), D3.7 (AT-1); D3-AC-2, D3-AC-12, D3-AC-14, D3-AC-16, D3-AC-23, D3-AC-24. 8.2: D3.7, D3.6 (RN-3, RN-9, RN-10); D3-AC-6, D3-AC-12. 8.3: D3.5 (PF-1 to PF-7); D3-AC-1, D3-AC-2, D3-AC-3, D3-AC-14. 8.4: D3.5 (HM-T1, HM-T2); D3-AC-1, D3-AC-2. 8.5: D3.3 (DD3-8), D3.4; D3-AC-4, D3-AC-9, D3-AC-24. 8.6: D3.6 (RN-8, RN-9); D3-AC-5, D3-AC-15, D3-AC-23. 8.7: D3.1, D3.7 (ST-1 to ST-5); D3-AC-19. 8.8: D3.3 (DD3-4), D3.6 (RN-12); D3-AC-4, D3-AC-8. 8.9: D3.4 (HK-7); D3-AC-1, D3-AC-4. 8.10: D3.6 (RN-7); D3-AC-5. 8.11: D3.7, D3.8 (S9); D3-AC-13, D3-AC-23. 8.12: D3.3 (DD3-3); D3-AC-4. 8.13: D3.9, D3.5 (HM-T5); D3-AC-4, D3-AC-15, D3-AC-17. 8.14: D3.4 (HK-0), D3.7; D3-AC-12. 8.15: D3.7 (AT-1 to AT-4), D3.8; D3-AC-7, D3-AC-12, D3-AC-20. 8.16: D3.8 (S3, S9), D3.13 (AM-D3-1); D3-AC-10, D3-AC-21. 8.17: D3.8 (PR-1 to PR-11), D3.13 (AM-D3-7); D3-AC-10, D3-AC-11, D3-AC-27. 8.18: D3.6 (RN-5), D3.8 (S4), D3.13 (AM-D3-6); D3-AC-5, D3-AC-10, D3-AC-26. 8.19: D3.8 (T-H1, S6, S11 to S13), D3.13 (AM-D3-6, AM-D3-7), D8.3 (DD8-15); D3-AC-10, D3-AC-27, D8-AC-25, D10-AC-6. 8.20: D8.3 (DD8-15), D3.13 (AM-D3-1); D8-AC-25, D3-AC-21.

**R9.** 9.1: D4.3, D4.12 (AM-D4-2), D4.13; D4-AC-1, D4-AC-2, D4-AC-18. 9.2: D4.6; D4-AC-5. 9.3: D4.4; D4-AC-3, D4-AC-4. 9.4: D4.6; D4-AC-6. 9.5: D4.6; D4-AC-4, D4-AC-6. 9.6: D4.5; D4-AC-8. 9.7: D4.5; D4-AC-7. 9.8: D4.3, D5.6; D4-AC-19, D5-AC-17. 9.9: D4.5; D4-AC-12. 9.10: D4.7; D4-AC-3, D4-AC-13, D4-AC-14. 9.11: D4.8; D4-AC-16. 9.12: D4.8; D4-AC-16. 9.13: D4.3, D4.4; D4-AC-2, D4-AC-3. 9.14: D4.4; D4-AC-9. 9.15: D4.8; D4-AC-17. 9.16: D4.5; D4-AC-10, D4-AC-11. 9.17: D4.7; D4-AC-15. 9.18: D4.7; D4-AC-5. 9.19: D4.4; D4-AC-3. 9.20: D4.7; D4-AC-3. 9.21: D8.3 (DD8-5), D8.5 (PR); D8-AC-11. 9.22: D4.12 (AM-D4-6), D4.13 (AM-D4-8), D8.4 (T8-29); D4-AC-18, D8-AC-28.

**R10.** 10.1: D5.4; D5-AC-6. 10.2: D5.5; D5-AC-9. 10.3: D5.2 (F5-1), D8.3 (DD8-14); D8-AC-28. 10.4: D5.4; D5-AC-2, D5-AC-7. 10.5: D5.5; D5-AC-1. 10.6: D5.4; D5-AC-4. 10.7: D5.4; D5-AC-3, D5-AC-15. 10.8: D5.3; D5-AC-8. 10.9: D5.3; D5-AC-8. 10.10: D5.3; D5-AC-8. 10.11: D5.7; D5-AC-8. 10.12: D5.7; D5-AC-8. 10.13: D5.3; D5-AC-8. 10.14: D5.3; D5-AC-8. 10.15: D5.9; D5-AC-5. 10.16: D5.7; D5-AC-8. 10.17: D5.7; D5-AC-8. 10.18: D5.5; D5-AC-9. 10.19: D5.6; D5-AC-10. 10.20: D5.3, D5.8; D5-AC-13. 10.21: D5.8; D5-AC-11, D5-AC-12, D5-AC-18. 10.22: D5.9; D5-AC-2, D5-AC-16. 10.23: D5.8; D5-AC-14. 10.24: D5.4; D5-AC-6. 10.25: D5.5; D5-AC-9. 10.26: D5.4; D5-AC-6. 10.27: D5.7; D5-AC-8. 10.28: D5.7; D5-AC-2, D5-AC-8. 10.29: D5.4; D5-AC-6. 10.30: D5.6, D5.9; D5-AC-6. 10.31: D5.6; D5-AC-7. 10.32: D5.3; D5-AC-1, D5-AC-13. 10.33: D5.3; D5-AC-8, D5-AC-13. 10.34: D5.8, D5.13 (AM-D5-12); D5-AC-11, D5-AC-12, D5-AC-18, D10-AC-7. 10.35: D5.12 (AM-D5-11), D5.13 (AM-D5-13); D5-AC-19.

**R11.** 11.1: D6.4, D6.5; D6-AC-3, D6-AC-14. 11.2: D6.6; D6-AC-2, D6-AC-5. 11.3: D6.6; D6-AC-6. 11.4: D6.5, D6.6; D6-AC-4. 11.5: D6.6, D6.7 (CS-10); D6-AC-13. 11.6: D6.6; D6-AC-7. 11.7: D6.7 (CS-01); D6-AC-1. 11.8: D6.7 (CS-03); D6-AC-10. 11.9: D6.7 (CS-02, CS-04 to CS-06, CS-09); D6-AC-10. 11.10: D6.7 (CS-07, CS-08); D6-AC-1. 11.11: D6.7; D6-AC-1. 11.12: D6.6; D6-AC-2. 11.13: D6.7; D6-AC-10. 11.14: D6.3, D6.5; D6-AC-12. 11.15: D6.4, D6.8; D6-AC-3, D6-AC-8, D6-AC-9, D6-AC-11, D6-AC-12, D6-AC-14. 11.16: D6.11 (AM-D6-1), D8.8; D8-AC-12, D6-AC-8, D6-AC-9. 11.17: D6.11 (AM-D6-2), D8.8; D6-AC-3, D8-AC-12. 11.18: D6.11 (AM-D6-3), D8.8; D8-AC-12.

**R12.** 12.1: D7.5; D7-AC-5. 12.2: D7.5; D7-AC-6. 12.3: D7.5; D7-AC-6. 12.4: D7.5; D7-AC-3. 12.5: D7.5; D7-AC-6. 12.6: D7.3 (DD7-2); D7-AC-17. 12.7: D7.5, D7.6; D7-AC-7. 12.8: D7.4; D7-AC-2. 12.9: D7.4; D7-AC-12. 12.10: D7.4; D7-AC-11. 12.11: D7.8; D7-AC-15. 12.12: D7.9; D7-AC-10. 12.13: D7.3 (DD7-1); D7-AC-1, D8-AC-15. 12.14: D7.7; D7-AC-14, D7-AC-18. 12.15: D7.6; D7-AC-6. 12.16: D7.6; D7-AC-8, D7-AC-9, D7-AC-13. 12.17: D7.8; D7-AC-15, D7-AC-16. 12.18: D7.8; D7-AC-16. 12.19: D7.4, D7.7; D7-AC-4. 12.20: D7.4; D7-AC-2, D7-AC-3. 12.21: D7.11 (AM-D7-1); D7-AC-1, D7-AC-2, D8-AC-29. 12.22: D7.6, D7.11 (AM-D7-2); D7-AC-5, D7-AC-6. 12.23: D7.11 (AM-D7-3); D8-AC-15, D9-AC-8. 12.24: D7.5, D7.11 (AM-D7-4); D7-AC-6, D7-AC-7, D7-AC-13.

**R13.** 13.1: D8.4; D8-AC-1. 13.2: D8.4; D8-AC-1. 13.3: D8.4; D8-AC-1. 13.4: D8.6; D8-AC-2. 13.5: D8.6 (P-a to P-e); D8-AC-2. 13.6: D8.7; D8-AC-3, D8-AC-14. 13.7: D8.6; D8-AC-2. 13.8: D8.13; D8-AC-8, D8-AC-9, D8-AC-12, D8-AC-16, D8-AC-18. 13.9: D8.14, D9.4; D8-AC-29, D9-AC-4. 13.10: D8.13; D8-AC-29. 13.11: D3.9, D8.5 (BE-1 closure); D8-AC-4, D8-AC-5. 13.12: D8.5 (BE-2 closure); D8-AC-7. 13.13: D8.5; D8-AC-4, D8-AC-7. 13.14: D8.7; D8-AC-19. 13.15: D8.13; D8-AC-30. 13.16: D8.5 (KT); D8-AC-8. 13.17: D8.5 (RI, CA), D8.9 (CU); D8-AC-9, D8-AC-18, D8-AC-20. 13.18: D8.5 (UA); D8-AC-10. 13.19: D8.5 (PR); D8-AC-11. 13.20: D8.8 (PD); D8-AC-12. 13.21: D8.7; D8-AC-13, D8-AC-14. 13.22: D8.10 (DR); D8-AC-15. 13.23: D8.11 (PC); D8-AC-16. 13.24: D8.12 (FC), D8.5 (IS); D8-AC-17, D8-AC-18. 13.25: D8.5 (Windows oracle, Python minimum); D8-AC-5. 13.26: D8.5 (BE-2 closure); D8-AC-6. 13.27: D8.3 (DD8-13); D8-AC-27. 13.28: D8.3 (DD8-14); D8-AC-28.

**R14.** 14.1: D9.4; D9-AC-2. 14.2: D9.4 (VM-5); D9-AC-2. 14.3: D9.3 (DD9-7), D9.4 (VM-6); D9-AC-5. 14.4: D9.4 (VM-6); D9-AC-5. 14.5: D9.4 (VM-7); D9-AC-6. 14.6: D9.4 (VM-7); D9-AC-6. 14.7: D9.4 (VM-7); D9-AC-6. 14.8: D9.3 (DD9-3), D9.5; D9-AC-3. 14.9: D9.5, D9.4 (VM-15); D9-AC-3. 14.10: D9.6; RB-1, RB-2, D9-AC-11. 14.11: D9.5, D9.6; D9-AC-11. 14.12: D9.5; D9-AC-14. 14.13: D9.3 (DD9-5); D9-AC-15. 14.14: D9.4 (VM-13); D9-AC-16. 14.15: D9.5; D9-AC-17. 14.16: D9.3 (DD9-1, DD9-2); D9-AC-1. 14.17: D9.5, D9.4 (VM-14); D9-AC-13. 14.18: D9.4 (VM-8); D9-AC-7. 14.19: D9.5, D9.6 (RB-12, RB-13), D9.4 (VM-3, VM-11); D9-AC-2, D9-AC-11. 14.20: D9.3 (DD9-4), D9.4 (VM-10); D9-AC-9, D8-AC-26. 14.21: D9.3 (DD9-2, DD9-7), D9.4 (VM-1); D9-AC-1, D9-AC-2. 14.22: D9.4 (VM-4); D9-AC-4. 14.23: D9.4 (VM-6, VM-7); D9-AC-5, D9-AC-6. 14.24: D9.4 (VM-8, VM-9); D9-AC-7, D9-AC-8. 14.25: D9.3 (DD9-9), D9.4 (VM-11); D9-AC-10. 14.26: D9.6, D9.7, D9.8; D9-AC-11, D9-AC-18, D9-AC-19. 14.27: D9.6 (RB-4), D9.4 (VM-19); D9-AC-12.

**R15.** 15.1 to 15.10: D0.7, D9.4 (VM-17); D9-AC-21.

**R16.** 16.1: D3.7 (credits), D9.4 (VM-18); D9-AC-22. 16.2: D3.7 (credits), D8.3 (DD8-15), D9.4 (VM-18); D3-AC-20, D8-AC-24, D9-AC-22. 16.3 to 16.5: D3.7 (credits), D9.4 (VM-18); D9-AC-22.

**Coverage check.** A script over `requirements.md` and this file lists every criterion, and finds for each at least one section and one row in the entries above. No criterion lacks either. Row D10-AC-8 repeats the check. The entries show where a criterion is handled, not that its rows pass. Every row stays UNVERIFIED.

**Substantive review.** A mention of a criterion number is not coverage. The criteria that the coverage check found without any earlier section or row (7.24, 7.26 and 8.19) and the criterion whose tests existed only in decision text (10.34) were taken apart and checked element by element against the design text and the rows. "Row added" means that no earlier row tested the element, and a row of D10-AC was added.

| Criterion | Element | Designed in | Tested by | Result |
|---|---|---|---|---|
| 7.24 | One credential per invitee, issued out of band, and no other credential accepted | D2.12 (AM-7) | D2-AC-26, SM-6, D10-AC-1 (adds a never-issued value) | Partial, row added |
| 7.24 | At least 128 bits of entropy | D2.12 (AM-7) | D10-AC-1 | Row added |
| 7.24 | Stored only as a hash | D2.12 (AM-7), D2.5 (DD2-8) | D10-AC-1 | Row added |
| 7.24 | Label, expiry inside the demonstration window, revocation flag | D2.12 (AM-7) | D10-AC-1 | Row added |
| 7.24 | Revocation without a redeploy within a documented bound, other credentials stay valid | D2.12 (AM-7) | D2-AC-26 (60 s, ASSUMED) | Covered |
| 7.24 | Failed attempts are rate limited | D2.12 (AM-7). Initial value set by OD-D10-1 (D10.10). | D10-AC-2 | Row added, value decided |
| 7.24 | No credential value in logs | D2.12 (AM-7), D2.5 (DD2-9) | D2-AC-26, D2-AC-12 | Covered |
| 7.24 | No HTTP administrative route that lists, decrypts or deletes cases | D2.5 (DD2-3 tier A), D2.11 (OD-D2-6) | D10-AC-3 | Row added |
| 7.26 | An internal liveness check with no public route, for the loopback answer and both children | D2.6 | D10-AC-4 | Row added |
| 7.26 | 200 only if the socket re-attests, the custody store opens, free space is above a documented threshold and run-slot accounting is not wedged | D2.6, D2.5 (DD2-6, 15 percent, ASSUMED) | D2-AC-13 (the socket check only), D10-AC-5 | Partial, row added |
| 7.26 | Each check result is reused for at most 5 s | D2.6 | D10-AC-5 | Row added |
| 7.26 | A failed check gives 503 with the same body shape and `status` `unavailable`, refuses new runs and keeps `isolationMode` | D2.6, D5.8 (row 3) | D2-AC-13 (503 after replacing the socket), D10-AC-5 | Partial, row added |
| 7.26 | The body holds only the six named fields | D2.6 | D2-AC-13 | Covered |
| 8.19 | Every executable hook configuration file is unchanged during a session | D3.8 (T-H1, S6, S11 to S13), D3.13 (AM-D3-6, AM-D3-7) | D3-AC-10 (names the hook files, the runner and `mcp.json`), D3-AC-27, D10-AC-6 | Partial, row added |
| 8.19 | An added, removed or changed file voids the review of the changed surface | D3.13 (AM-D3-7) | D3-AC-27 | Covered |
| 8.19 | No dependent hook evidence counts until a renewed review by a reviewer other than the agent | D3.13 (AM-D3-7), D3.7 (AT-1 e) | D3-AC-27, D10-AC-6 | Partial, row added |
| 8.19 | The same set is pinned in the contained environment | D8.3 (DD8-15, CE-5) | D8-AC-25 | Covered |
| 10.34 | One version served, one lockstep change | D5.8, D5.13 | D5-AC-11 | Covered |
| 10.34 | Migration section with a before example, an after example and a checklist | D5.13 (AM-D5-12) | D10-AC-7 | Row added |
| 10.34 | Tolerant client, strict validator and mutual refusal naming both versions | D5.13 (AM-D5-12) | D10-AC-7 | Row added |
| 10.34 | Bundles written under 1.1.0 keep verifying and replaying | D5.13 (AM-D5-12) | D5-AC-1, D9-AC-8 | Covered |

Two criteria were mapped to rows that test only part of them: the 5 s recording bound of 3.2 (OD-D10-2) and the handling of a rollback that does not complete in 4.6 (OD-D10-3). Both gaps are closed by decision in D10.10, and `tasks.md` carries the tests.

**Gap-closing rows.** All rows are UNVERIFIED until an Execution_Record exists.

| ID | Criterion | Method | Pass threshold | Req | Host |
|---|---|---|---|---|---|
| D10-AC-1 | Invitation credential record | Issue 3 credentials with the issuing procedure. Inspect the issued values and the stored records (the edge secret or the API-side table). Send a value that was never issued. | Each issued value carries at least 16 random bytes from the operating-system CSPRNG (length checked by test, source checked by code review). Each stored record holds a hash and no credential value, a label, an expiry no later than the end of the demonstration window and a revocation flag. A search of the stored records, the container output and the logs for each issued value finds 0 matches. The never-issued value gets 401 before any body byte is read. | 7.24 | CI or VM |
| D10-AC-2 | Failed-attempt limit | Send failed credential attempts from one client address faster than the documented limit, then a valid credential from another client address | The attempt over the limit gets 429 `RATE_LIMITED` with `Retry-After`. The valid credential from the other client still works. The limit is 5 failed attempts per 15 minutes per source and account (OD-D10-1), configurable within documented bounds, and the limit and its window are documented. 0 credential values appear in logs. | 7.24 | CI or VM |
| D10-AC-3 | No administrative route | Enumerate every application and edge route and compare it with the contract paths and the static paths of D2.3 | 0 routes list cases, decrypt a case or delete a case. A route added in a copy for one of those purposes makes the check fail. | 7.24 | CI or VM |
| D10-AC-4 | Liveness | Run the internal liveness probe with both children alive, with the examiner stopped and with the custodian stopped. Request every public path for a liveness route. | The probe exits 0 only when the API answers on loopback and both processes exist, and non-zero in the other two cases. 0 public liveness routes. | 7.26 | CI or VM |
| D10-AC-5 | Readiness checks | Fail each of the four checks in turn: replace the examiner socket with a non-examiner uid, make the custody store unopenable, fill the data volume below the threshold, wedge the run-slot accounting. Repeat a request inside 5 s and after 5 s. | Each failure gives 503 with the key set of the 200 body, `status` `unavailable` and `isolationMode` unchanged. A `POST /runs` is refused while a check fails. The body never names the failed check. A repeat inside 5 s does not run the check again, and one after 5 s does. | 7.26 | CI or VM |
| D10-AC-6 | Hook surface set | Compare the files that the session hash check (D3-AC-10) and the HM-T5 check (D3-AC-27) cover with the set that 8.19 names. Add a file under `scripts/hooks/` in a temporary copy. Present a renewed-review record whose reviewer is the agent. | 0 members of the 8.19 set are missing from either hash set, including the matcher corpus and the environment allowlist of the runner. The added file changes the set hash and the check fails with renewed review required. The record of the agent is rejected. | 8.19 | Windows, Linux CI, Owner (Windows) |
| D10-AC-7 | Contract 2.0.0 compatibility | Run a tolerant 1.1.0 client and a strict 1.1.0 validator against the 2.0.0 examples. Point the UI_Kit at a server of another major version and a server at a UI_Kit of another major version. Read the migration section of `docs/API_CONTRACT.md`. Replay the 1.1.0 corpus. | The tolerant client works. The strict validator fails on exactly the BREAKING rows of D5.8 and nothing else. Each refusal names both versions. The migration section has a before example, an after example and a client checklist for each BREAKING row. Bundles written under 1.1.0 verify and replay. | 10.34 | Windows, Linux |
| D10-AC-8 | Coverage and register check | A script reads `requirements.md` and this file. It lists every criterion and finds at least one section and one row for it in D10.5. It finds a non-empty Req cell for every row of the Components and Interfaces table. It checks that the Track register has one entry for each of P0 to P8. Once `tasks.md` exists, it checks that every task cites at least one criterion and every checkbox follows its record. | 0 criteria without a section and a row. 0 components without a requirement. 0 unresolved identifiers in D10.5. 9 of 9 register entries. | 4.1, 4.2, 4.3, 4.9 | Windows, Linux |
| D10-AC-9 | Steering preserved | `git diff --name-status 84df25c S -- .kiro/steering` | Only added files appear. 0 modified or deleted files. Each added file is a new rule. | 4.8 | Windows, Linux |

**TPR additions to D10.5.** The entries below cover the criteria that the task-plan review round added or changed. 3.2 and 3.5 (recorder): D10.11 TR-4; D10-AC-10. 3.15: D10.11 TR-4; D10-AC-11. 4.5 and 4.7: D10.11 TR-13; D10-AC-29. 4.10: D10.11 TR-8; D10-AC-17, RB-20. 7.27: D10.11 TR-11; D10-AC-21. 10.37: D10.11 TR-10; D10-AC-20. 13.11 (amended): D10.11 TR-5, TR-10; D10-AC-14, D10-AC-20. 13.13 (amended): D10.11 TR-1, TR-9; D10-AC-18, D10-AC-28. 13.29: D10.11 TR-18; D10-AC-27. 13.30: D10.11 TR-10; D10-AC-19. 14.10 and 14.11 (checkpoints): D10.11 TR-7; D10-AC-16, RB-19. 14.16 and 14.21 (amended): D10.11 TR-2; D10-AC-12, D9-AC-1. 1.4 to 1.7, 1.10, 1.11, 1.15, 1.16, 2.7, 2.10 and 14.4: D10.11 TR-13; D10-AC-29.

### D10.6 Remediation register

This is the shorter form of `docs/next-phase/REVIEW_REMEDIATION_REGISTER.md`. The independent review text is not stored in this repository. The summaries are the maintainer's one-line wording, and the mapping of a summary to a code defect stays UNVERIFIED where the summary names none. Every row is UNVERIFIED for Requirement 3 until an Execution_Record exists.

| ID | Disposition | Where | Status |
|---|---|---|---|
| H-1 | DD8-9: Private_Original kept private, Sanitized_Copy published with its own hash, zero-hit scan | D8.3, D8.5, D8-AC-22 | DESIGNED, AMENDED, APPLIED (documentation) |
| M-1 | DD8-2: the vault key is never a process argument | D8.3, D8.5, D8-AC-8 | DESIGNED, AMENDED |
| M-2 | DD8-3: replay evidence is isolated from the trusted root | D8.3, D8.5, D8-AC-9, D8-AC-20 | DESIGNED, AMENDED |
| M-3 | DD9-4: dispatch on the Phase_Branch with a head SHA check | D9.3, D8-AC-26, D9-AC-9 | DESIGNED, AMENDED |
| M-4 | BE-1 closure with a Windows oracle, 13.11 rewritten, 8.13 scoped | D8.5, D3.9, D8-AC-4, D8-AC-5 | DESIGNED, AMENDED |
| M-5 | DD8-15: Contained_Hook_Environment | D8.3, D8-AC-25 | DESIGNED, AMENDED |
| M-6 | DD8-13: External_Review_Record | D8.3, D8-AC-27, D9-AC-12 | DESIGNED, AMENDED |
| M-7 | DD8-14: complexity budget | D8.3, D8-AC-28 | DESIGNED, AMENDED |
| L-1 | DD8-10: isolation semantics | D8.3, D8.5, D8-AC-18 | DESIGNED, AMENDED |
| L-2 | DD8-11: the examiner authenticates the custodian | D8.3, D8.5, D8-AC-18 | DESIGNED, AMENDED |
| L-3 | DD8-6, DD8-7: Python 3.12.4 on Windows, the O1 oracle, an `AuthzAccessCheck` spike | D8.3, D8.5, D8-AC-5 | DESIGNED, AMENDED. The spike is UNVERIFIED. |
| L-4 | Ledger lint and the baseline reconciliation (C-006 to C-008) | D8.5, D8-AC-23 | DESIGNED, AMENDED, APPLIED (documentation) |
| L-5 | DD8-15 and DD9-9: Kiro evidence is preserved, never reconstructed | D8.3, D9.3, D8-AC-24 | DESIGNED, AMENDED |
| L-6 | DD8-5: Approved_Root and the safe-open helper | D8.3, D8.5, D8-AC-11 | DESIGNED, AMENDED |
| L-7 | DD8-4: upload admission before buffering | D8.3, D8.5, D8-AC-10 | DESIGNED, AMENDED |

| Decision | Where | Criteria | Status |
|---|---|---|---|
| AM-D4-8: `mcp` `>=2.3,<2.4` with one exact pin | D4.13 | 9.22 | DECIDED, DESIGNED |
| AM-D5-12: contract 2.0.0 with migration and compatibility tests | D5.13 | 10.21, 10.34 | DECIDED, DESIGNED |
| AM-D5-13: judge UI constant and label only | D5.13 | 1.8, 10.35 | DECIDED, DESIGNED |
| AM-D6-1 to AM-D6-3: fail-closed loading, duplicate rejection, provenance binding | D6.11 | 11.16 to 11.18 | DECIDED, DESIGNED |
| AM-D6-4: profile propagation | D6.11 | 7.19 | DECIDED, DESIGNED |
| AM-D7-1: `CA` to `ZZ` fixture hunks | D7.11 | 12.13, 12.21 | DECIDED, DESIGNED |
| AM-D7-2: read-only retrieval authorization | D7.11 | 12.22 | DECIDED, DESIGNED. No retrieval was made. |
| AM-D7-3: version-aware historical replay | D7.11 | 10.5, 12.23 | DECIDED, DESIGNED |
| AM-D7-4: preserved source artifacts | D7.11 | 12.24 | DECIDED, DESIGNED |

### D10.7 Status ledger

| Label | Items |
|---|---|
| IMPLEMENTED | None |
| VERIFIED | None. No Release_Candidate is selected, and VERIFIED needs a SUCCEEDED Execution_Record for it (3.9). |
| Recorded baseline results | The 26 canonical executions at `84df25c`, taken from the Execution_Index (45 raw records, 14 superseded duplicates, 5 execution errors). Their Outcome_Classes are in ledger rows E-001 to E-026, where E-025a and E-025b come from one run. `pytest -m "not isolation"` gave 444 passed, 2 failed (BE-1, BE-2), 5 skipped and 4 deselected, with 455 tests collected. The UI gave 19 Vitest tests passed. The four container gates and the offline replay exited 0 with `--network none`. These results are baseline results and are not evidence for a Release_Candidate. |
| DESIGNED | Every track D1 to D9, the canonical sections and D10. A DECIDED item is designed and not implemented. |
| UNVERIFIED | From D0.9: Browser E2E, `scripts/gate_nov22.sh`, the five cases that skip on Windows, automatic hook execution, a public deployment, per-test Linux evidence for BE-1 and BE-2, CI on this branch, and the items not established from the historical record. From D9.6: every blocker row until its record exists for S, the Kiro captures and the External_Review_Record. Every acceptance row of D1 to D10, the `AuthzAccessCheck` spike and each mapping of a review finding to a code defect. |
| NOT_AVAILABLE | Credits for this phase (16.2). U-001 to U-005 are separately observed usage evidence, are not summed and are not attributed. |

### D10.8 Open decisions and blockers

Each row names who decides or acts. No blocker is an agent action.

**Open decisions by section.** The IDs are defined in the section named. A row lists what is still open and what a record closed.

| Section | Open | Closed by a record | Decider |
|---|---|---|---|
| D1 | None | OD-1 to OD-9 (D1.16) | Maintainer |
| D2 | OD-D2-2 (`OPEN_SYNTHETIC`, recommended off), OD-D2-5 (client address in logs, recommended omit), OD-D2-6 (deletion endpoint, recommended none), OD-D2-7 (slimmer image), B-3 (values N and M), B-6 (domain, certificate owner, credential distribution, log and metric destinations) | OD-D2-1 (AM-1), OD-D2-3 (AM-D5-12), OD-D2-4 (AM-4) | Maintainer, owner |
| D3 | OD-D3-1, OD-D3-2, OD-D3-3 (read with DD8-7), OD-D3-5, OD-D3-6, OD-D3-7, OD-D3-9, OD-D3-10, OD-D3-11, B-H1, B-H3, B-H5 | OD-D3-4 (DD8-6), OD-D3-8 (AM-D3-1) | Maintainer, owner |
| D4 | OD-D4-3, R-D4-1, R-D4-2, R-D4-4 | OD-D4-1 (AM-D4-1), OD-D4-2 (AM-D4-3), OD-D4-4 (AM-D4-5), OD-D4-5 (AM-D4-6, AM-D4-8), R-D4-3 (DD8-5) | Maintainer |
| D5 | OD-D5-2, OD-D5-6, OD-D5-7, OD-D5-8, OD-D5-9, R-D5-1 to R-D5-5 | OD-D5-1 (AM-D5-12), OD-D5-3 (AM-D5-6), OD-D5-4 (AM-D5-5), OD-D5-5 (AM-D5-11, AM-D5-13) | Maintainer |
| D6 | OD-D6-1, OD-D6-3, OD-D6-6, OD-D6-7, R-D6-1 to R-D6-4 | OD-D6-2 (AM-D6-1), OD-D6-4 and OD-D6-5 (AM-D6-2), G-D6-1 (AM-D6-4) | Maintainer |
| D7 | OD-D7-2, OD-D7-4, OD-D7-6, OD-D7-7, OD-D7-8, OD-D7-9 (carrier of the Examination_Semantics id), B-D7-2 (review pending), R-D7-1 to R-D7-4 | B-D7-1 (AM-D7-1), OD-D7-1 (AM-D7-4), OD-D7-5 (AM-D7-3), OD-D7-3 and G-D7-1 (AM-D5-12) | Maintainer, reviewer |
| D8 | OD-D8-1 to OD-D8-9, R-D8-1 to R-D8-5 | None | Maintainer, owner |
| D9 | OD-D9-3 to OD-D9-7, R-D9-1 to R-D9-8 | OD-D9-1 (D10.10), OD-D9-2 (the requirement amendment) | Maintainer, owner |
| D10 | None | OD-D10-1 to OD-D10-4 (D10.10) | Maintainer |

**Open decisions found while writing D10.**

| ID | Item | Options | Recommendation |
|---|---|---|---|
| OD-D10-1 | The limit and window for failed credential attempts (7.24). AM-7 requires a rate limit and D2 sets no value. | A fixed value now, or a value chosen at implementation from the D2-AC-14 measurement | DECIDED (D10.10): 5 failed attempts per 15 minutes per source and account, configurable and bounded. |
| OD-D10-2 | The 5 s bound of 3.2. D9 records start and end times (DD9-1) and no record time, so the bound has no mechanical check. | A reviewed process rule, or a `recorded_utc` field in the Execution_Record checked by `report-lint` | DECIDED (D10.10): keep the 5 s target. Recording failures are visible and never `SUCCEEDED`. |
| OD-D10-3 | A rollback that does not complete (4.6). D9.7 gives a confirmation for each row and no wording for the per-track record. | The RP row is FAILED, the track line says incomplete and earlier rows stay unchanged (3.5), or a separate status | DECIDED (D10.10): a failed rollback blocks the release and needs recovery to a verified checkpoint. |
| OD-D10-4 | The reading of 13.5(a) and P-a over bytes of the zip container that no check covers (RC-22, CP-29) | Read the property over the manifest, the listed members and the envelope and state the limit in `docs/SIGNING.md`, or extend integrity to the container (a format change, outside this phase) | DECIDED (D10.10): three separate results. Exact archive-byte verification needs an external trusted digest. |

**Blockers.** The release blockers RB-1 to RB-17, RB-19 and RB-20 and their levels are in D9.6. RB-18 is in D10.10.

| ID | Blocker | Who |
|---|---|---|
| B-D8-1 | A Linux_Docker_Host full-checkout run: the BE-2 Linux leg, the Linux per-test baseline and every row marked for a Linux host | Owner |
| B-D8-2 | An External_Review_Record | Owner or an independent reviewer |
| B-D8-3 | A dedicated VM or a restricted account for the Contained_Hook_Environment, and the Kiro captures that need it (B-H2) | Owner |
| OD-D9-1 | DECIDED (D10.10): evidence commits reference the exact tested Release_Candidate SHA. A different commit is not automatically the same tested candidate. | Closed |
| D2 B-1, B-6, B-8, hosting, domain, certificate, budget, monitoring and the go decision | Public_Deployment_Readiness. Not authorized by this design. | Owner |
| Review | Maintainer review of D8, D9, D10 and the canonical sections | Maintainer |
| OA-00 | Owner acceptance of D8 to D10 (including D10.11) and of the corrected task plan, recorded as `ACCEPTED`, `ACCEPTED_WITH_CONDITIONS` or `REJECTED` (4.10). No implementation task starts without it. OA-08 holds the decisions OD-D8-1 to OD-D8-4 that PH1-11, PH1-16, PH1-17 and PH2-02 consume (RB-20) | Owner, maintainer |

### D10.9 Files for implementation

`tasks.md` was written after the final decisions of 2026-11-25. Every task cites at least one criterion (4.3, D10-AC-8). The file lists of each track are in the sections named below, and none of these files is changed now.

| Track | New or changed | Not changed | Section |
|---|---|---|---|
| P0 | `ui-kit/src` (tokens, decimal, status, shell, feedback, components, api, types), `apps/landing/web`, the two app `App.tsx` and `vite.config.ts` files, root `package.json`, `scripts/ui_e2e.sh`, `tests/ui/e2e_browser.cjs`, Vitest files | `core/`, `api/`, `tests/contract`, `ui/judge`, the Submission_Artifacts | D1.12 |
| P1 | `deploy/entrypoint.sh`, `Dockerfile`, `.dockerignore`, `core/src/verdictkit/api/`, `examiner/worker.py`, an edge image with its configuration, the base-path and route-check scripts | `api/openapi.yaml` (owned by D5), `ui/judge` | D2.3 to D2.8 |
| P2 | `scripts/hooks/vk_hook.py`, `.kiro/hooks/*.json`, `tests/contract/test_hook_matchers.py`, `test_hook_runner.py`, `hook_matcher_corpus.json`, `scripts/hooks/check_matchers.cjs`, the BE-1 test change and its Windows helper, records under `docs/next-phase/hooks/` | Existing tests, except the approved BE-1 hunk | D3.4 to D3.9 |
| P3 | `core/src/verdictkit/mcp_server.py`, the contract-version module, `core/pyproject.toml`, `.kiro/settings/mcp.json` (flag, renewed review), `docs/MCP_SERVER.md`, `docs/mcp/schemas/`, `docs/next-phase/kiro-mcp/`, tests | Existing MCP tests, except the BE-1 hunk | D4.11 |
| P4 | `bundle.py`, `signing.py`, the contract-version module, `cli.py`, `api/{server,presenter,run_service}.py`, `mcp_server.py`, `api/openapi.yaml`, `api/examples/*.json`, `ui-kit/src/{api,types,components}`, `docs/API_CONTRACT.md`, `docs/SIGNING.md`, `deploy/entrypoint.sh`, the `ui/judge` constant and label | Existing bundle tests | D5.11, D5.13 |
| P5 | `core/src/verdictkit/sdk/`, `cli.py` (`_load_registry`), `docs/SDK.md`, `tests/sdk/`, `tests/contract/test_sdk_fence.py`, the provenance build step | `plugin.py`, `examples/` | D6.10, D6.11 |
| P6 | `rules_v2.py`, `sources_v2.py`, `claim_type.py`, `scripts/rules_snapshot.py`, `rules/v2/`, `.gitattributes`, `docs/REGULATORY_SNAPSHOTS.md`, tests, the `CA` to `ZZ` fixture hunks | `TX.json`, `rules/MANIFEST.json`, `rules.py`, `sources.py`, `docs/B7_TEXAS_SPEC.md` | D7.10, D7.11 |
| P7 | `deploy/entrypoint.sh` (key file), `examiner/worker.py`, `examiner/client.py`, `api/server.py`, `mcp_server.py`, the provenance loader check, `docs/next-phase/THREAT_MODEL.md`, tests under `tests/security`, `tests/adversarial` and `tests/contract`. `docs/next-phase/EVIDENCE_REDACTION.md` is already in the repository. | Existing passing tests, except the approved hunks | D8.15 |
| P8 | `scripts/gate_e2e.py` with `gate-e2e`, `scripts/release_verify.py`, `tests/release/`, `.github/workflows/p0-integration.yml`, `scripts/gate_nov22.sh`, `RELEASE_REPORT.md`, `REPRODUCING_VERIFICATION.md`, `TEST_INVENTORY.*.txt` | `scripts/gate_http.py`, existing tests, `m3b-api-checks.yml`, the Frozen_Release refs | D9.10 |

### D10.10 Final maintainer decisions

Recorded 2026-11-25. These five decisions close OD-D9-1 and OD-D10-1 to OD-D10-4. Each is DECIDED and DESIGNED. None is implemented, and no Execution_Record exists for any of them. Where a decision differs from earlier text, this section governs (D10.2, rows 23 to 27).

| ID | Decision | Criteria | Effect | Carried by |
|---|---|---|---|---|
| OD-D9-1 | Evidence commits reference the exact tested Release_Candidate SHA. A different commit is not automatically the same tested candidate. | 14.16, 14.21 | Every Execution_Record of the release run and every Evidence_Commit names the full 40-character SHA S of the tested Release_Candidate. A later commit is a different commit. It never counts as the same tested candidate. It is an Evidence_Commit only under the rule of D10.11 TR-2 (TPR-C-2 replaced the earlier path check over `docs/next-phase/**` and the spec `tasks.md`, because that set held Test_Inputs), and the release report names both SHAs. Any other change is a new Release_Candidate. 14.21 is reconciled with this rule in `requirements.md`. | tasks.md, Phase 7 |
| OD-D10-4 | Manifest integrity, signature authenticity and complete archive-byte integrity are three separate results. Exact archive-byte verification requires an external trusted digest. | 10.14, 10.15, 10.36, 13.5(a), 14.24 | Property P-a (CP-29, D5-AC-16) is stated over the verified region: the canonical manifest, every manifest-listed member, the signature envelope and the embedded public key. A byte of the zip container outside that region is covered by no check in the Bundle (F5-2, R-D5-4). No format change and no new input is added. `docs/SIGNING.md` states the limit. No document, UI text, API field, CLI output or MCP result says or implies that a Bundle is byte-for-byte intact. `requirements.md` is reconciled by 10.36 (new), 13.5(a) and 14.24 (in place). | tasks.md, Phase 3 and Phase 5 |
| OD-D10-1 | The initial failed-authentication threshold is five attempts per 15 minutes per source and account. The threshold is configurable and bounded. | 7.24 | D10-AC-2 tests this value. The bounds and the setting names are chosen at implementation and recorded as ASSUMED. A value outside the bounds is rejected at start-up and is not clamped (2.4). No credential value appears in logs. | tasks.md, Phase 5 |
| OD-D10-2 | The five-second recording target of 3.2 is retained. A recording failure is visible and cannot create a successful evidence claim. | 3.2, 3.4, 3.5, 3.9 | Each Execution_Record carries the UTC time at which it was written, and `report-lint` compares it with the end time of the command (the mechanism recommended in the open decision). A record written more than 5 s after the command ended, or with either time missing or unreadable, is listed in the lint output and in the release report as a recording failure. It never becomes `SUCCEEDED`: the capability it would support stays `UNVERIFIED` until a valid record exists, and the late record stays in the ledger (3.5). | tasks.md, Phase 1 and Phase 7 |
| OD-D10-3 | A rollback that does not complete blocks the release and requires recovery to a verified checkpoint. | 4.6, 14.10, 14.26 | 4.6 stands: the RP row is `FAILED`, the track line says incomplete and earlier rows stay unchanged (3.5). In addition, release blocker RB-18 (level LOCAL) is open until the Phase_Branch is recovered to a verified checkpoint, which is a commit whose phase regression set has a `SUCCEEDED` Execution_Record. The recovery is a new commit that restores that commit's tree, and the regression set is rerun after it. No history reset, no force push and no change to `master` or a tag (D9.7). | tasks.md, Phase 7 and each phase checkpoint |

### D10.11 Task-plan review remediation (TPR)

Recorded 2026-11-26. An independent review of `tasks.md` reported 31 findings: TPR-C-1 to TPR-C-4 (critical), TPR-H-1 to TPR-H-10 (high), TPR-M-1 to TPR-M-12 (medium) and TPR-L-1 to TPR-L-5 (low). The review text is not stored in this repository, as for D10.6. This section holds the design rules that answer the findings. Every rule is DESIGNED and UNVERIFIED, and none is implemented. The rules are proposals until the owner records OA-00 (4.10). Writing this section is not an owner decision. Where a rule differs from earlier text, this section governs (D10.2, rows 28 to 36). The matrix of findings, files, tasks, rows and resolutions is in `docs/next-phase/REVIEW_REMEDIATION_REGISTER.md`.

**TR-1 Legs and deferred Linux verification (TPR-C-1).** A row that has a Windows leg and a Linux leg is two rows. The Windows leg, and every row that the agent runs on the Windows host or on a Linux_Docker_Host that it can reach, is an autonomous completion row: it decides the box of its task (4.9) and every later dependency. A Linux leg that needs a full checkout (BE-1, BE-2, the Linux per-test baseline, the five cases that skip on Windows) is a deferred row, listed as DLV-1 to DLV-4 in `tasks.md`. A deferred row is UNVERIFIED until a `SUCCEEDED` Execution_Record that names a Linux source exists. A Windows result never sets it, and neither a deferred row nor the owner's Linux run (OA-02) blocks a box of Phases 1 to 6. An owner item blocks a task only where that task names it in Depends on (the GATE items OA-00, OA-07a and OA-08, and the reviewer records OA-07c to OA-07e of Phase 6). It is a mandatory release gate: 13.12, 13.13 and 13.26 are `SUCCEEDED` in a track record only when both legs are, RB-1 and RB-3 stay open while a leg is missing, and PH7-17 runs every deferred row again on S. A deferred row that fails reopens its task, and the box is unticked in the same change as the `FAILED` record. The Windows leg needs at least 30 Windows trials where a row asks for trials, and the Linux leg needs at least 30 Linux trials. The source of a Linux record is the autonomous route (TR-9) or an owner run (OA-02), and the record names which.

**TR-2 Candidate, Evidence_Commit and Test_Input (TPR-C-2, TPR-M-10).** S is the commit that every Execution_Record of the release run names (14.16). A later commit is a new Release_Candidate unless it is an Evidence_Commit. The Evidence_Output_Set is the appended records of `docs/next-phase/EXECUTION_EVIDENCE.md`, `docs/next-phase/RELEASE_REPORT.md` and `docs/next-phase/release/**`. The only change of `tasks.md` that an Evidence_Commit may hold is the checkbox of PH7-17 and of PH7-18. Every other file is code or a Test_Input: task specifications (the other lines of `tasks.md`), the review-hash record `docs/next-phase/hooks/HOOK_SECURITY_REVIEW.md`, the Execution_Index and `baseline/**`, the test inventories, the Threat_Model, `REPRODUCING_VERIFICATION.md`, `.kiro/settings/mcp.json`, `.kiro/hooks/**`, `scripts/**`, `tests/**`, and every source and configuration file. A change to one of them after S makes a new Release_Candidate, and every autonomous verification runs again (14.21). An owner record carries over only if the hash of every file that it covers is equal. `release_verify.py check-evidence-commit --base S --tip E` checks the diff paths, that the ledger only grew (0 deleted lines), that `tasks.md` differs only on the two checkbox lines, and that no record in E names E in its Commit column. An Evidence_Commit is verified separately: publication scan, ledger lint, `report-lint` and the frozen refs. Its own verification record is written by the next Evidence_Commit, because a commit cannot contain its own id. The final Evidence_Commit is verified by those checks before it is created and by the documented command afterwards. `report-lint` of the final report runs only after the report exists (PH7-18). PH7-17 runs only the checks that need no report (VM-15a).

**TR-3 Extended isolation gate (TPR-C-3).** `gate-isolation <junit_xml>` keeps its first step: the four original tests of `tests/contract/test_isolation.py` run as `vk-examiner` and write `<junit_xml>` with exactly those 4 test cases. It then runs three groups from `tests/security/`, selected by identity markers (names chosen at implementation) and by a committed manifest of expected node ids (`tests/security/ISOLATION_MANIFEST.txt`). The examiner identity (`vk-examiner`, uid 901) runs the checks that take the examiner's own view: inherited descriptors, readable files, the vault, the draft files, another replay's namespace, and the trusted evidence root as read-only. The authorized root observer is the root process of the entrypoint, used only to read `/proc` and files (process arguments, the environment of other processes, logs, shell-trace output, crash output) and to start the processes under test. It is never a principal of the application, and the Threat_Model records its residual exposure (7.20). The distinct secondary uid is a numeric uid that is neither 0, 900 nor 901, taken through `setpriv`, with no account added to the image. It runs the cross-account checks, for example a peer that is neither custodian nor examiner. Each group writes its own JUnit file beside `<junit_xml>`. The gate then writes `gate-isolation-counts.json` with the expected, collected, executed and skipped counts of each group. It exits non-zero when a group collects 0 tests, when the collected set differs from the manifest, when executed differs from collected, or when a test is skipped. Every task that adds an `isolation` test adds its node ids to the manifest. CI calls the same command, so there is one gate. Before any group runs under `--network none`, the gate records a network-none negative control: only `lo` is present and a connection to a non-loopback address fails.

**TR-4 Evidence recorder (TPR-C-4, TPR-H-10).** The first implementation tooling task, PH1-02, creates `scripts/release_verify.py` with `run [--step NAME] -- <command> [args]`. It runs the command without a shell and without a pipe and takes the exit status from the process itself (a signal or a timeout is a non-zero status). It measures duration from integer monotonic nanoseconds, with no float, copies the passed, failed, skipped and deselected counts only from the runner's summary line (absent when there is none, 3.3), keeps the names and reasons of failed and skipped tests from the `-rA` listing, and hashes the merged output as published. It writes one record atomically (a temporary file in the same directory, flush, fsync, rename), so a crash leaves a complete record or none, and it only appends to the ledger text. `recorded_utc` is taken in the same invocation, and the ledger lint (PH1-02a) rejects a recorder record that was written more than 5 s after its end (3.2, OD-D10-2). `ingest` records evidence that another party produced, with `source_recorded_utc` from the artifact, `ingested_utc`, a source type and the artifact hash (3.15), and the 5 s bound does not apply to it. E-201 to E-222 are bootstrap records that a scratch procedure made, with the limitations that the ledger states. The recorder does not rewrite or repeat them, and the lint treats them as `BOOTSTRAP`. A disclosed scratch scan covers only the evidence commits of PH1-02 and PH1-03, because the scanner does not exist before PH1-03. From the first commit after the PH1-03 record, every commit that publishes evidence or a document runs the PH1-03 scan on all files to be published, and every task except PH1-01 (already complete), PH1-02 and PH1-03 depends on PH1-03, directly or through another task.

**TR-5 BE-1 guard by abstract syntax tree (TPR-H-1).** The original comparison is preserved by AST equality and not by byte or indentation equality. The BE1-5 guard reads `git show 84df25c:tests/contract/test_mcp_server.py`, extracts the `assert` of `oct(bundle.parent.stat().st_mode & 0o777) == "0o700"`, compares `ast.dump` of its expression with the current file, and requires it under the `os.name == "posix"` branch of the same test. It requires 0 `skip`, `skipif`, `xfail` and `pytest.skip`, and 0 `return` before the last functional assertion. It requires the replay and explain assertion statements of the baseline to sit at the top level of the test function, so the Windows run executes them. These mutants must fail the guard: the expression removed, the expression weakened, `skipif` added, `xfail` added, an early `return` on Windows, and a replay or explain assertion moved under the POSIX branch. `git diff -w` of the test file shows only the added branch and the Windows lines.

**TR-6 Final security matrix (TPR-H-2).** PH7-05 reruns the whole extended `gate-isolation` (TR-3) on a tree that holds the last change of `deploy/entrypoint.sh`, `Dockerfile`, `examiner/worker.py` and the signing path. That is a tree after PH5-14, PH5-15, PH5-17 and PH7-10. It includes KT-1 to KT-8 for the vault key and, as the variant KT-S of each case, for a canary signing key, and also FC-1 to FC-12, IS-1 to IS-8, CA-1 to CA-7, RI-1 to RI-8 and the profile property P-l, with collected and executed counts. Results from PH1-12 to PH1-15, PH3-04 and PH6-04 are development results and are never evidence for S. PH7-17 repeats the gate on S.

**TR-7 Checkpoints and blockers (TPR-H-3, TPR-L-5).** PH7-17 and OA-09 require the six checkpoint records PH1-18, PH2-10, PH3-14, PH4-10, PH5-17 and PH6-12. `release_verify.py check-checkpoints` exits non-zero when one of them is missing, `FAILED`, or `UNVERIFIED` without an accepted reason, and PH7-17 then starts no verification and the report lists RB-19. RB-20 covers a missing OA-00 acceptance and a missing record for a decision that a task consumed. The release report lists each unresolved owner decision with the tasks that it blocks.

**TR-8 Owner items: states and order (TPR-H-4 to TPR-H-8).** An owner item is `OPEN`, `PROVIDED` or `NOT_PROVIDED`. `NOT_PROVIDED` is a recorded statement of the owner that the item will not be supplied. It never turns an `UNVERIFIED` row into `SUCCEEDED` and it keeps the blockers open. A GATE item must be `PROVIDED` before a task that names it starts: OA-00, OA-08 for the tasks that name it, OA-07a before any retrieval, and OA-09. An EVIDENCE item may be `NOT_PROVIDED`. The order is: OA-00 before every implementation task; PH4-08 before OA-04; OA-06 after PH2-07, PH4-05, PH4-06 and PH4-10, which are the last changes of a pinned file; OA-05 after OA-04 and OA-06; PH6-06 and OA-07a before any retrieval; then retrieval and build, independent review (OA-07b to OA-07e) and promotion as three separate steps, with no promotion of an unreviewed snapshot to `ACTIVE`; and for the release OA-09 selects S, OA-01 authorizes the push of S and the dispatch, PH7-17 verifies S, OA-03 reviews the exact S and PH7-18 writes the report. The agent lists hashes of pinned files as pending review. It never records a review, never approves its own hashes and never writes an owner record.

**TR-9 Autonomous Linux full-checkout route (TPR-H-9).** `release_verify.py linux-run` (PH7-09a) verifies a commit on a Linux_Docker_Host without a bind mount. (1) `git bundle create` of an existing ref that resolves to the commit; no ref is created, moved or deleted. (2) A preparation stage with network access builds a verification image from pinned bases and fills the `uv` cache and the npm cache from the committed lock files only, and runs no repository code. (3) A run stage starts a container with `--network none`, copies the bundle in with `docker cp`, clones it inside the container file system, checks that `git rev-parse HEAD` equals the commit and that `git status --porcelain` is empty, runs `uv sync --frozen --offline` and `npm ci --offline`, then runs the listed commands unpiped with `-rA`, and copies the outputs out with `docker cp`. (4) It records the network-none negative control, `docker inspect` showing 0 mounts, a POSIX mode probe (a directory created with mode 0700 reads back as 0700), the Python version and the exit codes, with the labels `LINUX_CONTAINER_FULL_CHECKOUT` and `DIRECT`. (5) It removes only the container that it created. It never reports `SUCCEEDED` unless every step succeeded, and a missing Docker engine gives `UNVERIFIED` with the reason. Browser E2E stays a CI row unless the image holds Playwright browsers. OA-02 is the owner route for the same rows from a separate Linux host.

**TR-10 Secure filesystem module (TPR-M-4, TPR-M-5, TPR-M-7, TPR-M-8).** One Core production module (name chosen at implementation) holds: containment and secure open (the helper of DD8-5, which the replay namespaces, the vault key file reader, the signing key and Trust_Store readers and the scaffold destination also use), exclusive secure create, private-directory enforcement, and the Windows access-list reader (`ctypes` and `advapi32`, no new dependency). The BE-1 test and `mcp_server._workdir()` call the same function. On POSIX it opens components with `O_NOFOLLOW` and `dir_fd`, compares `fstat` of the opened descriptor with the expected type, owner and mode, creates files with `O_CREAT`, `O_EXCL` and `O_NOFOLLOW` and mode 0600, and requires a private directory (owner is the process uid, no group or other bits). On Windows it rejects a reparse point, re-checks the final path of the opened handle, creates exclusively and requires ACL-P for a private directory; without a provider it fails closed. ACL-P is the structural rule of 13.11. ACL-K (the signing-key file) allows no entry for a trustee outside the current user, OWNER RIGHTS, SYSTEM and Builtin Administrators, none for Everyone, Authenticated Users, Builtin Users or Builtin Guests, and an enumeration error fails the check. ACL-T (the Trust_Store file) allows no write-class right for a trustee outside those four. POSIX permission bits are never accepted as Windows evidence. Negative tests: a symbolic link as the final component and below the root, a precreated file with another owner or mode, a swap between check and open (1000 iterations), and on Windows a junction and a reparse point. A scan finds 0 other containment implementations.

**TR-11 Authentication before allocation (TPR-M-6).** In the public profile the order is: authenticate from the headers, take the upload slot, read the body. Authentication and the ownership check also come before a run slot, a replay namespace or an examination is allocated. A request without a valid credential gets 401 with no slot taken (UA-9) and no body byte read. The client address for rate and failed-attempt limits is the socket peer. `Forwarded`, `X-Forwarded-For` and `X-Real-IP` are honored only when the peer is in the configured trusted-proxy setting. Negative tests: a spoofed header from an untrusted peer is ignored, rotating header values cannot evade the limit of 5 failed attempts per 15 minutes, an absent trusted-proxy setting ignores every forwarded header, and a header from the trusted proxy is honored.

**TR-12 CI provenance and test collection (TPR-M-9).** The workflow builds with `--build-arg VK_COMMIT_SHA=${{ github.sha }}` and then compares the image label `org.opencontainers.image.revision`, the build argument and the `commitSha` of `GET /api/v1/health` with `github.sha`, and validates the other provenance labels. `release_verify.py collect-check` runs `pytest --collect-only` for `tests/security`, `tests/sdk` and `tests/release`, fails when a directory collects 0 tests or lacks a node id of `tests/COLLECTION_MANIFEST.txt`, and reads the counts of `gate-isolation-counts.json`. A pytest exit code 5 is a failure. The gate counts and the collection counts are separate fields of the record.

**TR-13 Evidence rules by criterion and single owners (TPR-M-1 to TPR-M-3).** The criteria 1.4, 1.5, 1.6, 1.7, 1.10, 1.11, 1.15, 1.16, 2.7, 2.10, 4.5, 4.7 and 14.4 are traced in `tasks.md` (table "TPR-M-2 mapping"), each with a measurable rule (D10-AC-29). The design rows D8-AC-24, D8-AC-27, D9-AC-12, D2-AC-12, D3-AC-14, D3-AC-16, D3-AC-18 and D9-AC-10 are traced to the tasks and owner items that `tasks.md` names, and D7-AC-19 stays superseded by AM-D7-3. Each property has one authoritative task that holds its only Hypothesis test, which PH7-02 checks: P-k belongs to PH1-03 and P-d to PH2-03. PH7-04 and PH2-08 add supplementary example checks and no second property test.

**TR-14 Legacy replay gate (TPR-M-12).** After every change to archive validation or Bundle parsing (PH3-05 and PH3-08) the five corpus Bundles of PH3-01 and `examples/stub_claimtype/golden.vkb` are replayed. The pass condition is an equal Verdict_Hash, `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, the SHA-256 of each corpus file unchanged, and an unsigned Bundle still accepted. A new check that rejects a baseline Bundle is a defect, and the check is fixed.

**TR-15 One wording and claim catalog (TPR-L-1).** `release_verify.py wording-scan` (PH1-03a) holds the rules WS-1 to WS-8 and is the only implementation. WS-1: "byte-for-byte intact" (10.36). WS-2: "authenticated", "signed" or "verified" for an unsigned Bundle (10.14). WS-3: "tamper-proof", "secure", "authentic" or "signed" for the hook guard, chain or marker (D3-AC-25). WS-4: "all values", "every value" or "any value" for a sweep (D1 AC-6). WS-5: a capability statement without a `SUCCEEDED` record of the Release_Candidate (3.9, 3.10). WS-6: a combined readiness line, or a public URL presented as live (14.26, 7.14). WS-7: a Kiro attribution without a captured artifact (3.6, 4.7). WS-8: a Windows observation worded as a verified Linux result (1.12, 1.16). Each rule has a negative control. Other tasks cite rule ids and add no second scanner, and `report-lint` calls the same catalog.

**TR-16 Credential inventory (TPR-L-2).** The table below is the one authoritative inventory of credential and secret handling. No other table in the design or in `tasks.md` restates it, and a conflict is resolved in favor of this table.

| CSI | Item | Held by | Storage | Reader | Log rule | Tests |
|---|---|---|---|---|---|---|
| CSI-1 | Vault key | custodian | tmpfs file, mode 0400, removed after one read (`VK_VAULT_KEY_FILE`). The environment form is for runs outside the container only | custodian | never | KT-1 to KT-8, PC-1 |
| CSI-2 | Signing private key | custodian | externally provisioned file (`VK_SIGNING_KEY_FILE`). Never generated, stored, logged or committed | custodian | never | KT-S, PC-7, D5-AC-9 |
| CSI-3 | Trust_Store | custodian and replay | operator file (`VK_TRUST_STORE_FILE`), public keys only | custodian, replay | path never | D5-AC-8, ACL-T |
| CSI-4 | Invitation credentials | edge or API | hash, label, expiry and revocation flag, no value | the check only | never | D10-AC-1, D10-AC-2, D2-AC-26 |
| CSI-5 | Owner cookie `vk_owner` | API | server-set, `SameSite=Strict`, binding in `case_owners` | API | never | D2-AC-10, D8-AC-20 |
| CSI-6 | Access tokens in requests | none | not stored | none | never | PC-4 |
| CSI-7 | Hook environment values | hook runner | closed variable list. Secret-named variables are dropped and listed by name only | child process | names only | D3-AC-26, PC-5 |

**TR-17 Redaction fixtures (TPR-L-3).** Automated redaction and scan tests on every host use synthetic fixtures built inside the test (constructed paths, names, addresses and canaries, labelled SYNTHETIC) and no value taken from the environment. The check that reproduces a published hash from a Private_Original runs only on the authorized host that holds the Private_Original, and elsewhere it is `UNVERIFIED` with that reason. The Private_Original stays outside the public repository.

**TR-18 Runtime floor (TPR-L-4).** The floor is CPython 3.12.4 or later (13.29, 13.25). It is enforced by the production access-list module (`UNSUPPORTED_PYTHON_PATCH`), by a check at image build, by a step of the CI workflow, by the Linux verification container and by `release_verify.py`. Each records the full version, and the provenance block lists it. An equivalent runtime needs a recorded owner decision (OA-08).

**TR-19 Same-file order (TPR-M-11).** Tasks that name one source file are ordered by an explicit `Depends on` line. PH1-17 depends on PH1-13, because the start-up and run path under `core/src/verdictkit/api/` and `SafetyMiddleware` share `core/src/verdictkit/api/server.py`. PH1-16 depends on PH1-14, PH1-15 and PH1-17. The earlier wave-only orderings stay.

**Acceptance rows.** All rows are UNVERIFIED until an Execution_Record exists.

| ID | Criterion | Method | Pass threshold | Req | Host |
|---|---|---|---|---|---|
| D10-AC-10 | Minimal recorder | `release_verify.py run -- <command>` on a passing, a failing and a killed command, a runner with skips and deselects, and a crash injected at each write step | The exit status is the process's own (0, non-zero, or a signal or timeout as non-zero). `recorded_utc` minus the end time is at most 5 s. A crash leaves 0 partial records. A 2 s sleep records a duration between 2.0 s and 2.5 s. Skipped and failed test names carry their reasons. A command with a pipe to `tail` or `head` is refused. 0 float values in the duration arithmetic | 3.2, 3.3, 3.5, 1.10, 1.15 | Both |
| D10-AC-11 | Source and ingestion times | `ingest` of an owner-supplied record that is hours old | `source_recorded_utc` and `ingested_utc` are separate fields, with a source type and the artifact hash. The 5 s bound is applied only to recorder records. An `ingested_utc` before `source_recorded_utc` is rejected. A source with no exit code is never `SUCCEEDED` | 3.15, 3.2 | Both |
| D10-AC-12 | Evidence_Commit | `check-evidence-commit --base S --tip E` | Only Evidence_Output_Set paths. The ledger has 0 deleted lines. `tasks.md` differs only on the checkbox lines of 7.17 and 7.18. No record names E in its Commit column. A change to each Test_Input class (the Threat_Model, the review-hash record, the Execution_Index, a test inventory, another `tasks.md` line, `.kiro/settings/mcp.json`, the reproduction document, a script) fails the check | 14.16, 14.21 | Both |
| D10-AC-13 | Extended isolation gate | `gate-isolation` on the image with `--network none`, and the same command in CI | `<junit_xml>` holds exactly the 4 original tests with 0 failures. Each group has collected equal to the manifest, executed equal to collected and 0 skipped, and `gate-isolation-counts.json` is written. A removed test, an empty group and a skipped test each make the gate exit non-zero. The network-none negative control is recorded | 13.8, 13.16, 13.17, 2.7 | Linux_Docker_Host, CI |
| D10-AC-14 | BE-1 AST guard | The guard on the real file and on six mutants | The real file passes. The mutants (expression removed, weakened, `skipif`, `xfail`, early `return` on Windows, a replay or explain assertion moved under the POSIX branch) each fail. The Windows run executes the replay and explain assertions. `git diff -w` shows only the added branch and Windows lines | 13.11, 2.11 | Both |
| D10-AC-15 | Final security matrix | PH7-05 on a tree after PH5-14, PH5-15, PH5-17 and PH7-10 | KT-1 to KT-8 for the vault key and for the canary signing key, FC-1 to FC-12, IS-1 to IS-8, CA-1 to CA-7 and RI-1 to RI-8 are collected and executed, 0 matches, 0 failures. The record names the commit | 13.16, 13.24, 7.20, 10.25 | Linux_Docker_Host |
| D10-AC-16 | Checkpoint completeness | `check-checkpoints` before PH7-17, with each of the six records removed in turn | 6 of 6 records `SUCCEEDED` (or `UNVERIFIED` with an accepted reason) passes. Each of the 6 removals exits non-zero, starts no verification and lists RB-19 | 4.4, 4.9, 14.10, 14.11 | Both |
| D10-AC-17 | Owner-item order and states | A graph check over `tasks.md`, and a check that no owner record is agent-authored | OA-00 precedes every implementation task. PH4-08 precedes OA-04. OA-06 follows PH2-07, PH4-05, PH4-06 and PH4-10. OA-05 follows OA-04 and OA-06. PH6-06 and OA-07a precede every retrieval. Each promotion follows its review. The release order is OA-09, OA-01, PH7-17, OA-03, PH7-18. A record written by the agent in an owner field is rejected | 4.10, 8.17, 8.19, 12.22, 13.27, 14.13 | Both |
| D10-AC-18 | Autonomous Linux route | `linux-run` on a bundle of a clean commit, and on a copy that uses a bind mount | HEAD equals the commit and the status is empty. `docker inspect` shows 0 mounts. A directory created with mode 0700 reads back as 0700. The network-none negative control is recorded. `uv sync --frozen --offline` and `npm ci --offline` succeed. The `-rA` listings and direct exit codes are captured. The bind-mount run is refused. A failed step is never `SUCCEEDED` | 13.13, 1.12, 1.16, 14.3, 14.21 | Linux_Docker_Host |
| D10-AC-19 | Secure filesystem module | The negative tests of TR-10 on both host classes, and a scan of the source tree | A symbolic link (final component and below the root), a precreated file with another owner or mode, and 1000 swap iterations each end in a refusal and 0 opens outside the root. A private directory with group or other access is refused. Windows junction and reparse cases are refused. PH1-16 and PH2-02 import the same module, and the scan finds 0 other containment code | 13.19, 13.28, 13.30, 9.21 | Both |
| D10-AC-20 | Production access-list module | The BE-1 test, the ACL-P, ACL-K and ACL-T checks, and a code check | The function that the test calls is the function that `_workdir()` calls. Each negative control (an Everyone entry, an inherited entry, a Builtin Users entry, a key file readable by Users, a Trust_Store writable by Users) fails the check. A test that passes only because of `os.chmod` fails. The check lives in `core/`, not under `tests/` | 13.11, 13.25, 10.37 | Windows |
| D10-AC-21 | Authentication before allocation | UA-9 and the forwarded-header tests in the public profile | A request without a valid credential gets 401, the slot count is unchanged and 0 body bytes are read. The same holds for a run slot and a replay namespace. A spoofed header from an untrusted peer is ignored. Rotating header values does not evade the limit. An absent trusted-proxy setting ignores all forwarded headers. A trusted proxy's header is honored | 7.27, 7.24, 7.21 | CI or VM |
| D10-AC-22 | CI provenance and collection | The workflow lint, and a dispatched run | `VK_COMMIT_SHA` equals `github.sha`. The image label, the build argument and `commitSha` agree. `collect-check` passes. An emptied directory, a missing manifest node id and pytest exit code 5 each fail the step | 14.17, 14.20, 13.7, 13.8 | CI |
| D10-AC-23 | Legacy replay gate | The corpus and `golden.vkb` replay after PH3-05 and after PH3-08 | Equal Verdict_Hash, `REPRODUCED` or `REPRODUCED_ACROSS_ENV`, 0 `UNVERIFIABLE` from a new check, each corpus file hash unchanged, an unsigned Bundle accepted | 12.23, 13.22, 10.5 | Both |
| D10-AC-24 | Wording and claim catalog | `wording-scan` rules WS-1 to WS-8, and `git grep` for another scanner | Each rule finds its planted negative control. Every other task cites rule ids. 0 duplicate scan implementations | 3.9, 3.10, 10.36 | Both |
| D10-AC-25 | Credential inventory | A check of the CSI table against the tasks that cite it | One table. Each row has storage, reader, log rule and a test id. PH1-11, PH3-04, PH5-10, PH5-11 and PH7-04 cite CSI rows. 0 other table | 7.24, 7.20, 10.25 | Both |
| D10-AC-26 | Redaction fixtures | The sanitizer and scan tests on Windows and in the Linux container | Fixtures are synthetic, and a check shows that none equals a value read from the environment. The Private_Original reproduction is `UNVERIFIED` with the reason on a host that lacks the file | 3.11, 3.14 | Both |
| D10-AC-27 | Runtime floor | Each environment: Windows host, image build, CI, Linux verification container | CPython 3.12.4 or later in each, else a failure with a code. The version is recorded in each record and in the provenance block | 13.25, 13.29, 14.17 | Both |
| D10-AC-28 | Deferred Linux verification | A check of the DLV register against the ledger | Each DLV row is `UNVERIFIED` until a `SUCCEEDED` record that names a Linux source exists. A Windows record never sets one. A failing DLV row unticks its task and opens RB-1 or RB-3 | 13.12, 13.13, 13.26, 1.12 | Both |
| D10-AC-29 | Evidence rules by criterion | The "TPR-M-2 mapping" table of `tasks.md` and the records of the named tasks | Each of 1.4, 1.5, 1.6, 1.7, 1.10, 1.11, 1.15, 1.16, 2.7, 2.10, 4.5, 4.7 and 14.4 names a task and a measurable rule. Records carry direct exit codes, accurate durations, skipped and deselected reasons, one record per execution, Windows and Linux results in separate rows, a network-none negative control for each such gate, distinct uids, vault mode 0700 and the socket check, a grid-cap rejection with 0 evaluated points, the four rollback fields, and a feature-attribution row for specs, steering, tasks, hooks, MCP and sub-agents | 1.4 to 1.7, 1.10, 1.11, 1.15, 1.16, 2.7, 2.10, 4.5, 4.7, 14.4 | Both |
| D10-AC-30 | Same-file order and property owners | The graph and wave check, and PH7-02's meta-test | 0 same-file conflicts in one wave. 15 of 15 properties each have exactly one Hypothesis test, in the task that the property list names | 13.4, 13.28, 4.3 | Both |

### D10.12 Owner scope freeze and decisions (OA-00, OA-08)

Recorded 2026-11-26. The repository owner recorded OA-00 as `ACCEPTED_WITH_CONDITIONS` for the checkpoint `fff6db49fb6f7f51080ca4fdb5e0ee7c1d37a581` and froze the scope of the enhanced release. The record, with the SHA-256 values of `requirements.md`, `design.md` and `tasks.md`, is `docs/next-phase/OWNER_DECISIONS.md`. Everything in this section is DESIGNED. Nothing is IMPLEMENTED or VERIFIED, and no deferred item is reported as either. As in D10.2, the earlier text is not edited unless a row below says so, and this section governs it. The statements that D10.11 or the plan await OA-00 are superseded by that record.

**Decisions.** OD-D8-1 (the tmpfs key file of DD8-2), OD-D8-2 (a server-generated replay namespace of 32 hexadecimal characters), OD-D8-3 (the private working directory as the default Approved_Root) and OD-D8-4 (2 concurrent uploads and 64 MiB per replay) are approved as designed. OD-D8-4 gives the total replay quota of RI-8 no value, and the owner approved none, so PH1-16 records the value as an unresolved decision (RB-20) until the owner supplies it. The recommendations for OD-D8-5, OD-D8-6, OD-D9-3 and OD-D9-6 are retained and stay visible. OD-D8-5 concerns only PH1-07, which is deferred, so O1 stays the only BE-1 oracle (DD8-7). No security acceptance criterion is weakened.

**Scope.** Retained: the Phase 1 security remediation, the Phase 2 MCP hardening, the Phase 3 signed Bundles and signer trust, the Phase 4 Kiro hooks and evidence tooling, the Phase 5 Judge UI and local deployment hardening, PH6-12 as the legacy replay checkpoint (P-g retained) and the Phase 7 release verification. Deferred: PH1-07, PH6-01 to PH6-11 (with PH6-08a, PH6-09a and PH6-10a), OA-07a to OA-07e and CD-01 to CD-09. The plan then has 92 queued tasks (1 complete, 91 remaining), 10 owner items in the graph, 52 waves and no dependency on a deferred item. The existing Texas adapter and historical replay stay intact (D7-AC-1, D8-AC-15, P-g, AM-D7-3).

| # | Earlier text | Reading under D10.12 |
|---|---|---|
| 1 | 14.2 and VM-5: the Conformance_Suite, the regulatory snapshot tests and the scaffold end-to-end test run on S | Not run, and listed `UNVERIFIED` with the reason `deferred scope`. The property tests are 13 (P-a to P-d, P-f to P-l, P-n, P-o). |
| 2 | 13.5(e), D8-AC-2 (P-a to P-e), P-e, P-m, D10-AC-30 (15 of 15), PH7-02 | P-e and P-m are deferred. D8-AC-2 covers P-a to P-d, and D10-AC-30 and PH7-02 count 13 of 13. |
| 3 | 13.24, D8-AC-17 (FC-1 to FC-12, 12 of 12), the final matrix of PH7-05 and D10.11 TR-6 | FC-10 (a plugin fails to load) and FC-12 (an unreadable plugin provenance manifest) are deferred with PH6-04. D8-AC-17 and PH7-05 count 10 of 10 (FC-1 to FC-9 and FC-11). |
| 4 | 13.20, D8-AC-12 (PD-1 to PD-12), D6-AC-8, D6-AC-9, 11.16 to 11.18 | Deferred with PH6-03 and PH6-04, not implemented, not verified. KL-1 applies. |
| 5 | 13.14, D8-AC-3 and PH7-03: seven adversarial surfaces | Five (API, MCP_Server, Bundle parsing, Trust_Store, signature envelopes). Plugin scaffolding and regulatory snapshots are deferred. The seven malformed-input kinds of 13.6 are unchanged. |
| 6 | D8.4 rows T8-16, T8-17, T8-22 and T8-23 | `UNTESTED` with the reason `deferred scope`. Row T8-1 cited only D6-AC-10 and D6-AC-11, which belong to the deferred PH6-01, so its test id now names the baseline `tests/contract/test_blinding.py`. The status of T8-1 does not change. |
| 7 | D9-AC-13 and D9.5: the plugin provenance manifest hash in the provenance block | The field is present with the value `NOT_BUILT` while PH6-04 is deferred. No hash is invented. |
| 8 | D9-AC-19 and RP-9 (plugin allowlist) | RP-9 is listed `NOT_APPLICABLE`, because no allowlist exists. The other 8 rows keep their confirmation checks. |
| 9 | D8-AC-29, 12.21 and AM-D7-1: the `CA` to `ZZ` hunks | Not applied, because California stays unsupported and criterion 12.21 is not triggered. |
| 10 | D5.8 and D5.12: the D7 items `as_of`, the snapshot retrieval date and the Examination_Semantics id are classified in the 2.0.0 event | PH3-12 classifies the Examination_Semantics id, which PH3-02 adds. `as_of` and the snapshot retrieval date are deferred. D5-AC-18 (0 unlabelled changes) is judged by PH3-12. |
| 11 | D7 and R12 | Deferred except criterion 12.13 (Texas findings and tests unchanged) and criterion 12.23 (the Examination_Semantics identifier and replay of every earlier Bundle). D6 and R11 are deferred in full. |
| 12 | Track P5 and P6 execution records (4.4) | Each criterion of Requirements 11 and 12 is listed, and every one except 12.13 and 12.23 is `UNVERIFIED` with the reason `deferred scope`. |

**Known limitation KL-1 (baseline entry-point loading in the public profile).** Read from `core/src/verdictkit/cli.py` (`_load_registry`): the function imports every entry point of the group `verdictkit.claim_types` and every module named in `VK_CLAIM_TYPES`, in every Security_Profile. It is used by the API server, the command line, the MCP server and the examiner worker, and `deploy/entrypoint.sh` passes `VK_CLAIM_TYPES` to the custodian and to the examiner. It has no allowlist and no provenance check. An exception raised while loading the entry-point group is swallowed without a message, and an exception from a `VK_CLAIM_TYPES` module is not. The start-up comparison of the claim-type digest (7.19, PH1-15) detects a difference between the two processes and does not prevent an import. The fail-closed public loader (11.16 to 11.18) and its tests (PD-1 to PD-12, FC-10, FC-12) are deferred, so secure public operation with respect to plugin loading is `UNVERIFIED`. The release report lists KL-1 under the known limitations. This section authorizes no public deployment. While CD-01 to CD-09 are deferred, RB-16 and RB-17 stay open and Public_Deployment_Readiness stays `NOT_VERIFIED`. A later authorization of public deployment must first assess KL-1, and if the retained loading behavior prevents secure public operation, public deployment stays blocked.

## Table of contents

Every section below is written. DESIGNED means that no code or test exists. The approval state comes from the decision records of each section. D1 to D7 are conditionally approved by the maintainer. D8 to D10 and the canonical sections await maintainer review.

| Section | Title | Requirements | Status |
|---|---|---|---|
| Overview | Purpose, scope, vocabulary, invariants and the ten decisions | all | DESIGNED (awaiting maintainer review) |
| Architecture | Target-state processes, trust boundaries, verification, release gates | all | DESIGNED (awaiting maintainer review) |
| Components and Interfaces | Components, external interfaces, environment variables | all | DESIGNED (awaiting maintainer review) |
| Data Models | Bundle, envelope, Trust_Store, rules, provenance, records | all | DESIGNED (awaiting maintainer review) |
| Correctness Properties | CP-1 to CP-50 | all | DESIGNED (awaiting maintainer review) |
| Error Handling | Codes, statuses and exit codes for each surface | all | DESIGNED (awaiting maintainer review) |
| Testing Strategy | Layers, hosts, rules, rows by track, untested items | all | DESIGNED (awaiting maintainer review) |
| D0 | Foundations | R1 to R4 | DESIGNED (maintainer decisions in D0.8) |
| D1 | P0 UI and landing page | R5, R6 | DESIGNED (conditionally approved; decisions in D1.16) |
| D2 | P1 secure public deployment | R7 | DESIGNED (conditionally approved; decisions in D2.12) |
| D3 | P2 hooks and Windows | R8 | DESIGNED (conditionally approved; decisions in D3.13) |
| D4 | P3 MCP | R9 | DESIGNED (conditionally approved; decisions in D4.12 and D4.13) |
| D5 | P4 signing | R10 | DESIGNED (conditionally approved; decisions in D5.12 and D5.13) |
| D6 | P5 SDK | R11 | DESIGNED and DEFERRED by the owner scope freeze (D10.12); decisions in D6.11 |
| D7 | P6 regulatory | R12 | DESIGNED and DEFERRED by the owner scope freeze except 12.13 and 12.23 (D10.12); decisions in D7.11 |
| D8 | P7 security and property testing, BE-1 and BE-2 remediation | R13 | DESIGNED (accepted with conditions by OA-00, D10.12; open decisions in D8.15) |
| D9 | P8 release verification | R14, R15, R16 | DESIGNED (accepted with conditions by OA-00, D10.12; open decisions in D9.10) |
| D10 | Traceability, reconciliation, status and open decisions, the task-plan review remediation (D10.11) and the owner scope freeze (D10.12) | all | DESIGNED (accepted with conditions by OA-00, D10.12; open items in D10.8) |
