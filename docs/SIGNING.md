# Signed verdict bundles (contract 1.2.0)

Design reference: `.kiro/specs/verdictkit-next-phase/design.md`, section D5. This page is the operator view.

## What a signature does and does not say

A signature says the holder of one Ed25519 key signed the exact bytes of a bundle's `manifest.json`. The manifest lists the SHA-256 of every other member, so the signature covers them too. It does **not** say the claim is true, that the signing time is trusted, or that the key was never compromised. Zip container bytes (timestamps, headers) are outside the signed object.

Five results stay separate in every report, CLI output and UI:

| Result | Values |
|---|---|
| `integrity` | `VERIFIED`, `FAILED` |
| `reproducibility` | `REPRODUCED`, `REPRODUCED_ACROSS_ENV`, `DIVERGED`, `UNVERIFIABLE`, `NOT_RUN` |
| `signatureValidity` | `UNSIGNED`, `VALID`, `INVALID`, `UNSUPPORTED_ALGORITHM` |
| `signerTrust` | `NOT_EVALUATED`, `TRUSTED`, `UNTRUSTED_SIGNER` |
| `authenticity` | `ESTABLISHED` only for `VALID` + `TRUSTED` + integrity `VERIFIED`; otherwise `NOT_ESTABLISHED` |

Unsigned (historical) bundles are `UNSIGNED` and `NOT_ESTABLISHED`. They keep verifying and replaying exactly as before. Signing adds one archive member, `signature/envelope.json`, which is not listed in the manifest and is not an input to the verdict hash.

## Signing

Set `VK_SIGNING_KEY_FILE` to the **path** of an unencrypted PKCS#8 PEM Ed25519 private key (at most 4,096 bytes). The variable never holds key bytes.

```
openssl genpkey -algorithm ed25519 -out signing.pem && chmod 600 signing.pem
```

- POSIX: a regular file, not a link, owned by the running user, no group or other permission bits.
- Windows: a regular file whose access list names only the current user, SYSTEM and Administrators.
  A new file inherits its folder's entries, and ordinary folders often grant other local accounts access,
  which is refused (`SIGNING_KEY_PERMISSIONS`). Lock it down first:
  `icacls signing.pem /inheritance:r /grant:r "%USERNAME%:F"`.
- Set but unusable is an error (`SIGNING_KEY_MISSING`, `SIGNING_KEY_UNREADABLE`, `SIGNING_KEY_UNSUPPORTED`, `SIGNING_KEY_PERMISSIONS`). The tools never fall back to an unsigned bundle. The API start-up stops with exit 2 and `VK_STARTUP_ERROR=CONFIG_INVALID:VK_SIGNING_KEY_FILE`.
- Only the custodian signs (`verdictkit run`, the API run service). The examiner never sees the key and its worker refuses to start if `VK_SIGNING_KEY_FILE` is in its environment. The MCP server does not sign.
- Never commit a production key. Tests and the `gate-sign` container gate use throwaway keys generated at run time.

## Trust store

Trust is the verifier's configuration, never the bundle's. An embedded public key is not trusted by itself.

`VK_TRUST_STORE_FILE` (or `--trust-store FILE`); optional `VK_TRUST_STORE_SHA256` pins the file. The file is re-read at each verification.

```json
{
  "format": "vk-trust-store",
  "format_version": 1,
  "serial": 1,
  "keys": [
    {
      "key_id": "<sha256 of the 32 raw public-key bytes, hex>",
      "public_key": "<32 raw public-key bytes, 64 hex characters>",
      "status": "ACTIVE",
      "not_before": "2026-01-01T00:00:00Z",
      "not_after": "2027-01-01T00:00:00Z",
      "note": "optional"
    }
  ]
}
```

Generate an entry from a key file (no private material is printed):

```
python -c "import json; from verdictkit.signing import load_signer, trust_entry_for; s = load_signer('signing.pem'); print(json.dumps(trust_entry_for(s, not_before='2026-01-01T00:00:00Z', not_after='2027-01-01T00:00:00Z'), indent=2))"
```

The schema is closed: an unknown field, status or format version makes the whole store unusable, which reports `NOT_EVALUATED` and never `TRUSTED`. At most 1,024 keys and 256 KiB. Duplicate keys, floats and small-order public keys are refused.

- `status` is `ACTIVE`, `ROTATED` or `REVOKED`. `not_before` and `not_after` are inclusive and are compared with the verifier's clock (`--as-of`, default now), not the manifest's `written_at`, which the signer chooses.
- **Rotation:** add the new key as `ACTIVE`, raise `serial`, distribute the file, then mark the old key `ROTATED`. Both stay trusted inside their intervals (`KEY_ROTATED` is reported for the old one).
- **Revocation:** mark the key `REVOKED` (not `ROTATED`) in a new file with a higher `serial`. There is no online revocation. Every report shows the store `serial` and `sha256`; pin the hash in deployment configuration.

## Verifying (offline)

```
verdictkit verify bundle.vkb --trust-store trust.json     # exit 0 only if authenticity is ESTABLISHED
verdictkit replay bundle.vkb --trust-store trust.json     # also re-executes; exit rule unchanged
```

`replay` keeps its exit rule (0 only for a reproduced bundle with verified integrity); a signature never changes it. HTTP reports `authenticity` in `GET /cases/{id}/bundle/metadata` and `POST /replays`; MCP reports it in `replay_bundle` and `explain_verdict`.

## Reason codes

Validity: `NO_ENVELOPE`, `ARCHIVE_UNREADABLE`, `DUPLICATE_ARCHIVE_PATH`, `UNKNOWN_SIGNATURE_MEMBER`, `ENVELOPE_LISTED_IN_MANIFEST`, `ENVELOPE_TOO_LARGE`, `ENVELOPE_MALFORMED`, `ENVELOPE_NON_CANONICAL`, `ALGORITHM_UNSUPPORTED`, `PROTOCOL_UNSUPPORTED`, `BUNDLE_FORMAT_UNSUPPORTED`, `KEY_ID_MISMATCH`, `PUBLIC_KEY_SMALL_ORDER`, `SIGNATURE_MALFORMED`, `MANIFEST_HASH_MISMATCH`, `SIGNATURE_MISMATCH`.
Trust: `TRUST_STORE_NOT_CONFIGURED`, `TRUST_STORE_UNREADABLE`, `TRUST_STORE_INVALID`, `TRUST_STORE_UNSUPPORTED_VERSION`, `TRUST_STORE_HASH_MISMATCH`, `KEY_NOT_IN_TRUST_STORE`, `KEY_REVOKED`, `KEY_ROTATED`, `KEY_NOT_YET_VALID`, `KEY_EXPIRED`.
Authenticity: `INTEGRITY_NOT_VERIFIED`.

## Known limits

- No trusted timestamp: a key used after rotation cannot be told from an earlier use.
- A stale trust store is the operator's risk; there is no online revocation.
- On Windows the permission checks are path-based and cannot close a race between the check and the open.
- Hardware or cloud key custody, signing of individual evidence blobs and transparency logs are not implemented.
