# D6 and D7 working notes (design-time scratch, not an Execution_Record)

Baseline: branch feature/kiro-next-phase at c29d2fe plus uncommitted D4/D5 text. Facts were read from source with targeted reads on 2026-11-24 (Windows host). Nothing was run as a gate. All facts are UNVERIFIED for Requirement 3 until an Execution_Record exists.

## D6 facts (read from source)
- core/src/verdictkit/plugin.py: ClaimType Protocol (runtime_checkable): type_id, schema_version, param_fields, outcome_fields, nine methods. Optional hooks use getattr: validate_assumptions, point_outcomes, illustrative_records, evidence_adapters, fixtures, extract_text. Registry.register overwrites a duplicate type_id silently. get raises KeyError. type_ids is sorted.
- cli._load_registry is the only discovery path. Callers: CLI run and replay, api/server.py, mcp_server._registry, examiner/worker.py.
  - Step 1 entry points: group verdictkit.claim_types, ep.load(), instantiate if callable, register. The whole loop is inside one try/except Exception: pass, so one failing plugin silently stops all later plugins.
  - Step 2 VK_CLAIM_TYPES: "pkg.module:Class" or bare module, importlib.import_module, errors propagate.
- deploy/entrypoint.sh passes VK_CLAIM_TYPES to both the custodian and the examiner process. Dockerfile copies examples/ and runs uv sync --frozen --all-packages, so the stub plugin is installed in the image.
- api/run_service.py CONTRACT_CLAIM_TYPES = reel.mechanical.v1, quote.finance.v1, quote.lease.v1. api/server.py _contract_registry filters AFTER _load_registry, so unlisted plugin code is still imported in the API process.
- Entry points today: quote-autopsy (quote.finance.v1, quote.lease.v1), reel-autopsy (reel.mechanical.v1), stub (name example_receipt, type_id example.receipt.v1). Entry point name need not equal type_id.
- No type_id grammar and no schema_version comparison exist in core. Intake uses raw.get("schema_version", claim_type.schema_version).
- Stub: examples/stub_claimtype/{__init__.py, receipt.py, claim.json, golden.vkb}, examples/pyproject.toml. A different copy of the receipt type is tests/contract/receipt_claimtype.py (file hashes differ). test_blinding and test_bundle_replay use the tests copy.
- Reusable contract checks: test_blinding (task bytes and examination independent of outcomes), test_llm_fence (AST scan, banned roots, import_module of banned literal), test_commitment, test_isolation (container only).
- First-party plugin sources have no float, no .now( and no os.environ (grep). reel imports datetime, date, timezone.
- VK_PROFILE exists only in the design (DD2-2). VK_JUDGE_MODE exists in code (api/server.py startup_checks).

## D6 decisions to write
1. Trust model: a plugin is trusted code admitted by an operator. The SDK is a conformance and safety rail, not a sandbox. No request, API field, MCP argument or UI input names a plugin.
2. New package core/src/verdictkit/sdk (loader, validate, conformance, scaffold). plugin.py and the ClaimType signatures are unchanged. cli._load_registry keeps its name and delegates to the loader.
3. Loader: deterministic order (distribution name, entry point name). Per-plugin isolation, one stderr code line per failure, no exception text. Duplicate type_id rejects ALL colliding registrations. Namespaces quote and reel are reserved for distributions quote-autopsy and reel-autopsy.
4. Restricted mode when VK_JUDGE_MODE=1 or VK_PROFILE=public: closed allowlist constant in code, filter BEFORE ep.load() so unlisted code is never imported. VK_CLAIM_TYPES set in this mode means startup refuses. The examiner worker uses the same policy (D2 coordination: entrypoint passes the profile to it).
5. Validation: type_id grammar NAMESPACE.NAME.vN, package-name rules, descriptor checks, claim validation by plugin raising SchemaError only.
6. Versions: vN suffix = compatibility generation, schema_version = revision, optional class attribute sdk_api (absent = 1, only 1 accepted), scaffold pyproject pins a verdictkit range. HTTP contract unchanged: new types are not exposed over HTTP. Gap: schema_version mismatch is not enforced at intake or replay.
7. Entry point: python -m verdictkit.sdk new and check. No change to the cli parser.
8. Scaffold: validate everything before touching disk, build in memory, exclusive create, refuse target inside core/src/verdictkit, refuse file or symlink target, reject Windows reserved names, remove only what this run created, deterministic bytes (LF, no timestamps).
9. Conformance checks CS-01 to CS-10 (registration, protocol surface, field disjointness, blinding bytes, determinism in process and across PYTHONHASHSEED, no float, evidence policy, canonical golden claim, golden replay REPRODUCED, AST fence).
10. Synthetic example: scaffold output for example.line_total.v1 generated at test time and not committed. The stub stays the committed example. Numbers are constructed and labelled synthetic (steering rule 8).

## D7 facts (read from source)
- rules/TX.json is canonical JSON with a closed key set: doc_fee, local_rate_max_pct, local_rate_min_pct, localities, sources, state, state_rate_pct. Each source has only uri, retrieved_at, sha256_of_source. No media type, excerpt or effective date. MANIFEST.json is {"files": {name: sha256}}. .gitattributes sets -text on rules/*.json.
- load_rules verifies the manifest hash, canonical form and the closed key set, so TX.json cannot gain fields. Its sha256 enters evidence hashes and the verdict hash, so editing TX.json changes every Texas verdict hash.
- claim_type.py: external findings tax_rate and doc_fee_cap. state != "TX" gives unsupported_jurisdiction. TX with no matching evidence gives evidence_unavailable. jurisdiction params are {state (two letters), locality_code}. Quote claims carry no date.
- Status enum has no UNVERIFIED. Finding.reason is a free string (OpenAPI reason is string or null).
- Existing tests use CA as the unsupported example: test_quote_b7_texas.py::test_non_tx_external_findings_unsupported_jurisdiction and tests/api/test_http_run_lifecycle.py::test_external_only_claim_is_indeterminate. Adding California conflicts with 12.13 and with D4-AC-2 (which allows no edit to the Texas test file).
- B7_TEXAS_SPEC.md: the 225 USD doc-fee amount rests on OCCC bulletin B16-5 (an agency document), and the amendment status of the rule is flagged unchecked. No source is the rule text itself (12.11).
- EvidenceDTO.retrievedAt is the acquisition time, not the source retrieval date. Showing the snapshot retrieval date (12.14) needs a contract-visible field, which belongs in the D5.8 compatibility classification.

## D7 decisions to write
1. Two tiers. Legacy tier (TX.json, load_rules, sources.py, Texas tests) is frozen byte for byte. New v2 snapshot format for CA, FL, NY. Texas gets an additive sidecar only.
2. Official host registry: exact hosts, https only, no IP literals, no userinfo, no cross-host redirects, a recorded basis per host. Candidate hosts are not named as facts.
3. Rule status: VERIFIED, UNVERIFIED, AMBIGUOUS, UNSUPPORTED. Authority class BINDING_LAW or AGENCY_GUIDANCE (default guidance unless the source shows otherwise). Only VERIFIED binding rules reach SUPPORTED or REFUTED. UNVERIFIED is a rule status, and the finding is INDETERMINATE with a reason code.
4. Update pipeline: fetch (only stage with network and clock), verify, build (pure function), review (human record the agent cannot write), promote. The reviewer supplies values and dates. The tool only verifies them against the retrieved bytes.
5. Time: as-of date in the claim, half-open window from effective_from to superseded_on, no wall clock. Retrieval age is shown and gated in CI, and never changes a verdict.
6. Rollback: manifest active pointer, old versions retained, rollback is a reviewed commit. Bundles embed their evidence, so replay is unaffected. Statuses ACTIVE, SUSPENDED, WITHDRAWN are checked at acquisition only.
7. Order: Texas completion (rule text or UNVERIFIED), then CA, FL, NY. A jurisdiction that fails the gate is recorded BLOCKED.
8. Acceptance tests: unsupported jurisdictions, contradictory evidence, effective-date boundaries, and the four outcomes for each jurisdiction (12.12).

## Open or blocking items found so far
- B-D7-1 CA test collision (above). Needs a maintainer decision.
- PDF sources: excerpt containment cannot be checked on raw PDF bytes. Needs an approved extraction method, or PDF-only rules stay UNVERIFIED.
- Stored source bytes and redistribution rights: 12.7 recomputes source hashes, which needs the bytes in the repository.
- Replay of bundles written before a jurisdiction is added (finding text and reason change).
- Quote claims have no date field, so the as-of date is an additive claim parameter.
## Status at end of this authoring pass
design.md is the source of truth. D4.12 and D5.12 (decision records), D6 (D6.1 to D6.10) and D7 (D7.1 to D7.10) are inserted before the table of contents, and the status paragraph and table of contents rows are updated. D0 to D5 text is unchanged apart from those lines (checked against a backup copy). The decision lists above are superseded by design.md. Nothing is implemented and no gate was run.

## Design-time observation (Windows host, 2026-11-24, Python 3.12.10; NOT an Execution_Record, UNVERIFIED for R3)
- Listing the entry-point group verdictkit.claim_types with importlib.metadata returned four entries with distribution, name and value, and imported none of the plugin modules (quote_autopsy, reel_autopsy, stub_claimtype). This supports the D6.4 rule that listing imports nothing.
  - quote-autopsy: quote.finance.v1 and quote.lease.v1
  - reel-autopsy: reel.mechanical.v1
  - verdictkit-stub-receipt: example_receipt (type_id example.receipt.v1)

## Process notes
- design.md uses CRLF line endings (2216 pairs before this pass). Insertions were converted to CRLF. The format validator reports the same 4 errors and 3 warnings as before this pass (missing D10 sections).
- Sensitive-information review of this file and D4_D5_WORKING_NOTES.md: pattern scan for key blocks, cloud key ids, secret assignments, user profile paths, e-mail addresses and long encoded runs found nothing.
- U-001 to U-005 already exist in docs/next-phase/EXECUTION_EVIDENCE.md. No ledger change was made.