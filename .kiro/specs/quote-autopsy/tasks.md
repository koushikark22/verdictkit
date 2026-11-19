# Implementation Plan — Quote Autopsy

Window: Nov 27–29 (Thanksgiving buffer). State decision (B7) closed by Nov 26.

- [ ] 1. Money and worksheet models (`money.py`, `worksheet.py`)
  - _Requirements: 1.1–1.4, 2.1–2.3_

- [ ] 2. Finance chain (`finance.py`)
  - [ ] 2.1 Taxable base, tax, AF, payment, TOP, finance charge
  - [ ] 2.2 Property tests P16, P16b, P17b — contract: `test_quote_contract.py`
  - _Requirements: 3.1–3.5_

- [ ] 3. Lease chain (`lease.py`)
  - [ ] 3.1 COMPONENT and FINAL conventions
  - [ ] 3.2 Property test P17 — contract: `test_quote_contract.py::test_lease_identity`
  - _Requirements: 4.1–4.4_

- [ ] 4. State rules snapshot (`rules.py`, `rules/<state>.json`)
  - [ ] 4.1 Snapshot of official sources with URI, retrieval date, SHA-256; loader verifies hash
  - _Requirements: 5.1_

- [ ] 5. Claim types (`claim_type.py`)
  - [ ] 5.1 Schemas, taxability-flag sweeps, rounding-convention sweep, internal + external findings
  - _Requirements: 3.6, 5.2–5.5_

- [ ] 6. Diagnostics (`diagnostics.py`)
  - [ ] 6.1 Local checks; payment-packing with inversion bound; registered as post-reveal
  - [ ] 6.2 Property test P17c
  - _Requirements: 6.1–6.4_

- [ ] 7. UI (`web/`) on the shared ui-kit: dissection table, point-of-failure marker, payment-packing reveal, bundle download

- [ ] 8. Demo fixtures: worksheets built from real arithmetic with deliberately planted, documented discrepancies (labelled as constructed examples), plus one fully consistent worksheet
