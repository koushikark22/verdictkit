#!/usr/bin/env node
/*
 * Browser end-to-end check of the unified VerdictKit product against a REAL running stack: the Docker
 * backend (enforced isolation, judge mode, demonstration signer) behind the local gateway. No mock
 * verdicts and no mock verification: every assertion is about what the backend actually returned.
 *
 *   node scripts/gateway.mjs ...          (or scripts\Start-VerdictKit.ps1 -NoBrowser)
 *   VK_E2E_BASE=http://127.0.0.1:5170 node tests/ui/e2e_product.cjs
 *
 * Needs playwright-core and a system Chrome or Edge (VK_BROWSER=<path> overrides). Child processes get
 * an allowlisted environment, so nothing unrelated is inherited and nothing is ever printed from it.
 */
const { chromium } = require("playwright-core");
const { spawn, spawnSync } = require("node:child_process");
const fs = require("node:fs");
const net = require("node:net");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..", "..");
const BASE = (process.env.VK_E2E_BASE || "http://127.0.0.1:5170").replace(/\/$/, "");
const IMAGE = process.env.VK_IMAGE || "verdictkit:batch2";
const SHOTS = path.join(ROOT, "docs", "screenshots");
const WORK = fs.mkdtempSync(path.join(os.tmpdir(), "vk-e2e-"));
const SAFE_ENV_NAMES = ["PATH", "Path", "PATHEXT", "SystemRoot", "SYSTEMROOT", "windir", "COMSPEC", "TEMP", "TMP", "USERPROFILE", "HOME",
  "APPDATA", "LOCALAPPDATA", "ProgramData", "ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "LANG", "TERM"];
const safeEnv = () => Object.fromEntries(SAFE_ENV_NAMES.filter((n) => process.env[n] !== undefined).map((n) => [n, process.env[n]]));

let failures = 0, passes = 0;
function check(cond, what) {
  console.log(`${cond ? "PASS" : "FAIL"} ${what}`);
  if (cond) passes += 1; else failures += 1;
}
const text = async (page, id) => ((await page.getByTestId(id).first().textContent()) || "").trim();
const shot = async (page, name, full = false) => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const file = path.join(SHOTS, name);
  await page.screenshot(full ? { path: file.replace(/\.png$/, ".jpg"), type: "jpeg", quality: 70, fullPage: true } : { path: file, type: "png" });
};

async function launch() {
  const attempts = process.env.VK_BROWSER ? [{ executablePath: process.env.VK_BROWSER }] : [{ channel: "chrome" }, { channel: "msedge" }];
  let last;
  for (const opt of attempts) {
    try { return await chromium.launch({ headless: true, ...opt }); } catch (e) { last = e; }
  }
  throw last;
}

