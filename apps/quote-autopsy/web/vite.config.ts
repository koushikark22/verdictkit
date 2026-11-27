import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The UI talks only to the real API (no mock verdicts). VK_API_URL points the dev and
// preview servers at a running `python -m verdictkit.api` (default 127.0.0.1:8000).
// `vite build --mode portal` builds for the unified local gateway, which serves this app under /quote/.
const api = process.env.VK_API_URL ?? "http://127.0.0.1:8000";
export default defineConfig(({ mode }) => ({
  base: mode === "portal" ? "/quote/" : "/",
  plugins: [react()],
  server: { port: 5173, strictPort: true, proxy: { "/api": api } },
  preview: { port: 4173, strictPort: true, proxy: { "/api": api } },
  test: { environment: "jsdom", globals: true },
}));
