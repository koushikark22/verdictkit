import type { ReactNode } from "react";
import type { DemoStatus, Health } from "@verdictkit/ui-kit";
import { QUOTE_DEMOS, REEL_DEMOS, VERIFY_DEMOS, type Demo } from "./samples";

export interface PortalConfig { image: string }

function Tile({ label, tone, value, children, testId }: { label: string; tone: "pass" | "warn" | "fail" | "info"; value: string; children?: ReactNode; testId: string }) {
  return (
    <div className={`vk-prop vk-${tone}`}>
      <h5>{label}</h5>
      <div className="vk-value"><b data-testid={testId}>{value}</b></div>
      {children}
    </div>
  );
}

/** The instrument panel. Every figure is what the API returned; when it returned nothing, it says so. */
export function SystemStatus({ health, healthError, loading, lab, labError, checkedAt, onRetry }: {
  health: Health | null; healthError: string | null; loading: boolean;
  lab: DemoStatus | null; labError: string | null; checkedAt: string | null; onRetry: () => void;
}) {
  if (loading) {
    return <div className="vk-props" aria-busy="true" data-testid="system-status">{[0, 1, 2, 3].map((i) => <div key={i} className="vk-prop"><div className="vk-skeleton" style={{ height: 64 }} /></div>)}</div>;
  }
  if (!health) {
    const limited = healthError?.startsWith("RATE_LIMITED") ?? false;
    return (
      <div className="vk-errorcard" role="alert" data-testid="system-status">
        <b>{limited ? "The backend is busy" : "Backend not reachable"}</b>
        <p>{limited
          ? "The backend answered but is rate limiting this browser for a moment. Nothing is shown rather than a guess; retry in a few seconds."
          : <>The portal could not read /api/v1/health, so no status is shown and no examination can run. Start everything with
            <code> scripts\Start-VerdictKit.ps1</code> (Windows) or <code>scripts/start-verdictkit.sh</code> (Linux).</>}</p>
        <pre data-testid="health-error">{healthError}</pre>
        <button type="button" className="vk-secondary vk-small" onClick={onRetry}>Retry</button>
      </div>
    );
  }
  const enforced = health.isolationMode === "ENFORCED";
  return (
    <>
      <div className="vk-props" data-testid="system-status">
        <Tile label="Backend" tone="pass" value="CONNECTED" testId="status-backend">
          <p>GET /api/v1/health answered{checkedAt ? ` at ${checkedAt}` : ""}. Status: {health.status}.</p>
        </Tile>
        <Tile label="API contract" tone="info" value={health.contractVersion} testId="status-api-version">
          <p>Engine version {health.engineVersion}. The UIs refuse any other contract version.</p>
        </Tile>
        <Tile label="Isolation" tone={enforced ? "pass" : "warn"} value={health.isolationMode} testId="status-isolation">
          <p>{enforced ? "The examiner runs as a separate OS user, over an authenticated socket, and cannot read the sealed claim."
            : "Development mode. OS-level separation is not enforced on this server."}</p>
        </Tile>
        <Tile label="Judge mode" tone={health.judgeMode ? "pass" : "info"} value={health.judgeMode ? "ON" : "OFF"} testId="status-judge">
          <p>{health.judgeMode ? "The server refuses to start unless isolation is enforced; cases expire." : "Judge mode is off."}</p>
        </Tile>
        {lab ? (
          <Tile label="Demonstration signer" tone={lab.signer ? "pass" : "warn"} value={lab.signer ? "SIGNING ON" : "SIGNING OFF"} testId="status-signer">
            <p>{lab.signer ? <>Disposable key <code className="vk-hash" data-testid="status-key-id">{lab.signer.keyId}</code>. Its private half never leaves the server.</>
              : "No signing key is configured, so new bundles are unsigned."}</p>
          </Tile>
        ) : (
          <Tile label="Demonstration signer" tone="warn" value="NOT ENABLED" testId="status-signer">
            <p>{labError ?? "The demonstration lab is not enabled on this server."}</p>
          </Tile>
        )}
      </div>
    </>
  );
}

function DemoList({ demos }: { demos: Demo[] }) {
  return (
    <ul>
      {demos.map((d) => (
        <li key={d.id}><a href={d.href} data-demo={d.id}>{d.title}</a> <span className="vk-muted">built to show {d.designed}</span></li>
      ))}
    </ul>
  );
}

