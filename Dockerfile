# VerdictKit container — two OS users, enforced vault isolation.
# Core requirement 4; architecture doc §1, §4.
#
# Pinned by digest (core task 15.1): the tag documents the version, the digest
# fixes the exact multi-platform index. Update both together.
FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# ── System packages ──────────────────────────────────────────────────────────
# util-linux: setpriv (uid/capability drop without execve overhead)
# procps:     used by resource-limit tests
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        util-linux \
        procps \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── OS identities ────────────────────────────────────────────────────────────
# vk-custodian owns the vault, runs the FastAPI service and pipeline.
# vk-examiner  owns the socket, runs the evaluator, never reads the vault.
RUN useradd --system --no-create-home --shell /bin/false --uid 900 vk-custodian && \
    useradd --system --no-create-home --shell /bin/false --uid 901 vk-examiner
RUN groupadd --system --gid 902 vk-ipc && \
    usermod -aG vk-ipc vk-custodian && \
    usermod -aG vk-ipc vk-examiner

# ── uv ───────────────────────────────────────────────────────────────────────
# Install uv into /usr/local/bin so both users can call `uv run`.
COPY --from=ghcr.io/astral-sh/uv:0.5.4@sha256:5436c72d52c9c0d011010ce68f4c399702b3b0764adcf282fe0e546f20ebaef6 /uv /uvx /usr/local/bin/

# ── Source tree ──────────────────────────────────────────────────────────────
WORKDIR /app
COPY pyproject.toml ./
COPY core/           ./core/
COPY examples/       ./examples/
COPY apps/           ./apps/
COPY tests/          ./tests/
COPY api/            ./api/
COPY scripts/        ./scripts/

# If uv.lock exists (gate prerequisite 1.3) copy it in and use --frozen.
# If it is absent the build still succeeds, but gate_nov22.sh will reject it.
COPY uv.lock* ./

# ── Python environment ───────────────────────────────────────────────────────
# Install into a virtualenv at /app/.venv so both users share one copy.
# --frozen: fail the build if uv.lock is absent or stale (gate prereq 1.3).
# --all-extras: include api and mcp optional deps.
# --group dev: install pytest, hypothesis and other dev dependencies.
# No fallback: a failed sync means the image is not fit for the gate.
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --frozen --all-packages --all-extras --group dev
# Make the venv readable and executable by all users (read + execute; no write).
RUN chmod -R a+rX /app/.venv

# ── Vault directory ──────────────────────────────────────────────────────────
# Created here so it exists before the entrypoint runs; mode is 0700 so only
# vk-custodian (uid 900) can read or list it.  The examiner (uid 901) has no
# access at all — this is the OS-level enforcement that test_isolation verifies.
RUN install -d -m 700 -o vk-custodian -g vk-custodian /var/lib/vk/vault && \
    install -d -m 750 -o vk-custodian -g vk-examiner  /var/lib/vk/evidence && \
    install -d -m 755 -o root          -g root         /var/lib/vk/work

# ── Examiner socket directory ─────────────────────────────────────────────────
RUN install -d -m 755 -o vk-examiner -g vk-examiner /run/vk

# ── Entrypoint ───────────────────────────────────────────────────────────────
COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# No default USER: the entrypoint starts as root so it can setpriv into each
# user.  No long-lived root process remains after the initial setup.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
