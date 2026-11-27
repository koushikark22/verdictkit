import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  EmptyState, ErrorCard, PhaseTracker, RunProgress, SampleCard, Spinner, StatusBadge, VerificationReport,
  describeError, useCaseWorkflow,
  type BundleMetadata, type Client, type DemoScenarioId, type DemoStatus, type DemoVerifyReport, type Health, type ReplayReport,
} from "@verdictkit/ui-kit";
import { explainReport } from "./explain";
import { LAB_SAMPLES, SCENARIO_ORDER } from "./samples";

type Result = { report: DemoVerifyReport } | { error: string };

const isScenario = (v: string | null): v is DemoScenarioId => !!v && (SCENARIO_ORDER as string[]).includes(v);

const COLUMNS: { key: string; label: string; pick: (r: DemoVerifyReport) => string }[] = [
  { key: "integrity", label: "Integrity", pick: (r) => r.integrity.status },
  { key: "signature", label: "Signature", pick: (r) => r.authenticity.signatureValidity },
  { key: "trust", label: "Signer trust", pick: (r) => r.authenticity.signerTrust },
  { key: "authenticity", label: "Authenticity", pick: (r) => r.authenticity.status },
  { key: "repro", label: "Reproducibility", pick: (r) => r.reproducibility.status },
  { key: "isolation", label: "Isolation", pick: (r) => r.demo.isolationMode },
];

