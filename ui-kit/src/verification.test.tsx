import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { VerificationReport, type VerificationInput } from "./verification";
import { explainOutcome, fmtNumber, STATUS_MEANING, statusTone, VerdictHero, VerdictView } from "./components";
import { explainError, LiveStatus } from "./shell";
import type { OutcomeResponse } from "./types";
import completed from "../../api/examples/outcome_completed_quote.json";

const KEY = "ab".repeat(32);
const base: VerificationInput = {
  integrity: { status: "VERIFIED", checks: [{ check: "MANIFEST_HASHES", ok: true }, { check: "LEDGER_CHAIN", ok: true }] },
  reproducibility: { status: "REPRODUCED", originalVerdictHash: "11".repeat(32), replayedVerdictHash: "11".repeat(32), envMatch: true },
  authenticity: {
    status: "ESTABLISHED", note: "A trusted signer signed these exact manifest bytes.", signatureValidity: "VALID",
    signerTrust: "TRUSTED", reasonCodes: [], signer: { keyId: KEY, algorithm: "ed25519" },
    trustStore: { formatVersion: 1, serial: 1, sha256: "cd".repeat(32), evaluatedAt: "2026-12-01T00:00:00Z" },
  },
};

describe("VerificationReport", () => {
  it("shows the six results as six separate values", () => {
    render(<VerificationReport report={base} isolationMode="ENFORCED" testId="r" />);
    const t = (id: string) => screen.getByTestId(id).textContent;
    expect([t("integrity-status"), t("signature-validity"), t("signer-trust"), t("authenticity-status"), t("repro-status"), t("isolation-mode")])
      .toEqual(["VERIFIED", "VALID", "TRUSTED", "ESTABLISHED", "REPRODUCED", "ENFORCED"]);
    expect(screen.getByTestId("signer-key-id").textContent).toBe(KEY);
  });

  it("a tampered bundle: valid signature and trusted signer do not rescue failed integrity", () => {
    const tampered: VerificationInput = {
      integrity: { status: "FAILED", checks: [{ check: "MANIFEST_HASHES", ok: false }, { check: "LEDGER_CHAIN", ok: true }] },
      reproducibility: { ...base.reproducibility, status: "UNVERIFIABLE", replayedVerdictHash: null, envMatch: null },
      authenticity: { ...base.authenticity, status: "NOT_ESTABLISHED", reasonCodes: ["INTEGRITY_NOT_VERIFIED"] },
    };
    render(<VerificationReport report={tampered} isolationMode="ENFORCED" testId="r" />);
    expect(screen.getByTestId("integrity-status").textContent).toBe("FAILED");
    expect(screen.getByTestId("signature-validity").textContent).toBe("VALID");
    expect(screen.getByTestId("authenticity-status").textContent).toBe("NOT_ESTABLISHED");
    expect(screen.getByTestId("repro-status").textContent).toBe("UNVERIFIABLE");
    expect(screen.getByTestId("reason-codes").textContent).toContain("INTEGRITY_NOT_VERIFIED");
  });

  it("an unknown signer is VALID but UNTRUSTED_SIGNER, with the reason in plain words", () => {
    const unknown: VerificationInput = {
      ...base, authenticity: { ...base.authenticity, status: "NOT_ESTABLISHED", signerTrust: "UNTRUSTED_SIGNER", reasonCodes: ["KEY_NOT_IN_TRUST_STORE"] },
    };
    render(<VerificationReport report={unknown} isolationMode={null} testId="r" />);
    expect(screen.getByTestId("signer-trust").textContent).toBe("UNTRUSTED_SIGNER");
    expect(screen.getByTestId("reason-codes").textContent).toContain("trust store does not list this key");
    expect(within(screen.getByTestId("r")).getByTestId("isolation-mode").textContent).toBe("UNKNOWN");
  });
});

