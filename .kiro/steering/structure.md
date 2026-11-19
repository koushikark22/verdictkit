---
inclusion: always
---
# Repository structure

- `core/src/verdictkit/` — the skeleton. No domain logic. Modules: `canonical`, `model`,
  `plugin`, `sweep`, `pipeline`, `bundle`, `envprint`, `mcp_server`, packages `custody/`,
  `examiner/`, `evidence/`, `api/`.
- `core/examples/stub_claimtype/` — third-domain reuse proof; must run with zero core edits.
- `apps/reel-autopsy/src/reel_autopsy/` and `apps/quote-autopsy/src/quote_autopsy/` — claim
  types, evaluators, adapters, diagnostics. `web/` holds each UI.
- `tests/contract/` — reviewer acceptance contract. Do not weaken these tests to make code
  pass; change the code or raise a design change.
- `.kiro/specs/<feature>/` — requirements, design, tasks. Keep task checkboxes current.
- `docs/` — ARCHITECTURE.md (decision log B1–B8), KIRO_USAGE.md, reviewer inputs.

Interfaces in `core/src/verdictkit/**` and `apps/*/src/**` are fixed by the design. Implement
bodies; do not change signatures without updating the design document first.
