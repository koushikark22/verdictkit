---
inclusion: fileMatch
fileMatchPattern: ["apps/**/*.py", "core/src/verdictkit/sweep.py", "core/src/verdictkit/model.py"]
---
# Money and rate arithmetic

- Use `Decimal` with an explicit `localcontext(prec=34, rounding=ROUND_HALF_EVEN)` for
  intermediate math; quantise displayed currency with `ROUND_HALF_UP` to `Decimal("0.01")`
  in Quote Autopsy (`money.cents`).
- Percent inputs are percentages (e.g. `"7.25"` means 7.25 %). Convert once, at the formula.
- Basis points: `bps / Decimal(10000)`.
- Monthly rate: `apr_pct / Decimal(1200)`. APR 0 is a special case (`AF / n`).
- Never compare money with `==` across rounding conventions; compare quantised values or
  use the claim type's declared tolerance.
- Annuity: `payment = AF * i / (1 - (1 + i) ** -n)`; use integer exponents only.
- Reel equity math is scale-free; start equity is `Decimal("10000")`.