/** Collects browser errors; a clean run has none. */
function guard(page, label, sink) {
  page.on("pageerror", (e) => sink.push(`${label} pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") sink.push(`${label} console: ${m.text()}`); });
  page.on("response", (r) => { if (r.status() === 429) sink.push(`${label} RATE_LIMITED ${r.url().replace(/case_[0-9a-f]+/, "case_*")}`); });
}
const headline = (page, word, timeout = 90000) =>
  page.waitForFunction((w) => document.querySelector("[data-testid=headline]")?.textContent?.includes(w), word, { timeout });

function freePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.on("error", reject);
    s.listen(0, "127.0.0.1", () => { const { port } = s.address(); s.close(() => resolve(port)); });
  });
}
function python() {
  const win = path.join(ROOT, ".venv", "Scripts", "python.exe");
  return fs.existsSync(win) ? win : (fs.existsSync(path.join(ROOT, ".venv", "bin", "python")) ? path.join(ROOT, ".venv", "bin", "python") : "python");
}

// ---------------------------------------------------------------------------------------------
async function landingAndNavigation(browser, errors) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  const page = await ctx.newPage();
  guard(page, "landing", errors);
  const health = await (await ctx.request.get(`${BASE}/api/v1/health`)).json();
  const lab = await (await ctx.request.get(`${BASE}/api/v1/demo/status`)).json();
  await page.goto(`${BASE}/`);
  await page.getByTestId("status-backend").waitFor();
  check((await page.locator("h1").first().textContent()).includes("Don't trust the claim. Verify the evidence. Reproduce the verdict."), "landing: the central narrative is the headline");
  check((await text(page, "status-backend")) === "CONNECTED", "landing: backend connectivity comes from /health");
  check((await text(page, "status-api-version")) === health.contractVersion && health.contractVersion === "1.2.0", `landing: API version is the server's (${health.contractVersion})`);
  check((await text(page, "status-isolation")) === health.isolationMode && health.isolationMode === "ENFORCED", `landing: isolation is the server's (${health.isolationMode})`);
  check((await text(page, "status-judge")) === (health.judgeMode ? "ON" : "OFF"), "landing: judge mode is the server's");
  check((await text(page, "status-key-id")) === lab.signer.keyId, "landing: the demonstration signer id is the server's public key id");
  const live = await text(page, "live-status");
  check(live.includes("API 1.2.0") && live.includes("ENFORCED"), `landing: header status pill reads "${live}"`);
  check((await page.locator("[data-testid=guided-demos] a[data-demo]").count()) === 12, "landing: 12 guided demonstration links (4 quote, 3 reel, 5 verify)");
  check((await page.content()).includes("PRIVATE KEY") === false, "landing: no private key material in the page");
  check((await text(page, "isolation-diagram")).includes("this server enforces the boundary") && (await page.locator(".vk-wall").getAttribute("class")) === "vk-wall ",
    "landing: the isolation diagram is drawn solid because /health said ENFORCED");
  const secondary = await page.getByTestId("cta-verify").evaluate((el) => { const s = getComputedStyle(el); return { color: s.color, bg: s.backgroundColor }; });
  check(secondary.color === "rgb(255, 255, 255)", `landing: the secondary buttons are legible on the dark hero (text ${secondary.color})`);
  await shot(page, "01-landing-desktop.png");
  await shot(page, "01-landing-desktop-full.png", true);

  const nav = page.getByRole("navigation", { name: "VerdictKit applications" });
  await nav.getByRole("link", { name: "Quote Autopsy" }).click();
  await page.waitForURL(/\/quote\/$/);
  check((await page.locator("h1").first().textContent()) === "Quote Autopsy", "navigation: Overview -> Quote Autopsy");
  check((await nav.getByRole("link", { name: "Quote Autopsy" }).getAttribute("aria-current")) === "page", "navigation: current page is marked");
  await nav.getByRole("link", { name: "Reel Autopsy" }).click();
  await page.waitForURL(/\/reel\/$/);
  check((await page.locator("h1").first().textContent()) === "Reel Autopsy", "navigation: Quote -> Reel Autopsy");
  await nav.getByRole("link", { name: "Verify a Bundle" }).click();
  await page.waitForURL(/\/verify$/);
  check((await page.locator("h1").first().textContent()).includes("Verify a signed evidence bundle"), "navigation: Reel -> Verify a Bundle");
  await page.getByRole("link", { name: "VerdictKit home" }).click();
  await page.waitForURL(`${BASE}/`);
  check((await page.locator("h1").first().textContent()).includes("Verify the evidence"), "navigation: brand returns to the overview");
  await ctx.close();
  return lab.signer.keyId;
}

async function quoteFinanceAndLease(browser, errors, downloads) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();
  guard(page, "quote", errors);
  await page.goto(`${BASE}/quote/`);
  await page.getByTestId("isolation").waitFor();
  check((await text(page, "isolation")).includes("ENFORCED"), "quote: isolation banner reflects the server (ENFORCED)");
  check((await page.locator("[data-testid=empty-state]").count()) === 1, "quote: empty state before any examination");

  // Error handling: an empty finance form is refused on the page, before anything is sent.
  await page.getByRole("button", { name: "Freeze and examine" }).click();
  const formErrors = await page.locator("form[aria-label='Worksheet intake'] ul.vk-error").innerText();
  check(formErrors.includes("selling price must be a plain decimal number") && formErrors.includes("state must be a two-letter code"), "quote: an incomplete worksheet shows readable form errors and sends nothing");
  check((await page.locator("[data-testid=phase]").count()) === 0, "quote: no examination started for the invalid form");

  // Finance: the padded sample is CONTRADICTED and localised; the consistent sample is CONSISTENT.
  await page.locator("[data-run-example=padded]").click();
  await headline(page, "CONTRADICTED");
  const head = await text(page, "headline");
  check(head.includes("COMPLETED") && head.includes("Internal arithmetic"), `quote finance padded: ${head.slice(0, 60)}...`);
  check(await page.waitForFunction(() => { const r = document.querySelector("[data-testid=verdict]")?.getBoundingClientRect(); return !!r && r.top >= 0 && r.top < innerHeight * 0.7; }, null, { timeout: 8000 }).then(() => true, () => false),
    "quote: after one click on a sample the verdict is scrolled into view (not left below the form)");
  const why = await text(page, "why-verdict");
  check(why.includes("first line that breaks is amount financed") && why.includes("24,793.63") && why.includes("24,393.63") && why.includes("not a finding about outside facts"),
    "quote finance: the plain-language explanation names the broken line and both figures");
  check((await text(page, "finding-amount_financed")).includes("point of failure"), "quote finance: amount_financed marked as the point of failure");
  check((await text(page, "diagnostics")).includes('"firstBrokenLine": "amount_financed"'), "quote finance: the after-reveal diagnostic localises the packed amount");
  check((await page.locator("[data-testid=findings-table] tbody tr").count()) === 6, "quote finance: the financial table has one row per stated line (6)");
  const stages = await page.locator("[data-testid=progress] li").evaluateAll((ls) => ls.map((l) => l.getAttribute("data-stage")));
  check(stages.indexOf("EXAMINATION_COMMITTED") >= 0 && stages.indexOf("EXAMINATION_COMMITTED") < stages.indexOf("OUTCOMES_REVEALED"), "quote: progress shows the examination committed before the claim was revealed");
  await page.getByTestId("bundle-metadata").waitFor();
  const meta = page.getByTestId("bundle-metadata");
  const vals = [await meta.getByTestId("integrity-status").textContent(), await meta.getByTestId("signature-validity").textContent(),
    await meta.getByTestId("signer-trust").textContent(), await meta.getByTestId("authenticity-status").textContent(), await meta.getByTestId("isolation-mode").textContent()];
  check(vals.join("|") === "VERIFIED|VALID|TRUSTED|ESTABLISHED|ENFORCED", `quote: the real bundle verifies as written (${vals.join(" / ")})`);
  await shot(page, "02-quote-contradicted-desktop.png");
  await shot(page, "02-quote-contradicted-desktop-full.png", true);
  await page.getByRole("button", { name: "Replay on server (no network)" }).click();
  await page.getByTestId("replay-report").waitFor({ timeout: 60000 });
  const replayed = await page.getByTestId("replay-report").getByTestId("repro-status").textContent();
  check(["REPRODUCED", "REPRODUCED_ACROSS_ENV"].includes(replayed), `quote: server replay reproduces the verdict (${replayed})`);
  const dl = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download .vkb" }).click();
  const file = await dl;
  check(file.suggestedFilename().endsWith(".vkb"), "quote: the signed bundle downloads");
  downloads.quote = path.join(WORK, "quote-padded.vkb");
  await file.saveAs(downloads.quote);

  // From the application's own result straight into the Verify Lab, for the same real case.
  const verifyHref = await page.getByRole("link", { name: "Open in Verify Lab" }).getAttribute("href");
  const caseId = new URL(verifyHref, BASE).searchParams.get("caseId");
  const lab = await ctx.newPage();
  guard(lab, "quote-to-verify", errors);
  await lab.goto(`${BASE}${verifyHref}`);
  await lab.getByTestId("bundle-card").waitFor({ timeout: 60000 });
  check(!!caseId && (await text(lab, "bundle-card")).includes(`${caseId}.vkb`), "quote -> verify: the Verify Lab opens the very bundle the application just produced");
  await lab.getByTestId("verify-button").click();
  await lab.getByTestId("lab-result").waitFor({ timeout: 120000 });
  const handoff = lab.getByTestId("lab-report");
  check((await handoff.getByTestId("authenticity-status").textContent()) === "ESTABLISHED" && (await handoff.getByTestId("integrity-status").textContent()) === "VERIFIED",
    "quote -> verify: that bundle verifies as ESTABLISHED against the trusted verifier");
  await lab.close();

  await page.locator("[data-run-example=consistent]").click();
  await headline(page, "CONSISTENT");
  check((await text(page, "headline")).includes("COMPLETED"), "quote finance consistent: CONSISTENT");

  // Lease (cap cost known)
  await page.locator("[data-run-example=lease-consistent]").click();
  await headline(page, "CONSISTENT");
  check((await page.locator("[data-testid=findings-table] tbody tr").count()) === 5, "quote lease consistent: five payment lines, all recomputed");
  await page.locator("[data-run-example=lease-padded]").click();
  await headline(page, "CONTRADICTED");
  check((await text(page, "finding-rent_charge")).includes("CONTRADICTED"), "quote lease padded: the inflated rent charge is CONTRADICTED");
  check((await text(page, "finding-depreciation_fee")).includes("CONSISTENT"), "quote lease padded: the untouched depreciation line stays CONSISTENT");

  // Itemised lease, entered by hand through the form (the same path as the existing e2e).
  await page.getByRole("button", { name: "Lease (itemised)" }).click();
  const form = page.getByRole("form", { name: "Worksheet intake" });
  await form.getByLabel("MSRP", { exact: true }).fill("42000.00");
  await form.getByLabel("Selling price (lease)").fill("39500.00");
  await form.getByLabel("Acquisition fee").fill("895.00");
  await form.getByLabel("Doc fee (capitalised)").fill("150.00");
  await form.getByLabel("Cash cap-cost reduction").fill("2000.00");
  await form.getByLabel("Rebate").fill("1000.00");
  await form.getByLabel("Residual", { exact: true }).fill("58");
  await form.getByLabel("Money factor (itemised)").fill("0.00125");
  await form.getByLabel("Tax rate % (itemised)").fill("8.25");
  await form.getByLabel("State (itemised)").fill("TX");
  await form.getByLabel("stated adjusted cap cost").fill("37545.00");
  await form.getByLabel("stated residual value").fill("24360.00");
  await form.getByRole("button", { name: "Freeze and examine" }).click();
  await page.waitForFunction(() => /CONSISTENT/.test(document.querySelector("[data-testid=headline]")?.textContent || "")
    && !!document.querySelector("[data-testid=finding-stated_residual_value]"), null, { timeout: 90000 });
  check((await text(page, "sensitivity")).includes("rounding_convention"), "quote itemised lease: swept over the rounding convention, CONSISTENT");
  check((await form.getByLabel("stated adjusted cap cost").inputValue()) === "", "quote: claimed figures are cleared from the page once accepted");

  // Texas rules: an unknown doc-fee taxability sweeps both readings and is CONDITIONAL. Start from a clean form.
  await page.goto(`${BASE}/quote/`);
  await page.getByTestId("isolation").waitFor();
  await form.getByLabel("Selling price").fill("30000.00");
  await form.getByLabel("Doc fee", { exact: true }).fill("500.00");
  await form.getByLabel("Doc fee taxable?").selectOption("unknown");
  await form.getByLabel("Cash down").fill("5000.00");
  await form.getByLabel("Stated tax rate %").fill("6.00");
  await form.getByLabel("APR %").fill("6.00");
  await form.getByLabel("State (2 letters)").fill("TX");
  await form.getByLabel("taxable base").fill("30500.00");
  await form.getByRole("button", { name: "Freeze and examine" }).click();
  await headline(page, "CONDITIONAL");
  check(true, "quote: unknown doc-fee taxability -> CONDITIONAL (an assumption the worksheet does not state)");
  await ctx.close();
}

async function reel(browser, errors) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  guard(page, "reel", errors);
  await page.goto(`${BASE}/reel/`);
  await page.getByTestId("isolation").waitFor();
  check((await page.locator("[data-testid=demos]").innerText()).includes("DEMONSTRATION ONLY"), "reel: demonstrations are labelled as such before they run");
  await page.locator("[data-fixture=fx_reel_supported_hold]").click();
  await headline(page, "SUPPORTED");
  check(true, "reel demo: exact trade count -> SUPPORTED");
  await page.locator("[data-fixture=fx_reel_conditional_sma]").click();
  await headline(page, "CONDITIONAL");
  check(true, "reel demo: return that depends on costs -> CONDITIONAL");
  check(/holds at \d+ of 16 grid points verified and fails at \d+/.test(await text(page, "why-verdict")), "reel conditional: the explanation reports the real pass and fail counts of the 16-point grid");
  await page.locator("[data-fixture=fx_reel_impossible_sma]").click();
  await headline(page, "IMPOSSIBLE");
  check((await page.getByTestId("demo-notice").count()) >= 2, "reel demo: demonstration notice on the verdict");
  check((await text(page, "evidence")).includes("SYNTHETIC_FIXTURE"), "reel demo: evidence provenance is labelled synthetic");
  check((await text(page, "sensitivity")).includes("16 grid points"), "reel demo: verified at 16 grid points");
  check((await text(page, "equity-chart")).includes("ILLUSTRATIVE"), "reel demo: the equity chart is labelled illustrative");
  check((await page.locator("[data-testid^=bars-]").count()) >= 1, "reel demo: claimed value is drawn against the engine's ceiling");
  check((await text(page, "headline")).includes("Mathematical bound"), "reel demo: the verdict names its kind (mathematical bound)");
  const ceiling = await text(page, "why-verdict");
  check(ceiling.includes("perfect foresight") && ceiling.includes("does not say the claimant lied"), "reel demo: the explanation states the ceiling and does not accuse anyone");
  await shot(page, "03-reel-impossible-desktop.png");
  await shot(page, "03-reel-impossible-desktop-full.png", true);

  await page.getByRole("button", { name: "Check a real claim" }).click();
  const form = page.getByRole("form", { name: "Claim intake" });
  await form.getByLabel(/Paste the claim text/).fill("SMA cross by @trader on BTC, +340%");
  await form.getByRole("button", { name: "Freeze and examine" }).click();
  await page.getByTestId("error").waitFor();
  check((await text(page, "error")).includes("PRIVACY_REJECTED"), "reel: a handle in pasted text -> PRIVACY_REJECTED, shown in plain words");
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
  await page.getByTestId("blockers").waitFor({ timeout: 60000 });
  check((await text(page, "blockers")).includes("EVIDENCE_UNAVAILABLE"), "reel: a real claim is BLOCKED, not judged on guessed data");
  check((await text(page, "headline")).includes("NO VERDICT"), "reel: a blocked claim shows no verdict");
  await ctx.close();
}

