---
inclusion: always
---
# Product: VerdictKit — The Claim Autopsy Engine

VerdictKit is a reusable forensic verification framework.
It freezes a claim into a canonical spec, seals the claimed outcome away from the evaluator,
evaluates blind on policy-checked evidence across a bounded assumption grid, and emits a
reproducible verdict bundle.

Two applications are built on the same core:
- **Reel Autopsy** (`apps/reel-autopsy`) — mechanical trading-strategy performance claims.
- **Quote Autopsy** (`apps/quote-autopsy`) — vehicle finance and lease worksheets.

Product promises we must never overstate:
- Not every claim is verifiable; INDETERMINATE and CONDITIONAL are first-class answers.
- Internal arithmetic contradictions and external-evidence refutations are different kinds
  of finding and are always labelled separately.
- Reproducibility is claimed for a pinned environment.
- Blinding is enforced by OS-user separation + encryption + type partition, not by hashes.

Theme: forensic morgue. Claim = subject on the table; finding = cause of death; ledger =
chain of custody; bundle = coroner's report. Every visual must reflect real app state.
