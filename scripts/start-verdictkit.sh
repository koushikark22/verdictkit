#!/usr/bin/env bash
# One command that starts all of VerdictKit locally (Linux/macOS). Prints one entry URL.
#
#   scripts/start-verdictkit.sh [--api-port 8000] [--gateway-port 5170] [--image verdictkit:batch2] [--rebuild]
#
# Starts the Docker backend (enforced OS-user isolation, judge mode, disposable demonstration signer),
# verifies its health, builds the UIs if needed and starts one local gateway. Everything listens on
# 127.0.0.1 only. An occupied port is never freed: the next free port is used. Only the container and
# the gateway process that this script started are ever stopped. No secret is created or printed here.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$REPO/.verdictkit-run"
STATE="$RUN_DIR/state.vars"
CONTAINER="vk-batch2-backend"
LABEL="com.verdictkit.managed=1"
CONTRACT="1.2.0"
API_PORT=8000
GATEWAY_PORT=5170
IMAGE="verdictkit:batch2"
REBUILD=0

while [ $# -gt 0 ]; do
    case "$1" in
        --api-port) API_PORT="$2"; shift 2 ;;
        --gateway-port) GATEWAY_PORT="$2"; shift 2 ;;
        --image) IMAGE="$2"; shift 2 ;;
        --rebuild) REBUILD=1; shift ;;
        -h|--help) sed -n '2,9p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
done

step() { printf '==> %s\n' "$1"; }
ok()   { printf '    ok  %s\n' "$1"; }
note() { printf '    %s\n' "$1"; }
fail() { printf 'FAILED: %s\n' "$1" >&2; exit 1; }

