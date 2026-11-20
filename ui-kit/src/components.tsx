/**
 * Presentation components. Every value shown comes from an API response; nothing is
 * computed or defaulted into a verdict here. Wording follows docs/API_CONTRACT.md:
 * "verified at N grid points", integrity / reproducibility / authenticity kept separate,
 * and the demonstration notice rendered on every synthetic view.
 */
import { useCallback, useEffect, useState } from "react";
import type { Client } from "./api";
import { ApiError, BlockedError, ContractMismatchError, followRun } from "./api";
import type {
  BundleMetadata, DraftCase, EvidenceDTO, FindingDTO, Health, IntakeRequest, KeyRecord,
  OutcomeResponse, ParameterEntry, ProgressEvent, ReplayReport, Sensitivity, Blocker,
} from "./types";

const PASSING = new Set(["CONSISTENT", "SUPPORTED", "WITHIN_BOUND"]);

export function statusTone(status: string | null): "pass" | "fail" | "warn" | "none" {
  if (status === null) return "none";
  if (PASSING.has(status)) return "pass";
  if (status === "CONDITIONAL" || status === "INDETERMINATE") return "warn";
  return "fail";
}

export function StatusBadge({ status }: { status: string | null }) {
  return <span className={`vk-badge vk-${statusTone(status)}`}>{status ?? "NO VERDICT"}</span>;
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
      <h3>Blocked</h3>
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
    <table className="vk-table" data-testid="ledger">
      <thead><tr><th>Parameter</th><th>Value</th><th>State</th><th>Basis</th></tr></thead>
      <tbody>{entries.map((e) => (
        <tr key={e.name} className={e.state === "MISSING" && e.critical ? "vk-row-fail" : undefined}>
          <td><code>{e.name}</code></td>
          <td>{e.value ?? (e.range ? `swept ${fmtRange(e)}` : "—")}</td>
          <td>{e.state}</td><td>{e.basis}</td>
        </tr>
      ))}</tbody>
    </table>
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
    <ol className="vk-progress" data-testid="progress">
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

function Numbers({ f }: { f: FindingDTO }) {
  const n = f.numbers;
  if (n.expected == null && n.observed == null) return null;
  return (
    <dl className="vk-numbers">
      <dt>Computed</dt><dd>{n.expected ?? "—"}</dd>
      <dt>Claimed</dt><dd>{n.observed ?? "—"}</dd>
      <dt>Difference</dt><dd>{n.difference ?? "—"}</dd>
      <dt>Tolerance</dt><dd>±{n.tolerance ?? "—"}</dd>
    </dl>
  );
}

export function FindingCard({ f }: { f: FindingDTO }) {
  return (
    <article className={`vk-card vk-finding vk-${statusTone(f.status)}`} data-testid={`finding-${f.findingId}`}>
      <header>
        <StatusBadge status={f.status} /> <code>{f.findingId}</code>
        {f.pointOfFailure ? <span className="vk-tag">point of failure</span> : null}
        {f.propagated ? <span className="vk-tag">propagated</span> : null}
      </header>
      <p>{f.statement}</p>
      {f.reason ? <p className="vk-muted">Reason: <code>{f.reason}</code></p> : null}
      <Numbers f={f} />
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

export function SensitivityGrid({ s }: { s: Sensitivity | null }) {
  if (!s) return null;
  return (
    <section className="vk-card" data-testid="sensitivity">
      <h3>Sensitivity — verified at {s.variantsExecuted} grid point{s.variantsExecuted === 1 ? "" : "s"}</h3>
      <p className="vk-muted">
        Axes: {s.axes.length ? s.axes.map((a) => `${a.name} ∈ {${a.values.join(", ")}} (${a.origin})`).join("; ") : "none"}.
        Holding at these points is not a claim about all values.
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
      <h3>Evidence provenance</h3>
      {items.length === 0 ? <p className="vk-muted">No external evidence: findings use only the frozen document values.</p> : (
        <table className="vk-table">
          <thead><tr><th>Provider</th><th>Origin</th><th>Independence</th><th>Licence</th><th>Snapshot SHA-256</th><th>In bundle</th></tr></thead>
          <tbody>{items.map((e) => (
            <tr key={e.evidenceId}>
              <td>{e.providerId}</td><td>{e.origin}</td><td>{e.independenceBasis}</td><td>{e.licenseClass}</td>
              <td><code className="vk-hash">{e.snapshotHash}</code></td><td>{e.embeddedInBundle ? "yes" : "no (hash only)"}</td>
            </tr>
          ))}</tbody>
        </table>
      )}
      {items.map((e) => <p key={e.evidenceId} className="vk-muted">{e.providerId}: {e.rightsNote}</p>)}
    </section>
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

export function VerdictView({ outcome, children }: { outcome: OutcomeResponse; children?: React.ReactNode }) {
  return (
    <section className="vk-verdict" data-testid="verdict">
      <DemoNotice notice={outcome.demonstrationNotice} />
      <header className="vk-card vk-specimen">
        <div className="vk-muted">{outcome.specimen.specimenId} · {outcome.specimen.claimTypeLabel}
          {outcome.specimen.fixtureId ? <> · fixture <code>{outcome.specimen.fixtureId}</code></> : null}</div>
        <h2>{outcome.specimen.title}</h2>
        <div className="vk-toe-tag" data-testid="headline">
          <StatusBadge status={outcome.headline.status} />
          <span> execution {outcome.executionStatus}</span>
          <span className="vk-muted"> · confidence {outcome.headline.confidenceClass ?? "none"}</span>
          <span className="vk-muted"> · isolation {outcome.isolationMode}</span>
        </div>
        {outcome.verdictHash ? <div className="vk-muted">verdict hash <code className="vk-hash">{outcome.verdictHash}</code></div> : null}
      </header>
      <Blockers blockers={outcome.blockers} />
      {outcome.findings.map((f) => <FindingCard key={f.findingId} f={f} />)}
      <SensitivityGrid s={outcome.sensitivity} />
      <EvidenceTable items={outcome.evidence} />
      <KeyRecords records={outcome.keyRecords} />
      <Diagnostics d={outcome.diagnostics} />
      <section className="vk-card"><h3>Parameter ledger (frozen)</h3><ParameterLedger entries={outcome.parameterLedger} /></section>
      {children}
      <DemoNotice notice={outcome.demonstrationNotice} />
    </section>
  );
}

function ReportView({ title, integrity, repro, authenticity }: {
  title: string; integrity: ReplayReport["integrity"]; repro: ReplayReport["reproducibility"];
  authenticity: ReplayReport["authenticity"];
}) {
  return (
    <div data-testid={title === "Replay" ? "replay-report" : "bundle-metadata"}>
      <h4>{title}</h4>
      <p>Integrity: <StatusBadge status={integrity.status === "VERIFIED" ? "CONSISTENT" : "CONTRADICTED"} /> {integrity.status}
        {" "}({integrity.checks.map((c) => `${c.check} ${c.ok ? "ok" : "FAILED"}`).join(", ")})</p>
      <p>Reproducibility: <b data-testid="repro-status">{repro.status}</b>
        {repro.replayedVerdictHash ? <> · replayed hash <code className="vk-hash">{repro.replayedVerdictHash}</code></> : null}</p>
      <p>Authenticity: <b>{authenticity.status}</b> — {authenticity.note}</p>
    </div>
  );
}

export function BundlePanel({ client, caseId }: { client: Client; caseId: string }) {
  const [meta, setMeta] = useState<BundleMetadata | null>(null);
  const [replay, setReplay] = useState<ReplayReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    client.bundleMetadata(caseId).then(setMeta, (e) => setErr(describeError(e)));
  }, [client, caseId]);
  const replayServer = useCallback(async () => {
    setErr(null);
    try {
      setReplay(await client.replay(await client.bundleBytes(caseId)));
    } catch (e) {
      setErr(describeError(e));
    }
  }, [client, caseId]);
  return (
    <section className="vk-card" data-testid="bundle">
      <h3>Bundle</h3>
      <a className="vk-button" href={client.bundleUrl(caseId)} download={`${caseId}.vkb`}>Download .vkb</a>{" "}
      <button className="vk-button" type="button" onClick={replayServer}>Replay on server (no network)</button>
      {meta ? <>
        <p className="vk-muted">sha256 <code className="vk-hash">{meta.bundleSha256}</code> · {meta.sizeBytes} bytes · offline: <code>{meta.replayCommand}</code></p>
        <ReportView title="As written" integrity={meta.integrity} repro={meta.reproducibility} authenticity={meta.authenticity} />
      </> : null}
      {replay ? <ReportView title="Replay" integrity={replay.integrity} repro={replay.reproducibility} authenticity={replay.authenticity} /> : null}
      {err ? <p className="vk-error">{err}</p> : null}
      <p className="vk-muted">Integrity and reproducibility are not proof of origin; bundles are unsigned in v1.</p>
    </section>
  );
}

export function ReplayUpload({ client }: { client: Client }) {
  const [report, setReport] = useState<ReplayReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  return (
    <section className="vk-card" data-testid="replay-upload">
      <h3>Replay a bundle</h3>
      <p className="vk-muted">Re-executes a .vkb on the server with no network access.</p>
      <input type="file" accept=".vkb,application/zip" aria-label="Bundle file" onChange={async (ev) => {
        const file = ev.target.files?.[0];
        if (!file) return;
        setErr(null);
        setReport(null);
        try {
          setReport(await client.replay(file));
        } catch (e) {
          setErr(describeError(e));
        }
      }} />
      {report ? <>
        <ReportView title="Replay" integrity={report.integrity} repro={report.reproducibility} authenticity={report.authenticity} />
        {report.notes.length ? <ul>{report.notes.map((n, i) => <li key={i} className="vk-muted">{n}</li>)}</ul> : null}
      </> : null}
      {err ? <p className="vk-error">{err}</p> : null}
    </section>
  );
}

export function describeError(e: unknown): string {
  if (e instanceof BlockedError) return `Blocked: ${e.message}`;
  if (e instanceof ApiError) return `${e.code}: ${e.message}${e.field ? ` (${e.field})` : ""}`;
  if (e instanceof ContractMismatchError) return e.message;
  return "Unexpected error; no result is shown.";
}

export type Phase = "idle" | "intake" | "draft-blocked" | "freezing" | "evidence" | "running" | "done" | "error";

export interface WorkflowState {
  phase: Phase;
  draft: DraftCase | null;
  events: ProgressEvent[];
  outcome: OutcomeResponse | null;
  caseId: string | null;
  error: string | null;
}

/**
 * Drives intake -> freeze -> evidence -> run -> outcome. ``onAccepted`` is called once
 * the server has the claim, so the page can clear claimed values from its own state
 * (API contract §0). A blocked stage loads the server's BLOCKED outcome.
 */
export function useCaseWorkflow(client: Client) {
  const [state, setState] = useState<WorkflowState>({
    phase: "idle", draft: null, events: [], outcome: null, caseId: null, error: null,
  });

  const submit = useCallback(async (intake: IntakeRequest, onAccepted?: () => void) => {
    setState({ phase: "intake", draft: null, events: [], outcome: null, caseId: null, error: null });
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

  return { state, submit };
}
