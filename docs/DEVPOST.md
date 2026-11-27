# VerdictKit: Devpost submission text

Prepared 2026-11-27 from recorded evidence. Replaces the pre-Batch-1 wording in `SUBMISSION_DRAFT.md`, which stated contract 1.1.0 and unsigned bundles. Every figure below comes from a run listed in `docs/next-phase/EXECUTION_EVIDENCE.md`. The demo video is **not yet recorded**; see `docs/DEMO_STORYBOARD.md`.

## Title
VerdictKit: The Claim Autopsy Engine

## Tagline
Don't trust the claim. Verify the evidence. Reproduce the verdict.

## Category
Skeleton Crew (confirm the category on the submission form).

## Short description
One reusable examination framework that freezes a claim, hides the claimed answer from the examiner, recomputes it on checked evidence, and returns a signed bundle anyone can verify and replay offline. It powers a car-finance worksheet checker, a trading-claim checker and a signature verification lab, with the same trust code under all three.

## What it does
A claim is easy to state and hard to check without hindsight. VerdictKit takes the claim apart so the check cannot be nudged by the answer.

**Claim → Evidence → Deterministic examination → Verdict → Signed bundle → Independent verification → Offline replay.**

* **Quote Autopsy** recomputes a finance or lease worksheet from its itemised inputs, blind to the stated totals, and names the first line that breaks. In the demonstration a worksheet with 400.00 hidden in the amount financed comes back `CONTRADICTED`, labelled as an internal arithmetic contradiction, "not a finding about outside facts".
* **Reel Autopsy** tests a mechanical trading claim against a perfect-foresight ceiling on labelled synthetic data. A claimed +3,400% comes back `IMPOSSIBLE` (the ceiling on that data is 2,872.54), phrased as "does not say the claimant lied". An illustrative equity chart is drawn from the engine's own series.
* **Verify Lab** takes the signed bundle any examination produced and checks it five ways against trust stores the *verifier* configured: trusted signer, unknown signer, revoked signer, unsigned historical bundle, tampered bundle. Six separate results are shown (integrity, signature, signer trust, authenticity, reproducibility, isolation), then the bundle is replayed offline with `docker run --network none`.

It says plainly when it cannot decide. `INDETERMINATE`, `CONDITIONAL` and `BLOCKED` are answers, results read "verified at N grid points", and a signature is never presented as proof that the claim is true.

## Why this is a Skeleton Crew entry
The skeleton is the framework: custody, blind examiner, bounded assumption sweep, deterministic bundle, Ed25519 signing, independent verification, replay, API and MCP server. It contains no domain logic. Everything specific to a domain is a small claim type with its own evaluator.

* Two very different applications (money arithmetic with a state rule snapshot, and market-performance bounds) run on that one core. Neither re-implements custody, signing or verification.
* A third claim type (`examples/stub_claimtype`) runs through the same pipeline with **zero core edits**. That is the reuse test, and it runs in the Docker gate.
* The Verify Lab added no verification logic. It calls the same replay and authenticity code as the API, through one new engine module and one modified file, and ships a shared `ui-kit` used by all three screens.
* Trust is built once: a verifier decides whom to trust, a key inside a bundle never counts, and every application inherits that.

## How it is built
Python 3.12 core (canonical JSON, SHA-256 commitments, hash-chained ledger, AES-GCM vault, `Decimal` everywhere, no floats), FastAPI contract 1.2.0, `cryptography` for AES-GCM and Ed25519, Hypothesis and pytest, React, Vite and TypeScript, one Docker image with two OS users. The examiner runs as a different OS user behind an authenticated Unix socket (peer credentials checked) and holds no key. Blinding is OS-user separation, encryption and a type partition, not hashes. An MCP server exposes `list_claim_types`, `verify_claim`, `explain_verdict` and `replay_bundle`, limited to approved file roots.

## What has been verified
Runs of 2026-11-27, with logs kept in a private archive and summarised in the ledger:

* Python regression on Windows: 642 passed, 16 skipped, 4 deselected. Same suite inside the Linux image as the custodian user: 623 passed, 15 skipped, 6 deselected.
* Enforced-isolation gates with `--network none`: startup, isolation, signed bundles (14 checks including unknown, revoked and three tamper cases), judge-mode HTTP lifecycle (no vault key seen in 926 process samples), case and offline replay.
* Frontend: typecheck clean, 53 unit tests, production builds. Browser end-to-end against the real backend in Chrome: 105 checks passed, 0 console errors.
* `npm audit` and `pip-audit`: no known vulnerabilities. An independent security review found no blocker (`docs/SECURITY_REVIEW_BATCH3.md`).
* The same stub claim gives the same sealed verdict hash on Windows (in-process) and in the enforced Linux container; the isolation mode differs and is recorded, the verdict does not.

