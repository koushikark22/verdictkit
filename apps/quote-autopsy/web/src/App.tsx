import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AppShell, BundlePanel, Blockers, EmptyState, ErrorCard, IsolationBanner, ParameterLedger, PhaseTracker, ReplayUpload,
  RunProgress, SampleCard, StatusLegend, VerdictView, createClient, useCaseWorkflow, useHealth, useScrollToResult,
} from "@verdictkit/ui-kit";
import {
  FINANCE_OUTCOMES, ITEMISED_LEASE_OUTCOMES, LEASE_OUTCOMES, emptyFinance, emptyItemisedLease, emptyLease,
  financeIntake, itemisedLeaseIntake, leaseIntake, type FinanceForm, type ItemisedLeaseForm, type LeaseForm, type Tri,
} from "./intake";
import examplesFile from "./examples.json";

interface Example<F> { id: string; label: string; expect: string; form: F; stated: Record<string, string> }
const FINANCE_EXAMPLES = examplesFile.examples as Example<FinanceForm>[];
const LEASE_EXAMPLES = examplesFile.leaseExamples as Example<LeaseForm>[];

const BLURB: Record<string, string> = {
  consistent: "A car-loan worksheet whose totals follow from its own line items.",
  padded: "The same worksheet with 400.00 hidden inside the amount financed; the later lines are derived from the inflated figure.",
  "lease-consistent": "A lease whose payment lines are the figures the engine itself computes from the cap cost, residual, money factor, tax and term.",
  "lease-padded": "The same lease with 40.00 hidden inside the rent charge; the later lines carry it through.",
};
const SAMPLES = [
  ...FINANCE_EXAMPLES.map((e) => ({ kind: "finance" as const, ex: e })),
  ...LEASE_EXAMPLES.map((e) => ({ kind: "lease" as const, ex: e })),
];

const ADDON_CODES = ["SERVICE_CONTRACT", "GAP", "PAINT_PROTECTION", "THEFT_ETCH", "TIRE_WHEEL", "OTHER"];

function Text({ label, value, onChange, hint }: { label: string; value: string; onChange: (v: string) => void; hint?: string }) {
  return <label>{label}<input value={value} inputMode="decimal" placeholder={hint} onChange={(e) => onChange(e.target.value)} /></label>;
}

function TriSelect({ label, value, onChange }: { label: string; value: Tri; onChange: (v: Tri) => void }) {
  return (
    <label>{label}
      <select value={value} onChange={(e) => onChange(e.target.value as Tri)}>
        <option value="yes">Taxable</option><option value="no">Not taxable</option>
        <option value="unknown">Not shown on worksheet (sweep both)</option>
      </select>
    </label>
  );
}

