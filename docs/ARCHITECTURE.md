# VerdictKit — Technical Architecture (frozen-scope baseline)

Status: reviewer baseline. Author role: architecture (Claude).
Scope is frozen per the team consensus of 2026-11-16. This document resolves the remaining
technical contradictions, fixes the interfaces, and defines the security boundaries the
implementation must honour. Implementation is to be performed through Kiro's spec workflow
(see §11), not hand-written outside it.

---

## 0. Blocking contradictions — resolved decisions

Each item was a real conflict between two frozen requirements. Each has a decision that the
specs below already encode. Items marked **DECISION NEEDED** must be closed by the team
before the listed date.

| # | Conflict | Resolution |
|---|---|---|
| B1 | **Offline replay vs. no restricted financial data.** Neither Coinbase Exchange market data (proprietary, distributed through authorised redistribution partners) nor Binance Vision (governed by its own dataset terms) is clearly licensed for re-hosting inside a downloadable bundle. | Evidence carries a `license_class`. `REDISTRIBUTABLE` evidence is embedded in bundles. `REFETCH_ONLY` evidence is sealed by URI + SHA-256 only; replay is offline **once the replayer's own local cache holds bytes with the sealed hash**, and the replay report says so. Quote Autopsy bundles are fully self-contained (user-entered document values + fact excerpts from official sources). **DECIDED 2026-11-16 (ChatGPT review):** Binance and Coinbase are provisionally `REFETCH_ONLY` with rights basis `UNVERIFIED`; raw data is never distributed. Tests and demos use labelled `SYNTHETIC_FIXTURE` data in `SYNTHETIC_DEMO` cases (no confidence class). `LIVE_EVIDENCE` with an unverified source is `BLOCKED`. Real-data integration waits for a documented rights basis. |
| B2 | **"Payment packing" reveal needs the claimed payment, but evaluation must be blind to claimed outcomes.** | The verdict is computed blind (forward computation from itemised inputs). The inverse solve (implied amount financed from the stated payment) is a **post-reveal diagnostic**: it runs only after `VERDICT_SEALED` is in the ledger, cannot change any finding status, and is rendered with a "diagnostic — computed after reveal" label. Enforced by the ledger state machine. |
| B3 | **"Real access separation" vs. Windows development environment.** OS-user separation is POSIX-only. | Isolation is enforced in the Linux container (two OS users, see §4). Native dev runs set `isolation_mode=UNENFORCED`; every ledger, bundle and UI view stamps it, and judge mode refuses to start unless `ENFORCED`. A contract test asserts this. |
| B4 | **Disqualification risk: "insufficient use of Kiro."** If reviewer AIs write the implementation, Kiro's role is thin. | These documents are *inputs*. Feed them into Kiro's spec workflow so Kiro owns the final `.kiro/specs`, task execution, and property-test generation. Keep reviewer drafts under `docs/reviewer-inputs/`. The write-up states this honestly. |
| B5 | **"Reproducible" vs. "do not claim universal reproducibility."** | The verdict hash covers only deterministic content (spec hash, evidence hashes, examination result, revealed outcomes, findings). Timestamps, salts and ledger entries are excluded. Replay reports `REPRODUCED` (same env fingerprint), `REPRODUCED_ACROSS_ENV` (identical verdict hash, different fingerprint), `DIVERGED`, or `UNVERIFIABLE`. The env fingerprint = Python version + lockfile hash + engine version + container image digest (if known). |
| B6 | **Impossibility verdicts vs. defaulted assumptions.** A bound computed under a tool-chosen mechanic (e.g. "no leverage") proves nothing about a claimant who actually used 10× futures. | MVP supports only `SPOT_LONG_FLAT` (no margin, no shorting), which makes the bound sound without any leverage parameter. `IMPOSSIBLE` may be issued only when `instrument_mode` and the timeframe have origin `CLAIMANT` or `USER_CONFIRMED`. A `DEFAULT_POLICY` origin downgrades the finding to `INDETERMINATE` with reason `bound_requires_declared_mechanics`. |
| B7 | **Tax jurisdiction.** One state only (frozen), but local rates vary. | State rate is external evidence. When the locality is unknown, local add-on rates become a swept assumption over the official published range, so the finding may be `CONDITIONAL`. **DECIDED: Texas (TX).** Texas has no local motor vehicle tax, so the rate range is degenerate (6.25 %) and the finding is SUPPORTED or REFUTED. The $225 documentary fee is a presumed-reasonable amount, not a cap, so a higher fee is INDETERMINATE (`requires_regulator_filing`), never REFUTED. Lease payments are not taxed per payment in Texas, so lease `tax_rate` is INDETERMINATE (`not_applicable_lease_tax_model`). See `docs/B7_TEXAS_SPEC.md`. |
| B8 | **Judge access until Jan 29, 2027.** | Hosting must not sleep or expire during judging; budget for ~11 weeks. Judge mode is stateless apart from a TTL case cache. |

