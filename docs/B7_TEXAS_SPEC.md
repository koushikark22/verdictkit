# B7 — Texas rules snapshot for Quote Autopsy: implementation specification

Status: **specification only, nothing implemented yet.** Written by Claude (Claude Code session,
2026-11-23) against `master` @ `97d1037`. Implementation is reserved for a real Kiro session
(see `docs/KIRO_B7_PROMPT.md`). Nothing in this document is Kiro activity.

Closes: quote tasks 4.1 and 5.1 (external part), requirements 5.1–5.5, decision **B7 = Texas (TX)**.

## 1. Scope

In scope (minimum):

* One hash-pinned Texas snapshot (`TX.json` + `MANIFEST.json`) built from official sources.
* A local, no-network evidence adapter that serves that snapshot.
* External findings `tax_rate` and `doc_fee_cap` for **`quote.finance.v1` only**.
* Loader schema change for the doc fee (section 4). A single "cap" number cannot represent Texas.

Out of scope (leave as-is, document as a limitation):

* `quote.lease.v1` external `tax_rate`. In Texas the lessor pays motor-vehicle tax on its
  purchase and lease payments are not taxed, so a per-payment "tax rate" check would be
  misleading. Lease external findings stay `INDETERMINATE`, with the new reason
  `not_applicable_lease_tax_model` when `state == "TX"`.
* Checking `doc_fee_taxable`. The Comptroller excludes a separately stated doc fee from
  the taxable total consideration. That is a good follow-up check, but it needs a new
  outcome field and a contract decision. Do not add it in this pass.
* Standard presumptive value, private-party sales, new-resident/gift/even-trade taxes,
  county title/registration fees, and verifying a dealer's OCCC filing.

## 2. Texas facts and their official sources

The person running Kiro must fetch each page **at implementation time**. For each one,
record the URI, the UTC retrieval date and the SHA-256 of the exact bytes retrieved, then
check the fact against the page. Do not copy facts from this table without fetching.

| Fact used by the snapshot | Official source (fetch and hash) |
|---|---|
| Motor vehicle sales tax rate is 6.25%, on the sales price less trade-in allowance | Texas Comptroller, *Motor Vehicle – Sales and Use Tax*: `https://comptroller.texas.gov/taxes/motor-vehicle/sales-use.php` |
| Current rate is 6.25% (historical table) | Comptroller pub. 96-254, *Tax Rates*: `https://comptroller.texas.gov/taxes/publications/96-254/tax-rates.php` |
| There is **no local motor vehicle tax** | Comptroller pub. 98-805: `https://comptroller.texas.gov/taxes/publications/98-805.php` |
| A separately stated documentary fee is **excluded** from taxable total consideration (informational for the follow-up check, not used in this pass) | Comptroller pub. 96-254, *Total Consideration*: `https://comptroller.texas.gov/taxes/publications/96-254/total-consideration.php` |
| $225 doc fee: a seller needs no OCCC notification or cost analysis at or below $225; **above $225 the seller must first notify the OCCC and file a cost analysis** (7 TAC §84.205, effective July 11, 2024; Tex. Fin. Code §348.006) | OCCC Bulletin B16-5 (rev. 7/2/24): `https://occc.texas.gov/wp-content/uploads/2025/11/b16-5-mvsf-doc-fee-filing-instructions-7-2-24_0.pdf` |
| Amendment status of §84.205 | OCCC rules page `https://occc.texas.gov/publications/rules`. A May 2026 precomment draft amended the cost-analysis rules for fees above $225 and said it does not affect fees of $225 or less. **Check whether anything adopted later changed the $225 amount before snapshotting.** |

**The $225 figure is not a cap.** It is the amount *presumed reasonable*. A Texas dealer
may lawfully charge more after filing with the OCCC. VerdictKit cannot see those filings.
So a doc fee above $225 must **never** be REFUTED in Texas.

The snapshot contains only these numbers: `state_rate_pct = "6.25"`,
`local_rate_min_pct = "0.00"`, `local_rate_max_pct = "0.00"`, `localities = null`, and the
doc-fee rule in section 4. If a fetched page disagrees with any of them, stop and report
the disagreement instead of picking one.

## 3. Files

