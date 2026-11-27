/**
 * Presentation components. Every value shown comes from an API response; nothing is
 * computed or defaulted into a verdict here. Wording follows docs/API_CONTRACT.md:
 * "verified at N grid points", integrity / reproducibility / authenticity kept separate,
 * and the demonstration notice rendered on every synthetic view.
 */
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import type { Client } from "./api";
import { BlockedError, followRun } from "./api";
import { describeError, Spinner } from "./shell";
import { VerificationReport } from "./verification";
import type {
  BundleMetadata, DraftCase, EvidenceDTO, FindingDTO, Health, IntakeRequest, KeyRecord,
  OutcomeResponse, ParameterEntry, ProgressEvent, ReplayReport, Sensitivity, Blocker, IsolationMode,
} from "./types";

const PASSING = new Set(["CONSISTENT", "SUPPORTED", "WITHIN_BOUND"]);
export function statusTone(status: string | null): "pass" | "fail" | "warn" | "none" {
  if (status === null) return "none";
  if (PASSING.has(status)) return "pass";
  if (status === "CONDITIONAL" || status === "INDETERMINATE") return "warn";
  return "fail";
}

/** What each result word means, in plain language. Internal contradictions and external refutations stay separate kinds. */
export const STATUS_MEANING: Record<string, { glyph: string; kind: string; plain: string }> = {
  CONSISTENT: { glyph: "✓", kind: "Internal arithmetic", plain: "The stated figure follows from the claim's own inputs at every grid point verified." },
  CONTRADICTED: { glyph: "✗", kind: "Internal arithmetic", plain: "The stated figure cannot be produced from the claim's own inputs at the grid points verified. This is a contradiction inside the claim, not a finding about outside facts." },
  SUPPORTED: { glyph: "✓", kind: "External evidence", plain: "Independent evidence agrees with the claim at the grid points verified." },
  REFUTED: { glyph: "✗", kind: "External evidence", plain: "Independent evidence disagrees with the claim." },
  CONDITIONAL: { glyph: "◐", kind: "Depends on an assumption", plain: "The claim holds under some assumptions and fails under others, and the claim does not say which applies." },
  WITHIN_BOUND: { glyph: "✓", kind: "Mathematical bound", plain: "The claimed result is at or below the ceiling the declared mechanics allow. That does not show it was achieved." },
  IMPOSSIBLE: { glyph: "⊘", kind: "Mathematical bound", plain: "Under the mechanics declared for this claim, the claimed result is above the ceiling anything could reach." },
  INDETERMINATE: { glyph: "?", kind: "Cannot be determined", plain: "There is not enough verifiable evidence or information to decide. This is an answer, not a failure." },
};

/** Thousands separators for decimal strings without ever converting them to a binary float. */
export function fmtNumber(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const m = /^(-?)(\d+)(\.\d+)?$/.exec(value);
  if (!m) return value;
  return `${m[1]}${m[2].replace(/\B(?=(\d{3})+(?!\d))/g, ",")}${m[3] ?? ""}`;
}

const pretty = (id: string) => id.replace(/^stated_/, "").replace(/_/g, " ");

export function StatusBadge({ status }: { status: string | null }) {
  const glyph = status ? STATUS_MEANING[status]?.glyph : null;
  return <span className={`vk-badge vk-${statusTone(status)}`}>{glyph ? <span aria-hidden="true">{glyph}</span> : null}{status ?? "NO VERDICT"}</span>;
}

/** A collapsible key to the result words, for readers with no background in the domain. */
export function StatusLegend({ statuses }: { statuses: string[] }) {
  return (
    <details className="vk-help" data-testid="status-legend">
      <summary>How to read the result words</summary>
      <ul>{statuses.filter((s) => STATUS_MEANING[s]).map((s) => (
        <li key={s}><StatusBadge status={s} /> <b>{STATUS_MEANING[s].kind}.</b> {STATUS_MEANING[s].plain}</li>
      ))}</ul>
      <p className="vk-muted">Not every claim can be checked. INDETERMINATE and CONDITIONAL are real answers, and a result is only ever "verified at N grid points", never "for all values".</p>
    </details>
  );
}

export function IsolationBanner({ health }: { health: Health | null }) {
  if (!health) return <div className="vk-banner vk-warn">Checking API…</div>;
  return (
    <div className={`vk-banner ${health.isolationMode === "ENFORCED" ? "vk-pass" : "vk-warn"}`} data-testid="isolation">
      Isolation <b>{health.isolationMode}</b>
      {health.isolationMode === "ENFORCED"
        ? " — the examiner runs as a separate OS user and never sees claimed results."
        : " — development mode: OS-level separation is not enforced for this server."}
      {health.judgeMode ? " · judge mode" : ""} · contract {health.contractVersion}
    </div>
  );
}

