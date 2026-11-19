# Design Document — Reel Autopsy

## Overview

A `ClaimType` plugin (`reel.mechanical.v1`) plus an OHLCV evidence adapter and a UI.
All evaluator code is pure, `Decimal`-only and imports nothing outside the standard library
and `verdictkit.model`.

## Components and Interfaces (`apps/reel-autopsy/src/reel_autopsy/`)

| Module | API |
|---|---|
| `claim_type.py` | `ReelClaimType` implementing `verdictkit.plugin.ClaimType` |
| `bars.py` | `Bar(ts, open, high, low, close, volume)`; `expected_timestamps(start, end, timeframe)`; `find_gaps(bars, start, end, timeframe)` |
| `strategies.py` | `Template` enum; `target_positions(template, params, bars) -> list[int]` (0/1 per bar) |
| `simulator.py` | `simulate(bars, targets, costs: CostModel, position_fraction) -> SimResult` with per-bar `MarkRow(ts, cash, units, close, equity)` and `Fill` list |
| `metrics.py` | `total_return_pct`, `max_drawdown_pct`, `trade_count`, `win_rate_pct` |
| `bound.py` | `interval_returns(bars)`; `perfect_foresight_bound_pct(bars) -> Decimal`; `oracle_targets(bars) -> list[int]` |
| `tolerance.py` | `precision_tolerance(claimed: str) -> Decimal` |
| `sources/` | `OhlcvSource` protocol; registry with `license_class`; one concrete adapter chosen at decision B1 |

### Examine/compare split
* `examine(task, evidence, point)` — runs at each grid point in the Examiner: targets are
  computed once per task and cached by `(spec_hash)`; the simulator runs per point.
  Returns computed metrics, the bound, coverage, and the equity series for the
  first-failing / worst points (needed for counterexample charts).
* `findings(examination, outcomes)` — Custodian side, after reveal: tolerance comparison,
  aggregation, bound check.

## Data flow for one claim
1. Intake freezes parameters; outcomes are sealed.
2. Examiner acquires bars `[start, end)` through the broker; coverage check.
3. Targets from template (once). For each of ≤ 16 default grid points: simulate → metrics.
4. Bound computed once (independent of costs).
5. Custodian reveals outcomes, builds findings, seals the verdict, writes the bundle.

## Correctness Properties

* **P13 No lookahead** — for any bars and any *t*, replacing `bars[t+1:]` with arbitrary
  valid bars leaves `target_positions(...)[0..t]` unchanged. *(Req 2.1)*
* **P14 Accounting identity** — for any bars, targets, costs and fraction, every mark row
  satisfies `equity = cash + units × close`, `cash ≥ 0`, `units ≥ 0`; with zero costs and
  all-zero targets equity is constant. *(Req 3.4, 3.5)*
* **P15 Bound soundness and tightness** — for any bars and any 0/1 target sequence, the
  zero-cost simulated return ≤ `perfect_foresight_bound_pct`; for `oracle_targets` with
  zero costs and fraction 1 the simulated return equals the bound exactly. *(Req 7.1–7.2)*
* **P15b Cost monotonicity** — for fixed targets, increasing fee or slippage never
  increases final equity. *(Req 3.2)*

Note on P15 and fill timing: the target for bar *t* fills at open *t+1*, so the position
held over interval `open_{t+1} → open_{t+2}` is the target computed at bar *t*. The oracle
therefore sets `target[t] = 1` iff `r_{t+1} > 0`, which uses future data by design; it is
used only for the bound, never for reproduction.

## Error Handling
* Gap ⇒ coverage `INDETERMINATE`, reproductions `INDETERMINATE(evidence_gap)`.
* Undefined indicator for the whole range (e.g. `slow` > bar count) ⇒ intake rejection.
* Source unavailable ⇒ `INDETERMINATE(evidence_unavailable)`; never a cached guess.

## UI evidence of genuine behaviour (for Muse's storyboard)
* Equity curve chart is drawn from `examination` data of the selected grid point.
* The "toe tag" headline comes from `Verdict.headline`.
* The bound gauge shows `bound_pct` vs the claim, with the scope sentence of Req 7.5.
* Sweep heatmap cells = actual grid points; clicking a cell loads that point's equity series.
