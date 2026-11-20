# VerdictKit API Contract (contract 1.1.0)

Normative schema: `api/openapi.yaml` (OpenAPI 3.1, JSON Schema 2020-12). Examples:
`api/examples/` (placeholders, not results). Enforced by `tests/contract/test_api_schema.py`
and `tests/contract/test_presenter.py`. This is a **presentation adapter**: it never changes
a domain status, it only withholds a confidence class where required and adds
execution-level framing. Domain and security contracts in `docs/ARCHITECTURE.md` are
unchanged.

Every JSON response carries `contractVersion: "1.1.0"` (header `X-VerdictKit-Contract`).
`GET /claim-types` returns `{contractVersion, claimTypes: [...]}` rather than a bare array. Startup accepts only literal `VK_JUDGE_MODE=0` or `VK_JUDGE_MODE=1`; invalid values refuse with exit 2 and `VK_STARTUP_ERROR=CONFIG_INVALID:VK_JUDGE_MODE`. A successful startup check prints `VK_STARTUP_OK isolation=ENFORCED` or `VK_STARTUP_OK isolation=UNENFORCED`. Judge mode without verified isolation refuses with exit 3 and `VK_STARTUP_ERROR=ISOLATION_NOT_ENFORCED`.
Changing any schema requires bumping it; the frontend refuses unknown versions.

## 0. Blinding scope (what is and is not secret)

The blinding guarantee is **examiner-side**: the Examiner process (separate OS user, no
vault access) never receives asserted outcomes before its result is committed. The
browser is not part of that guarantee: the user typed the outcomes, so the browser holds
them at intake. The contract therefore promises only that:
* asserted outcome values are **write-only** — no response before the verdict join echoes
  them (`DraftCase.outcomeFields` carries `{name, captured}` only, no values, no spans);
* the frontend should clear outcome values from its own state once intake is accepted, and
  must not describe this as secrecy from the user;
* UI copy may say "the examiner never saw the claimed result", never "nobody can see it".

## 1. Routes (`/api/v1`, no auth in judge mode)

| Step | Method & path | Result |
|---|---|---|
| Health | `GET /health` | `isolationMode`, `judgeMode`. Judge mode with `UNENFORCED` is unrepresentable; the server refuses to start. |
| Types | `GET /claim-types` | includes `acceptsPastedText` |
| Intake | `POST /cases` | `DraftCase` with parameter ledger + blockers. Nothing frozen. |
| Edit/confirm | `PATCH /cases/{caseId}` | draft only; `confirm[]` sets basis `USER_CONFIRMED` |
| Freeze | `POST /cases/{caseId}/freeze` | `FrozenCase` (spec hash, commitment). Irreversible. 422 = `BlockedResponse`. |
| Evidence | `POST /cases/{caseId}/evidence` | `EvidenceResult`; 422 = blocked (rights, gap, policy) |
| Execute | `POST /cases/{caseId}/runs` | 202 `RunAccepted`; idempotent per case |
| Progress | `GET /cases/{caseId}/runs/{runId}/events` | SSE of `ProgressEvent`; `GET …/runs/{runId}` = persisted `RunRecord` |
| Verdict join | `GET /cases/{caseId}/outcome` | `OutcomeResponse` (the one object the UI renders), incl. `specimen` and `sensitivity` |
| Export | `GET /cases/{caseId}/bundle` | `.vkb` zip |
| Bundle metadata | `GET /cases/{caseId}/bundle/metadata` | integrity, reproducibility (`NOT_RUN`), authenticity, replay command |
| Replay | `POST /replays` (zip body) | `ReplayReport`, no network |

Errors use `{"error": {code, message, field}}`. Limits in judge mode: 256 KiB JSON bodies,
8 MiB bundle uploads, per-IP rate limit, 24 h case TTL.

## 2. Execution status vs. epistemic status (corrections 1, 2)

`executionStatus` says whether the engine could reach a conclusion; finding `status` says
what it concluded.

| executionStatus | When | Findings | headline | confidenceClass |
|---|---|---|---|---|
| `BLOCKED` | a blocker stopped the case before examination (missing critical parameter, grid too large, privacy, rights unverified, evidence unavailable/gap, policy) | none | `null` | `null` |
| `INDETERMINATE` | ran and sealed, but every finding is `INDETERMINATE` | ≥1, all `INDETERMINATE` | `INDETERMINATE` | `null` |
| `COMPLETED` | sealed with ≥1 determinate finding | ≥1 | worst finding status | of the worst finding |