---

## 0a. API and presentation adapter
HTTP routes, DTOs, execution vs. epistemic status, progress events and the
integrity/reproducibility/authenticity split: `docs/API_CONTRACT.md`, `api/openapi.yaml`.

## 1. System overview

```
                 ┌──────────────────────── container (Linux) ────────────────────────┐
 Browser ──HTTPS─▶  API / Custodian  (uid vk-custodian)                                │
 (Reel UI,        │   • intake: validate → canonicalise → partition → freeze          │
  Quote UI)       │   • vault: seal claimed outcomes (AES-GCM), dir 0700             │
                  │   • ledger: hash-chained, state-machine enforced                  │
 Kiro / MCP ─stdio▶  • comparator: reveal → compare → findings → verdict            │
 client           │   • diagnostics (post-reveal only)                                │
                  │   • bundle writer                                                 │
                  │          │  BlindedTask (params + evidence refs, NO outcomes)    │
                  │          ▼  unix socket, JSON, size-capped                        │
                  │  Examiner (uid vk-examiner, no read perm on vault)                │
                  │   • evidence broker (policy allowlist, content-addressed store)  │
                  │   • sweep engine (bounded grid)                                   │
                  │   • domain evaluators (pure, Decimal, no network, no LLM)         │
                  │          │  ExaminationResult (per-point computed values)        │
                  │          ▼                                                        │
                  │  Custodian commits EXAMINATION_COMMITTED → only then reveals      │
                  └───────────────────────────────────────────────────────────────────┘
 Offline:  verdictkit replay bundle.vkb  → same engine, no network (unless --allow-refetch)
```

Two applications (`apps/reel-autopsy`, `apps/quote-autopsy`) are independent services built
from the same core. Each contributes only: a claim-type plugin, evidence adapters, evaluators,
an optional post-reveal diagnostic, and its own UI. A third stub claim type in
`core/examples/` proves the core needs no changes for a new domain.

## 2. Lifecycle and ledger state machine

```
CASE_OPENED → CLAIM_FROZEN → OUTCOMES_COMMITTED → EVIDENCE_ACQUIRED
            → EXAMINATION_COMMITTED → OUTCOMES_REVEALED → VERDICT_SEALED
            → (DIAGNOSTICS_APPENDED)*  → BUNDLE_WRITTEN
```

* Each entry: `{seq, kind, payload_hash, prev_hash, entry_hash, recorded_at}`;
  `entry_hash = SHA256("vk-ledger-v1" ‖ seq ‖ kind ‖ payload_hash ‖ prev_hash)`.
  `recorded_at` is informational and excluded from `entry_hash`.
* Any out-of-order append raises `LedgerOrderError`. In particular, `OUTCOMES_REVEALED`
  is impossible before `EXAMINATION_COMMITTED`, and diagnostics are impossible before
  `VERDICT_SEALED`.
* **What the ledger proves:** internal ordering and tamper-evidence of the bundle's own
  record. **What it does not prove:** wall-clock time or that no one ran the evaluator
  twice outside the system. We do not claim trusted timestamping.

## 3. Data model (summary — exact types in `core/src/verdictkit/model.py`)

