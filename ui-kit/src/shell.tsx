/**
 * Shared application shell: brand, navigation, live backend status and the common loading,
 * empty and error states. The status pill shows what /api/v1/health returned and nothing else;
 * when the request fails it says so instead of guessing.
 */
import { useCallback, useEffect, useState, type ReactNode } from "react";
import type { Client } from "./api";
import { ApiError, BlockedError, ContractMismatchError } from "./api";
import type { Health } from "./types";

export function describeError(e: unknown): string {
  if (e instanceof BlockedError) return `Blocked: ${e.message}`;
  if (e instanceof ApiError) return `${e.code}: ${e.message}${e.field ? ` (${e.field})` : ""}`;
  if (e instanceof ContractMismatchError) return e.message;
  return "Unexpected error; no result is shown.";
}

/** A plain-language title and next step for an error the user can act on. */
export function explainError(message: string): { title: string; hint: string | null } {
  if (message.startsWith("BACKEND_UNAVAILABLE")) {
    return { title: "The VerdictKit backend is not reachable",
      hint: "Start it with scripts\\Start-VerdictKit.ps1 (Windows) or scripts/start-verdictkit.sh (Linux), then retry." };
  }
  if (message.startsWith("CUSTODY_NOT_CONFIGURED")) {
    return { title: "This server has no encrypted case storage", hint: "Start the backend through the VerdictKit start script, which configures it." };
  }
  if (message.startsWith("RATE_LIMITED")) return { title: "Too many requests", hint: "Wait a few seconds and try again." };
  if (message.startsWith("PRIVACY_REJECTED")) return { title: "The pasted text contains personal identifiers", hint: "Remove handles, e-mail addresses, links and phone numbers, then retry." };
  if (message.startsWith("Blocked:")) return { title: "The examination was blocked", hint: "A required input or evidence source is missing. Nothing was guessed." };
  return { title: "The request did not complete", hint: null };
}

export function useHealth(client: Client, pollMs = 30000) {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const reload = useCallback(async () => {
    try {
      setHealth(await client.health());
      setError(null);
    } catch (e) {
      setHealth(null);
      setError(describeError(e));
    } finally {
      setLoading(false);
    }
  }, [client]);
  useEffect(() => {
    void reload();
    if (pollMs <= 0) return undefined;
    // A hidden tab does not poll: it would spend the server's per-client request budget for nothing.
    const timer = setInterval(() => { if (!document.hidden) void reload(); }, pollMs);
    return () => clearInterval(timer);
  }, [reload, pollMs]);
  return { health, error, loading, reload };
}

export type NavId = "home" | "quote" | "reel" | "verify";
export const NAV_LINKS: { id: NavId; label: string; href: string }[] = [
  { id: "home", label: "Overview", href: "/" },
  { id: "quote", label: "Quote Autopsy", href: "/quote/" },
  { id: "reel", label: "Reel Autopsy", href: "/reel/" },
  { id: "verify", label: "Verify a Bundle", href: "/verify" },
];

export function Mark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <rect x="1" y="1" width="30" height="30" rx="7" fill="#152a32" stroke="#c9a35b" strokeWidth="2" />
      <path d="M8 11l8 13 8-13" fill="none" stroke="#35b5ad" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="16" cy="7" r="1.7" fill="#c9a35b" />
    </svg>
  );
}

export function LiveStatus({ health, error, loading }: { health: Health | null; error: string | null; loading: boolean }) {
  let tone = "warn", text = "Connecting…";
  if (!loading && health) {
    tone = health.isolationMode === "ENFORCED" ? "pass" : "warn";
    text = `API ${health.contractVersion} · isolation ${health.isolationMode}`;
  } else if (!loading && error?.startsWith("RATE_LIMITED")) {
    // The server answered: it is up and is slowing this browser down. That is not "offline".
    text = "Busy: rate limited, retrying";
  } else if (!loading && error) {
    tone = "fail";
    text = "Backend offline";
  }
  return (
    <span className="vk-live" role="status" data-testid="live-status" title={error ?? undefined}>
      <span className={`vk-dot vk-${tone}`} aria-hidden="true" />{text}
    </span>
  );
}

export function AppShell({ active, health, error, loading, children }: {
  active: NavId | null; health: Health | null; error: string | null; loading: boolean; children: ReactNode;
}) {
  return (
    <>
      <a className="vk-skip" href="#main">Skip to content</a>
      <header className="vk-topbar">
        <div className="vk-topbar-in">
          <a className="vk-brand" href="/" aria-label="VerdictKit home">
            <Mark /><span>VerdictKit<small>Claim autopsy engine</small></span>
          </a>
          <nav className="vk-nav" aria-label="VerdictKit applications">
            {NAV_LINKS.map((l) => (
              <a key={l.id} href={l.href} aria-current={active === l.id ? "page" : undefined}>{l.label}</a>
            ))}
          </nav>
          <LiveStatus health={health} error={error} loading={loading} />
        </div>
      </header>
      {children}
      <footer className="vk-footer">
        VerdictKit{health ? ` · contract ${health.contractVersion} · engine ${health.engineVersion}` : ""} · local demonstration build,
        not a public service · synthetic and constructed data only · a verdict never says a claim is true for all values, only what was verified at the grid points shown.
      </footer>
    </>
  );
}

export function Spinner({ label }: { label: string }) {
  return <span role="status"><span className="vk-spinner" aria-hidden="true" />{label}</span>;
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return <div className="vk-empty" data-testid="empty-state"><b>{title}</b>{children}</div>;
}

export function ErrorCard({ message, onRetry, testId = "error" }: { message: string; onRetry?: () => void; testId?: string }) {
  const { title, hint } = explainError(message);
  return (
    <div className="vk-errorcard" role="alert">
      <b>{title}</b>
      {hint ? <p>{hint}</p> : null}
      <pre data-testid={testId}>{message}</pre>
      {onRetry ? <button type="button" className="vk-secondary vk-small" onClick={onRetry}>Retry</button> : null}
    </div>
  );
}
