import { describe, expect, it } from "vitest";
import { DEMO_FIXTURES, demoIntake, emptyReel, liveIntake } from "./intake";

describe("demo intake", () => {
  it("sends only a bundled fixture id in SYNTHETIC_DEMO", () => {
    const body = demoIntake(DEMO_FIXTURES[0].id);
    expect(body).toEqual({ claimType: "reel.mechanical.v1", dataMode: "SYNTHETIC_DEMO", fixtureId: DEMO_FIXTURES[0].id, pastedText: null });
    expect(body.form).toBeUndefined();
    expect(() => demoIntake("fx_made_up")).toThrow();
  });
});

describe("live intake", () => {
  const complete = { ...emptyReel(), instrument: "BTCUSD", timeframe: "1d", start: "2025-01-01", end: "2026-01-01",
    template: "SMA_CROSS", templateParams: { fast: "10", slow: "30" } };

  it("is always LIVE_EVIDENCE with integer template params and decimal-string results", () => {
    const { intake, errors } = liveIntake(complete, { total_return_pct: "+340" }, "");
    expect(errors).toEqual([]);
    expect(intake!.dataMode).toBe("LIVE_EVIDENCE");
    expect((intake!.form!.params as any).template_params).toEqual({ fast: 10, slow: 30 });
    expect(intake!.form!.outcomes).toEqual({ total_return_pct: "340" });
    expect(intake!.pastedText).toBeNull();
  });

  it("lets pasted text supply fields; form defaults never override it", () => {
    const { intake, errors } = liveIntake(emptyReel(), {}, "SMA_CROSS fast 10 slow 30 return 5%");
    expect(errors).toEqual([]);
    expect(intake!.form!.params).toEqual({ instrument_mode: "SPOT_LONG_FLAT" });
    expect(intake!.pastedText).toContain("SMA_CROSS");
  });

  it("rejects incomplete form claims and bad numbers", () => {
    expect(liveIntake(emptyReel(), {}, "").errors.length).toBeGreaterThan(0);
    expect(liveIntake(complete, { total_return_pct: "1e3" }, "").errors.join()).toMatch(/decimal/);
    expect(liveIntake({ ...complete, templateParams: { fast: "1.5", slow: "30" } }, { trade_count: "3" }, "").errors.join()).toMatch(/whole/);
  });
});
