# VerdictKit — judge demo and independent reproduction

VerdictKit is a **validated demonstration**. It must not be presented as a production multi-user service. Use **synthetic data only** for Reel and sample worksheet entries for Quote.

Repository: https://github.com/koushikark22/verdictkit

## Prerequisites

- Git and Docker (Linux Docker daemon or Docker Desktop on Windows/macOS)
- Optional local UI: Python 3.12, `uv`, Node.js 22, npm
- No external dataset keys or payments are required

## Quick-start Docker verification (Linux/macOS shell or Windows with bash)

From the cloned repository root:

```bash
docker build -t verdictkit .
docker run --rm --network none verdictkit gate-startup
docker run --rm --network none verdictkit gate-http
```

Expected judge startup marker:

```text
VK_STARTUP_OK isolation=ENFORCED
```

The HTTP gate should terminate with `GATE-HTTP PASSED` and reject synthetic evidence in a live case. This tests a Linux container with distinct `vk-custodian` and `vk-examiner` OS identities. Running `uv` directly on Windows does **not** establish ENFORCED isolation.

For the deterministic example case:

```bash
mkdir -p gate
docker run --rm --network none -v "$PWD/gate:/out" -v "$PWD/examples/stub_claimtype:/in:ro" verdictkit gate-case /in/claim.json /out/stub.vkb
docker run --rm --network none -v "$PWD/gate:/out:ro" verdictkit verdictkit replay /out/stub.vkb
```

The replay should verify integrity and reproduce the sealed verdict. The bundle is **not signed**. On Windows PowerShell, volume mount syntax may differ; use a bash-compatible shell for the commands above or inspect `deploy/entrypoint.sh`.

## Local browser demos

From the repository root, install Python and Node dependencies:

```bash
uv sync --frozen --all-packages --all-extras --group dev
npm ci
```

Run the real FastAPI app (in a development terminal):

```bash
export VK_DRAFT_DIR=/tmp/vk
export VK_VAULT_KEY="$(python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
uv run --no-sync python -m verdictkit.api --port 8000
```

In additional terminals:

```bash
npm run dev -w apps/quote-autopsy/web
npm run dev -w apps/reel-autopsy/web
```

Open the two Vite development URLs printed by their respective commands (nominally ports 5173 and 5174). Both communicate with a real API, not fabricated verdicts. Use bundled sample scenarios; do not enter sensitive user or financial information.

Optional browser regression on a Linux environment with a Playwright Chromium installation:

```bash
bash scripts/ui_e2e.sh
```

## What a judge can verify

1. **Reusable core**: canonical JSON, answer blinding, sealed commitment, deterministic evaluation, bounded assumption sweeps.
2. **Quote Autopsy**: sample document-internal finance/lease arithmetic, scenario sensitivity, and post-verdict diagnostic separation. External tax-rate and dealer-fee findings remain INDETERMINATE without an authoritative rules snapshot.
3. **Reel Autopsy**: synthetic OHLCV evaluation and illustrative equity chart. These are not live prices or independently verified real returns.
4. **Isolation boundary**: examiner IPC identity verified by Linux peer credentials; only container mode can legitimately claim ENFORCED.
5. **Offline replay**: bundle integrity and verdict reproducibility; authenticity is NOT_ESTABLISHED absent signatures.

## Public test evidence

The merged implementation and post-merge workflows were checked on November 20, 2026:

- Merge commit: `226ec473cb9058630a38863814b673cc1375aba6`
- Integration: https://github.com/koushikark22/verdictkit/actions/runs/44816981661
- API safety: https://github.com/koushikark22/verdictkit/actions/runs/44816981688

Those historical runs validate that commit, not future changes. For any later PR, rely on CI at the **new head**. CI evidence is not a substitute for running the demonstration on the judge's own machine.

## Important safety and accuracy boundaries

- No live third-party market feeds or licensed redistribution are bundled.
- No publicly accessible hosted demo is asserted here.
- No genuine Kiro interaction is asserted by this guide; see `docs/KIRO_USAGE.md`.
- Do not treat verdict bundles as digitally signed.
- Deploy outside the Docker gate only with explicit acknowledgment of UNENFORCED isolation, and never claim judge-mode enforcement without the container gate.
