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
    const c = createClient("/api/v1", respond(422, { contractVersion: "1.2.0",
      error: { code: "PRIVACY_REJECTED", message: "no", field: "pastedText" } }) as any);
    const err = await c.createCase({ claimType: "reel.mechanical.v1", dataMode: "LIVE_EVIDENCE" }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("PRIVACY_REJECTED");
    expect(err.field).toBe("pastedText");
  });

  it("distinguishes a BLOCKED response from an error", async () => {
    const c = createClient("/api/v1", respond(422, { contractVersion: "1.2.0", caseId: "case_x",
      executionStatus: "BLOCKED", blockers: [{ code: "EVIDENCE_UNAVAILABLE", message: "m" }] }) as any);
    const err = await c.acquireEvidence("case_x").catch((e) => e);
    expect(err).toBeInstanceOf(BlockedError);
    expect(err.blockers[0].code).toBe("EVIDENCE_UNAVAILABLE");
  });

  it("encodes path segments", () => {
    const c = createClient();
    expect(c.bundleUrl("../x")).toBe("/api/v1/cases/..%2Fx/bundle");
  });

  it("reports an unreachable backend as such, not as a contract mismatch", async () => {
    const c = createClient("/api/v1", respond(502, { error: { code: "BACKEND_UNAVAILABLE", message: "API backend is unavailable" } }) as any);
    const err = await c.health().catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("BACKEND_UNAVAILABLE");
  });

  it("sends only a scenario name and the bundle bytes to the demo lab, never a key or trust store", async () => {
    let seen: { url: string; init: RequestInit } | null = null;
    const fetchImpl = (async (url: string, init: RequestInit) => {
      seen = { url, init };
      return new Response(JSON.stringify({ contractVersion: "1.2.0" }), { status: 200 });
    }) as any;
    const bundle = new Blob([new Uint8Array([80, 75, 3, 4])]);
    await createClient("/api/v1", fetchImpl).demoVerify("revoked-signer", bundle);
    expect(seen!.url).toBe("/api/v1/demo/verify?scenario=revoked-signer");
    expect(seen!.init.method).toBe("POST");
    expect(seen!.init.body).toBe(bundle);
    expect(JSON.stringify(seen!.init.headers)).not.toMatch(/key|trust/i);
  });
});

describe("parseSseFrame", () => {
  it("parses a persisted progress event", () => {
    const e = parseSseFrame('id: 3\nevent: progress\ndata: {"contractVersion":"1.2.0","runId":"r","seq":3,"stage":"VERDICT_SEALED","at":"t","ledgerSeq":6,"ledgerKind":"VERDICT_SEALED","detail":{}}');
    expect(e!.seq).toBe(3);
    expect(parseSseFrame(": keep-alive")).toBeNull();
    expect(() => parseSseFrame('data: {"contractVersion":"9"}')).toThrow(ContractMismatchError);
  });
});
