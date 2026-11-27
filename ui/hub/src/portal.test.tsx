import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Client, DemoStatus, DemoVerifyReport, Health } from "@verdictkit/ui-kit";
import { explainReport } from "./explain";
import { IsolationDiagram, Landing } from "./Landing";
import { LAB_SAMPLES, QUOTE_DEMOS, REEL_DEMOS, SCENARIO_ORDER, VERIFY_DEMOS } from "./samples";
import { VerifyLab } from "./VerifyLab";

// Fixtures in this file stand in for server responses so that rendering and wiring can be tested
// without a server. They are test inputs only; no product screen ever uses them.
const KEY = "ab".repeat(32);
const health: Health = { contractVersion: "1.2.0", status: "ok", isolationMode: "ENFORCED", judgeMode: true, engineVersion: "0.1.0" };
const profile = (id: string, status: "ACTIVE" | "REVOKED" = "ACTIVE") => ({
  id, label: `${id} verifier`, description: `profile ${id}`, trustStore: { serial: 1, sha256: "cd".repeat(32), keys: [{ keyId: KEY, status }] },
});
const lab: DemoStatus = {
  contractVersion: "1.2.0", enabled: true, demonstrationNotice: "DEMONSTRATION SIGNER: a disposable Ed25519 key.",
  signer: { keyId: KEY, algorithm: "ed25519", disposable: true }, isolationMode: "ENFORCED", judgeMode: true,
  verifierProfiles: [profile("trusted"), profile("unknown"), profile("revoked", "REVOKED")],
  scenarios: SCENARIO_ORDER.map((id) => ({ id, label: id.replace(/-/g, " "), profile: id === "unknown-signer" ? "unknown" : id === "revoked-signer" ? "revoked" : "trusted",
    transform: id === "unsigned-historical" ? "strip-signature" : id === "tampered-bundle" ? "tamper-verdict" : "none", setup: `setup for ${id}` })),
};
const noop = () => undefined;

function report(scenarioId: (typeof SCENARIO_ORDER)[number]): DemoVerifyReport {
  const scenario = lab.scenarios.find((s) => s.id === scenarioId)!;
  return {
    contractVersion: "1.2.0", notes: [],
    integrity: { status: "VERIFIED", checks: [{ check: "MANIFEST_HASHES", ok: true }] },
    reproducibility: { status: "REPRODUCED", originalVerdictHash: "11".repeat(32), replayedVerdictHash: "11".repeat(32), envMatch: true },
    authenticity: { status: "ESTABLISHED", note: "ok", signatureValidity: "VALID", signerTrust: "TRUSTED", reasonCodes: [],
      signer: { keyId: KEY, algorithm: "ed25519" }, trustStore: { formatVersion: 1, serial: 1, sha256: "cd".repeat(32), evaluatedAt: "t" } },
    demo: { scenario, verifierProfile: lab.verifierProfiles[0], isolationMode: "ENFORCED",
      tested: { sha256: "ef".repeat(32), sizeBytes: 4, transform: scenario.transform, description: "Not modified." } },
  };
}

describe("explainReport", () => {
  const base = report("trusted-signer");
  it("never says that a claim is true, and tells the five situations apart", () => {
    const established = explainReport(base);
    expect(established).toMatch(/does not show that the claim is true/);
    const tampered = explainReport({ ...base, integrity: { status: "FAILED", checks: [] } });
    expect(tampered).toMatch(/no longer match/);
    const unsigned = explainReport({ ...base, authenticity: { ...base.authenticity, status: "NOT_ESTABLISHED", signatureValidity: "UNSIGNED", signerTrust: "NOT_EVALUATED", signer: null } });
    expect(unsigned).toMatch(/Nothing in this bundle says who made it/);
    const unknown = explainReport({ ...base, authenticity: { ...base.authenticity, status: "NOT_ESTABLISHED", signerTrust: "UNTRUSTED_SIGNER", reasonCodes: ["KEY_NOT_IN_TRUST_STORE"] } });
    expect(unknown).toMatch(/never trusted on its own/);
    const revoked = explainReport({ ...base, authenticity: { ...base.authenticity, status: "NOT_ESTABLISHED", signerTrust: "UNTRUSTED_SIGNER", reasonCodes: ["KEY_REVOKED"] } });
    expect(revoked).toMatch(/revoked/);
  });
});

