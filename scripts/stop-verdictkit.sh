#!/usr/bin/env bash
# Stops what start-verdictkit.sh started, and nothing else.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE="$REPO/.verdictkit-run/state.vars"
CONTAINER="vk-batch2-backend"

if [ -f "$STATE" ]; then
    # shellcheck disable=SC1090
    . "$STATE"
    if [ -n "${GATEWAY_PID:-}" ] && ps -p "$GATEWAY_PID" -o args= 2>/dev/null | grep -q "$REPO/scripts/gateway.mjs"; then
        kill "$GATEWAY_PID" && echo "stopped gateway (pid $GATEWAY_PID)"
    else
        echo "no running VerdictKit gateway found (nothing stopped)"
    fi
fi
if command -v docker >/dev/null 2>&1; then
    if [ -n "$(docker ps -a --filter "name=^/${CONTAINER}\$" --filter 'label=com.verdictkit.managed=1' --format '{{.ID}}' 2>/dev/null)" ]; then
        docker rm -f "$CONTAINER" >/dev/null && echo "removed container $CONTAINER"
    else
        echo "no VerdictKit backend container found (nothing removed)"
    fi
fi
rm -f "$STATE"
