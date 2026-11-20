import { useEffect, useMemo, useState } from "react";
import {
  BundlePanel, Blockers, IsolationBanner, ParameterLedger, ReplayUpload, RunProgress, VerdictView,
  createClient, describeError, useCaseWorkflow, type Health,
} from "@verdictkit/ui-kit";
import {
  FINANCE_OUTCOMES, LEASE_OUTCOMES, emptyFinance, emptyLease, financeIntake, leaseIntake,
  type FinanceForm, type LeaseForm, type Tri,
} from "./intake";
import examplesFile from "./examples.json";

const EXAMPLES = examplesFile.examples as { id: string; label: string; form: FinanceForm; stated: Record<string, string> }[];

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
  const [health, setHealth] = useState<Health | null>(null);
  const [healthErr, setHealthErr] = useState<string | null>(null);
  const [kind, setKind] = useState<"finance" | "lease">("finance");
  const [finance, setFinance] = useState<FinanceForm>(emptyFinance);
  const [lease, setLease] = useState<LeaseForm>(emptyLease);
  const [stated, setStated] = useState<Record<string, string>>({});
  const [formErrors, setFormErrors] = useState<string[]>([]);
  const { state, submit } = useCaseWorkflow(client);

  useEffect(() => { client.health().then(setHealth, (e) => setHealthErr(describeError(e))); }, [client]);

  const setF = (k: keyof FinanceForm) => (v: string) => setFinance((f) => ({ ...f, [k]: v }));
  const setL = (k: keyof LeaseForm) => (v: string) => setLease((f) => ({ ...f, [k]: v }));
  const outcomeNames = kind === "finance" ? FINANCE_OUTCOMES : LEASE_OUTCOMES;
  const busy = ["intake", "freezing", "evidence", "running"].includes(state.phase);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const built = kind === "finance" ? financeIntake(finance, stated) : leaseIntake(lease, stated);
    setFormErrors(built.errors);
    // Claimed figures are write-only: clear them once the server has accepted the case.
    if (built.intake) void submit(built.intake, () => setStated({}));
  };

  return (
    <main>
      <h1>Quote Autopsy</h1>
      <p className="vk-muted">Re-computes a dealer finance or lease worksheet from its itemised lines, blind to the
        stated totals, then compares. The examiner never saw the claimed figures.</p>
      {healthErr ? <p className="vk-error">API unavailable: {healthErr}</p> : <IsolationBanner health={health} />}

      <div className="vk-tabs" role="group" aria-label="Worksheet type">
        <button type="button" aria-pressed={kind === "finance"} onClick={() => { setKind("finance"); setStated({}); }}>Finance (retail installment)</button>
        <button type="button" aria-pressed={kind === "lease"} onClick={() => { setKind("lease"); setStated({}); }}>Lease</button>
      </div>

      {kind === "finance" ? (
        <div className="vk-card" data-testid="examples">
          <p className="vk-muted">Constructed examples (not real dealer quotes; figures computed by the engine). Loading one
            fills the form; you still submit it as a normal case.</p>
          {EXAMPLES.map((ex) => (
            <button key={ex.id} type="button" className="vk-secondary" data-example={ex.id}
              onClick={() => { setFinance({ ...ex.form }); setStated({ ...ex.stated }); }}>{ex.label}</button>
          ))}
        </div>
      ) : null}

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
          payment. Lease: APR ≈ money factor × 2400 is a convention, not an identity. External tax-rate and doc-fee
          checks are not available until an official state rules snapshot is adopted; those findings stay INDETERMINATE.
        </p>
        <div className="vk-span-all"><button type="submit" disabled={busy}>{busy ? "Examining…" : "Freeze and examine"}</button></div>
        {formErrors.length ? <ul className="vk-span-all vk-error">{formErrors.map((e) => <li key={e}>{e}</li>)}</ul> : null}
      </form>

      {state.phase !== "idle" ? <p className="vk-muted" data-testid="phase">Stage: {state.phase}</p> : null}
      {state.error ? <p className="vk-error" data-testid="error">{state.error}</p> : null}
      {state.draft && state.phase === "draft-blocked" ? <>
        <Blockers blockers={state.draft.blockers} /><ParameterLedger entries={state.draft.parameterLedger} />
      </> : null}
      <RunProgress events={state.events} />
      {state.outcome ? (
        <VerdictView outcome={state.outcome}>
          {state.outcome.bundleAvailable && state.caseId ? <BundlePanel client={client} caseId={state.caseId} /> : null}
        </VerdictView>
      ) : null}
      <ReplayUpload client={client} />
    </main>
  );
}