describe("Landing", () => {
  const props = { loading: false, checkedAt: "10:00:00 UTC", onRetry: noop, lab, labError: null };
  it("shows only what the backend reported: connection, API version, isolation, signer", () => {
    render(<Landing {...props} health={health} healthError={null} />);
    expect(screen.getByTestId("status-backend").textContent).toBe("CONNECTED");
    expect(screen.getByTestId("status-api-version").textContent).toBe("1.2.0");
    expect(screen.getByTestId("status-isolation").textContent).toBe("ENFORCED");
    expect(screen.getByTestId("status-signer").textContent).toBe("SIGNING ON");
    expect(screen.getByTestId("status-key-id").textContent).toBe(KEY);
  });

  it("says plainly that the backend is unreachable, and invents no numbers", () => {
    render(<Landing {...props} health={null} healthError="BACKEND_UNAVAILABLE: API backend is unavailable" lab={null} />);
    expect(screen.getByRole("alert").textContent).toMatch(/Backend not reachable/);
    expect(screen.getByTestId("health-error").textContent).toMatch(/BACKEND_UNAVAILABLE/);
    expect(screen.queryByTestId("status-api-version")).toBeNull();
  });

  it("reports UNENFORCED isolation and a lab that is not enabled instead of hiding them", () => {
    render(<Landing {...props} health={{ ...health, isolationMode: "UNENFORCED", judgeMode: false }} healthError={null} lab={null} labError="The demonstration lab is not enabled on this server." />);
    expect(screen.getByTestId("status-isolation").textContent).toBe("UNENFORCED");
    expect(screen.getByTestId("status-signer").textContent).toBe("NOT ENABLED");
  });

  it("links straight to every guided demonstration", () => {
    render(<Landing {...props} health={health} healthError={null} />);
    const demos = within(screen.getByTestId("guided-demos"));
    for (const d of [...QUOTE_DEMOS, ...REEL_DEMOS]) {
      expect(demos.getByRole("link", { name: d.title }).getAttribute("href")).toBe(d.href);
    }
    expect(VERIFY_DEMOS.map((d) => d.scenario)).toEqual(SCENARIO_ORDER);
    for (const d of VERIFY_DEMOS) expect(demos.getByRole("link", { name: d.title }).getAttribute("href")).toContain(`scenario=${d.scenario}`);
  });
});

describe("IsolationDiagram", () => {
  it("draws a solid wall only when the server reports ENFORCED, and says so when it reports nothing", () => {
    const { rerender } = render(<IsolationDiagram health={health} lab={lab} />);
    expect(document.querySelector(".vk-wall")!.className).toBe("vk-wall ");
    expect(screen.getByLabelText("Isolation boundary").textContent).toMatch(/enforces the boundary/);
    expect(screen.getByTestId("diagram-signer").textContent).toContain(KEY.slice(0, 16));
    rerender(<IsolationDiagram health={{ ...health, isolationMode: "UNENFORCED" }} lab={null} />);
    expect(document.querySelector(".vk-wall")!.className).toContain("vk-warn");
    expect(screen.getByLabelText("Isolation boundary").textContent).toMatch(/WITHOUT OS-level separation/);
    expect(screen.getByTestId("diagram-signer").textContent).toMatch(/No signing key is reported/);
    rerender(<IsolationDiagram health={null} lab={null} />);
    expect(document.querySelector(".vk-wall")!.className).toContain("vk-unknown");
    expect(screen.getByLabelText("Isolation boundary").textContent).toMatch(/not reachable, so the boundary is not reported/);
  });
});

describe("samples", () => {
  it("builds real intake bodies from the applications' own sample data", () => {
    expect(LAB_SAMPLES.map((s) => s.intake.claimType)).toEqual(["quote.lease.v1", "quote.lease.v1", "reel.mechanical.v1", "reel.mechanical.v1"]);
    const lease = LAB_SAMPLES[0].intake.form!;
    expect(lease.params.adjusted_cap_cost).toBe("30000.00");
    expect(lease.outcomes.rent_charge).toBe("60.00");
    expect(LAB_SAMPLES[2].intake).toMatchObject({ dataMode: "SYNTHETIC_DEMO", fixtureId: "fx_reel_impossible_sma" });
    expect(QUOTE_DEMOS.map((d) => d.id)).toEqual(["consistent", "padded", "lease-consistent", "lease-padded"]);
    expect(REEL_DEMOS.map((d) => d.id)).toEqual(["fx_reel_supported_hold", "fx_reel_conditional_sma", "fx_reel_impossible_sma"]);
  });
});

