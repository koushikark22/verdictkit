# Demonstration verification lab (Batch 2)

An opt-in server extension that lets a browser show signed-bundle verification with real backend code. It is **not part of API contract 1.2.0** (`api/openapi.yaml` is unchanged) and its routes do not exist unless the operator enables it.

## What it is for

`docs/SIGNING.md` describes five separate results and a trust store the verifier configures. To *see* the difference between a trusted, an unknown and a revoked signer, you need the same bundle checked by verifiers with different trust stores, plus an unsigned and a tampered bundle. The lab provides exactly that and nothing else. It adds no verification logic: every result comes from the same `replay_bundle` and `authenticity_dict` code that `POST /replays` uses.

## Enabling it

Set `VK_DEMO_LAB_DIR` to a directory holding three **public** trust stores written by `scripts/demo_signer.py provision SIGN_DIR LAB_DIR`:

| File | Content | Serial |
|---|---|---|
| `trust-trusted.json` | the demonstration signer, `ACTIVE` | 1 |
| `trust-unknown.json` | one unrelated public key (its private half is discarded, never serialised) | 1 |
| `trust-revoked.json` | the demonstration signer, `REVOKED` | 2 |

`deploy/entrypoint.sh demo` does all of this inside the container, then starts the examiner and the API with `VK_SIGNING_KEY_FILE`, `VK_TRUST_STORE_FILE` (+ `VK_TRUST_STORE_SHA256` pin) and `VK_DEMO_LAB_DIR`. A configured but unusable lab stops the server start, like an unusable signing key. Unset, `/api/v1/demo/*` returns the ordinary 404.

## Routes (only when enabled)

| Route | Purpose |
|---|---|
| `GET /api/v1/demo/status` | the signer's **public** key id, the three verifier profiles (serial, sha256, key ids and statuses), the five scenarios, isolation and judge mode |
| `GET /api/v1/demo/trust-store` | the public `trust-trusted.json`, so a verifier can repeat the check offline with the CLI |
| `POST /api/v1/demo/verify?scenario=ID` | body: bundle bytes. Applies the scenario's one transform and verifier profile, then runs the real verification and replay. Returns the `ReplayReport` fields plus a `demo` object (scenario, profile, what was changed, sha256 of the tested bytes, isolation mode) |

Upload admission, size caps (8 MiB), the 30 s deadline, the two-slot limit and the per-replay evidence namespace are the ones `POST /replays` uses.

## Scenarios

| Scenario | Bundle tested | Verifier trust store |
|---|---|---|
| `trusted-signer` | as written | lists the signer `ACTIVE` |
| `unknown-signer` | as written | lists an unrelated key only |
| `revoked-signer` | as written | lists the signer `REVOKED` |
| `unsigned-historical` | `signature/envelope.json` removed (what a pre-signing bundle looks like) | `ACTIVE` store |
| `tampered-bundle` | first character of `verdict_hash` in `verdict/verdict.json` changed after signing | `ACTIVE` store |

Results are read from the backend; the UI states what was done to the bundle, never what the outcome should be.

## Security properties (each has a test in `tests/api/test_demo_lab.py`)

- A client names a scenario. It never sends a key or a trust store, and nothing inside an uploaded bundle is added to a trust store. A bundle signed by a stranger is `UNTRUSTED_SIGNER` / `KEY_NOT_IN_TRUST_STORE` even though it embeds its own public key.
- The lab reads **public** material only. The private key lives in a `0700` custodian directory as a `0600` file, is loaded only by the custodian, is never serialised into a response, a log or this repository, and is regenerated at every start. The examiner cannot read it and its worker refuses to start with `VK_SIGNING_KEY_FILE` in its environment.
- The demonstration key's trust window is seven days from provisioning. After that the trusted scenario reports `KEY_EXPIRED`, which is the correct answer.
- Transforms re-zip with bounded reads and the bundle size limits of `bundle.py`; an unreadable upload is a `422 BUNDLE_UNREADABLE`.

## Limits

- It proves nothing about any real signer. The key is disposable and says so in every view.
- There is deliberately no "no trust store" scenario: `verdictkit verify BUNDLE` without `--trust-store` exits 1 with `signer trust: NOT_EVALUATED`, and the browser tests check that offline.
- A trust store profile is chosen by the server's scenario table. This is a demonstration of the mechanism, not a way to reconfigure a production verifier.
