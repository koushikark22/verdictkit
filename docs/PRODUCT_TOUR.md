# VerdictKit product tour

> Don't trust the claim. Verify the evidence. Reproduce the verdict.

Everything below runs locally. All services listen on `127.0.0.1` only. Samples are constructed worksheets and labelled synthetic price data; nothing here is a real dealer quote, a real market or a real person's claim.

## Start

Windows (PowerShell, from the repository root):

```
powershell -ExecutionPolicy Bypass -File scripts\Start-VerdictKit.ps1 -Image verdictkit:batch3 -Rebuild
```

Linux or macOS: `bash scripts/start-verdictkit.sh --image verdictkit:batch3 --rebuild`. Stop with `scripts\Stop-VerdictKit.ps1` or `scripts/stop-verdictkit.sh`.

The script starts the Docker backend (enforced OS-user isolation, judge mode, a disposable demonstration signer), checks that `/api/v1/health` reports `ENFORCED`, `judgeMode: true` and contract `1.2.0`, builds the UIs if needed, starts one local gateway and prints **one entry URL** (default `http://127.0.0.1:5170/`). If a port is taken it uses the next free one and says so. It never stops a process or container it did not start itself; occupied ports are left alone.

## Three minutes

1. **Overview** (`/`). The live panel shows what `/health` and `/api/v1/demo/status` returned: connection, API version, isolation, judge mode and the demonstration signer's public key id. The diagram's wall is drawn solid only because the server said `ENFORCED`.
2. **Quote Autopsy** (`/quote/?demo=padded`). A finance worksheet with 400.00 hidden in the amount financed. The verdict is `CONTRADICTED`, labelled *Internal arithmetic*, with the first broken line named and the unexplained amount estimated by the engine's after-reveal diagnostic. Try `lease-consistent` and `lease-padded` too.
3. **Reel Autopsy** (`/reel/?demo=fx_reel_impossible_sma`). A claimed +3,400% on labelled synthetic data against the engine's perfect-foresight ceiling: `IMPOSSIBLE`, labelled *Mathematical bound*. `fx_reel_conditional_sma` shows an answer that depends on fee assumptions.
4. **Verify a bundle** (`/verify?auto=1&sample=lease-consistent&scenario=tampered-bundle`). One URL runs a sample, obtains a signed bundle, then verifies the scenario. Use **Run all five scenarios** to see them side by side.

## Signed-bundle demonstration

1. Open `/verify` and press **Examine this sample** (any of the four).
2. The bundle card shows the file, its sha256 and the demonstration key that signed it. Download the bundle and the public trust store.
3. Pick a scenario and press **Verify and replay**. Six results appear separately: evidence integrity, signature validity, signer trust, authenticity, verdict reproducibility and isolation mode. A plain sentence explains the combination without saying the claim is true.
4. Try it yourself: change one byte inside the downloaded `.vkb` with any zip tool and upload it in step 4. Integrity fails and nothing is reproduced.
5. Offline, no network (the exact command with your file name is on the page):

```
docker run --rm --network none -v "$(pwd):/data:ro" verdictkit:batch3 verdictkit replay /data/<case>.vkb --trust-store /data/vk-demo-trust-store.json
```

`verdictkit verify` with no `--trust-store` exits 1 with `signer trust: NOT_EVALUATED`: an embedded key is never trusted.

## Routes

| Route | Screen |
|---|---|
| `/` | Overview and live system status |
| `/verify` | Verify Lab (query: `auto=1`, `sample`, `scenario`, `caseId`) |
| `/quote/` | Quote Autopsy (query: `demo=consistent\|padded\|lease-consistent\|lease-padded`) |
| `/reel/` | Reel Autopsy (query: `demo=fx_reel_supported_hold\|fx_reel_conditional_sma\|fx_reel_impossible_sma`) |
| `/api/v1/*` | proxied to the backend; `/__gateway/health` and `/__gateway/config.json` belong to the gateway |

## When something is wrong

- *Backend offline*: the header pill and every page say so and show how to start it; no number is invented.
- *Busy*: the backend allows 120 requests a minute per client. The UI reports "rate limited, retrying", not "offline".
- *Blocked*: a real Reel claim has no licensed data and is blocked at the evidence stage instead of judged on guesses.
- The demonstration key is valid for seven days from start. Restart to get a new one.

## What is not claimed

Not every claim is verifiable; `INDETERMINATE` and `CONDITIONAL` are answers. Results are "verified at N grid points", never "for all values". Reproducibility is claimed for the pinned environment. A signature says who sealed a bundle, not that the claim is true. Public deployment is not authorised and is not done.
