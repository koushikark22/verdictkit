# Implementation Plan — Quote Autopsy

Window: Nov 27–29 (Thanksgiving buffer). State decision (B7) closed by Nov 26.

- [x] 1. Money and worksheet models (`money.py`, `worksheet.py`)
  - _Requirements: 1.1–1.4, 2.1–2.3_

- [x] 2. Finance chain (`finance.py`)
  - [x] 2.1 Taxable base, tax, AF, payment, TOP, finance charge
  - [x] 2.2 Property tests P16, P16b, P17b — contract: `test_quote_contract.py`
  - _Requirements: 3.1–3.5_

- [x] 3. Lease chain (`lease.py`)
  - [x] 3.1 COMPONENT and FINAL conventions
  - [x] 3.2 Property test P17 — contract: `test_quote_contract.py::test_lease_identity`
  - _Requirements: 4.1–4.4_

- [ ] 4. State rules snapshot (`rules.py`, `rules/<state>.json`)
  - [ ] 4.1 Snapshot of official sources with URI, retrieval date, SHA-256; loader verifies hash
    - Loader done (`rules.py`, hash + canonical + schema checks, tests in
      `tests/integration/test_quote_rules_diagnostics.py`). Blocked: no official snapshot until decision B7.
  - _Requirements: 5.1_

- [ ] 5. Claim types (`claim_type.py`)
  - [ ] 5.1 Schemas, taxability-flag sweeps, rounding-convention sweep, internal + external findings
    - Done: schemas, internal findings. Open: taxability and rounding sweeps. Blocked: external findings (B7).
  - _Requirements: 3.6, 5.2–5.5_

- [x] 6. Diagnostics (`diagnostics.py`)
  - [x] 6.1 Local checks; payment-packing with inversion bound; registered as post-reveal
  - [x] 6.2 Property test P17c
  - _Requirements: 6.1–6.4_

- [ ] 7. UI (`web/`) on the shared ui-kit: dissection table, point-of-failure marker, payment-packing reveal, bundle download

- [ ] 8. Demo fixtures: worksheets built from real arithmetic with deliberately planted, documented discrepancies (labelled as constructed examples), plus one fully consistent worksheet

Note: task 1 models implement a reduced field set relative to requirements 1.1–2.1; see `docs/TRACEABILITY.md`.
