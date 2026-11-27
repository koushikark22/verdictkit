"""Ed25519 signed verdict bundles. Reference: design D5 (envelope, protocol, trust store).

Four results stay separate: ``integrity`` and ``reproducibility`` (bundle.py) and, here,
``signatureValidity`` (who signed these exact manifest bytes) and ``signerTrust`` (does this
operator's trust store accept that key). ``authenticity`` is ESTABLISHED only for VALID +
TRUSTED + integrity VERIFIED. It never says the claim is true.

Verification is offline and a pure function of the archive bytes, the trust-store bytes and the
caller-supplied ``as_of`` time (the verifier's clock, never the manifest's ``written_at``).
Trust is configured by the operator (``VK_TRUST_STORE_FILE``); no bundle member, API parameter
or MCP argument can select or change it. An embedded public key is never trusted by itself.

Private keys are loaded from a file named by ``VK_SIGNING_KEY_FILE``. The code never generates,
stores, logs or prints a production key. Error text is fixed and never holds key bytes, paths
or exception text.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canonical import CanonicalizationError, canonical_bytes, parse_canonical, sha256_hex
from .safeio import UnsafeFile, read_secret_file

SIGNATURE_MEMBER = "signature/envelope.json"
ALGORITHM = "ed25519"
PROTOCOL = "vk-bundle-sig"
PROTOCOL_VERSION = "1"
BUNDLE_FORMAT = "vkb/1"
MAX_ENVELOPE_BYTES = 2048
MAX_SIGNING_KEY_BYTES = 4096
MAX_TRUST_STORE_BYTES = 262144
MAX_TRUST_KEYS = 1024
_MAX_MEMBER_BYTES = 16 * 1024 * 1024
_TAG = b"VerdictKit bundle signature v1\x00"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX128 = re.compile(r"^[0-9a-f]{128}$")
_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# The eight small-order points of edwards25519. A signature by such a key can verify for any message.
_SMALL_ORDER = frozenset(bytes.fromhex(h) for h in (
    "0000000000000000000000000000000000000000000000000000000000000000",
    "0100000000000000000000000000000000000000000000000000000000000000",
    "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
    "0000000000000000000000000000000000000000000000000000000000000080",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",
))
# R = identity, S = 0. Verifies under every small-order key (including non-canonical encodings
# the library accepts) and under no honest key.
_PROBE_SIGNATURE = bytes.fromhex("01" + "00" * 31) + b"\x00" * 32

SIGNATURE_STATES = ("UNSIGNED", "VALID", "INVALID", "UNSUPPORTED_ALGORITHM")
TRUST_STATES = ("NOT_EVALUATED", "TRUSTED", "UNTRUSTED_SIGNER")


# ------------------------------------------------------------------------- signing keys

class SigningKeyError(ValueError):
    """The configured signing key cannot be used. ``code`` is one of SIGNING_KEY_MISSING,
    SIGNING_KEY_UNREADABLE, SIGNING_KEY_UNSUPPORTED, SIGNING_KEY_PERMISSIONS."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Signer:
    key_id: str
    public_key_hex: str
    _private: Ed25519PrivateKey = field(repr=False, compare=False)

    def sign(self, message: bytes) -> bytes:
        return self._private.sign(message)


def signer_from_private_key(private: Ed25519PrivateKey) -> Signer:
    raw = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return Signer(key_id=hashlib.sha256(raw).hexdigest(), public_key_hex=raw.hex(), _private=private)


_KEY_ERRORS = {
    "MISSING": "SIGNING_KEY_MISSING", "PERMISSIONS": "SIGNING_KEY_PERMISSIONS",
    "UNREADABLE": "SIGNING_KEY_UNREADABLE", "NOT_REGULAR": "SIGNING_KEY_UNREADABLE",
    "TOO_LARGE": "SIGNING_KEY_UNREADABLE", "NOT_REMOVED": "SIGNING_KEY_UNREADABLE",
}


