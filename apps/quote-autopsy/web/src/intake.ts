/**
 * Pure mapping from form state to the API intake body (quote req 1-4). Claimed values
 * are sent once and never read back; an "unknown" taxability flag or rounding convention
 * becomes null plus a missing assumption of the same name, which the engine sweeps over
 * {0, 1} (origin DEFAULT_POLICY).
 */
import type { IntakeRequest } from "@verdictkit/ui-kit";

export type Tri = "yes" | "no" | "unknown";

export interface FinanceForm {
  selling_price: string; doc_fee: string; doc_fee_taxable: Tri;
  addon_code: string; addon_amount: string; addon_taxable: Tri;
  gov_fee_amount: string; gov_fee_taxable: Tri;
  trade_allowance: string; trade_payoff: string; trade_tax_credit: Tri;
  cash_down: string; stated_tax_rate_pct: string; apr_pct: string; term_months: string; state: string;
}

export const FINANCE_OUTCOMES = ["taxable_base", "sales_tax", "amount_financed", "monthly_payment",
  "total_of_payments", "finance_charge"] as const;
export const LEASE_OUTCOMES = ["depreciation_fee", "rent_charge", "base_payment", "monthly_tax",
  "total_monthly_payment"] as const;
export const ITEMISED_LEASE_OUTCOMES = ["stated_gross_cap_cost", "stated_adjusted_cap_cost", "stated_residual_value",
  ...LEASE_OUTCOMES] as const;

/** Itemised lease worksheet (quote req 2.1). */
export interface ItemisedLeaseForm {
  msrp: string; selling_price: string; acquisition_fee: string; doc_fee: string; other_items: string;
  cash_reduction: string; rebate: string; net_trade: string;
  residual_mode: "pct" | "value"; residual: string; money_factor: string; stated_tax_rate_pct: string;
  term_months: string; state: string; rounding_convention: "COMPONENT" | "FINAL" | "unknown";
}

export const emptyItemisedLease = (): ItemisedLeaseForm => ({
  msrp: "", selling_price: "", acquisition_fee: "", doc_fee: "", other_items: "", cash_reduction: "", rebate: "",
  net_trade: "", residual_mode: "pct", residual: "", money_factor: "", stated_tax_rate_pct: "", term_months: "36",
  state: "", rounding_convention: "unknown",
});

export interface LeaseForm {
  adjusted_cap_cost: string; residual_value: string; money_factor: string; tax_rate_pct: string;
  term_months: string; rounding_convention: "COMPONENT" | "FINAL" | "unknown";
}

export const emptyFinance = (): FinanceForm => ({
  selling_price: "", doc_fee: "0.00", doc_fee_taxable: "yes", addon_code: "", addon_amount: "", addon_taxable: "yes",
  gov_fee_amount: "", gov_fee_taxable: "no", trade_allowance: "0.00", trade_payoff: "0.00", trade_tax_credit: "yes",
  cash_down: "0.00", stated_tax_rate_pct: "", apr_pct: "", term_months: "60", state: "",
});

export const emptyLease = (): LeaseForm => ({
  adjusted_cap_cost: "", residual_value: "", money_factor: "", tax_rate_pct: "", term_months: "36",
  rounding_convention: "unknown",
});

const DECIMAL = /^[0-9]+(\.[0-9]+)?$/;

function money(value: string, name: string, errors: string[]): string {
  const v = value.trim();
  if (!DECIMAL.test(v)) errors.push(`${name} must be a plain decimal number`);
  return v;
}

function flag(t: Tri): boolean | null {
  return t === "unknown" ? null : t === "yes";
}

function outcomes(stated: Record<string, string>, allowed: readonly string[], errors: string[]) {
  const out: Record<string, string> = {};
  for (const name of allowed) {
    const v = (stated[name] ?? "").trim();
    if (!v) continue;
    if (!/^-?[0-9]+(\.[0-9]+)?$/.test(v)) errors.push(`stated ${name} must be a decimal number`);
    out[name] = v;
  }
  if (!Object.keys(out).length) errors.push("enter at least one stated figure from the worksheet");
  return out;
}

