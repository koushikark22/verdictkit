# Kiro usage — evidence record

This file records only verifiable facts. It must not contain reconstructed or invented
Kiro sessions, timestamps or screenshots.

## Kiro artifacts committed in the repository

| Artifact | Path | Verified state (2026-11-19) |
|---|---|---|
| Feature specs (requirements, design, tasks) | `.kiro/specs/{verdictkit-core,reel-autopsy,quote-autopsy}/` | Present. Task checkboxes updated to match passing tests; see `docs/TRACEABILITY.md`. |
| Steering | `.kiro/steering/*.md` (6 files) | Present; rules (Decimal-only, LLM fence, fail-closed) are enforced by tests. |
| Agent hooks | `.kiro/hooks/{core,app}-contract-tests.json`, `llm-fence.json` | Present. Each hook's command was executed by hand outside Kiro and passes: core contract 236 passed; reel 13 passed; quote 8 passed; LLM fence 55 passed. |
| MCP registration | `.kiro/settings/mcp.json` → `python -m verdictkit.mcp_server` | The server now exists and was exercised over stdio with the MCP SDK client (4 tools listed, `list_claim_types` called). Not exercised from inside Kiro. |

## Evidence log (real items only)

| Date | Kiro feature | What happened | Evidence |
|---|---|---|---|
| — | — | No Kiro session transcript, Kiro-attributed commit or hook-run log exists in this repository's history. | `git log` authors: the repository owner, prior Claude sessions, `github-actions[bot]`. |

## Integration pass of 2026-11-19 (not Kiro)

The consolidation and completion pass (HTTP run/outcome/bundle/replay workflow, MCP
server, quote rules loader and diagnostics, pasted-text intake, bundle hardening, CI
gates) was performed with **Claude Code**, not with Kiro. Kiro was not available in that
environment, so no Kiro spec, task-execution or property-generation run took place, and
none is claimed. The `.kiro` specs were used as the requirements source and their task
status was updated from test results.

## Implementation pass of 2026-11-20 (not Kiro)

Synthetic demo fixtures, the Reel evaluator on evidence, quote sweeps and the two
React/Vite UIs were implemented with **Claude Code**, not Kiro. No Kiro spec,
task-execution, hook or property-generation run took place and none is claimed. The
`.kiro` task checkboxes were updated from passing tests; `docs/TRACEABILITY.md` lists
the evidence for each.

## Open item

To produce genuine Kiro evidence, open the repository in Kiro, run the remaining open
tasks (quote taxability/rounding sweeps, reel evaluator once B1 is resolved, UIs) through
Kiro's spec workflow, and record each run here with its commit SHA.

## Honest attribution

Architecture, interface stubs and the contract tests were drafted with reviewer AIs
(Claude, ChatGPT) and Muse before implementation. Implementation commits are by the
repository owner and by Claude sessions as shown in `git log`.

## B7 Texas rules snapshot (2026-11-24, partly Kiro)
Reviewer AIs (Claude, ChatGPT) wrote `docs/B7_TEXAS_SPEC.md` and `docs/KIRO_B7_PROMPT.md`; the implementation below is what was run in Kiro.
* The Kiro orchestrator ran in spec task-execution mode and dispatched `spec-task-execution` sub-agents for quote tasks 4.1 and 5.1.
* First attempt: the two spec documents were not in this checkout, so the orchestrator improvised a spec and produced commit `7d33b66` (`doc_fee_cap: null`, with hashes of identical JavaScript app shells). The owner rejected it. It is kept on branch `backup/b7-incorrect-7d33b66` and reverted in `7029dbc`.
* The spec documents were then copied in from the owner's other checkout (`KIROWEEN\verdictkit`). Task 4.1 (commits `3a11a86`, `bb78aad`) fetched and hashed four official sources on 2026-11-24 UTC. No Kiro hook output was observed in task 4.1.
* Task 5.1 (sub-agent): commits `779bdfd` (adapter, external findings, and a one-line MCP examiner evidence-root fix) and `4effb3a` (14 acceptance tests; `test_external_only_claim_is_indeterminate` moved to CA; `test_quote_sweeps.py` helper gets an evidence root). No hook output was observed.
* MCP check: the `verdictkit` MCP tools were not exposed to the sub-agent, so no Kiro MCP tool call was made. As a labelled fallback outside Kiro's MCP integration, a throwaway Python stdio client (not committed) started `python -m verdictkit.mcp_server` with `VK_MCP_READONLY=1` and called `list_claim_types` and `verify_claim`. Doc fee 150.00 gave `tax_rate` SUPPORTED and `doc_fee_cap` SUPPORTED; doc fee 499.00 gave `doc_fee_cap` INDETERMINATE (`requires_regulator_filing`) and `tax_rate` SUPPORTED. Raw responses were saved to `%TEMP%\vk-b7-mcp\`.
* Not run: browser E2E (`scripts/ui_e2e.sh`, no `uv` or `node` inside the available WSL bash) and the Docker gate (`docker` is not installed).