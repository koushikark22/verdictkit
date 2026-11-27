import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BundlePanel } from "./components";
import type { Client } from "./api";
import type { BundleMetadata } from "./types";
import metadata from "../../api/examples/bundle_metadata.json";

// api/examples/bundle_metadata.json is the contract's schema-valid placeholder (an unsigned
// bundle). The signed variants below change only the authenticity object, as the contract allows.
const base = metadata as unknown as BundleMetadata;
const KEY_ID = "ab".repeat(32);

function clientFor(authenticity: BundleMetadata["authenticity"]): Client {
  return {
    bundleMetadata: async () => ({ ...base, authenticity }),
    bundleUrl: () => "/bundle",
    bundleBytes: async () => new ArrayBuffer(0),
    replay: async () => ({ ...base, notes: [] }),
  } as unknown as Client;
}

describe("BundlePanel authenticity", () => {
  it("shows an unsigned bundle as UNSIGNED, not evaluated, not established", async () => {
    render(<BundlePanel client={clientFor(base.authenticity)} caseId="case_x" />);
    await waitFor(() => expect(screen.getByTestId("signature-validity")).toBeTruthy());
    expect(screen.getByTestId("signature-validity").textContent).toBe("UNSIGNED");
    expect(screen.getByTestId("signer-trust").textContent).toBe("NOT_EVALUATED");
    expect(screen.getByTestId("authenticity-status").textContent).toBe("NOT_ESTABLISHED");
  });

  it("keeps signature validity, signer trust and authenticity as three separate results", async () => {
    const validButUntrusted: BundleMetadata["authenticity"] = {
      status: "NOT_ESTABLISHED", note: "The signature is valid, but this operator's trust store does not accept the signer.",
      signatureValidity: "VALID", signerTrust: "UNTRUSTED_SIGNER", reasonCodes: ["KEY_NOT_IN_TRUST_STORE"],
      signer: { keyId: KEY_ID, algorithm: "ed25519" }, trustStore: null,
    };
    render(<BundlePanel client={clientFor(validButUntrusted)} caseId="case_x" />);
    await waitFor(() => expect(screen.getByTestId("signature-validity")).toBeTruthy());
    expect(screen.getByTestId("signature-validity").textContent).toBe("VALID");
    expect(screen.getByTestId("signer-trust").textContent).toBe("UNTRUSTED_SIGNER");
    expect(screen.getByTestId("authenticity-status").textContent).toBe("NOT_ESTABLISHED");
    expect(screen.getByTestId("bundle").textContent).toContain(KEY_ID);
    expect(screen.getByTestId("bundle").textContent).toContain("KEY_NOT_IN_TRUST_STORE");
  });

  it("only a trusted valid signature reads as ESTABLISHED, and the page never claims the claim is true", async () => {
    const established: BundleMetadata["authenticity"] = {
      status: "ESTABLISHED", note: "A trusted signer signed these exact manifest bytes and integrity is verified.",
      signatureValidity: "VALID", signerTrust: "TRUSTED", reasonCodes: [],
      signer: { keyId: KEY_ID, algorithm: "ed25519" },
      trustStore: { formatVersion: 1, serial: 3, sha256: "cd".repeat(32), evaluatedAt: "2026-12-01T00:00:00Z" },
    };
    render(<BundlePanel client={clientFor(established)} caseId="case_x" />);
    await waitFor(() => expect(screen.getByTestId("authenticity-status")).toBeTruthy());
    expect(screen.getByTestId("authenticity-status").textContent).toBe("ESTABLISHED");
    const text = screen.getByTestId("bundle").textContent ?? "";
    expect(text).toContain("never shows that the claim is true");
    expect(text).not.toContain("unsigned in v1");
  });
});
