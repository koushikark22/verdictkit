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
#   gate-startup
#       Verify judge-mode startup reports ENFORCED with a live examiner.
#
#   gate-http
#       Judge-mode HTTP lifecycle (intake -> run -> outcome -> bundle -> replay)
#       through the authenticated socket examiner; scripts/gate_http.py. Also samples /proc
#       for the vault key (scripts/gate_argv_scan.py).
#
#   gate-sign [claim.json]
#       Signed bundles under enforced isolation, verified offline by a different OS user;
#       unknown/revoked signers and tampered bundles are rejected (scripts/gate_sign.py).
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
REPLAY_DIR="${VK_REPLAY_DIR:-/var/lib/vk/replay}"
WORK_DIR="${VK_WORK_DIR:-/var/lib/vk/work}"
SOCKET_PATH="${VK_EXAMINER_SOCKET:-/run/vk/examiner.sock}"
KEY_DIR="${VK_KEY_DIR:-/dev/shm/vk-keys}"
APP_DIR="/app"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

setup_vault() {
    # (Re-)enforce ownership and permissions every time the entrypoint runs.
    install -d -m 700 -o vk-custodian -g vk-custodian "$VAULT_DIR"
    install -d -m 750 -o vk-custodian -g vk-examiner  "$EVIDENCE_DIR"
    # Uploaded-bundle evidence lives here, one namespace per replay, never in EVIDENCE_DIR.
    install -d -m 750 -o vk-custodian -g vk-examiner  "$REPLAY_DIR"
    install -d -m 755 -o root          -g root         "$WORK_DIR"
    # Socket directory writable by vk-examiner only.
    install -d -m 2750 -o vk-examiner -g vk-ipc "$(dirname "$SOCKET_PATH")"
}

# ---------------------------------------------------------------------------
# vault key hand-off (design DD8-2): the key is never a process argument.
#
# It is written with shell builtins and redirections only, to a custodian-owned mode-0400 file
# on tmpfs. The custodian reads that file once and removes it. Only the file's PATH is passed
# on (VK_VAULT_KEY_FILE). No variable in this script holds a generated key.
# ---------------------------------------------------------------------------

prepare_key_dir() {
    # KEY_DIR must be container-private tmpfs. Do not run with --ipc=host: that makes /dev/shm the
    # host's. Point VK_KEY_DIR at another container-private tmpfs if /dev/shm is shared.
    install -d -m 700 -o vk-custodian -g vk-custodian "$KEY_DIR"
    # A key file the custodian never consumed (early exit, crash) does not outlive this script.
    trap 'rm -f "$KEY_DIR/vault.key"' EXIT
    case "$(stat -f -c %T "$KEY_DIR")" in
        tmpfs|ramfs) ;;
        *) echo "[keys] ${KEY_DIR} is not on tmpfs; refusing to place key material there" >&2
           return 1 ;;
    esac
}

seal_key_file() {
    # Ownership and mode are fixed after the (root-only, umask 077) write.
    chown vk-custodian:vk-custodian "$1"
    chmod 0400 "$1"
    VK_VAULT_KEY_FILE="$1"
    export VK_VAULT_KEY_FILE
}

provision_random_vault_key() {
    local key_file="$KEY_DIR/vault.key"
    rm -f "$key_file"
    ( umask 077; python3 -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())' > "$key_file" )
    seal_key_file "$key_file"
}

provision_vault_key_from_env() {
    # serve: the operator supplies VK_VAULT_KEY in the container environment.
    local key_file="$KEY_DIR/vault.key"
    rm -f "$key_file"
    ( umask 077; printf '%s' "$VK_VAULT_KEY" > "$key_file" )   # printf is a builtin: no argv
    seal_key_file "$key_file"
    unset VK_VAULT_KEY
}

