# Design Document — VerdictKit Core

## Overview

The core implements the custody pipeline shared by every claim type:

```
intake ─▶ freeze ─▶ commit+seal ─▶ acquire evidence ─▶ examine (blind, isolated)
       ─▶ commit examination ─▶ reveal ─▶ compare ─▶ seal verdict ─▶ [diagnose] ─▶ bundle
```

Full rationale, threat model and blocking-decision log: `docs/ARCHITECTURE.md`.

## Architecture

Two OS principals inside one Linux container:

* **Custodian** (`vk-custodian`): FastAPI app, intake, vault, ledger, comparator,
  diagnostics runner, bundle writer, MCP server.
* **Examiner** (`vk-examiner`): long-lived worker on a unix socket; evidence broker,
  sweep engine, claim-type `examine()` calls.

The entrypoint starts as root, creates `/var/lib/vk/vault` (0700, vk-custodian) and
`/var/lib/vk/evidence` (0750, group `vk-evidence` with read for vk-examiner, write for
vk-custodian), then `exec`s each process under its own uid via `setpriv`. No long-lived root
process remains.

Evidence acquisition runs in the Examiner (it needs the data), writes through the broker
into the content-addressed store, and returns `EvidenceItem` records to the Custodian, which
re-verifies hashes and policy before recording `EVIDENCE_ACQUIRED`.

## Components and Interfaces

All signatures are fixed in `core/src/verdictkit/`. Summary:

| Module | Responsibility | Key API |
|---|---|---|
| `canonical.py` | canonical JSON + hashing | `canonical_bytes(obj) -> bytes`, `parse_canonical(b) -> object`, `sha256_hex(b)` |
| `model.py` | immutable data types, verdict matrix | `FrozenClaim`, `BlindedTask`, `Commitment`, `EvidenceItem`, `Finding`, `Verdict`, `validate_finding()`, `headline_status()` |
| `plugin.py` | `ClaimType` protocol + registry | `ClaimType`, `Registry.register/get` |
| `custody/intake.py` | validate, partition, freeze | `freeze(claim_type, raw) -> IntakeResult` |
| `custody/commitment.py` | commitments | `commit(outcomes, salt)`, `verify(commitment, outcomes, salt)` |
| `custody/vault.py` | AES-GCM sealed storage | `Vault.seal(case_id, outcomes) -> SealedRef`, `Vault.unseal(ref)` |
| `custody/ledger.py` | hash chain + state machine | `Ledger.append(kind, payload)`, `Ledger.verify() -> LedgerCheck` |
| `custody/comparator.py` | reveal + findings + verdict | `compare(claim_type, frozen, examination, outcomes) -> Verdict` |
| `examiner/protocol.py` | wire codec, size cap | `encode_task`, `decode_task`, `encode_result`, `decode_result` |
| `examiner/client.py` / `worker.py` | IPC + isolated execution | `ExaminerClient.examine(task) -> ExaminationResult` |
| `evidence/policy.py` | permitted/forbidden sources | `EvidencePolicy.check(item) -> PolicyDecision` |
| `evidence/store.py` | content-addressed store | `EvidenceStore.put(bytes, meta) -> EvidenceItem`, `get(sha256) -> bytes` |
| `evidence/broker.py` | adapter dispatch | `EvidenceBroker.acquire(requests) -> list[EvidenceItem]` |
| `sweep.py` | grid expansion + aggregation | `expand_grid(assumptions, cap)`, `aggregate(point_outcomes)` |
| `pipeline.py` | orchestration | `run_case(type_id, raw_claim, *, clock) -> CaseFile` |
| `bundle.py` | write + replay | `write_bundle(case, path, *, clock)`, `replay_bundle(path, *, allow_refetch=False) -> ReplayReport` |
| `envprint.py` | environment fingerprint | `fingerprint() -> EnvFingerprint` |
| `mcp_server.py` | MCP tools | `list_claim_types`, `verify_claim`, `replay_bundle`, `explain_verdict` |

## Data Models

See `model.py` docstrings. Invariants:

* All dataclasses are `frozen=True, slots=True`.
* Numeric fields are `Decimal` or `int`; no `float` type appears in any model.
* `Finding.numbers` values are canonical Decimal strings.
* `Verdict.verdict_hash` is computed by `model.compute_verdict_hash()` only.

## Error Handling

| Error | Raised by | Outcome |
|---|---|---|
| `CanonicalizationError` | canonical, intake | HTTP 422 with JSON path |
| `SchemaError` | intake | HTTP 422 |
| `GridTooLargeError` | sweep | HTTP 422 with grid size and cap |
| `CommitmentMismatchError` | comparator | case aborted, ledger records `CASE_ABORTED` |
| `LedgerOrderError` | ledger | programming error, 500, never swallowed |
| `EvidenceIntegrityError` | store | dependent findings INDETERMINATE(`evidence_integrity`) |
| `PolicyViolation` (decision, not exception) | policy | dependent findings INDETERMINATE(`policy_violation`) |
| `IsolationNotEnforcedError` | startup | judge mode refuses to start |
| `ExaminerTimeout` | client | case INDETERMINATE(`examiner_timeout`) |

Rule: an error may make a finding INDETERMINATE; no error path may produce
`SUPPORTED`, `CONSISTENT` or `WITHIN_BOUND`.

## Correctness Properties

Each property becomes at least one Hypothesis test. Reviewer contract versions live in
`tests/contract/`; Kiro-generated versions live next to each package.

* **P1 Canonical determinism** — for any JSON-safe value, `canonical_bytes` is independent of
  dict insertion order, and `parse_canonical(canonical_bytes(x)) == x`. Floats, NaN and
  duplicate keys are always rejected. *(Req 1.2, 1.3)*
* **P2 Blinding invariance** — for any claim and any two outcome assignments,
  `encode_task(blind(...))` bytes are identical and the examination result is identical.
  *(Req 2.3)*
* **P3 Outcome absence** — sentinel outcome values never occur in encoded task bytes.
  *(Req 2.4)*
* **P4 Commitment binding** — `verify(commit(o, s), o, s)` holds; it fails for any `o' ≠ o` or
  `s' ≠ s`. *(Req 3.1, 3.3)*
* **P5 Spec-hash sensitivity** — changing any param/assumption/tolerance changes
  `spec_hash`; changing only outcomes does not. *(Req 1.4–1.6)*
* **P6 Ledger ordering** — every permutation that violates the state machine raises
  `LedgerOrderError` and leaves the ledger unchanged. *(Req 8.1, 8.2)*
* **P7 Ledger tamper evidence** — modifying any payload hash breaks `verify()` at exactly that
  sequence number. *(Req 8.4)*
* **P8 Fail-closed policy** — a finding citing evidence with a forbidden source class is
  never `SUPPORTED/CONSISTENT/WITHIN_BOUND`. *(Req 5.3)*
* **P9 Evidence integrity** — any byte flip in a stored blob raises on read. *(Req 5.4)*
* **P10 Replay determinism** — with a fixed injected clock, two bundles of the same case are
  byte-identical, and replay returns `REPRODUCED`. *(Req 9.4, 9.5)*
* **P11 Bounded, ordered sweep** — grid size equals the product of axis sizes, ordering is
  deterministic, over-cap grids raise, missing assumptions affect only dependent findings.
  *(Req 7)*
* **P12 Verdict matrix + headline** — invalid basis/status pairs raise; the headline is the
  maximum under the severity order; diagnostics never change `verdict_hash`.
  *(Req 6, 10.4)*

## Testing Strategy

* Hypothesis, `derandomize=True` in CI profile, `max_examples=200` (core), 100 (apps).
* Isolation integration test (`-m isolation`) runs only inside the container with
  `VK_ISOLATION=enforced`; it attempts to read the vault as vk-examiner and asserts
  `PermissionError`, and asserts the examiner environment lacks `VK_VAULT_KEY`.
* LLM fence test runs on every commit (AST import scan).
* Replay golden test: a committed stub-claim bundle must replay to `REPRODUCED` or
  `REPRODUCED_ACROSS_ENV` on CI.
