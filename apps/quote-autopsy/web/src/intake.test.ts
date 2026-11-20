import { describe, expect, it } from "vitest";
import { emptyFinance, emptyLease, financeIntake, leaseIntake } from "./intake";

const filled = () => ({
  ...emptyFinance(), selling_price: "30000.00", doc_fee: "500.00", stated_tax_rate_pct: "6.00",
  apr_pct: "6.00", term_months: "60", state: "tx", cash_down: "5000.00",
});

describe("financeIntake", () => {
  it("builds a live intake with only the stated figures", () => {
    const { intake, errors } = financeIntake(filled(), { sales_tax: "1830.00", monthly_payment: "" });
    expect(errors).toEqual([]);
    expect(intake!.dataMode).toBe("LIVE_EVIDENCE");
    expect(intake!.form!.outcomes).toEqual({ sales_tax: "1830.00" });
    expect((intake!.form!.params as any).jurisdiction).toEqual({ state: "TX" });
    expect(intake!.form!.assumptions).toEqual({});
  });

  it("turns an unknown flag into null plus a missing assumption of the same name", () => {
    const { intake } = financeIntake({ ...filled(), doc_fee_taxable: "unknown", addon_amount: "800.00",
      addon_code: "GAP", addon_taxable: "unknown" }, { taxable_base: "31300.00" });
    const params = intake!.form!.params as any;
    expect(params.doc_fee_taxable).toBeNull();
    expect(params.addons[0].taxable).toBeNull();
    expect(intake!.form!.assumptions).toEqual({ doc_fee_taxable: null, "addons.0.taxable": null });
  });

  it("never sends floats or malformed numbers", () => {
    const { intake, errors } = financeIntake({ ...filled(), selling_price: "3e4" }, { sales_tax: "1830" });
    expect(intake).toBeUndefined();
    expect(errors.join()).toMatch(/selling price/);
    expect(financeIntake(filled(), {}).errors.join()).toMatch(/at least one stated figure/);
    expect(financeIntake({ ...filled(), term_months: "12.5" }, { sales_tax: "1" }).errors.join()).toMatch(/term/);
  });
});

describe("leaseIntake", () => {
  it("sweeps an unstated rounding convention", () => {
    const { intake } = leaseIntake({ ...emptyLease(), adjusted_cap_cost: "24000", residual_value: "12000",
      money_factor: "0.00125", tax_rate_pct: "8.875" }, { total_monthly_payment: "416.00" });
    expect((intake!.form!.params as any).rounding_convention).toBeNull();
    expect(intake!.form!.assumptions).toEqual({ rounding_convention: null });
  });

  it("keeps a stated convention as a parameter", () => {
    const { intake } = leaseIntake({ ...emptyLease(), adjusted_cap_cost: "24000", residual_value: "12000",
      money_factor: "0.00125", tax_rate_pct: "0", rounding_convention: "FINAL" }, { base_payment: "1" });
    expect((intake!.form!.params as any).rounding_convention).toBe("FINAL");
    expect(intake!.form!.assumptions).toEqual({});
  });
});

describe("itemisedLeaseIntake", () => {
  it("builds item lines and exactly one residual form", async () => {
    const { emptyItemisedLease, itemisedLeaseIntake } = await import("./intake");
    const { intake, errors } = itemisedLeaseIntake({ ...emptyItemisedLease(), msrp: "42000.00", selling_price: "39500.00",
      acquisition_fee: "895.00", cash_reduction: "2000.00", residual: "58", money_factor: "0.00125",
      stated_tax_rate_pct: "8.25", state: "tx" }, { stated_adjusted_cap_cost: "38395.00" });
    expect(errors).toEqual([]);
    const p = intake!.form!.params as any;
    expect(p.capitalized_items).toEqual([{ code: "ACQUISITION_FEE", amount: "895.00" }]);
    expect(p.cap_cost_reductions).toEqual([{ code: "CASH", amount: "2000.00" }]);
    expect(p.residual_pct_of_msrp).toBe("58");
    expect("residual_value" in p).toBe(false);
    expect(intake!.form!.assumptions).toEqual({ rounding_convention: null });
  });
});
