#!/usr/bin/env node
/*
 * VerdictKit local gateway: one origin for the portal, both applications and the API.
 *
 *   /            portal (overview) and /verify (Verify Lab)      <- ui/hub/dist
 *   /quote/      Quote Autopsy                                   <- apps/quote-autopsy/web/dist
 *   /reel/       Reel Autopsy                                    <- apps/reel-autopsy/web/dist
 *   /api/v1/*    proxied to the Docker backend on 127.0.0.1:<api-port>
 *
 * Security posture: binds 127.0.0.1 only (a non-loopback --host is refused); checks the Host header
 * against the port it serves, which closes DNS rebinding; forwards a short allowlist of request
 * headers (no cookies, no credentials); logs nothing per request, so case ids never reach a log.
 * Standard library only. It is a local convenience, not a public server.
 *
 *   node scripts/gateway.mjs --port 5170 --api-port 8000 [--image verdictkit:batch2]
 */
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}
const host = arg("host", "127.0.0.1");
const port = Number(arg("port", process.env.VK_GATEWAY_PORT ?? "5170"));
const apiPort = Number(arg("api-port", process.env.VK_API_PORT ?? "8000"));
const image = arg("image", process.env.VK_IMAGE ?? "verdictkit:batch2");
const logFile = arg("log", "");

// With --log the gateway appends its few lines to that file itself. The launcher can then start it without
// redirecting any handle, so a caller's output pipe can never be inherited and held open by this process.
function log(line, isError = false) {
  if (logFile) {
    try { fs.appendFileSync(logFile, `${line}\n`); } catch { /* logging must never stop the gateway */ }
  } else if (isError) console.error(line); else console.log(line);
}

if (host !== "127.0.0.1") {
  log(`refusing to bind ${host}: the gateway listens on 127.0.0.1 only`, true);
  process.exit(2);
}
for (const [name, value] of [["port", port], ["api-port", apiPort]]) {
  if (!Number.isInteger(value) || value < 1024 || value > 65535) {
    log(`--${name} must be an integer from 1024 to 65535`, true);
    process.exit(2);
  }
}

const MOUNTS = [
  { prefix: "/quote/", dir: path.join(root, "apps", "quote-autopsy", "web", "dist") },
  { prefix: "/reel/", dir: path.join(root, "apps", "reel-autopsy", "web", "dist") },
  { prefix: "/", dir: path.join(root, "ui", "hub", "dist") },
];
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
  ".png": "image/png", ".ico": "image/x-icon", ".txt": "text/plain; charset=utf-8", ".map": "application/json",
  ".woff2": "font/woff2",
};
const SECURITY = {
  "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
  "Cross-Origin-Resource-Policy": "same-origin", "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};
const REQUEST_HEADERS = ["accept", "content-type", "content-length", "last-event-id"];
const RESPONSE_HEADERS = ["content-type", "content-length", "content-disposition", "cache-control", "x-verdictkit-contract", "retry-after"];
const API_METHODS = new Set(["GET", "HEAD", "POST", "PATCH"]);
const started = Date.now();

function send(res, status, body, headers = {}) {
  res.writeHead(status, { ...SECURITY, "Cache-Control": "no-store", ...headers });
  res.end(body);
}
function sendJson(res, status, value) {
  const body = JSON.stringify(value);
  send(res, status, body, { "Content-Type": "application/json; charset=utf-8", "Content-Length": Buffer.byteLength(body) });
}

function serveStatic(req, res, pathname) {
  const mount = MOUNTS.find((m) => pathname.startsWith(m.prefix)) ?? MOUNTS[MOUNTS.length - 1];
  const rel = path.posix.normalize(pathname.slice(mount.prefix.length) || "index.html");
  if (rel.startsWith("..") || rel.includes("\0")) return send(res, 400, "Bad path");
  // Nothing under a dot-name is ever served or mapped to the SPA (.git, .env and the like), whatever the mount.
  if (rel.split("/").some((segment) => segment.startsWith("."))) return send(res, 404, "Not found");
  let file = path.join(mount.dir, rel.endsWith("/") ? path.join(rel, "index.html") : rel);
  if (path.relative(mount.dir, file).startsWith("..")) return send(res, 400, "Bad path");
  let isIndex = false;
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    // Single-page-app fallback for extension-less routes such as /verify; a missing asset is a 404.
    if (path.extname(rel)) return send(res, 404, "Not found");
    file = path.join(mount.dir, "index.html");
    isIndex = true;
  }
  if (!fs.existsSync(file)) {
    return send(res, 503, "This UI has not been built yet. Run: npm run build:portal", { "Content-Type": "text/plain; charset=utf-8" });
  }
  const ext = path.extname(file).toLowerCase();
  const data = fs.readFileSync(file);
  const immutable = !isIndex && ext !== ".html" && /[\\/]assets[\\/]/.test(file);
  res.writeHead(200, {
    ...SECURITY, "Content-Type": MIME[ext] ?? "application/octet-stream", "Content-Length": data.length,
    "Cache-Control": immutable ? "public, max-age=31536000, immutable" : "no-store",
  });
  res.end(req.method === "HEAD" ? undefined : data);
}

