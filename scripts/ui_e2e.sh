#!/usr/bin/env bash
# Browser E2E for both UIs against a real, locally started API (UNENFORCED: OS-level
# isolation exists only in the container; the UI shows that). Requires: uv workspace
# synced, `npm ci && npm run build`, and Playwright with Chromium on NODE_PATH or locally.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
GROUPS_TO_KILL=()
cleanup() {
  # Each server runs in its own process group so its children (node, uvicorn) die too.
  for pgid in "${GROUPS_TO_KILL[@]}"; do kill -TERM -- "-$pgid" 2>/dev/null || true; done
  sleep 0.5
  for pgid in "${GROUPS_TO_KILL[@]}"; do kill -KILL -- "-$pgid" 2>/dev/null || true; done
  rm -rf "$WORK"
}
trap cleanup EXIT

port_free() { ! (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
for port in 8000 4173 4174; do
  port_free "$port" || { echo "port $port is already in use; refusing to test against a stale server" >&2; exit 2; }
done

start() {  # start <log> <dir> <command...>
  local log="$1" dir="$2"; shift 2
  (cd "$dir" && exec setsid "$@") > "$log" 2>&1 &
  GROUPS_TO_KILL+=("$!")
}
export VK_DRAFT_DIR="$WORK/custody" VK_JUDGE_MODE=0 VK_EXAMINER_SOCKET=""
VK_VAULT_KEY="$(python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
export VK_VAULT_KEY
start "$WORK/api.log" "$ROOT" uv run --no-sync python -m verdictkit.api --host 127.0.0.1 --port 8000
start "$WORK/quote.log" "$ROOT/apps/quote-autopsy/web" npx vite preview --host 127.0.0.1
start "$WORK/reel.log" "$ROOT/apps/reel-autopsy/web" npx vite preview --host 127.0.0.1

wait_for() {
  for _ in $(seq 1 120); do curl -fsS --noproxy '*' "$1" >/dev/null 2>&1 && return 0; sleep 0.5; done
  echo "server not ready: $1" >&2; cat "$WORK"/*.log >&2; return 1
}
wait_for http://127.0.0.1:8000/api/v1/health
wait_for http://127.0.0.1:4173/api/v1/health   # quote preview proxies to this run's API
wait_for http://127.0.0.1:4174/api/v1/health   # reel preview proxies to this run's API
node "$ROOT/tests/ui/e2e_browser.cjs"