* **FrozenClaim** — `claim_type`, `schema_version`, `params` (canonical), `assumptions`
  (each with value/range/set/missing + `origin`), `tolerances`, `spec_hash`.
  `spec_hash` covers params + assumptions + tolerances + type/version, **not** outcomes.
* **SealedOutcomes** — ciphertext in vault + `Commitment{alg, digest}` where
  `digest = SHA256("vk-commit-v1" ‖ salt(32B) ‖ canonical(outcomes))`.
* **BlindedTask** — `case_id`, `spec_hash`, `claim_type`, `params`, `assumption_grid`,
  `evidence_refs`. Constructed by a function whose input type cannot contain outcomes.
* **EvidenceItem** — `source_id`, `source_class`, `uri`, `retrieved_at`, `sha256`,
  `media_type`, `license_class ∈ {REDISTRIBUTABLE, REFETCH_ONLY, DOCUMENT, USER_SUPPLIED}`.
* **Finding** — `finding_id`, `basis`, `status`, `statement`, `confidence_scope`,
  `evidence_used`, `assumption_dependencies`, `counterexamples`, `numbers` (expected,
  observed, difference, tolerance — all Decimal strings).
* **Verdict** — ordered findings + overall headline + `verdict_hash`.

### 3.1 Verdict taxonomy (basis × status). Other combinations are rejected.

| Basis | Allowed statuses | Confidence scope (fixed wording) |
|---|---|---|
| `INTERNAL_ARITHMETIC` | `CONSISTENT`, `CONTRADICTED`, `CONDITIONAL`, `INDETERMINATE` | "Given the frozen document values and the stated formula convention." No external evidence used. `CONDITIONAL` only when the result varies across swept document facts the worksheet did not show (e.g. taxability) or across disclosed rounding conventions. |
| `EXTERNAL_EVIDENCE` | `SUPPORTED`, `REFUTED`, `CONDITIONAL`, `INDETERMINATE` | "Given the cited evidence snapshots and the declared assumption ranges." |
| `MECHANICAL_BOUND` | `WITHIN_BOUND`, `IMPOSSIBLE`, `INDETERMINATE` | "Given the declared mechanics only (see B6)." |

Headline rule: worst status wins in the order `IMPOSSIBLE > CONTRADICTED > REFUTED >
CONDITIONAL > INDETERMINATE > SUPPORTED/CONSISTENT/WITHIN_BOUND`. The UI always shows all
findings; the headline never hides an INDETERMINATE.

## 4. Security boundaries and threat model

### 4.1 Principals
* **vk-custodian** — runs API, intake, vault, ledger, comparator, bundle writer. Holds the
  vault key in process memory (from `VK_VAULT_KEY` at boot, never passed to children).
* **vk-examiner** — long-lived worker under its own uid. Both processes are started by a
  root entrypoint that immediately `exec`s each under its own uid via `setpriv`; no
  long-lived root process remains.
* **judge / user** — unauthenticated in judge mode; can submit claims and download bundles.

### 4.2 Boundaries and enforcement

| Boundary | Enforcement (runtime, not hooks) | Verified by |
|---|---|---|
| Examiner cannot read claimed outcomes | (a) outcomes never serialised into `BlindedTask` (type-level partition); (b) vault dir `0700` owned by vk-custodian; (c) vault payloads AES-GCM encrypted with a key the examiner never receives; (d) examiner env scrubbed (`env -i` + allowlist) | P2, P3, isolation integration test (container only) |
| Reveal cannot precede examination | ledger state machine in custodian | P6 |
| Evidence must come from permitted, non-claimant sources | `EvidencePolicy` checked by broker before use and again by comparator before a finding may cite it; violation ⇒ `INDETERMINATE(policy_violation)`, never a pass | P8 |
| Evidence cannot change silently | content-addressed store; hash recomputed on every read | P9 |
| No LLM in the verdict path | CI import-fence over `verdictkit.custody`, `verdictkit.examiner`, `verdictkit.sweep`, `verdictkit.evidence`, and app evaluator modules; LLM use, if any, lives in an `assist/` package whose output is marked `EXTRACTED` and requires user confirmation before freezing | contract test `test_llm_fence.py` (runs today) |
| Examiner resource abuse | `RLIMIT_CPU`, `RLIMIT_AS`, socket message cap (8 MiB), sweep cap (≤ 1000 points), per-IP rate limit in judge mode | config tests |
| Judge-mode privacy | no names/VIN/addresses in schemas; free-text fields rejected; TTL cache (24 h); no analytics on case contents | schema tests |

