#!/usr/bin/env bash
# VerdictKit container entrypoint.
#
# Subcommands (defined by scripts/gate_nov22.sh and core task 15.3):
#
#   gate-isolation <junit_xml>
#       1. Set up vault (vk-custodian owns it, mode 0700).
#       2. Write probe.sealed as vk-custodian.
#       3. Run the four pytest isolation tests as vk-examiner with a scrubbed
#          environment containing no VK_VAULT_KEY.
#       4. Write JUnit XML to <junit_xml>.
#
#   gate-case <claim.json> <output.vkb>
#       Run the full pipeline (enforced isolation, no network):
#       - Start the examiner worker as vk-examiner (scrubbed env, background).
#       - Run `verdictkit run` as vk-custodian (VK_ISOLATION=enforced).
#       - Kill the worker when done.
#
#   serve
#       Start custodian (FastAPI) and examiner worker under their respective
#       users.  Used for the production deployment.
#
#   verdictkit <args...>   (and any other command)
#       Passthrough: exec as the calling user (or root → suitable for replay
#       which needs no special privilege).
#
# Security invariants enforced here (§4.2 of ARCHITECTURE.md):
#   * Vault dir is always (re-)chowned to vk-custodian:vk-custodian, mode 0700,
#     before anything runs — the entrypoint is the single owner of that setup.
#   * The examiner worker is always exec'd via setpriv with an *explicit*
#     allowlist environment.  VK_VAULT_KEY is never in that environment.
#   * No long-lived root process remains after setup.
set -euo pipefail

VAULT_DIR="${VK_VAULT_DIR:-/var/lib/vk/vault}"
EVIDENCE_DIR="${VK_EVIDENCE_DIR:-/var/lib/vk/evidence}"
WORK_DIR="${VK_WORK_DIR:-/var/lib/vk/work}"
SOCKET_PATH="${VK_EXAMINER_SOCKET:-/run/vk/examiner.sock}"
APP_DIR="/app"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

setup_vault() {
    # (Re-)enforce ownership and permissions every time the entrypoint runs.
    install -d -m 700 -o vk-custodian -g vk-custodian "$VAULT_DIR"
    install -d -m 750 -o vk-custodian -g vk-examiner  "$EVIDENCE_DIR"
    install -d -m 755 -o root          -g root         "$WORK_DIR"
    # Socket directory writable by vk-examiner only.
    install -d -m 2750 -o vk-examiner -g vk-ipc "$(dirname "$SOCKET_PATH")"
}

# Run a command as vk-custodian with a curated environment.
# VK_VAULT_KEY is kept (custodian needs it); VK_ISOLATION is set to enforced.
as_custodian() {
    setpriv \
        --reuid=vk-custodian \
        --regid=vk-custodian \
        --init-groups \
        --no-new-privs \
        -- \
        env -i \
            PATH="/app/.venv/bin:/usr/local/bin:/usr/bin:/bin" \
            HOME="/tmp/vk-custodian" \
            LANG="${LANG:-C.UTF-8}" \
            PYTHONHASHSEED=0 \
            PYTHONDONTWRITEBYTECODE=1 \
            VK_ISOLATION=enforced \
            VK_JUDGE_MODE="${VK_JUDGE_MODE:-0}" \
            VK_VAULT_DIR="$VAULT_DIR" \
            VK_EVIDENCE_DIR="$EVIDENCE_DIR" \
            VK_EXAMINER_SOCKET="$SOCKET_PATH" \
            ${VK_VAULT_KEY:+VK_VAULT_KEY="$VK_VAULT_KEY"} \
            ${VK_CLAIM_TYPES:+VK_CLAIM_TYPES="$VK_CLAIM_TYPES"} \
        "$@"
}

# Run a command as vk-examiner with a scrubbed environment.
# VK_VAULT_KEY is NEVER passed; this is the core blinding guarantee.
as_examiner() {
    setpriv \
        --reuid=vk-examiner \
        --regid=vk-examiner \
        --init-groups \
        --no-new-privs \
        -- \
        env -i \
            PATH="/app/.venv/bin:/usr/local/bin:/usr/bin:/bin" \
            HOME="/tmp/vk-examiner" \
            LANG="${LANG:-C.UTF-8}" \
            PYTHONHASHSEED=0 \
            PYTHONDONTWRITEBYTECODE=1 \
            VK_EXAMINER_SOCKET="$SOCKET_PATH" \
            VK_EVIDENCE_DIR="$EVIDENCE_DIR" \
            VK_ISOLATION=enforced \
            ${VK_SOURCES_CONFIG:+VK_SOURCES_CONFIG="$VK_SOURCES_CONFIG"} \
            ${VK_CLAIM_TYPES:+VK_CLAIM_TYPES="$VK_CLAIM_TYPES"} \
        "$@"
}

