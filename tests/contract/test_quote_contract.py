"""Quote Autopsy contract: P16 amortization, P16b inversion bound, P17 lease, P17b tax.
Quote requirements 3, 4, 6.2, 6.4. (P17c diagnostics inertness is covered by the core
tests test_bundle_replay.py::test_diagnostics_are_inert and the ledger order tests.)"""
from decimal import Decimal
from fractions import Fraction

from hypothesis import assume, given
from hypothesis import strategies as st

from contract.oracles import (
    F,
    annuity_factor_exact,
    finance_chain_oracle,
    lease_exact_base,
    near_half_cent,
    payment_exact,
    round_half_up_cents,
)
from quote_autopsy import finance, lease
from quote_autopsy.worksheet import (
    Addon,
    AddonCode,
    FinanceWorksheet,
    GovFee,
    GovFeeCode,
    Jurisdiction,
    LeaseConvention,
    Rebate,
    RebateTiming,
)


def cents_st(lo, hi):
    return st.integers(lo, hi).map(lambda c: Decimal(c).scaleb(-2))


principal_st = cents_st(100, 20_000_000)  # $1 .. $200,000
apr_st = st.integers(0, 30_000).map(lambda x: Decimal(x).scaleb(-3))  # 0 .. 30.000 %
term_st = st.integers(1, 96)


@given(principal_st, apr_st, term_st)
def test_payment_exact(p, apr, n):
    """P16 / Req 3.4: payment equals exact annuity payment rounded half-up to the cent."""
    exact = payment_exact(F(p), F(apr), n)
    assume(not near_half_cent(exact))
    assert F(finance.monthly_payment(p, apr, n)) == round_half_up_cents(exact)


@given(principal_st, term_st)
def test_zero_apr(p, n):
    exact = F(p) / n
    assume(not near_half_cent(exact))
    assert F(finance.monthly_payment(p, Decimal(0), n)) == round_half_up_cents(exact)


@given(principal_st, apr_st, term_st)
def test_annuity_factor(p, apr, n):
    exp = annuity_factor_exact(F(apr), n)
    assert abs(F(finance.annuity_factor(apr, n)) - exp) <= Fraction(1, 10**25) * (1 + exp)


@given(principal_st, apr_st, term_st)
def test_inversion_bound(p, apr, n):
    """P16b / Req 6.2, 6.4: inverting a rounded payment recovers AF within the stated bound."""
    pay = finance.monthly_payment(p, apr, n)
    implied = F(finance.implied_amount_financed(pay, apr, n))
    bound = Fraction(1, 200) * annuity_factor_exact(F(apr), n) + Fraction(1, 100)
    assert abs(implied - F(p)) <= bound


@given(cents_st(0, 20_000_000), st.integers(0, 1500), st.integers(0, 1500))
def test_tax_monotone_in_rate(base, r1, r2):
    """P17b: tax never decreases as the rate increases."""
    lo, hi = sorted((Decimal(r1).scaleb(-2), Decimal(r2).scaleb(-2)))
    assert finance.sales_tax(base, lo) <= finance.sales_tax(base, hi)


@given(cents_st(0, 20_000_000), cents_st(0, 20_000_000), st.integers(0, 1500))
def test_tax_monotone_in_base(b1, b2, r):
    lo, hi = sorted((b1, b2))
    rate = Decimal(r).scaleb(-2)
    assert finance.sales_tax(lo, rate) <= finance.sales_tax(hi, rate)


@st.composite
def worksheets(draw):
    money = lambda lo, hi: draw(cents_st(lo, hi))  # noqa: E731
    addons = tuple(
        Addon(draw(st.sampled_from(list(AddonCode))), money(0, 300_000), draw(st.booleans()))
        for _ in range(draw(st.integers(0, 3)))
    )
    gov = tuple(
        GovFee(draw(st.sampled_from(list(GovFeeCode))), money(0, 50_000), draw(st.booleans()))
        for _ in range(draw(st.integers(0, 3)))
    )
    rebates = tuple(
        Rebate(money(0, 300_000), draw(st.sampled_from(list(RebateTiming))))
        for _ in range(draw(st.integers(0, 2)))
    )
    return FinanceWorksheet(
        selling_price=money(500_000, 10_000_000),
        addons=addons,
        doc_fee=money(0, 100_000),
        doc_fee_taxable=draw(st.booleans()),
        gov_fees=gov,
        rebates=rebates,
        trade_allowance=money(0, 2_000_000),
        trade_payoff=money(0, 2_000_000),
        trade_tax_credit=draw(st.booleans()),
        cash_down=money(0, 1_000_000),
        stated_tax_rate_pct=Decimal(draw(st.integers(0, 1200))).scaleb(-2),
        apr_pct=draw(apr_st),
        term_months=draw(st.integers(12, 84)),
        jurisdiction=Jurisdiction("XX"),
    )


@given(worksheets())
def test_finance_chain_matches_oracle(ws):
    """Req 3.1–3.5: every line of the blind chain equals the independent Fraction oracle."""
    exp = finance_chain_oracle(ws)
    assume(exp["amount_financed"] > 0)
    assume(not near_half_cent(exp["tax_exact"]) and not near_half_cent(exp["payment_exact"]))
    got = finance.chain(ws)
    assert F(got.taxable_base) == exp["taxable_base"]
    assert F(got.sales_tax) == exp["sales_tax"]
    assert F(got.amount_financed) == exp["amount_financed"]
    assert F(got.monthly_payment) == exp["monthly_payment"]
    assert F(got.total_of_payments) == exp["total_of_payments"]
    assert F(got.finance_charge) == exp["finance_charge"]


@st.composite
def lease_inputs(draw):
    adj = draw(cents_st(100_000, 15_000_000))
    residual = draw(cents_st(0, int(adj * 100) - 1))
    mf = Decimal(draw(st.integers(10, 4000))).scaleb(-6)  # 0.000010 .. 0.004000
    n = draw(st.integers(12, 60))
    rate = Decimal(draw(st.integers(0, 1500))).scaleb(-2)  # 0 .. 15 %
    return adj, residual, mf, n, rate


@given(lease_inputs())
def test_lease_identity(inp):
    """P17 / Req 4.1–4.3."""
    adj, res, mf, n, rate = inp
    comp = lease.compute(adj, res, mf, n, rate, LeaseConvention.COMPONENT)
    fin = lease.compute(adj, res, mf, n, rate, LeaseConvention.FINAL)
    # COMPONENT: components are whole cents and add up exactly.
    assert comp.depreciation_fee == comp.depreciation_fee.quantize(Decimal("0.01"))
    assert comp.rent_charge == comp.rent_charge.quantize(Decimal("0.01"))
    assert comp.base_payment == comp.depreciation_fee + comp.rent_charge
    assert comp.total_monthly_payment == comp.base_payment + comp.monthly_tax
    # FINAL: total equals the exact oracle rounded once.
    exact_total = lease_exact_base(F(adj), F(res), F(mf), n) * (1 + F(rate) / 100)
    assume(not near_half_cent(exact_total))
    assert F(fin.total_monthly_payment) == round_half_up_cents(exact_total)
    # Conventions differ by at most two cents for rates <= 15 %.
    assert abs(comp.total_monthly_payment - fin.total_monthly_payment) <= Decimal("0.02")