### 4.3 What we explicitly do **not** claim
* Hash commitments alone do not provide isolation — isolation is the OS-user + encryption +
  type-partition combination above.
* Separation is within one host/trust domain. A root compromise of the container defeats it.
* Two evidence sources being "independent" in the world is not proven; we enforce
  independence **from the claimant** and record provenance.
* Not every claim is verifiable. Underspecified claims yield INDETERMINATE or CONDITIONAL.
* Reproducibility is claimed for a pinned environment (B5).

### 4.4 Why blinding matters for deterministic code
Judges may ask: "if evaluators are pure functions, what does blinding add?" Answer: the
blinding guarantees hold for every future plugin, including ones contributed by others
or drafted with AI assistance. A plugin cannot be anchored to the claimed answer because it
structurally never receives it. Property P2 tests this for every registered claim type.

## 5. Determinism rules
* No floats anywhere in claims, evidence parsing, evaluators or findings. Canonicaliser
  rejects floats, NaN/Infinity, duplicate keys, non-string map keys.
* Money/rates are `Decimal` parsed from strings; arithmetic in an explicit
  `decimal.localcontext(prec=34, rounding=ROUND_HALF_EVEN)`; currency outputs quantised by
  the claim type's declared convention (Quote: `ROUND_HALF_UP` to cents).
* Canonical JSON: UTF-8, sorted keys, no insignificant whitespace, Decimals as strings,
  ints as JSON integers.
* Sweep order: lexicographic by assumption name, then ascending value.
* Bundles: zip with fixed timestamps (1980-01-01), sorted entries, fixed permissions.
* Wall-clock time is never an evaluator input.

## 6. Bounded sensitivity analysis
* Each assumption: `fixed(value)`, `range(min,max,step)`, `set(values)`, or `missing`.
* Missing + claim type supplies a `DEFAULT_POLICY` range ⇒ swept, disclosed in the report.
* Missing + no policy range ⇒ findings that declare a dependency on it become
  `INDETERMINATE(missing_assumption:<name>)`; unaffected findings still evaluate.
* Grid size cap 1000 (configurable down only). Over-cap ⇒ intake rejects with a message;
  it never silently subsamples.
* Aggregation per finding: all points pass ⇒ SUPPORTED; none ⇒ REFUTED; mixed ⇒
  CONDITIONAL with the flip region and **concrete counterexample points** (first failing and
  first passing point in sweep order, plus the worst point by margin).
* Report wording: "verified at N grid points"; never "for all values".

## 7. Bundle format (`.vkb`, zip)
```
manifest.json            # engine version, env fingerprint, isolation_mode, file hashes
claim/frozen.json        # FrozenClaim (canonical)
claim/commitment.json
claim/reveal.json        # salt + outcomes (present only after reveal)
evidence/index.json      # EvidenceItem[] incl. license_class
evidence/blobs/<sha256>  # REDISTRIBUTABLE / DOCUMENT / USER_SUPPLIED only
examination/result.json  # per-point computed values
verdict/verdict.json     # findings + verdict_hash
verdict/diagnostics.json # post-reveal diagnostics (optional, excluded from verdict_hash)
ledger/ledger.jsonl
report/report.html       # self-contained human report (optional)
```

## 8. Plugin interface (core contract)
Defined in `core/src/verdictkit/plugin.py`. A claim type declares: `type_id`,
`schema_version`, `param_fields`, `outcome_fields`, `assumption_specs()` (with policy
defaults and origins), `tolerances()`, `evidence_requests(params)`, `evidence_policy()`,
`examine(task, evidence, points) -> Examination` (all grid points in one call, so
point-independent work such as signals is computed once), `findings(frozen, examination,
outcomes, evidence) -> list[Finding]` (comparator-side, pure), and optional
`diagnose(...)` (post-reveal). The core owns everything else.