export function App() {
  const client = useMemo(() => createClient(), []);
  const { health, error: healthErr, loading, reload } = useHealth(client);
  const [kind, setKind] = useState<"finance" | "lease" | "itemised">("finance");
  const [itemised, setItemised] = useState<ItemisedLeaseForm>(emptyItemisedLease);
  const [finance, setFinance] = useState<FinanceForm>(emptyFinance);
  const [lease, setLease] = useState<LeaseForm>(emptyLease);
  const [stated, setStated] = useState<Record<string, string>>({});
  const [formErrors, setFormErrors] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const { state, submit } = useCaseWorkflow(client);
  useScrollToResult(state.phase);
  const autoRan = useRef(false);

  const setF = (k: keyof FinanceForm) => (v: string) => setFinance((f) => ({ ...f, [k]: v }));
  const setL = (k: keyof LeaseForm) => (v: string) => setLease((f) => ({ ...f, [k]: v }));
  const setI = (k: keyof ItemisedLeaseForm) => (v: string) => setItemised((f) => ({ ...f, [k]: v }));
  const outcomeNames = kind === "finance" ? FINANCE_OUTCOMES : kind === "lease" ? LEASE_OUTCOMES : ITEMISED_LEASE_OUTCOMES;
  const busy = ["intake", "freezing", "evidence", "running"].includes(state.phase);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSelected(null);
    const built = kind === "finance" ? financeIntake(finance, stated)
      : kind === "lease" ? leaseIntake(lease, stated) : itemisedLeaseIntake(itemised, stated);
    setFormErrors(built.errors);
    // Claimed figures are write-only: clear them once the server has accepted the case.
    if (built.intake) void submit(built.intake, () => setStated({}));
  };

  const loadSample = (s: (typeof SAMPLES)[number]) => {
    setFormErrors([]);
    setSelected(s.ex.id);
    setKind(s.kind);
    if (s.kind === "finance") setFinance({ ...(s.ex.form as FinanceForm) }); else setLease({ ...(s.ex.form as LeaseForm) });
    setStated({ ...s.ex.stated });
  };
  // One click: build the same intake body a person would submit from the form, then run it.
  const runSample = useCallback((s: (typeof SAMPLES)[number]) => {
    loadSample(s);
    const built = s.kind === "finance" ? financeIntake(s.ex.form as FinanceForm, s.ex.stated) : leaseIntake(s.ex.form as LeaseForm, s.ex.stated);
    setFormErrors(built.errors);
    if (built.intake) void submit(built.intake, () => setStated({}));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [submit]);

  // Deep link from the portal: /quote/?demo=padded runs that sample once the backend answers.
  useEffect(() => {
    if (autoRan.current || loading || !health) return;
    const id = new URLSearchParams(window.location.search).get("demo");
    const sample = SAMPLES.find((s) => s.ex.id === id);
    if (sample) { autoRan.current = true; runSample(sample); }
  }, [loading, health, runSample]);

  return (
    <AppShell active="quote" health={health} error={healthErr} loading={loading}>
      <main id="main">
        <p className="vk-kicker">Application 1 of 2 · vehicle finance and lease worksheets</p>
        <h1>Quote Autopsy</h1>
        <p className="vk-muted">Re-computes a dealer finance or lease worksheet from its itemised lines, blind to the
          stated totals, then compares. The examiner never saw the claimed figures.</p>
        <div className="vk-card">
          <h3>New to car financing? Start here.</h3>
          <p className="vk-muted">A dealer's worksheet lists a price, fees, tax, an interest rate and a monthly payment. Quote Autopsy
            recomputes every line from the itemised inputs and only afterwards compares with the totals the worksheet states.
            <b> CONTRADICTED</b> means the arithmetic cannot be reproduced from the worksheet's own inputs. It is not an accusation, and
            a clean result does not make an offer a good deal.</p>
          <StatusLegend statuses={["CONSISTENT", "CONTRADICTED", "CONDITIONAL", "SUPPORTED", "REFUTED", "INDETERMINATE"]} />
        </div>
        {healthErr ? <ErrorCard message={healthErr} onRetry={reload} testId="health-error" /> : <IsolationBanner health={health} />}

        <section aria-labelledby="samples-h" data-testid="examples">
          <h2 id="samples-h">Try a sample worksheet</h2>
          <p className="vk-muted">Constructed examples (not real dealer quotes). Where a sample states figures, they were computed by the engine
            or derived by plain arithmetic as the note says. One click runs the sample as a normal case; the verdict is whatever the engine computes.</p>
          <div className="vk-samples">
            {SAMPLES.map((s) => (
              <SampleCard key={s.ex.id} id={s.ex.id} title={`${s.kind === "finance" ? "Finance" : "Lease"}: ${s.ex.label.replace(/^Constructed (example|lease): /, "")}`}
                blurb={BLURB[s.ex.id] ?? ""} designed={s.ex.expect} selected={selected === s.ex.id} busy={busy}
                onRun={() => runSample(s)} onLoad={() => loadSample(s)} runAttr={{ "data-run-example": s.ex.id }} loadAttr={{ "data-example": s.ex.id }} />
            ))}
          </div>
        </section>

        <h2>Or enter your own worksheet</h2>
        <div className="vk-tabs" role="group" aria-label="Worksheet type">
          <button type="button" aria-pressed={kind === "finance"} onClick={() => { setKind("finance"); setStated({}); }}>Finance (retail installment)</button>
          <button type="button" aria-pressed={kind === "lease"} onClick={() => { setKind("lease"); setStated({}); }}>Lease (cap cost known)</button>
          <button type="button" aria-pressed={kind === "itemised"} onClick={() => { setKind("itemised"); setStated({}); }}>Lease (itemised)</button>
        </div>

        <form className="vk-card vk-form" onSubmit={onSubmit} aria-label="Worksheet intake">
          {kind === "finance" ? <>
            <Text label="Selling price" value={finance.selling_price} onChange={setF("selling_price")} hint="30000.00" />
            <Text label="Doc fee" value={finance.doc_fee} onChange={setF("doc_fee")} />
            <TriSelect label="Doc fee taxable?" value={finance.doc_fee_taxable} onChange={setF("doc_fee_taxable")} />
            <label>Add-on<select value={finance.addon_code} onChange={(e) => setF("addon_code")(e.target.value)}>
              <option value="">(none)</option>{ADDON_CODES.map((c) => <option key={c} value={c}>{c}</option>)}</select></label>
            <Text label="Add-on amount" value={finance.addon_amount} onChange={setF("addon_amount")} />
            <TriSelect label="Add-on taxable?" value={finance.addon_taxable} onChange={setF("addon_taxable")} />
            <Text label="Title / government fee" value={finance.gov_fee_amount} onChange={setF("gov_fee_amount")} />
            <TriSelect label="Government fee taxable?" value={finance.gov_fee_taxable} onChange={setF("gov_fee_taxable")} />
            <Text label="Trade allowance" value={finance.trade_allowance} onChange={setF("trade_allowance")} />
            <Text label="Trade payoff" value={finance.trade_payoff} onChange={setF("trade_payoff")} />
            <TriSelect label="Trade-in tax credit?" value={finance.trade_tax_credit} onChange={setF("trade_tax_credit")} />
            <Text label="Cash down" value={finance.cash_down} onChange={setF("cash_down")} />
            <Text label="Stated tax rate %" value={finance.stated_tax_rate_pct} onChange={setF("stated_tax_rate_pct")} hint="6.25" />
            <Text label="APR %" value={finance.apr_pct} onChange={setF("apr_pct")} hint="5.90" />
            <Text label="Term (months)" value={finance.term_months} onChange={setF("term_months")} />
            <Text label="State (2 letters)" value={finance.state} onChange={setF("state")} hint="TX" />
          </> : kind === "itemised" ? <>
            <Text label="MSRP" value={itemised.msrp} onChange={setI("msrp")} />
            <Text label="Selling price (lease)" value={itemised.selling_price} onChange={setI("selling_price")} />
            <Text label="Acquisition fee" value={itemised.acquisition_fee} onChange={setI("acquisition_fee")} />
            <Text label="Doc fee (capitalised)" value={itemised.doc_fee} onChange={setI("doc_fee")} />
            <Text label="Other capitalised items" value={itemised.other_items} onChange={setI("other_items")} />
            <Text label="Cash cap-cost reduction" value={itemised.cash_reduction} onChange={setI("cash_reduction")} />
            <Text label="Rebate" value={itemised.rebate} onChange={setI("rebate")} />
            <Text label="Net trade" value={itemised.net_trade} onChange={setI("net_trade")} />
            <label>Residual given as<select value={itemised.residual_mode} onChange={(e) => setI("residual_mode")(e.target.value)}>
              <option value="pct">% of MSRP</option><option value="value">amount</option></select></label>
            <Text label="Residual" value={itemised.residual} onChange={setI("residual")} />
            <Text label="Money factor (itemised)" value={itemised.money_factor} onChange={setI("money_factor")} hint="0.00125" />
            <Text label="Tax rate % (itemised)" value={itemised.stated_tax_rate_pct} onChange={setI("stated_tax_rate_pct")} />
            <Text label="Term (months, itemised)" value={itemised.term_months} onChange={setI("term_months")} />
            <Text label="State (itemised)" value={itemised.state} onChange={setI("state")} hint="TX" />
            <label>Rounding convention (itemised)<select value={itemised.rounding_convention}
              onChange={(e) => setI("rounding_convention")(e.target.value)}>
              <option value="unknown">Not stated (sweep both)</option><option value="COMPONENT">Round each component</option>
              <option value="FINAL">Round displayed totals only</option></select></label>
          </> : <>
            <Text label="Adjusted cap cost" value={lease.adjusted_cap_cost} onChange={setL("adjusted_cap_cost")} />
            <Text label="Residual value" value={lease.residual_value} onChange={setL("residual_value")} />
            <Text label="Money factor" value={lease.money_factor} onChange={setL("money_factor")} hint="0.00125" />
            <Text label="Tax rate %" value={lease.tax_rate_pct} onChange={setL("tax_rate_pct")} />
            <Text label="Term (months)" value={lease.term_months} onChange={setL("term_months")} />
            <label>Rounding convention<select value={lease.rounding_convention}
              onChange={(e) => setL("rounding_convention")(e.target.value)}>
              <option value="unknown">Not stated (sweep both)</option><option value="COMPONENT">Round each component</option>
              <option value="FINAL">Round displayed totals only</option></select></label>
          </>}
          <fieldset className="vk-span-all vk-card">
            <legend>Figures stated on the worksheet (sealed; sent once, never shown back before the verdict)</legend>
            <div className="vk-form">
              {outcomeNames.map((name) => (
                <Text key={name} label={name.replace(/_/g, " ")} value={stated[name] ?? ""}
                  onChange={(v) => setStated((s) => ({ ...s, [name]: v }))} />
              ))}
            </div>
          </fieldset>
          <p className="vk-muted vk-span-all">
            Conventions: monthly periods, first payment one period after contract, ROUND_HALF_UP to cents, no odd final
            payment. Lease: APR ≈ money factor × 2400 is a convention, not an identity. External checks cover Texas
            finance worksheets only, against a hash-pinned snapshot of Texas Comptroller and OCCC sources retrieved
            2026-11-24: the stated tax rate is SUPPORTED or REFUTED against the 6.25% motor vehicle rate (no local
            tax), and a doc fee at or below $225 is SUPPORTED as presumed reasonable; above $225 it is INDETERMINATE
            because an OCCC filing cannot be verified. Texas lease tax rate is not checked. Other states stay
            INDETERMINATE.
          </p>
          <div className="vk-span-all"><button type="submit" className="vk-primary" disabled={busy}>{busy ? "Examining…" : "Freeze and examine"}</button></div>
          {formErrors.length ? <ul className="vk-span-all vk-error">{formErrors.map((e) => <li key={e}>{e}</li>)}</ul> : null}
        </form>

        <section aria-live="polite" aria-labelledby="result-h">
          <h2 id="result-h">Result</h2>
          <PhaseTracker phase={state.phase} />
          {state.phase !== "idle" ? <p className="vk-muted" data-testid="phase">Stage: {state.phase}</p> : null}
          {state.phase === "idle" ? (
            <EmptyState title="No examination yet">Pick a sample above, or fill in a worksheet and press “Freeze and examine”.</EmptyState>
          ) : null}
          {state.error ? <ErrorCard message={state.error} /> : null}
          {state.draft && state.phase === "draft-blocked" ? <>
            <Blockers blockers={state.draft.blockers} /><ParameterLedger entries={state.draft.parameterLedger} />
          </> : null}
          <RunProgress events={state.events} />
          {state.outcome ? (
            <VerdictView outcome={state.outcome}>
              {state.outcome.bundleAvailable && state.caseId ? <BundlePanel client={client} caseId={state.caseId} /> : null}
            </VerdictView>
          ) : null}
        </section>
        <ReplayUpload client={client} isolationMode={health?.isolationMode ?? null} />
      </main>
    </AppShell>
  );
}
