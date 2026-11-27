"""Ed25519 signed verdict bundles (design D5, contract 1.2.0).

Integrity, reproducibility, signature validity and signer trust stay separate results.
Authenticity is ESTABLISHED only for VALID + TRUSTED + integrity VERIFIED, and never says the
claim is true. Verification is offline. Keys here are throwaway test keys.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pytest
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from hypothesis import given, settings, strategies as st

from security.helpers import (
    AS_OF, POSIX, NOT_AFTER, NOT_BEFORE, clock, grant_everyone, in_memory_zip, make_case, new_private_key,
    new_signer, receipt_registry, rezip, signed_and_unsigned, trust_store)
from jsonschema import ValidationError

from verdictkit import bundle as bundle_mod, cli
from verdictkit.bundle import (
    ReplayStatus, authenticity_dict, replay_bundle, verify_bundle_integrity, write_bundle)
from verdictkit.canonical import canonical_bytes, parse_canonical
from verdictkit.contract import CONTRACT_VERSION
from verdictkit.safeio import write_private_file
from verdictkit.signing import (
    SIGNATURE_MEMBER, SigningKeyError, TrustStoreError, load_signer, load_signer_from_env, load_trust_store,
    signer_from_private_key, trust_entry_for)

ROOT = Path(__file__).resolve().parents[2]
REPRODUCED = (ReplayStatus.REPRODUCED, ReplayStatus.REPRODUCED_ACROSS_ENV)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """One case written unsigned and signed, plus a trust store that accepts the signer."""
    tmp = tmp_path_factory.mktemp("signed")
    signed, unsigned, signer, key_file = signed_and_unsigned(tmp)
    good = trust_store(tmp / "trust-good.json", signer)
    return {"tmp": tmp, "signed": signed, "unsigned": unsigned, "signer": signer, "key_file": key_file,
            "good": good}


def auth(path, trust=None, *, as_of=AS_OF, **kw):
    result, _ = verify_bundle_integrity(path)
    return authenticity_dict(path, result, as_of=as_of, trust_store_file=str(trust) if trust else None, **kw)


# ------------------------------------------------------------------------ keys

def test_signing_is_off_when_unset_or_empty_and_on_when_configured(world):
    assert load_signer_from_env({}) is None
    assert load_signer_from_env({"VK_SIGNING_KEY_FILE": ""}) is None
    signer = load_signer_from_env({"VK_SIGNING_KEY_FILE": str(world["key_file"])})
    assert signer.key_id == world["signer"].key_id and len(signer.key_id) == 64


def test_the_signer_never_exposes_key_material_in_its_repr(world):
    text = repr(world["signer"]) + str(world["signer"])
    assert "Ed25519PrivateKey" not in text and "PRIVATE" not in text
    assert world["key_file"].read_bytes() not in text.encode()


def test_unusable_signing_keys_are_errors_with_fixed_codes_and_no_text(tmp_path):
    def code(path) -> str:
        with pytest.raises(SigningKeyError) as err:
            load_signer(path)
        assert str(path) not in str(err.value) and "BEGIN" not in str(err.value)
        return err.value.code

    def private(name: str, data: bytes) -> Path:
        # Private (0600 / private ACL) files, so the content check, not the permission check, decides.
        path = tmp_path / name
        write_private_file(path, data)
        return path

    assert code(tmp_path / "absent.pem") == "SIGNING_KEY_MISSING"
    assert code(tmp_path) == "SIGNING_KEY_UNREADABLE"  # a directory
    assert code(private("empty.pem", b"")) == "SIGNING_KEY_UNSUPPORTED"
    rsa_pem = rsa.generate_private_key(65537, 2048).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    assert code(private("rsa.pem", rsa_pem)) == "SIGNING_KEY_UNSUPPORTED"
    encrypted_pem = new_private_key().private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(b"pw"))
    assert code(private("enc.pem", encrypted_pem)) == "SIGNING_KEY_UNSUPPORTED"
    assert code(private("garbage.pem", b"not a key")) == "SIGNING_KEY_UNSUPPORTED"
    assert code(private("big.pem", b"x" * 5000)) == "SIGNING_KEY_UNREADABLE"
    with pytest.raises(SigningKeyError):
        load_signer_from_env({"VK_SIGNING_KEY_FILE": str(tmp_path / "absent.pem")})  # never a silent downgrade


@pytest.mark.skipif(not POSIX, reason="POSIX mode bits and symlinks")
def test_signing_key_must_be_private_and_not_a_link(tmp_path):
    signer, path = new_signer(tmp_path)
    path.chmod(0o644)
    with pytest.raises(SigningKeyError) as err:
        load_signer(path)
    assert err.value.code == "SIGNING_KEY_PERMISSIONS"
    path.chmod(0o600)
    link = tmp_path / "link.pem"
    link.symlink_to(path)
    with pytest.raises(SigningKeyError) as err:
        load_signer(link)
    assert err.value.code == "SIGNING_KEY_UNREADABLE"
    assert load_signer(path).key_id == signer.key_id


@pytest.mark.skipif(POSIX, reason="Windows access-control check")
def test_signing_key_readable_by_everyone_is_refused_on_windows(tmp_path):
    signer, path = new_signer(tmp_path)
    assert load_signer(path).key_id == signer.key_id
    grant_everyone(path)
    with pytest.raises(SigningKeyError) as err:
        load_signer(path)
    assert err.value.code == "SIGNING_KEY_PERMISSIONS"


# ------------------------------------------------------- round trip and compatibility

def test_signed_bundle_verifies_offline_and_unsigned_stays_unsigned(world):
    a = auth(world["signed"], world["good"])
    assert (a["signatureValidity"], a["signerTrust"], a["status"]) == ("VALID", "TRUSTED", "ESTABLISHED")
    assert a["signer"] == {"keyId": world["signer"].key_id, "algorithm": "ed25519"}
    assert a["trustStore"]["serial"] == 1 and a["trustStore"]["evaluatedAt"] == AS_OF
    assert a["reasonCodes"] == [] and "does not show that the claim is true" in a["note"]
    u = auth(world["unsigned"], world["good"])
    assert (u["signatureValidity"], u["signerTrust"], u["status"]) == ("UNSIGNED", "NOT_EVALUATED", "NOT_ESTABLISHED")
    assert u["signer"] is None and u["trustStore"] is None and u["reasonCodes"] == ["NO_ENVELOPE"]
    assert "unsigned" in u["note"].lower()


def test_signing_adds_exactly_one_member_and_changes_no_verdict_input(world):
    with zipfile.ZipFile(world["signed"]) as s, zipfile.ZipFile(world["unsigned"]) as u:
        assert sorted(s.namelist()) == sorted(u.namelist() + [SIGNATURE_MEMBER])
        for name in u.namelist():
            assert s.read(name) == u.read(name), f"{name} must be byte-identical"
        manifest = parse_canonical(s.read("manifest.json"))
        assert SIGNATURE_MEMBER not in manifest["files"], "the envelope is never listed in the manifest"
        assert parse_canonical(s.read("verdict/verdict.json"))["verdict_hash"] == manifest["verdict_hash"]


def test_signed_bundle_passes_integrity_and_replays_to_the_same_verdict_hash(world, tmp_path):
    for key in ("signed", "unsigned"):
        result, _ = verify_bundle_integrity(world[key])
        assert result.ok, result.notes
    signed = replay_bundle(world["signed"], registry=receipt_registry(), workdir=tmp_path / "s")
    unsigned = replay_bundle(world["unsigned"], registry=receipt_registry(), workdir=tmp_path / "u")
    assert signed.status in REPRODUCED and unsigned.status in REPRODUCED
    assert signed.original_verdict_hash == unsigned.original_verdict_hash == signed.replayed_verdict_hash


def test_signing_is_deterministic_for_one_case_clock_and_key(world, tmp_path):
    case = make_case(tmp_path / "w")
    first = write_bundle(case, tmp_path / "a.vkb", clock=clock, signer=world["signer"])
    second = write_bundle(case, tmp_path / "b.vkb", clock=clock, signer=world["signer"])
    assert first.read_bytes() == second.read_bytes()


def test_the_committed_golden_bundle_is_a_historical_unsigned_bundle_that_replays(tmp_path):
    from verdictkit.cli import _load_registry
    golden = ROOT / "examples/stub_claimtype/golden.vkb"
    report = replay_bundle(golden, registry=_load_registry(), workdir=tmp_path)
    assert report.status in REPRODUCED, report.notes
    result, _ = verify_bundle_integrity(golden)
    a = authenticity_dict(golden, result, as_of=AS_OF)
    assert (a["signatureValidity"], a["status"]) == ("UNSIGNED", "NOT_ESTABLISHED") and result.ok


def test_failed_write_leaves_no_partial_bundle_and_no_temporary_file(world, tmp_path, monkeypatch):
    case = make_case(tmp_path / "w")

    def boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(bundle_mod.os, "replace", boom)
    with pytest.raises(OSError):
        write_bundle(case, tmp_path / "out" / "x.vkb", clock=clock, signer=world["signer"])
    assert list((tmp_path / "out").iterdir()) == []


# --------------------------------------------------------------------- trust matrix

def test_no_trust_store_means_trust_is_not_evaluated(world):
    a = auth(world["signed"])
    assert (a["signatureValidity"], a["signerTrust"], a["status"]) == ("VALID", "NOT_EVALUATED", "NOT_ESTABLISHED")
    assert a["reasonCodes"] == ["TRUST_STORE_NOT_CONFIGURED"] and a["trustStore"] is None


def test_unknown_signer_is_distinguished_from_a_trusted_one(world, tmp_path):
    other = signer_from_private_key(new_private_key())
    store = trust_store(tmp_path / "other.json", other, serial=4)
    a = auth(world["signed"], store)
    assert (a["signatureValidity"], a["signerTrust"], a["status"]) == ("VALID", "UNTRUSTED_SIGNER", "NOT_ESTABLISHED")
    assert a["reasonCodes"] == ["KEY_NOT_IN_TRUST_STORE"] and a["trustStore"]["serial"] == 4


def test_embedding_your_own_key_does_not_make_you_trusted(world, tmp_path):
    """An attacker re-signs a bundle with their own key and embeds it: VALID, never TRUSTED."""
    attacker = signer_from_private_key(new_private_key())
    case = make_case(tmp_path / "w")
    forged = write_bundle(case, tmp_path / "forged.vkb", clock=clock, signer=attacker)
    a = auth(forged, world["good"])
    assert (a["signatureValidity"], a["signerTrust"], a["status"]) == ("VALID", "UNTRUSTED_SIGNER", "NOT_ESTABLISHED")
    assert a["signer"]["keyId"] == attacker.key_id != world["signer"].key_id


@pytest.mark.parametrize("status, as_of, trust, reasons", [
    ("REVOKED", AS_OF, "UNTRUSTED_SIGNER", ["KEY_REVOKED"]),
    ("ACTIVE", "2025-12-31T23:59:59Z", "UNTRUSTED_SIGNER", ["KEY_NOT_YET_VALID"]),
    ("ACTIVE", "2027-01-01T00:00:01Z", "UNTRUSTED_SIGNER", ["KEY_EXPIRED"]),
    ("ACTIVE", NOT_BEFORE, "TRUSTED", []),          # both ends of the interval are inclusive
    ("ACTIVE", NOT_AFTER, "TRUSTED", []),
    ("ROTATED", AS_OF, "TRUSTED", ["KEY_ROTATED"]),
    ("ROTATED", "2027-06-01T00:00:00Z", "UNTRUSTED_SIGNER", ["KEY_EXPIRED"]),
])
def test_trust_follows_status_and_the_verifiers_clock(world, tmp_path, status, as_of, trust, reasons):
    entry = trust_entry_for(world["signer"], not_before=NOT_BEFORE, not_after=NOT_AFTER, status=status)
    a = auth(world["signed"], trust_store(tmp_path / "t.json", entry), as_of=as_of)
    assert a["signatureValidity"] == "VALID" and a["signerTrust"] == trust and a["reasonCodes"] == reasons
    assert a["status"] == ("ESTABLISHED" if trust == "TRUSTED" else "NOT_ESTABLISHED")


def test_the_manifest_clock_cannot_extend_trust(world, tmp_path):
    """written_at is chosen by the signer; only the verifier's as_of decides key validity."""
    manifest = parse_canonical(zipfile.ZipFile(world["signed"]).read("manifest.json"))
    assert manifest["written_at"] < "2026-12-31T00:00:00Z"
    entry = trust_entry_for(world["signer"], not_before=NOT_BEFORE, not_after="2026-12-01T00:00:00Z")
    a = auth(world["signed"], trust_store(tmp_path / "t.json", entry), as_of="2027-03-01T00:00:00Z")
    assert a["signerTrust"] == "UNTRUSTED_SIGNER" and a["reasonCodes"] == ["KEY_EXPIRED"]