/**
 * The isolation boundary, drawn from what the backend reported. The two rooms are a fixed description of the
 * architecture; the wall between them is solid only when /health says ENFORCED, dashed when UNENFORCED and dotted
 * when nothing was reported. No isolation is ever drawn that the server did not claim.
 */
export function IsolationDiagram({ health, lab }: { health: Health | null; lab: DemoStatus | null }) {
  const mode = health?.isolationMode ?? null;
  const wall = mode === "ENFORCED" ? "" : mode === "UNENFORCED" ? "vk-warn" : "vk-unknown";
  const label = mode ?? "NOT CHECKED";
  return (
    <aside className="vk-diagram" aria-label="Isolation boundary" data-testid="isolation-diagram">
      <h2>Where the claim is kept apart</h2>
      <p className="vk-sub">{mode === "ENFORCED" ? "Live: this server enforces the boundary below."
        : mode === "UNENFORCED" ? "Live: this server runs WITHOUT OS-level separation (development mode)."
          : "The backend was not reachable, so the boundary is not reported."}</p>
      <div className="vk-rooms">
        <div className="vk-room"><b>Custodian</b><code>vk-custodian</code>
          <ul><li>holds the encrypted, sealed claim</li><li>compares only after the examination is committed</li><li>signs the bundle</li></ul></div>
        <div className={`vk-wall ${wall}`} aria-hidden="true"><span>{label}</span></div>
        <div className="vk-room"><b>Examiner</b><code>vk-examiner</code>
          <ul><li>sees the frozen spec and evidence</li><li>never receives a claimed result</li><li>cannot read the vault or the key</li></ul></div>
      </div>
      <div className="vk-flow"><div>freeze, then seal the claim</div><div>examine blind, then reveal and compare</div></div>
      <p className="vk-signer" data-testid="diagram-signer">{lab?.signer
        ? <>Bundles are signed with a disposable demonstration key, public id <code>{lab.signer.keyId.slice(0, 16)}…</code></>
        : "No signing key is reported by this server."}</p>
    </aside>
  );
}

