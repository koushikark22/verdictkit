# Evidence publication, redaction methodology and hashes

Status: documentation, written 2026-11-25. It records one application of the publication rule of design D8 (DD8-9, finding H-1) and requirements 1.14, 3.11 and 3.14. It is not an Execution_Record.

## Rule

- A Private_Original is a raw evidence file kept byte for byte outside the published tree. Its SHA-256 is published.
- A Sanitized_Copy is the published file. It has its own SHA-256. It has the same lines in the same order, so line n of the copy is line n of the original and the record identifiers of `baseline/EXECUTION_INDEX.md` still apply.
- The rules below are ordered, exact-string and case-sensitive. They are applied to the raw file text, where a path separator appears as `\\` inside JSON strings. The list of removed values is never published. Only the class, the placeholder and the counts are.
- A zero-hit scan over the classes below gates every commit that publishes evidence or documents. The result is a count and is never a claim that nothing sensitive remains.

## Rules

| Rule | Class | What it matches | Placeholder |
|---|---|---|---|
| RR-1 | Local checkout path | The absolute path of the local clone of this repository (drive, user profile folder, parent folders, repository folder) | `<REPO>` |
| RR-2 | Temporary directory path | The user's temporary directory below the user profile | `<TEMP>` |
| RR-3 | User profile path | The user profile directory | `<USERPROFILE>` |

Classes scanned and not matched by these rules in the published files: other user names, host names, e-mail addresses, non-loopback IP addresses, access tokens, key blocks, secret assignments, long encoded runs other than SHA-256 values.

## Applied files

| File | Treatment | Private original SHA-256 | Published file | Published SHA-256 | Lines | Redactions |
|---|---|---|---|---|---|---|
| `baseline/records.jsonl` (R) | Private_Original kept, Sanitized_Copy published | `828d336960a1e7787b6d41d6bacb03cb7e80e5e6367c784025c2d5b4cbd35ea4` (equals the Execution_Index) | `baseline/records.sanitized.jsonl` | `05f9e31ab6d2aee78b576b9ba3fea6d39456031fb9a37f92a3f2f0cdc9df6a8c` | 28 | RR-1: 1, RR-2: 3, RR-3: 0, on 3 lines (R20, R23, R24) |
| `baseline/records-first-pass-overlapping.jsonl` (F) | No class matched, published unchanged under its original name | not needed (published file is the original) | `baseline/records-first-pass-overlapping.jsonl` | `5cee53f557544a2e220a89ab0abbc8569f0f7d2a0aff61c06d48a56b7b1dd4ba` (equals the Execution_Index) | 17 | 0 |
| `baseline/logs/*.log` | Git-ignored (`*.log`), not published. Hashes are published in `baseline/LOG_HASHES.txt` | in `LOG_HASHES.txt` | none | none | n/a | n/a |

The Private_Original of `records.jsonl` is kept under `baseline/private-originals/`, which a local, unversioned exclude rule keeps out of git. The owner may move it to storage of their choice. Its hash in the Execution_Index identifies it.

## Verification

1. Without the original: the SHA-256 of each published file equals the value above, and the line count is as stated.
2. With the original: apply RR-1, RR-2 and RR-3 in this order and compare the SHA-256 of the result with the published value.
3. Idempotence: applying the rules to the published copy changes nothing (checked on 2026-11-25; design-time observation, UNVERIFIED for Requirement 3).

## Not redacted, and why

- Text that was already published before this change (commit `c29d2fe` and earlier) names the executable and the process id of an unrelated local service that held port 8000 (design D0, `BASELINE_REPORT.md`, ledger E-027). Classification: low sensitivity, a software inventory item. History is not rewritten, because a force push is not permitted. New documents say "an unrelated local service". The owner may decide to redact the published text in a later commit.
- Fictional example paths in the design (hook matcher fixtures) use the names `dev` and `Jane Doe`. They are constructed test data.
- SHA-256 values, commit identifiers, UTC timestamps, tool versions and command lines are evidence and are kept.

## Open item

OD-D8-8: whether to publish sanitized copies of the logs. Not decided. The existing pattern (hash published, file private) stays.