# Run a command as vk-custodian with a curated environment.
# The custodian receives the PATH of its vault key file (VK_VAULT_KEY_FILE), never the key.
# VK_ISOLATION is set to enforced.
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
            VK_REPLAY_DIR="$REPLAY_DIR" \
            VK_EXAMINER_SOCKET="$SOCKET_PATH" \
            ${VK_VAULT_KEY_FILE:+VK_VAULT_KEY_FILE="$VK_VAULT_KEY_FILE"} \
            ${VK_SIGNING_KEY_FILE:+VK_SIGNING_KEY_FILE="$VK_SIGNING_KEY_FILE"} \
            ${VK_TRUST_STORE_FILE:+VK_TRUST_STORE_FILE="$VK_TRUST_STORE_FILE"} \
            ${VK_TRUST_STORE_SHA256:+VK_TRUST_STORE_SHA256="$VK_TRUST_STORE_SHA256"} \
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
            VK_REPLAY_DIR="$REPLAY_DIR" \
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
# argv scan (gate evidence for DD8-2): see scripts/gate_argv_scan.py
# ---------------------------------------------------------------------------

SCAN_DIR=""
SCAN_PID=""

start_argv_scan() {
    SCAN_DIR="$(mktemp -d)"
    chmod 700 "$SCAN_DIR"
    python3 "$APP_DIR/scripts/gate_argv_scan.py" "$VK_VAULT_KEY_FILE" \
        "$SCAN_DIR/result" "$SCAN_DIR/stop" "$SCAN_DIR/ready" &
    SCAN_PID=$!
    local waited=0
    while [ ! -e "$SCAN_DIR/ready" ] && [ "$waited" -lt 100 ]; do
        sleep 0.05
        waited=$((waited + 1))
    done
    [ -e "$SCAN_DIR/ready" ] || { echo "[argv-scan] scanner did not start" >&2; return 1; }
}

finish_argv_scan() {
    : > "$SCAN_DIR/stop"
    local rc=0
    wait "$SCAN_PID" || rc=$?
    cat "$SCAN_DIR/result" 2>/dev/null || true
    rm -rf "$SCAN_DIR"
    return "$rc"
}