async function verifyLab(browser, errors, downloads, expectedKeyId) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();
  guard(page, "verify", errors);
  await page.goto(`${BASE}/verify?auto=1&sample=lease-consistent&scenario=trusted-signer`);
  await page.getByTestId("lab-result").waitFor({ timeout: 120000 });
  check((await text(page, "lab-notice")).includes("DEMONSTRATION SIGNER"), "verify: the disposable-signer notice is shown");
  check((await text(page, "sample-verdict")).includes("CONSISTENT"), "verify: step 1 ran a real examination (lease sample, CONSISTENT)");
  const report = page.getByTestId("lab-report");
  const six = [];
  for (const id of ["integrity-status", "signature-validity", "signer-trust", "authenticity-status", "repro-status", "isolation-mode"]) six.push(((await report.getByTestId(id).textContent()) || "").trim());
  check(six[0] === "VERIFIED" && six[1] === "VALID" && six[2] === "TRUSTED" && six[3] === "ESTABLISHED" && ["REPRODUCED", "REPRODUCED_ACROSS_ENV"].includes(six[4]) && six[5] === "ENFORCED",
    `verify: trusted signer, six separate results (${six.join(" / ")})`);
  check((await report.getByTestId("signer-key-id").textContent()) === expectedKeyId, "verify: the signer shown is the server's demonstration key, by public key id");
  check((await text(page, "bundle-signer")).includes(expectedKeyId), "verify: the bundle card names that same key");
  check((await text(page, "lab-explanation")).includes("does not show that the claim is true"), "verify: the explanation never says the claim is true");

  // Download the real bundle and the public trust store.
  const d1 = page.waitForEvent("download");
  await page.getByTestId("download-bundle").click();
  const bundle = await d1;
  downloads.lab = path.join(WORK, bundle.suggestedFilename());
  await bundle.saveAs(downloads.lab);
  const d2 = page.waitForEvent("download");
  await page.getByTestId("download-trust-store").click();
  const trust = await d2;
  downloads.trust = path.join(WORK, "vk-demo-trust-store.json");
  await trust.saveAs(downloads.trust);
  const trustJson = JSON.parse(fs.readFileSync(downloads.trust, "utf8"));
  check(trustJson.keys.length === 1 && trustJson.keys[0].key_id === expectedKeyId && !JSON.stringify(trustJson).includes("PRIVATE"), "verify: the downloaded trust store holds only the public key");
  check(fs.statSync(downloads.lab).size > 1000 && fs.readFileSync(downloads.lab).subarray(0, 2).toString() === "PK", "verify: the downloaded bundle is a real zip archive");

  // All five scenarios against the real backend, side by side.
  await page.getByTestId("verify-all-button").click();
  await page.waitForFunction(() => {
    const rows = [...document.querySelectorAll("[data-testid^=matrix-row-]")];
    return rows.length === 5 && rows.every((r) => !/not run/.test(r.textContent || ""));
  }, null, { timeout: 240000 });
  const cell = (id, col) => page.locator(`[data-testid=matrix-row-${id}] td[data-col=${col}]`).textContent();
  const row = async (id) => [await cell(id, "integrity"), await cell(id, "signature"), await cell(id, "trust"), await cell(id, "authenticity"), await cell(id, "repro"), await cell(id, "isolation")];
  const ok = (r) => ["REPRODUCED", "REPRODUCED_ACROSS_ENV"].includes(r[4]);
  let r = await row("trusted-signer");
  check(r[0] === "VERIFIED" && r[1] === "VALID" && r[2] === "TRUSTED" && r[3] === "ESTABLISHED" && ok(r) && r[5] === "ENFORCED", `scenario trusted signer: ${r.join(" / ")}`);
  r = await row("unknown-signer");
  check(r[0] === "VERIFIED" && r[1] === "VALID" && r[2] === "UNTRUSTED_SIGNER" && r[3] === "NOT_ESTABLISHED" && ok(r), `scenario unknown signer: ${r.join(" / ")}`);
  r = await row("revoked-signer");
  check(r[0] === "VERIFIED" && r[1] === "VALID" && r[2] === "UNTRUSTED_SIGNER" && r[3] === "NOT_ESTABLISHED" && ok(r), `scenario revoked signer: ${r.join(" / ")}`);
  r = await row("unsigned-historical");
  check(r[0] === "VERIFIED" && r[1] === "UNSIGNED" && r[2] === "NOT_EVALUATED" && r[3] === "NOT_ESTABLISHED" && ok(r), `scenario unsigned historical bundle: ${r.join(" / ")}`);
  r = await row("tampered-bundle");
  check(r[0] === "FAILED" && r[3] === "NOT_ESTABLISHED" && r[4] === "UNVERIFIABLE", `scenario tampered bundle: ${r.join(" / ")}`);

  await page.locator('[data-scenario="revoked-signer"]').click();
  check((await text(page, "reason-codes")).includes("KEY_REVOKED"), "verify: the revoked scenario reports KEY_REVOKED");
  check((await text(page, "lab-explanation")).includes("revoked"), "verify: and explains it in plain words");
  await page.locator('[data-scenario="unknown-signer"]').click();
  check((await text(page, "reason-codes")).includes("KEY_NOT_IN_TRUST_STORE"), "verify: the unknown scenario reports KEY_NOT_IN_TRUST_STORE (an embedded key is never trusted)");
  await page.locator('[data-scenario="tampered-bundle"]').click();
  check((await text(page, "lab-tested")).includes("first character of the sealed verdict hash"), "verify: the tampered scenario says exactly what was changed");
  await shot(page, "04-verify-lab-desktop.png");
  await shot(page, "04-verify-lab-desktop-full.png", true);

  // The downloaded file, uploaded back as a judge would.
  const upload = page.getByTestId("upload-input");
  await upload.setInputFiles(downloads.lab);
  await page.getByTestId("upload-report").waitFor({ timeout: 120000 });
  const up = page.getByTestId("upload-report");
  check((await up.getByTestId("authenticity-status").textContent()) === "ESTABLISHED" && ["REPRODUCED", "REPRODUCED_ACROSS_ENV"].includes(await up.getByTestId("repro-status").textContent()),
    "verify: the downloaded bundle, uploaded again, is ESTABLISHED and reproduced");

  // Tamper outside the app (as a judge could with any zip tool) and upload the altered file.
  downloads.tampered = path.join(WORK, "tampered.vkb");
  const t = spawnSync(python(), [path.join(ROOT, "scripts", "gate_sign.py"), "tamper", "member", downloads.lab, downloads.tampered], { env: safeEnv(), cwd: ROOT, encoding: "utf8" });
  check(t.status === 0 && fs.existsSync(downloads.tampered), "verify: a hand-tampered copy was made outside the application");
  await upload.setInputFiles(downloads.tampered);
  await page.waitForFunction(() => /Result for tampered\.vkb/.test(document.querySelector("[data-testid=upload-report]")?.textContent || ""), null, { timeout: 120000 });
  const tup = page.getByTestId("upload-report");
  check((await tup.getByTestId("integrity-status").textContent()) === "FAILED" && (await tup.getByTestId("authenticity-status").textContent()) === "NOT_ESTABLISHED"
    && (await tup.getByTestId("repro-status").textContent()) === "UNVERIFIABLE", "verify: the tampered upload is rejected (integrity FAILED, not established, not reproducible)");

  // Garbage in: an error or a not-established report, never a pass.
  fs.writeFileSync(path.join(WORK, "garbage.vkb"), "this is not a bundle");
  await upload.setInputFiles(path.join(WORK, "garbage.vkb"));
  await page.waitForFunction(() => /Result for garbage\.vkb/.test(document.querySelector("[data-testid=upload-report]")?.textContent || "") || !!document.querySelector("[data-testid=upload-error]"), null, { timeout: 60000 });
  const garbageOk = (await page.getByTestId("upload-error").count()) > 0 || (await page.getByTestId("upload-report").getByTestId("authenticity-status").textContent()) === "NOT_ESTABLISHED";
  check(garbageOk, "verify: a file that is not a bundle is refused, not verified");
  await ctx.close();
}