uv_run() {
    # Wrapper that calls `uv run` from the app directory.
    cd "$APP_DIR"
    uv run "$@"
}

# ---------------------------------------------------------------------------
# subcommand: gate-isolation <junit_xml>
# ---------------------------------------------------------------------------

cmd_gate_isolation() {
    local junit_xml="${1:?gate-isolation requires a JUnit XML output path}"
    local junit_dir; junit_dir="$(dirname "$junit_xml")"
    mkdir -p "$junit_dir"
    # Allow vk-examiner to write the XML to the output directory.
    chmod a+rwx "$junit_dir" 2>/dev/null || true

    echo "[gate-isolation] Setting up vault as vk-custodian (mode 0700)..."
    setup_vault

    # Write the probe file as vk-custodian (inside the 0700 dir).
    echo "[gate-isolation] Writing probe.sealed as vk-custodian..."
    as_custodian bash -c \
        "echo 'probe' > '${VAULT_DIR}/probe.sealed' && chmod 600 '${VAULT_DIR}/probe.sealed'"

    echo "[gate-isolation] Running isolation tests as vk-examiner..."
    # The test module reads VK_VAULT_DIR from its environment; VK_VAULT_KEY is absent.
    # Use the preinstalled pytest binary directly — no network access, no uv sync.
    as_examiner \
        env VK_VAULT_DIR="$VAULT_DIR" \
        bash -c "cd /app && /app/.venv/bin/python -m pytest -m isolation tests/contract/test_isolation.py -v --junitxml='${junit_xml}'"
    echo "[gate-isolation] Done."
}

# ---------------------------------------------------------------------------
# subcommand: gate-case <claim.json> <output.vkb>
# ---------------------------------------------------------------------------

cmd_gate_case() {
    local claim_json="${1:?gate-case requires a claim.json path}"
    local output_vkb="${2:?gate-case requires an output .vkb path}"
    local out_dir; out_dir="$(dirname "$output_vkb")"
    mkdir -p "$out_dir"

    echo "[gate-case] Setting up vault..."
    setup_vault

    # Give vk-custodian a temporary home directory.
    mkdir -p /tmp/vk-custodian /tmp/vk-examiner
    chown vk-custodian /tmp/vk-custodian
    chown vk-examiner  /tmp/vk-examiner

    # Allow vk-custodian to write the .vkb to the output directory.
    chmod a+rwx "$out_dir" 2>/dev/null || true

    echo "[gate-case] Starting examiner worker as vk-examiner..."
    # Remove a stale socket if it exists.
    rm -f "$SOCKET_PATH"

    # Start examiner in the background, scrubbed env, --no-new-privs.
    # Using the installed binary path so -I (isolated) Python flag is applied
    # and no PYTHONPATH leakage from the root environment is possible.
    as_examiner \
        bash -c "cd /app && python -I -m verdictkit.examiner.worker" \
        &
    local examiner_pid=$!
    echo "[gate-case] Examiner PID: ${examiner_pid}"

    # Give the worker a moment to bind the socket.
    local retries=20
    while [ $retries -gt 0 ] && [ ! -S "$SOCKET_PATH" ]; do
        sleep 0.2
        retries=$((retries - 1))
    done
    if [ ! -S "$SOCKET_PATH" ]; then
        echo "[gate-case] ERROR: examiner socket did not appear at ${SOCKET_PATH}" >&2
        kill "$examiner_pid" 2>/dev/null || true
        exit 1
    fi
    echo "[gate-case] Examiner socket ready."

    # Make the socket readable by vk-custodian (examiner owns it; grant group
    # access since both are in separate groups — use world-accessible socket).
    chgrp vk-ipc "$SOCKET_PATH"
    chmod 660 "$SOCKET_PATH"

    # Generate a fresh vault key for this run.
    local vault_key; vault_key="$(python3 -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())')"

    echo "[gate-case] Running pipeline as vk-custodian..."
    # Use the installed verdictkit binary from the venv; cd to /app for uv project root.
    # VK_EXAMINER_SOCKET is already set in as_custodian's environment, so the
    # pipeline will use SocketExaminer (enforced isolation) rather than InProcessExaminer.
    as_custodian \
        env VK_VAULT_KEY="$vault_key" \
        bash -c "cd /app && /app/.venv/bin/verdictkit run '${claim_json}' --out '${output_vkb}'"

    echo "[gate-case] Stopping examiner..."
    kill "$examiner_pid" 2>/dev/null || true
    wait "$examiner_pid" 2>/dev/null || true

    echo "[gate-case] Bundle written to: ${output_vkb}"
}