describe("verdict presentation", () => {
  it("explains every result word and keeps internal contradictions apart from external refutations", () => {
    for (const status of ["CONSISTENT", "CONTRADICTED", "SUPPORTED", "REFUTED", "CONDITIONAL", "WITHIN_BOUND", "IMPOSSIBLE", "INDETERMINATE"]) {
      expect(STATUS_MEANING[status].plain.length).toBeGreaterThan(20);
    }
    expect(STATUS_MEANING.CONTRADICTED.kind).toBe("Internal arithmetic");
    expect(STATUS_MEANING.REFUTED.kind).toBe("External evidence");
    expect(statusTone("INDETERMINATE")).toBe("warn");
  });

  it("the toe tag carries the result word, its meaning and the run facts", () => {
    render(<VerdictHero outcome={completed as unknown as OutcomeResponse} />);
    const text = screen.getByTestId("headline").textContent ?? "";
    expect(text).toContain("CONTRADICTED");
    expect(text).toContain("Internal arithmetic");
    expect(text).toMatch(/execution COMPLETED/);
    expect(text).toMatch(/isolation (ENFORCED|UNENFORCED)/);
  });

  it("formats decimal strings exactly, without converting to a float", () => {
    expect(fmtNumber("1234567.89")).toBe("1,234,567.89");
    expect(fmtNumber("-24393.63")).toBe("-24,393.63");
    expect(fmtNumber("0.00125")).toBe("0.00125");
    expect(fmtNumber("12345678901234567890.123456789")).toBe("12,345,678,901,234,567,890.123456789");
    expect(fmtNumber(null)).toBe("—");
    expect(fmtNumber("n/a")).toBe("n/a");
  });
});

describe("LiveStatus", () => {
  const health = { contractVersion: "1.2.0", status: "ok" as const, isolationMode: "ENFORCED" as const, judgeMode: true, engineVersion: "0.1.0" };
  it("reads only what the API returned", () => {
    const { rerender } = render(<LiveStatus health={health} error={null} loading={false} />);
    expect(screen.getByTestId("live-status").textContent).toBe("API 1.2.0 · isolation ENFORCED");
    rerender(<LiveStatus health={null} error="BACKEND_UNAVAILABLE: x" loading={false} />);
    expect(screen.getByTestId("live-status").textContent).toBe("Backend offline");
    rerender(<LiveStatus health={null} error={null} loading={true} />);
    expect(screen.getByTestId("live-status").textContent).toBe("Connecting…");
  });
  it("does not call a rate-limited server offline", () => {
    render(<LiveStatus health={null} error="RATE_LIMITED: Request rate limit exceeded" loading={false} />);
    expect(screen.getByTestId("live-status").textContent).toMatch(/rate limited/);
    expect(screen.getByTestId("live-status").textContent).not.toMatch(/offline/);
  });
});

// Test inputs only: shaped like API responses so the explanation logic can be checked without a server.
function outcome(status: OutcomeResponse["headline"]["status"], over: Partial<OutcomeResponse> = {}): OutcomeResponse {
  return { ...(completed as unknown as OutcomeResponse), headline: { status, confidenceClass: null }, findings: [], diagnostics: null, sensitivity: null, ...over };
}
const finding = (id: string, st: string, extra: object = {}) => ({
  findingId: id, status: st, confidenceClass: null, confidenceScope: null, statement: `${id} statement`, reason: null,
  numbers: { expected: "100.00", observed: "140.00", difference: "40.00", tolerance: "0.01" }, evidenceIds: [], assumptionDependencies: [],
  gridPointsEvaluated: 4, keyRecordIds: [], ...extra,
}) as OutcomeResponse["findings"][number];