export function VerifyLab({ client, health, lab, labError, image }: {
  client: Client; health: Health | null; lab: DemoStatus | null; labError: string | null; image: string;
}) {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const auto = params.get("auto") === "1";
  const [scenario, setScenario] = useState<DemoScenarioId>(isScenario(params.get("scenario")) ? (params.get("scenario") as DemoScenarioId) : "trusted-signer");
  const { state, submit } = useCaseWorkflow(client);
  const [caseId, setCaseId] = useState<string | null>(params.get("caseId"));
  const [bundle, setBundle] = useState<Blob | null>(null);
  const [meta, setMeta] = useState<BundleMetadata | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [results, setResults] = useState<Partial<Record<DemoScenarioId, Result>>>({});
  const [running, setRunning] = useState<DemoScenarioId | null>(null);
  const [upload, setUpload] = useState<{ name?: string; report?: ReplayReport; error?: string; busy: boolean }>({ busy: false });
  const [picked, setPicked] = useState<string | null>(null);
  const started = useRef(false);
  const verified = useRef(false);
  const busyExam = ["intake", "freezing", "evidence", "running"].includes(state.phase);
  const labReady = !!lab && lab.enabled;
  // Unknown is not the same as disabled: only a definite answer (an error such as NOT_FOUND, or enabled=false) says the lab is off.
  const labPending = lab === null && labError === null;

  // 1. A finished examination that wrote a bundle becomes the bundle under test.
  useEffect(() => {
    if (state.phase === "done" && state.caseId && state.outcome?.bundleAvailable) setCaseId(state.caseId);
  }, [state.phase, state.caseId, state.outcome]);

  // 2. Fetch the bundle's metadata and bytes from the server for that case.
  useEffect(() => {
    if (!caseId) return undefined;
    let cancelled = false;
    setBundle(null); setMeta(null); setResults({}); setLoadErr(null);
    Promise.all([client.bundleMetadata(caseId), client.bundleBytes(caseId)]).then(
      ([m, b]) => { if (!cancelled) { setMeta(m); setBundle(b); } },
      (e) => { if (!cancelled) setLoadErr(describeError(e)); });
    return () => { cancelled = true; };
  }, [client, caseId]);

  const verifyOne = useCallback(async (id: DemoScenarioId) => {
    if (!bundle) return;
    setRunning(id);
    try {
      const report = await client.demoVerify(id, bundle);
      setResults((r) => ({ ...r, [id]: { report } }));
    } catch (e) {
      setResults((r) => ({ ...r, [id]: { error: describeError(e) } }));
    } finally {
      setRunning(null);
    }
  }, [client, bundle]);

  const verifyAll = useCallback(async () => {
    for (const id of SCENARIO_ORDER) await verifyOne(id);
  }, [verifyOne]);

  // When a verification finishes, bring its result into view so the click never seems to do nothing.
  const wasRunning = useRef<DemoScenarioId | null>(null);
  useEffect(() => {
    const finished = wasRunning.current !== null && running === null;
    wasRunning.current = running;
    if (finished) document.querySelector("[data-testid=lab-result]")?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }, [running]);

  const runSample = useCallback((id: string) => {
    const sample = LAB_SAMPLES.find((s) => s.id === id);
    if (!sample) return;
    setPicked(id);
    setCaseId(null); setBundle(null); setMeta(null); setResults({});
    void submit(sample.intake);
  }, [submit]);

  // Guided demo link: /verify?auto=1&sample=...&scenario=... runs the sample, then verifies that scenario once.
  useEffect(() => {
    if (!auto || started.current || !health || caseId) return;
    started.current = true;
    runSample(params.get("sample") ?? LAB_SAMPLES[0].id);
  }, [auto, health, caseId, params, runSample]);
  useEffect(() => {
    if (!auto || verified.current || !bundle || !labReady) return;
    verified.current = true;
    void verifyOne(scenario);
  }, [auto, bundle, labReady, scenario, verifyOne]);

  const current = results[scenario];
  const selected = lab?.scenarios.find((s) => s.id === scenario);
  const profile = lab?.verifierProfiles.find((p) => p.id === selected?.profile);
  const signer = meta?.authenticity.signer ?? null;
  const fileName = caseId ? `${caseId}.vkb` : "bundle.vkb";

  return (
    <main id="main">
      <p className="vk-kicker">Application 3 · evidence bundle verification</p>
      <h1>Verify a signed evidence bundle</h1>
      <p className="vk-muted">Run a sample examination, receive a digitally signed bundle, download it, then check it the way an independent verifier
        would: against a trust store the <i>verifier</i> configured, never against a key found inside the bundle. Six results are reported
        separately because they answer six different questions.</p>

      {labReady ? (
        <div className="vk-banner vk-demo" role="note" data-testid="lab-notice">{lab!.demonstrationNotice}</div>
      ) : labPending ? (
        // Nothing has said the lab is off: /demo/status has not answered (still loading, or the backend is unreachable).
        <div className="vk-banner vk-info" role="status" data-testid="lab-pending">
          {health ? "Checking whether the demonstration lab is enabled…"
            : "Waiting for the backend. The demonstration lab status is shown once it answers; the status pill above says whether it is reachable."}
        </div>
      ) : (
        <div className="vk-banner vk-warn" data-testid="lab-disabled">
          {labError ?? "The demonstration lab is not enabled on this server."} Scenario verification needs the backend started by the VerdictKit
          start script, which provisions the disposable demonstration signer. You can still run samples and verify files below.
        </div>
      )}

      <section className="vk-card" aria-labelledby="s1" data-testid="step-sample">
        <h2 id="s1">1 · Run a sample examination</h2>
        <p className="vk-muted">Each sample runs the real engine through the full pipeline: freeze, seal, blind examination, reveal, bundle. The server signs the finished bundle with its demonstration key.</p>
        <div className="vk-samples">
          {LAB_SAMPLES.map((s) => (
            <SampleCard key={s.id} id={s.id} title={s.title} blurb={s.blurb} designed={s.designed} busy={busyExam}
              selected={picked === s.id} onRun={() => runSample(s.id)} runAttr={{ "data-lab-sample": s.id }} />
          ))}
        </div>
        <PhaseTracker phase={state.phase} />
        {busyExam ? <p className="vk-muted"><Spinner label="Examining…" /></p> : null}
        {state.error ? <ErrorCard message={state.error} /> : null}
        <RunProgress events={state.events} />
        {state.outcome ? (
          <p data-testid="sample-verdict">Verdict: <StatusBadge status={state.outcome.headline.status} /> <span className="vk-muted">({state.outcome.specimen.title.trim()} · case <code>{state.caseId}</code>)</span>
            {state.outcome.demonstrationNotice ? <span className="vk-muted"> · {state.outcome.demonstrationNotice}</span> : null}</p>
        ) : null}
        {state.outcome && !state.outcome.bundleAvailable ? <p className="vk-error">This examination produced no bundle, so there is nothing to verify.</p> : null}
        {state.phase === "idle" && !caseId ? <EmptyState title="No bundle yet">Pick a sample to produce a real signed bundle.</EmptyState> : null}
      </section>

      <section className="vk-card" aria-labelledby="s2" data-testid="step-bundle">
        <h2 id="s2">2 · The signed bundle</h2>
        {loadErr ? <ErrorCard message={loadErr} /> : null}
        {caseId && !meta && !loadErr ? <p className="vk-muted"><Spinner label="Reading the bundle…" /></p> : null}
        {!caseId ? <p className="vk-muted">Waiting for a sample examination.</p> : null}
        {meta ? <>
          <p data-testid="bundle-card">File <code>{fileName}</code> · {meta.sizeBytes} bytes · sha256 <code className="vk-hash" data-testid="bundle-sha">{meta.bundleSha256}</code></p>
          <p className="vk-muted" data-testid="bundle-signer">{signer
            ? <>Signed by the demonstration key <code className="vk-hash">{signer.keyId}</code> ({signer.algorithm}). The server's own trust store{" "}
              {meta.authenticity.signerTrust === "TRUSTED" ? "accepts" : "does not accept"} that key.</>
            : "This bundle carries no signature."}</p>
          <div className="vk-actions">
            <a className="vk-button vk-primary" href={client.bundleUrl(caseId!)} download={fileName} data-testid="download-bundle">Download bundle (.vkb)</a>{" "}
            {labReady ? <a className="vk-button vk-secondary" href={client.demoTrustStoreUrl()} download="vk-demo-trust-store.json" data-testid="download-trust-store">Download the public trust store</a> : null}
          </div>
          <details className="vk-help">
            <summary>Verify it offline, with no network (Docker)</summary>
            <p>Save both files in one folder, open a terminal there and run:</p>
            <pre className="vk-json" data-testid="offline-command">{`docker run --rm --network none -v "$(pwd):/data:ro" ${image} verdictkit replay /data/${fileName} --trust-store /data/vk-demo-trust-store.json`}</pre>
            <p className="vk-muted">The container has no network. It re-executes the examination from the bundle and reports integrity, signature, signer trust, authenticity and reproducibility.</p>
          </details>
        </> : null}
      </section>

      <section className="vk-card" aria-labelledby="s3" data-testid="step-verify">
        <h2 id="s3">3 · Verify with an independently configured trust store</h2>
        <p className="vk-muted">Pick a scenario. The browser sends the bundle and the scenario's <i>name</i>. The server applies a verifier configuration it holds
          itself and runs its real verification and replay code. You never supply a key, and the bundle cannot add one.</p>
        <div className="vk-scenarios" role="group" aria-label="Verification scenarios">
          {(lab?.scenarios ?? []).map((s) => (
            <button key={s.id} type="button" className="vk-scenario" aria-pressed={scenario === s.id} data-scenario={s.id} onClick={() => setScenario(s.id)}>
              <b>{s.label}</b><span>{s.setup}</span>
            </button>
          ))}
        </div>
        {!labReady ? <p className="vk-muted" data-testid="no-scenarios">{labPending
          ? "Scenarios appear once the backend reports the demonstration lab."
          : "No scenarios are available because the lab is not enabled."}</p> : null}
        {profile ? <p className="vk-muted" data-testid="profile-note"><b>Verifier configuration:</b> {profile.label}. {profile.description}
          {" "}Trust store serial {profile.trustStore.serial}, sha256 <code>{profile.trustStore.sha256.slice(0, 16)}…</code></p> : null}
        <div className="vk-actions">
          <button type="button" className="vk-primary" disabled={!bundle || !labReady || running !== null} onClick={() => void verifyOne(scenario)} data-testid="verify-button">
            Verify and replay: {selected?.label ?? "scenario"}
          </button>{" "}
          <button type="button" className="vk-secondary" disabled={!bundle || !labReady || running !== null} onClick={() => void verifyAll()} data-testid="verify-all-button">
            Run all five scenarios
          </button>
        </div>
        {running ? <p className="vk-muted"><Spinner label={`Verifying (${running}) and re-executing the examination…`} /></p> : null}
        {current && "error" in current ? <ErrorCard message={current.error} testId="lab-error" /> : null}
        {current && "report" in current ? (
          <div data-testid="lab-result">
            <VerificationReport heading={current.report.demo.scenario.label} testId="lab-report" report={current.report} isolationMode={current.report.demo.isolationMode} />
            <p className="vk-banner vk-info" data-testid="lab-explanation">{explainReport(current.report)}</p>
            <p className="vk-muted" data-testid="lab-tested">Tested bytes: {current.report.demo.tested.description} sha256 <code className="vk-hash">{current.report.demo.tested.sha256}</code> ({current.report.demo.tested.sizeBytes} bytes).</p>
            {current.report.notes.length ? <ul>{current.report.notes.map((n, i) => <li key={i} className="vk-muted">{n}</li>)}</ul> : null}
          </div>
        ) : null}
        {!current && !running && bundle && labReady ? <p className="vk-muted">Choose “Verify and replay” to run this scenario against the real backend.</p> : null}

        {Object.keys(results).length ? (
          <div data-testid="matrix-wrap">
            <h3>Side by side</h3>
            <div className="vk-scroll">
              <table className="vk-table vk-matrix" data-testid="matrix">
                <thead><tr><th>Scenario</th>{COLUMNS.map((c) => <th key={c.key}>{c.label}</th>)}</tr></thead>
                <tbody>{SCENARIO_ORDER.map((id) => {
                  const r = results[id];
                  const label = lab?.scenarios.find((s) => s.id === id)?.label ?? id;
                  return (
                    <tr key={id} data-testid={`matrix-row-${id}`}>
                      <th scope="row">{label}</th>
                      {COLUMNS.map((c) => (
                        <td key={c.key} data-col={c.key}>{!r ? <span className="vk-pending">not run</span> : "error" in r ? "error" : c.pick(r.report)}</td>
                      ))}
                    </tr>
                  );
                })}</tbody>
              </table>
            </div>
          </div>
        ) : null}
      </section>

      <section className="vk-card" aria-labelledby="s4" data-testid="step-upload">
        <h2 id="s4">4 · Verify a file you already have</h2>
        <p className="vk-muted">Upload any .vkb, including one you edited by hand. The server checks its signature against its own trust store and replays it with no network access.
          Try downloading the bundle above, changing one byte inside it with a zip tool, and uploading it here.</p>
        <input type="file" accept=".vkb,application/zip" aria-label="Bundle file to verify" data-testid="upload-input" onChange={async (ev) => {
          const file = ev.target.files?.[0];
          if (!file) return;
          setUpload({ name: file.name, busy: true });
          try {
            setUpload({ name: file.name, busy: false, report: await client.replay(file) });
          } catch (e) {
            setUpload({ name: file.name, busy: false, error: describeError(e) });
          }
        }} />
        {upload.busy ? <p className="vk-muted"><Spinner label={`Replaying ${upload.name}…`} /></p> : null}
        {upload.error ? <ErrorCard message={upload.error} testId="upload-error" /> : null}
        {upload.report ? <>
          <VerificationReport heading={`Result for ${upload.name}`} testId="upload-report" report={upload.report} isolationMode={health?.isolationMode ?? null} />
          <p className="vk-banner vk-info">{explainReport(upload.report)}</p>
        </> : null}
      </section>
    </main>
  );
}
