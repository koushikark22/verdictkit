# Kiro prompt — B7 Texas rules snapshot

Prepared by Claude (Claude Code), 2026-11-23, for Koushik to run **inside Kiro**.
Preparing this prompt is Claude's work. The implementation it asks for is Kiro's work,
and should be recorded in `docs/KIRO_USAGE.md` only after it really happens.

## Before you paste it

1. Open `C:\Users\koush\Desktop\KIROWEEN\verdictkit` in Kiro. Then run
   `git checkout master && git pull && git checkout -b feature/b7-texas-rules`.
2. Make sure `docs/B7_TEXAS_SPEC.md` is in the working tree. It is on the local branch
   `docs/b7-texas-handoff`; apply the patch or copy the file in.
3. Start screen recording if you want video evidence. The Kiro steps worth capturing are
   the spec update, the agent's file edits, the `quote-contract-tests-on-agent-save` hook
   firing, and the MCP `verify_claim` call in step 6.

## Prompt (paste everything below into Kiro chat, Spec mode)

---

Implement decision B7 (Texas) for Quote Autopsy, following `docs/B7_TEXAS_SPEC.md` exactly.
Read these before writing code:
`.kiro/steering/verdict-integrity.md`, `.kiro/steering/money-math.md`,
`.kiro/specs/quote-autopsy/requirements.md` (Requirement 5), `.kiro/specs/quote-autopsy/design.md`,
`.kiro/specs/quote-autopsy/tasks.md` (tasks 4 and 5),
`apps/quote-autopsy/src/quote_autopsy/rules.py`, `apps/quote-autopsy/src/quote_autopsy/claim_type.py`,
`apps/reel-autopsy/src/reel_autopsy/sources/synthetic.py` (the adapter pattern to copy),
`core/src/verdictkit/evidence/broker.py`, `core/src/verdictkit/api/evidence_boundary.py`,
`tests/integration/test_quote_rules_diagnostics.py`, `tests/api/test_http_run_lifecycle.py`.

Work in this order and stop after each step that says STOP:

1. **Spec first.** Update `.kiro/specs/quote-autopsy/requirements.md` Requirement 5 to match
   spec sections 4 and 6:
   * the doc-fee rule kinds;
   * Texas "presumed reasonable amount" above $225 → INDETERMINATE(`requires_regulator_filing`), never REFUTED;
   * a degenerate rate range → SUPPORTED/REFUTED;
   * lease in TX → `not_applicable_lease_tax_model`.

   Update `design.md` and `tasks.md` to match. STOP and show me the diff.

2. **Snapshot.** Fetch each official page in spec section 2 yourself. Show me the URL, the
   HTTP status and the SHA-256 of the bytes you received, and quote the sentence on that
   page that supports each value. If any page is unreachable, or disagrees with 6.25%, no
   local motor-vehicle tax, or the $225 presumed-reasonable amount, STOP and tell me. Do not
   substitute values. Also check `https://occc.texas.gov/publications/rules` for any adopted
   amendment to 7 TAC §84.205 that changes $225. Then write `TX.json` (canonical JSON) and
   `MANIFEST.json` under `apps/quote-autopsy/src/quote_autopsy/rules/`, with
   `retrieved_at` set to today's UTC date. STOP and show me both files.

3. **Loader.** Change `rules.py` to the `doc_fee` object schema (spec section 4), and update
   `tests/integration/test_quote_rules_diagnostics.py` to match. Keep every existing hash,
   manifest and canonical check. Run
   `uv run pytest tests/integration/test_quote_rules_diagnostics.py -q`.

4. **Adapter and claim type.** Add `TexasRulesAdapter` (spec section 5), then wire
   `FinanceClaimType` (`evidence_requests`, `evidence_policy`, `evidence_adapters`, `examine`,
   `findings`) and the lease TX reason (spec section 6). The examiner must never see outcomes.
   No floats, no network, no wall-clock time.

5. **Tests.** Write all 14 acceptance tests in spec section 7 in
   `tests/integration/test_quote_b7_texas.py`. Make the changes to existing tests listed in
   spec section 8, and nothing else. Explain each change to an existing test in one line.
   Then run:
   ```
   uv run --no-sync ruff check .
   uv run --no-sync pytest -q -m "not isolation"
   npm run typecheck; npm test; npm run build
   ```
   On Windows, run `bash scripts/ui_e2e.sh` from Git Bash or WSL. Report the real pass and
   fail counts. Fix failures in the implementation, not by weakening tests.

6. **MCP check from inside Kiro.** Using the `verdictkit` MCP server configured in
   `.kiro/settings/mcp.json`, call `list_claim_types`, then `verify_claim` with this claim.
   Show me the raw tool results.
   ```json
   {"claim_type":"quote.finance.v1","schema_version":1,
    "params":{"selling_price":"30000.00","addons":[],"doc_fee":"150.00","doc_fee_taxable":false,
              "gov_fees":[],"rebates":[],"trade_allowance":"0.00","trade_payoff":"0.00",
              "trade_tax_credit":true,"cash_down":"5000.00","stated_tax_rate_pct":"6.25",
              "apr_pct":"6.00","term_months":60,"jurisdiction":{"state":"TX"}},
    "outcomes":{"tax_rate":"6.25","doc_fee_cap":"150.00"},"assumptions":{}}
   ```
   Expected: `tax_rate` SUPPORTED and `doc_fee_cap` SUPPORTED. Then repeat with
   `"doc_fee":"499.00"`. Expected: `doc_fee_cap` INDETERMINATE (`requires_regulator_filing`), not REFUTED.

7. **Docs.**
   * Update `docs/TRACEABILITY.md` rows 5.1 and 5.2–5.5, the B7 row in
     `docs/RELEASE_READINESS.md`, and the Texas limitations: lease tax model, doc-fee
     taxability, and OCCC filings that can't be verified.
   * Append to `docs/KIRO_USAGE.md` only what actually happened in this Kiro session: spec
     edits, files written, hooks that fired, and the MCP calls with their results.
   * Commit in small, scoped commits. Do not push, open a PR or merge until I say so.

Constraints: do not touch branch `fix/judge-e2e-prerequisites-20261123` (PR #7). Do not
change API contract 1.1.0. Do not add hackathon references to source-code comments. Do not
claim any test result you did not run.

---

## Evidence to keep (owner checklist)

- [ ] Kiro chat transcript or export showing steps 1–7
- [ ] Screenshot or recording of the `quote-contract-tests-on-agent-save` hook running after a save
- [ ] Screenshot of the MCP tool results from step 6, inside Kiro
- [ ] The commit SHAs Kiro produced, and the CI run link for the PR
- [ ] `docs/KIRO_USAGE.md` entry matching the above
