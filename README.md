# VerdictKit: The Claim Autopsy Engine

> **Don't trust the claim. Verify the evidence. Reproduce the verdict.**

VerdictKit freezes a claim, seals the claimed answer away from the examiner, recomputes it blind on policy-checked evidence across a bounded assumption grid, and returns a **signed bundle that anyone can verify and replay offline**. It says plainly when a claim cannot be checked.

**One examination framework, three surfaces, no duplicated trust code.**

| Surface | What it examines | Try it |
|---|---|---|
| **Quote Autopsy** | Vehicle finance and lease worksheets. Recomputes every line, finds the first line that breaks. | `/quote/?demo=padded` |
| **Reel Autopsy** | Mechanical trading-strategy claims on labelled synthetic data. Tests a claim against a perfect-foresight ceiling. | `/reel/?demo=fx_reel_impossible_sma` |
| **Verify Lab** | Any signed bundle: five verifier scenarios side by side, then offline replay. | `/verify?auto=1&sample=lease-consistent&scenario=tampered-bundle` |

A third claim type (`examples/stub_claimtype`) runs through the same core with zero core edits. That is the reuse proof.

## The journey

**Claim** → **Evidence** → **Deterministic examination** → **Verdict** → **Signed bundle** → **Independent verification** → **Offline replay**

1. The claim is frozen into a canonical spec. The claimed figures are sealed (AES-GCM) in a vault the examiner cannot read.
2. The examiner is a different OS user, reached over an authenticated Unix socket. It receives the spec and the evidence, never the claimed result.
3. It sweeps a bounded grid of assumptions and returns findings. Only then is the claim revealed and compared.
4. The verdict goes into a bundle (hash-chained ledger, commitment, spec hash) signed with Ed25519.
5. A verifier checks integrity, signature, signer trust, authenticity, reproducibility and isolation as six separate results, against a trust store **the verifier** configured. A key inside a bundle is never trusted.
6. `verdictkit replay` re-runs the examination from the bundle with no network.

Findings are labelled by kind: a contradiction inside a claim's own arithmetic (`CONTRADICTED`) is never confused with a refutation by outside evidence (`REFUTED`). `INDETERMINATE`, `CONDITIONAL` and `BLOCKED` are first-class answers. Results read "verified at N grid points", never "for all values".

## Run it

Needs Docker and Node.js 20 or newer. The first run builds the Docker image and installs the UI packages locally, so allow a few minutes; later starts take seconds. Nothing is installed globally and nothing listens beyond `127.0.0.1`.

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File scripts\Start-VerdictKit.ps1
```

```bash
# Linux or macOS
scripts/start-verdictkit.sh
```

The script builds the Docker image if needed, starts the backend (enforced isolation, judge mode, a disposable demonstration signer), checks `/api/v1/health`, builds the UIs, and prints one URL (default `http://127.0.0.1:5170/`). It stops only what it started. Stop with `scripts\Stop-VerdictKit.ps1` or `scripts/stop-verdictkit.sh`.

Then follow the three-minute tour in [`docs/PRODUCT_TOUR.md`](docs/PRODUCT_TOUR.md). To verify a bundle offline, with no network:

```bash
docker run --rm --network none -v "$(pwd):/data:ro" verdictkit:batch2 verdictkit replay /data/<case>.vkb --trust-store /data/vk-demo-trust-store.json
```

## What has been verified

From runs on 2026-11-27 (Windows 11 with Docker Desktop). Ledger with every record: [`docs/next-phase/EXECUTION_EVIDENCE.md`](docs/next-phase/EXECUTION_EVIDENCE.md).

| Check | Result |
|---|---|
| Python regression, Windows (`pytest -m "not isolation"`, CI Hypothesis profile) | 642 passed, 16 skipped, 4 deselected |
| Same suite inside the Linux image as the custodian user | 623 passed, 15 skipped, 6 deselected |
| Enforced-isolation gates (`--network none`): startup, isolation, signed bundles, judge-mode HTTP lifecycle, case and replay | all passed; the judge-mode scan found no vault key in 926 samples |
| Frontend: typecheck, unit tests, production build | clean; 53 tests |
| Browser end-to-end against the real backend (Chrome, no mocks) | 105 checks passed, 0 console errors |
| Dependency audits | `npm audit` and `pip-audit`: no known vulnerabilities |
| Independent security review | no blocker found; see [`docs/SECURITY_REVIEW_BATCH3.md`](docs/SECURITY_REVIEW_BATCH3.md) |

The same stub claim yields the same sealed verdict hash (`547fba0c…aaa79`) in-process on Windows and inside the enforced Linux container. The isolation mode is recorded and differs; the verdict does not.

## What it does not claim

* Not every claim is verifiable. A signature says who sealed a bundle, never that the claim is true.
* Reproducibility is claimed for a pinned environment. Blinding rests on OS-user separation, encryption and a type partition, not on hashes.
* The signing key in the demonstration is disposable and new at every start. It proves nothing about a real signer.
* Quote worksheets are constructed. Reel data is synthetic and labelled; real Reel claims are blocked until licensed data exists. External tax and fee checks cover Texas finance worksheets only, against a hash-pinned snapshot.
* It is a local demonstration, not a public service. Public deployment is not authorised and has not been done.

## How Kiro was used

Specs (`.kiro/specs/`: core, Reel, Quote, and the next-phase plan), steering (`.kiro/steering/`, six files that tests enforce), agent hooks (`.kiro/hooks/`) and an MCP server (`.kiro/settings/mcp.json`). What was actually observed inside Kiro, and what was not, is recorded without embellishment in [`docs/KIRO_USAGE.md`](docs/KIRO_USAGE.md). Earlier implementation passes were done with Claude Code and are labelled as such.

## For developers

```bash
uv sync --frozen --all-packages --all-extras --group dev
HYPOTHESIS_PROFILE=ci uv run --no-sync pytest -q -m "not isolation"
uv run --no-sync verdictkit replay examples/stub_claimtype/golden.vkb
npm ci && npm run typecheck && npm test && npm run build:portal
docker build -t verdictkit . && docker run --rm --network none verdictkit gate-http
node tests/ui/e2e_product.cjs      # needs the stack running; see docs/PRODUCT_TOUR.md
```

* Architecture and decision log: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Signing and trust: [`docs/SIGNING.md`](docs/SIGNING.md). HTTP contract (1.2.0): [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md), `api/openapi.yaml`.
* Judge reproduction: [`docs/JUDGE_DEMO.md`](docs/JUDGE_DEMO.md). Competition text and demo plan: [`docs/DEVPOST.md`](docs/DEVPOST.md), [`docs/DEMO_STORYBOARD.md`](docs/DEMO_STORYBOARD.md).
* Layout: `core/src/verdictkit/` (custody, examiner, evidence, sweep, bundle, signing, API, MCP server), `apps/quote-autopsy`, `apps/reel-autopsy`, `ui/hub` (portal and Verify Lab), `ui-kit` (shared UI), `deploy/` (container entrypoint), `scripts/` (start, stop, gateway, gates).
* MCP server: `python -m verdictkit.mcp_server` (stdio; tools `list_claim_types`, `verify_claim`, `explain_verdict`, `replay_bundle`; file access limited to approved roots).
