import type { VerificationInput } from "@verdictkit/ui-kit";

/**
 * One plain-language sentence for a verification result. It is a pure function of the fields the
 * backend returned; it never decides anything and never says that the claim itself is true.
 */
export function explainReport(r: VerificationInput): string {
  const a = r.authenticity;
  if (r.integrity.status === "FAILED") {
    return "The bundle's contents no longer match the manifest that was sealed. Whatever the signature says, this file is not what was signed, so it cannot be replayed or trusted.";
  }
  if (a.status === "ESTABLISHED") {
    return "A signer this verifier trusts signed exactly these bytes, the integrity checks pass, and replaying the examination reproduced the verdict. That establishes who sealed the bundle. It does not show that the claim is true.";
  }
  if (a.signatureValidity === "UNSIGNED") {
    return "Nothing in this bundle says who made it. It still verifies and replays, so the verdict is reproducible, but its origin is not established.";
  }
  if (a.signatureValidity !== "VALID") {
    return "The signature does not check out against the signed manifest, so the bundle's origin is not established.";
  }
  if (a.reasonCodes.includes("KEY_REVOKED")) {
    return "The signature is mathematically valid, but this verifier has revoked the signing key and no longer accepts signatures from it.";
  }
  if (a.signerTrust === "UNTRUSTED_SIGNER") {
    return "The signature is mathematically valid, but this verifier has no reason to trust that key. A key found inside a bundle is never trusted on its own.";
  }
  return "The signature is valid, but the signer was not evaluated against a trust store, so authenticity is not established.";
}
