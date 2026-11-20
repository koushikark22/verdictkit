import { describe, expect, it } from "vitest";
import { ApiError, BlockedError, ContractMismatchError, createClient, parseSseFrame } from "./api";

function respond(status: number, body: unknown) {
  return async () => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("client", () => {
  it("refuses any other contract version", async () => {
    const c = createClient("/api/v1", respond(200, { contractVersion: "2.0.0", status: "ok" }) as any);
    await expect(c.health()).rejects.toBeInstanceOf(ContractMismatchError);
  });

  it("maps the error envelope", async () => {
    const c = createClient("/api/v1", respond(422, { contractVersion: "1.1.0",
      error: { code: "PRIVACY_REJECTED", message: "no", field: "pastedText" } }) as any);
    const err = await c.createCase({ claimType: "reel.mechanical.v1", dataMode: "LIVE_EVIDENCE" }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("PRIVACY_REJECTED");
    expect(err.field).toBe("pastedText");
  });

  it("distinguishes a BLOCKED response from an error", async () => {
    const c = createClient("/api/v1", respond(422, { contractVersion: "1.1.0", caseId: "case_x",
      executionStatus: "BLOCKED", blockers: [{ code: "EVIDENCE_UNAVAILABLE", message: "m" }] }) as any);
    const err = await c.acquireEvidence("case_x").catch((e) => e);
    expect(err).toBeInstanceOf(BlockedError);
    expect(err.blockers[0].code).toBe("EVIDENCE_UNAVAILABLE");
  });

  it("encodes path segments", () => {
    const c = createClient();
    expect(c.bundleUrl("../x")).toBe("/api/v1/cases/..%2Fx/bundle");
  });
});

describe("parseSseFrame", () => {
  it("parses a persisted progress event", () => {
    const e = parseSseFrame('id: 3\nevent: progress\ndata: {"contractVersion":"1.1.0","runId":"r","seq":3,"stage":"VERDICT_SEALED","at":"t","ledgerSeq":6,"ledgerKind":"VERDICT_SEALED","detail":{}}');
    expect(e!.seq).toBe(3);
    expect(parseSseFrame(": keep-alive")).toBeNull();
    expect(() => parseSseFrame('data: {"contractVersion":"9"}')).toThrow(ContractMismatchError);
  });
});
