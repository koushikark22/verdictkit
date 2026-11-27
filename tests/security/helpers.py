"""Shared builders for the security regression tests. Throwaway keys only; nothing here is a
production key or real financial data. The claim type is the core test receipt type."""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Callable

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from contract.receipt_claimtype import ReceiptClaimType, raw_claim
from verdictkit.bundle import write_bundle
from verdictkit.canonical import canonical_bytes, parse_canonical
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import EvidenceItem, LicenseClass, SourceClass, compute_verdict_hash
from verdictkit.pipeline import CaseFile, run_case
from verdictkit.plugin import Registry, examination_payload
from verdictkit.safeio import write_private_file
from verdictkit.signing import Signer, signer_from_private_key, trust_entry_for

POSIX = sys.platform != "win32"
EMBEDDED = b"redistributable evidence bytes\n"
NOT_BEFORE, NOT_AFTER = "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z"
AS_OF = "2026-12-01T00:00:00Z"


def clock() -> str:
    return "2026-11-22T12:00:00Z"


def receipt_registry() -> Registry:
    registry = Registry()
    registry.register(ReceiptClaimType())
    return registry


def make_case(workdir: Path, *, stated: str = "15.50", case_id: str = "case-0001") -> CaseFile:
    registry = receipt_registry()
    return run_case(raw_claim(["10.00", "5.50"], stated, None), registry=registry,
                    examiner=InProcessExaminer(registry), workdir=workdir, clock=clock,
                    case_id=case_id, vault_key=bytes(range(32)), network=False)


def make_case_with_evidence(workdir: Path) -> tuple[CaseFile, EvidenceItem]:
    """A case that cites one redistributable evidence blob (embedded in its bundle)."""
    case = make_case(workdir, case_id="case-ev")
    item = EvidenceItem(source_id="a", source_class=SourceClass.DOCUMENT, uri="https://example.invalid/a",
                        retrieved_at=clock(), sha256=hashlib.sha256(EMBEDDED).hexdigest(),
                        media_type="text/plain", license_class=LicenseClass.REDISTRIBUTABLE)
    verdict_hash = compute_verdict_hash(
        spec_hash=case.frozen.spec_hash, evidence_hashes=[item.sha256],
        examination=examination_payload(case.examination), outcomes=dict(case.outcomes),
        findings=case.verdict.findings)
    return (replace(case, evidence=(item,), evidence_blobs={item.sha256: EMBEDDED},
                    verdict=replace(case.verdict, verdict_hash=verdict_hash)), item)


def new_private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


def key_pem(private: Ed25519PrivateKey) -> bytes:
    return private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                 serialization.NoEncryption())


def new_signer(directory: Path, name: str = "signing.pem") -> tuple[Signer, Path]:
    """A throwaway signer and its private key file (mode 0600 / private ACL)."""
    private = new_private_key()
    path = directory / name
    write_private_file(path, key_pem(private))
    return signer_from_private_key(private), path


def trust_store(path: Path, *signers_or_entries, serial: int = 1) -> Path:
    keys = [e if isinstance(e, dict) else trust_entry_for(e, not_before=NOT_BEFORE, not_after=NOT_AFTER)
            for e in signers_or_entries]
    path.write_text(json.dumps({"format": "vk-trust-store", "format_version": 1, "serial": serial,
                                "keys": keys}, indent=2))
    return path


def signed_and_unsigned(tmp_path: Path) -> tuple[Path, Path, Signer, Path]:
    """(signed bundle, unsigned bundle, signer, signing key file) for one case."""
    signer, key_file = new_signer(tmp_path)
    case = make_case(tmp_path / "work")
    unsigned = write_bundle(case, tmp_path / "unsigned.vkb", clock=clock)
    signed = write_bundle(case, tmp_path / "signed.vkb", clock=clock, signer=signer)
    return signed, unsigned, signer, key_file


def rezip(src: Path, dst: Path, mutate: Callable[[str, bytes], bytes | None]) -> Path:
    """Copy a bundle member by member; ``mutate`` may change or drop (None) any member."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in zin.namelist():
            data = mutate(name, zin.read(name))
            if data is not None:
                zout.writestr(name, data)
    return dst


def replace_member(src: Path, dst: Path, member: str, data: bytes, *, fix_manifest: bool = True) -> Path:
    """Replace one member; by default also rewrite its hash in the manifest, which keeps the
    bundle self-consistent (integrity VERIFIED) while its content is hostile."""
    def mutate(name: str, old: bytes) -> bytes:
        if name == member:
            return data
        if name == "manifest.json" and fix_manifest:
            manifest = parse_canonical(old)
            manifest["files"][member] = hashlib.sha256(data).hexdigest()
            return canonical_bytes(manifest)
        return old
    return rezip(src, dst, mutate)


def in_memory_zip(members: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return out.getvalue()


class AsgiResponse:
    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status_code, self.headers, self.content = status, headers, body

    def json(self):
        return json.loads(self.content)


async def asgi_post(app, path: str, content, *, headers: dict[str, str] | None = None) -> AsgiResponse:
    """Minimal ASGI client (no HTTP library needed). ``content`` is ``bytes`` (sent with a
    Content-Length) or an async iterator of chunks (sent without one, like a chunked upload).
    The body is pulled lazily: it is only read when the application calls ``receive``."""
    import asyncio

    async def one_chunk(data: bytes):
        yield data

    hdrs = dict(headers or {})
    if isinstance(content, (bytes, bytearray)):
        hdrs.setdefault("content-length", str(len(content)))
        chunks = one_chunk(bytes(content))
    else:
        chunks = content
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST",
             "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
             "root_path": "", "headers": [(k.lower().encode(), v.encode()) for k, v in hdrs.items()],
             "client": ("127.0.0.1", 50000), "server": ("vk", 80), "state": {}}
    source = chunks.__aiter__()
    exhausted = False
    never = asyncio.Event()

    async def receive():
        nonlocal exhausted
        if exhausted:
            await never.wait()  # a real server holds the connection until the response is done
        try:
            return {"type": "http.request", "body": await source.__anext__(), "more_body": True}
        except StopAsyncIteration:
            exhausted = True
            return {"type": "http.request", "body": b"", "more_body": False}

    status, response_headers, parts = 0, {}, []

    async def send(message):
        nonlocal status, response_headers
        if message["type"] == "http.response.start":
            status = message["status"]
            response_headers = {k.decode().lower(): v.decode() for k, v in message["headers"]}
        elif message["type"] == "http.response.body":
            parts.append(message.get("body", b""))

    await app(scope, receive, send)
    return AsgiResponse(status, response_headers, b"".join(parts))


def grant_everyone(path: Path) -> None:
    """Windows only: add an ALLOW entry for Everyone, which makes a private object non-private."""
    # Inheritance flags are only valid for directories; icacls ignores them on files without an error.
    grant = "*S-1-1-0:(OI)(CI)R" if path.is_dir() else "*S-1-1-0:R"
    subprocess.run(["icacls", str(path), "/grant", grant], check=True, capture_output=True)
