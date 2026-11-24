# Release readiness (2026-11-20)

**Status: validated demonstration, not production-ready.**

## What is validated
* Custody pipeline, blinding, commitment, ledger, bundles and offline replay: unit,
  property and contract tests (see `docs/TRACEABILITY.md`).
* Enforced isolation (two OS users, authenticated examiner socket, encrypted vault):
  container gates `gate-isolation`, `gate-startup`, `gate-http`, `gate-case` in CI.
* HTTP API contract 1.1.0: every response in the API tests is validated against
  `api/openapi.yaml`; browser E2E drives both UIs against a running API.
* Quote Autopsy document-internal arithmetic, sweeps and diagnostics; Reel Autopsy
  evaluator on labelled synthetic data.

## Why it is not production-ready
| Gap | Consequence | Owner action |
|---|---|---|
| No licensed historical OHLCV source (decision B1) | Real Reel claims are BLOCKED; only synthetic demonstrations run. | Obtain and document a rights basis, then implement and verify an adapter. |
| Texas-only external checks (decision B7 = TX) | Quote tax-rate and doc-fee checks run for Texas finance claims only; other states stay INDETERMINATE(`unsupported_jurisdiction`). | Add per-state snapshots if more states are wanted. |
| Texas lease tax model not checked | Lease `tax_rate` is INDETERMINATE(`not_applicable_lease_tax_model`). | None planned. |
| Doc-fee taxability not checked | The Comptroller treats a separately stated doc fee as outside taxable total consideration; `doc_fee_taxable` is not compared. | Needs a new outcome field and a contract decision. |
| OCCC filings cannot be verified | A Texas doc fee above $225 is INDETERMINATE(`requires_regulator_filing`), never REFUTED. | None; filings are not available to VerdictKit. |
| Snapshot is a point-in-time copy | Retrieved 2026-11-24; later rule changes are not tracked. | Re-fetch and re-hash before relying on it. |
| 7 TAC §84.205 rule text not retrieved from the Texas Secretary of State | The $225 rule rests on OCCC Bulletin B16-5 and the OCCC rules page. | Retrieve and hash the rule text. |
| Bundles are unsigned | Authenticity is NOT_ESTABLISHED by design. | Add signing if provenance is required. |
| No authentication outside judge mode; in-process rate limiting; single-process SQLite custody store | Not suitable for multi-tenant or horizontally scaled deployment. | Add auth, shared rate limiting and a production datastore before public multi-user use. |
| Server-side replay in enforced mode restores uploaded evidence into the shared, write-once store | Storage grows with uploads (bounded per request by size limits and rate limiting). | Add retention/quota for replayed evidence. |
| Kiro execution evidence | None recorded (see `docs/KIRO_USAGE.md`). | Run remaining work through Kiro if required. |
