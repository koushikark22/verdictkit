# Independent security review, Batch 3 (2026-11-27)

Scope: the implementation committed by Batch 1 (signed bundles, custody and MCP hardening) and Batch 2 (portal, Verify Lab, gateway, one-command start), at commit `78f3f58`. Method: read the code that decides trust, then try to break it. Every suspected defect needed a reproduction before any change was allowed, and every result is classified BLOCKER, NON-BLOCKER or NOT REPRODUCED.

**Result: no BLOCKER was found, so no security code was changed in this review.** Seven NON-BLOCKER items are reproduced and listed with the fix that would close each. The only changes made in Batch 3 are four presentation fixes (see `docs/next-phase/EXECUTION_EVIDENCE.md`, "Final Batch 3").

## How it was tested

* Code read: `signing.py`, `bundle.py`, `safeio.py`, `mcp_server.py`, `api/server.py`, `api/demo_lab.py`, `api/draft_store.py`, `deploy/entrypoint.sh`, `scripts/gateway.mjs`, the start and stop scripts.
* Black-box probes of a **second gateway instance** (never the live one) with raw sockets, and of a **throwaway backend container** on its own port with a 1 GiB memory cap. The live demonstration stack was only probed read-only.
* Container permission probes run as the examiner OS user (`vk-examiner`) against the live container.
* Scans of container logs, process arguments, image environment and image contents for secrets.
* The existing regression and gate suites were run as well (`EXECUTION_EVIDENCE.md`, records B3-xx). They are not repeated here.

The raw probe output is kept in a private archive and is not published. This page states what each probe showed.

## NON-BLOCKER findings (reproduced, not fixed)

None of these breaks a product promise (blinding, fail-closed verdicts, signature checks) or exposes private data. The service is a local, loopback-only demonstration; public deployment stays blocked (KL-1).

| ID | Finding | Reproduction | Why it does not block | Fix when needed |
|---|---|---|---|---|
| NB-1 | A cross-site page can send blind writes. | `POST /api/v1/cases` with `Origin: https://evil.example`, `Sec-Fetch-Site: cross-site` and no `Content-Type` (or `text/plain`) returned 201 and a case id. | No response is readable cross-site (no CORS headers; `Cross-Origin-Resource-Policy: same-origin`). Case ids are random. Data is synthetic. Writes are bounded by 120 requests a minute and a 24 h case expiry. | In the gateway, refuse unsafe methods when `Origin` differs from its own origin or `Sec-Fetch-Site` is `cross-site`. Add the same check to the API for its directly published port. |
| NB-2 | The API accepts any `Host` header on its own port. | `GET /api/v1/health` with `Host: evil.example:8001` returned 200. The gateway does check `Host` (421 for six foreign forms). | A DNS-rebinding page could only use the engine as a service. There is no list endpoint and ids are unguessable, so there is nothing private to read. | Add a trusted-host list to the API. |
| NB-3 | The container's access log contains case ids. | `docker logs` shows request paths. 606 lines were scanned: no key, token, traceback or file path. | Only the machine owner reads it. The gateway itself logs nothing per request. | Start the server with `access_log=False`. |
| NB-4 | `drafts.sqlite3` is mode 0644 inside a 0700 custodian directory, and its docstring is imprecise. | Four distinctive claimed figures were searched in every table and column: pre-reveal tables (`drafts`, `freezes`, `evidence_stages`) held none. Only `runs.outcome`, the post-reveal outcome JSON, did. | Pre-reveal data is AES-GCM sealed. The post-reveal outcome is what `GET /outcome` returns anyway. The directory is unreadable to the examiner (checked). | Mode 0600 for the file; reword "No asserted outcomes are stored" to say "before the reveal". |
| NB-5 | The gateway serves `index.html` under NTFS alias names. | `/index.html::$DATA` and `/INDEX~1.HTM` returned the index page as `application/octet-stream`. | Nothing outside `dist` was reachable. Cosmetic. | Reject `:` and `~` in the path. |
| NB-6 | `demo_lab.transform_bundle` reads archive members by name. | For duplicate member names, both copies get the last member's bytes. | Affects only the lab's demonstration copy, which the real verifier then checks. | Read by `ZipInfo`, not by name. |
| NB-7 | Known, documented limits. | See `docs/SIGNING.md` and the earlier ledger. | Stated openly in the product. | No trusted timestamp (expiry is judged when verifying); plugin loading from entry points and `VK_CLAIM_TYPES` (KL-1); Windows permission checks are path-based and cannot close a check/open race. |

