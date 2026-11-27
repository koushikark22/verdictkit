"""Demonstration verification lab (opt-in; Batch 2).

Enabled only when ``VK_DEMO_LAB_DIR`` names a directory of *public* verifier profiles written by
``scripts/demo_signer.py``. The lab never reads a private key. It adds no verification logic of its
own: every result comes from the same ``replay_bundle`` / ``authenticity_dict`` code that
``POST /replays`` uses. What the lab adds is (a) three named verifier trust stores, so one signed
bundle can be checked by a verifier that trusts, does not know, or has revoked its signer, and
(b) two single-defect bundle transforms (signature removed, one verdict character changed).

Trust stays the verifier's configuration: a client names a scenario, never a key, and nothing
embedded in an uploaded bundle is ever added to a trust store. The lab has no "no trust store"
scenario on purpose: that case is what the CLI's ``verify`` reports when ``--trust-store`` is omitted
(``verdictkit verify BUNDLE`` exits 1 with ``signer trust: NOT_EVALUATED``).

Opt-in and documented in docs/DEMO_LAB.md; it is not part of API contract 1.2.0.
"""
from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

from verdictkit.bundle import MAX_BUNDLE_ENTRIES, MAX_BUNDLE_UNCOMPRESSED, MAX_ENTRY_UNCOMPRESSED
from verdictkit.signing import SIGNATURE_MEMBER, TrustStoreError, load_trust_store

LAB_ENV = "VK_DEMO_LAB_DIR"
NOTICE = ("DEMONSTRATION SIGNER: a disposable Ed25519 key created when this server started. Its private "
          "half stays inside the server and is never shown, returned or logged. It proves nothing about "
          "any real person or organisation.")

#: profile id -> (file name, label, plain-language description of the verifier's configuration)
PROFILES = {
    "trusted": ("trust-trusted.json", "Verifier trusts the demonstration signer",
                "The verifier's trust store lists the demonstration signer's public key as ACTIVE."),
    "unknown": ("trust-unknown.json", "Verifier has never heard of the signer",
                "The verifier's trust store holds one unrelated public key and not the demonstration signer's."),
    "revoked": ("trust-revoked.json", "Verifier has revoked the signer",
                "The verifier's trust store lists the demonstration signer's public key as REVOKED."),
}


@dataclass(frozen=True)
class Scenario:
    id: str
    label: str
    profile: str
    transform: str          # "none" | "strip-signature" | "tamper-verdict"
    setup: str              # what is done to the bundle and the verifier; never a statement of the result


SCENARIOS = (
    Scenario("trusted-signer", "Trusted signer", "trusted", "none",
             "The bundle exactly as the server wrote it, checked by a verifier that lists the signer's key as ACTIVE."),
    Scenario("unknown-signer", "Unknown signer", "unknown", "none",
             "The same bundle, checked by a verifier whose trust store has never enrolled this signer."),
    Scenario("revoked-signer", "Revoked signer", "revoked", "none",
             "The same bundle, checked by a verifier whose trust store lists the signer's key as REVOKED."),
    Scenario("unsigned-historical", "Unsigned historical bundle", "trusted", "strip-signature",
             "The signature member is removed. A bundle written before signing existed looks the same."),
    Scenario("tampered-bundle", "Tampered bundle", "trusted", "tamper-verdict",
             "After signing, one character inside the sealed verdict record is changed. "
             "The manifest and the signature are left exactly as they were."),
)
_BY_ID = {s.id: s for s in SCENARIOS}


class LabError(ValueError):
    """A scenario cannot be applied to this upload. ``code`` is stable; ``message`` is fixed text."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def scenario(scenario_id: str) -> Scenario | None:
    return _BY_ID.get(scenario_id)


@dataclass(frozen=True)
class Profile:
    id: str
    label: str
    description: str
    path: str
    sha256: str
    serial: int
    keys: tuple[tuple[str, str], ...]   # (key_id, status)

    def public(self) -> dict:
        return {"id": self.id, "label": self.label, "description": self.description,
                "trustStore": {"serial": self.serial, "sha256": self.sha256,
                               "keys": [{"keyId": k, "status": s} for k, s in self.keys]}}


@dataclass(frozen=True)
class Lab:
    directory: Path
    profiles: dict[str, Profile]


def load_lab(directory: str) -> Lab:
    """Read the three verifier profiles. Anything missing or invalid stops the server start."""
    base = Path(directory)
    profiles: dict[str, Profile] = {}
    for pid, (name, label, description) in PROFILES.items():
        path = base / name
        try:
            store = load_trust_store(path)
        except TrustStoreError as exc:
            raise RuntimeError(f"demo lab profile {pid} unusable ({exc.code})") from None
        profiles[pid] = Profile(pid, label, description, str(path), store.sha256, store.serial,
                                tuple((e.key_id, e.status) for e in store.entries.values()))
    return Lab(base, profiles)


def lab_from_env() -> Lab | None:
    directory = os.environ.get(LAB_ENV, "")
    return load_lab(directory) if directory else None


def scenario_public(s: Scenario) -> dict:
    return {"id": s.id, "label": s.label, "profile": s.profile, "transform": s.transform, "setup": s.setup}


# ------------------------------------------------------------------------------ transforms

def _read_bounded(zf: zipfile.ZipFile, name: str) -> bytes:
    try:
        with zf.open(name) as fh:
            data = fh.read(MAX_ENTRY_UNCOMPRESSED + 1)
    except (zipfile.BadZipFile, EOFError, NotImplementedError, OSError, ValueError):
        raise LabError("BUNDLE_UNREADABLE", "The upload is not a readable bundle archive") from None
    if len(data) > MAX_ENTRY_UNCOMPRESSED:
        raise LabError("BUNDLE_UNREADABLE", "A bundle entry is too large")
    return data


def _flip_first_hex(data: bytes, marker: bytes) -> bytes:
    i = data.find(marker)
    if i < 0:
        raise LabError("SCENARIO_NOT_APPLICABLE", "This bundle has no sealed verdict record to alter")
    i += len(marker)
    return data[:i] + (b"0" if data[i:i + 1] != b"0" else b"1") + data[i + 1:]


def transform_bundle(kind: str, source: Path, target: Path) -> str:
    """Write ``target`` from ``source`` with exactly one defined change. Returns a plain-language
    description of what changed. ``none`` copies nothing: the caller verifies ``source`` itself."""
    if kind == "none":
        return "Not modified."
    try:
        zin = zipfile.ZipFile(source)
    except (zipfile.BadZipFile, OSError):
        raise LabError("BUNDLE_UNREADABLE", "The upload is not a readable bundle archive") from None
    with zin:
        infos = zin.infolist()
        if len(infos) > MAX_BUNDLE_ENTRIES or sum(i.file_size for i in infos) > MAX_BUNDLE_UNCOMPRESSED:
            raise LabError("BUNDLE_UNREADABLE", "The bundle is larger than the limits allow")
        changed = False
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in infos:
                if kind == "strip-signature" and info.filename == SIGNATURE_MEMBER:
                    changed = True
                    continue
                data = _read_bounded(zin, info.filename)
                if kind == "tamper-verdict" and info.filename == "verdict/verdict.json":
                    data = _flip_first_hex(data, b'"verdict_hash":"')
                    changed = True
                zout.writestr(info, data)
    if kind == "strip-signature":
        return ("The signature member was removed." if changed
                else "The bundle carried no signature, so nothing needed removing.")
    if not changed:
        raise LabError("SCENARIO_NOT_APPLICABLE", "This bundle has no sealed verdict record to alter")
    return "The first character of the sealed verdict hash was changed. Nothing else was touched."