def test_a_pinned_trust_store_hash_is_enforced(world, tmp_path):
    import hashlib
    digest = hashlib.sha256(world["good"].read_bytes()).hexdigest()
    ok = auth(world["signed"], world["good"], trust_store_sha256=digest)
    assert ok["status"] == "ESTABLISHED" and ok["trustStore"]["sha256"] == digest
    bad = auth(world["signed"], world["good"], trust_store_sha256="0" * 64)
    assert (bad["signerTrust"], bad["status"], bad["reasonCodes"]) == (
        "NOT_EVALUATED", "NOT_ESTABLISHED", ["TRUST_STORE_HASH_MISMATCH"])


def test_a_bundle_cannot_choose_the_trust_store_but_the_environment_can(world, monkeypatch):
    monkeypatch.setenv("VK_TRUST_STORE_FILE", str(world["good"]))
    result, _ = verify_bundle_integrity(world["signed"])
    assert authenticity_dict(world["signed"], result, as_of=AS_OF)["status"] == "ESTABLISHED"
    monkeypatch.delenv("VK_TRUST_STORE_FILE")
    assert authenticity_dict(world["signed"], result, as_of=AS_OF)["status"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("text, code", [
    ("", "TRUST_STORE_INVALID"),
    ("not json", "TRUST_STORE_INVALID"),
    ('{"format":"vk-trust-store","format_version":1,"serial":1,"keys":[],"keys":[]}', "TRUST_STORE_INVALID"),
    ('{"format":"vk-trust-store","format_version":1,"serial":1.5,"keys":[]}', "TRUST_STORE_INVALID"),
    ('{"format":"vk-trust-store","format_version":1,"serial":0,"keys":[]}', "TRUST_STORE_INVALID"),
    ('{"format":"vk-trust-store","format_version":1,"serial":true,"keys":[]}', "TRUST_STORE_INVALID"),
    ('{"format":"other","format_version":1,"serial":1,"keys":[]}', "TRUST_STORE_INVALID"),
    ('{"format":"vk-trust-store","format_version":1,"serial":1,"keys":[],"extra":1}', "TRUST_STORE_INVALID"),
    ('{"format":"vk-trust-store","format_version":2,"serial":1,"keys":[]}', "TRUST_STORE_UNSUPPORTED_VERSION"),
    ('{"format":"vk-trust-store","format_version":1,"serial":1,"keys":[{"key_id":"x"}]}', "TRUST_STORE_INVALID"),
])
def test_malformed_trust_stores_are_unusable_and_never_trust_anyone(world, tmp_path, text, code):
    path = tmp_path / "t.json"
    path.write_text(text)
    with pytest.raises(TrustStoreError) as err:
        load_trust_store(path)
    assert err.value.code == code
    a = auth(world["signed"], path)
    assert a["signerTrust"] == "NOT_EVALUATED" and a["status"] == "NOT_ESTABLISHED" and a["reasonCodes"] == [code]


def test_trust_store_entries_are_checked_against_their_keys(world, tmp_path):
    signer = world["signer"]
    good = trust_entry_for(signer, not_before=NOT_BEFORE, not_after=NOT_AFTER)
    other = signer_from_private_key(new_private_key())
    cases = {
        "key_id does not hash the key": dict(good, key_id=other.key_id),
        "unknown status": dict(good, status="TRUSTED"),
        "inverted interval": dict(good, not_before=NOT_AFTER, not_after=NOT_BEFORE),
        "bad time format": dict(good, not_before="2026-01-01"),
        "unknown field": dict(good, surprise="x"),
        "small-order key": {"key_id": __import__("hashlib").sha256(bytes(32)).hexdigest(),
                            "public_key": "00" * 32, "status": "ACTIVE", "not_before": NOT_BEFORE,
                            "not_after": NOT_AFTER},
    }
    for label, entry in cases.items():
        with pytest.raises(TrustStoreError):
            load_trust_store(trust_store(tmp_path / "t.json", entry))
        assert label
    with pytest.raises(TrustStoreError):  # duplicate key_id
        load_trust_store(trust_store(tmp_path / "t.json", good, good))
    assert load_trust_store(trust_store(tmp_path / "t.json", dict(good, note="rotation 2026"))).serial == 1


# ------------------------------------------------------------------- tamper matrix

def test_member_tamper_keeps_the_signature_valid_but_integrity_fails_and_authenticity_is_denied(world, tmp_path):
    def flip(name, data):
        return data.replace(b"CONSISTENT", b"CONTRADICTED") if name == "verdict/verdict.json" else data
    path = rezip(world["signed"], tmp_path / "t.vkb", flip)
    result, _ = verify_bundle_integrity(path)
    a = auth(path, world["good"])
    assert not result.ok
    assert (a["signatureValidity"], a["signerTrust"], a["status"]) == ("VALID", "TRUSTED", "NOT_ESTABLISHED")
    assert a["reasonCodes"] == ["INTEGRITY_NOT_VERIFIED"]


def test_manifest_tamper_is_caught_by_the_signature_even_though_integrity_passes(world, tmp_path):
    """The manifest is not self-covered, so integrity alone misses this. The signature does not."""
    def edit(name, data):
        return data.replace(b'"case_id":"case-0001"', b'"case_id":"case-0002"') if name == "manifest.json" else data
    path = rezip(world["signed"], tmp_path / "t.vkb", edit)
    result, _ = verify_bundle_integrity(path)
    a = auth(path, world["good"])
    assert result.ok, "integrity of listed files still passes"
    assert (a["signatureValidity"], a["status"], a["reasonCodes"]) == (
        "INVALID", "NOT_ESTABLISHED", ["MANIFEST_HASH_MISMATCH"])


def _envelope(path) -> dict:
    return json.loads(zipfile.ZipFile(path).read(SIGNATURE_MEMBER))


def _with_envelope(src, dst, mutate_envelope):
    def edit(name, data):
        if name != SIGNATURE_MEMBER:
            return data
        out = mutate_envelope(json.loads(data))
        return out if isinstance(out, bytes) else canonical_bytes(out)
    return rezip(src, dst, edit)


@pytest.mark.parametrize("label, mutate, validity, reason", [
    ("flipped signature", lambda e: {**e, "signature": ("0" if e["signature"][0] != "0" else "1") + e["signature"][1:]},
     "INVALID", "SIGNATURE_MISMATCH"),
    ("short signature", lambda e: {**e, "signature": e["signature"][:-2]}, "INVALID", "SIGNATURE_MALFORMED"),
    ("key_id of another key", lambda e: {**e, "key_id": "ab" * 32}, "INVALID", "KEY_ID_MISMATCH"),
    ("public key replaced", lambda e: {**e, "public_key": "ab" * 32}, "INVALID", "KEY_ID_MISMATCH"),
    ("other manifest hash", lambda e: {**e, "manifest_sha256": "cd" * 32}, "INVALID", "MANIFEST_HASH_MISMATCH"),
    ("algorithm", lambda e: {**e, "alg": "ed448"}, "UNSUPPORTED_ALGORITHM", "ALGORITHM_UNSUPPORTED"),
    ("protocol", lambda e: {**e, "protocol": "other"}, "UNSUPPORTED_ALGORITHM", "PROTOCOL_UNSUPPORTED"),
    ("protocol version", lambda e: {**e, "protocol_version": "2"}, "UNSUPPORTED_ALGORITHM", "PROTOCOL_UNSUPPORTED"),
    ("bundle format", lambda e: {**e, "bundle_format": "vkb/2"}, "UNSUPPORTED_ALGORITHM", "BUNDLE_FORMAT_UNSUPPORTED"),
    ("extra field", lambda e: {**e, "extra": "x"}, "INVALID", "ENVELOPE_MALFORMED"),
    ("missing field", lambda e: {k: v for k, v in e.items() if k != "alg"}, "INVALID", "ENVELOPE_MALFORMED"),
    ("non-string field", lambda e: {**e, "protocol_version": 1}, "INVALID", "ENVELOPE_MALFORMED"),
    ("upper-case hex", lambda e: {**e, "key_id": e["key_id"].upper()}, "INVALID", "ENVELOPE_MALFORMED"),
    ("not canonical", lambda e: json.dumps(e, indent=2).encode(), "INVALID", "ENVELOPE_NON_CANONICAL"),
    ("not json", lambda e: b"\x00\x01 not json", "INVALID", "ENVELOPE_MALFORMED"),
    ("oversized", lambda e: canonical_bytes({**e, "pad": "x" * 3000}), "INVALID", "ENVELOPE_TOO_LARGE"),
])
def test_envelope_attacks_never_validate(world, tmp_path, label, mutate, validity, reason):
    path = _with_envelope(world["signed"], tmp_path / "t.vkb", mutate)
    a = auth(path, world["good"])
    assert (a["signatureValidity"], a["reasonCodes"]) == (validity, [reason]), label
    assert a["status"] == "NOT_ESTABLISHED" and a["signer"] is None and a["signerTrust"] == "NOT_EVALUATED"


def test_small_order_public_keys_cannot_validate_a_universal_signature(world, tmp_path):
    import hashlib
    from verdictkit.signing import BUNDLE_FORMAT, PROTOCOL, PROTOCOL_VERSION
    manifest = zipfile.ZipFile(world["signed"]).read("manifest.json")
    for public in ("01" + "00" * 31, "00" * 32, "ec" + "ff" * 30 + "7f"):
        envelope = {"alg": "ed25519", "bundle_format": BUNDLE_FORMAT, "key_id": hashlib.sha256(bytes.fromhex(public)).hexdigest(),
                    "manifest_sha256": hashlib.sha256(manifest).hexdigest(), "protocol": PROTOCOL,
                    "protocol_version": PROTOCOL_VERSION, "public_key": public,
                    "signature": ("01" + "00" * 31) + "00" * 32}  # R = identity, S = 0
        path = _with_envelope(world["signed"], tmp_path / "t.vkb", lambda _e, env=envelope: env)
        a = auth(path, world["good"])
        assert (a["signatureValidity"], a["reasonCodes"]) == ("INVALID", ["PUBLIC_KEY_SMALL_ORDER"]), public


def test_signature_member_name_games_are_invalid(world, tmp_path):
    original = zipfile.ZipFile(world["signed"])
    members = {n: original.read(n) for n in original.namelist()}
    envelope = members[SIGNATURE_MEMBER]

    def build(extra: dict[str, bytes], *, drop_envelope=False, manifest=None) -> Path:
        built = {n: d for n, d in members.items() if not (drop_envelope and n == SIGNATURE_MEMBER)}
        if manifest is not None:
            built["manifest.json"] = manifest
        built.update(extra)
        path = tmp_path / f"n{len(list(tmp_path.iterdir()))}.vkb"
        path.write_bytes(in_memory_zip(built))
        return path

    # zipfile rewrites os.sep when WRITING on Windows, so the raw backslash name is made by
    # patching same-length bytes. Reading must then judge the raw name identically on both hosts.
    backslash = build({"signature|envelope.json": envelope})
    backslash.write_bytes(backslash.read_bytes().replace(b"signature|envelope.json", b"signature\\envelope.json"))
    for label, path in {
        "second reserved member": build({"signature/other.json": envelope}),
        "case variant": build({"Signature/envelope.json": envelope}),
        "full-width variant": build({"\uff53ignature/envelope.json": envelope}),
        "backslash variant": backslash,
    }.items():
        a = auth(path, world["good"])
        assert (a["signatureValidity"], a["status"]) == ("INVALID", "NOT_ESTABLISHED"), label
        assert a["reasonCodes"] == ["UNKNOWN_SIGNATURE_MEMBER"], label

    listed = parse_canonical(members["manifest.json"])
    listed["files"][SIGNATURE_MEMBER] = "0" * 64
    a = auth(build({}, manifest=canonical_bytes(listed)), world["good"])
    assert a["reasonCodes"] == ["ENVELOPE_LISTED_IN_MANIFEST"] and a["signatureValidity"] == "INVALID"

    # A duplicate envelope entry cannot be written with zipfile's public API without a warning.
    duplicate = tmp_path / "dup.vkb"
    with pytest.warns(UserWarning):
        with zipfile.ZipFile(duplicate, "w") as zf:
            for n, d in members.items():
                zf.writestr(n, d)
            zf.writestr(SIGNATURE_MEMBER, envelope)
    a = auth(duplicate, world["good"])
    assert (a["signatureValidity"], a["reasonCodes"]) == ("INVALID", ["DUPLICATE_ARCHIVE_PATH"])


def test_unreadable_archives_are_unsigned_not_exceptions(world, tmp_path):
    for data in (b"", b"not a zip", b"PK\x03\x04" + b"x" * 100):
        path = tmp_path / "bad.vkb"
        path.write_bytes(data)
        result, _ = verify_bundle_integrity(path)
        a = authenticity_dict(path, result, as_of=AS_OF)
        assert not result.ok
        assert (a["signatureValidity"], a["status"], a["reasonCodes"]) == (
            "UNSIGNED", "NOT_ESTABLISHED", ["ARCHIVE_UNREADABLE"])
    assert authenticity_dict(tmp_path / "missing.vkb", result, as_of=AS_OF)["signatureValidity"] == "UNSIGNED"


@settings(max_examples=60, deadline=None)
@given(st.data())
def test_no_change_to_any_signed_member_ever_yields_established(world, data):
    """Property: with the signer trusted, flipping any bit of any member's content (manifest,
    listed member or envelope) never leaves authenticity ESTABLISHED. Container bytes (zip
    timestamps and headers) are outside the signed object and are not mutated here."""
    tmp = world["tmp"] / "prop"
    tmp.mkdir(exist_ok=True)
    names = sorted(zipfile.ZipFile(world["signed"]).namelist())
    name = data.draw(st.sampled_from(names), label="member")
    original = zipfile.ZipFile(world["signed"]).read(name)
    index = data.draw(st.integers(0, len(original) - 1), label="byte")
    bit = data.draw(st.integers(0, 7), label="bit")

    def flip(n, content):
        if n != name:
            return content
        mutated = bytearray(content)
        mutated[index] ^= 1 << bit
        return bytes(mutated)

    path = rezip(world["signed"], tmp / "mutant.vkb", flip)
    a = auth(path, world["good"])
    assert a["status"] == "NOT_ESTABLISHED", (name, index, bit, a["reasonCodes"])


# ----------------------------------------------------------------------------- CLI

CLAIM = str(ROOT / "examples/stub_claimtype/claim.json")


@pytest.fixture()
def cli_env(monkeypatch):
    for name in ("VK_EXAMINER_SOCKET", "VK_VAULT_KEY", "VK_VAULT_KEY_FILE", "VK_SIGNING_KEY_FILE",
                 "VK_TRUST_STORE_FILE", "VK_TRUST_STORE_SHA256", "VK_EVIDENCE_DIR"):
        monkeypatch.delenv(name, raising=False)
    # The fixture bundles use the core test claim type; the stub type arrives by entry point.
    monkeypatch.setenv("VK_CLAIM_TYPES", "contract.receipt_claimtype:ReceiptClaimType")
    return monkeypatch


def test_cli_run_signs_only_when_a_key_is_configured(cli_env, tmp_path, capsys):
    signer, key_file = new_signer(tmp_path)
    assert cli.main(["run", CLAIM, "--out", str(tmp_path / "plain.vkb")]) == 0
    assert "signed:        no" in capsys.readouterr().out
    cli_env.setenv("VK_SIGNING_KEY_FILE", str(key_file))
    assert cli.main(["run", CLAIM, "--out", str(tmp_path / "signed.vkb")]) == 0
    captured = capsys.readouterr()
    assert f"signed:        yes (ed25519, key_id {signer.key_id})" in captured.out
    assert "UNENFORCED" in captured.err, "signing under UNENFORCED isolation must warn"
    assert auth(tmp_path / "signed.vkb", trust_store(tmp_path / "t.json", signer))["status"] == "ESTABLISHED"


def test_cli_run_never_downgrades_to_unsigned_when_the_key_is_unusable(cli_env, tmp_path, capsys):
    cli_env.setenv("VK_SIGNING_KEY_FILE", str(tmp_path / "absent.pem"))
    out = tmp_path / "x.vkb"
    assert cli.main(["run", CLAIM, "--out", str(out)]) == 1
    err = capsys.readouterr().err
    assert "SIGNING_KEY_MISSING" in err and str(tmp_path) not in err
    assert not out.exists() and list(tmp_path.glob("*.tmp")) == []


def test_cli_verify_exit_codes_and_separate_results(cli_env, world, capsys):
    good, signed, unsigned = str(world["good"]), str(world["signed"]), str(world["unsigned"])
    assert cli.main(["verify", signed, "--trust-store", good, "--as-of", AS_OF]) == 0
    out = capsys.readouterr().out
    for line in ("integrity:         VERIFIED", "signature:         VALID", "signer trust:      TRUSTED",
                 "authenticity:      ESTABLISHED", f"signer key_id:   {world['signer'].key_id}"):
        assert line in out, line
    assert cli.main(["verify", signed, "--as-of", AS_OF]) == 1
    assert "signer trust:      NOT_EVALUATED" in capsys.readouterr().out
    assert cli.main(["verify", unsigned, "--trust-store", good]) == 1
    assert "signature:         UNSIGNED" in capsys.readouterr().out
    assert cli.main(["verify", signed, "--trust-store", good, "--as-of", "2030-01-01T00:00:00Z"]) == 1
    assert "KEY_EXPIRED" in capsys.readouterr().out
    assert cli.main(["verify", signed, "--as-of", "yesterday"]) == 2
    assert cli.main(["verify", str(world["tmp"] / "absent.vkb")]) == 1


def test_cli_verify_json_is_machine_readable(cli_env, world, capsys):
    assert cli.main(["verify", str(world["signed"]), "--trust-store", str(world["good"]), "--as-of", AS_OF,
                     "--json"]) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["integrity"]["status"] == "VERIFIED"
    assert set(body["authenticity"]) == {"status", "note", "signatureValidity", "signerTrust", "reasonCodes",
                                         "signer", "trustStore"}


def test_cli_verify_honours_the_operators_environment_for_trust(cli_env, world, capsys):
    cli_env.setenv("VK_TRUST_STORE_FILE", str(world["good"]))
    assert cli.main(["verify", str(world["signed"]), "--as-of", AS_OF]) == 0
    capsys.readouterr()


def test_cli_replay_reports_all_results_and_keeps_its_exit_rule(cli_env, world, tmp_path, capsys):
    good = str(world["good"])
    assert cli.main(["replay", str(world["signed"]), "--trust-store", good, "--as-of", AS_OF]) == 0
    out = capsys.readouterr().out
    assert re.search(r"reproducibility:\s+REPRODUCED", out) and "authenticity:      ESTABLISHED" in out
    assert cli.main(["replay", str(world["unsigned"])]) == 0  # historical bundles still replay
    unsigned_out = capsys.readouterr().out
    assert "signature:         UNSIGNED" in unsigned_out and "authenticity:      NOT_ESTABLISHED" in unsigned_out
    bad = rezip(world["signed"], tmp_path / "bad.vkb",
                lambda n, d: d.replace(b"CONSISTENT", b"CONTRADICTED") if n == "verdict/verdict.json" else d)
    assert cli.main(["replay", str(bad), "--trust-store", good, "--json"]) == 1
    body = json.loads(capsys.readouterr().out)
    assert body["integrity"]["status"] == "FAILED" and body["authenticity"]["status"] == "NOT_ESTABLISHED"


# --------------------------------------------------------------- contract and surfaces

def test_contract_version_is_defined_once_and_every_surface_agrees():
    spec = yaml.safe_load((ROOT / "api/openapi.yaml").read_text(encoding="utf-8"))
    assert spec["info"]["version"] == CONTRACT_VERSION == spec["components"]["schemas"]["ContractVersion"]["const"]
    stale = []
    for path in sorted((ROOT / "api/examples").glob("*.json")):
        for match in re.finditer(r'"contractVersion":\s*"([^"]+)"', path.read_text(encoding="utf-8")):
            if match.group(1) != CONTRACT_VERSION:
                stale.append(path.name)
    assert stale == []


@pytest.mark.skipif(not (ROOT / "ui-kit/src/api.ts").exists(), reason="UI sources are not part of the container image")
def test_ui_surfaces_pin_the_same_contract_version():
    assert re.search(rf'CONTRACT_VERSION = "{re.escape(CONTRACT_VERSION)}"', (ROOT / "ui-kit/src/api.ts").read_text(encoding="utf-8"))
    assert f"const CONTRACT = '{CONTRACT_VERSION}'" in (ROOT / "ui/judge/app.js").read_text(encoding="utf-8")
    assert f"CONTRACT {CONTRACT_VERSION}" in (ROOT / "ui/judge/index.html").read_text(encoding="utf-8")


def test_server_presenter_and_mcp_use_the_single_constant():
    from verdictkit.api import presenter, server
    assert server.VERSION == presenter.CONTRACT_VERSION == CONTRACT_VERSION


def test_openapi_authenticity_schema_accepts_signed_and_unsigned_and_rejects_forged_status(world):
    from jsonschema import Draft202012Validator
    spec = yaml.safe_load((ROOT / "api/openapi.yaml").read_text(encoding="utf-8"))
    validator = Draft202012Validator({**spec, "$ref": "#/components/schemas/AuthenticityReport"})
    for path, trust in ((world["signed"], world["good"]), (world["signed"], None), (world["unsigned"], None)):
        validator.validate(auth(path, trust))
    forged = dict(auth(world["signed"], world["good"]), status="VERIFIED")
    with pytest.raises(ValidationError):
        validator.validate(forged)
    with pytest.raises(ValidationError):
        validator.validate({**auth(world["signed"], world["good"]), "unexpected": 1})


def test_mcp_tools_report_the_new_authenticity_fields(world, tmp_path, monkeypatch):
    from verdictkit import mcp_server
    monkeypatch.setenv("VK_MCP_BUNDLE_ROOTS", str(world["tmp"]))
    monkeypatch.setattr(mcp_server, "_ROOTS_CACHE", None)
    monkeypatch.setenv("VK_TRUST_STORE_FILE", str(world["good"]))
    replay = mcp_server.replay_bundle(str(world["signed"]))
    assert replay["contractVersion"] == CONTRACT_VERSION
    assert replay["authenticity"]["signatureValidity"] == "VALID"
    explained = mcp_server.explain_verdict(str(world["signed"]))
    assert explained["authenticity"]["signerTrust"] == "TRUSTED"
    assert re.search(r"Authenticity: \w+ \(signature: VALID; signer trust: (TRUSTED|NOT_EVALUATED)\)", explained["summary"])
    plain = mcp_server.explain_verdict(str(world["unsigned"]))
    assert "NOT_ESTABLISHED" in plain["summary"] and "signature: UNSIGNED" in plain["summary"]
