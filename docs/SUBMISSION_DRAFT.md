# VerdictKit — public submission draft (not yet submitted)

**Draft status:** This is prepared wording. **Do not submit until a genuine Kiro usage record and a public demonstration video exist.** Fill only placeholders with verified facts.

## Project title
VerdictKit — The Claim Autopsy Engine

## Category
Skeleton Crew (verify category choice on submission form)

## Short pitch
One forensic verification core, two applications. VerdictKit seals an asserted answer, evaluates permitted evidence without letting the examiner see that answer, then produces a reproducible verdict and portable replay bundle.

## What it does
Claims can bias evaluations when the alleged outcome is visible to the evaluator. VerdictKit makes that boundary explicit. A custody pipeline canonicalizes the claim, commits to the asserted outcome, and sends only blinded inputs to a separate examiner. The examiner evaluates a bounded grid of assumptions against eligible evidence. Custody then reveals the sealed outcome, compares it with independent findings, and records a deterministic verdict with an audit-friendly bundle.

The same core powers two distinctly packaged applications:

- **Quote Autopsy** checks internally consistent vehicle purchase and lease worksheets, explores missing assumptions, and displays post-verdict diagnostics. External tax-rate and doc-fee checks cover Texas finance worksheets only, against a hash-pinned snapshot of official Texas sources; for other states it does **not** claim tax-rate or fee-law conclusions.
- **Reel Autopsy** tests mechanically specified trading-performance assertions over clearly labelled synthetic data. It renders an illustrative equity chart. Real market-performance claims remain blocked until authorized licensed evidence is available.

## Technical implementation
The Python 3.12 core uses canonical JSON, SHA-256 commitments, a stateful custody ledger, AES-GCM vault storage, typed verdict models, bounded property-based sensitivity sweeps, deterministic zip bundles, offline replay, and an examiner isolated as a distinct Linux OS user behind an authenticated UNIX socket. HTTP API contract 1.1.0 is implemented with FastAPI; both front ends are React/Vite applications using the real API. An MCP server exposes controlled verification and explanation tools.

Reproducibility is tested on GitHub Actions, including Docker enforced isolation, judge-mode HTTP lifecycle, November acceptance checks, and Playwright browser E2E. Passing tests support this demonstration, not production-grade multi-tenant security.

## Why it matters
A single framework handles disputes in which the claim is easy to state but hard to verify without hindsight bias. By separating answer custody from evaluation and recording exactly how a verdict was derived, reviewers can audit failures, rerun cases, and understand evidence or assumption limitations instead of accepting a persuasive-looking result.

## How Kiro was used — **DO NOT COMPLETE UNTIL VERIFIED**
The repository currently contains Kiro steering files, three specs, hooks, and MCP configuration. Those artifacts were prepared and tested, but `docs/KIRO_USAGE.md` records no authenticated Kiro session or tool execution. **Do not state that Kiro implemented the application until there is real evidence.**

After running Kiro, replace this section with a factual write-up:
- Kiro environment/version and workflow actually used: [verified]
- Spec/task implemented in Kiro: [actual task ID and commit]
- Steering effects observed: [actual evidence]
- Hook execution inside Kiro: [actual command/output or explicitly not used]
- MCP calls inside Kiro: [actual call/output or explicitly not used]
- What Kiro changed and tests that ran: [commit and CI URL]
- Other contributors and AI tools: code history also includes Claude sessions; attribute them truthfully.

## Demo video
Public YouTube URL: [REQUIRED — upload recording, under 3:00]
Include actual Quote and synthetic Reel UI runs, actual enforced container gate, offline replay, and a real Kiro interaction only if captured.

## Links
- GitHub: https://github.com/koushikark22/verdictkit
- Judge reproducibility: https://github.com/koushikark22/verdictkit/blob/master/docs/JUDGE_DEMO.md
- Traceability: https://github.com/koushikark22/verdictkit/blob/master/docs/TRACEABILITY.md
- Post-merge CI: https://github.com/koushikark22/verdictkit/actions/runs/44816981661
- API CI: https://github.com/koushikark22/verdictkit/actions/runs/44816981688
- Live demo URL: [not currently asserted; use reproducible Docker build or provide a verified hosted link]

## Third-party and safety disclosure
The synthetic market fixture is not exchange market data or proof of real returns. Real OHLCV rights are unresolved (B1). External tax/fee verification covers Texas only (B7): a point-in-time snapshot retrieved 2026-11-24 that does not track later rule changes, no lease tax check, no doc-fee taxability check, and OCCC filings for fees above $225 cannot be verified. The app is a demonstration; bundles are unsigned, and deployment beyond judge mode lacks production access control and shared state.

## Pre-submit checklist
- [ ] Capture authentic Kiro execution evidence and accurately update `docs/KIRO_USAGE.md`.
- [ ] Verify that work is eligible under the required October 30–December 4, 2026 build window, and disclose any pre-existing components.
- [ ] Record and publish a sub-3-minute YouTube video; put the link here and in Devpost.
- [ ] Confirm a free, functional judge test route (Docker instructions or a verified publicly available deployment).
- [ ] Specify Skeleton Crew and any optional bonus categories only if qualified.
- [ ] Submit the Devpost form before 2026-12-04 14:00 Pacific, and retain the confirmation.