| File | Change |
|---|---|
| `apps/quote-autopsy/src/quote_autopsy/rules.py` | Schema change (section 4). Keep the hash/manifest/canonical checks exactly as they are. |
| `apps/quote-autopsy/src/quote_autopsy/rules/TX.json` | **New.** Canonical JSON snapshot (sorted keys, no floats, no trailing newline). Must equal `canonical_bytes(doc)`. |
| `apps/quote-autopsy/src/quote_autopsy/rules/MANIFEST.json` | **New.** `{"files": {"TX.json": "<sha256 of TX.json bytes>"}}` |
| `apps/quote-autopsy/src/quote_autopsy/sources.py` (or `sources/rules_adapter.py`) | **New.** `TexasRulesAdapter`, section 5. |
| `apps/quote-autopsy/src/quote_autopsy/claim_type.py` | Finance: `evidence_requests`, `evidence_policy`, `evidence_adapters`, `examine` reads the snapshot, `findings` produces the external findings. Lease: TX reason code only. |
| `tests/integration/test_quote_rules_diagnostics.py` | Update the `CONSTRUCTED` fixture and the mutation cases to the new schema. |
| `tests/integration/test_quote_b7_texas.py` | **New.** Acceptance tests, section 7. |
| `tests/api/test_http_run_lifecycle.py` | Update `test_external_only_claim_is_indeterminate` (section 8). |
| `.kiro/specs/quote-autopsy/requirements.md`, `tasks.md`; `docs/TRACEABILITY.md`; `docs/RELEASE_READINESS.md`; `docs/KIRO_USAGE.md` | Update requirement 5.4 wording, tick 4.1/5.1, record B7 = TX, record what Kiro actually did. |

Hatchling packages everything under `src/quote_autopsy`, and the Dockerfile copies `apps/`,
so no build change should be needed. Verify by building the Docker image.

## 4. Snapshot schema change (`rules.py`)

Replace the field `"doc_fee_cap": "<amount>" | null` with:

```json
"doc_fee": {
  "kind": "STATUTORY_MAXIMUM" | "PRESUMED_REASONABLE_AMOUNT" | "NO_STATUTORY_LIMIT",
  "amount": "<decimal string>" | null,
  "applies_to": "RETAIL_INSTALLMENT_CONTRACT"
}
```

Loader rules (each violation raises `RulesIntegrityError`):

* `kind` must be one of the three values.
* `amount` must be a non-negative decimal string when `kind` is not `NO_STATUTORY_LIMIT`, and `null` when it is.
* `applies_to` is required and is the literal `"RETAIL_INSTALLMENT_CONTRACT"` in this version.
* The required top-level field set becomes `{state, state_rate_pct, local_rate_min_pct, local_rate_max_pct, localities, doc_fee, sources}`.
* `StateRules.doc_fee_cap` is replaced by `StateRules.doc_fee_kind` and `StateRules.doc_fee_amount`.

Texas value:
`{"kind": "PRESUMED_REASONABLE_AMOUNT", "amount": "225.00", "applies_to": "RETAIL_INSTALLMENT_CONTRACT"}`.

`sources` stays `[{uri, retrieved_at, sha256_of_source}]`. List every page from section 2
that a snapshot value depends on.

## 5. Evidence adapter

Follow the existing pattern in `apps/reel-autopsy/src/reel_autopsy/sources/synthetic.py`:

* `source_id = "tx-rules-snapshot-v1"`
* `requires_network = False` (this lets it pass `preflight_evidence` in the HTTP service)
* `source_class = SourceClass.GOVERNMENT_OFFICIAL`
* `license_class = LicenseClass.REDISTRIBUTABLE`. Add a `rights_note` saying it is a
  derived summary of Texas government publications, with source URIs listed inside the snapshot.
* `fetch()` reads `TX.json` and `MANIFEST.json` with `importlib.resources` and calls
  `load_rules(...)`. If that raises `RulesIntegrityError`, the adapter raises too, so no
  bytes are served. It returns `(TX.json bytes, "package://quote-autopsy/rules/TX.json", "application/json")`.

Finance claim type:

* `evidence_requests(params)` returns one `EvidenceRequest("tx-rules-snapshot-v1", {"state": "TX"})`
  **only when** `jurisdiction.state == "TX"`. Every other state returns `()`, which is
  today's behaviour.
* `evidence_policy()` returns `EvidencePolicySpec(frozenset({"tx-rules-snapshot-v1"}))`.
* `evidence_adapters()` returns `(TexasRulesAdapter(),)`.

## 6. Examination and findings

Blinding is unchanged. The examiner never sees outcomes.