export function Landing({ health, healthError, loading, lab, labError, checkedAt, onRetry }: {
  health: Health | null; healthError: string | null; loading: boolean;
  lab: DemoStatus | null; labError: string | null; checkedAt: string | null; onRetry: () => void;
}) {
  return (
    <>
      <section className="vk-hero" aria-labelledby="hero-h">
        <div className="vk-hero-in">
          <div className="vk-hero-grid">
            <div>
              <p className="vk-kicker">Forensic verification framework</p>
              <h1 id="hero-h">Don't trust the claim. <span className="vk-l2">Verify the evidence.</span> <span className="vk-l3">Reproduce the verdict.</span></h1>
              <p className="vk-lede">VerdictKit freezes a claim, seals the claimed result away from the examiner, recomputes it blind on policy-checked
                evidence, and returns a signed bundle that anyone can verify and replay offline. It says plainly when a claim cannot be checked.</p>
              <div className="vk-cta">
                <a className="vk-button vk-primary" href="/quote/?demo=padded" data-testid="cta-demo">Run a guided demo</a>
                <a className="vk-button vk-secondary" href="/verify?auto=1&sample=lease-consistent&scenario=trusted-signer" data-testid="cta-verify">Verify a signed bundle</a>
                <a className="vk-button vk-secondary" href="#status">See live system status</a>
              </div>
            </div>
            <IsolationDiagram health={health} lab={lab} />
          </div>
          <ol className="vk-steps" aria-label="How a claim is examined">
            <li><b>Freeze</b>The claim is fixed into a canonical spec. Nothing can be changed afterwards.</li>
            <li><b>Seal</b>The claimed result is encrypted away from the examiner (separate OS user).</li>
            <li><b>Examine blind</b>The examiner recomputes from itemised inputs and evidence across a bounded assumption grid.</li>
            <li><b>Reveal and report</b>Only then is the claim compared. The verdict goes into a signed, replayable bundle.</li>
          </ol>
        </div>
      </section>

      <main id="main">
        <section id="status" aria-labelledby="status-h">
          <p className="vk-kicker">Live from the backend</p>
          <h2 id="status-h">System status</h2>
          <SystemStatus health={health} healthError={healthError} loading={loading} lab={lab} labError={labError} checkedAt={checkedAt} onRetry={onRetry} />
        </section>

        <section aria-labelledby="apps-h">
          <p className="vk-kicker">Two applications, one engine</p>
          <h2 id="apps-h">Choose a specimen</h2>
          <div className="vk-grid">
            <article className="vk-drawer" data-testid="drawer-quote">
              <span className="vk-drawer-tag">DRAWER 1 · QUOTE</span>
              <h3>Quote Autopsy</h3>
              <p className="vk-muted">Vehicle finance and lease worksheets. Recomputes every line from the itemised inputs, blind to the stated totals, and finds the first line that breaks.</p>
              <ul><li>Finance and lease (cap cost known or itemised)</li><li>Texas finance rules checked against pinned sources</li><li>Contradictions localised to a line</li></ul>
              <div className="vk-actions"><a className="vk-button vk-primary" href="/quote/">Open Quote Autopsy</a><a className="vk-button vk-secondary" href="/quote/?demo=padded">Guided demo</a></div>
            </article>
            <article className="vk-drawer" data-testid="drawer-reel">
              <span className="vk-drawer-tag">DRAWER 2 · REEL</span>
              <h3>Reel Autopsy</h3>
              <p className="vk-muted">Mechanical trading-strategy claims. Re-runs the rule on independent data, sweeps undeclared costs and compares the claim with a perfect-foresight ceiling.</p>
              <ul><li>Synthetic, clearly labelled demonstrations</li><li>Fee and slippage sensitivity at counted grid points</li><li>Real claims are blocked, not guessed, without licensed data</li></ul>
              <div className="vk-actions"><a className="vk-button vk-primary" href="/reel/">Open Reel Autopsy</a><a className="vk-button vk-secondary" href="/reel/?demo=fx_reel_impossible_sma">Guided demo</a></div>
            </article>
            <article className="vk-drawer" data-testid="drawer-verify">
              <span className="vk-drawer-tag">DRAWER 3 · BUNDLE</span>
              <h3>Evidence Bundle Verification</h3>
              <p className="vk-muted">Run a sample, receive a digitally signed bundle, download it, then verify it against a trust store the verifier configured. Six results, kept separate.</p>
              <ul><li>Trusted, unknown and revoked signers</li><li>Unsigned historical and tampered bundles</li><li>Replay the verdict, offline if you like</li></ul>
              <div className="vk-actions"><a className="vk-button vk-primary" href="/verify">Open the Verify Lab</a><a className="vk-button vk-secondary" href="/verify?auto=1&sample=lease-consistent&scenario=tampered-bundle">Guided demo</a></div>
            </article>
          </div>
        </section>

        <section aria-labelledby="demos-h">
          <p className="vk-kicker">Direct access</p>
          <h2 id="demos-h">Guided demonstrations</h2>
          <p className="vk-muted">Each link runs the real engine on a labelled sample. “Built to show” is what the sample was designed to demonstrate; the verdict you see is whatever the engine computes.</p>
          <div className="vk-grid" data-testid="guided-demos">
            <div className="vk-card"><h3>Quote Autopsy</h3><DemoList demos={QUOTE_DEMOS} /></div>
            <div className="vk-card"><h3>Reel Autopsy (synthetic data)</h3><DemoList demos={REEL_DEMOS} /></div>
            <div className="vk-card"><h3>Bundle verification</h3>
              <ul>{VERIFY_DEMOS.map((d) => (
                <li key={d.scenario}><a href={d.href} data-demo={d.scenario}>{d.title}</a> <span className="vk-muted">{d.blurb}</span></li>
              ))}</ul>
            </div>
          </div>
        </section>

        <section aria-labelledby="honest-h">
          <p className="vk-kicker">What VerdictKit will not claim</p>
          <h2 id="honest-h">Limits, stated up front</h2>
          <div className="vk-card">
            <ul>
              <li>Not every claim is verifiable. INDETERMINATE and CONDITIONAL are first-class answers, not failures.</li>
              <li>Contradictions inside a claim's own arithmetic and refutations by outside evidence are different findings and are labelled separately.</li>
              <li>Results are "verified at N grid points", never "for all values".</li>
              <li>Reproducibility is claimed for a pinned environment. A signature says who sealed a bundle, never that the claim is true.</li>
              <li>Blinding rests on OS-user separation, encryption and a type partition, not on hashes.</li>
              <li>Reel Autopsy demonstrations use synthetic price data. Quote Autopsy samples are constructed worksheets, not real dealer quotes.</li>
            </ul>
          </div>
        </section>
      </main>
    </>
  );
}
