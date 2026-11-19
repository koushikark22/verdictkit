# Requirements Document — Reel Autopsy

## Introduction

Reel Autopsy verifies *mechanical* trading-strategy performance claims of the kind posted in
short-form social videos ("SMA crossover on BTC made +340% in 2025"). A claim names one
strategy template with parameters, one spot instrument, one timeframe, one UTC date range
and the claimed results. Reel Autopsy reproduces the strategy on independently sourced
OHLCV data, sweeps undeclared costs, and tests the claim against a perfect-foresight bound.

MVP scope: spot, long-or-flat, no margin, no shorting, no options, no code generation.
Reel Autopsy can establish what the stated rule would have produced on independent data.
It cannot establish what the claimant actually traded, and the UI says so.

## Requirements

### Requirement 1: Claim schema

**User Story:** As a viewer of a trading reel, I want to enter the claim in a structured
form, so that it can be frozen and tested exactly.

#### Acceptance Criteria

1. THE claim type `reel.mechanical.v1` SHALL accept parameters: `instrument` (from the source's listed spot symbols), `timeframe ∈ {1h, 4h, 1d}`, `start` and `end` (UTC dates, end exclusive), `template`, `template_params`, `instrument_mode = SPOT_LONG_FLAT`.
2. THE claim type SHALL accept templates `BUY_AND_HOLD`, `SMA_CROSS(fast, slow)`, `DONCHIAN_BREAKOUT(lookback)`, `RSI_REVERSION(period, lower, upper)` with integer periods 2–400 and `fast < slow`, `0 < lower < upper < 100`.
3. THE claim type SHALL accept outcomes: `total_return_pct` (required), and optionally `max_drawdown_pct`, `trade_count`, `win_rate_pct`, each as a decimal string.
4. THE claim type SHALL accept assumptions `fee_bps_per_side`, `slippage_bps_per_side`, `position_fraction`, each fixed, ranged, a set, or missing.
5. IF a 1h claim spans more than 366 days THEN THE claim type SHALL reject it at intake.
6. THE frozen claim schema SHALL contain no field for a person's name, handle, or URL of the original post (paste intake: Requirement 8).

### Requirement 2: Strategy signal semantics

**User Story:** As a sceptic, I want each template defined exactly, so that a reproduction is
the strategy and not my guess at it.

#### Acceptance Criteria

1. THE evaluator SHALL compute the target position for bar *t* using only bars `0..t`.
2. THE evaluator SHALL define `SMA_CROSS` as target 1 when SMA(fast) of closes > SMA(slow) of closes at bar *t* (both defined), else 0.
3. THE evaluator SHALL define `DONCHIAN_BREAKOUT` as: enter (target 1) when close_t > max(high over the previous `lookback` bars); exit (target 0) when close_t < min(low over the previous `lookback` bars); otherwise keep the previous target.
4. THE evaluator SHALL define `RSI_REVERSION` with Wilder's RSI on closes (seed = simple average of the first `period` gains/losses; RSI = 100 when average loss is 0): enter when RSI < lower, exit when RSI > upper, otherwise keep the previous target.
5. THE evaluator SHALL define `BUY_AND_HOLD` as target 1 from bar 0.

### Requirement 3: Execution and accounting

**User Story:** As a sceptic, I want fills and costs stated, so that results are comparable.

#### Acceptance Criteria

1. WHEN the target at bar *t* differs from the current position THE simulator SHALL fill at the open of bar *t+1*; a target change on the final bar SHALL NOT fill.
2. THE simulator SHALL apply buy fills at `open × (1 + slippage)` and sell fills at `open × (1 − slippage)`, and charge `fee = notional × fee_bps / 10 000` per fill.
3. WHEN entering THE simulator SHALL buy units worth `position_fraction × equity` including fees; WHEN exiting it SHALL sell all units.
4. THE simulator SHALL start with equity 10 000 (scale-free; returns are reported) and SHALL keep `cash ≥ 0` and `units ≥ 0` at all times.
5. THE simulator SHALL mark equity at every bar close as `cash + units × close` and SHALL mark open positions at the final close without liquidating.

### Requirement 4: Metrics

#### Acceptance Criteria

1. THE evaluator SHALL compute `total_return_pct = (E_final / E_0 − 1) × 100`.
2. THE evaluator SHALL compute `max_drawdown_pct` as the maximum of `(peak − E_t) / peak × 100` over close-marked equity.
3. THE evaluator SHALL compute `trade_count` as the number of entry fills.
4. THE evaluator SHALL compute `win_rate_pct` as winning closed round trips (net of fees and slippage) divided by closed round trips × 100; with zero closed round trips the metric SHALL be undefined and its finding `INDETERMINATE`.

### Requirement 5: Evidence

**User Story:** As a judge, I want the price data independent of the claimant and traceable.

#### Acceptance Criteria

1. THE evidence adapter SHALL fetch OHLCV only from sources in the Reel source registry, each with a recorded license class.
2. THE evidence adapter SHALL reject user-uploaded price data in judge mode.
3. WHEN any expected bar in the range is missing THE claim type SHALL report the coverage finding `INDETERMINATE` with the first missing bar timestamp, and SHALL mark every reproduction finding `INDETERMINATE(evidence_gap)`. Gaps SHALL NOT be filled or interpolated.
4. THE evidence adapter SHALL parse prices from text into `Decimal` without passing through `float`.
5. THE source registry SHALL record each source's `rights_basis` (`VERIFIED` with a documented basis, or `UNVERIFIED`). Binance and Coinbase are `REFETCH_ONLY` and `UNVERIFIED` until the team documents a rights basis (decision B1, 2026-11-16).
6. THE repository SHALL include clearly labelled synthetic OHLCV fixtures (`SYNTHETIC_FIXTURE`) for tests and `SYNTHETIC_DEMO` cases; they SHALL never be used in `LIVE_EVIDENCE` cases.

### Requirement 6: Reproduction findings

#### Acceptance Criteria

1. THE claim type SHALL produce one `EXTERNAL_EVIDENCE` finding per claimed metric.
2. THE comparator SHALL apply a precision tolerance equal to half a unit in the last digit the claimant stated (e.g. "340" ⇒ ±0.5; "340.2" ⇒ ±0.05).
3. WHEN the computed metric is within tolerance at every grid point THE finding SHALL be `SUPPORTED`; at no grid point, `REFUTED`; otherwise `CONDITIONAL` with counterexample points.
4. WHEN missing assumptions have no policy default THE dependent findings SHALL be `INDETERMINATE(missing_assumption:<name>)`.
5. THE default policy ranges SHALL be: `fee_bps_per_side ∈ {0, 10, 25, 50}`, `slippage_bps_per_side ∈ {0, 5, 10, 25}`, `position_fraction = 1`, all disclosed with origin `DEFAULT_POLICY`.

### Requirement 7: Perfect-foresight bound

**User Story:** As a viewer, I want to know whether a claim is impossible no matter which
strategy was used.

#### Acceptance Criteria

1. WITH bars indexed `0..n−1` (the earliest possible fill is at `open_1`), THE claim type SHALL compute interval returns `r_k` for `k = 1..n−1`, where `r_k = open_{k+1}/open_k − 1` for `k < n−1` and `r_{n−1} = close_{n−1}/open_{n−1} − 1`.
2. THE claim type SHALL compute `bound_pct = (Π(1 + max(r_i, 0)) − 1) × 100` for `SPOT_LONG_FLAT`.
3. WHEN the lower edge of the claimed `total_return_pct` (claimed minus precision tolerance) exceeds `bound_pct` THE finding SHALL be `IMPOSSIBLE`, otherwise `WITHIN_BOUND`.
4. IF `instrument_mode` or the timeframe has origin `DEFAULT_POLICY` THEN THE bound finding SHALL be `INDETERMINATE(bound_requires_declared_mechanics)`.
5. THE UI SHALL state the bound's scope: "No long-or-flat spot strategy trading at most once per bar on this data, without leverage and before costs, could exceed this return."

### Requirement 8: Paste-a-claim intake

#### Acceptance Criteria

1. THE intake SHALL accept at most 2000 characters of pasted text and SHALL reject text containing URLs, @handles, emails or phone numbers (`PRIVACY_REJECTED`); ISO dates SHALL NOT be treated as phone numbers.
2. THE extractor SHALL be deterministic (no LLM) and SHALL return each extracted field with its character span.
3. THE pasted text SHALL never be persisted, logged, frozen or bundled; fields not extracted SHALL appear as `MISSING` in the parameter ledger.

### Requirement 9: Key records

#### Acceptance Criteria

1. THE claim type SHALL judge aggregate claims only on aggregate metrics at grid points.
2. THE presentation SHALL mark trades and equity series `ILLUSTRATIVE` and SHALL use only `GRID_POINT` records as `COUNTEREXAMPLE`.