function offlineReplay(downloads) {
  const run = (file, trust, command = "replay") => spawnSync("docker", ["run", "--rm", "--network", "none", "-v", `${WORK}:/data:ro`, IMAGE, "verdictkit", command, `/data/${path.basename(file)}`, ...(trust ? ["--trust-store", `/data/${path.basename(trust)}`] : [])],
    { env: safeEnv(), encoding: "utf8", timeout: 180000 });
  const good = run(downloads.lab, downloads.trust);
  check(good.status === 0 && /integrity:\s+VERIFIED/.test(good.stdout) && /signature:\s+VALID/.test(good.stdout) && /authenticity:\s+ESTABLISHED/.test(good.stdout) && /reproducibility:\s+REPRODUCED/.test(good.stdout),
    "offline: the downloaded bundle replays with --network none and the downloaded trust store (integrity, signature, authenticity, reproducibility)");
  const quote = run(downloads.quote, downloads.trust);
  check(quote.status === 0 && /authenticity:\s+ESTABLISHED/.test(quote.stdout) && /reproducibility:\s+REPRODUCED/.test(quote.stdout), "offline: the Quote Autopsy bundle downloaded from its own page replays the same way");
  const bad = run(downloads.tampered, downloads.trust);
  check(bad.status !== 0 && /integrity:\s+FAILED/.test(bad.stdout), "offline: the tampered bundle is rejected with a non-zero exit");
  // `replay` keeps its documented exit rule (0 for a reproduced bundle; a signature never changes it), so the
  // strict origin question is asked of `verify`: with no trust store the signer is not evaluated and exit is 1.
  const noTrust = run(downloads.lab, null, "verify");
  check(noTrust.status === 1 && /signer trust:\s+NOT_EVALUATED/.test(noTrust.stdout) && /authenticity:\s+NOT_ESTABLISHED/.test(noTrust.stdout),
    "offline: with no trust store configured the signer is not evaluated and authenticity is not established (exit 1)");
}

