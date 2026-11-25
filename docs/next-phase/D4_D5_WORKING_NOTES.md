# D4 and D5 working notes (design-time scratch, not an Execution_Record)

Baseline: HEAD c29d2fe equals origin/feature/kiro-next-phase. U-001..U-005 already exist in docs/next-phase/EXECUTION_EVIDENCE.md (lines 65-69). No ledger repair needed.

## Where to write
- design.md: insert D4 then D5 before the heading "## Table of contents for D1 to D10". Update the "Document status" paragraph (line 6) and the D4/D5 TOC rows. Do not touch D0-D3.

## D4 facts (read from source)
- mcp_server.py returns failures as plain dicts {"error": "<string>"}; no isError. Version literal "0.1.0" in MCPServer(...). contractVersion literal "1.1.0" in replay_bundle result.
- SDK locked mcp 2.3.0; pyproject says mcp>=1.2 but code imports mcp.server.mcpserver.MCPServer (2.x API). Declaration mismatch.
- SDK: a tool may return CallToolResult (passes through; output validation skipped when is_error). ToolError gives isError with text only (no structured error). Unexpected exceptions are logged with logger.exception (traceback to stderr).
- SDK pre_parse_json and pydantic lax mode may coerce strings for non-str params (allow_refetch). To probe.
- Existing test asserts EXACTLY four tools -> diagnostic tool (R9.4) must be opt-in (R9.1, R9.13 forbid editing that test).
- Existing tests assert only "error" in result -> structured error object is compatible.
- mcp.json: autoApprove [list_claim_types, explain_verdict], env VK_MCP_READONLY=1. mcp.json is hash-pinned executable config (AM-D3-7): any change needs renewed review.
- Tampered bundle: baseline replay_bundle returns report with integrity FAILED; explain_verdict returns {integrity, error}. R9.19 does not list tampered bundle as an execution error -> decision OD-D4.
- R9.6 vs baseline: read-only verify_claim does not fail (network=False). Interpretation decision.

## D5 facts (read from source)
- bundle.py: manifest has NO format version; unlisted-member rule is names - listed - {"manifest.json"}; _check_zip_safety rejects duplicates, "..", backslash, dirs, >4096 entries.
- AUTHENTICITY constant {"status": "NOT_ESTABLISHED", note} used by replay_report_dict (API, CLI, MCP) and api/server.py metadata.
- write_bundle callers: cli.py, mcp_server.py, api/run_service.py. verify_bundle_integrity callers: api/server.py, mcp explain.
- openapi.yaml: AuthenticityReport status const NOT_ESTABLISHED, additionalProperties false; ContractVersion const "1.1.0". ui-kit types.ts mirrors literal. docs/API_CONTRACT.md: "Changing any schema requires bumping it; the frontend refuses unknown versions".
- D2 AM-10: D5 owns ONE contract-version event (rows 1-7 of the coordination table). D1 OD-7: D5 finalizes authenticity fields and tones.
- cryptography 50.0.2 locked, >=43 declared. No new dependency.

## Proposed decisions (to confirm against code before writing)
D4: wrapper returns CallToolResult(is_error=True, structured_content={"error": {code,message,tool}}) for execution errors only; plain functions unchanged; diagnostics tool `server_diagnostics` opt-in via VK_MCP_DIAGNOSTICS=1; no always-on fifth tool.
D5: single member signature/envelope.json (canonical JSON); signing input = domain tag + canonical bytes of signed-fields object; keyId = fingerprint = sha256(raw pubkey); trust store strict JSON, closed schema, as_of injected; MCP never signs; contract 1.2.0 single event.
## Probe results (design-time observation, Windows host, 2026-11-24, mcp 2.3.0; NOT an Execution_Record, UNVERIFIED for R3)
- initialize: protocolVersion 2025-06-18 echoed; serverInfo {name verdictkit, version "0.1.0"}; capabilities prompts, resources, tools.
- tools/list: exactly 4 tools; inputSchema props: list_claim_types none; verify_claim claim (required); replay_bundle path (required), allow_refetch; explain_verdict path (required). No annotations. outputSchema: dict tools permissive {"type":"object","additionalProperties":true}; list_claim_types wrapped {"result":[...]} with required result.
- BASELINE DEFECT: replay_bundle missing path -> isError false, structured {"error":"bundle not found"}.
- SDK validation failure (claim string, path int, missing path) -> isError true but text echoes input_value (canary leaked) and has NO structuredContent.
- allow_refetch "yes" (string) is coerced to true by SDK (read-only mode then refused it). Extra unknown argument is silently ignored. claim passed as JSON string is parsed to object by SDK pre-parse.
- Unknown tool -> isError true text "Unknown tool: <name>" (echoes name).
- verify_claim stub claim ok: fields bundle_path, case_id, isolation_mode, verdict; headline CONTRADICTED; bundle under vk-mcp-* temp dir. explain fields headline, integrity, summary, verdict_hash. list_claim_types returns 4 content blocks (one per claim type) + structured {"result":[...]}.
- stderr: SDK logs one line per rejected call with FIELD NAMES only (no values) at INFO level; no traceback in these cases.