## NOT REPRODUCED

| Hypothesis | What was tried | Result |
|---|---|---|
| Windows device names hang the gateway (its file reads are synchronous) | `/CON`, `/NUL`, `/AUX`, `/PRN`, `/COM1`, `/LPT1`, `/con.txt`, `/assets/NUL`, `/quote/CON`, nested forms | Every request answered in under 0.05 s. The instance was still serving after about 70 hostile requests. |
| Traversal or encoded paths reach files outside `dist` or the API | `..`, `%2e%2e`, `%5c`, `%2f`, backslash, NUL, overlong UTF-8, `..;/`, 5000-character path, 3000 query pairs | 400 or 404 or the index page; no file outside `dist` was returned. |
| DNS rebinding and request smuggling against the gateway | Foreign, empty, IP and trailing-dot `Host`; `Content-Length` with `Transfer-Encoding`; duplicate `Host`; absolute-form target | Foreign hosts got 421, smuggling shapes got 400 or normal handling, with no cross-request effect. |
| Upload exhaustion on the API | 9 MiB body, a lying 99-digit `Content-Length`, 4097 and 4000 entries, 70 MiB declared in five entries, `../` and `\` names, a 400000-deep JSON manifest, a 1500-deep envelope, duplicate `manifest.json` | 413 in 0.00 s for oversize. Every archive case returned a FAILED report in under 0.15 s. No 500; the server stayed healthy. |
| Stalled uploads hold the slots forever | Two uploads stalled after one byte, then a third upload | The third got 429 with `Retry-After: 5` at once. The stalled two were ended with 408 at 28.5 s, and the next upload succeeded. |
| The examiner can read the vault, the signing key or the API's memory | As `vk-examiner`: `signing.pem`, vault, drafts, API `environ` and `fd` | All permission denied. It can read evidence (by design) and cannot write evidence, vault or trust stores. |
| Secrets in arguments, environment, logs or the image | Process list, environment variable names, container logs, `docker image inspect`, files in the image | None. The only credential-shaped name is the public `GPG_KEY` constant of the Python base image. The image holds no docs, no `.kiro` and no evidence. |
| Private key or trust material leaves through the API | `/demo/status`, `/demo/trust-store` | Public key id and public trust stores only. |
| MCP tools open paths outside approved roots (UNC, device, alternate stream) | Code review of `_syntactically_allowed` and `read_file_under_roots`; a real MCP client asking `replay_bundle` for a repository path | Rejected before any file system access (`PATH_NOT_ALLOWED`). |
| Start or stop scripts end an unrelated process or container | Read of the ownership checks | A gateway is ended only if its command line names `gateway.mjs` and this repository; a container only if it carries the managed label. |
| Unsafe sinks or a network or LLM client in the evaluator paths | Search of `core` and both apps | No `pickle`, `eval`, `exec`, `subprocess`, shell or `float(`; sockets only in the examiner transport. |
| HTML injection from bundle-controlled text | Search of all UI sources | No `innerHTML` or equivalent; the CSP meta allows scripts from `'self'` only. |

## Not reviewed

Timing side channels; the base image's own supply chain beyond the digest pin and the dependency audits; any public deployment (none exists); a Linux per-test run from a full checkout (DLV-1 to DLV-4 stay UNVERIFIED).