function proxyApi(req, res, url) {
  const headers = {};
  for (const h of REQUEST_HEADERS) if (req.headers[h]) headers[h] = req.headers[h];
  const upstream = http.request({ host: "127.0.0.1", port: apiPort, method: req.method, path: url.pathname + url.search, headers }, (up) => {
    const out = { ...SECURITY };
    for (const h of RESPONSE_HEADERS) if (up.headers[h]) out[h] = up.headers[h];
    res.writeHead(up.statusCode ?? 502, out);
    up.pipe(res);
  });
  upstream.on("error", () => {
    if (res.headersSent) return res.destroy();
    sendJson(res, 502, { error: { code: "BACKEND_UNAVAILABLE", message: "API backend is unavailable" } });
  });
  res.on("close", () => upstream.destroy());
  req.pipe(upstream);
}

const server = http.createServer((req, res) => {
  const allowedHosts = new Set([`127.0.0.1:${port}`, `localhost:${port}`]);
  if (!allowedHosts.has(String(req.headers.host ?? "").toLowerCase())) {
    return send(res, 421, "Misdirected request: this gateway answers only on its own loopback address", { "Content-Type": "text/plain; charset=utf-8" });
  }
  let url, pathname;
  try {
    url = new URL(req.url ?? "/", `http://127.0.0.1:${port}`);
    pathname = decodeURIComponent(url.pathname);
  } catch {
    return send(res, 400, "Bad request");
  }
  // A NUL or a backslash has no business in a path here, and on Windows the latter is a separator.
  if (pathname.includes("\0") || pathname.includes("\\")) return send(res, 400, "Bad request");
  if (pathname === "/__gateway/health") return sendJson(res, 200, { ok: true, apiPort, uptimeSeconds: Math.round((Date.now() - started) / 1000) });
  if (pathname === "/__gateway/config.json") return sendJson(res, 200, { image });
  if (pathname.startsWith("/api/")) {
    if (!API_METHODS.has(req.method ?? "")) return sendJson(res, 405, { error: { code: "METHOD_NOT_ALLOWED", message: "HTTP method unavailable" } });
    return proxyApi(req, res, url);
  }
  if (req.method !== "GET" && req.method !== "HEAD") return send(res, 405, "Method not allowed");
  if (pathname === "/quote" || pathname === "/reel") {
    return send(res, 308, "", { Location: `${pathname}/${url.search}` });
  }
  return serveStatic(req, res, pathname);
});

server.on("error", (e) => {
  log(e.code === "EADDRINUSE" ? `port ${port} is already in use` : `gateway error: ${e.code ?? e.message}`, true);
  process.exit(e.code === "EADDRINUSE" ? 3 : 1);
});
server.listen(port, host, () => {
  log(`VerdictKit gateway: http://127.0.0.1:${port}/  (api -> 127.0.0.1:${apiPort}, image ${image})`);
});
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => server.close(() => process.exit(0)));