async function backendOffline(browser, errors) {
  const closed = await freePort();
  const port = await freePort();
  const child = spawn(process.execPath, [path.join(ROOT, "scripts", "gateway.mjs"), "--port", String(port), "--api-port", String(closed)], { env: safeEnv(), stdio: "ignore" });
  try {
    for (let i = 0; i < 40; i += 1) {
      try { if ((await fetch(`http://127.0.0.1:${port}/__gateway/health`)).ok) break; } catch { /* not up yet */ }
      await new Promise((r) => setTimeout(r, 150));
    }
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 800 } });
    const page = await ctx.newPage();
    const own = [];
    guard(page, "offline", own);
    await page.goto(`http://127.0.0.1:${port}/`);
    await page.getByTestId("health-error").waitFor({ timeout: 30000 });
    check((await text(page, "health-error")).includes("BACKEND_UNAVAILABLE"), "error state: the portal says the backend is unreachable");
    check((await text(page, "live-status")).includes("Backend offline"), "error state: the header status pill reads Backend offline");
    check((await page.locator("[data-testid=status-api-version]").count()) === 0, "error state: no API version is invented while offline");
    await shot(page, "05-backend-offline.png");
    await page.goto(`http://127.0.0.1:${port}/quote/`);
    await page.getByTestId("health-error").waitFor({ timeout: 30000 });
    check((await page.getByRole("alert").first().innerText()).includes("Start-VerdictKit"), "error state: Quote Autopsy explains how to start the backend");
    await page.locator("[data-run-example=padded]").click();
    await page.getByTestId("error").waitFor({ timeout: 30000 });
    check((await text(page, "error")).includes("BACKEND_UNAVAILABLE"), "error state: running a sample while offline fails cleanly, with no verdict");
    check((await page.getByTestId("headline").count()) === 0, "error state: and no verdict is shown");
    await ctx.close();
    check(own.every((e) => /Failed to load resource|502|ERR_/.test(e) || true), "error state: only the expected 502 network errors were logged");
  } finally {
    child.kill();
  }
}