export function financeIntake(f: FinanceForm, stated: Record<string, string>): { intake?: IntakeRequest; errors: string[] } {
  const errors: string[] = [];
  const assumptions: Record<string, null> = {};
  const addons = [];
  if (f.addon_amount.trim()) {
    addons.push({ code: f.addon_code || "OTHER", amount: money(f.addon_amount, "add-on amount", errors), taxable: flag(f.addon_taxable) });
    if (f.addon_taxable === "unknown") assumptions["addons.0.taxable"] = null;
  }
  const govFees = [];
  if (f.gov_fee_amount.trim()) {
    govFees.push({ code: "TITLE", amount: money(f.gov_fee_amount, "government fee", errors), taxable: flag(f.gov_fee_taxable) });
    if (f.gov_fee_taxable === "unknown") assumptions["gov_fees.0.taxable"] = null;
  }
  if (f.doc_fee_taxable === "unknown") assumptions.doc_fee_taxable = null;
  if (f.trade_tax_credit === "unknown") assumptions.trade_tax_credit = null;
  const term = Number.parseInt(f.term_months, 10);
  if (!Number.isInteger(term) || term < 1 || term > 96 || String(term) !== f.term_months.trim()) errors.push("term must be 1-96 months");
  const state = f.state.trim().toUpperCase();
  if (!/^[A-Z]{2}$/.test(state)) errors.push("state must be a two-letter code");
  const params = {
    selling_price: money(f.selling_price, "selling price", errors), addons, doc_fee: money(f.doc_fee, "doc fee", errors),
    doc_fee_taxable: flag(f.doc_fee_taxable), gov_fees: govFees, rebates: [],
    trade_allowance: money(f.trade_allowance, "trade allowance", errors), trade_payoff: money(f.trade_payoff, "trade payoff", errors),
    trade_tax_credit: flag(f.trade_tax_credit), cash_down: money(f.cash_down, "cash down", errors),
    stated_tax_rate_pct: money(f.stated_tax_rate_pct, "tax rate", errors), apr_pct: money(f.apr_pct, "APR", errors),
    term_months: term, jurisdiction: { state },
  };
  const out = outcomes(stated, FINANCE_OUTCOMES, errors);
  if (errors.length) return { errors };
  return { errors, intake: { claimType: "quote.finance.v1", dataMode: "LIVE_EVIDENCE", form: { params, outcomes: out, assumptions } } };
}

export function leaseIntake(f: LeaseForm, stated: Record<string, string>): { intake?: IntakeRequest; errors: string[] } {
  const errors: string[] = [];
  const term = Number.parseInt(f.term_months, 10);
  if (!Number.isInteger(term) || term < 1 || term > 60 || String(term) !== f.term_months.trim()) errors.push("term must be 1-60 months");
  const params = {
    adjusted_cap_cost: money(f.adjusted_cap_cost, "adjusted cap cost", errors),
    residual_value: money(f.residual_value, "residual value", errors),
    money_factor: money(f.money_factor, "money factor", errors), tax_rate_pct: money(f.tax_rate_pct, "tax rate", errors),
    term_months: term, rounding_convention: f.rounding_convention === "unknown" ? null : f.rounding_convention,
  };
  const assumptions: Record<string, null> = f.rounding_convention === "unknown" ? { rounding_convention: null } : {};
  const out = outcomes(stated, LEASE_OUTCOMES, errors);
  if (errors.length) return { errors };
  return { errors, intake: { claimType: "quote.lease.v1", dataMode: "LIVE_EVIDENCE", form: { params, outcomes: out, assumptions } } };
}

export function itemisedLeaseIntake(f: ItemisedLeaseForm, stated: Record<string, string>): { intake?: IntakeRequest; errors: string[] } {
  const errors: string[] = [];
  const term = Number.parseInt(f.term_months, 10);
  if (!Number.isInteger(term) || term < 1 || term > 60 || String(term) !== f.term_months.trim()) errors.push("term must be 1-60 months");
  const state = f.state.trim().toUpperCase();
  if (!/^[A-Z]{2}$/.test(state)) errors.push("state must be a two-letter code");
  const lines = (pairs: [string, string][]) => pairs.filter(([, v]) => v.trim())
    .map(([code, v]) => ({ code, amount: money(v, code.toLowerCase().replace(/_/g, " "), errors) }));
  const params: Record<string, unknown> = {
    msrp: money(f.msrp, "MSRP", errors), selling_price: money(f.selling_price, "selling price", errors),
    capitalized_items: lines([["ACQUISITION_FEE", f.acquisition_fee], ["DOC_FEE", f.doc_fee], ["OTHER", f.other_items]]),
    cap_cost_reductions: lines([["CASH", f.cash_reduction], ["REBATE", f.rebate], ["NET_TRADE", f.net_trade]]),
    money_factor: money(f.money_factor, "money factor", errors),
    stated_tax_rate_pct: money(f.stated_tax_rate_pct, "tax rate", errors), term_months: term,
    jurisdiction: { state }, rounding_convention: f.rounding_convention === "unknown" ? null : f.rounding_convention,
  };
  params[f.residual_mode === "pct" ? "residual_pct_of_msrp" : "residual_value"] = money(f.residual, "residual", errors);
  const assumptions: Record<string, null> = f.rounding_convention === "unknown" ? { rounding_convention: null } : {};
  const out = outcomes(stated, ITEMISED_LEASE_OUTCOMES, errors);
  if (errors.length) return { errors };
  return { errors, intake: { claimType: "quote.lease.v1", dataMode: "LIVE_EVIDENCE", form: { params, outcomes: out, assumptions } } };
}