`confidenceClass` per finding: `INTERNAL_ARITHMETIC → DOCUMENT_INTERNAL`,
`EXTERNAL_EVIDENCE → EXTERNAL`, `MECHANICAL_BOUND → MECHANICAL_BOUND`; `null` whenever the
finding is `INDETERMINATE`, the run is not `COMPLETED`, or `dataMode = SYNTHETIC_DEMO`.
Infrastructure errors are not execution statuses: run state `FAILED` + HTTP 5xx.

## 3. Data mode and rights (B1)

`dataMode ∈ {LIVE_EVIDENCE, SYNTHETIC_DEMO}`, fixed at intake.
* `LIVE_EVIDENCE`: synthetic evidence is forbidden by the core (fail closed). Market-data
  sources (Binance, Coinbase) are `REFETCH_ONLY` and carry `rightsBasis = UNVERIFIED` until
  a rights basis is documented; an unverified source yields `BLOCKED /
  EVIDENCE_RIGHTS_UNVERIFIED`. Raw market data is never embedded in bundles.
* `SYNTHETIC_DEMO`: created **only from a bundled fixture claim** (`fixtureId`; no pasted
  text, no user form), so no user-supplied real claim can ever be run against synthetic
  data. Evidence is `SYNTHETIC_FIXTURE`, `specimen.source = SYNTHETIC_FIXTURE`,
  `demonstrationOnly = true`, `demonstrationNotice` is a non-empty fixed sentence, and every
  confidence class is `null` — **even when `executionStatus` is `COMPLETED`**. The UI must
  render the notice on the verdict, the specimen header and any exported image.

Consequence: until rights are verified, Reel Autopsy can show real engine behaviour only on
labelled synthetic fixtures. Quote Autopsy is unaffected (document-internal + official facts).
Securing a licensed historical source is prioritised ahead of UI polish (reel task 5.0).

## 4. Evidence DTO (correction 4)

`evidenceId, providerId, origin, retrievedAt, snapshotHash, independenceBasis, rightsNote,
licenseClass, embeddedInBundle, uri`. Schema-enforced pairings: official/exchange origin ⇒
`INDEPENDENT_OF_CLAIMANT`; worksheet ⇒ `CLAIMANT_DOCUMENT_SELF` (used only by
`DOCUMENT_INTERNAL` findings); synthetic ⇒ `SYNTHETIC_NOT_EVIDENCE`; `REFETCH_ONLY` ⇒
`embeddedInBundle = false`.

## 5. Parameter ledger (correction 5)

Each entry: `name, value, range?, state ∈ {SPECIFIED, ASSUMED, MISSING}, sourceSpan,
basis ∈ {CLAIMANT_TEXT, USER_FORM, USER_CONFIRMED, DEFAULT_POLICY, NONE}, critical`.
Rules: `MISSING ⇒ value null, basis NONE`; `ASSUMED ⇒ basis DEFAULT_POLICY` (the swept range
is shown); `sourceSpan` only with `CLAIMANT_TEXT`; after freeze every `sourceSpan` is `null`
(schema-enforced in `FrozenCase` and `OutcomeResponse`). Because the pasted text is discarded,
the frontend cannot highlight source text after freeze; no retained text representation
exists in v1.
A `MISSING` + `critical` entry is a `MISSING_CRITICAL_PARAMETER` blocker. Domain mapping:
`SPECIFIED ↔ CLAIMANT/USER_CONFIRMED`, `ASSUMED ↔ DEFAULT_POLICY`, `MISSING ↔ AssumptionKind.MISSING`.

## 5a. Presentation metadata (adapter only)

* `specimen`: `specimenId, claimType, claimTypeLabel, source, fixtureId, title, fields[],
  frozenAt, specHashShort`. Built by `presenter.specimen_dto` from frozen **parameters**
  only, through a fixed per-claim-type template; no outcome values, no free text.
* `sensitivity`: `templateVersion` (`<claimType>/sweep-vN`), `gridCap`, `variantsExecuted`,
  `axes[{name, values, origin}]`, `results[{findingId, aggregate, passCount, failCount,
  cells[{variant, point, passed, margin}]}]` (≤ 1000 cells). Built by
  `presenter.sensitivity_dto` from the examination after reveal; `null` when BLOCKED.
  Evaluators never see either structure.

## 6. Key records (correction 6)

`recordRole ∈ {ILLUSTRATIVE, COUNTEREXAMPLE, INTERNAL_TRACE}`,
`recordKind ∈ {GRID_POINT, WORKSHEET_LINE, TRADE, EQUITY_SERIES, LEDGER_ENTRY, LOCAL_CHECK}`.
* `COUNTEREXAMPLE` only for `GRID_POINT` or `WORKSHEET_LINE`, and only for a finding whose
  status is `CONTRADICTED/REFUTED/CONDITIONAL/IMPOSSIBLE`.