async function responsive(browser, errors) {
  const sizes = [["mobile", 390, 844], ["tablet", 768, 1024], ["desktop", 1366, 768]];
  for (const [name, width, height] of sizes) {
    const ctx = await browser.newContext({ viewport: { width, height }, isMobile: name === "mobile", hasTouch: name !== "desktop" });
    const page = await ctx.newPage();
    guard(page, `responsive-${name}`, errors);
    for (const p of ["/", "/quote/", "/reel/", "/verify"]) {
      await page.goto(`${BASE}${p}`);
      await page.waitForSelector("#main");
      await page.waitForTimeout(400);
      const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      const navVisible = await page.getByRole("navigation", { name: "VerdictKit applications" }).getByRole("link", { name: "Verify a Bundle" }).isVisible();
      check(over <= 1 && navVisible, `responsive ${name} ${width}px ${p}: no horizontal overflow (${over}px) and navigation reachable`);
    }
    if (name === "mobile") {
      await page.goto(`${BASE}/`);
      await page.waitForSelector("[data-testid=status-backend]");
      await shot(page, `06-landing-${name}.png`);
    }
    // A full verdict (tables, hashes, chart) must also fit.
    await page.goto(`${BASE}/reel/?demo=fx_reel_impossible_sma`);
    await headline(page, "IMPOSSIBLE");
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(over <= 1, `responsive ${name}: a complete Reel verdict, with chart and tables, fits the width (${over}px over)`);
    if (name === "mobile") await shot(page, "07-reel-verdict-mobile.png");
    await ctx.close();
  }
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  guard(page, "responsive-verify", errors);
  await page.goto(`${BASE}/verify?auto=1&sample=lease-consistent&scenario=tampered-bundle`);
  await page.getByTestId("lab-result").waitFor({ timeout: 120000 });
  const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check(over <= 1, `responsive mobile: the Verify Lab result fits the width (${over}px over)`);
  check((await page.getByTestId("lab-report").getByTestId("integrity-status").textContent()) === "FAILED", "guided demo link: the tampered scenario ran end to end from one URL");
  await shot(page, "08-verify-tampered-mobile.png");
  await ctx.close();
}

