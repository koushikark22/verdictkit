# Design Document — Quote Autopsy

## Overview

Two claim types (`quote.finance.v1`, `quote.lease.v1`) sharing a money module, a tax
module and a state-rules snapshot. Pure `Decimal` evaluators; no network in evaluators.

## Components and Interfaces (`apps/quote-autopsy/src/quote_autopsy/`)

| Module | API |
|---|---|
| `money.py` | `D(str)`, `cents(x)` (ROUND_HALF_UP to 0.01), `CTX` local context |
| `finance.py` | `taxable_base(ws, flags)`, `sales_tax(base, rate_pct)`, `amount_financed(ws, tax)`, `monthly_payment(af, apr_pct, n)`, `annuity_factor(apr_pct, n)`, `implied_amount_financed(payment, apr_pct, n)`, `chain(ws, flags) -> FinanceChain` |
| `lease.py` | `chain(ws, convention) -> LeaseChain` |
| `worksheet.py` | `FinanceWorksheet`, `LeaseWorksheet`, item dataclasses, `TaxFlags` |
| `rules.py` | `StateRules` snapshot loader (hash-verified), `combined_rate(locality)`, `rate_range()`, `doc_fee_kind`, `doc_fee_amount` (`doc_fee` object: `STATUTORY_MAXIMUM` / `PRESUMED_REASONABLE_AMOUNT` / `NO_STATUTORY_LIMIT`, `applies_to`) |
| `sources.py` | `TexasRulesAdapter` (`tx-rules-snapshot-v1`): local, no-network `GOVERNMENT_OFFICIAL` / `REDISTRIBUTABLE` evidence adapter serving the hash-verified `rules/TX.json`; raises if `load_rules` fails, so no bytes are served |
| `claim_type.py` | `FinanceClaimType`, `LeaseClaimType` |
| `diagnostics.py` | `local_checks(ws, stated) -> list[LocalCheck]`, `payment_packing(stated, ws) -> PackingDiagnostic` (post-reveal only) |

## External evidence (decision B7 = Texas)

`FinanceClaimType` requests the `tx-rules-snapshot-v1` evidence only when `jurisdiction.state == "TX"`. The examiner reads the snapshot from the evidence broker and puts rule values in `Examination.shared`; it never sees outcomes. Texas rate 6.25 % with no local motor-vehicle tax gives a degenerate range, so the rate finding is SUPPORTED or REFUTED. Sources are hash-pinned in `rules/TX.json`; `rules/MANIFEST.json` pins the snapshot itself.

## Verdict-matrix change (core)

`INTERNAL_ARITHMETIC × CONDITIONAL` is allowed. It is used only when the internal result
varies across a swept *document fact* (an unshown taxability flag) or across the disclosed
rounding conventions. Its counterexamples show the exact flag/convention values under which
the stated figure is consistent and inconsistent.

## Dependency order of findings

Finance: `taxable_base → sales_tax → amount_financed → monthly_payment →
total_of_payments → finance_charge`. Lease: `gross_cap_cost → adjusted_cap_cost →
residual → depreciation_fee → rent_charge → base_payment → monthly_tax → total`.
Findings are listed in this order. The UI marks the first non-consistent finding as the
"point of failure" and later ones as "propagated"; the post-reveal local checks then say
whether each later line is internally consistent with the stated line before it.

## Key records
`WORKSHEET_LINE` records may be `COUNTEREXAMPLE` for the first non-consistent finding;
propagated lines are `ILLUSTRATIVE`; post-reveal local checks are `LOCAL_CHECK`
(`ILLUSTRATIVE`), never counterexamples (docs/API_CONTRACT.md §6).

## Correctness Properties

* **P16 Amortization exactness** — for principal in [$1, $200 000], APR in [0, 30]% (0.001
  steps) and n in [1, 96], `monthly_payment` equals the exact rational annuity payment
  rounded half-up to the cent (Fraction oracle), excluding inputs within 10⁻¹² of a
  half-cent boundary. *(Req 3.4)*
* **P16b Inversion bound** — `|implied_amount_financed(monthly_payment(P)) − P| ≤
  0.005 × annuity_factor + 0.01`. *(Req 6.2, 6.4)*
* **P17 Lease identity** — `base_payment = depreciation_fee + rent_charge` and the FINAL
  convention equals the Fraction oracle before display rounding; for tax rates ≤ 15 %, COMPONENT
  and FINAL totals differ by at most $0.02 (bound: `0.01·(1+ρ) + 0.01` < 0.03, and both
  totals are whole cents). *(Req 4.1–4.3)*
* **P17b Tax monotonicity** — sales tax is non-decreasing in rate and in base. *(Req 3.2)*
* **P17c Diagnostics are inert** — `verdict_hash` is identical with and without
  diagnostics; diagnostics cannot be computed before `VERDICT_SEALED`. *(Req 6.3)*

## Error Handling
* Negative amount financed or residual > adjusted cap cost ⇒ intake rejection with message.
* Unsupported jurisdiction ⇒ external findings INDETERMINATE(`unsupported_jurisdiction`); internal still run.
* Rules snapshot hash mismatch or acquisition failure ⇒ external findings INDETERMINATE(`evidence_unavailable`); internal findings unchanged.
* Texas doc fee above the presumed-reasonable $225 ⇒ INDETERMINATE(`requires_regulator_filing`), never REFUTED.
* Texas lease `tax_rate` ⇒ INDETERMINATE(`not_applicable_lease_tax_model`).
* The outcome key `doc_fee_cap` is kept so API contract 1.1.0 is unchanged; it evaluates the worksheet `doc_fee` against the snapshot `doc_fee` rule.

## UI evidence of genuine behaviour (for Muse's storyboard)
* Worksheet "dissection table": each line shows stated vs recomputed with a live diff.
* The "point of failure" marker comes from the first non-consistent finding.
* The payment-packing reveal animates only after the API returns `diagnostics` (i.e.
  after `VERDICT_SEALED`), showing implied vs itemised amount financed and the ± bound.
