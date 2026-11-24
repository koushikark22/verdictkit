# Requirements Document — Quote Autopsy

## Introduction

Quote Autopsy verifies a vehicle dealer's retail-installment (finance) worksheet or lease
worksheet. The user types the worksheet's lines into a structured form (no OCR). Itemised
inputs and stated rates are parameters; the worksheet's stated derived figures (taxable
base, tax, amount financed, payment, totals) are sealed outcomes. The Examiner recomputes
the chain blind. The Custodian compares after reveal. Post-reveal diagnostics then
localise the first broken line and quantify any unexplained amount hidden in the payment.

Two kinds of finding are kept strictly apart:
* `INTERNAL_ARITHMETIC`: established from frozen document values and the disclosed formula
  convention alone. No external evidence.
* `EXTERNAL_EVIDENCE`: stated tax rate and doc fee compared with an official state-source
  snapshot for the single supported state.

## Requirements

### Requirement 1: Finance worksheet schema

#### Acceptance Criteria

1. THE claim type `quote.finance.v1` SHALL accept parameters: `selling_price`, `addons[]` (`code ∈ {SERVICE_CONTRACT, GAP, PAINT_PROTECTION, THEFT_ETCH, TIRE_WHEEL, OTHER}`, `amount`, `taxable`), `doc_fee`, `doc_fee_taxable`, `gov_fees[]` (`code ∈ {TITLE, REGISTRATION, PLATE, OTHER}`, `amount`, `taxable`), `rebates[]` (`amount`, `applied ∈ {PRE_TAX, POST_TAX}`), `trade_allowance`, `trade_payoff`, `trade_tax_credit`, `cash_down`, `stated_tax_rate_pct`, `apr_pct`, `term_months` (1–96), `jurisdiction` (`state`, optional `locality_code`).
2. THE claim type SHALL accept outcomes, each optional: `stated_taxable_base`, `stated_sales_tax`, `stated_amount_financed`, `stated_monthly_payment`, `stated_total_of_payments`, `stated_finance_charge`. At least one SHALL be present.
3. WHEN a taxability flag (`taxable`, `doc_fee_taxable`, `trade_tax_credit`) is not shown on the worksheet THE user SHALL be able to mark it unknown, and THE claim type SHALL treat it as an assumption swept over {true, false} with origin `DEFAULT_POLICY`.
4. THE claim schema SHALL contain no fields for names, addresses, VINs, dealer names or free text.

### Requirement 2: Lease worksheet schema

#### Acceptance Criteria

1. THE claim type `quote.lease.v1` SHALL accept parameters: `msrp`, `selling_price`, `capitalized_items[]` (`code ∈ {ACQUISITION_FEE, DOC_FEE, ADDON, OTHER}`, `amount`), `cap_cost_reductions[]` (`code ∈ {CASH, REBATE, NET_TRADE}`, `amount`), exactly one of `residual_value` or `residual_pct_of_msrp`, `money_factor`, `term_months` (1–60), `stated_tax_rate_pct`, `jurisdiction`.
2. THE claim type SHALL accept outcomes, each optional: `stated_gross_cap_cost`, `stated_adjusted_cap_cost`, `stated_residual_value`, `stated_depreciation_fee`, `stated_rent_charge`, `stated_base_payment`, `stated_monthly_tax`, `stated_total_monthly_payment`.
3. THE claim type SHALL support only the monthly-payment lease tax method in the MVP.

### Requirement 3: Finance arithmetic (blind, internal)

#### Acceptance Criteria