**`examine`** (finance): if `task.evidence_refs` is non-empty, read the snapshot with
`evidence.read(ref)` and parse it with `parse_canonical`. Then put these strings in
`Examination.shared`:
`rules_state`, `rules_snapshot_sha256`, `official_rate_min_pct`, `official_rate_max_pct`,
`official_rate_by_locality` (null for TX), `doc_fee_kind`, `doc_fee_amount`, and
`doc_fee_charged` (from params). If there is no evidence, `shared` stays `{}`, which is
today's behaviour. The examiner must not re-verify the manifest. The broker store is
already hash-verified, and the adapter checked the manifest at acquisition.

**`findings`**, for each claimed external outcome (basis `EXTERNAL_EVIDENCE`,
`evidence_used = (rules sha256,)`, tolerance `"0"`):

| Situation | `tax_rate` (claimed rate R) | `doc_fee_cap` (evaluates `params.doc_fee` = F) |
|---|---|---|
| `state != "TX"` | INDETERMINATE, `unsupported_jurisdiction` | INDETERMINATE, `unsupported_jurisdiction` |
| TX, no evidence (acquisition failed or integrity failed) | INDETERMINATE, `evidence_unavailable` | INDETERMINATE, `evidence_unavailable` |
| TX, locality given (`localities` is null for TX) | Same as "no locality" (TX has no local motor-vehicle tax). The statement says the locality is irrelevant. | — |
| TX, R == 6.25 (Decimal equality, so "6.250" counts) | **SUPPORTED**. The range is degenerate (min == max), so there is no locality uncertainty and CONDITIONAL would be wrong. | — |
| TX, R != 6.25 | **REFUTED**, with numbers expected 6.25, observed R, difference, tolerance 0 | — |
| TX, F ≤ 225.00 | — | **SUPPORTED**: "at or below the $225 documentary fee presumed reasonable under 7 TAC §84.205; no OCCC filing required" |
| TX, F > 225.00 | — | **INDETERMINATE**, reason `requires_regulator_filing`: "above $225; permitted only if the dealer notified the OCCC and filed a cost analysis, which VerdictKit cannot verify". **Never REFUTED.** |
| `kind == STATUTORY_MAXIMUM` (other states later) | — | F ≤ amount → SUPPORTED, else REFUTED (requirement 5.4 as written) |
| `kind == NO_STATUTORY_LIMIT` | — | SUPPORTED, "no statutory cap in <state>" |

Notes:

* The outcome key stays `doc_fee_cap` so that API contract 1.1.0 is unchanged. The `reason`
  field is a free string in `api/openapi.yaml`, so the new reason codes need no contract change.
* The finding's claimed value is the outcome as submitted. It must still parse as money. The
  comparison uses the frozen `params.doc_fee`, because that is the fee on the worksheet.
* Internal arithmetic findings must be byte-identical with and without the snapshot. Only
  the external findings and the evidence list change.
* No other part of the verdict may change. In particular, `CONSISTENT` internal findings stay `CONSISTENT`.

Lease (`quote.lease.v1`) with `state == "TX"`: `tax_rate` → INDETERMINATE,
reason `not_applicable_lease_tax_model`. All other lease behaviour stays as it is today.

## 7. Acceptance tests (`tests/integration/test_quote_b7_texas.py`)

Each test names the requirement it covers.

1. `test_tx_snapshot_matches_manifest_and_is_canonical` (5.1): loading the packaged
   snapshot succeeds; `canonical_bytes(parse_canonical(b)) == b`; the SHA-256 equals the
   manifest entry; there is at least one source per fact, and every source has an `https://` URI, a date and a 64-hex hash.
2. `test_tx_snapshot_values` (5.1): rate 6.25, local range 0.00–0.00, localities null,
   doc fee kind `PRESUMED_REASONABLE_AMOUNT`, amount 225.00.
3. `test_loader_rejects_doc_fee_schema_violations` (5.1): `kind` not in the enum;
   `NO_STATUTORY_LIMIT` with an amount; a numeric (non-string) amount; a missing `applies_to`;
   an old-style `doc_fee_cap` field. Each raises `RulesIntegrityError`.
4. `test_tampered_snapshot_serves_no_evidence` (design, "hash mismatch"): with the adapter
   pointed at a copy of `TX.json` that has one byte changed, `broker.acquire` raises, and
   the resulting finance case gives `tax_rate` = INDETERMINATE(`evidence_unavailable`)
   while internal findings are unchanged.