## 8a. Contract-test validation status (2026-11-16)

`tests/contract/` holds 159 tests. Against the shipped interface stubs: 47 pass (oracle
self-checks, LLM fence, spec constants), 108 fail with `NotImplementedError` only, and 4
container-only isolation tests skip outside the image. To make sure the tests are
satisfiable and not wrong, they were also run, under the derandomised `ci` profile,
against a throwaway reference implementation that was **not** committed (so the
implementation remains Kiro's): 155 passed, 4 skipped. Two issues surfaced and are fixed:
the sweep test now expects rejection for over-cap random grids, and the simulator spec now
defines a *relative* rounding clamp after buys (residue of −2.9e-20 observed at equity
≈1.6e14).

## 9. Application designs (summary; full detail in each spec)

### 9.1 Reel Autopsy
* Claims are *mechanical*: one of four templates — `BUY_AND_HOLD`, `SMA_CROSS(fast, slow)`,
  `DONCHIAN_BREAKOUT(lookback)`, `RSI_REVERSION(period, lower, upper)` — on one spot
  instrument, one timeframe (`1h`, `4h`, `1d`), one UTC date range. No code generation.
* Execution semantics: signal on bar *t* close ⇒ fill at bar *t+1* open; costs = fee bps +
  slippage bps per side; target ∈ {0, 1}; entry buys `position_fraction × equity`;
  `cash ≥ 0` and `units ≥ 0` always (spot, long-or-flat, no margin).
* Claimed outcomes: `total_return_pct` (required), optional `max_drawdown_pct`,
  `trade_count`, `win_rate_pct`.
* Findings: reproduction (EXTERNAL_EVIDENCE, swept over fees/slippage), perfect-foresight
  bound (MECHANICAL_BOUND; B6 applies), data completeness (gaps ⇒ INDETERMINATE).
* Bound: over the holdable intervals `r_k` (open→open, final open→close),
  `bound = Π(1 + max(r_k, 0))`. Because cash and units are never negative, the fraction
  of equity in the asset is always in [0, 1], so each interval multiplies equity by at
  most `1 + max(r_k, 0)`; costs only reduce equity. The bound is therefore sound for every
  long-or-flat spot strategy trading at most once per bar, and tight (attained by the
  perfect-foresight target sequence at zero cost). Both facts are property-tested (P15).
* Legal: claim records carry no person names or handles; demo claims are anonymised.

### 9.2 Quote Autopsy
* Structured entry of a retail-installment (finance) worksheet or a lease worksheet. No OCR.
* Internal findings (no external evidence): line-item sums, tax = rate × base at the
  worksheet's stated rate, payment from stated AF/APR/term, total of payments, finance
  charge; lease depreciation + rent charge + tax.
* External findings: stated tax rate vs. official state(+local range) snapshot; doc fee vs.
  statutory cap if the state has one ("no statutory cap" is reported as such, not as a
  violation).
* Post-reveal diagnostic: implied amount financed from the stated payment; unexplained
  delta vs. itemised AF.
* Conventions disclosed: monthly payments, first payment one period after contract,
  `ROUND_HALF_UP` to cents, payment tolerance $0.01. MF ↔ APR (×2400) is labelled a
  convention, not an identity.

## 10. Repository structure
```
/                              (public GitHub, OSI license in About)
├── .kiro/
│   ├── specs/{verdictkit-core,reel-autopsy,quote-autopsy}/{requirements,design,tasks}.md
│   ├── steering/{product,tech,structure,verdict-integrity,money-math,testing}.md
│   ├── hooks/*.json
│   └── settings/mcp.json
├── core/                      # Python package `verdictkit` (the skeleton)
│   ├── src/verdictkit/{model,canonical,plugin,sweep,pipeline,bundle,envprint,mcp_server}.py
│   ├── src/verdictkit/{custody,examiner,evidence,api}/
│   └── examples/stub_claimtype/   # third-domain reuse proof
├── apps/
│   ├── reel-autopsy/   {src/reel_autopsy/, web/, fixtures/}
│   └── quote-autopsy/  {src/quote_autopsy/, web/, fixtures/}
├── ui-kit/                    # shared forensic React components (Muse's design system)
├── tests/contract/            # reviewer acceptance contract (this package)
├── deploy/                    # Dockerfile, entrypoint (two uids), compose
└── docs/                      # ARCHITECTURE.md, KIRO_USAGE.md, reviewer-inputs/
```
Stack: Python 3.12, FastAPI, `cryptography` (AES-GCM), Hypothesis, `uv` lockfile;
React + Vite + TypeScript for UIs; one Docker image, two app services.

## 11. Kiro usage plan (genuine, not decorative)

| Feature | Use | Why it is not artificial |
|---|---|---|
| Specs | Three feature specs; requirements in EARS; design includes numbered correctness properties; tasks traced to requirement IDs. | The product's own idea ("freeze the claim before judging it") mirrors spec-first development; the specs are the real build plan. |
| Property-based testing | Kiro extracts properties P1–P17 from the design and generates Hypothesis tests per package; `tests/contract/` is the independent reviewer contract. | The properties are the security and math guarantees of the product. |
| Steering | `verdict-integrity.md` (always) encodes non-negotiables; `money-math.md` and `testing.md` via fileMatch. | Prevents regressions the agent would otherwise introduce (floats, LLM imports, silent subsampling). |
| Hooks | `PostFileSave` command hooks run the relevant contract tests and the LLM fence when the agent edits evaluator/core files. | Kiro file hooks fire on **agent** edits only, so they are a development guardrail. Runtime guarantees live in code + CI; the write-up says exactly this. |
| MCP | VerdictKit ships an MCP server (`verify_claim`, `replay_bundle`, `explain_verdict`, `list_claim_types`), registered in `.kiro/settings/mcp.json`. Used during development to replay fixture bundles and in the demo to replay a judge-downloaded bundle from inside Kiro. | The MCP surface is a product feature (agents can verify claims), not a wrapper around someone else's API. |

## 12. Schedule and gates

| Date | Gate (kill criterion in bold) |
|---|---|
| Nov 16–17 | Kiro specs accepted; repo public with license + `.kiro/`; credits requested; B1 decision |
| Nov 18–22 | Core: canonical, partition, commitment, vault, ledger, examiner process, broker, sweep, bundle, replay. **Gate Nov 22: a stub-claim bundle replays to `REPRODUCED` offline, and P1–P10 pass.** If missed, freeze core features and cut stretch items. |
| Nov 23–26 | Reel Autopsy evaluators, bound, adapter, fixtures; B7 decision by Nov 26 |
| Nov 27–29 | Quote Autopsy finance + lease, state snapshot, diagnostics (Thanksgiving buffer) |
| Nov 30–Dec 2 | UIs on Muse's design system, container with enforced isolation, judge mode deploy, MCP demo |
| Dec 3 | Video, Kiro write-up, blog post; final acceptance run (ChatGPT) |
| Dec 4 | Buffer; submit before 14:00 PT |

## 13. Implementation risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Data-source terms block bundling (B1) | H | M | license classes + refetch replay; decided Nov 18 |
| Examiner IPC / uid setup eats days | M | H | single entrypoint script, unix socket JSON; fall back to subprocess-per-case under the examiner uid if the long-lived worker slips |
| Decimal performance on 1h bars × 1000 grid points | M | M | cap 1h ranges to 1 year; sweep only costs (signals computed once per param set; costs applied per point) |
| Two UIs halve polish time | H | H | shared ui-kit; Quote UI built second from the same components |
| Rounding-convention disputes in Quote | M | M | disclose convention; tolerance $0.01; CONDITIONAL rather than CONTRADICTED when a difference is within plausible alternative conventions |
| Kiro usage judged insufficient | M | H | B4 process; KIRO_USAGE.md with real spec/hook/MCP evidence |
| Judge-mode abuse / cost | L | M | rate limit, payload caps, no persistence |
