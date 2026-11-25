# Historical evidence reconciliation

Date of reconciliation: 2026-11-24. Method: read-only inspection of two directories outside this repository. No file in them was modified, and no raw log, transcript or archive was copied here. Only derived values are recorded below.

Sources (outside the repository):

- `%USERPROFILE%\Desktop\KIROWEEN\submission-evidence` (audit report `KIRO_FINAL_AUDIT.md`, `kiro-final/`, probe scripts)
- `%USERPROFILE%\Desktop\KIROWEEN\KIRO_LOG_EXPORT` (`sessions/`, `logs/`, `verification/`, `SHA256_MANIFEST.csv`)

Recomputation was done by parsing the `payload.type` and field structure of `sessions/**/*.jsonl` and counting. Message content was not printed.

## Reconciliation records

| ID | Claim | Recomputed value | Status | How recomputed |
|---|---|---|---|---|
| H1 | 92.9518 credits consumed | 92.95176173134327494 (sum of `usage` over 14 `usage_summary` events, all with `unit` = `credit`) | CONFIRMED | Sum of `promptTurnSummaries[].usage` in `usage_summary` payloads across all session and sub-execution files |
| H2 | 318 recorded request identifiers | 318 unique values in `usage_summary.requestIds` | CONFIRMED | Union of `requestIds` across 14 events |
| H3 | 417 unique tool calls | 417 unique `toolCallId` values in `tool_call` payloads (main sessions and sub-executions) | CONFIRMED | Distinct `toolCallId` |
| H4 | Four `spec-task-execution` sub-agent runs | 4 `sub_agent_start` and 4 `sub_agent_complete` events, all with `subAgentName` = `spec-task-execution` | CONFIRMED | Count of events |
| H5 | Six sessions with conversation transcripts | 6 session directories contain `messages.jsonl`; 3 further sessions have only `session.json` | CONFIRMED | File listing |
| H6 | All four VerdictKit MCP tools invoked from inside Kiro | 23 MCP `tool_call` events: `verify_claim` 14, `list_claim_types` 4, `explain_verdict` 3, `replay_bundle` 2. Each of the four had at least one result with `success=true` | CONFIRMED | Counted `args.tool_id` of `tool_call` events and joined to `tool_result` by `toolCallId` |
| H7 | All four registered claim types exercised through Kiro MCP | `verify_claim` arguments name `example.receipt.v1` (4), `quote.finance.v1` (8), `quote.lease.v1` (1), `reel.mechanical.v1` (1) | CONFIRMED_WITH_CORRECTION | "Exercised" means submitted. Seven `verify_claim` results contained `SchemaError`, and the audit attributes them to finance claims that lost empty arrays plus two malformed probes. A per-type tally of successful verdicts was not recomputed here (UNVERIFIED). The Reel claim returned `INDETERMINATE (evidence_unavailable)`, which is correct fail-closed behaviour with the network disabled. |
| H8 | Automatic agent-hook execution unverified | Kiro log shows `hooks.reload.loaded {"read":4,"registered":4}` (16 occurrences) and `hooks.v2.executionDisabledUntrustedWorkspace` (4 occurrences). No hook execution event appears in the Kiro logs (0 matches in 3 other log types). The session files contain 0 hook-typed events. `verification/hook-execution/README.txt` says `PENDING MANUAL IDE ACTION`. | CONFIRMED_WITH_CORRECTION | Corrects the earlier statement that no log shows hooks being loaded: Kiro did load and register all four. It also adds a likely cause of non-execution, which is that execution was disabled for an untrusted workspace. Whether the trust state was the only cause is UNVERIFIED. |

## Disagreements between historical documents

| Topic | Earlier statement (`KIRO_FINAL_AUDIT.md`, section 6) | Later statement (`FINAL_KIRO_VERIFICATION.md`) | Reconciled |
|---|---|---|---|
| Finance `SchemaError` through Kiro | Most likely cause is that boolean values were not delivered as JSON booleans | Refuted. Booleans arrive intact. Kiro's tool-call path removes empty arrays and objects. Finance params require `addons`, `gov_fees` and `rebates`, so removing them gives `SchemaError`. | The later statement is better supported (controlled probes P1 to P6, a stdio control probe). Use it. The component that removes empty containers is not identified (UNVERIFIED). |
| Hook `timeout` and `enabled` keys | Called undocumented | Called documented | Later statement used. The hook files already contain both keys. |
| Hook trigger wording | `PostFileSave` fires when "a user saves a code file" | The IDE trigger table says "saved/modified by the agent" | A manual editor save is not the documented trigger. Use agent edits to test. |
| Windows `0o777 != 0o700` failure | Windows-only POSIX permission limitation | Passes in the Linux image `verdictkit:submission` | Consistent. This phase re-observed the failure on Windows (see baseline report). |

## Corrections to the frozen documentation

The frozen `docs/KIRO_USAGE.md` states that no Kiro MCP call and no hook output were observed. The historical record shows 23 MCP calls from Kiro and 4 hooks registered. Per Requirement 15.8, the frozen file was not edited. This file is the correction record.

## Items this reconciliation did not establish

- Which Kiro component removes empty arrays and objects from tool arguments (no Kiro log records the forwarded payload).
- Whether any hook has ever fired. The export contains no execution event.
- Per-claim-type successful verdict counts through Kiro.
- Isolation `ENFORCED` through Kiro MCP. Every MCP run in the record used the in-process examiner (`UNENFORCED`).
- The 92.9518-credit figure covers six sessions and four sub-executions in the export. Its attribution to individual features or tracks is not available and is not estimated.

## Credit record for this phase

Credits consumed in this phase's own sessions: `NOT_AVAILABLE`. The agent has no access to a Kiro usage record for the current session. The historical total above belongs to the earlier work and is kept separate (Requirement 16.4).