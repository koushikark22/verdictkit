/**
 * The six results of verifying a bundle, kept separate on purpose (docs/SIGNING.md):
 * evidence integrity, signature validity, signer trust, authenticity, verdict reproducibility
 * and isolation mode. Every value is copied from an API response; nothing is derived here.
 */
import type { ReactNode } from "react";
import type { AuthenticityReport, IntegrityReport, IsolationMode, ReproducibilityReport } from "./types";

type Tone = "pass" | "fail" | "warn" | "info";

const SIGNATURE_TONE: Record<string, Tone> = { VALID: "pass", UNSIGNED: "warn", INVALID: "fail", UNSUPPORTED_ALGORITHM: "fail" };
const TRUST_TONE: Record<string, Tone> = { TRUSTED: "pass", UNTRUSTED_SIGNER: "fail", NOT_EVALUATED: "warn" };
const REPRO_TONE: Record<string, Tone> = {
  REPRODUCED: "pass", REPRODUCED_ACROSS_ENV: "pass", DIVERGED: "fail", UNVERIFIABLE: "fail", NOT_RUN: "info",
};

export interface VerificationInput {
  integrity: IntegrityReport; reproducibility: ReproducibilityReport; authenticity: AuthenticityReport;
}

function Prop({ title, tone, value, testId, children }: {
  title: string; tone: Tone; value: string; testId: string; children?: ReactNode;
}) {
  return (
    <div className={`vk-prop vk-${tone}`}>
      <h5>{title}</h5>
      <div className="vk-value"><b data-testid={testId}>{value}</b></div>
      {children}
    </div>
  );
}

const REASON_TEXT: Record<string, string> = {
  NO_ENVELOPE: "no signature is attached", KEY_NOT_IN_TRUST_STORE: "the verifier's trust store does not list this key",
  KEY_REVOKED: "the verifier's trust store lists this key as revoked", KEY_EXPIRED: "the key's validity window has ended",
  KEY_NOT_YET_VALID: "the key's validity window has not started", INTEGRITY_NOT_VERIFIED: "the integrity checks did not pass",
  SIGNATURE_MISMATCH: "the signature does not match the signed manifest", MANIFEST_HASH_MISMATCH: "the manifest differs from what was signed",
  TRUST_STORE_NOT_CONFIGURED: "the verifier has no trust store configured", KEY_ROTATED: "the key was rotated but is still inside its window",
};

export function VerificationReport({ report, isolationMode, testId, heading }: {
  report: VerificationInput; isolationMode: IsolationMode | null; testId: string; heading?: string;
}) {
  const { integrity, reproducibility: repro, authenticity: auth } = report;
  const failed = integrity.checks.filter((c) => !c.ok).map((c) => c.check);
  const reasons = auth.reasonCodes.filter((r) => r !== "NO_ENVELOPE" || auth.signatureValidity === "UNSIGNED");
  return (
    <div data-testid={testId}>
      {heading ? <h4>{heading}</h4> : null}
      <div className="vk-props">
        <Prop title="1 · Evidence integrity" tone={integrity.status === "VERIFIED" ? "pass" : "fail"} value={integrity.status} testId="integrity-status">
          <p>{integrity.checks.map((c) => `${c.check.toLowerCase().replace(/_/g, " ")} ${c.ok ? "ok" : "FAILED"}`).join(" · ")}
            {failed.length ? ` — ${failed.length} check${failed.length === 1 ? "" : "s"} failed` : ""}</p>
        </Prop>
        <Prop title="2 · Signature validity" tone={SIGNATURE_TONE[auth.signatureValidity] ?? "warn"} value={auth.signatureValidity} testId="signature-validity">
          <p>{auth.signer ? <>Signer key <code className="vk-hash" data-testid="signer-key-id">{auth.signer.keyId}</code> ({auth.signer.algorithm})</>
            : "No signer is identified."}</p>
        </Prop>
        <Prop title="3 · Signer trust" tone={TRUST_TONE[auth.signerTrust] ?? "warn"} value={auth.signerTrust} testId="signer-trust">
          <p>{auth.trustStore ? `Trust store serial ${auth.trustStore.serial}, sha256 ${auth.trustStore.sha256.slice(0, 12)}…` : "No trust store was consulted."}</p>
          {reasons.length ? <p data-testid="reason-codes">{reasons.map((r) => `${r}${REASON_TEXT[r] ? ` (${REASON_TEXT[r]})` : ""}`).join("; ")}</p> : null}
        </Prop>
        <Prop title="4 · Authenticity" tone={auth.status === "ESTABLISHED" ? "pass" : "warn"} value={auth.status} testId="authenticity-status">
          <p>{auth.note}</p>
        </Prop>
        <Prop title="5 · Verdict reproducibility" tone={REPRO_TONE[repro.status] ?? "warn"} value={repro.status} testId="repro-status">
          <p>original <code className="vk-hash">{repro.originalVerdictHash}</code>
            {repro.replayedVerdictHash ? <> · replayed <code className="vk-hash">{repro.replayedVerdictHash}</code></> : " · not replayed"}
            {repro.envMatch === null ? "" : repro.envMatch ? " · same environment" : " · different environment"}</p>
        </Prop>
        <Prop title="6 · Isolation mode" tone={isolationMode === "ENFORCED" ? "pass" : "warn"} value={isolationMode ?? "UNKNOWN"} testId="isolation-mode">
          <p>{isolationMode === "ENFORCED" ? "The examiner ran as a separate OS user that cannot read the sealed claim."
            : isolationMode === "UNENFORCED" ? "Development mode: OS-level separation was not enforced." : "Not reported."}</p>
        </Prop>
      </div>
      <details className="vk-help">
        <summary>What do these six results mean?</summary>
        <p><b>Integrity</b>: every file in the bundle still matches the hash written in its manifest, and the ledger chain and commitment hold.
          <b> Signature validity</b>: the digital signature matches the exact manifest bytes. <b>Signer trust</b>: whether the verifier's own
          trust store accepts that signing key; a key inside the bundle is never trusted on its own. <b>Authenticity</b> is established only
          when the signature is valid, the signer is trusted and integrity is verified. <b>Reproducibility</b>: the examination was run again
          from the bundle and produced the same verdict hash. <b>Isolation</b>: whether the examiner was kept a separate OS user.
          None of these says the claim is true.</p>
      </details>
    </div>
  );
}
