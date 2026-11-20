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
| No official state rules snapshot (decision B7) | Quote tax-rate and doc-fee checks stay INDETERMINATE. | Choose the state, snapshot official sources with hashes. |
| Bundles are unsigned | Authenticity is NOT_ESTABLISHED by design. | Add signing if provenance is required. |
| No authentication outside judge mode; in-process rate limiting; single-process SQLite custody store | Not suitable for multi-tenant or horizontally scaled deployment. | Add auth, shared rate limiting and a production datastore before public multi-user use. |
| Server-side replay in enforced mode restores uploaded evidence into the shared, write-once store | Storage grows with uploads (bounded per request by size limits and rate limiting). | Add retention/quota for replayed evidence. |
| Kiro execution evidence | None recorded (see `docs/KIRO_USAGE.md`). | Run remaining work through Kiro if required. |
