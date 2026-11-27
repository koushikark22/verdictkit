import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AppShell, BundlePanel, Blockers, EmptyState, ErrorCard, IsolationBanner, ParameterLedger, PhaseTracker, ReplayUpload,
  RunProgress, SampleCard, StatusLegend, VerdictView, createClient, useCaseWorkflow, useHealth, useScrollToResult,
} from "@verdictkit/ui-kit";
import { DEMO_FIXTURES, OUTCOMES, TEMPLATES, demoIntake, emptyReel, liveIntake, type ReelForm } from "./intake";

const BOUND_SCOPE = "No long-or-flat spot strategy trading at most once per bar on this data, without leverage and before costs, could exceed this return.";

const BLURB: Record<string, string> = {
  fx_reel_supported_hold: "Claim: a buy-and-hold strategy made exactly one trade over the year. A trade count can be checked exactly, whatever the fees.",
  fx_reel_conditional_sma: "Claim: a 10/30 moving-average rule lost 37%. Whether the rule reproduces that depends on the fees and slippage assumed, which the claim does not state.",
  fx_reel_impossible_sma: "Claim: the same rule gained 3,400%. The engine compares it with the perfect-foresight ceiling, the most any long-or-flat strategy could have earned on this data.",
};

export function App() {
  const client = useMemo(() => createClient(), []);
  const { health, error: healthErr, loading, reload } = useHealth(client);
  const [tab, setTab] = useState<"demo" | "claim">("demo");
  const [form, setForm] = useState<ReelForm>(emptyReel);
  const [stated, setStated] = useState<Record<string, string>>({});
  const [pasted, setPasted] = useState("");
  const [formErrors, setFormErrors] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const { state, submit } = useCaseWorkflow(client);
  useScrollToResult(state.phase);
  const autoRan = useRef(false);
  const busy = ["intake", "freezing", "evidence", "running"].includes(state.phase);

  const runDemo = useCallback((id: string) => {
    setFormErrors([]);
    setSelected(id);
    void submit(demoIntake(id));
  }, [submit]);

  // Deep link from the portal: /reel/?demo=fx_reel_impossible_sma runs that fixture once the backend answers.
  useEffect(() => {
    if (autoRan.current || loading || !health) return;
    const id = new URLSearchParams(window.location.search).get("demo");
    if (id && DEMO_FIXTURES.some((f) => f.id === id)) { autoRan.current = true; runDemo(id); }
  }, [loading, health, runDemo]);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const built = liveIntake(form, stated, pasted);
    setFormErrors(built.errors);
    // Claimed results and pasted text are sent once, then cleared from the page.
    if (built.intake) void submit(built.intake, () => { setStated({}); setPasted(""); });
  };
  const hasBound = state.outcome?.findings.some((f) => f.findingId === "total_return_bound");

  return (
    <AppShell active="reel" health={health} error={healthErr} loading={loading}>
      <main id="main">
        <p className="vk-kicker">Application 2 of 2 · mechanical trading-strategy claims</p>
        <h1>Reel Autopsy</h1>
        <p className="vk-muted">Reproduces a mechanical trading-strategy claim on independent price data, sweeps undeclared
          costs, and tests it against a perfect-foresight bound. It can establish what the stated rule would have produced
          on the data — not what the claimant actually traded.</p>
        <div className="vk-card">
          <h3>New to trading? Start here.</h3>
          <p className="vk-muted">Social posts often claim a strategy "returned +340%". A mechanical rule (for example "buy when the 10-day average
            crosses above the 30-day average") can be re-run on price data. Reel Autopsy re-runs it, tries different fee and slippage
            assumptions, and checks the claim against the highest return that <i>any</i> long-or-flat strategy could have reached on that data.
            Results describe the rule on the data, never a person's actual account.</p>
          <StatusLegend statuses={["SUPPORTED", "CONDITIONAL", "IMPOSSIBLE", "WITHIN_BOUND", "INDETERMINATE", "REFUTED"]} />
        </div>
        {healthErr ? <ErrorCard message={healthErr} onRetry={reload} testId="health-error" /> : <IsolationBanner health={health} />}

        <div className="vk-tabs" role="group" aria-label="Mode">
          <button type="button" aria-pressed={tab === "demo"} onClick={() => setTab("demo")}>Synthetic demonstrations</button>
          <button type="button" aria-pressed={tab === "claim"} onClick={() => setTab("claim")}>Check a real claim</button>
        </div>

        {tab === "demo" ? (
          <section className="vk-card" data-testid="demos">
            <div className="vk-banner vk-demo">DEMONSTRATION ONLY: these run the real engine on labelled synthetic price data
              (instrument SYNTH-USD, which does not exist). Results say nothing about any real market or claim.</div>
            <div className="vk-samples">
              {DEMO_FIXTURES.map((f) => (
                <SampleCard key={f.id} id={f.id} title={f.label} blurb={BLURB[f.id] ?? ""} designed={f.expect} selected={selected === f.id}
                  busy={busy} onRun={() => runDemo(f.id)} runAttr={{ "data-fixture": f.id }} />
              ))}
            </div>
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
            <div className="vk-span-all"><button type="submit" className="vk-primary" disabled={busy}>Freeze and examine</button></div>
            {formErrors.length ? <ul className="vk-span-all vk-error">{formErrors.map((e) => <li key={e}>{e}</li>)}</ul> : null}
          </form>
        )}

        <section aria-live="polite" aria-labelledby="result-h">
          <h2 id="result-h">Result</h2>
          <PhaseTracker phase={state.phase} />
          {state.phase !== "idle" ? <p className="vk-muted" data-testid="phase">Stage: {state.phase}</p> : null}
          {state.phase === "idle" ? (
            <EmptyState title="No examination yet">Run one of the three synthetic demonstrations above to see a complete verdict in a few seconds.</EmptyState>
          ) : null}
          {state.error ? <ErrorCard message={state.error} /> : null}
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
        </section>
        <ReplayUpload client={client} isolationMode={health?.isolationMode ?? null} />
      </main>
    </AppShell>
  );
}
