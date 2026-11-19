---
inclusion: always
---
# Tech stack

- Python 3.12, `uv` workspace and lockfile (commit `uv.lock`).
- FastAPI for APIs; `cryptography` (AES-GCM) for the vault; Hypothesis + pytest for tests.
- React + Vite + TypeScript for both UIs, sharing `ui-kit/`.
- One Docker image (Linux); two OS users `vk-custodian` and `vk-examiner`.
- MCP server: `python -m verdictkit.mcp_server` (stdio).

Commands:
- Contract tests: `uv run pytest tests/contract -q`
- Isolation tests (container only): `uv run pytest -m isolation`
- LLM fence: `uv run pytest tests/contract/test_llm_fence.py -q`

Do not add dependencies to `core` evaluator paths beyond the standard library and the
packages above without an explicit design change.