export function DemoNotice({ notice }: { notice: string | null }) {
  if (!notice) return null;
  return <div className="vk-banner vk-demo" role="note" data-testid="demo-notice">{notice}</div>;
}

export function Blockers({ blockers }: { blockers: Blocker[] }) {
  if (!blockers.length) return null;
  return (
    <div className="vk-card vk-blockers" data-testid="blockers">
      <h3>Blocked: nothing was guessed</h3>
      <p className="vk-muted">The examination needs something that is missing. It stops here instead of judging on invented data.</p>
      <ul>{blockers.map((b, i) => (
        <li key={i}><code>{b.code}</code> {b.message}{b.field ? <> (<code>{b.field}</code>)</> : null}</li>
      ))}</ul>
    </div>
  );
}

function fmtRange(e: ParameterEntry): string {
  if (!e.range) return "";
  return e.range.kind === "SET" ? `{${(e.range.values ?? []).join(", ")}}` : `${e.range.min}…${e.range.max} step ${e.range.step}`;
}

export function ParameterLedger({ entries }: { entries: ParameterEntry[] }) {
  return (
    <div className="vk-scroll">
      <table className="vk-table" data-testid="ledger">
        <thead><tr><th>Parameter</th><th>Value</th><th>State</th><th>Basis</th></tr></thead>
        <tbody>{entries.map((e) => (
          <tr key={e.name} className={e.state === "MISSING" && e.critical ? "vk-row-fail" : undefined}>
            <td><code>{e.name}</code></td>
            <td className="vk-num">{e.value ? fmtNumber(e.value) : (e.range ? `swept ${fmtRange(e)}` : "—")}</td>
            <td>{e.state}</td><td>{e.basis}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

const STAGE_LABEL: Record<string, string> = {
  RUN_QUEUED: "Run queued", TASK_BLINDED: "Blinded task built (no claimed results)",
  EXAMINATION_STARTED: "Examination started", EXAMINATION_PROGRESS: "Examination progress",
  EXAMINATION_COMMITTED: "Examination committed to the ledger", OUTCOMES_REVEALED: "Claimed results revealed",
  VERDICT_SEALED: "Verdict sealed", DIAGNOSTICS_APPENDED: "Diagnostics appended (after reveal)",
  BUNDLE_WRITTEN: "Bundle written", RUN_COMPLETED: "Run completed", RUN_INDETERMINATE: "Run ended indeterminate",
  RUN_BLOCKED: "Run blocked", RUN_FAILED: "Run failed",
};

export function RunProgress({ events }: { events: ProgressEvent[] }) {
  if (!events.length) return null;
  return (
    <ol className="vk-progress" data-testid="progress" aria-label="Chain of custody: what the server recorded">
      {events.map((e) => (
        <li key={e.seq} data-stage={e.stage}>
          <span>{STAGE_LABEL[e.stage] ?? e.stage}</span>
          {e.detail.pointsTotal ? <small> {e.detail.pointsDone ?? 0}/{e.detail.pointsTotal} grid points</small> : null}
          {e.ledgerSeq !== null ? <small> · ledger #{e.ledgerSeq}</small> : null}
        </li>
      ))}
    </ol>
  );
}

export type Phase = "idle" | "intake" | "draft-blocked" | "freezing" | "evidence" | "running" | "done" | "error";
const PHASES: { phase: Phase; label: string }[] = [
  { phase: "intake", label: "1 Intake" }, { phase: "freezing", label: "2 Seal and freeze" }, { phase: "evidence", label: "3 Evidence" },
  { phase: "running", label: "4 Blind examination" }, { phase: "done", label: "5 Verdict" },
];

/** Where the examination is right now. Driven only by the workflow phase the server's responses advanced. */
export function PhaseTracker({ phase }: { phase: Phase }) {
  if (phase === "idle") return null;
  const current = PHASES.findIndex((p) => p.phase === (phase === "draft-blocked" ? "intake" : phase));
  return (
    <ol className="vk-phases" aria-label="Examination progress" data-testid="phases">
      {PHASES.map((p, i) => {
        const cls = phase === "done" || i < current ? "vk-done" : i === current && phase !== "error" ? "vk-now" : undefined;
        return <li key={p.phase} className={cls} aria-current={cls === "vk-now" ? "step" : undefined}>{p.label}</li>;
      })}
    </ol>
  );
}

function NumbersTable({ f }: { f: FindingDTO }) {
  const n = f.numbers;
  if (n.expected == null && n.observed == null) return null;
  return (
    <dl className="vk-numbers">
      <dt>Computed</dt><dd>{fmtNumber(n.expected)}</dd>
      <dt>Claimed</dt><dd>{fmtNumber(n.observed)}</dd>
      <dt>Difference</dt><dd>{fmtNumber(n.difference)}</dd>
      <dt>Tolerance</dt><dd>±{fmtNumber(n.tolerance)}</dd>
    </dl>
  );
}

/**
 * Claimed figure against the engine's result on one shared scale. Geometry only; every number is the API's.
 * When either value is negative the scale has a zero line in the middle, so a loss is never drawn as a gain.
 */
function BoundBars({ f }: { f: FindingDTO }) {
  const { expected, observed } = f.numbers;
  if (expected == null || observed == null) return null;
  const e = Number(expected), o = Number(observed);
  if (!Number.isFinite(e) || !Number.isFinite(o)) return null;
  const max = Math.max(Math.abs(e), Math.abs(o)) || 1;
  const diverging = e < 0 || o < 0;
  const span = (v: number) => {
    if (!diverging) return { left: "0%", width: `${Math.max(2, (v / max) * 100).toFixed(1)}%` };
    const half = Math.max(1, (Math.abs(v) / max) * 50);
    return { left: v < 0 ? `${(50 - half).toFixed(1)}%` : "50%", width: `${half.toFixed(1)}%` };
  };
  const track = (v: number) => (
    <span className="vk-track" style={{ position: "relative" }}>
      {diverging ? <span style={{ position: "absolute", left: "50%", top: 0, bottom: 0, borderLeft: "1px solid #52615f" }} /> : null}
      <span className="vk-fill" style={{ position: "absolute", top: 0, bottom: 0, ...span(v) }} />
    </span>
  );
  return (
    <div className="vk-bars" aria-hidden="true" data-testid={`bars-${f.findingId}`}>
      <div className="vk-bar"><span>Engine result</span>{track(e)}<b>{fmtNumber(expected)}</b></div>
      <div className={`vk-bar vk-claimed ${statusTone(f.status) === "fail" ? "vk-fail" : ""}`}><span>Claimed</span>{track(o)}<b>{fmtNumber(observed)}</b></div>
      {diverging ? <div className="vk-muted" style={{ fontSize: ".74rem", margin: 0 }}>The line in the middle of each bar is zero: bars to its left are negative.</div> : null}
    </div>
  );
}

interface LocalCheck { line: string; stated: string; fromStatedPredecessors: string; difference: string; consistent: boolean }
interface Packing { impliedAmountFinanced: string; inversionUncertainty: string; itemisedAmountFinanced: string; unexplainedAmount: string }

export interface Explanation { title: string; paragraphs: string[]; uncertain: string[] }

/**
 * A plain-language account of why a verdict is not a pass. Every sentence is assembled from fields the engine
 * returned (a finding's numbers, its sensitivity results, and the after-reveal diagnostic); nothing is decided
 * or computed here, and a verdict that passes gets no explanation.
 */
export function explainOutcome(outcome: OutcomeResponse): Explanation | null {
  const status = outcome.headline.status;
  if (!status || statusTone(status) === "pass") return null;
  const paragraphs: string[] = [];
  const named = (f: FindingDTO) => pretty(f.findingId);
  const point = outcome.findings.find((f) => f.pointOfFailure) ?? outcome.findings.find((f) => f.status === status);
  const diag = (outcome.diagnostics?.items?.[0] ?? null) as { firstBrokenLine?: string; localChecks?: LocalCheck[]; paymentPacking?: Packing } | null;
  let title = "Why this verdict";
  if (status === "CONTRADICTED") {
    title = "Where the worksheet contradicts itself";
    const check = diag?.localChecks?.find((c) => c.line === diag.firstBrokenLine);
    if (check) {
      paragraphs.push(`The first line that breaks is ${pretty(check.line)}. The worksheet states ${fmtNumber(check.stated)}, but the lines before it, as the worksheet itself states them, give ${fmtNumber(check.fromStatedPredecessors)}: a difference of ${fmtNumber(check.difference)}.`);
      const later = (diag?.localChecks ?? []).filter((c) => c.consistent).length;
      if (later > 0) paragraphs.push(`${later} other line${later === 1 ? "" : "s"} follow correctly from their predecessors, so the error entered once and was carried through the rest.`);
    } else if (point?.numbers.expected != null && point.numbers.observed != null) {
      paragraphs.push(`${named(point)} is the point of failure. The worksheet states ${fmtNumber(point.numbers.observed)}; the engine computes ${fmtNumber(point.numbers.expected)} from the itemised inputs (difference ${fmtNumber(point.numbers.difference)}, tolerance ±${fmtNumber(point.numbers.tolerance)}).`);
    }
    const p = diag?.paymentPacking;
    if (p) paragraphs.push(`Working backwards from the stated monthly payment, the amount financed would have to be about ${fmtNumber(p.impliedAmountFinanced)} (±${fmtNumber(p.inversionUncertainty)}). The itemised lines explain ${fmtNumber(p.itemisedAmountFinanced)}. About ${fmtNumber(p.unexplainedAmount)} is not accounted for by any line. This diagnostic is computed after the reveal and does not change the verdict.`);
    paragraphs.push("This is a contradiction inside the worksheet's own arithmetic. It is not a finding about outside facts, and it does not say anyone intended it.");
  } else if (status === "IMPOSSIBLE") {
    title = "Why the claim is above the ceiling";
    if (point?.numbers.expected != null && point.numbers.observed != null) {
      paragraphs.push(`The claimed result is ${fmtNumber(point.numbers.observed)}. Under the mechanics declared for this claim, nothing could exceed ${fmtNumber(point.numbers.expected)}: that is the result of a strategy with perfect foresight of every price. The claim is ${fmtNumber(point.numbers.difference)} above it.`);
    }
    paragraphs.push("This holds only under the declared mechanics and the data used. It does not say the claimant lied; it says the claim cannot be what the stated rule produced.");
  } else if (status === "CONDITIONAL") {
    title = "Why the answer depends on an assumption";
    for (const f of outcome.findings.filter((x) => x.status === "CONDITIONAL")) {
      const grid = outcome.sensitivity?.results.find((r) => r.findingId === f.findingId);
      const total = grid ? grid.passCount + grid.failCount : f.gridPointsEvaluated;
      paragraphs.push(`${named(f)} holds at ${grid ? grid.passCount : "some"} of ${total} grid point${total === 1 ? "" : "s"} verified${grid ? ` and fails at ${grid.failCount}` : ""}. Which applies depends on ${f.assumptionDependencies.length ? f.assumptionDependencies.join(", ") : "an assumption the claim does not state"}, and the claim does not say which.`);
    }
    paragraphs.push("A conditional result is not a failure. It marks exactly the assumption that would decide the question.");
  } else if (status === "REFUTED") {
    title = "Where outside evidence disagrees";
    if (point?.numbers.expected != null && point.numbers.observed != null) paragraphs.push(`${named(point)}: the evidence gives ${fmtNumber(point.numbers.expected)} where the claim says ${fmtNumber(point.numbers.observed)}.`);
  } else if (status === "INDETERMINATE") {
    title = "Why this could not be decided";
    for (const f of outcome.findings.filter((x) => x.status === "INDETERMINATE")) paragraphs.push(`${named(f)}: ${f.statement}${f.reason ? ` (${f.reason})` : ""}`);
    paragraphs.push("The engine does not guess. Missing evidence or a missing assumption can only make a finding indeterminate, never a pass.");
  }
  const uncertain = outcome.findings.filter((f) => (f.status === "CONDITIONAL" || f.status === "INDETERMINATE") && f.status !== status)
    .map((f) => `${named(f)} is ${f.status}: ${f.statement}${f.reason ? ` (${f.reason})` : ""}`);
  return paragraphs.length || uncertain.length ? { title, paragraphs, uncertain } : null;
}

export function WhyThisVerdict({ outcome }: { outcome: OutcomeResponse }) {
  const why = explainOutcome(outcome);
  if (!why) return null;
  return (
    <section className="vk-explain" data-testid="why-verdict" aria-label="Why this verdict">
      <h3>{why.title}</h3>
      {why.paragraphs.map((p, i) => <p key={i}>{p}</p>)}
      {why.uncertain.length ? (
        <div className="vk-uncertain" data-testid="also-uncertain"><b>Also uncertain</b>{why.uncertain.map((u, i) => <p key={i}>{u}</p>)}</div>
      ) : null}
    </section>
  );
}

/**
 * Keeps the result in view: on submit the page jumps to the progress, and when the run ends it jumps to the verdict,
 * so a click on a sample never appears to do nothing while the answer sits below the fold.
 */
export function useScrollToResult(phase: Phase, doneSelector = "[data-testid=verdict]", startSelector = "#result-h") {
  const previous = useRef<Phase>("idle");
  useEffect(() => {
    const before = previous.current;
    previous.current = phase;
    if (phase === before) return;
    const reduce = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const options: ScrollIntoViewOptions = { behavior: reduce ? "auto" : "smooth", block: "start" };
    const target = phase === "intake" ? document.querySelector(startSelector)
      : phase === "done" || phase === "error" || phase === "draft-blocked" ? (document.querySelector(doneSelector) ?? document.querySelector(startSelector)) : null;
    target?.scrollIntoView?.(options);
  }, [phase, doneSelector, startSelector]);
}

export function FindingCard({ f }: { f: FindingDTO }) {
  const meaning = STATUS_MEANING[f.status];
  return (
    <article className={`vk-card vk-finding vk-${statusTone(f.status)}`} data-testid={`finding-${f.findingId}`}>
      <header>
        <StatusBadge status={f.status} /> <code>{f.findingId}</code>
        {meaning ? <span className="vk-tag">{meaning.kind}</span> : null}
        {f.pointOfFailure ? <span className="vk-tag">point of failure</span> : null}
        {f.propagated ? <span className="vk-tag">propagated</span> : null}
      </header>
      <p>{f.statement}</p>
      {meaning ? <p className="vk-muted">{meaning.plain}</p> : null}
      {f.reason ? <p className="vk-muted">Reason: <code>{f.reason}</code></p> : null}
      <NumbersTable f={f} />
      {statusTone(f.status) !== "pass" ? <BoundBars f={f} /> : null}
      <p className="vk-muted">
        Verified at {f.gridPointsEvaluated} grid point{f.gridPointsEvaluated === 1 ? "" : "s"}
        {f.assumptionDependencies.length ? <> · depends on {f.assumptionDependencies.join(", ")}</> : null}
      </p>
      <p className="vk-muted">
        Confidence: {f.confidenceClass ?? "none"}{f.confidenceScope ? <> — {f.confidenceScope}</> : null}
      </p>
    </article>
  );
}

/** Line-by-line check: what was stated, what the engine recomputed, and the result. */
export function FindingsTable({ findings }: { findings: FindingDTO[] }) {
  if (!findings.length) return null;
  return (
    <section className="vk-card" data-testid="findings-table">
      <h3>Line-by-line check</h3>
      <div className="vk-scroll">
        <table className="vk-table">
          <thead><tr><th>Line</th><th className="vk-num">Claimed</th><th className="vk-num">Engine result</th><th className="vk-num">Difference</th><th className="vk-num">Tolerance</th><th>Result</th></tr></thead>
          <tbody>{findings.map((f) => (
            <tr key={f.findingId} className={statusTone(f.status) === "fail" ? "vk-row-fail" : undefined}>
              <td>{pretty(f.findingId)}{f.pointOfFailure ? <span className="vk-tag">point of failure</span> : null}</td>
              <td className="vk-num">{fmtNumber(f.numbers.observed)}</td><td className="vk-num">{fmtNumber(f.numbers.expected)}</td>
              <td className="vk-num">{fmtNumber(f.numbers.difference)}</td>
              <td className="vk-num">{f.numbers.tolerance == null ? "—" : `±${fmtNumber(f.numbers.tolerance)}`}</td>
              <td><StatusBadge status={f.status} /></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </section>
  );
}

export function SensitivityGrid({ s }: { s: Sensitivity | null }) {
  if (!s) return null;
  return (
    <section className="vk-card" data-testid="sensitivity">
      <h3>Sensitivity — verified at {s.variantsExecuted} grid point{s.variantsExecuted === 1 ? "" : "s"}</h3>
      <p className="vk-muted">
        Axes: {s.axes.length ? s.axes.map((a) => `${a.name} ∈ {${a.values.join(", ")}} (${a.origin})`).join("; ") : "none"}.
        Holding at these points is not a claim about all values. Each square is one grid point: green held, red did not.
      </p>
      {s.results.map((r) => (
        <div key={r.findingId} className="vk-sens-row">
          <code>{r.findingId}</code> {r.aggregate} · {r.passCount} pass / {r.failCount} fail
          <div className="vk-cells">{r.cells.map((c) => (
            <span key={c.variant} className={`vk-cell ${c.passed ? "vk-pass" : "vk-fail"}`}
              title={`${Object.entries(c.point).map(([k, v]) => `${k}=${v}`).join(", ") || "single point"} · margin ${c.margin}`} />
          ))}</div>
        </div>
      ))}
    </section>
  );
}

export function EvidenceTable({ items }: { items: EvidenceDTO[] }) {
  return (
    <section className="vk-card" data-testid="evidence">
      <h3>Evidence provenance (chain of custody)</h3>
      {items.length === 0 ? <p className="vk-muted">No external evidence: findings use only the frozen document values.</p> : (
        <div className="vk-scroll">
          <table className="vk-table">
            <thead><tr><th>Provider</th><th>Origin</th><th>Independence</th><th>Licence</th><th>Snapshot SHA-256</th><th>In bundle</th></tr></thead>
            <tbody>{items.map((e) => (
              <tr key={e.evidenceId}>
                <td>{e.providerId}</td><td>{e.origin}</td><td>{e.independenceBasis}</td><td>{e.licenseClass}</td>
                <td><code className="vk-hash">{e.snapshotHash}</code></td><td>{e.embeddedInBundle ? "yes" : "no (hash only)"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {items.map((e) => <p key={e.evidenceId} className="vk-muted">{e.providerId}: {e.rightsNote}</p>)}
    </section>
  );
}

/** A stroke painted behind the glyphs, in the card colour: the start label stays readable where the series line crosses it. */
const HALO = { stroke: "#ffffff", strokeWidth: 3.5, strokeLinejoin: "round", paintOrder: "stroke" } as const;
/** Draws an EQUITY_SERIES key record. Always illustrative: never a counterexample. */
export function EquityChart({ record }: { record: KeyRecord }) {
  const raw = (record.payload.equity as string[] | undefined) ?? [];
  const values = raw.map(Number).filter(Number.isFinite);
  if (values.length < 2) return null;
  const w = 720, h = 250, padL = 58, padR = 80, padT = 16, padB = 34;
  const min = Math.min(...values), max = Math.max(...values), span = max - min || 1;
  // Labels show at most two decimals by truncating the engine's decimal string (no float round trip).
  const short = (s: string) => s.replace(/^(-?\d+\.\d{2})\d*$/, "$1");
  const x = (i: number) => padL + (i * (w - padL - padR)) / (values.length - 1);
  const y = (v: number) => padT + (h - padT - padB) - ((v - min) * (h - padT - padB)) / span;
  const pts = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${x(0).toFixed(1)},${y(min).toFixed(1)} ${pts} ${x(values.length - 1).toFixed(1)},${y(min).toFixed(1)}`;
  const ticks = [min, min + span / 2, max];
  const last = values.length - 1;
  const point = Object.entries((record.payload.point as Record<string, string>) ?? {}).map(([k, v]) => `${k}=${v}`).join(", ");
  return (
    <figure className="vk-card vk-chart" data-testid="equity-chart">
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label={`Equity series from ${raw[0]} to ${raw[raw.length - 1]}`}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={padL} x2={w - padR} y1={y(t)} y2={y(t)} stroke="#d3dbd8" strokeWidth="1" />
            <text x={padL - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill="#52615f">{t.toFixed(0)}</text>
          </g>
        ))}
        <line x1={padL} x2={w - padR} y1={y(values[0])} y2={y(values[0])} stroke="#c9a35b" strokeWidth="1.5" strokeDasharray="5 4" />
        <text x={w - padR} y={y(values[0]) - 5} textAnchor="end" fontSize="11" fill="#7a5c1c" {...HALO}>start {short(raw[0])}</text>
        <polygon points={area} fill="currentColor" opacity=".12" />
        <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={x(last)} cy={y(values[last])} r="4.5" fill="currentColor" />
        {/* The end label sits in the right margin, level with the end point. The series stops at that point, so the line can never
            run through the label, and the label never meets the bar-number axis labels. */}
        <text x={x(last) + 9} y={y(values[last]) + 4} textAnchor="start" fontSize="11" fill="currentColor">end {short(raw[raw.length - 1])}</text>
        <text x={padL} y={h - 10} fontSize="11" fill="#52615f">bar 1</text>
        <text x={w - padR} y={h - 10} textAnchor="end" fontSize="11" fill="#52615f">bar {values.length}</text>
      </svg>
      <figcaption className="vk-muted">ILLUSTRATIVE equity (start 10000) at grid point {point || "—"}. {record.note} The line is the engine's series for one grid point and says nothing about any real market.</figcaption>
    </figure>
  );
}

export function KeyRecords({ records }: { records: KeyRecord[] }) {
  if (!records.length) return null;
  return (
    <section className="vk-card" data-testid="key-records">
      <h3>Key records</h3>
      <ul>{records.map((r) => (
        <li key={r.recordId}><b>{r.recordRole}</b> {r.recordKind} <code>{r.findingId}</code>: {r.note}
          <code className="vk-json">{JSON.stringify(r.payload)}</code></li>
      ))}</ul>
    </section>
  );
}

export function Diagnostics({ d }: { d: OutcomeResponse["diagnostics"] }) {
  if (!d) return null;
  return (
    <section className="vk-card vk-diagnostic" data-testid="diagnostics">
      <h3>Diagnostic — computed after reveal</h3>
      <p className="vk-muted">Does not affect any finding or the verdict hash.</p>
      {d.items.map((item, i) => <pre key={i} className="vk-json">{JSON.stringify(item, null, 2)}</pre>)}
    </section>
  );
}

/** The verdict as a toe tag: the result word, what kind of finding it is and what it means. */
export function VerdictHero({ outcome }: { outcome: OutcomeResponse }) {
  const status = outcome.headline.status;
  const tone = statusTone(status);
  const meaning = status ? STATUS_MEANING[status] : undefined;
  return (
    <div className={`vk-verdict-hero vk-${tone}`} data-testid="headline">
      <div className="vk-verdict-word">{meaning ? <span aria-hidden="true">{meaning.glyph} </span> : null}{status ?? "NO VERDICT"}</div>
      <div>
        {meaning ? <><span className="vk-kicker">{meaning.kind}</span><p>{meaning.plain}</p></>
          : <p>{outcome.executionStatus === "BLOCKED"
            ? "The examination could not proceed, so no verdict is given. Nothing was guessed; the blockers below say what is missing."
            : "No verdict was produced."}</p>}
      </div>
      <div className="vk-verdict-meta">
        <span>execution {outcome.executionStatus}</span>
        <span>confidence {outcome.headline.confidenceClass ?? "none"}</span>
        <span>isolation {outcome.isolationMode}</span>
        {outcome.demonstrationOnly ? <span>demonstration only</span> : null}
      </div>
    </div>
  );
}

export function VerdictView({ outcome, children }: { outcome: OutcomeResponse; children?: ReactNode }) {
  return (
    <section className="vk-verdict vk-results-anchor" data-testid="verdict">
      <DemoNotice notice={outcome.demonstrationNotice} />
      <header className="vk-card vk-specimen">
        <div className="vk-muted">{outcome.specimen.specimenId} · {outcome.specimen.claimTypeLabel}
          {outcome.specimen.fixtureId ? <> · fixture <code>{outcome.specimen.fixtureId}</code></> : null}</div>
        <h2>{outcome.specimen.title}</h2>
        {outcome.verdictHash ? <div className="vk-muted">verdict hash <code className="vk-hash">{outcome.verdictHash}</code></div> : null}
      </header>
      <VerdictHero outcome={outcome} />
      <WhyThisVerdict outcome={outcome} />
      <Blockers blockers={outcome.blockers} />
      <FindingsTable findings={outcome.findings} />
      {outcome.findings.map((f) => <FindingCard key={f.findingId} f={f} />)}
      <SensitivityGrid s={outcome.sensitivity} />
      <EvidenceTable items={outcome.evidence} />
      {outcome.keyRecords.filter((r) => r.recordKind === "EQUITY_SERIES" && r.recordRole === "ILLUSTRATIVE")
        .map((r) => <EquityChart key={r.recordId} record={r} />)}
      <KeyRecords records={outcome.keyRecords.filter((r) => r.recordKind !== "EQUITY_SERIES")} />
      <Diagnostics d={outcome.diagnostics} />
      <section className="vk-card"><h3>Parameter ledger (frozen)</h3><ParameterLedger entries={outcome.parameterLedger} /></section>
      {children}
      <DemoNotice notice={outcome.demonstrationNotice} />
    </section>
  );
}

/** One sample case a visitor can run with a single click. The result still comes from the engine. */
export function SampleCard({ id, title, blurb, designed, selected, busy, onRun, onLoad, runAttr, loadAttr }: {
  id: string; title: string; blurb: string; designed?: string; selected?: boolean; busy?: boolean;
  onRun: () => void; onLoad?: () => void; runAttr?: Record<string, string>; loadAttr?: Record<string, string>;
}) {
  return (
    <div className={`vk-sample${selected ? " vk-selected" : ""}`} data-sample={id}>
      <h4>{title}</h4>
      <p className="vk-muted">{blurb}</p>
      {designed ? <p className="vk-muted">Built to show: <b>{designed}</b> (the engine decides the actual result)</p> : null}
      <div className="vk-actions">
        <button type="button" className="vk-primary" disabled={busy} onClick={onRun} {...runAttr}>Examine this sample</button>
        {onLoad ? <button type="button" className="vk-secondary" disabled={busy} onClick={onLoad} {...loadAttr}>Load into form</button> : null}
      </div>
    </div>
  );
}

export function BundlePanel({ client, caseId }: { client: Client; caseId: string }) {
  const [meta, setMeta] = useState<BundleMetadata | null>(null);
  const [replay, setReplay] = useState<ReplayReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    client.bundleMetadata(caseId).then(setMeta, (e) => setErr(describeError(e)));
  }, [client, caseId]);
  const replayServer = useCallback(async () => {
    setErr(null);
    setBusy(true);
    try {
      setReplay(await client.replay(await client.bundleBytes(caseId)));
    } catch (e) {
      setErr(describeError(e));
    } finally {
      setBusy(false);
    }
  }, [client, caseId]);
  const isolation: IsolationMode | null = meta?.isolationMode ?? null;
  return (
    <section className="vk-card" data-testid="bundle">
      <h3>The coroner's report: evidence bundle</h3>
      <p className="vk-muted">One file holds the frozen claim, the ledger, the evidence snapshots and the sealed verdict. It can be verified and replayed offline.</p>
      <div className="vk-actions">
        <a className="vk-button vk-primary" href={client.bundleUrl(caseId)} download={`${caseId}.vkb`}>Download .vkb</a>{" "}
        <button className="vk-button vk-secondary" type="button" onClick={replayServer} disabled={busy}>Replay on server (no network)</button>{" "}
        <a className="vk-button vk-secondary" href={`/verify?caseId=${encodeURIComponent(caseId)}`}>Open in Verify Lab</a>
      </div>
      {busy ? <p className="vk-muted"><Spinner label="Re-executing the examination from the bundle…" /></p> : null}
      {meta ? <>
        <p className="vk-muted">sha256 <code className="vk-hash">{meta.bundleSha256}</code> · {meta.sizeBytes} bytes · offline: <code>{meta.replayCommand}</code></p>
        <VerificationReport heading="As written" testId="bundle-metadata" report={meta} isolationMode={isolation} />
      </> : (err ? null : <p className="vk-muted"><Spinner label="Reading bundle metadata…" /></p>)}
      {replay ? <VerificationReport heading="Replay" testId="replay-report" report={replay} isolationMode={isolation} /> : null}
      {err ? <p className="vk-error">{err}</p> : null}
      <p className="vk-muted">Integrity and reproducibility are not proof of origin. Origin is established only by a valid signature from a signer the operator trusts, and never shows that the claim is true.</p>
    </section>
  );
}

export function ReplayUpload({ client, isolationMode = null }: { client: Client; isolationMode?: IsolationMode | null }) {
  const [report, setReport] = useState<ReplayReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <section className="vk-card" data-testid="replay-upload">
      <h3>Replay a bundle</h3>
      <p className="vk-muted">Re-executes a .vkb on the server with no network access, and checks its signature against the server's trust store.</p>
      <input type="file" accept=".vkb,application/zip" aria-label="Bundle file" onChange={async (ev) => {
        const file = ev.target.files?.[0];
        if (!file) return;
        setErr(null);
        setReport(null);
        setBusy(true);
        try {
          setReport(await client.replay(file));
        } catch (e) {
          setErr(describeError(e));
        } finally {
          setBusy(false);
        }
      }} />
      {busy ? <p className="vk-muted"><Spinner label="Replaying…" /></p> : null}
      {report ? <>
        <VerificationReport heading="Replay" testId="replay-report" report={report} isolationMode={isolationMode} />
        {report.notes.length ? <ul>{report.notes.map((n, i) => <li key={i} className="vk-muted">{n}</li>)}</ul> : null}
      </> : null}
      {err ? <p className="vk-error">{err}</p> : null}
    </section>
  );
}

export interface WorkflowState {
  phase: Phase;
  draft: DraftCase | null;
  events: ProgressEvent[];
  outcome: OutcomeResponse | null;
  caseId: string | null;
  error: string | null;
}
const IDLE: WorkflowState = { phase: "idle", draft: null, events: [], outcome: null, caseId: null, error: null };

/**
 * Drives intake -> freeze -> evidence -> run -> outcome. ``onAccepted`` is called once
 * the server has the claim, so the page can clear claimed values from its own state
 * (API contract §0). A blocked stage loads the server's BLOCKED outcome.
 */
export function useCaseWorkflow(client: Client) {
  const [state, setState] = useState<WorkflowState>(IDLE);
  const reset = useCallback(() => setState(IDLE), []);
  const submit = useCallback(async (intake: IntakeRequest, onAccepted?: () => void) => {
    setState({ ...IDLE, phase: "intake" });
    let caseId: string | null = null;
    try {
      const draft = await client.createCase(intake);
      caseId = draft.caseId;
      onAccepted?.();
      if (draft.blockers.length) {
        setState((s) => ({ ...s, phase: "draft-blocked", draft, caseId }));
        return;
      }
      setState((s) => ({ ...s, phase: "freezing", draft, caseId }));
      await client.freeze(draft.caseId);
      setState((s) => ({ ...s, phase: "evidence" }));
      await client.acquireEvidence(draft.caseId);
      setState((s) => ({ ...s, phase: "running" }));
      const accepted = await client.startRun(draft.caseId);
      const record = await followRun(client, accepted, (e) =>
        setState((s) => ({ ...s, events: s.events.some((x) => x.seq === e.seq) ? s.events : [...s.events, e] })));
      const outcome = await client.outcome(draft.caseId);
      setState((s) => ({ ...s, phase: "done", events: record.events, outcome }));
    } catch (e) {
      if (e instanceof BlockedError && caseId) {
        try {
          const outcome = await client.outcome(caseId);
          setState((s) => ({ ...s, phase: "done", outcome }));
          return;
        } catch (inner) {
          setState((s) => ({ ...s, phase: "error", error: describeError(inner) }));
          return;
        }
      }
      setState((s) => ({ ...s, phase: "error", error: describeError(e) }));
    }
  }, [client]);
  return { state, submit, reset };
}