def load_signer(path: str | os.PathLike) -> Signer:
    """An unencrypted PKCS#8 PEM Ed25519 key in a regular, non-link, private file."""
    try:
        data = read_secret_file(os.path.abspath(os.fspath(path)), max_bytes=MAX_SIGNING_KEY_BYTES)
    except UnsafeFile as exc:
        raise SigningKeyError(_KEY_ERRORS.get(exc.reason, "SIGNING_KEY_UNREADABLE")) from None
    if not data.strip():
        raise SigningKeyError("SIGNING_KEY_UNSUPPORTED")
    try:
        key = serialization.load_pem_private_key(data, password=None)
    except (TypeError, ValueError, UnsupportedAlgorithm):
        raise SigningKeyError("SIGNING_KEY_UNSUPPORTED") from None
    if not isinstance(key, Ed25519PrivateKey):
        raise SigningKeyError("SIGNING_KEY_UNSUPPORTED")
    return signer_from_private_key(key)


def load_signer_from_env(environ: Mapping[str, str] | None = None) -> Signer | None:
    """``VK_SIGNING_KEY_FILE`` unset or empty: no signing. Set but unusable: ``SigningKeyError``.
    There is no silent downgrade to an unsigned bundle."""
    env = os.environ if environ is None else environ
    path = env.get("VK_SIGNING_KEY_FILE", "")
    if not path:
        return None
    return load_signer(path)


# ------------------------------------------------------------------- envelope and protocol

def _signing_input(signed: Mapping[str, str]) -> bytes:
    return _TAG + canonical_bytes(dict(signed))


def build_envelope(signer: Signer, manifest_bytes: bytes) -> bytes:
    signed = {
        "alg": ALGORITHM, "bundle_format": BUNDLE_FORMAT, "key_id": signer.key_id,
        "manifest_sha256": sha256_hex(manifest_bytes), "protocol": PROTOCOL,
        "protocol_version": PROTOCOL_VERSION,
    }
    envelope = dict(signed, public_key=signer.public_key_hex,
                    signature=signer.sign(_signing_input(signed)).hex())
    return canonical_bytes(envelope)


@dataclass(frozen=True)
class SignatureCheck:
    validity: str                      # one of SIGNATURE_STATES
    reasons: tuple[str, ...] = ()
    key_id: str | None = None
    public_key: str | None = None


def _is_small_order(public: bytes) -> bool:
    if public in _SMALL_ORDER:
        return True
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(_PROBE_SIGNATURE, b"verdictkit small-order probe")
    except (InvalidSignature, ValueError):
        return False
    return True


