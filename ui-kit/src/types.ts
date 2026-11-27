/** TypeScript view of api/openapi.yaml (contract 1.2.0). Only fields the UIs read. */

export type DataMode = "LIVE_EVIDENCE" | "SYNTHETIC_DEMO";
export type IsolationMode = "ENFORCED" | "UNENFORCED";
export type ExecutionStatus = "COMPLETED" | "BLOCKED" | "INDETERMINATE";
export type EpistemicStatus =
  | "CONSISTENT" | "CONTRADICTED" | "SUPPORTED" | "REFUTED" | "CONDITIONAL"
  | "WITHIN_BOUND" | "IMPOSSIBLE" | "INDETERMINATE";

export interface Blocker { code: string; message: string; field?: string | null }

export interface Health {
  contractVersion: string; status: "ok"; isolationMode: IsolationMode;
  judgeMode: boolean; engineVersion: string;
}

export interface ClaimTypeInfo {
  claimType: string; schemaVersion: number; outcomeFields: string[]; acceptsPastedText: boolean;
}

export interface ParameterEntry {
  name: string; value: string | null;
  range?: { kind: "RANGE" | "SET"; min?: string; max?: string; step?: string; values?: string[] } | null;
  state: "SPECIFIED" | "ASSUMED" | "MISSING";
  sourceSpan: { start: number; end: number } | null;
  basis: string; critical: boolean;
}

export interface DraftCase {
  contractVersion: string; caseId: string; claimType: string; state: "DRAFT"; dataMode: DataMode;
  parameterLedger: ParameterEntry[]; outcomeFields: { name: string; captured: boolean }[];
  blockers: Blocker[]; expiresAt: string;
}

export interface Specimen {
  specimenId: string; claimType: string; claimTypeLabel: string;
  source: "USER_SUBMITTED" | "SYNTHETIC_FIXTURE"; fixtureId?: string | null; title: string;
  fields: { label: string; value: string }[]; frozenAt: string | null; specHashShort: string | null;
}

export interface FrozenCase {
  contractVersion: string; caseId: string; state: "FROZEN"; specHash: string;
  commitment: { alg: string; digest: string }; frozenAt: string; ledgerSeq: number;
  parameterLedger: ParameterEntry[]; specimen: Specimen;
}

export interface EvidenceDTO {
  evidenceId: string; providerId: string; origin: string; retrievedAt: string; snapshotHash: string;
  independenceBasis: string; rightsNote: string; licenseClass: string; embeddedInBundle: boolean;
  uri: string | null;
}

export interface EvidenceResult { contractVersion: string; caseId: string; evidence: EvidenceDTO[] }

export interface RunAccepted {
  contractVersion: string; runId: string; caseId: string; state: string; eventsUrl: string; runUrl: string;
}

export interface ProgressEvent {
  contractVersion: string; runId: string; seq: number; stage: string; at: string;
  ledgerSeq: number | null; ledgerKind: string | null;
  detail: { pointsDone?: number; pointsTotal?: number; blocker?: Blocker };
}

export interface RunRecord {
  contractVersion: string; runId: string; caseId: string; state: string; isolationMode: IsolationMode;
  startedAt: string; finishedAt: string | null; events: ProgressEvent[];
}

export interface Numbers {
  expected?: string | null; observed?: string | null; difference?: string | null; tolerance?: string | null;
}

export interface FindingDTO {
  findingId: string; status: EpistemicStatus; confidenceClass: string | null;
  confidenceScope: string | null; statement: string; reason: string | null; numbers: Numbers;
  evidenceIds: string[]; assumptionDependencies: string[]; gridPointsEvaluated: number;
  keyRecordIds: string[]; pointOfFailure?: boolean; propagated?: boolean;
}

export interface KeyRecord {
  recordId: string; findingId: string | null; recordRole: string; recordKind: string;
  payload: Record<string, unknown>; note: string;
}

export interface Sensitivity {
  templateVersion: string; gridCap: number; variantsExecuted: number;
  axes: { name: string; values: string[]; origin: string }[];
  results: {
    findingId: string; aggregate: "ALL_PASS" | "NONE_PASS" | "MIXED"; passCount: number; failCount: number;
    cells: { variant: number; point: Record<string, string>; passed: boolean; margin: string }[];
  }[];
}

export interface OutcomeResponse {
  contractVersion: string; caseId: string; runId: string | null; claimType: string;
  dataMode: DataMode; demonstrationOnly: boolean; demonstrationNotice: string | null;
  specimen: Specimen; executionStatus: ExecutionStatus;
  headline: { status: EpistemicStatus | null; confidenceClass: string | null };
  findings: FindingDTO[]; sensitivity: Sensitivity | null; parameterLedger: ParameterEntry[];
  evidence: EvidenceDTO[]; keyRecords: KeyRecord[];
  diagnostics: { computedAfterReveal: true; affectsVerdict: false; items: Record<string, unknown>[] } | null;
  blockers: Blocker[]; specHash: string | null; verdictHash: string | null;
  isolationMode: IsolationMode; bundleAvailable: boolean;
}

export interface IntegrityReport { status: "VERIFIED" | "FAILED"; checks: { check: string; ok: boolean }[] }

export interface ReproducibilityReport {
  status: string; originalVerdictHash: string; replayedVerdictHash: string | null; envMatch: boolean | null;
}

/** Signature validity, signer trust and authenticity are separate results (design D5.3). */
export interface AuthenticityReport {
  status: "NOT_ESTABLISHED" | "ESTABLISHED"; note: string;
  signatureValidity: "UNSIGNED" | "VALID" | "INVALID" | "UNSUPPORTED_ALGORITHM";
  signerTrust: "NOT_EVALUATED" | "TRUSTED" | "UNTRUSTED_SIGNER";
  reasonCodes: string[];
  signer: { keyId: string; algorithm: "ed25519" } | null;
  trustStore: { formatVersion: number; serial: number; sha256: string; evaluatedAt: string } | null;
}

export interface BundleMetadata {
  contractVersion: string; caseId: string; bundleSha256: string; sizeBytes: number; engineVersion: string;
  envFingerprint: { engineVersion: string; pythonVersion: string; lockfileSha256: string; imageDigest: string };
  isolationMode: IsolationMode; embeddedEvidence: string[];
  refetchOnlyEvidence: { evidenceId: string; uri: string; snapshotHash: string }[];
  integrity: IntegrityReport; reproducibility: ReproducibilityReport;
  authenticity: AuthenticityReport; replayCommand: string;
}

export interface ReplayReport {
  contractVersion: string; integrity: IntegrityReport; reproducibility: ReproducibilityReport;
  authenticity: AuthenticityReport; notes: string[];
}

/** Intake body. Outcome values are write-only: the server never echoes them. */
export interface IntakeRequest {
  claimType: string;
  dataMode: DataMode;
  fixtureId?: string | null;
  form?: { params: Record<string, unknown>; outcomes: Record<string, unknown>; assumptions?: Record<string, unknown> };
  pastedText?: string | null;
}