1. THE evaluator SHALL compute `taxable_base = selling_price + Σ taxable addons + (doc_fee if doc_fee_taxable) + Σ taxable gov_fees − (trade_allowance if trade_tax_credit) − Σ PRE_TAX rebates`, floored at 0.
2. THE evaluator SHALL compute `sales_tax = round_half_up(taxable_base × stated_tax_rate_pct / 100, 0.01)`.
3. THE evaluator SHALL compute `amount_financed = selling_price + Σ addons + doc_fee + Σ gov_fees + sales_tax − trade_allowance + trade_payoff − Σ rebates − cash_down`.
4. THE evaluator SHALL compute `monthly_payment = round_half_up(AF × i / (1 − (1 + i)^−n), 0.01)` with `i = apr_pct / 1200`, and `AF / n` rounded half-up when `apr_pct = 0`.
5. THE evaluator SHALL compute `total_of_payments = monthly_payment × n` and `finance_charge = total_of_payments − amount_financed`.
6. THE comparator SHALL report each stated value as `CONSISTENT` or `CONTRADICTED` with expected, observed and difference; tolerance $0.01 for payment-derived values and $0.00 for sums. Where the value depends on a swept taxability flag the finding SHALL be `CONDITIONAL` if results differ across points (allowed only because that flag's origin is recorded).
7. THE UI SHALL disclose conventions: monthly periods, first payment one period after contract, `ROUND_HALF_UP` to cents, no odd final payment.

> Note: Requirement 3.6 uses `CONDITIONAL` for an internal finding only when the outcome
> depends on a document fact the worksheet did not show. The model therefore allows
> `INTERNAL_ARITHMETIC × CONDITIONAL`; see design §Verdict-matrix change.

### Requirement 4: Lease arithmetic (blind, internal)

#### Acceptance Criteria

1. THE evaluator SHALL compute `gross_cap_cost = selling_price + Σ capitalized_items`, `adjusted_cap_cost = gross_cap_cost − Σ cap_cost_reductions`, `residual_value` = given value, or `msrp × residual_pct / 100` rounded half-up to cents.
2. THE evaluator SHALL compute `depreciation_fee = (adjusted_cap_cost − residual_value) / n`, `rent_charge = (adjusted_cap_cost + residual_value) × money_factor`, `base_payment = depreciation_fee + rent_charge`, `monthly_tax = base_payment × rate / 100`, `total_monthly_payment = base_payment + monthly_tax`.
3. THE evaluator SHALL evaluate the rounding convention as an assumption with values `COMPONENT` (round each component to cents before summing) and `FINAL` (round only displayed totals), swept unless the user confirms one.
4. THE UI SHALL label `APR ≈ money_factor × 2400` as a convention, not an identity.

### Requirement 5: External rate and fee checks

Decision B7: the single supported state is Texas (TX).

#### Acceptance Criteria

1. THE claim type SHALL use one supported state's rules snapshot, containing the state rate, the official range of local add-on rates (or a locality table), and a `doc_fee` rule, each with source URI, retrieval date and SHA-256 of the fetched source. THE `doc_fee` rule SHALL have a `kind` in {`STATUTORY_MAXIMUM`, `PRESUMED_REASONABLE_AMOUNT`, `NO_STATUTORY_LIMIT`}, an `amount` (a decimal string, or null only for `NO_STATUTORY_LIMIT`) and `applies_to` = `RETAIL_INSTALLMENT_CONTRACT`.
2. WHEN a locality code is given AND the snapshot has a locality table THE finding on the stated tax rate SHALL be `SUPPORTED` if it equals the official combined rate and `REFUTED` otherwise. WHEN the snapshot has no locality table (Texas has no local motor-vehicle tax) THE locality code SHALL be ignored and criterion 3 SHALL apply.
3. WHEN no locality applies THE finding on the stated tax rate SHALL be `CONDITIONAL` if the official combined range is not degenerate and the stated rate lies within it, and `REFUTED` if outside it. WHEN the range is degenerate (minimum equals maximum) THE finding SHALL be `SUPPORTED` if the stated rate equals it (Decimal equality) and `REFUTED` otherwise, never `CONDITIONAL`.
4. WHEN the doc-fee `kind` is `STATUTORY_MAXIMUM` THE finding SHALL be `REFUTED` if the doc fee exceeds `amount`, else `SUPPORTED`. WHEN the kind is `NO_STATUTORY_LIMIT` THE finding SHALL be `SUPPORTED` with statement "no statutory cap in <state>". WHEN the kind is `PRESUMED_REASONABLE_AMOUNT` (Texas, $225.00) THE finding SHALL be `SUPPORTED` if the doc fee is at or below `amount`, with a statement scoped to the retail installment contract that does not claim overall compliance, and `INDETERMINATE(requires_regulator_filing)` if above it. A doc fee above a presumed-reasonable amount SHALL NEVER be `REFUTED`, because a dealer may lawfully charge more after notifying the regulator and filing a cost analysis, which cannot be verified.
5. IF the jurisdiction is not the supported state THEN external findings SHALL be `INDETERMINATE(unsupported_jurisdiction)`; internal findings SHALL still run. IF the supported state's snapshot cannot be acquired or fails its integrity check THEN external findings SHALL be `INDETERMINATE(evidence_unavailable)`; internal findings SHALL be unchanged.
6. IF the claim type is `quote.lease.v1` AND the state is TX THEN the external `tax_rate` finding SHALL be `INDETERMINATE(not_applicable_lease_tax_model)`, because Texas does not tax lease payments as a rate on each payment.

### Requirement 6: Post-reveal diagnostics

**User Story:** As a car buyer, I want to know where the numbers went wrong and how much is
unexplained.

#### Acceptance Criteria

1. AFTER `VERDICT_SEALED` THE claim type SHALL compute local checks: each stated line against the formula applied to the *stated* preceding lines, and report the first broken line.
2. AFTER `VERDICT_SEALED` THE claim type SHALL compute `implied_amount_financed` from `stated_monthly_payment`, `apr_pct` and `term_months`, and `unexplained_amount = implied_amount_financed − itemised amount_financed`.
3. THE diagnostics SHALL be labelled "diagnostic — computed after reveal", SHALL NOT change any finding status, and SHALL be excluded from `verdict_hash`.
4. THE diagnostics SHALL report the inversion uncertainty: payment rounding to the cent bounds the implied amount financed to within `±0.005 × annuity_factor`.
