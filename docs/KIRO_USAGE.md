# Kiro usage — evidence record

This file records only verifiable facts. It must not contain reconstructed or invented
Kiro sessions, timestamps or screenshots. Each item says where its evidence lives and
who or what ran it. "Kiro" below means work the repository owner ran in the Kiro IDE;
"outside Kiro" means a command run by hand or by another tool.

## Summary

* One Kiro session has been recorded: the B7 Texas rules work (quote tasks 4.1 and
  5.1), run by the owner in Kiro's spec task-execution mode on 2026-11-23/24 (UTC).
  It produced the commits listed under "Evidence log". It was merged as squash commit
  `c399e36` (PR #8).
* All other implementation passes (2026-11-19, 2026-11-20, 2026-11-24 readiness pass)
  were done with Claude Code, not Kiro, and are listed below as such.
* No Kiro agent-hook run and no Kiro MCP tool call has been observed in any Kiro
  session. Hook commands and the MCP server have only been exercised outside Kiro. **Superseded 2026-11-27:** a hook run and four MCP tool calls have since been observed inside Kiro (see "Batch 2" and "Batch 3" at the end of this file); the sentence is kept as the record of 2026-11-24.
* Git metadata cannot by itself show which tool produced a commit: every B7 commit is
  authored and committed under the owner's identity with no tool trailer. Attribution of
  those commits to Kiro rests on the owner's session record below.

## Kiro artifacts committed in the repository

| Artifact | Path | Verified state (2026-11-24, outside Kiro) |
|---|---|---|
| Feature specs (requirements, design, tasks) | `.kiro/specs/{verdictkit-core,reel-autopsy,quote-autopsy}/` | Present. Task checkboxes match passing tests; see `docs/TRACEABILITY.md`. Quote tasks 4/4.1 and 5/5.1 were executed in Kiro (B7). |
| Steering | `.kiro/steering/*.md` (6 files) | Present; rules (Decimal-only, LLM fence, fail-closed) are enforced by tests. |
| Agent hooks | `.kiro/hooks/{core,app}-contract-tests.json`, `llm-fence.json` | Present. Each hook's command was run by hand outside Kiro on 2026-11-24: core contract 239 passed (4 isolation tests deselected); reel contract 13 passed; quote contract 8 passed; LLM fence 58 passed. Before the readiness-pass fix to `taxable_base` (below) the quote-contract command failed 1 test under the default Hypothesis profile. No hook output was observed inside Kiro. |
| MCP registration | `.kiro/settings/mcp.json` → `python -m verdictkit.mcp_server` | The server exists and has been exercised over stdio with an MCP client outside Kiro. Its tools were not exposed to the Kiro sub-agent in the B7 session, so no call has been made from inside Kiro. |

## Evidence log (real items only)

Times are commit author dates in UTC. Every commit below is reachable on GitHub from
`refs/pull/8/head` and from branch `feature/b7-texas-rules` (head `7b8b910`).

| Date (UTC) | Commit | Recorded as | What it contains |
|---|---|---|---|
| 2026-11-23 21:56 | `7d33b66` | Kiro, first attempt (rejected) | Orchestrator ran without the B7 spec documents in the checkout and improvised: `doc_fee_cap: null`, a `local_rate_max_pct` of 2.00, and three `statutes.capitol.texas.gov` source hashes that are identical because each URL served the same JavaScript app shell, not statute text. The owner rejected it. |
| 2026-11-24 01:45 | `7029dbc` | Owner (revert) | `git revert` of `7d33b66`. |
| 2026-11-24 01:52 | `3a11a86` | Task 4.1 (owner's record) | `docs/B7_TEXAS_SPEC.md` and `docs/KIRO_B7_PROMPT.md` (written by reviewer AIs and copied in from the owner's other checkout) plus the quote spec updates for B7 in `.kiro/specs/quote-autopsy/`. |
| 2026-11-24 01:59 | `bb78aad` | Kiro task 4.1 | Fetched and hashed four official Texas sources (three Comptroller pages, one OCCC bulletin PDF); `rules/TX.json`, `rules/MANIFEST.json`, `doc_fee` rule-object loader schema, `.gitattributes` rule keeping the snapshot bytes unconverted. |
| 2026-11-24 02:12 | `779bdfd` | Kiro task 5.1 (sub-agent) | `TexasRulesAdapter`, finance external findings, Texas lease `not_applicable_lease_tax_model`, and a one-line in-process MCP examiner evidence-root fix. |
| 2026-11-24 02:12 | `4effb3a` | Kiro task 5.1 (sub-agent) | 14 B7 acceptance tests; `test_external_only_claim_is_indeterminate` moved to CA; `test_quote_sweeps.py` helper gets an evidence root. |
| 2026-11-24 02:13 | `596299a` | Not recorded as Kiro | Traceability, readiness limitations and this file's B7 section. |
| 2026-11-24 02:32 | `7b8b910` | Not recorded as Kiro | PR #8 review fix: socket-mode MCP `verify_claim` shares `VK_EVIDENCE_DIR` with the examiner and fails closed without it; regression tests. |
| 2026-11-24 02:35 | `c399e36` | Squash merge of PR #8 | One commit on `master`. Its tree is identical to `7b8b910`'s tree (`c69c4f0`), so the squash dropped no content; the individual commits above survive only on the PR and branch refs. |

No Kiro hook output was observed in task 4.1 or task 5.1.

MCP check in the B7 session: the `verdictkit` MCP tools were not exposed to the
sub-agent, so no Kiro MCP tool call was made. As a labelled fallback outside Kiro's MCP
integration, a throwaway Python stdio client (not committed) started
`python -m verdictkit.mcp_server` with `VK_MCP_READONLY=1` and called `list_claim_types`
and `verify_claim`. Doc fee 150.00 gave `tax_rate` SUPPORTED and `doc_fee_cap`
SUPPORTED; doc fee 499.00 gave `doc_fee_cap` INDETERMINATE (`requires_regulator_filing`)
and `tax_rate` SUPPORTED. Raw responses were saved locally by the owner to
`%TEMP%\vk-b7-mcp\` and are not in the repository.

Not run in the B7 session: browser E2E (`scripts/ui_e2e.sh`; no `uv` or `node` in the
available WSL bash) and the Docker gate (`docker` not installed). Both run in CI on
every pull request (`.github/workflows/p0-integration.yml`).

### Preserving the commit history

The per-commit history exists on GitHub only through `refs/pull/8/head` (kept by GitHub
for the pull request) and branch `feature/b7-texas-rules`. Before that branch is deleted,
keep these references:

| Reference | Points at | Purpose |
|---|---|---|
| `evidence/kiro-b7-pr8-history` | `7b8b910` | Full B7 history including the Kiro commits. |
| `backup/b7-incorrect-7d33b66` | `7d33b66` | The rejected first Kiro attempt, as the earlier record stated. |

Check which of them exist with `git ls-remote origin 'refs/heads/evidence/*' 'refs/heads/backup/*'`.

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

## Readiness pass of 2026-11-24 (not Kiro)

Performed with **Claude Code**, not Kiro. Running the hook commands by hand found that
the quote-contract command failed: `taxable_base` was not floored at 0 (quote
requirement 3.1) when a trade credit exceeded the price. The derandomised CI Hypothesis
profile had not generated that case. The floor was added in `finance.py` and the case
pinned as an explicit example. The same pass made corrupt ZIP entries in an uploaded
bundle replay as UNVERIFIABLE instead of raising, pinned the synthetic Reel CSV and the
shell scripts to LF line endings (a `core.autocrlf=true` checkout broke the CSV digest
and the bash scripts), and corrected the Texas description in the Quote UI and docs.

## Open items

* Kiro agent hooks have never been observed firing inside Kiro (**as of 2026-11-24; observed since, see Batch 3**). To record one, save a
  file under a hook's matcher in a Kiro session and note the hook output with the date.
* The `verdictkit` MCP server has not been called from inside Kiro (**as of 2026-11-24; called since, see Batch 2 and Batch 3**).
* Reel tasks blocked on decision B1 (licensed market data) have not been run in Kiro.

## Honest attribution

Architecture, interface stubs and the contract tests were drafted with reviewer AIs
(Claude, ChatGPT) and Muse before implementation. Reviewer AIs (Claude, ChatGPT) wrote
`docs/B7_TEXAS_SPEC.md` and `docs/KIRO_B7_PROMPT.md`. Implementation commits are by
the repository owner (including the Kiro B7 session) and by Claude sessions, as shown in
`git log`.

## Batch 2 (2026-11-27): Kiro capabilities observed in the IDE

The full record, with numbers, is in `docs/next-phase/EXECUTION_EVIDENCE.md` ("Accelerated Batch 2", records B2-17 and B2-18). Nothing below is manufactured: each item says what was seen and what was not.

**How to repeat the MCP demonstration.** With the `verdictkit` MCP server connected, ask Kiro to call, in this order: `list_claim_types` (auto-approved), `verify_claim` with `examples/stub_claimtype/claim.json` as the claim, then `explain_verdict` (auto-approved) and `replay_bundle` with the `bundle_path` that `verify_claim` returned. Expect `CONTRADICTED`, integrity `VERIFIED` and `REPRODUCED` with equal verdict hashes. **Restart the MCP server first** (Kiro: MCP Servers panel). In Batch 2 the IDE's server processes pre-dated the Batch 1 hardening and answered with `contractVersion` 1.1.0 and "unsigned in v1" wording.

**How to repeat the hook demonstration.** `.kiro/hooks/` holds three `PostFileSave` hooks (`llm-fence`, `core-contract-tests`, `app-contract-tests`). Ask Kiro to save any `.py` file, then look for the effect, because hook output is not forwarded to the agent: in PowerShell, `Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | Where-Object CommandLine -match 'uv run pytest'` while saving, or the modification time of `.pytest_cache/v/cache/nodeids` (only runs that enable the cache write it; pass `-p no:cacheprovider` in your own runs). Batch 2 saw both the `llm-fence` and the `core-contract-tests` commands start after one save of `core/src/verdictkit/api/demo_lab.py`; whether they passed is `UNVERIFIED`. Hooks created in a session start only with the next session.

**Steering.** Five of the six steering files were applied as included rules (`money-math` was not included). **Specifications.** None created or edited; a Kiro spec workflow was not exercised. **Shared code.** One `ui-kit` serves the portal and both applications; one engine serves both applications and the demonstration lab, with one modified file (`api/server.py`) and one new module (`api/demo_lab.py`) in the engine package (corrected 2026-11-27, ledger C-010; the earlier text said "a one-file change").

## Batch 3 (2026-11-27): hooks and MCP observed again, with limits

Full record and numbers: `docs/next-phase/EXECUTION_EVIDENCE.md` ("Final Batch 3", records B3-08 to B3-11). The raw logs are in a private archive; only these summaries are published.

**MCP, before any restart.** Through Kiro's MCP client the four tools were called in order on the server as it was running: `list_claim_types` (4 claim types), `verify_claim` with `examples/stub_claimtype/claim.json` (`CONTRADICTED`, verdict hash `547fba0c67e3bcdfa7da58b914d36dc3301b7503fb1278753bbb0eb23d9aaa79`), `explain_verdict` (integrity `VERIFIED`) and `replay_bundle` (`REPRODUCED`, original and replayed hashes equal). The answers were **stale**: `contractVersion` 1.1.0 and the "bundles are unsigned in v1" wording, from a server process started 2026-11-26 00:43, before the Batch 1 commit. The bundle path sat in the same private directory name as in Batch 2, so it was the same process. The IDE's MCP log records that process connecting (`mcp.connect.ok`, 00:43:50) and nothing per call.

**MCP, restart.** Reconnecting is an action of Kiro's MCP Servers panel (it sends `_kiro/mcp/resetServer`), and an agent cannot press it. The agent ended that server's process tree (three processes; identity and parentage checked first, evidence kept) to see whether Kiro would start a fresh server by itself. It did not: the next tool call returned "Not connected", and a timestamp-only touch of `.kiro/settings/mcp.json` (content hash unchanged) changed nothing. **The server stays disconnected until someone presses Reconnect on the `verdictkit` row.** A post-restart call from inside Kiro is therefore `UNVERIFIED`. What the current code returns was checked through a fresh process and the MCP SDK client, which is not Kiro's integration: `contractVersion` 1.2.0, "signature: UNSIGNED; signer trust: NOT_EVALUATED" wording, the same verdict hash, equal original and replayed hashes, and `PATH_NOT_ALLOWED` for a repository path outside the approved roots.

**Hooks.** Agent saves of harmless `.py` files under `artifacts/` (not tracked) were made while an independent observer polled the process list. The IDE (`Kiro.exe`, the extension host, a child of the main `Kiro.exe`) started `cmd.exe /d /s /c "uv run pytest tests/contract/test_llm_fence.py -q"`, which started `uv`, `pytest` and Python, and everything had ended about 5.7 seconds later. A temporary, untracked pytest plugin inside that run (removed afterwards) wrote the exit status: **0, with 61 collected, 61 passed, 0 failed**, and its parent process id matched the observed ancestry. Two earlier saves produced records with the same arguments and result, but their ancestry was not observed. A save of a `.txt` file started nothing. Hook output is still not forwarded to the agent, which is why the recorder was needed. The `core-contract-tests` and `app-contract-tests` hooks were not instrumented in this batch, so their pass or fail inside Kiro remains `UNVERIFIED`. The IDE's agent log (`Kiro Logs.log`) records that the four hooks loaded at session start, and no hook outcome.

**Spec and steering.** No spec was created or edited. Five of the six steering files were again applied as included rules (`money-math` was not included).

**Corrections made in this file** (ledger C-010 to C-012). The Batch 2 sentence "a one-file change in the engine package" was wrong: the change was one modified file (`api/server.py`) and one new module (`api/demo_lab.py`). The dated 2026-11-24 statements that no hook run or MCP call had been observed inside Kiro are marked superseded where they stand, with their wording kept. The Batch 2 statement that the IDE's log files are empty is not supported for window 1, whose logs have content.
