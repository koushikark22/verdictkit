#!/usr/bin/env bash
# Nov 22 gate. Run from the repo root on Linux, WSL2 or macOS with Docker.
# Produces gate/transcript.txt plus JUnit XML; prints true pass/fail/skip counts.
# Every command and its full output is recorded; nothing is filtered.
set -uo pipefail
OUT=gate
mkdir -p "$OUT"
LOG="$OUT/transcript.txt"
: > "$LOG"
RC=0
step() {
  printf '\n$ %s\n' "$*" | tee -a "$LOG"
  "$@" 2>&1 | tee -a "$LOG"
  local rc=${PIPESTATUS[0]}
  printf '[exit %s]\n' "$rc" | tee -a "$LOG"
  [ "$rc" -eq 0 ] || RC=1
}
export HYPOTHESIS_PROFILE=ci

# 0. Prerequisites. The gate is NOT executable until all of these exist (Kiro core
#    tasks 1.3 and 15.1). Missing items are reported and the script exits 2 without
#    running anything, so a partial run can never be reported as a gate result.
missing=()
[ -f uv.lock ] || missing+=("uv.lock (core task 1.3: uv lock, committed)")
[ -f Dockerfile ] || missing+=("Dockerfile (core task 15.1)")
[ -f core/src/verdictkit/examiner/worker.py ] && grep -q NotImplementedError core/src/verdictkit/examiner/worker.py \
  && missing+=("examiner worker implementation (core task 9.2)")
grep -q NotImplementedError core/src/verdictkit/cli.py && missing+=("verdictkit CLI implementation (core task 11.4)")
command -v uv >/dev/null || missing+=("uv on PATH")
command -v docker >/dev/null && docker info >/dev/null 2>&1 || missing+=("running Docker daemon")
git rev-parse HEAD >/dev/null 2>&1 || missing+=("git repository with at least one commit")
if [ ${#missing[@]} -gt 0 ]; then
  printf 'GATE NOT EXECUTABLE — missing prerequisites:\n' | tee -a "$LOG"
  printf '  - %s\n' "${missing[@]}" | tee -a "$LOG"
  exit 2
fi

step date -u +%Y-%m-%dT%H:%M:%SZ
step git rev-parse HEAD
step git status --porcelain
step uv --version
step docker --version
step uv sync --frozen --all-packages --all-extras --group dev

# 1. Core contract tests (gate scope) — must be fully green.
step uv run --no-sync pytest tests/contract -m "not isolation" -q -rfEs \
  --ignore=tests/contract/test_reel_contract.py \
  --ignore=tests/contract/test_quote_contract.py \
  --ignore=tests/contract/test_reel_intake_presentation.py \
  --junitxml="$OUT/core_contract.xml"

# 2. App contract tests — reported, not gating on Nov 22 (apps are scheduled after).
uv run --no-sync pytest tests/contract/test_reel_contract.py tests/contract/test_quote_contract.py \
  tests/contract/test_reel_intake_presentation.py -q --junitxml="$OUT/app_contract.xml" \
  > "$OUT/app_contract.txt" 2>&1 || true
printf '\n(app contract tests: see %s; not gating on Nov 22)\n' "$OUT/app_contract.txt" | tee -a "$LOG"

# 3. Container with enforced OS-user isolation.
step docker build -t verdictkit:gate .
step docker image inspect --format '{{.Id}}' verdictkit:gate
step docker run --rm --network none -v "$PWD/$OUT:/out" verdictkit:gate gate-isolation /out/isolation.xml

# 4. Full path in the container (enforced isolation, no network), then offline replay.
step docker run --rm --network none -v "$PWD/$OUT:/out" \
  -v "$PWD/examples/stub_claimtype:/in:ro" verdictkit:gate gate-case /in/claim.json /out/stub.vkb
step docker run --rm --network none -v "$PWD/$OUT:/out" verdictkit:gate verdictkit replay /out/stub.vkb
# Outside the container: a different environment, so REPRODUCED_ACROSS_ENV is the expected status.
step uv run --no-sync verdictkit replay "$OUT/stub.vkb"
step sha256sum "$OUT/stub.vkb"

# 5. Judge mode must refuse to start without enforced isolation.
step bash -c '
    output=$(VK_JUDGE_MODE=1 timeout 20 uv run --no-sync python -m verdictkit.api --check-startup 2>&1)
    rc=$?
    printf "%s\n" "$output"
    [ "$rc" -eq 3 ] &&
    printf "%s\n" "$output" | grep -Fxq "VK_STARTUP_ERROR=ISOLATION_NOT_ENFORCED"
'
step bash -c '
    output=$(VK_JUDGE_MODE=banana timeout 20 uv run --no-sync python -m verdictkit.api --check-startup 2>&1)
    rc=$?
    printf "%s\n" "$output"
    [ "$rc" -eq 2 ] &&
    printf "%s\n" "$output" | grep -Fxq "VK_STARTUP_ERROR=INVALID_JUDGE_MODE"
'

# 6. True counts.
step uv run --no-sync python scripts/junit_counts.py "$OUT/core_contract.xml" "$OUT/isolation.xml" "$OUT/app_contract.xml"

printf '\nGATE %s\n' "$([ $RC -eq 0 ] && echo PASSED || echo FAILED)" | tee -a "$LOG"
exit $RC
