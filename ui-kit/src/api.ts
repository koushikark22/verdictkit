/**
 * Contract-checked client for /api/v1 (docs/API_CONTRACT.md). The UI refuses any response
 * whose contractVersion is not 1.2.0, never invents results, and surfaces blockers and
 * errors exactly as the server reports them.
 */
import type {
  BundleMetadata, ClaimTypeInfo, DraftCase, EvidenceResult, FrozenCase, Health, IntakeRequest,
  OutcomeResponse, ProgressEvent, ReplayReport, RunAccepted, RunRecord, Blocker,
} from "./types";

export const CONTRACT_VERSION = "1.2.0";
export const TERMINAL_STAGES = new Set(["RUN_COMPLETED", "RUN_INDETERMINATE", "RUN_BLOCKED", "RUN_FAILED"]);

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public field: string | null = null) {
    super(message);
    this.name = "ApiError";
  }
}

/** A 422 BlockedResponse: the engine could not proceed. Not an error in the system. */
export class BlockedError extends Error {
  constructor(public caseId: string, public blockers: Blocker[]) {
    super(blockers.map((b) => `${b.code}: ${b.message}`).join("; "));
    this.name = "BlockedError";
  }
}

export class ContractMismatchError extends Error {
  constructor(public got: unknown) {
    super(`Server speaks contract ${String(got)}; this UI requires ${CONTRACT_VERSION}`);
    this.name = "ContractMismatchError";
  }
}

type Fetch = typeof fetch;

export function createClient(base = "/api/v1", fetchImpl: Fetch = (...a) => fetch(...a)) {
  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetchImpl(base + path, {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers ?? {}) },
      credentials: "same-origin",
    });
    let body: any;
    try {
      body = await res.json();
    } catch {
      throw new ApiError(res.status, "NON_JSON_RESPONSE", "Server returned a non-JSON response");
    }
    if (!body || body.contractVersion !== CONTRACT_VERSION) throw new ContractMismatchError(body?.contractVersion);
    if (res.status === 422 && body.executionStatus === "BLOCKED") throw new BlockedError(body.caseId, body.blockers);
    if (!res.ok) {
      const e = body.error ?? {};
      throw new ApiError(res.status, e.code ?? "HTTP_ERROR", e.message ?? "Request failed", e.field ?? null);
    }
    return body as T;
  }

  const json = (method: string, payload?: unknown): RequestInit => ({
    method,
    headers: { "Content-Type": "application/json" },
    body: payload === undefined ? undefined : JSON.stringify(payload),
  });

  return {
    health: () => request<Health>("/health"),
    claimTypes: () => request<{ claimTypes: ClaimTypeInfo[] }>("/claim-types"),
    createCase: (intake: IntakeRequest) => request<DraftCase>("/cases", json("POST", intake)),
    updateCase: (caseId: string, update: Record<string, unknown>) =>
      request<DraftCase>(`/cases/${encodeURIComponent(caseId)}`, json("PATCH", update)),
    freeze: (caseId: string) => request<FrozenCase>(`/cases/${encodeURIComponent(caseId)}/freeze`, json("POST")),
    acquireEvidence: (caseId: string) =>
      request<EvidenceResult>(`/cases/${encodeURIComponent(caseId)}/evidence`, json("POST")),
    startRun: (caseId: string) => request<RunAccepted>(`/cases/${encodeURIComponent(caseId)}/runs`, json("POST")),
    getRun: (caseId: string, runId: string) =>
      request<RunRecord>(`/cases/${encodeURIComponent(caseId)}/runs/${encodeURIComponent(runId)}`),
    outcome: (caseId: string) => request<OutcomeResponse>(`/cases/${encodeURIComponent(caseId)}/outcome`),
    bundleUrl: (caseId: string) => `${base}/cases/${encodeURIComponent(caseId)}/bundle`,
    bundleMetadata: (caseId: string) =>
      request<BundleMetadata>(`/cases/${encodeURIComponent(caseId)}/bundle/metadata`),
    bundleBytes: async (caseId: string): Promise<Blob> => {
      const res = await fetchImpl(`${base}/cases/${encodeURIComponent(caseId)}/bundle`);
      if (!res.ok) throw new ApiError(res.status, "BUNDLE_UNAVAILABLE", "Bundle unavailable");
      return res.blob();
    },
    replay: (bundle: Blob) =>
      request<ReplayReport>("/replays", { method: "POST", headers: { "Content-Type": "application/zip" }, body: bundle }),
  };
}

export type Client = ReturnType<typeof createClient>;

/** Parse one SSE frame ("id: n\nevent: progress\ndata: {...}"). Returns null for comments. */
export function parseSseFrame(frame: string): ProgressEvent | null {
  const data = frame.split("\n").filter((l) => l.startsWith("data: ")).map((l) => l.slice(6)).join("\n");
  if (!data) return null;
  const event = JSON.parse(data) as ProgressEvent;
  if (event.contractVersion !== CONTRACT_VERSION) throw new ContractMismatchError(event.contractVersion);
  return event;
}

/**
 * Follow a run's progress. Events are only ever those persisted by the server
 * (write-then-emit); after the stream ends the persisted record is re-read so the
 * displayed sequence is exactly the record.
 */
export async function followRun(
  client: Client, accepted: RunAccepted, onEvent: (e: ProgressEvent) => void, fetchImpl: Fetch = (...a) => fetch(...a),
): Promise<RunRecord> {
  const res = await fetchImpl(accepted.eventsUrl, { headers: { Accept: "text/event-stream" } });
  if (res.ok && res.body) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        const event = parseSseFrame(buffer.slice(0, idx));
        buffer = buffer.slice(idx + 2);
        if (event) onEvent(event);
      }
    }
  }
  return client.getRun(accepted.caseId, accepted.runId);
}