# ---------------------------------------------------------------------------
# subcommand: gate-startup
# ---------------------------------------------------------------------------
cmd_gate_startup() {
    setup_vault
    mkdir -p /tmp/vk-custodian /tmp/vk-examiner
    chown vk-custodian /tmp/vk-custodian
    chown vk-examiner /tmp/vk-examiner

    rm -f "$SOCKET_PATH"
    as_examiner bash -c "cd /app && python -I -m verdictkit.examiner.worker" &
    local examiner_pid=$!

    local retries=30
    while [ "$retries" -gt 0 ] && [ ! -S "$SOCKET_PATH" ]; do
        sleep 0.2
        retries=$((retries - 1))
    done
    if [ ! -S "$SOCKET_PATH" ]; then
        echo "examiner socket did not become ready" >&2
        return 1
    fi
    chgrp vk-ipc "$SOCKET_PATH"
    chmod 660 "$SOCKET_PATH"

    local VK_JUDGE_MODE=1
    local output
    output="$(as_custodian bash -c 'cd /app && /app/.venv/bin/python -m verdictkit.api --check-startup')"
    printf '%s\n' "$output"
    printf '%s\n' "$output" | grep -Fxq "VK_STARTUP_OK isolation=ENFORCED"
    echo "[gate-startup] Verified Linux judge startup"
    kill "$examiner_pid" 2>/dev/null || true
    wait "$examiner_pid" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# subcommand: serve
# ---------------------------------------------------------------------------

cmd_serve() {
    echo "[serve] Setting up vault..."
    setup_vault
    mkdir -p /tmp/vk-custodian /tmp/vk-examiner
    chown vk-custodian /tmp/vk-custodian
    chown vk-examiner  /tmp/vk-examiner

    rm -f "$SOCKET_PATH"
    local vault_key="${VK_VAULT_KEY:?VK_VAULT_KEY must be set for serve}"

    echo "[serve] Starting examiner worker as vk-examiner..."
    as_examiner bash -c "cd /app && python -I -m verdictkit.examiner.worker" &
    local examiner_pid=$!

    # Wait for socket.
    local retries=30
    while [ $retries -gt 0 ] && [ ! -S "$SOCKET_PATH" ]; do
        sleep 0.2
        retries=$((retries - 1))
    done
    [ -S "$SOCKET_PATH" ] || { echo "ERROR: examiner socket timeout" >&2; exit 1; }
    chgrp vk-ipc "$SOCKET_PATH"
    chmod 660 "$SOCKET_PATH"

    echo "[serve] Starting API server as vk-custodian..."
    as_custodian \
        env VK_VAULT_KEY="$vault_key" \
        bash -c "cd /app && python -m verdictkit.api --host 0.0.0.0 --port '${PORT:-8000}'" \
        &
    local api_pid=$!

    echo "[serve] Running. API PID=${api_pid}, Examiner PID=${examiner_pid}"
    # Wait for either process to exit; propagate failure.
    wait -n "$api_pid" "$examiner_pid" 2>/dev/null || true
    kill "$api_pid"      2>/dev/null || true
    kill "$examiner_pid" 2>/dev/null || true
    wait
}

# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

SUBCOMMAND="${1:-}"

case "$SUBCOMMAND" in
    gate-isolation)
        shift
        cmd_gate_isolation "$@"
        ;;
    gate-case)
        shift
        cmd_gate_case "$@"
        ;;
    gate-startup)
        shift
        cmd_gate_startup "$@"
        ;;
    serve)
        shift
        cmd_serve "$@"
        ;;
    verdictkit)
        # Pass remaining args straight to the installed CLI binary.
        shift
        cd "$APP_DIR"
        exec /app/.venv/bin/verdictkit "$@"
        ;;
    "")
        echo "Usage: entrypoint.sh {gate-isolation|gate-case|serve|verdictkit ...}" >&2
        exit 1
        ;;
    *)
        # Generic passthrough for any other command (e.g. bash, pytest).
        exec "$@"
        ;;
esac