describe("VerifyLab", () => {
  beforeEach(() => window.history.replaceState({}, "", "/verify?caseId=case_abc"));

  function fakeClient(demoVerify: Client["demoVerify"]): Client {
    const blob = new Blob([new Uint8Array([80, 75, 3, 4])]);
    return {
      bundleMetadata: async () => ({
        contractVersion: "1.2.0", caseId: "case_abc", bundleSha256: "aa".repeat(32), sizeBytes: 4, engineVersion: "0.1.0",
        envFingerprint: { engineVersion: "0.1.0", pythonVersion: "3.12", lockfileSha256: "x", imageDigest: "y" },
        isolationMode: "ENFORCED", embeddedEvidence: [], refetchOnlyEvidence: [], replayCommand: "verdictkit replay case_abc.vkb",
        integrity: report("trusted-signer").integrity, reproducibility: { ...report("trusted-signer").reproducibility, status: "NOT_RUN" },
        authenticity: report("trusted-signer").authenticity,
      }),
      bundleBytes: async () => blob, bundleUrl: (id: string) => `/api/v1/cases/${id}/bundle`,
      demoTrustStoreUrl: () => "/api/v1/demo/trust-store", demoVerify,
    } as unknown as Client;
  }

  it("sends only the scenario name and the downloaded bundle bytes, then shows six separate results", async () => {
    const demoVerify = vi.fn(async (id: string) => report(id as (typeof SCENARIO_ORDER)[number]));
    render(<VerifyLab client={fakeClient(demoVerify as unknown as Client["demoVerify"])} health={health} lab={lab} labError={null} image="verdictkit:batch2" />);
    await waitFor(() => expect(screen.getByTestId("bundle-card").textContent).toContain("case_abc.vkb"));
    expect(screen.getByTestId("download-bundle").getAttribute("href")).toBe("/api/v1/cases/case_abc/bundle");
    expect(screen.getByTestId("offline-command").textContent).toContain("--network none");
    expect(screen.getByTestId("offline-command").textContent).toContain("verdictkit:batch2");

    fireEvent.click(document.querySelector('[data-scenario="tampered-bundle"]')!);
    fireEvent.click(screen.getByTestId("verify-button"));
    await waitFor(() => expect(screen.getByTestId("lab-result")).toBeTruthy());
    expect(demoVerify).toHaveBeenCalledTimes(1);
    const [scenarioArg, bundleArg] = demoVerify.mock.calls[0] as unknown as [string, Blob];
    expect(scenarioArg).toBe("tampered-bundle");
    expect(bundleArg).toBeInstanceOf(Blob);
    const report6 = within(screen.getByTestId("lab-report"));
    expect(report6.getAllByText(/^(VERIFIED|VALID|TRUSTED|ESTABLISHED|REPRODUCED|ENFORCED)$/)).toHaveLength(6);
    expect(screen.getByTestId("matrix-row-tampered-bundle")).toBeTruthy();
    expect(screen.getByTestId("matrix-row-trusted-signer").textContent).toContain("not run");
  });

  it("shows a failed verification as an error, never as a result", async () => {
    const demoVerify = vi.fn(async () => { throw new Error("boom"); });
    render(<VerifyLab client={fakeClient(demoVerify as unknown as Client["demoVerify"])} health={health} lab={lab} labError={null} image="x" />);
    await waitFor(() => expect(screen.getByTestId("verify-button").hasAttribute("disabled")).toBe(false));
    fireEvent.click(screen.getByTestId("verify-button"));
    await waitFor(() => expect(screen.getByTestId("lab-error")).toBeTruthy());
    expect(screen.queryByTestId("lab-report")).toBeNull();
  });

  it("without the lab, scenario verification is unavailable and the reason is stated", () => {
    render(<VerifyLab client={fakeClient(vi.fn() as unknown as Client["demoVerify"])} health={health} lab={null} labError="The demonstration lab is not enabled on this server." image="x" />);
    expect(screen.getByTestId("lab-disabled").textContent).toMatch(/not enabled/);
    expect(screen.getByTestId("verify-button").hasAttribute("disabled")).toBe(true);
  });
});