port_free() {
    # Free means: nothing accepts connections on it, on loopback or any other address.
    ! (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null
}
find_port() {  # find_port <preferred> [avoid]
    local p="$1" avoid="${2:-0}" n=0
    while [ "$n" -lt 40 ]; do
        if [ "$p" != "$avoid" ] && port_free "$p"; then echo "$p"; return 0; fi
        p=$((p + 1)); n=$((n + 1))
    done
    fail "no free port from $1 to $(($1 + 39))"
}
json_field() { python3 -c 'import json,sys; print(json.load(sys.stdin)'"$1"')' ; }

step "Checking prerequisites"
command -v docker >/dev/null || fail "Docker is not installed."
docker info >/dev/null 2>&1 || fail "The Docker daemon is not running."
command -v node >/dev/null || fail "Node.js 20 or newer is required."
[ "$(node -p 'process.versions.node.split(".")[0]')" -ge 20 ] || fail "Node.js 20 or newer is required."
command -v curl >/dev/null || fail "curl is required."
command -v python3 >/dev/null || fail "python3 is required (to read JSON)."
ok "docker, node $(node --version)"

# Stop only what this script started earlier.
mkdir -p "$RUN_DIR"
if [ -f "$STATE" ]; then
    # shellcheck disable=SC1090
    . "$STATE"
    if [ -n "${GATEWAY_PID:-}" ] && ps -p "$GATEWAY_PID" -o args= 2>/dev/null | grep -q "$REPO/scripts/gateway.mjs"; then
        note "stopping the gateway this script started earlier (pid $GATEWAY_PID)"
        kill "$GATEWAY_PID" 2>/dev/null || true
    fi
fi
if [ -n "$(docker ps -a --filter "name=^/${CONTAINER}\$" --format '{{.ID}}')" ]; then
    [ -n "$(docker ps -a --filter "name=^/${CONTAINER}\$" --filter "label=$LABEL" --format '{{.ID}}')" ] \
        || fail "a container named $CONTAINER exists but was not started by VerdictKit; it was left untouched."
    note "replacing the VerdictKit backend container from the previous run"
    docker rm -f "$CONTAINER" >/dev/null
fi

step "Choosing ports (nothing that is already running is touched)"
API="$(find_port "$API_PORT")"
GATEWAY="$(find_port "$GATEWAY_PORT" "$API")"
[ "$API" = "$API_PORT" ] || note "port $API_PORT is in use; the backend will use $API"
[ "$GATEWAY" = "$GATEWAY_PORT" ] || note "port $GATEWAY_PORT is in use; the entry URL will use $GATEWAY"
ok "backend 127.0.0.1:$API, entry 127.0.0.1:$GATEWAY"

step "Docker image $IMAGE"
if [ "$REBUILD" = 1 ] || ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    note "building the image (first build takes a few minutes)"
    docker build -t "$IMAGE" "$REPO" >"$RUN_DIR/docker-build.log" 2>&1 || { tail -25 "$RUN_DIR/docker-build.log"; fail "docker build failed."; }
fi
ok "image ready"

step "Starting the backend (enforced isolation, judge mode, demonstration signer)"
docker run -d --name "$CONTAINER" --label "$LABEL" --label com.verdictkit.role=demo-backend \
    -p "127.0.0.1:${API}:8000" "$IMAGE" demo >/dev/null || fail "docker run failed."
HEALTH=""
for _ in $(seq 1 110); do
    HEALTH="$(curl -fsS --max-time 4 "http://127.0.0.1:${API}/api/v1/health" 2>/dev/null || true)"
    [ -n "$HEALTH" ] && break
    sleep 0.8
done
if [ -z "$HEALTH" ]; then docker logs --tail 40 "$CONTAINER" || true; docker rm -f "$CONTAINER" >/dev/null; fail "the backend did not become healthy within 90 seconds (container removed)."; fi
[ "$(echo "$HEALTH" | json_field "['contractVersion']")" = "$CONTRACT" ] || fail "unexpected contract version."
ISO="$(echo "$HEALTH" | json_field "['isolationMode']")"
JUDGE="$(echo "$HEALTH" | json_field "['judgeMode']")"
if [ "$ISO" != "ENFORCED" ] || [ "$JUDGE" != "True" ]; then docker rm -f "$CONTAINER" >/dev/null; fail "isolation is $ISO and judge mode is $JUDGE; refusing to continue (container removed)."; fi
ok "health ok: contract $CONTRACT, isolation $ISO, judge mode on"
LAB="$(curl -fsS --max-time 5 "http://127.0.0.1:${API}/api/v1/demo/status" 2>/dev/null || true)"
KEY="$(echo "${LAB:-{\}}" | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("signer") or {}).get("keyId",""))')"
[ -n "$KEY" ] || fail "the demonstration signer is not active on the backend."
ok "demonstration signer active, public key id ${KEY:0:16}... (private key stays in the container)"

step "Preparing the web UIs"
if [ "$REBUILD" = 1 ] || [ ! -f "$REPO/ui/hub/dist/index.html" ] || [ ! -f "$REPO/apps/quote-autopsy/web/dist/index.html" ] || [ ! -f "$REPO/apps/reel-autopsy/web/dist/index.html" ]; then
    (cd "$REPO" && { [ -d node_modules ] || npm ci --no-audit --no-fund >"$RUN_DIR/npm-ci.log" 2>&1; } && npm run build:portal >"$RUN_DIR/ui-build.log" 2>&1) \
        || { tail -25 "$RUN_DIR/ui-build.log" 2>/dev/null || true; fail "the UI build failed."; }
fi
ok "UIs built"

step "Starting the local gateway"
rm -f "$RUN_DIR/gateway.log"
nohup node "$REPO/scripts/gateway.mjs" --port "$GATEWAY" --api-port "$API" --image "$IMAGE" --log "$RUN_DIR/gateway.log" </dev/null >/dev/null 2>&1 &
GATEWAY_PID=$!
printf 'GATEWAY_PID=%s\nGATEWAY_PORT=%s\nAPI_PORT=%s\n' "$GATEWAY_PID" "$GATEWAY" "$API" >"$STATE"
for _ in $(seq 1 40); do curl -fsS --max-time 3 "http://127.0.0.1:${GATEWAY}/__gateway/health" >/dev/null 2>&1 && break; sleep 0.25; done
curl -fsS --max-time 5 "http://127.0.0.1:${GATEWAY}/api/v1/health" | grep -q "$CONTRACT" || { cat "$RUN_DIR/gateway.log" 2>/dev/null || true; fail "the gateway does not reach the backend."; }
ok "gateway up, backend reachable through it (pid $GATEWAY_PID)"

ENTRY="http://127.0.0.1:${GATEWAY}/"
cat <<EOF

  VerdictKit is running.

  Open this URL:   ${ENTRY}

  What to try
    Guided demo, contradicted worksheet   ${ENTRY}quote/?demo=padded
    Guided demo, claim above the bound    ${ENTRY}reel/?demo=fx_reel_impossible_sma
    Signed bundle, tampered scenario      ${ENTRY}verify?auto=1&sample=lease-consistent&scenario=tampered-bundle

  Status
    backend   127.0.0.1:${API}  (container ${CONTAINER}, image ${IMAGE})
    isolation ${ISO}, judge mode on, contract ${CONTRACT}
    signer    disposable demonstration key ${KEY:0:16}... (new at every start)
    logs      ${RUN_DIR}  |  docker logs ${CONTAINER}

  Stop everything this script started:  scripts/stop-verdictkit.sh
  Everything listens on 127.0.0.1 only. This is a local demonstration, not a public service.

EOF
