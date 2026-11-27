import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The portal talks only to the real API (no mock verdicts). VK_API_URL points the dev and preview
// servers at a running backend (default 127.0.0.1:8000). Normally the local gateway serves the
// built portal and proxies /api, so the whole product shares one origin.
const api = process.env.VK_API_URL ?? "http://127.0.0.1:8000";
export default defineConfig({
  base: "/",
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5170, strictPort: true, proxy: { "/api": api } },
  preview: { host: "127.0.0.1", port: 4170, strictPort: true, proxy: { "/api": api } },
  test: { environment: "jsdom", globals: true },
});
