import { useEffect, useMemo, useState } from "react";
import { ApiError, AppShell, createClient, describeError, useHealth, type DemoStatus } from "@verdictkit/ui-kit";
import { Landing, type PortalConfig } from "./Landing";
import { VerifyLab } from "./VerifyLab";

const DEFAULT_CONFIG: PortalConfig = { image: "verdictkit:batch2" };

/** Two routes served by the local gateway: "/" (overview) and "/verify" (the Verify Lab). */
export function App() {
  const client = useMemo(() => createClient(), []);
  const { health, error, loading, reload } = useHealth(client);
  const [lab, setLab] = useState<DemoStatus | null>(null);
  const [labError, setLabError] = useState<string | null>(null);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  const [config, setConfig] = useState<PortalConfig>(DEFAULT_CONFIG);
  const route = (window.location.pathname.replace(/\/+$/, "") || "/") === "/verify" ? "verify" : "home";

  useEffect(() => {
    if (!health) { setLab(null); return; }
    setCheckedAt(`${new Date().toISOString().slice(11, 19)} UTC`);
  }, [health]);

  // The demonstration lab is an opt-in server extension: 404 simply means it was not enabled.
  const up = health !== null;
  useEffect(() => {
    if (!up) return;
    client.demoStatus().then(
      (s) => { setLab(s); setLabError(null); },
      (e) => { setLab(null); setLabError(e instanceof ApiError && e.code === "NOT_FOUND" ? "The demonstration lab is not enabled on this server." : describeError(e)); });
  }, [client, up]);

  // Best effort: the local gateway reports the Docker image name so offline commands are exact.
  useEffect(() => {
    fetch("/__gateway/config.json", { headers: { Accept: "application/json" } })
      .then((r) => (r.ok ? r.json() : null))
      .then((c) => { if (c && typeof c.image === "string" && /^[\w./:@-]{1,120}$/.test(c.image)) setConfig({ image: c.image }); })
      .catch(() => undefined);
  }, []);

  return (
    <AppShell active={route === "verify" ? "verify" : "home"} health={health} error={error} loading={loading}>
      {route === "verify"
        ? <VerifyLab client={client} health={health} lab={lab} labError={labError} image={config.image} />
        : <Landing health={health} healthError={error} loading={loading} lab={lab} labError={labError} checkedAt={checkedAt} onRetry={reload} />}
    </AppShell>
  );
}