* `TRADE` and `EQUITY_SERIES` are always `ILLUSTRATIVE`: an aggregate trading claim is never
  refuted by one losing trade.
* `LEDGER_ENTRY` is `INTERNAL_TRACE`; `LOCAL_CHECK` (post-reveal) is never a counterexample.

## 7. Progress events (correction 7)

`ProgressEvent{runId, seq, stage, at, ledgerSeq, ledgerKind, detail}`. Write-then-emit: each
event is appended to the persisted `RunRecord` before it is sent; SSE `id = seq`; reconnect
with `Last-Event-ID` replays from the record. Stages that correspond to ledger appends
(`EXAMINATION_COMMITTED, OUTCOMES_REVEALED, VERDICT_SEALED, DIAGNOSTICS_APPENDED,
BUNDLE_WRITTEN`) must carry the matching `ledgerSeq/ledgerKind`; pre-ledger stages carry
`null`. UI animations may only be driven by these events.

## 8. Privacy and pasted text (correction 8)

Frozen schemas still contain no free text. Reel intake may accept `pastedText`
(≤ 2000 chars), parsed deterministically in the Custodian (no LLM). URLs, @handles,
emails and phone numbers ⇒ `PRIVACY_REJECTED` (ISO dates must not trip the phone rule).
The text is never persisted, logged, frozen or bundled; spans exist only in the draft
response. Quote intake rejects `pastedText`.

## 9. Isolation (correction 9)

Unchanged from ARCHITECTURE §4: two OS users, encrypted vault, blinded tasks. Every
response carries `isolationMode`; judge mode refuses to start unless `ENFORCED`.

## 10. Integrity ≠ reproducibility ≠ authenticity (correction 10)

| Report | Question | Values |
|---|---|---|
| `integrity` | Is the bundle internally consistent since it was written? (manifest hashes, ledger chain, commitment, spec hash) | `VERIFIED / FAILED` |
| `reproducibility` | Does re-execution give the same verdict hash? | `REPRODUCED / REPRODUCED_ACROSS_ENV / DIVERGED / UNVERIFIABLE`; `NOT_RUN` in metadata |
| `authenticity` | Did our deployment produce it? | always `NOT_ESTABLISHED` (bundles are unsigned in v1) |

The UI and write-up must never present integrity or reproducibility as proof of origin.

## 11. Implementation notes (server behaviour, 1.1.0)

* `POST /cases/{caseId}/runs` executes the run to a terminal state before answering
  `202 RunAccepted` (state `COMPLETED` or `INDETERMINATE`); a repeated call returns the
  existing run. Infrastructure failure (examiner unreachable or unauthenticated, spec
  substitution, commitment mismatch) yields run state `FAILED`, HTTP 500
  `RUN_FAILED`, no bundle and no verdict.
* The SSE stream replays the persisted `RunRecord` (`id = seq`, `event: progress`) and
  ends at the terminal event; `Last-Event-ID` must be a non-negative integer.
* `GET /cases/{caseId}/outcome` answers `425 TOO_EARLY` until a verdict is sealed, or a
  `BLOCKED` `OutcomeResponse` when freeze or evidence was refused.
* Case routes answer `503 CUSTODY_NOT_CONFIGURED` unless `VK_DRAFT_DIR` and a 32-byte
  base64 `VK_VAULT_KEY` are configured. Only claim types in the `ClaimTypeId` enum are
  exposed over HTTP.
* `POST /replays` never refetches; malformed, oversized (> 64 MiB uncompressed) or
  integrity-failing bundles are reported `UNVERIFIABLE` and are not re-executed. At most
  two replays run concurrently (`429` otherwise).
* In judge mode every case, frozen or not, is purged 24 h after intake.
* `SYNTHETIC_DEMO` is implemented as specified in §3: `POST /cases` accepts only a bundled
  `fixtureId` (Reel: `fx_reel_supported_hold`, `fx_reel_conditional_sma`,
  `fx_reel_impossible_sma`), refuses any form or pasted text, and the case cannot be
  edited. Evidence is the labelled synthetic series (origin `SYNTHETIC_FIXTURE`, licence
  `SYNTHETIC`, embedded in the bundle). A `LIVE_EVIDENCE` claim on the synthetic
  instrument is `BLOCKED / POLICY_VIOLATION`. No schema changed for this.
* Unknown document facts (Quote) are sent as `null` parameters plus a missing assumption
  of the same name in `form.assumptions`; the ledger reports them as `ASSUMED` with the
  swept set. No schema changed for this.
