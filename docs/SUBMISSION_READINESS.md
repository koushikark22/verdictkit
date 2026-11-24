# VerdictKit — submission readiness and evidence checklist

Status: **draft preparation**, not a completed submission. Last reviewed 2026-11-20.

Official requirements: https://kiroween.devpost.com/rules
Submission deadline: 2026-12-04 14:00 Pacific / 16:00 Central.

## Category and positioning

**Skeleton Crew** is the intended category to verify on the submission form: one reusable, forensic claim-verification core with **two distinct application folders** (`apps/reel-autopsy` and `apps/quote-autopsy`). Do not claim a live trading-data integration or external tax-rate verification.

**One-sentence description:** VerdictKit verifies assertions without first exposing the asserted answer to its examiner: it freezes inputs, seals outcomes, evaluates policy-permitted evidence in an isolated process, then issues a deterministic verdict bundle that can be replayed offline.

## Eligibility and completeness matrix

| Requirement | Current evidence | Action |
|---|---|---|
| Public GitHub source | https://github.com/koushikark22/verdictkit | Present |
| Open-source license | `LICENSE` (MIT) | Present |
| Root `.kiro` directory | Steering, three specs, hooks, MCP config | Present; do not gitignore |
| Two separate application folders | `apps/reel-autopsy`, `apps/quote-autopsy` | Present |
| Working application | CI gates + browser E2E against live API | Verified in CI; provide judge instructions and demo |
| Kiro used to build project | `docs/KIRO_USAGE.md` explicitly records no genuine Kiro session | **Blocking: run real Kiro task(s), capture records** |
| Public application/test access | GitHub Docker build and local web UI instructions | Ensure judges can run freely without private keys, restricted datasets, or paid services |
| Public YouTube demonstration, <3 minutes | Not provided in this repository | **Blocking: record, upload, add URL** |
| Accurate Kiro write-up | Existing configurations documented; no actual invocation evidence | **Blocking: complete only after real Kiro use** |
| Submission form and category | Not verified submitted | **Blocking: submit on Devpost by deadline** |
| New work during submission period | Commit history must be audited for 2026-10-30 to 2026-12-04 eligibility; explain pre-existing material | Review provenance carefully and disclose reuse |
| Third-party data rights | Synthetic Reel fixtures only; no licensed live feed | Do not claim external data or distribute restricted datasets |

## Current release boundaries

- Core/Quote/Reel functional CI evidence is in `docs/TRACEABILITY.md`, `docs/RELEASE_READINESS.md`, and GitHub Actions.
- Quote Autopsy validates document-internal arithmetic and assumption sweeps. External checks cover Texas only (decision B7): the stated tax rate and the documentary fee against a hash-pinned snapshot of Texas Comptroller and OCCC publications. A Texas doc fee above $225 is never refuted (INDETERMINATE, `requires_regulator_filing`); lease tax rate is not checked; other states are INDETERMINATE.
- Reel Autopsy runs on clearly labelled synthetic historical-looking observations. Live financial-performance claims are intentionally BLOCKED pending a documented rights basis and real source adapter (B1).
- Bundles are deterministic but not cryptographically signed. Do not assert authenticated origin or production-grade chain of custody.
- The demo is not a production SaaS: no general-user authentication, no distributed rate limiter, and SQLite is single-process.

## Three-minute video outline (record actual UI footage)

| Timeline | What to show | Accurate narration point |
|---|---|---|
| 0:00–0:20 | Problem and VerdictKit overview | Claim outcomes remain sealed during examination |
| 0:20–0:55 | Quote Autopsy form, example, submit, verdict | Show worksheet computation and bounded assumptions |
| 0:55–1:25 | Reel Autopsy synthetic scenario, illustrative equity chart | Clearly state synthetic, not verified live returns |
| 1:25–2:05 | Enforced judge-mode gate and case in container | Actual separate OS users, authenticated examiner, ENFORCED marker |
| 2:05–2:35 | Download/replay bundle, comparison hash | Replay checks integrity and reproduction; avoid implying signatures |
| 2:35–2:55 | Kiro IDE/CLI session showing a genuine implemented task, hook or MCP call | Only show authentic Kiro interaction and verifiable commit |
| 2:55–2:59 | Final URL / takeaway | Two apps, one reusable core |

Use a publicly visible YouTube video (under three minutes); no unlicensed music, images or third-party marks.

## Kiro completion procedure (must actually run in Kiro)

1. Open the **current master** repository in Kiro IDE or Kiro CLI; read `.kiro/steering` and `.kiro/specs`.
2. Choose one *new, bounded, demonstrable* improvement. Suggested: add a documentation-consistency validation test that checks the public README's claims against the fixed `docs/RELEASE_READINESS.md` boundaries, or add better negative tests for malformed worksheet input. Avoid changing security invariants merely to generate proof.
3. Ask Kiro to develop a spec delta, modify code/tests, and run the relevant suite. Exercise a real hook (e.g. `.kiro/hooks/llm-fence.json`) if supported by the installed Kiro environment; independently capture hook output.
4. Capture a real Kiro conversation/session export or screenshots, task ID, timestamp, command output, changed files, and resulting commit SHA. Never reconstruct or fabricate Kiro logs.
5. Put only verifiable evidence in `docs/KIRO_USAGE.md`, including whether a hook/MCP call was actually invoked **inside** Kiro. Keep original Claude provenance for prior work.
6. Push a PR; check CI on its exact SHA and merge only when green. Update the demo and submission narrative to match reality.

### Suggested Kiro prompt to paste into Kiro

> Read the repository's .kiro steering and VerdictKit core requirements. Make a small, verifiable improvement to the test coverage for malformed Quote worksheet inputs without changing the API 1.1.0 contract or the ENFORCED isolation promise. First propose the spec delta and exact acceptance tests, then implement the change with tests. Run the relevant hooks and tests, report actual command output, and record the exact files changed and commit SHA. Do not invent execution evidence or change any historical attribution.

## Judge reproducibility

Use `docs/JUDGE_DEMO.md`. All container checks should run with `--network none`. Judges should not need licensed market data, third-party credentials, or real financial inputs.

## Remaining work ownership

- **Owner action required:** real Kiro execution, video recording and YouTube upload, submission form, licensing decision B1 if live market verification is desired.
- **Optional production track:** bundle signing, multi-tenant auth, shared rate limits/datastore, storage retention and quotas. This track is not a prerequisite to the synthetic demonstration.