# check <expected-exit> <expected-text> <description> <command...>
check() {
    local want_rc="$1" want_text="$2" desc="$3"
    shift 3
    local out rc=0
    out="$("$@" 2>&1)" || rc=$?
    if [ "$rc" -ne "$want_rc" ] || ! printf '%s\n' "$out" | grep -Fq -- "$want_text"; then
        printf '%s\n' "$out" >&2
        echo "FAIL ${desc} (exit ${rc}; wanted exit ${want_rc} and text '${want_text}')" >&2
        return 1
    fi
    echo "PASS ${desc}"
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

    # Fresh vault key for this run, handed over as a tmpfs key file (never as an argument).
    prepare_key_dir
    provision_random_vault_key

    echo "[gate-case] Running pipeline as vk-custodian..."
    # Use the installed verdictkit binary from the venv; cd to /app for uv project root.
    # VK_EXAMINER_SOCKET is already set in as_custodian's environment, so the
    # pipeline will use SocketExaminer (enforced isolation) rather than InProcessExaminer.
    as_custodian \
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
# subcommand: gate-http
#   Judge-mode HTTP lifecycle through the authenticated socket examiner.
# ---------------------------------------------------------------------------
cmd_gate_http() {
    setup_vault
    mkdir -p /tmp/vk-custodian /tmp/vk-examiner
    chown vk-custodian /tmp/vk-custodian
    chown vk-examiner /tmp/vk-examiner
    local draft_dir=/var/lib/vk/drafts
    install -d -m 700 -o vk-custodian -g vk-custodian "$draft_dir"

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
        kill "$examiner_pid" 2>/dev/null || true
        return 1
    fi
    chgrp vk-ipc "$SOCKET_PATH"
    chmod 660 "$SOCKET_PATH"

    prepare_key_dir
    provision_random_vault_key
    local VK_JUDGE_MODE=1
    local rc=0
    # While the HTTP lifecycle runs, sample /proc: the key must appear in no process argument
    # and in no environment outside the custodian's (a canary proves the scan can see argv).
    start_argv_scan
    as_custodian env VK_DRAFT_DIR="$draft_dir" \
        bash -c "cd /app && /app/.venv/bin/python scripts/gate_http.py" || rc=$?
    finish_argv_scan || rc=$?
    kill "$examiner_pid" 2>/dev/null || true
    wait "$examiner_pid" 2>/dev/null || true
    return "$rc"
}

# ---------------------------------------------------------------------------
# subcommand: gate-sign [claim.json]
#   Signed bundles end to end under enforced isolation, verified offline by another OS user.
#   Uses throwaway keys generated inside this run. Nothing here is a production key.
# ---------------------------------------------------------------------------

cmd_gate_sign() {
    local claim_json="${1:-$APP_DIR/examples/stub_claimtype/claim.json}"
    local sign_dir=/var/lib/vk/signing trust_dir=/var/lib/vk/trust out_dir=/var/lib/vk/gate-sign
    local vk=/app/.venv/bin/verdictkit
    local failed=0 out

    setup_vault
    mkdir -p /tmp/vk-custodian /tmp/vk-examiner
    chown vk-custodian /tmp/vk-custodian
    chown vk-examiner  /tmp/vk-examiner
    install -d -m 700 -o vk-custodian -g vk-custodian "$sign_dir"
    install -d -m 755 -o vk-custodian -g vk-custodian "$trust_dir" "$out_dir"

    echo "[gate-sign] Generating a throwaway signing key and trust stores as vk-custodian..."
    as_custodian bash -c "cd /app && /app/.venv/bin/python scripts/gate_sign.py keygen '$sign_dir' '$trust_dir'"

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
        kill "$examiner_pid" 2>/dev/null || true
        return 1
    fi
    chgrp vk-ipc "$SOCKET_PATH"
    chmod 660 "$SOCKET_PATH"

    # vk-examiner is in the socket's group, so it can connect. A VALID task from it must still be
    # refused: only the custodian's uid is served (SO_PEERCRED). The custodian is the positive control.
    check 0 "peer-rejected" "the worker refuses a valid task from a client that is not the custodian" \
        as_examiner /app/.venv/bin/python /app/scripts/gate_peer_probe.py "$claim_json" || failed=1
    check 0 "served" "the same task from the custodian is served (positive control)" \
        as_custodian /app/.venv/bin/python /app/scripts/gate_peer_probe.py "$claim_json" || failed=1

    echo "[gate-sign] Signed run through the authenticated examiner (vk-custodian)..."
    prepare_key_dir
    provision_random_vault_key
    out="$(as_custodian env VK_SIGNING_KEY_FILE="$sign_dir/signing.pem" \
        bash -c "cd /app && $vk run '$claim_json' --out '$out_dir/signed.vkb'" 2>&1)" \
        || { printf '%s\n' "$out" >&2; kill "$examiner_pid" 2>/dev/null || true; return 1; }
    printf '%s\n' "$out"
    printf '%s\n' "$out" | grep -Fq "isolation:     ENFORCED" \
        || { echo "FAIL signed run was not ENFORCED" >&2; failed=1; }
    printf '%s\n' "$out" | grep -Fq "signed:        yes (ed25519" \
        || { echo "FAIL the run did not sign" >&2; failed=1; }

    echo "[gate-sign] Historical (unsigned) run..."
    provision_random_vault_key
    out="$(as_custodian bash -c "cd /app && $vk run '$claim_json' --out '$out_dir/unsigned.vkb'" 2>&1)" \
        || { printf '%s\n' "$out" >&2; kill "$examiner_pid" 2>/dev/null || true; return 1; }
    printf '%s\n' "$out" | grep -Fq "signed:        no" || { echo "FAIL unsigned run reported signing" >&2; failed=1; }

    for kind in member manifest signature; do
        as_custodian bash -c "cd /app && /app/.venv/bin/python scripts/gate_sign.py tamper $kind '$out_dir/signed.vkb' '$out_dir/t-$kind.vkb'"
    done

    echo "[gate-sign] Offline verification by vk-examiner (a different OS user, no signing key)..."
    check 0 "signature:         VALID" "signed bundle: signature VALID" \
        as_examiner "$vk" verify "$out_dir/signed.vkb" --trust-store "$trust_dir/trust-good.json" || failed=1
    check 0 "authenticity:      ESTABLISHED" "valid signature + trusted signer + verified integrity => ESTABLISHED" \
        as_examiner "$vk" verify "$out_dir/signed.vkb" --trust-store "$trust_dir/trust-good.json" || failed=1
    check 0 "reproducibility:   REPRODUCED" "signed bundle replays offline (REPRODUCED)" \
        as_examiner "$vk" replay "$out_dir/signed.vkb" --trust-store "$trust_dir/trust-good.json" || failed=1
    check 1 "signer trust:      UNTRUSTED_SIGNER" "unknown signer: valid signature, not trusted" \
        as_examiner "$vk" verify "$out_dir/signed.vkb" --trust-store "$trust_dir/trust-other.json" || failed=1
    check 1 "KEY_REVOKED" "revoked signer is not trusted" \
        as_examiner "$vk" verify "$out_dir/signed.vkb" --trust-store "$trust_dir/trust-revoked.json" || failed=1
    check 1 "signer trust:      NOT_EVALUATED" "no trust store: authenticity not established" \
        as_examiner "$vk" verify "$out_dir/signed.vkb" || failed=1
    check 1 "integrity:         FAILED" "tampered member is rejected" \
        as_examiner "$vk" verify "$out_dir/t-member.vkb" --trust-store "$trust_dir/trust-good.json" || failed=1
    check 1 "signature:         INVALID" "tampered manifest is rejected" \
        as_examiner "$vk" verify "$out_dir/t-manifest.vkb" --trust-store "$trust_dir/trust-good.json" || failed=1
    check 1 "SIGNATURE_MISMATCH" "tampered signature is rejected" \
        as_examiner "$vk" verify "$out_dir/t-signature.vkb" --trust-store "$trust_dir/trust-good.json" || failed=1
    check 0 "signature:         UNSIGNED" "historical unsigned bundle still replays" \
        as_examiner "$vk" replay "$out_dir/unsigned.vkb" || failed=1
    check 1 "Permission denied" "the examiner cannot read the signing key" \
        as_examiner cat "$sign_dir/signing.pem" || failed=1
    check 1 "must not be present in examiner environment" "the worker refuses a signing key in its environment" \
        as_examiner env VK_SIGNING_KEY_FILE=/nonexistent python -I -m verdictkit.examiner.worker || failed=1

    kill "$examiner_pid" 2>/dev/null || true
    wait "$examiner_pid" 2>/dev/null || true
    if [ "$failed" -ne 0 ]; then
        echo "GATE-SIGN FAILED" >&2
        return 1
    fi
    echo "GATE-SIGN PASSED"
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
    : "${VK_VAULT_KEY:?VK_VAULT_KEY must be set for serve}"
    # Hand the key to the custodian as a tmpfs file and drop it from this shell's environment
    # before any child starts, so no child (examiner included) can inherit it.
    prepare_key_dir
    provision_vault_key_from_env

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

    # Encrypted case custody (drafts, freezes, runs, bundles): custodian-only, 0700.
    local draft_dir="${VK_DRAFT_DIR:-/var/lib/vk/drafts}"
    install -d -m 700 -o vk-custodian -g vk-custodian "$draft_dir"

    echo "[serve] Starting API server as vk-custodian..."
    as_custodian \
        env VK_DRAFT_DIR="$draft_dir" \
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
    gate-http)
        shift
        cmd_gate_http "$@"
        ;;
    gate-sign)
        shift
        cmd_gate_sign "$@"
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
        echo "Usage: entrypoint.sh {gate-isolation|gate-case|gate-startup|gate-http|gate-sign|serve|verdictkit ...}" >&2
        exit 1
        ;;
    *)
        # Generic passthrough for any other command (e.g. bash, pytest).
        exec "$@"
        ;;
esac