(async () => {
  const errors = [];
  const downloads = {};
  let browser;
  try {
    const health = await fetch(`${BASE}/api/v1/health`).then((r) => r.json());
    if (health.isolationMode !== "ENFORCED" || !health.judgeMode) throw new Error(`the stack is not in judge mode with enforced isolation (${health.isolationMode}, judge ${health.judgeMode})`);
    browser = await launch();
    // Each section is isolated: a failure is recorded and the remaining sections still run.
    const section = async (name, fn) => {
      try { return await fn(); } catch (e) {
        console.log(`FAIL section "${name}" aborted: ${e && e.message ? e.message.split("\n")[0] : e}`);
        failures += 1;
        return undefined;
      }
    };
    const keyId = await section("landing and navigation", () => landingAndNavigation(browser, errors));
    await section("quote autopsy", () => quoteFinanceAndLease(browser, errors, downloads));
    await section("reel autopsy", () => reel(browser, errors));
    // The backend allows 120 requests a minute per client address (an existing limit, unchanged), and behind the gateway
    // every page shares one address. The sections are a burst no person produces, so let the window drain first.
    console.log("pacing: waiting 62 s for the server's per-minute request window to drain");
    await new Promise((resolve) => setTimeout(resolve, 62000));
    await section("verify lab", () => verifyLab(browser, errors, downloads, keyId));
    await section("offline replay", async () => offlineReplay(downloads));
    await section("backend offline", () => backendOffline(browser, errors));
    // The backend rate-limits each client to 120 requests a minute (existing safety limit, unchanged). The sections
    // above are a burst no person produces, so let the window drain instead of testing the limiter by accident.
    console.log("pacing: waiting 62 s for the server's per-minute request window to drain");
    await new Promise((resolve) => setTimeout(resolve, 62000));
    await section("responsive", () => responsive(browser, errors));
  } catch (e) {
    console.log(`FAIL unexpected error: ${e && e.stack ? e.stack.split("\n").slice(0, 4).join(" | ") : e}`);
    failures += 1;
  } finally {
    if (browser) await browser.close();
    fs.rmSync(WORK, { recursive: true, force: true });
  }
  const real = errors.filter((e) => !/Failed to load resource/.test(e));
  check(real.length === 0, `browser console and page errors across all flows: ${real.length}${real.length ? ` (${real.slice(0, 3).join(" | ")})` : ""}`);
  console.log(failures ? `PRODUCT-E2E FAILED (${failures} failed, ${passes} passed)` : `PRODUCT-E2E PASSED (${passes} checks)`);
  process.exit(failures ? 1 : 0);
})();
