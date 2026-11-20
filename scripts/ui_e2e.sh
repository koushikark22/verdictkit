#!/usr/bin/env bash
# Browser E2E for both UIs against a real, locally started API (UNENFORCED: OS-level
# isolation exists only in the container; the UI shows that). Requires: uv workspace
# synced, `npm ci && npm run build`, and Playwright with Chromium on NODE_PATH or locally.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
cleanup() { kill "${PIDS[@]}" 2>/dev/null || true; rm -rf "$WORK"; }
PIDS=()
trap cleanup EXIT
export VK_DRAFT_DIR="$WORK/custody" VK_JUDGE_MODE=0 VK_EXAMINER_SOCKET=""
VK_VAULT_KEY="$(python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
export VK_VAULT_KEY
(cd "$ROOT" && uv run --no-sync python -m verdictkit.api --host 127.0.0.1 --port 8000) > "$WORK/api.log" 2>&1 &
PIDS+=($!)
(cd "$ROOT/apps/quote-autopsy/web" && npx vite preview --host 127.0.0.1) > "$WORK/quote.log" 2>&1 &
PIDS+=($!)
(cd "$ROOT/apps/reel-autopsy/web" && npx vite preview --host 127.0.0.1) > "$WORK/reel.log" 2>&1 &
PIDS+=($!)
for url in http://127.0.0.1:8000/api/v1/health http://127.0.0.1:4173/ http://127.0.0.1:4174/; do
  for _ in $(seq 1 60); do curl -fsS --noproxy '*' "$url" >/dev/null 2>&1 && break; sleep 0.5; done
done
node "$ROOT/tests/ui/e2e_browser.cjs"