describe("explainOutcome", () => {
  it("gives a passing verdict no explanation", () => {
    expect(explainOutcome(outcome("CONSISTENT", { findings: [finding("a", "CONSISTENT")] }))).toBeNull();
    expect(explainOutcome(outcome("SUPPORTED"))).toBeNull();
  });

  it("explains a contradiction from the engine's own diagnostic, and says it is not about outside facts", () => {
    const why = explainOutcome(outcome("CONTRADICTED", {
      findings: [finding("amount_financed", "CONTRADICTED", { pointOfFailure: true })],
      diagnostics: { computedAfterReveal: true, affectsVerdict: false, items: [{
        firstBrokenLine: "amount_financed",
        localChecks: [
          { line: "sales_tax", stated: "1415.63", fromStatedPredecessors: "1415.63", difference: "0.00", consistent: true },
          { line: "amount_financed", stated: "24793.63", fromStatedPredecessors: "24393.63", difference: "400.00", consistent: false },
          { line: "monthly_payment", stated: "421.52", fromStatedPredecessors: "421.52", difference: "0.00", consistent: true }],
        paymentPacking: { impliedAmountFinanced: "24793.7940", inversionUncertainty: "0.2941", itemisedAmountFinanced: "24393.63", unexplainedAmount: "400.1640" } }] },
    }))!;
    const text = why.paragraphs.join(" ");
    expect(why.title).toMatch(/contradicts itself/);
    expect(text).toContain("first line that breaks is amount financed");
    expect(text).toContain("24,793.63");
    expect(text).toContain("24,393.63");
    expect(text).toContain("400.00");
    expect(text).toContain("2 other lines follow correctly");
    expect(text).toContain("400.1640");
    expect(text).toMatch(/not a finding about outside facts/);
  });

  it("explains a conditional result with the counts the sensitivity grid reported", () => {
    const why = explainOutcome(outcome("CONDITIONAL", {
      findings: [finding("total_return_pct", "CONDITIONAL", { assumptionDependencies: ["fee_bps_per_side"] })],
      sensitivity: { templateVersion: "1", gridCap: 64, variantsExecuted: 16, axes: [], results: [{ findingId: "total_return_pct", aggregate: "MIXED", passCount: 4, failCount: 12, cells: [] }] },
    }))!;
    expect(why.paragraphs[0]).toContain("holds at 4 of 16 grid points verified and fails at 12");
    expect(why.paragraphs[0]).toContain("fee_bps_per_side");
    expect(why.paragraphs.at(-1)).toMatch(/not a failure/);
  });

  it("explains an impossible claim with the ceiling and the amount above it, and never accuses", () => {
    const why = explainOutcome(outcome("IMPOSSIBLE", { findings: [finding("total_return_bound", "IMPOSSIBLE", {
      numbers: { expected: "2872.54378305", observed: "3400", difference: "527.45621695", tolerance: "0.5" } })] }))!;
    expect(why.paragraphs[0]).toContain("2,872.54378305");
    expect(why.paragraphs[0]).toContain("527.45621695 above it");
    expect(why.paragraphs[1]).toMatch(/does not say the claimant lied/);
  });

  it("lists other uncertain findings alongside the headline instead of hiding them", () => {
    const why = explainOutcome(outcome("CONTRADICTED", { findings: [finding("a", "CONTRADICTED", { pointOfFailure: true }), finding("b", "INDETERMINATE", { reason: "NO_EVIDENCE" })] }))!;
    expect(why.uncertain).toEqual(["b is INDETERMINATE: b statement (NO_EVIDENCE)"]);
  });

  it("renders into the verdict view, in plain text, only for non-passing verdicts", () => {
    const { rerender } = render(<VerdictView outcome={outcome("IMPOSSIBLE", { findings: [finding("total_return_bound", "IMPOSSIBLE")] })} />);
    expect(screen.getByTestId("why-verdict").textContent).toMatch(/ceiling/);
    rerender(<VerdictView outcome={outcome("CONSISTENT", { findings: [finding("a", "CONSISTENT")] })} />);
    expect(screen.queryByTestId("why-verdict")).toBeNull();
  });
});

describe("explainError", () => {
  it("gives a start-up hint when the backend is unreachable", () => {
    expect(explainError("BACKEND_UNAVAILABLE: API backend is unavailable").hint).toMatch(/Start-VerdictKit/);
    expect(explainError("PRIVACY_REJECTED: no").title).toMatch(/personal identifiers/);
  });
});