def verify_envelope(manifest_bytes: bytes, envelope_bytes: bytes) -> SignatureCheck:
    """Design D5.6 steps 4 to 7. Never raises; never returns VALID unless the math verifies."""
    def invalid(code: str) -> SignatureCheck:
        return SignatureCheck("INVALID", (code,))

    if len(envelope_bytes) > MAX_ENVELOPE_BYTES:
        return invalid("ENVELOPE_TOO_LARGE")
    try:
        json.loads(envelope_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return invalid("ENVELOPE_MALFORMED")
    try:
        env = parse_canonical(envelope_bytes)
    except CanonicalizationError:
        return invalid("ENVELOPE_NON_CANONICAL")
    names = {"alg", "bundle_format", "key_id", "manifest_sha256", "protocol", "protocol_version",
             "public_key", "signature"}
    if not isinstance(env, dict) or set(env) != names or not all(isinstance(v, str) for v in env.values()):
        return invalid("ENVELOPE_MALFORMED")
    if not (_HEX64.match(env["key_id"]) and _HEX64.match(env["manifest_sha256"])
            and _HEX64.match(env["public_key"])):
        return invalid("ENVELOPE_MALFORMED")
    if not _HEX128.match(env["signature"]):
        return invalid("SIGNATURE_MALFORMED")

    unsupported = []
    if env["alg"] != ALGORITHM:
        unsupported.append("ALGORITHM_UNSUPPORTED")
    if env["protocol"] != PROTOCOL or env["protocol_version"] != PROTOCOL_VERSION:
        unsupported.append("PROTOCOL_UNSUPPORTED")
    if env["bundle_format"] != BUNDLE_FORMAT:
        unsupported.append("BUNDLE_FORMAT_UNSUPPORTED")
    if unsupported:
        return SignatureCheck("UNSUPPORTED_ALGORITHM", tuple(sorted(unsupported)))

    public = bytes.fromhex(env["public_key"])
    if not hmac.compare_digest(hashlib.sha256(public).hexdigest(), env["key_id"]):
        return invalid("KEY_ID_MISMATCH")
    if _is_small_order(public):
        return invalid("PUBLIC_KEY_SMALL_ORDER")
    if not hmac.compare_digest(sha256_hex(manifest_bytes), env["manifest_sha256"]):
        return invalid("MANIFEST_HASH_MISMATCH")
    signed = {k: env[k] for k in ("alg", "bundle_format", "key_id", "manifest_sha256", "protocol",
                                  "protocol_version")}
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(bytes.fromhex(env["signature"]),
                                                          _signing_input(signed))
    except InvalidSignature:
        return invalid("SIGNATURE_MISMATCH")
    except ValueError:
        return invalid("ENVELOPE_MALFORMED")
    return SignatureCheck("VALID", (), env["key_id"], env["public_key"])


def _reserved(name: str) -> bool:
    return unicodedata.normalize("NFKC", name).casefold().startswith("signature")


def check_archive(path: str | os.PathLike) -> SignatureCheck:
    """Design D5.6 steps 1 to 7 for a bundle file. Reads only the member list, the manifest
    and the envelope. Independent of the integrity checks."""
    try:
        zf = zipfile.ZipFile(path, "r")
    except (zipfile.BadZipFile, OSError):
        return SignatureCheck("UNSIGNED", ("ARCHIVE_UNREADABLE",))
    try:
        with zf:
            infos = zf.infolist()
            raw_names = [(i.orig_filename, i.filename) for i in infos]
            envelope_infos = [i for i in infos if i.filename == SIGNATURE_MEMBER
                              and i.orig_filename == SIGNATURE_MEMBER]
            others = [n for raw, clean in raw_names for n in (raw, clean)
                      if _reserved(n) and n != SIGNATURE_MEMBER]
            if others:
                return SignatureCheck("INVALID", ("UNKNOWN_SIGNATURE_MEMBER",))
            if len(envelope_infos) > 1:
                return SignatureCheck("INVALID", ("DUPLICATE_ARCHIVE_PATH",))
            if not envelope_infos:
                return SignatureCheck("UNSIGNED", ("NO_ENVELOPE",))
            envelope_info = envelope_infos[0]
            manifest_infos = [i for i in infos if i.filename == "manifest.json"]
            if len(manifest_infos) != 1 or manifest_infos[0].file_size > _MAX_MEMBER_BYTES:
                return SignatureCheck("INVALID", ("ARCHIVE_UNREADABLE",))
            if envelope_info.file_size > MAX_ENVELOPE_BYTES:
                return SignatureCheck("INVALID", ("ENVELOPE_TOO_LARGE",))
            with zf.open(manifest_infos[0]) as fh:
                manifest_bytes = fh.read(_MAX_MEMBER_BYTES + 1)
            if len(manifest_bytes) > _MAX_MEMBER_BYTES:
                return SignatureCheck("INVALID", ("ARCHIVE_UNREADABLE",))
            with zf.open(envelope_info) as fh:
                envelope_bytes = fh.read(MAX_ENVELOPE_BYTES + 1)
    except (zipfile.BadZipFile, OSError, EOFError, NotImplementedError, ValueError):
        return SignatureCheck("INVALID", ("ARCHIVE_UNREADABLE",))
    try:
        listed = parse_canonical(manifest_bytes)
        if isinstance(listed, dict) and isinstance(listed.get("files"), dict) and any(
                _reserved(n) for n in listed["files"]):
            return SignatureCheck("INVALID", ("ENVELOPE_LISTED_IN_MANIFEST",))
    except CanonicalizationError:
        pass  # an unreadable manifest fails integrity; the signature math below still binds its bytes
    return verify_envelope(manifest_bytes, envelope_bytes)


# --------------------------------------------------------------------------- trust store

class TrustStoreError(ValueError):
    """The store cannot be used. ``code`` is a reason code of design D5.3."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class TrustEntry:
    key_id: str
    public_key: str
    status: str
    not_before: str
    not_after: str


@dataclass(frozen=True)
class TrustStore:
    serial: int
    sha256: str
    entries: Mapping[str, TrustEntry]
    format_version: int = 1


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate key")
        out[k] = v
    return out


def _reject_number(_text: str) -> Any:
    raise ValueError("non-integer number")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def load_trust_store(path: str | os.PathLike, *, pinned_sha256: str | None = None) -> TrustStore:
    """Strict, closed-schema trust store (design D5.7). Read at each verification."""
    try:
        data = read_secret_file(os.path.abspath(os.fspath(path)), max_bytes=MAX_TRUST_STORE_BYTES,
                                require_private=False)
    except UnsafeFile:
        raise TrustStoreError("TRUST_STORE_UNREADABLE") from None
    digest = hashlib.sha256(data).hexdigest()
    if pinned_sha256 is not None and not hmac.compare_digest(digest, pinned_sha256.strip().lower()):
        raise TrustStoreError("TRUST_STORE_HASH_MISMATCH")
    try:
        if data.startswith(b"\xef\xbb\xbf"):
            raise ValueError("BOM")
        doc = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicates,
                         parse_float=_reject_number, parse_constant=_reject_number)
    except (ValueError, UnicodeDecodeError):
        raise TrustStoreError("TRUST_STORE_INVALID") from None
    if not isinstance(doc, dict) or set(doc) != {"format", "format_version", "serial", "keys"} \
            or doc["format"] != "vk-trust-store":
        raise TrustStoreError("TRUST_STORE_INVALID")
    if not _is_int(doc["format_version"]):
        raise TrustStoreError("TRUST_STORE_INVALID")
    if doc["format_version"] != 1:
        raise TrustStoreError("TRUST_STORE_UNSUPPORTED_VERSION")
    if not _is_int(doc["serial"]) or doc["serial"] < 1 or not isinstance(doc["keys"], list) \
            or len(doc["keys"]) > MAX_TRUST_KEYS:
        raise TrustStoreError("TRUST_STORE_INVALID")
    required = {"key_id", "public_key", "status", "not_before", "not_after"}
    entries: dict[str, TrustEntry] = {}
    for item in doc["keys"]:
        if not isinstance(item, dict) or not required <= set(item) <= required | {"note"}:
            raise TrustStoreError("TRUST_STORE_INVALID")
        if not all(isinstance(item[k], str) for k in item):
            raise TrustStoreError("TRUST_STORE_INVALID")
        if item["status"] not in ("ACTIVE", "ROTATED", "REVOKED"):
            raise TrustStoreError("TRUST_STORE_INVALID")
        if not (_HEX64.match(item["key_id"]) and _HEX64.match(item["public_key"])
                and _TIME.match(item["not_before"]) and _TIME.match(item["not_after"])
                and item["not_before"] < item["not_after"]):
            raise TrustStoreError("TRUST_STORE_INVALID")
        public = bytes.fromhex(item["public_key"])
        if hashlib.sha256(public).hexdigest() != item["key_id"] or item["key_id"] in entries \
                or _is_small_order(public):
            raise TrustStoreError("TRUST_STORE_INVALID")
        entries[item["key_id"]] = TrustEntry(item["key_id"], item["public_key"], item["status"],
                                             item["not_before"], item["not_after"])
    return TrustStore(serial=doc["serial"], sha256=digest, entries=entries)


def trust_entry_for(signer: Signer, *, not_before: str, not_after: str, status: str = "ACTIVE") -> dict:
    """The trust-store ``keys`` element that would accept ``signer``. Operators and tests build
    trust stores from public keys with this; it carries no private material."""
    return {"key_id": signer.key_id, "public_key": signer.public_key_hex, "status": status,
            "not_before": not_before, "not_after": not_after}


def evaluate_trust(check: SignatureCheck, store: TrustStore | None, store_error: str | None,
                   as_of: str) -> tuple[str, list[str]]:
    """Pure derivation of ``signerTrust`` and its reason codes (design D5.7)."""
    if check.validity != "VALID":
        return "NOT_EVALUATED", []
    if store_error is not None:
        return "NOT_EVALUATED", [store_error]
    if store is None:
        return "NOT_EVALUATED", ["TRUST_STORE_NOT_CONFIGURED"]
    entry = store.entries.get(check.key_id or "")
    if entry is None or entry.public_key != check.public_key:
        return "UNTRUSTED_SIGNER", ["KEY_NOT_IN_TRUST_STORE"]
    if entry.status == "REVOKED":
        return "UNTRUSTED_SIGNER", ["KEY_REVOKED"]
    if as_of < entry.not_before:
        return "UNTRUSTED_SIGNER", ["KEY_NOT_YET_VALID"]
    if as_of > entry.not_after:
        return "UNTRUSTED_SIGNER", ["KEY_EXPIRED"]
    return "TRUSTED", (["KEY_ROTATED"] if entry.status == "ROTATED" else [])


_NOTE_ESTABLISHED = ("A trusted signer signed these exact manifest bytes and integrity is verified. "
                     "This does not show that the claim is true, that the signing time is trusted, "
                     "or that the key was never compromised.")


def _note(validity: str, trust: str, integrity_ok: bool) -> str:
    if validity == "UNSIGNED":
        return "This bundle is unsigned. Authenticity is not established."
    if validity == "INVALID":
        return "The signature is invalid. Authenticity is not established."
    if validity == "UNSUPPORTED_ALGORITHM":
        return "The signature uses an unsupported algorithm or protocol. Authenticity is not established."
    if trust == "NOT_EVALUATED":
        return ("The signature is valid, but the signer was not evaluated against a trust store. "
                "Authenticity is not established.")
    if trust == "UNTRUSTED_SIGNER":
        return ("The signature is valid, but this operator's trust store does not accept the signer. "
                "Authenticity is not established.")
    if not integrity_ok:
        return ("The signature is valid and the signer is trusted, but the integrity checks did not pass. "
                "Authenticity is not established.")
    return _NOTE_ESTABLISHED


def authenticity_report(check: SignatureCheck, trust: str, trust_reasons: list[str],
                        store: TrustStore | None, *, integrity_ok: bool, as_of: str) -> dict:
    """The contract 1.2.0 ``AuthenticityReport``. Fixed notes; no input text reaches the output."""
    reasons = list(check.reasons) + list(trust_reasons)
    established = check.validity == "VALID" and trust == "TRUSTED" and integrity_ok
    if check.validity == "VALID" and trust == "TRUSTED" and not integrity_ok:
        reasons.append("INTEGRITY_NOT_VERIFIED")
    valid = check.validity == "VALID"
    return {
        "status": "ESTABLISHED" if established else "NOT_ESTABLISHED",
        "note": _note(check.validity, trust, integrity_ok),
        "signatureValidity": check.validity,
        "signerTrust": trust,
        "reasonCodes": sorted(set(reasons)),
        "signer": {"keyId": check.key_id, "algorithm": ALGORITHM} if valid else None,
        "trustStore": ({"formatVersion": store.format_version, "serial": store.serial,
                        "sha256": store.sha256, "evaluatedAt": as_of}
                       if valid and store is not None else None),
    }


def trust_config_from_env(environ: Mapping[str, str] | None = None) -> tuple[str | None, str | None]:
    env = os.environ if environ is None else environ
    return (env.get("VK_TRUST_STORE_FILE") or None, env.get("VK_TRUST_STORE_SHA256") or None)


def unsigned_authenticity() -> dict:
    """Authenticity of a bundle nobody looked at: the same shape as any UNSIGNED result."""
    return authenticity_report(SignatureCheck("UNSIGNED", ("NO_ENVELOPE",)), "NOT_EVALUATED", [], None,
                               integrity_ok=False, as_of="")


def bundle_authenticity(path: str | os.PathLike, *, integrity_ok: bool, as_of: str,
                        trust_store_file: str | None = None, trust_store_sha256: str | None = None) -> dict:
    """Authenticity of a bundle file. ``as_of`` is ``YYYY-MM-DDTHH:MM:SSZ`` from the caller's clock.
    The trust store defaults to the operator's environment, never to anything in the bundle."""
    if trust_store_file is None:
        trust_store_file, env_pin = trust_config_from_env()
        if trust_store_sha256 is None:
            trust_store_sha256 = env_pin
    check = check_archive(path)
    store: TrustStore | None = None
    store_error: str | None = None
    if check.validity == "VALID" and trust_store_file:
        try:
            store = load_trust_store(trust_store_file, pinned_sha256=trust_store_sha256)
        except TrustStoreError as exc:
            store_error = exc.code
    trust, reasons = evaluate_trust(check, store, store_error, as_of)
    return authenticity_report(check, trust, reasons, store, integrity_ok=integrity_ok, as_of=as_of)