## How Kiro was used
Facts only; the detail and the limits are in `docs/KIRO_USAGE.md`.

* **Specs.** Three feature specs (`verdictkit-core`, `reel-autopsy`, `quote-autopsy`) and a next-phase spec (requirements, design, tasks) live in `.kiro/specs/`. The Texas rules work (quote tasks 4.1 and 5.1) was executed by Kiro's spec task runner and merged. Kiro's local task metadata (generated by the IDE, not committed) also records the execution of task 1.1 of the next-phase spec.
* **Steering.** Six steering files encode the rules the tests enforce: Decimal-only money, no LLM clients in evaluator code, fail closed, no weakened contract tests. Five were applied as included rules in the recorded sessions.
* **Hooks.** Four `PostFileSave` hooks run the contract tests and the LLM fence. In Batch 3 an agent save of a harmless `.py` file was observed starting `uv run pytest tests/contract/test_llm_fence.py -q` from Kiro's own process (ancestry recorded), and a temporary recorder in the test run reported exit status 0 with 61 of 61 passed. A save of a `.txt` file started nothing.
* **MCP.** The `verdictkit` server is registered in `.kiro/settings/mcp.json`. All four tools were called from inside Kiro on the current code with the stub claim: `list_claim_types` returned four claim types, `verify_claim` returned `CONTRADICTED` (verdict hash `547fba0c…aaa79`), and `explain_verdict` and `replay_bundle` reported integrity `VERIFIED`. The replay was `REPRODUCED` with equal original and replayed hashes and contract version 1.2.0, and the authenticity line reads "signature: UNSIGNED; signer trust: NOT_EVALUATED. This bundle is unsigned. Authenticity is not established." An earlier run had answered with contract 1.1.0 from a server that started before the signing work, and that finding is closed. Limits: the server ran in-process on a Windows host, so isolation was `UNENFORCED` (the enforced runs are the Docker gates); the claim is a constructed receipt; Kiro's log shows that the four calls succeeded but not what they returned; and the server had to be reconnected first, by a temporary toggle of its `disabled` setting whose effect cannot be told apart from a click on Reconnect. Detail: `docs/KIRO_USAGE.md` and ledger records B3F-01 to B3F-06.
* **Other tools.** Earlier implementation passes were done with Claude Code and are attributed that way. Reviewer AIs drafted the architecture and the Texas specification.

## Challenges
Keeping the examiner honestly blind (the claim, the key and the vault are separate OS identities, and a test proves each refusal); making signature results impossible to over-read (six separate answers, and a plain sentence that never says the claim is true); and refusing to invent data (synthetic and constructed samples are labelled everywhere, real Reel claims are blocked without licensed data).

## What we learned
A framework is only reusable if the trust boundary has no domain code in it. Writing the third claim type against the unchanged core was the quickest way to find where that was not true.

## What is next
A licensed market-data source for real Reel claims, more state rule snapshots for Quote, and plugin loading with an allow-list so the engine can be deployed beyond a local judge-mode demonstration.

## Try it
Needs Docker and Node.js 20+: `powershell -ExecutionPolicy Bypass -File scripts\Start-VerdictKit.ps1` (Windows) or `scripts/start-verdictkit.sh`, then open the printed URL. Guided links: `/quote/?demo=padded`, `/reel/?demo=fx_reel_impossible_sma`, `/verify?auto=1&sample=lease-consistent&scenario=tampered-bundle`. Repository: https://github.com/koushikark22/verdictkit

## Disclosures
Demonstration only, not a public service. The demonstration signing key is disposable and proves nothing about any real signer. Quote worksheets are constructed; Reel data is synthetic; external tax and fee checks cover Texas finance worksheets only, from a hash-pinned snapshot retrieved 2026-11-24. No market data is used. Public deployment is not authorised and has not been done.

## Before submitting
- [ ] Record the video (`docs/DEMO_STORYBOARD.md`), watch it through, and only then add the link here.
- [ ] Confirm build-window eligibility. All 127 commits are dated inside the window, but the first is a "Baseline" commit (2026-11-18) of an existing core, so state where that baseline came from.
- [x] Re-run the MCP calls after a Reconnect in Kiro, and update the MCP bullet above with what they return. Done 2026-11-27 (ledger B3F-04).
- [ ] Confirm the free judge test route (the Docker start script above).
