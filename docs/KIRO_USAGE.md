# How Kiro is used (fill in as you go — this file becomes the submission write-up)

## Process (decision B4)
1. Open the repo in Kiro. Steering in `.kiro/steering/` loads automatically
   (`product`, `tech`, `structure`, `verdict-integrity` always; `money-math`, `testing`
   by file match).
2. For each feature (`verdictkit-core`, `reel-autopsy`, `quote-autopsy`) start a Kiro
   spec session and give it the reviewer draft in `.kiro/specs/<feature>/` as the brief.
   Let Kiro run its requirements analysis (it may flag contradictions — record them here),
   then design, then tasks. Keep Kiro's versions as the official spec files; move the
   reviewer drafts to `docs/reviewer-inputs/` before the first Kiro commit.
3. Use Kiro's correctness/property-based-testing flow to generate package-level
   property tests from the design's properties P1–P17. `tests/contract/` stays as the
   independent acceptance contract; do not edit it to make code pass.
4. Execute tasks through Kiro. The `PostFileSave` command hooks in `.kiro/hooks/` run the
   matching contract tests and the LLM fence after the agent edits files. File hooks fire
   on agent edits only, not manual saves, so CI is the real gate.
5. Register the VerdictKit MCP server (`.kiro/settings/mcp.json`) once `mcp_server.py`
   exists; use it to replay fixture bundles from inside Kiro.

## Evidence log (record real items only)
| Date | Kiro feature | What happened | Commit |
|---|---|---|---|
| | Spec requirements analysis | | |
| | Property-based test caught a bug | | |
| | Hook blocked a regression | | |
| | Steering prevented a float/LLM import | | |
| | MCP replay used in development | | |

## Honest attribution
Architecture, interface stubs and the contract tests were drafted with reviewer AIs
(Claude, ChatGPT) and Muse before implementation; specs were then run through Kiro's spec
workflow and the implementation was produced through Kiro task execution.
