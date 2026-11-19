---
inclusion: always
---
# Verdict integrity rules (non-negotiable)

1. No `float` anywhere in claims, evidence parsing, evaluators, comparators or findings.
   Parse numbers from strings into `Decimal`; compute inside `decimal.localcontext`.
2. Evaluators (`examine`) never receive claimed outcomes. Never add an outcome field to
   `BlindedTask`, and never pass `FrozenClaim.outcomes`-like data to the Examiner.
3. No LLM client imports (`openai`, `anthropic`, `boto3` bedrock clients, `langchain`,
   `litellm`, etc.) in `verdictkit.custody`, `verdictkit.examiner`, `verdictkit.evidence`,
   `verdictkit.sweep`, or any app evaluator module.
4. Fail closed: an error, policy violation, missing evidence or missing assumption may make
   a finding INDETERMINATE. It may never make it SUPPORTED, CONSISTENT or WITHIN_BOUND.
5. Never subsample an over-cap assumption grid; reject it.
6. Never use wall-clock time as an evaluator or comparator input. Inject a clock.
7. Post-reveal diagnostics must not change finding statuses or `verdict_hash`.
8. Do not invent financial data, results or test counts in fixtures, docs or UI copy.
   Demo fixtures are computed by the engine from real evidence or are explicitly labelled
   constructed worksheets.
9. `IMPOSSIBLE` requires claimant- or user-declared mechanics (decision B6).
10. Wording: "verified at N grid points", never "for all values".
