"""VerdictKit adapter for reel.mechanical.v1 (reel requirements 1-7, 9).

Evidence is the only source of prices. With no hash-verified OHLCV evidence (every
LIVE_EVIDENCE case until a licensed source exists, decision B1) every finding is
INDETERMINATE(evidence_unavailable). The only evidence source wired today is the
labelled synthetic fixture (``sources.synthetic``), which the core forbids in
LIVE_EVIDENCE cases; with it the full evaluator runs (simulator, metrics, bound).

Assumptions (Req 1.4, 6.5): ``fee_bps_per_side``, ``slippage_bps_per_side`` and
``position_fraction``; a missing or omitted one is swept over the policy default and
disclosed with origin DEFAULT_POLICY. A declared value is CLAIMANT.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from typing import Mapping, Sequence

from verdictkit.custody.intake import SchemaError
from verdictkit.model import (
    Assumption, AssumptionKind, Basis, BlindedTask, Counterexample, EvidenceItem, Finding,
    FrozenClaim, Origin, Status,
)
from verdictkit.plugin import (
    EvidencePolicySpec, EvidenceReader, EvidenceRequest, Examination, PointResult,
)
from verdictkit.sweep import AggregateKind, PointOutcome, aggregate

from .bars import Bar, Timeframe, find_gaps, parse_decimal
from .bound import perfect_foresight_bound_pct
from .metrics import max_drawdown_pct, total_return_pct, trade_count, win_rate_pct
from .simulator import CostModel, simulate
from .sources import synthetic
from .strategies import Template, target_positions, validate_params as validate_strategy
from .tolerance import precision_tolerance

METRICS = ("total_return_pct", "max_drawdown_pct", "trade_count", "win_rate_pct")
BOUND_ID = "total_return_bound"
POLICY_DEFAULTS: Mapping[str, tuple[str, ...]] = {
    "fee_bps_per_side": ("0", "10", "25", "50"),
    "slippage_bps_per_side": ("0", "5", "10", "25"),
    "position_fraction": ("1",),
}
_Q = Decimal("1e-8")
BOUND_SCOPE = ("No long-or-flat spot strategy trading at most once per bar on this data, "
               "without leverage and before costs, could exceed this return.")


def _epoch(text: str) -> int:
    return int(datetime.combine(date.fromisoformat(text), datetime.min.time(),
                                tzinfo=timezone.utc).timestamp())


def _q(value: Decimal) -> str:
    with localcontext() as ctx:
        ctx.prec = 60
        return format(value.quantize(_Q), "f")


def _parse_bars(data: bytes) -> tuple[Bar, ...]:
    bars = []
    for line in data.decode("ascii").splitlines():
        if not line or line.startswith("#") or line.startswith("ts,"):
            continue
        parts = line.split(",")
        if len(parts) != 6 or not parts[0].isdecimal():
            raise ValueError("malformed OHLCV row")
        o, h, l, c, v = (parse_decimal(x) for x in parts[1:])
        if not (l <= min(o, c) and h >= max(o, c)):
            raise ValueError("inconsistent OHLC row")
        bars.append(Bar(int(parts[0]), o, h, l, c, v))
    if [b.ts for b in bars] != sorted({b.ts for b in bars}):
        raise ValueError("OHLCV rows must be strictly increasing")
    return tuple(bars)


def _declared_axis(name: str, raw: object) -> Assumption:
    try:
        if raw is None:
            return Assumption(name, AssumptionKind.SET, Origin.DEFAULT_POLICY,
                              values=tuple(Decimal(v) for v in POLICY_DEFAULTS[name]))
        if isinstance(raw, str):
            return Assumption(name, AssumptionKind.FIXED, Origin.CLAIMANT, value=Decimal(raw))
        if isinstance(raw, dict) and set(raw) == {"set"} and isinstance(raw["set"], list) \
                and raw["set"] and all(isinstance(v, str) for v in raw["set"]):
            return Assumption(name, AssumptionKind.SET, Origin.CLAIMANT,
                              values=tuple(Decimal(v) for v in raw["set"]))
        if isinstance(raw, dict) and set(raw) == {"min", "max", "step"} \
                and all(isinstance(raw[k], str) for k in raw):
            return Assumption(name, AssumptionKind.RANGE, Origin.CLAIMANT,
                              minimum=Decimal(raw["min"]), maximum=Decimal(raw["max"]),
                              step=Decimal(raw["step"]))
    except InvalidOperation as exc:
        raise SchemaError(f"invalid assumption {name}") from exc
    raise SchemaError(f"assumption {name} must be a decimal string, a set, a range or null")


class ReelClaimType:
    type_id = "reel.mechanical.v1"
    schema_version = 1
    param_fields = frozenset({"instrument", "timeframe", "start", "end", "template", "template_params", "instrument_mode"})
    outcome_fields = frozenset(METRICS)

    def validate_params(self, params: Mapping[str, object]) -> None:
        if set(params) != self.param_fields:
            raise SchemaError(f"reel params require exactly {sorted(self.param_fields)}")
        if not isinstance(params["instrument"], str) or not params["instrument"].strip() or len(params["instrument"]) > 32:
            raise SchemaError("invalid instrument")
        if params["timeframe"] not in ("1h", "4h", "1d"):
            raise SchemaError("timeframe must be 1h, 4h or 1d")
        if not isinstance(params["start"], str) or not isinstance(params["end"], str):
            raise SchemaError("start and end must be date strings")
        try:
            start = date.fromisoformat(params["start"])
            end = date.fromisoformat(params["end"])
        except ValueError as exc:
            raise SchemaError("invalid ISO dates") from exc
        if start >= end:
            raise SchemaError("start must precede end")
        if params["timeframe"] == "1h" and (end - start).days > 366:
            raise SchemaError("1h claims may span at most 366 days")  # Req 1.5
        if params["instrument_mode"] != "SPOT_LONG_FLAT":
            raise SchemaError("only SPOT_LONG_FLAT supported")
        try:
            template = Template(params["template"])
        except (ValueError, TypeError) as exc:
            raise SchemaError("unsupported template") from exc
        if not isinstance(params["template_params"], dict):
            raise SchemaError("template_params must be a mapping")
        try:
            validate_strategy(template, params["template_params"])
        except ValueError as exc:
            raise SchemaError(str(exc)) from exc

    def extract_text(self, text: str) -> tuple[dict, dict, dict[str, tuple[int, int]]]:
        """Optional intake hook (API contract §8): deterministic, no LLM, no persistence.

        Returns (params, outcomes, spans). Every parameter is present; values not found
        in the text are None (MISSING). Raises ValueError("privacy:<kinds>") for URLs,
        handles, emails, phone numbers or text over 2000 characters.
        """
        from .intake_text import extract, privacy_violations
        issues = privacy_violations(text)
        if issues:
            raise ValueError("privacy:" + ",".join(issues))
        found = extract(text)
        params: dict[str, object] = {name: None for name in self.param_fields}
        outcomes: dict[str, object] = {}
        spans: dict[str, tuple[int, int]] = {}
        template_params: dict[str, int] = {}
        for f in found.fields:
            if f.name.startswith("template_params."):
                template_params[f.name.split(".", 1)[1]] = int(f.value)
                continue
            if f.name in self.outcome_fields:
                outcomes.setdefault(f.name, f.value)
                continue
            if f.name in params and params[f.name] is None:
                params[f.name] = f.value
                spans[f.name] = (f.start, f.end)
        if template_params:
            params["template_params"] = template_params
        return params, outcomes, spans

    def validate_outcomes(self, outcomes: Mapping[str, object]) -> None:
        if not outcomes or not set(outcomes) <= self.outcome_fields:
            raise SchemaError("at least one recognized outcome required")
        for key, value in outcomes.items():
            if not isinstance(value, str):
                raise SchemaError(f"{key} must be a decimal string")
            try:
                precision_tolerance(value)
            except ValueError as exc:
                raise SchemaError(f"invalid {key}") from exc

    def assumption_specs(self, declared: Mapping[str, object]) -> tuple[Assumption, ...]:
        unknown = set(declared) - set(POLICY_DEFAULTS)
        if unknown:
            raise SchemaError(f"unknown assumptions: {sorted(unknown)}")
        return tuple(_declared_axis(name, declared.get(name)) for name in sorted(POLICY_DEFAULTS))

    def tolerances(self, params: Mapping[str, object], outcomes: Mapping[str, object]) -> Mapping[str, str]:
        return {key: format(precision_tolerance(value), "f") for key, value in outcomes.items()}

    def evidence_requests(self, params: Mapping[str, object]) -> Sequence[EvidenceRequest]:
        # Only the labelled synthetic series has an adapter. No real data provider is
        # invented: other instruments get no request and stay evidence_unavailable.
        if params.get("instrument") == synthetic.INSTRUMENT:
            return (EvidenceRequest(synthetic.SOURCE_ID, {
                "instrument": params["instrument"], "timeframe": params["timeframe"],
                "start": params["start"], "end": params["end"]}),)
        return ()

    def evidence_policy(self) -> EvidencePolicySpec:
        return EvidencePolicySpec(frozenset({synthetic.SOURCE_ID}))

    def evidence_adapters(self):
        return (synthetic.SyntheticFixtureAdapter(),)

    def fixtures(self) -> Mapping[str, Mapping[str, object]]:
        from .fixtures import FIXTURES
        return FIXTURES

    # ---- Examiner side -------------------------------------------------------------
    def examine(self, task: BlindedTask, evidence: EvidenceReader, points: Sequence[Mapping[str, str]]) -> Examination:
        if not task.evidence_refs or evidence is None:
            return Examination(
                spec_hash=task.spec_hash,
                shared={"coverage": "UNVERIFIED", "reason": "evidence_unavailable"},
                points=tuple(PointResult(dict(p), {}) for p in points),
                missing_assumptions=("verified_ohlcv_evidence",),
            )
        params = task.params
        timeframe = Timeframe(params["timeframe"])
        start_ts, end_ts = _epoch(params["start"]), _epoch(params["end"])
        bars = tuple(b for b in _parse_bars(evidence.read(task.evidence_refs[0]))
                     if start_ts <= b.ts < end_ts)
        gaps = find_gaps(bars, start_ts, end_ts, timeframe)
        if gaps or len(bars) < 2:
            return Examination(task.spec_hash, {
                "coverage": "GAP", "first_missing_ts": gaps[0] if gaps else start_ts,
                "bar_count": len(bars)}, tuple(PointResult(dict(p), {}) for p in points))
        template = Template(params["template"])
        targets = target_positions(template, params["template_params"], bars)
        results = []
        curve: list[str] = []
        for p in points:
            costs = CostModel(Decimal(p["fee_bps_per_side"]), Decimal(p["slippage_bps_per_side"]))
            sim = simulate(bars, targets, costs, Decimal(p["position_fraction"]))
            values: dict[str, object] = {
                "total_return_pct": _q(total_return_pct(sim)),
                "max_drawdown_pct": _q(max_drawdown_pct(sim)),
                "trade_count": trade_count(sim),
            }
            win = win_rate_pct(sim)
            if win is not None:
                values["win_rate_pct"] = _q(win)
            if not curve:  # first grid point (lowest costs): illustrative equity series
                step = max(1, len(sim.marks) // 120)
                curve = [_q(m.equity.quantize(Decimal("0.01"))) for m in sim.marks[::step]]
            results.append(PointResult(dict(p), values))
        shared = {"coverage": "COMPLETE", "bar_count": len(bars),
                  "bound_pct": _q(perfect_foresight_bound_pct(bars)),
                  "equity_curve_first_point": curve}
        return Examination(task.spec_hash, shared, tuple(results))

    # ---- Custodian side, after reveal ----------------------------------------------
    def _outcomes_per_point(self, frozen, examination, outcomes) -> dict[str, list[PointOutcome]]:
        out: dict[str, list[PointOutcome]] = {}
        for name, claimed in outcomes.items():
            tol = Decimal(frozen.tolerances[name])
            rows = []
            for pr in examination.points:
                if name not in pr.values:
                    break
                diff = Decimal(claimed) - Decimal(str(pr.values[name]))
                rows.append(PointOutcome(dict(pr.point), abs(diff) <= tol, tol - abs(diff)))
            else:
                out[name] = rows
        return out

    def point_outcomes(self, frozen: FrozenClaim, examination: Examination,
                       outcomes: Mapping[str, object]) -> Mapping[str, Sequence[PointOutcome]]:
        """Presentation hook: per-grid-point pass/fail for the sensitivity view."""
        if examination.shared.get("coverage") != "COMPLETE":
            return {}
        return self._outcomes_per_point(frozen, examination, outcomes)

    def findings(
        self, frozen: FrozenClaim, examination: Examination,
        outcomes: Mapping[str, object], evidence: Sequence[EvidenceItem],
    ) -> Sequence[Finding]:
        coverage = examination.shared.get("coverage")
        if coverage != "COMPLETE":
            reason = "evidence_gap" if coverage == "GAP" else "evidence_unavailable"
            used = tuple(e.sha256 for e in evidence) if coverage == "GAP" else ()
            return tuple(
                Finding(key, Basis.EXTERNAL_EVIDENCE if used else Basis.MECHANICAL_BOUND,
                        Status.INDETERMINATE,
                        f"{key} cannot be evaluated without complete, hash-verified OHLCV evidence",
                        reason=reason, evidence_used=used)
                for key in sorted(outcomes)
            )
        used = tuple(e.sha256 for e in evidence)
        axes = tuple(sorted({k for pr in examination.points for k in pr.point}))
        n = len(examination.points)
        per_point = self._outcomes_per_point(frozen, examination, outcomes)
        results: list[Finding] = []
        for name in sorted(outcomes):
            tol = frozen.tolerances[name]
            rows = per_point.get(name)
            if rows is None:
                results.append(Finding(name, Basis.EXTERNAL_EVIDENCE, Status.INDETERMINATE,
                    f"{name} is undefined at one or more grid points (no closed round trips)",
                    reason="metric_undefined", evidence_used=used, assumption_dependencies=axes))
                continue
            agg = aggregate(rows)
            status = {AggregateKind.ALL_PASS: Status.SUPPORTED,
                      AggregateKind.NONE_PASS: Status.REFUTED,
                      AggregateKind.MIXED: Status.CONDITIONAL}[agg.kind]

            def cex(po: PointOutcome, note: str, name: str = name, tol: str = tol) -> Counterexample:
                computed = next(pr.values[name] for pr in examination.points if dict(pr.point) == dict(po.point))
                diff = Decimal(outcomes[name]) - Decimal(str(computed))
                return Counterexample(dict(po.point), str(computed), str(outcomes[name]),
                                      _q(diff), tol, note)

            ces: tuple[Counterexample, ...] = ()
            if status is Status.REFUTED:
                ces = (cex(agg.first_fail, "first failing grid point"),)
            elif status is Status.CONDITIONAL:
                ces = (cex(agg.first_fail, "first failing grid point"),
                       cex(agg.first_pass, "first passing grid point"))
            worst = cex(agg.worst, "worst grid point by margin")
            results.append(Finding(
                name, Basis.EXTERNAL_EVIDENCE, status,
                f"Reproduced {name} on the cited OHLCV evidence; verified at {n} grid points",
                evidence_used=used, assumption_dependencies=axes, counterexamples=ces,
                numbers={"expected": worst.expected, "observed": worst.observed,
                         "difference": worst.difference, "tolerance": tol}))
        if "total_return_pct" in outcomes:
            claimed = Decimal(outcomes["total_return_pct"])
            tol = Decimal(frozen.tolerances["total_return_pct"])
            bound = Decimal(examination.shared["bound_pct"])
            impossible = claimed - tol > bound  # Req 7.3; mechanics are claimant-declared (B6)
            diff = _q(claimed - bound)
            ce = (Counterexample({}, examination.shared["bound_pct"], outcomes["total_return_pct"],
                                 diff, format(tol, "f"), "claim exceeds the perfect-foresight bound"),)
            results.append(Finding(
                BOUND_ID, Basis.MECHANICAL_BOUND,
                Status.IMPOSSIBLE if impossible else Status.WITHIN_BOUND,
                "Claimed total return vs the perfect-foresight bound. " + BOUND_SCOPE,
                evidence_used=used, counterexamples=ce if impossible else (),
                numbers={"expected": examination.shared["bound_pct"],
                         "observed": outcomes["total_return_pct"], "difference": diff,
                         "tolerance": format(tol, "f")}))
        return tuple(results)

    def diagnose(self, frozen: FrozenClaim, examination: Examination, outcomes: Mapping[str, object]) -> Mapping[str, object] | None:
        return None
