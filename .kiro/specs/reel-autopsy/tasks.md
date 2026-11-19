# Implementation Plan — Reel Autopsy

Window: Nov 23–26 (core gate must be green first).

- [ ] 5.0 PRIORITY (before any UI polish): obtain a historical OHLCV source with a documented rights basis for a public app. Free candidates checked 2026-11-16 are non-commercial (Binance Vision, CryptoDataDownload: CC BY-NC-SA 4.0). Options: a paid licence that explicitly permits this use (e.g. CoinAPI flat files/API), or written permission from a provider. Record the basis in the source registry; until then live Reel cases stay BLOCKED.

- [x] 1. Bars and coverage (`bars.py`)
  - [x] 1.1 Decimal bar type; expected timestamps per timeframe; gap finder
  - _Requirements: 5.3, 5.4_

- [x] 2. Strategy templates (`strategies.py`)
  - [x] 2.1 SMA_CROSS, DONCHIAN_BREAKOUT, RSI_REVERSION (Wilder), BUY_AND_HOLD
  - [x] 2.2 Property test P13 — contract: `test_reel_contract.py::test_no_lookahead`
  - _Requirements: 2.1–2.5_

- [x] 3. Simulator and metrics (`simulator.py`, `metrics.py`)
  - [x] 3.1 Next-open fills, fee/slippage, fraction sizing, cash/units invariants
  - [x] 3.2 Metrics per Requirement 4
  - [x] 3.3 Property tests P14, P15b — contract: `test_reel_contract.py`
  - _Requirements: 3.1–3.5, 4.1–4.4_

- [x] 4. Bound (`bound.py`)
  - [x] 4.1 Interval returns, bound, oracle targets
  - [x] 4.2 Property test P15 — contract: `test_reel_contract.py::test_bound_sound_and_tight`
  - _Requirements: 7.1–7.4_

- [ ] 5. Evidence adapter (`sources/`)
  - [ ] 5.1 Source chosen at decision B1; license class recorded; text→Decimal parsing
  - [ ] 5.2 Fixture bars for tests and demo, stored only if the source is REDISTRIBUTABLE
  - _Requirements: 5.1, 5.2, 5.4_

- [ ] 6. Claim type (`claim_type.py`, `tolerance.py`)
  - [ ] 6.1 Schema, policy defaults, examine/findings split
  - [ ] 6.2 Precision tolerance; IMPOSSIBLE gating on declared mechanics
    - Precision tolerance done (`tolerance.py`); the claim type is a fail-closed scaffold until evidence (5.0) exists.
  - _Requirements: 1.1–1.6, 6.1–6.5, 7.3–7.5_

- [ ] 7. UI (`web/`) on the shared ui-kit
  - [ ] 7.1 Claim form, toe-tag verdict, findings list, sweep heatmap, equity chart, bound gauge, bundle download
  - _Requirements: 7.5_

- [ ] 8. Demo fixtures (B1): labelled synthetic OHLCV + three fixture-only (`fixtureId`) SYNTHETIC_DEMO claims (one SUPPORTED, one CONDITIONAL, one IMPOSSIBLE) whose results are computed by the engine. Real-data claims only after a rights basis is documented.

- [x] 9. Intake and presentation
  - [x] 9.1 `intake_text.py` (privacy + deterministic extraction) — contract: `test_reel_intake_presentation.py`
  - [x] 9.2 `presentation.py` key records — contract: same file
  - _Requirements: 8, 9_