5. `test_tx_tax_rate_supported_and_refuted` (5.2/5.3): through `run_case`, "6.25" and
   "6.250" → SUPPORTED; "6.00", "8.25" → REFUTED with numbers.expected == "6.25".
6. `test_tx_locality_does_not_change_rate` (5.2): `locality_code: "AUSTIN"` with "6.25" →
   SUPPORTED, and "8.25" → REFUTED. This shows local sales tax is not applied to motor vehicles.
7. `test_tx_doc_fee_at_or_below_presumed_amount_supported` (5.4, TX): F = 150.00 and
   F = 225.00 → SUPPORTED.
8. `test_tx_doc_fee_above_presumed_amount_is_never_refuted` (5.4, TX): F = 225.01, 500.00
   and 1500.00 → INDETERMINATE, reason `requires_regulator_filing`. Never REFUTED.
9. `test_non_tx_external_findings_unsupported_jurisdiction` (5.5): `state: "CA"` →
   both external findings INDETERMINATE(`unsupported_jurisdiction`), no evidence acquired,
   and internal findings unchanged.
10. `test_tx_lease_tax_rate_not_applicable` (scope): lease, TX, `tax_rate` → INDETERMINATE(`not_applicable_lease_tax_model`).
11. `test_external_snapshot_does_not_change_internal_verdict` (core invariant): the same TX
    claim with only internal outcomes gives identical internal findings and statuses
    whether the adapter is registered or not.
12. `test_tx_bundle_replays_offline` (core 9): `write_bundle` then `replay_bundle(..., allow_refetch=False)`
    gives integrity VERIFIED and a reproducibility match. The snapshot bytes are embedded
    because the license is REDISTRIBUTABLE.
13. `test_http_tx_case_acquires_official_evidence` (HTTP): a LIVE_EVIDENCE TX finance case
    goes through freeze → evidence, and the evidence list has exactly one item with origin
    `GOVERNMENT_OFFICIAL`. The run's `tax_rate` = "6.25" finding → SUPPORTED.
14. `test_mcp_verify_claim_tx` (MCP): `mcp_server.verify_claim` with `VK_MCP_READONLY=1`
    and a TX claim → `tax_rate` SUPPORTED. This proves the local adapter works without network.

## 8. Existing tests that will change, and why

* `tests/api/test_http_run_lifecycle.py::test_external_only_claim_is_indeterminate` uses
  a TX worksheet with `tax_rate: "6.00"`. After B7 that is REFUTED, correctly. Change its
  jurisdiction to a non-TX state, so it keeps testing the INDETERMINATE path, and add the
  TX case as test 13. Do not change it to make a failure go away silently.
* `tests/integration/test_quote_rules_diagnostics.py`: the `CONSTRUCTED` fixture and the
  `doc_fee_cap="-1"` mutation move to the new `doc_fee` object.
* Browser E2E (`tests/ui/e2e_browser.cjs`): the Quote constructed examples are TX, so the
  evidence panel will now show one GOVERNMENT_OFFICIAL item. Update only assertions that
  break because of that, and say so in the commit message.
* `tests/api/test_m3b_http_drafts.py` expects `evidence == []`. Its payload has no
  jurisdiction, so it should be unaffected. If it changes, investigate rather than edit.

## 9. Invariants (from `.kiro/steering/verdict-integrity.md`; all must still hold)

* No fabricated rule, rate or fee. Every snapshot value must trace to a fetched, hashed source.
* INDETERMINATE is never turned into SUPPORTED or CONSISTENT by a default.
* No network in evaluators or in the adapter.
* Outcomes stay blind to the examiner, and `verdict_hash` stays deterministic.
* Diagnostics stay post-seal and unchanged.

## 10. Definition of done

* `uv run --no-sync ruff check .` is clean, and `HYPOTHESIS_PROFILE=ci uv run --no-sync pytest -q -m "not isolation"` passes, including all 14 new tests.
* `npm run typecheck && npm test && npm run build`, and `bash scripts/ui_e2e.sh` passes.
* The Docker gate (`bash scripts/gate_nov22.sh` or the CI job) is green on the PR.
* `docs/KIRO_USAGE.md` records what was actually done inside Kiro (spec, hook, MCP call and
  so on), with the commit SHA. Anything done outside Kiro is labelled as such.
