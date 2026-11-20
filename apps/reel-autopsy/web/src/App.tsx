import { useEffect, useMemo, useState } from "react";
import {
  BundlePanel, Blockers, IsolationBanner, ParameterLedger, ReplayUpload, RunProgress, VerdictView,
  createClient, describeError, useCaseWorkflow, type Health,
} from "@verdictkit/ui-kit";
import { DEMO_FIXTURES, OUTCOMES, TEMPLATES, demoIntake, emptyReel, liveIntake, type ReelForm } from "./intake";

const BOUND_SCOPE = "No long-or-flat spot strategy trading at most once per bar on this data, without leverage and before costs, could exceed this return.";

export function App() {
  const client = useMemo(() => createClient(), []);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthErr, setHealthErr] = useState<string | null>(null);
  const [tab, setTab] = useState<"demo" | "claim">("demo");
  const [form, setForm] = useState<ReelForm>(emptyReel);
  const [stated, setStated] = useState<Record<string, string>>({});
  const [pasted, setPasted] = useState("");
  const [formErrors, setFormErrors] = useState<string[]>([]);
  const { state, submit } = useCaseWorkflow(client);
  const busy = ["intake", "freezing", "evidence", "running"].includes(state.phase);

  useEffect(() => { client.health().then(setHealth, (e) => setHealthErr(describeError(e))); }, [client]);

  const runDemo = (id: string) => { setFormErrors([]); void submit(demoIntake(id)); };
  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const built = liveIntake(form, stated, pasted);
    setFormErrors(built.errors);
    // Claimed results and pasted text are sent once, then cleared from the page.
    if (built.intake) void submit(built.intake, () => { setStated({}); setPasted(""); });
  };
  const hasBound = state.outcome?.findings.some((f) => f.findingId === "total_return_bound");

  return (
    <main>
      <h1>Reel Autopsy</h1>
      <p className="vk-muted">Reproduces a mechanical trading-strategy claim on independent price data, sweeps undeclared
        costs, and tests it against a perfect-foresight bound. It can establish what the stated rule would have produced
        on the data — not what the claimant actually traded.</p>
      {healthErr ? <p className="vk-error">API unavailable: {healthErr}</p> : <IsolationBanner health={health} />}

      <div className="vk-tabs" role="group" aria-label="Mode">
        <button type="button" aria-pressed={tab === "demo"} onClick={() => setTab("demo")}>Synthetic demonstrations</button>
        <button type="button" aria-pressed={tab === "claim"} onClick={() => setTab("claim")}>Check a real claim</button>
      </div>

      {tab === "demo" ? (
        <section className="vk-card" data-testid="demos">
          <div className="vk-banner vk-demo">DEMONSTRATION ONLY: these run the real engine on labelled synthetic price data
            (instrument SYNTH-USD, which does not exist). Results say nothing about any real market or claim.</div>
          {DEMO_FIXTURES.map((f) => (
            <p key={f.id}><button type="button" disabled={busy} onClick={() => runDemo(f.id)} data-fixture={f.id}>
              Run {f.label}</button> <span className="vk-muted"><code>{f.id}</code></span></p>
          ))}
        </section>
      ) : (
        <form className="vk-card vk-form" onSubmit={onSubmit} aria-label="Claim intake">
          <p className="vk-muted vk-span-all">Licensed historical price data is not yet available (decision B1), so a real
            claim is frozen and recorded but will be <b>BLOCKED</b> at the evidence stage rather than judged on guessed data.</p>
          <label className="vk-span-all">Paste the claim text (optional; no links, handles, emails or phone numbers; never stored)
            <textarea value={pasted} maxLength={2000} onChange={(e) => setPasted(e.target.value)}
              placeholder="SMA_CROSS fast 10 slow 30 instrument BTCUSD timeframe 1d start 2025-01-01 end 2026-01-01 return +340%" />
          </label>
          <label>Instrument<input value={form.instrument} onChange={(e) => setForm({ ...form, instrument: e.target.value })} /></label>
          <label>Timeframe<select value={form.timeframe} onChange={(e) => setForm({ ...form, timeframe: e.target.value })}>
            <option value="">(from text)</option><option>1h</option><option>4h</option><option>1d</option></select></label>
          <label>Start (UTC date)<input type="date" value={form.start} onChange={(e) => setForm({ ...form, start: e.target.value })} /></label>
          <label>End (exclusive)<input type="date" value={form.end} onChange={(e) => setForm({ ...form, end: e.target.value })} /></label>
          <label>Template<select value={form.template} onChange={(e) => setForm({ ...form, template: e.target.value, templateParams: {} })}>
            <option value="">(from text)</option>{Object.keys(TEMPLATES).map((t) => <option key={t}>{t}</option>)}</select></label>
          {(TEMPLATES[form.template] ?? []).map((n) => (
            <label key={n}>{n}<input inputMode="numeric" value={form.templateParams[n] ?? ""}
              onChange={(e) => setForm({ ...form, templateParams: { ...form.templateParams, [n]: e.target.value } })} /></label>
          ))}
          <fieldset className="vk-span-all vk-card"><legend>Claimed results (sealed; never shown back before the verdict)</legend>
            <div className="vk-form">{OUTCOMES.map((n) => (
              <label key={n}>{n.replace(/_/g, " ")}<input inputMode="decimal" value={stated[n] ?? ""}
                onChange={(e) => setStated((s) => ({ ...s, [n]: e.target.value }))} /></label>
            ))}</div>
          </fieldset>
          <div className="vk-span-all"><button type="submit" disabled={busy}>Freeze and examine</button></div>
          {formErrors.length ? <ul className="vk-span-all vk-error">{formErrors.map((e) => <li key={e}>{e}</li>)}</ul> : null}
        </form>
      )}

      {state.phase !== "idle" ? <p className="vk-muted" data-testid="phase">Stage: {state.phase}</p> : null}
      {state.error ? <p className="vk-error" data-testid="error">{state.error}</p> : null}
      {state.draft && state.phase === "draft-blocked" ? <>
        <Blockers blockers={state.draft.blockers} /><ParameterLedger entries={state.draft.parameterLedger} />
        <p className="vk-muted">Fill the missing fields in the form and submit again.</p>
      </> : null}
      <RunProgress events={state.events} />
      {state.outcome ? (
        <VerdictView outcome={state.outcome}>
          {hasBound ? <p className="vk-muted vk-card">Bound scope: {BOUND_SCOPE}</p> : null}
          {state.outcome.bundleAvailable && state.caseId ? <BundlePanel client={client} caseId={state.caseId} /> : null}
        </VerdictView>
      ) : null}
      <ReplayUpload client={client} />
    </main>
  );
}