## SDK hooks found
- MCPServer.call_tool(name, arguments, context) is public; _handle_call_tool calls self.call_tool, so a subclass override can normalise errors. MCPServer also has provisional middleware (ctx, call_next).
- Python SDK client skips output-schema validation when isError is true. TypeScript client behaviour UNVERIFIED.
- pre_parse_json parses top-level string arguments into objects (Claude Desktop quirk). Keep for claim; reject non-bool allow_refetch via raw-argument check before delegating.

## Pipeline facts
- run_case: broker.acquire exceptions (EvidenceUnavailable when network False and adapter needs network) are swallowed -> evidence_items=() -> findings INDETERMINATE (evidence_missing). So read-only verify_claim yields a verdict, not an error. R9.6 reading: refetch and acquisition are refused by being disabled; no failure object for verify_claim.
- SocketExaminer.__init__ with expected_peer_uid verifies the socket (verify_examiner_socket) and sets ENFORCED; default timeout 60 s. Diagnostics needs its own 2 s probe.
- test_quote_b7_texas.py also uses mcp_server plain functions and private helpers (_registry, _workdir) and asserts "error" in result and "verdict" not in result -> plain-function return shapes must stay.
## Status at end of this authoring pass
design.md is the source of truth. D4 (section D4.1 to D4.11) and D5 (D5.1 to D5.11) are inserted before the table of contents. Decisions still open are listed in D4.11 (OD-D4-1 to OD-D4-5) and D5.11 (OD-D5-1 to OD-D5-9). Nothing is implemented, run as a gate, or committed. The "Proposed decisions" list above is superseded by design.md.

## D5 probe results (design-time observation, Windows host, 2026-11-24; NOT an Execution_Record, UNVERIFIED for R3)
- cryptography 50.0.2 with OpenSSL 4.0.3. Ed25519 signing is deterministic (identical 64-byte signatures for one message). Signature with S+L is rejected.
- Small-order public keys load: the identity point (y=1) and 32 zero bytes both load, and the universal signature R=identity, S=0 VERIFIES for an arbitrary message. A blocklist of small-order encodings is therefore required (D5.6 step 5, A-12, R-D5-5).
- load_pem_private_key loads an RSA PKCS#8 PEM as RSAPrivateKey (type check needed). An encrypted PEM loaded without a password raises TypeError.
- zipfile (Python 3.12.10, Windows): ZipInfo.filename is sanitised: truncated at NUL, and os.sep rewritten to "/". A member stored as signature\envelope.json reports filename signature/envelope.json (orig_filename keeps the raw name). The baseline backslash test in _check_zip_safety therefore cannot fire on Windows. Two members "signature/envelope.json" and "signature\envelope.json" both report the same filename. D5.2 F5-3 and D5.6 step 1 require every name test to use orig_filename.
- Contract version pins: 10 of 13 files in api/examples contain 1.1.0. Code literals: mcp_server.py:173, api/presenter.py:15, api/server.py:41, ui-kit/src/api.ts:11 (plus ui-kit/src/api.test.ts), ui/judge/app.js and index.html.

## Process notes
- The validate_spec_format tool reports 4 errors and 3 warnings (missing Overview, Architecture, Components and Interfaces, Data Models, Correctness Properties, Error Handling, Testing Strategy). The same result appears on the committed checkpoint c29d2fe, so it is pre-existing. These sections belong to D10.
- U-001 to U-005 already exist in docs/next-phase/EXECUTION_EVIDENCE.md (lines 65 to 69). No ledger change was made.