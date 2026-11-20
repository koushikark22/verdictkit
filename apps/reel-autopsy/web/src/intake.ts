/**
 * Reel intake (reel req 1, 8). Synthetic demonstrations are created only from the trusted
 * fixture ids bundled with the server; the UI sends the id and nothing else. A user's
 * own claim is always LIVE_EVIDENCE. Pasted text is sent once and never stored by the
 * server; explicit form values take precedence over text extraction.
 */
import type { IntakeRequest } from "@verdictkit/ui-kit";

/** Must equal the server's reel_autopsy.fixtures.FIXTURES keys (checked by a Python test). */
export const DEMO_FIXTURES = [
  { id: "fx_reel_supported_hold", label: "Buy-and-hold trade count", expect: "SUPPORTED" },
  { id: "fx_reel_conditional_sma", label: "SMA 10/30 return that depends on costs", expect: "CONDITIONAL" },
  { id: "fx_reel_impossible_sma", label: "SMA 10/30 claim above the perfect-foresight bound", expect: "IMPOSSIBLE" },
] as const;

export const TEMPLATES: Record<string, string[]> = {
  BUY_AND_HOLD: [], SMA_CROSS: ["fast", "slow"], DONCHIAN_BREAKOUT: ["lookback"], RSI_REVERSION: ["period", "lower", "upper"],
};
export const OUTCOMES = ["total_return_pct", "max_drawdown_pct", "trade_count", "win_rate_pct"] as const;

export interface ReelForm {
  instrument: string; timeframe: string; start: string; end: string; template: string;
  templateParams: Record<string, string>;
}

export const emptyReel = (): ReelForm => ({ instrument: "", timeframe: "", start: "", end: "", template: "", templateParams: {} });

export function demoIntake(fixtureId: string): IntakeRequest {
  if (!DEMO_FIXTURES.some((f) => f.id === fixtureId)) throw new Error("unknown fixture");
  return { claimType: "reel.mechanical.v1", dataMode: "SYNTHETIC_DEMO", fixtureId, pastedText: null };
}

export function liveIntake(f: ReelForm, stated: Record<string, string>, pasted: string): { intake?: IntakeRequest; errors: string[] } {
  const errors: string[] = [];
  const text = pasted.trim();
  if (text.length > 2000) errors.push("pasted text must be at most 2000 characters");
  const params: Record<string, unknown> = { instrument_mode: "SPOT_LONG_FLAT" };
  if (f.instrument.trim()) params.instrument = f.instrument.trim();
  if (f.timeframe) params.timeframe = f.timeframe;
  if (f.start) params.start = f.start;
  if (f.end) params.end = f.end;
  if (f.template) {
    params.template = f.template;
    const tp: Record<string, number> = {};
    for (const name of TEMPLATES[f.template] ?? []) {
      const raw = (f.templateParams[name] ?? "").trim();
      if (!raw) continue;
      if (!/^[0-9]+$/.test(raw)) errors.push(`${name} must be a whole number`);
      tp[name] = Number.parseInt(raw, 10);
    }
    if (Object.keys(tp).length || !text) params.template_params = tp;
  }
  const outcomes: Record<string, string> = {};
  for (const name of OUTCOMES) {
    const v = (stated[name] ?? "").trim();
    if (!v) continue;
    if (!/^[+-]?[0-9]+(\.[0-9]+)?$/.test(v)) errors.push(`claimed ${name} must be a decimal number`);
    outcomes[name] = v.replace(/^\+/, "");
  }
  if (!text) {
    for (const k of ["instrument", "timeframe", "start", "end", "template"]) if (!params[k]) errors.push(`${k} is required`);
    if (!Object.keys(outcomes).length) errors.push("enter at least one claimed result");
  }
  if (errors.length) return { errors };
  return {
    errors,
    intake: { claimType: "reel.mechanical.v1", dataMode: "LIVE_EVIDENCE", fixtureId: null,
      form: { params, outcomes }, pastedText: text || null },
  };
}
