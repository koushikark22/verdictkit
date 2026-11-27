/**
 * Guided demonstrations. The sample data is single-sourced from the two applications (the Quote
 * example worksheets and the Reel fixture ids), so a demonstration from the portal runs exactly the
 * case the application itself would run. Nothing here is a result: the verdict is whatever the
 * engine computes when the case is run.
 */
import type { DemoScenarioId, IntakeRequest } from "@verdictkit/ui-kit";
import examples from "../../../apps/quote-autopsy/web/src/examples.json";
import { leaseIntake, type LeaseForm } from "../../../apps/quote-autopsy/web/src/intake";
import { DEMO_FIXTURES, demoIntake } from "../../../apps/reel-autopsy/web/src/intake";

export interface Demo { id: string; title: string; blurb: string; designed: string; href: string }

const QUOTE_COPY: Record<string, { title: string; blurb: string }> = {
  consistent: { title: "Finance worksheet: consistent", blurb: "Every total follows from the line items." },
  padded: { title: "Finance worksheet: 400.00 hidden in the amount financed", blurb: "Later lines are derived from the inflated figure." },
  "lease-consistent": { title: "Lease worksheet: consistent", blurb: "Payment lines equal what the engine computes." },
  "lease-padded": { title: "Lease worksheet: 40.00 hidden in the rent charge", blurb: "The padding is carried through to the payment." },
};
const REEL_COPY: Record<string, string> = {
  fx_reel_supported_hold: "A trade count that holds at every fee assumption.",
  fx_reel_conditional_sma: "A return that only holds under some fee and slippage assumptions.",
  fx_reel_impossible_sma: "A +3,400% claim, above the perfect-foresight ceiling.",
};

export const QUOTE_DEMOS: Demo[] = [...examples.examples, ...examples.leaseExamples].map((e) => ({
  id: e.id, title: QUOTE_COPY[e.id]?.title ?? e.label, blurb: QUOTE_COPY[e.id]?.blurb ?? "", designed: e.expect,
  href: `/quote/?demo=${encodeURIComponent(e.id)}`,
}));

export const REEL_DEMOS: Demo[] = DEMO_FIXTURES.map((f) => ({
  id: f.id, title: f.label, blurb: REEL_COPY[f.id] ?? "", designed: f.expect, href: `/reel/?demo=${encodeURIComponent(f.id)}`,
}));

/** A sample the Verify Lab can examine to obtain a real signed bundle. */
export interface LabSample { id: string; title: string; blurb: string; designed: string; intake: IntakeRequest }

function leaseSample(id: "lease-consistent" | "lease-padded"): LabSample {
  const ex = examples.leaseExamples.find((e) => e.id === id)!;
  const built = leaseIntake(ex.form as LeaseForm, ex.stated);
  if (!built.intake) throw new Error(`sample ${id} does not build an intake: ${built.errors.join("; ")}`);
  return { id, title: QUOTE_COPY[id].title, blurb: QUOTE_COPY[id].blurb, designed: ex.expect, intake: built.intake };
}

export const LAB_SAMPLES: LabSample[] = [
  leaseSample("lease-consistent"),
  leaseSample("lease-padded"),
  { id: "fx_reel_impossible_sma", title: "Reel claim above the bound (synthetic)", blurb: REEL_COPY.fx_reel_impossible_sma, designed: "IMPOSSIBLE",
    intake: demoIntake("fx_reel_impossible_sma") },
  { id: "fx_reel_supported_hold", title: "Reel trade count (synthetic)", blurb: REEL_COPY.fx_reel_supported_hold, designed: "SUPPORTED",
    intake: demoIntake("fx_reel_supported_hold") },
];

export const SCENARIO_ORDER: DemoScenarioId[] = [
  "trusted-signer", "unknown-signer", "revoked-signer", "unsigned-historical", "tampered-bundle",
];

export const VERIFY_DEMOS: { scenario: DemoScenarioId; title: string; blurb: string; href: string }[] = [
  { scenario: "trusted-signer", title: "Trusted signer", blurb: "Run a sample, sign it, verify it against a trust store that knows the signer." },
  { scenario: "unknown-signer", title: "Unknown signer", blurb: "Same bundle, a verifier that never enrolled the signer." },
  { scenario: "revoked-signer", title: "Revoked signer", blurb: "Same bundle, a verifier that has revoked the signer's key." },
  { scenario: "unsigned-historical", title: "Unsigned historical bundle", blurb: "Signature removed: still replays, but proves no origin." },
  { scenario: "tampered-bundle", title: "Tampered bundle", blurb: "One character of the sealed verdict changed after signing." },
].map((d) => ({ ...d, scenario: d.scenario as DemoScenarioId, href: `/verify?auto=1&sample=lease-consistent&scenario=${d.scenario}` }));
