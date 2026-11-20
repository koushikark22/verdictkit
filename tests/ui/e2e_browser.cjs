#!/usr/bin/env node
/*
 * Browser end-to-end check of both UIs against a REAL running API (no mock verdicts).
 * Expects: API on VK_API_URL's host (proxied by `vite preview`), quote UI at QUOTE_URL,
 * reel UI at REEL_URL. Driven by scripts/ui_e2e.sh. Exit code 0 only if every check passes.
 */
const { chromium } = require("playwright");

const QUOTE_URL = process.env.QUOTE_URL || "http://127.0.0.1:4173/";
const REEL_URL = process.env.REEL_URL || "http://127.0.0.1:4174/";
let failures = 0;

function check(cond, what) {
  console.log(`${cond ? "PASS" : "FAIL"} ${what}`);
  if (!cond) failures += 1;
}

async function text(page, testid) {
  return (await page.getByTestId(testid).first().textContent()) || "";
}

async function quote(browser) {
  const page = await browser.newPage();
  await page.goto(QUOTE_URL);
  await page.getByTestId("isolation").waitFor();
  check((await text(page, "isolation")).includes("UNENFORCED"), "quote: isolation banner reflects the server");
  const form = page.getByRole("form", { name: "Worksheet intake" });
  await form.getByLabel("Selling price").fill("30000.00");
  await form.getByLabel("Doc fee", { exact: true }).fill("500.00");
  await form.getByLabel("Doc fee taxable?").selectOption("unknown");
  await form.getByLabel("Cash down").fill("5000.00");
  await form.getByLabel("Stated tax rate %").fill("6.00");
  await form.getByLabel("APR %").fill("6.00");
  await form.getByLabel("State (2 letters)").fill("TX");
  await form.getByLabel("taxable base").fill("30500.00");
  await form.getByRole("button", { name: "Freeze and examine" }).click();
  await page.getByTestId("verdict").waitFor({ timeout: 30000 });
  const headline = await text(page, "headline");
  check(headline.includes("CONDITIONAL") && headline.includes("COMPLETED"), `quote: unknown doc-fee taxability -> ${headline.trim()}`);
  check((await form.getByLabel("taxable base").inputValue()) === "", "quote: claimed figure cleared after intake");
  const stages = await page.locator("[data-testid=progress] li").evaluateAll((ls) => ls.map((l) => l.getAttribute("data-stage")));
  check(stages.includes("EXAMINATION_COMMITTED") && stages.indexOf("EXAMINATION_COMMITTED") < stages.indexOf("OUTCOMES_REVEALED"),
    "quote: progress shows examination committed before reveal");
  await page.getByTestId("bundle-metadata").waitFor();
  check((await text(page, "bundle-metadata")).includes("VERIFIED"), "quote: bundle integrity VERIFIED");
  await page.getByRole("button", { name: "Replay on server (no network)" }).click();
  await page.getByTestId("replay-report").waitFor();
  const replayed = (await page.getByTestId("replay-report").getByTestId("repro-status").textContent() || "").trim();
  check(["REPRODUCED", "REPRODUCED_ACROSS_ENV"].includes(replayed), `quote: server replay reproduces (${replayed})`);
  await page.locator("[data-example=padded]").click();
  await form.getByRole("button", { name: "Freeze and examine" }).click();
  await page.waitForFunction(() => document.querySelector("[data-testid=headline]")?.textContent?.includes("CONTRADICTED"), null, { timeout: 30000 });
  check((await text(page, "finding-amount_financed")).includes("point of failure"), "quote: padded example marks amount_financed as point of failure");
  check((await text(page, "diagnostics")).includes('"firstBrokenLine": "amount_financed"'), "quote: after-reveal diagnostic localises the packed amount");
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download .vkb" }).click();
  check((await download).suggestedFilename().endsWith(".vkb"), "quote: bundle downloads");
  await page.close();
}

async function reel(browser) {
  const page = await browser.newPage();
  await page.goto(REEL_URL);
  await page.locator("[data-fixture=fx_reel_impossible_sma]").click();
  await page.getByTestId("verdict").waitFor({ timeout: 60000 });
  check((await text(page, "headline")).includes("IMPOSSIBLE"), "reel demo: engine computes IMPOSSIBLE");
  check((await page.getByTestId("demo-notice").count()) >= 2, "reel demo: demonstration notice on the verdict");
  check((await text(page, "evidence")).includes("SYNTHETIC_FIXTURE"), "reel demo: evidence provenance is labelled synthetic");
  check((await text(page, "sensitivity")).includes("16 grid points"), "reel demo: verified at 16 grid points");
  await page.locator("[data-fixture=fx_reel_conditional_sma]").click();
  await page.waitForFunction(() => document.querySelector("[data-testid=headline]")?.textContent?.includes("CONDITIONAL"), null, { timeout: 60000 });
  check(true, "reel demo: conditional fixture -> CONDITIONAL");

  await page.getByRole("button", { name: "Check a real claim" }).click();
  const form = page.getByRole("form", { name: "Claim intake" });
  await form.getByLabel(/Paste the claim text/).fill("SMA cross by @trader on BTC, +340%");
  await form.getByRole("button", { name: "Freeze and examine" }).click();
  await page.getByTestId("error").waitFor();
  check((await text(page, "error")).includes("PRIVACY_REJECTED"), "reel: handle in pasted text -> PRIVACY_REJECTED");

  await form.getByLabel(/Paste the claim text/).fill("");
  await form.getByLabel("Instrument").fill("BTCUSD");
  await form.getByLabel("Timeframe").selectOption("1d");
  await form.getByLabel("Start (UTC date)").fill("2025-01-01");
  await form.getByLabel("End (exclusive)").fill("2026-01-01");
  await form.getByLabel("Template").selectOption("SMA_CROSS");
  await form.getByLabel("fast").fill("10");
  await form.getByLabel("slow").fill("30");
  await form.getByLabel("total return pct").fill("340");
  await form.getByRole("button", { name: "Freeze and examine" }).click();
  await page.getByTestId("blockers").waitFor({ timeout: 30000 });
  check((await text(page, "blockers")).includes("EVIDENCE_UNAVAILABLE"), "reel: real claim is BLOCKED, not judged on guessed data");
  check((await text(page, "headline")).includes("NO VERDICT"), "reel: blocked claim shows no verdict");
  await page.close();
}

(async () => {
  const browser = await chromium.launch();
  try {
    await quote(browser);
    await reel(browser);
  } catch (e) {
    console.log(`FAIL unexpected error: ${e && e.message}`);
    failures += 1;
  } finally {
    await browser.close();
  }
  console.log(failures ? `UI-E2E FAILED (${failures})` : "UI-E2E PASSED");
  process.exit(failures ? 1 : 0);
})();
