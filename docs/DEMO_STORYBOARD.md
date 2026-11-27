# Demo storyboard, narration and recording checklist

**Status: the video has NOT been recorded.** This is the plan. Do not describe a video as made until a recording exists and has been watched through against the checklist at the end.

Target: 2 minutes 50 seconds, one take of the real application (no mock screens). The story is the whole journey:

**Claim → Evidence → Deterministic examination → Verdict → Signed bundle → Independent verification → Offline replay.**

The three product moments are *Quote Contradicted*, *Reel Impossible* and the *five Verify Lab scenarios*. Everything shown is computed live by the engine; the narration states what the screen shows and nothing the screen does not.

## Shot list

| Time | On screen | Narration (read at a calm pace) |
|---|---|---|
| 0:00-0:15 | Overview page `/`: headline, the isolation diagram, the live status tiles. | "Anyone can state a claim. VerdictKit checks it without letting the answer influence the check. It freezes the claim, seals the claimed result away from the examiner, recomputes it blind, and gives you a signed bundle you can verify and replay offline. One framework, three screens." |
| 0:15-0:55 | `/quote/?demo=padded`. Let the progress chips run. Stop on the verdict, then the line-by-line table. | "A car-finance worksheet. The examiner never saw the stated totals. Verdict: contradicted. The first line that breaks is the amount financed: the worksheet says 24,793.63, its own lines give 24,393.63, a difference of 400.00, and every later line follows from that one. This is an arithmetic contradiction inside the worksheet. It does not say anyone meant it." |
| 0:55-1:25 | `/reel/?demo=fx_reel_impossible_sma`. Verdict, the line-by-line table, then the equity chart. | "A trading claim of plus 3,400 percent, on labelled synthetic data. Under the declared mechanics nothing could beat 2,872. The verdict is impossible, and it says that is about the claim, not about the person. The chart is the engine's own series for one grid point, marked illustrative. Same custody, same examiner, different domain." |
| 1:25-2:20 | `/verify?auto=1&sample=lease-consistent&scenario=trusted-signer`. Show the signed bundle card (file, sha256, signer key id), then press **Run all five scenarios**. Hold on the side-by-side table, then on the tampered result. | "This demonstration signs each examination bundle. Here the verifier trusts the signer: integrity verified, signature valid, trusted, authenticity established, verdict reproduced. Same bundle, a verifier that never heard of the signer: valid signature, not trusted. A verifier that revoked the key: not trusted. A bundle with the signature removed still replays, but proves no origin. And one character changed after signing: integrity fails, nothing is replayed. A signature says who sealed it. It never says the claim is true." |
| 2:20-2:45 | A terminal beside the browser: `docker run --rm --network none -v "$(pwd):/data:ro" verdictkit:batch3 verdictkit replay /data/<case>.vkb --trust-store /data/vk-demo-trust-store.json`. Show `integrity: VERIFIED`, `reproducibility: REPRODUCED` and the two equal hashes. Optionally rerun on a hand-edited copy to show the non-zero exit. | "Now with no network at all. The downloaded bundle and the public trust store, replayed in a container: integrity verified, verdict reproduced, original and replayed hashes identical." |
| 2:45-2:50 | Overview page again, or the repository README. | "Not every claim can be verified, and VerdictKit says so. One engine, three surfaces, built with Kiro specs, steering, hooks and an MCP server." |

The post-reconnect MCP calls are now documented in `docs/KIRO_USAGE.md`. An optional five-second cut of a genuine Kiro interaction can demonstrate the integration; label Windows MCP isolation as UNENFORCED and do not imply that its bundle is signed.

## Facts the narration relies on (re-check against the screen when recording)

* Quote padded sample: stated amount financed 24,793.63, engine 24,393.63, difference 400.00; finance charge and monthly payment also differ; sales tax and taxable base are consistent.
* Reel impossible sample: claimed 3,400; engine ceiling 2,872.54378305; the engine's own return on the data is -34.51672459 (`REFUTED`, external evidence). The demonstration notice is visible.
* Five scenarios: trusted `ESTABLISHED`; unknown and revoked `NOT_ESTABLISHED` (`UNTRUSTED_SIGNER`); unsigned historical `NOT_ESTABLISHED` yet `REPRODUCED`; tampered `FAILED` and `UNVERIFIABLE`.
* The demonstration signer is disposable and new at every start; the page says so. Do not call it a certificate authority or a real identity.

## Pre-flight checklist

- [ ] Fresh start: `scripts\Stop-VerdictKit.ps1`, then `scripts\Start-VerdictKit.ps1 -Image verdictkit:batch3 -Rebuild`. Confirm the pill reads `API 1.2.0 · isolation ENFORCED`.
- [ ] Pre-run each guided link once, then wait one minute. The backend allows 120 requests a minute per client and every tab shares one address.
- [ ] Browser at 100% zoom, 1440 x 900 or 1920 x 1080, one window, bookmarks bar hidden, no personal tabs. Close unrelated applications and mute notifications.
- [ ] Terminal font large enough to read; the prompt must not show a user name or home path (use a clean prompt and a short working directory).
- [ ] Download the bundle and `vk-demo-trust-store.json` into an empty folder before recording the offline replay.
- [ ] Screen recorder set to capture the browser and the terminal at the same time; microphone level checked with a test clip.

## After recording: inspection checklist (all must be ticked before the video is called done)

- [ ] Watched end to end at normal speed; length is under 3:00.
- [ ] Every number spoken matches the screen at that moment.
- [ ] No claim of a real dealer, real market or real signer; "demonstration" and "synthetic" are said or visible where they apply.
- [ ] No private information visible: user name, home path, tokens, e-mail, other tabs, notifications.
- [ ] The five scenario results shown are the ones in the fact list above.
- [ ] If Kiro is shown, what is on screen is a real Kiro interaction, labelled as it was recorded.
- [ ] File hash and length noted in the evidence ledger; the link added to `docs/DEVPOST.md` only now.

## Stills for the Devpost gallery

`docs/screenshots/` is regenerated by `node tests/ui/e2e_product.cjs`: `01-landing-desktop`, `02-quote-contradicted-desktop`, `03-reel-impossible-desktop`, `04-verify-lab-desktop` (five-scenario table with the tampered result), `05-backend-offline`, `06-landing-mobile`, `07-reel-verdict-mobile`, `08-verify-tampered-mobile`, plus `-full.jpg` page captures. Each was looked at before it was kept.
