"""Replay namespaces, byte quotas and upload admission (design DD8-3, DD8-4).

Owner-approved limits: 64 MiB per replay, 128 MiB across replays, 2 concurrent uploads, atomic
capacity reservation. Regression tests for: uploaded evidence entering the trusted evidence root,
body buffering before any slot check, and unbounded replay storage.
"""
from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path

import pytest

from security.helpers import POSIX, asgi_post, clock, make_case_with_evidence, receipt_registry
from verdictkit.api import server as server_mod
from verdictkit.api.replay_store import (
    MAX_REPLAY_BYTES, MAX_TOTAL_REPLAY_BYTES, NAMESPACE, ReplayCapacityError, ReplayRoot)
from verdictkit.api.server import MAX_BUNDLE, create_app
from verdictkit.bundle import write_bundle
from verdictkit.evidence.store import EvidenceIntegrityError, EvidenceMeta, EvidenceStore, ReadOnlyEvidence
from verdictkit.examiner import protocol, worker
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import LicenseClass, SourceClass, BlindedTask

MIB = 1024 * 1024
META = dict(source_id="s", source_class=SourceClass.DOCUMENT, uri="https://example.invalid/x",
            retrieved_at="2026-11-22T12:00:00Z", media_type="text/plain",
            license_class=LicenseClass.REDISTRIBUTABLE)


def test_owner_approved_limits_are_the_defaults():
    assert MAX_REPLAY_BYTES == 64 * MIB
    assert MAX_TOTAL_REPLAY_BYTES == 128 * MIB
    assert server_mod.MAX_BUNDLE == 8 * MIB  # the upload body cap of contract 1.x is unchanged


# ------------------------------------------------------------------------ replay root

def test_namespace_is_server_generated_unique_and_always_removed(tmp_path):
    root = ReplayRoot(tmp_path / "replays")
    seen = []
    for _ in range(3):
        with root.namespace(1024) as (token, path):
            assert NAMESPACE.fullmatch(token) and path == root.root / token and path.is_dir()
            (path / "blobs").mkdir()
            (path / "blobs" / "x").write_bytes(b"data")
            seen.append(token)
        assert not path.exists()
    assert len(set(seen)) == 3
    assert list(root.root.iterdir()) == [] and root.reserved == 0


@pytest.mark.skipif(not POSIX, reason="POSIX mode bits")
def test_namespace_is_readable_by_the_examiner_user_and_writable_only_by_the_custodian(tmp_path):
    """Regression for a defect found by the container gate: a 0750 namespace carries the custodian's
    primary group, so the examiner (another OS user) could not traverse it and the replay diverged.
    The replay root is the access control; the namespace must allow r-x for the examiner and no write."""
    import os
    import stat
    old = os.umask(0o077)  # even a restrictive umask must not lock the examiner out
    try:
        root = ReplayRoot(tmp_path / "replays")
        with root.namespace(1) as (_token, path):
            mode = stat.S_IMODE(path.stat().st_mode)
    finally:
        os.umask(old)
    assert mode == 0o755 and not mode & 0o022, oct(mode)


def test_namespace_is_removed_when_the_replay_raises(tmp_path):
    root = ReplayRoot(tmp_path / "replays")
    with pytest.raises(RuntimeError):
        with root.namespace(10) as (_token, path):
            (path / "f").write_bytes(b"x")
            raise RuntimeError("replay failed")
    assert list(root.root.iterdir()) == [] and root.reserved == 0


def test_per_replay_and_total_quotas(tmp_path):
    root = ReplayRoot(tmp_path / "replays", per_replay=64, total=128)
    with pytest.raises(ReplayCapacityError):
        with root.namespace(65):
            pass
    with pytest.raises(ReplayCapacityError):
        with root.namespace(-1):
            pass
    with root.namespace(64):
        with root.namespace(64):
            with pytest.raises(ReplayCapacityError):
                with root.namespace(1):  # 128 bytes are reserved: nothing more fits
                    pass
            assert root.reserved == 128
    assert root.reserved == 0
    with root.namespace(64):  # capacity is reusable once released
        pass


def test_capacity_reservation_is_atomic_under_contention(tmp_path):
    """Eight simultaneous 64-byte requests against a 128-byte total: exactly two are admitted."""
    root = ReplayRoot(tmp_path / "replays", per_replay=64, total=128)
    barrier, hold = threading.Barrier(8), threading.Event()
    admitted, refused = [], []

    def attempt():
        barrier.wait()
        try:
            with root.namespace(64) as (token, _path):
                admitted.append(token)
                hold.wait(10)
        except ReplayCapacityError:
            refused.append(1)

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for t in threads:
        t.start()
    deadline = time.monotonic() + 30
    # Every attempt has an outcome once admitted + refused == 8. Waiting for refusals alone would race
    # with the admitted threads, which record themselves only after namespace() has returned.
    while len(admitted) + len(refused) < 8 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(admitted) == 2 and len(refused) == 6
    assert root.reserved == 128
    hold.set()
    for t in threads:
        t.join(10)
    assert root.reserved == 0 and list(root.root.iterdir()) == []


def test_orphans_are_swept_at_start_and_foreign_entries_are_left_alone(tmp_path):
    base = tmp_path / "replays"
    base.mkdir()
    orphan = base / ("ab" * 16)
    (orphan / "blobs").mkdir(parents=True)
    (orphan / "blobs" / "leftover").write_bytes(b"x")
    foreign_dir, foreign_file = base / "not-a-namespace", base / ("cd" * 16 + ".txt")
    foreign_dir.mkdir()
    foreign_file.write_text("keep")
    root = ReplayRoot(base)
    assert root.swept == 1
    assert not orphan.exists() and foreign_dir.exists() and foreign_file.exists()


HOSTILE_HASHES = ["../../etc/passwd", "..\\..\\x", "a" * 63, "A" * 64, "g" * 64, "a" * 64 + "/..", "", "a/b",
                  "\x00" * 64, "a" * 65]


@pytest.mark.parametrize("bad", HOSTILE_HASHES)
def test_evidence_hashes_are_never_used_as_paths_unless_they_are_64_lowercase_hex(tmp_path, bad):
    """Uploaded bundles name evidence by hash. That string becomes a file name in the store, the
    examiner's reader and the replay cache, so anything but 64 lowercase hex must be refused."""
    store = EvidenceStore(tmp_path / "evidence")
    for call in (store.get, store.item, store.blob_path):
        with pytest.raises(EvidenceIntegrityError):
            call(bad)
    with pytest.raises(EvidenceIntegrityError):
        ReadOnlyEvidence(tmp_path / "evidence", [bad])
    with pytest.raises(KeyError):
        ReadOnlyEvidence(tmp_path / "evidence", []).read(bad)


@pytest.mark.parametrize("bad", ["../../outside", "a" * 63, "Z" * 64])
def test_a_replayed_bundle_with_a_hostile_evidence_hash_is_unverifiable_and_touches_nothing(tmp_path, bad):
    import json
    import zipfile
    from security.helpers import replace_member
    from verdictkit.bundle import ReplayStatus, replay_bundle
    case, item = make_case_with_evidence(tmp_path / "w")
    source = write_bundle(case, tmp_path / "ev.vkb", clock=clock)
    with zipfile.ZipFile(source) as zf:
        index = json.loads(zf.read("evidence/index.json"))
    index[0]["sha256"] = bad
    from verdictkit.canonical import canonical_bytes
    hostile = replace_member(source, tmp_path / "hostile.vkb", "evidence/index.json", canonical_bytes(index))
    cache = tmp_path / "cache"
    cache.mkdir()
    (tmp_path / "outside").write_bytes(b"outside the cache")
    report = replay_bundle(hostile, registry=receipt_registry(), workdir=tmp_path / "r", evidence_cache=cache)
    assert report.status is ReplayStatus.UNVERIFIABLE and report.replayed_verdict_hash is None
    assert (tmp_path / "outside").read_bytes() == b"outside the cache"
    assert item.sha256 not in report.notes


@pytest.mark.skipif(not POSIX, reason="POSIX symlinks")
def test_a_symlink_that_looks_like_a_namespace_is_not_followed_by_the_sweep(tmp_path):
    base, outside = tmp_path / "replays", tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    (outside / "precious").write_text("keep")
    (base / ("ef" * 16)).symlink_to(outside, target_is_directory=True)
    ReplayRoot(base)
    assert (outside / "precious").read_text() == "keep"


# ----------------------------------------------- namespaces on the examiner wire protocol

def _task() -> BlindedTask:
    return BlindedTask(case_id="c", claim_type="contract.receipt.v1", schema_version=1, spec_hash="a" * 64,
                       params={"items": ["1.00"]}, assumptions=(), evidence_refs=())


def test_namespace_travels_with_the_task_frame_and_is_validated():
    token = "0123456789abcdef" * 2
    assert protocol.decode_namespace(protocol.encode_task(_task(), token)) == token
    assert protocol.decode_task(protocol.encode_task(_task(), token)).case_id == "c"
    assert protocol.decode_namespace(protocol.encode_task(_task())) is None
    for bad in ("../../etc", "0123456789ABCDEF" * 2, "0123456789abcdef", "g" * 32, "", "a" * 33, 7):
        with pytest.raises(ValueError):
            protocol.encode_task(_task(), bad)  # type: ignore[arg-type]
    for bad in (b'{"namespace":"../x","task":{},"type":"task"}', b'{"namespace":5,"task":{},"type":"task"}'):
        with pytest.raises(ValueError):
            protocol.decode_namespace(bad)


def test_the_frame_still_has_no_outcome_field():
    assert b"outcome" not in protocol.encode_task(_task(), "0123456789abcdef" * 2)


def test_worker_resolves_only_real_namespace_directories(tmp_path, monkeypatch):
    base = tmp_path / "replays"
    base.mkdir()
    monkeypatch.setenv("VK_REPLAY_DIR", str(base))
    monkeypatch.setenv("VK_EVIDENCE_DIR", str(tmp_path / "evidence"))
    token = "ab" * 16
    (base / token).mkdir()
    assert worker._evidence_root(token) == str(base / token)
    assert worker._evidence_root(None) == str(tmp_path / "evidence")
    with pytest.raises(OSError):
        worker._evidence_root("cd" * 16)  # no such namespace
    (base / ("ef" * 16)).write_text("a file, not a directory")
    with pytest.raises(ValueError):
        worker._evidence_root("ef" * 16)
    monkeypatch.delenv("VK_REPLAY_DIR")
    with pytest.raises(ValueError):
        worker._evidence_root(token)


def test_namespace_content_does_not_touch_the_trusted_store_and_is_rehashed_on_read(tmp_path):
    trusted = EvidenceStore(tmp_path / "evidence")
    good = trusted.put(b"same bytes", EvidenceMeta(**META))
    root = ReplayRoot(tmp_path / "replays")
    with root.namespace(100) as (_token, path):
        hostile = dict(META, source_id="forged", uri="https://attacker.invalid/x",
                       license_class=LicenseClass.USER_SUPPLIED)
        EvidenceStore(path).put(b"same bytes", EvidenceMeta(**hostile))
        assert EvidenceStore(path).item(good.sha256).source_id == "forged"
        reader = ReadOnlyEvidence(path, [good.sha256])
        assert reader.read(good.sha256) == b"same bytes"
        (path / "blobs" / good.sha256).write_bytes(b"swapped after restore")
        with pytest.raises(EvidenceIntegrityError):
            reader.read(good.sha256)
        with pytest.raises(KeyError):
            ReadOnlyEvidence(path, []).read(good.sha256)  # not referenced by the task
    assert trusted.item(good.sha256).source_id == "s", "the live-case record must be untouched"
    assert trusted.get(good.sha256) == b"same bytes"


# --------------------------------------------------------------------------- the API

def _evidence_bundle(tmp_path: Path) -> tuple[bytes, str]:
    case, item = make_case_with_evidence(tmp_path / "w")
    return write_bundle(case, tmp_path / "ev.vkb", clock=clock).read_bytes(), item.sha256


def _enforced(monkeypatch, tmp_path):
    """Simulate the ENFORCED start-up decision; the examiner itself is replaced by a recorder."""
    from verdictkit.api import check_startup
    monkeypatch.setattr(check_startup, "startup_checks", lambda force_judge=False: (False, "ENFORCED"))
    evidence, replays = tmp_path / "trusted-evidence", tmp_path / "replay-root"
    evidence.mkdir()
    monkeypatch.setenv("VK_EVIDENCE_DIR", str(evidence))
    monkeypatch.setenv("VK_REPLAY_DIR", str(replays))
    return evidence, replays


def test_uploaded_evidence_goes_to_a_removed_namespace_never_the_trusted_root(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    evidence, replays = _enforced(monkeypatch, tmp_path)
    bundle, sha = _evidence_bundle(tmp_path)
    observed = []

    class Recording(InProcessExaminer):
        def __init__(self, registry, ns_dir, token, isolation):
            super().__init__(registry, evidence_root=str(ns_dir))
            self.ns_dir, self.token, self.isolation_requested = Path(ns_dir), token, isolation

        def examine(self, task):  # runs after the replay restored the embedded evidence
            observed.append((self.isolation_requested, self.token, self.ns_dir,
                             (self.ns_dir / "blobs" / sha).is_file()))
            return super().examine(task)

    monkeypatch.setattr(server_mod, "_make_examiner",
                        lambda isolation, registry, evidence_dir=None, namespace=None:
                        Recording(registry, evidence_dir, namespace, isolation))
    with TestClient(create_app(receipt_registry())) as client:
        body = client.post("/api/v1/replays", content=bundle).json()
    assert body["reproducibility"]["status"] in ("REPRODUCED", "REPRODUCED_ACROSS_ENV"), body
    ((isolation, token, ns_dir, had_blob),) = observed
    assert isolation == "ENFORCED" and NAMESPACE.fullmatch(token)
    assert ns_dir == replays / token and had_blob, "the blob must be restored inside the namespace"
    assert not ns_dir.exists() and list(replays.iterdir()) == [], "namespace removed after the replay"
    assert list(evidence.iterdir()) == [], "nothing may be written to the trusted evidence root"


def test_two_replays_never_share_a_namespace(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    _enforced(monkeypatch, tmp_path)
    bundle, _sha = _evidence_bundle(tmp_path)
    tokens = []

    def fake_make_examiner(isolation, registry, evidence_dir=None, namespace=None):
        tokens.append(namespace)
        return InProcessExaminer(registry, evidence_root=str(evidence_dir))

    monkeypatch.setattr(server_mod, "_make_examiner", fake_make_examiner)
    with TestClient(create_app(receipt_registry())) as client:
        for _ in range(2):
            assert client.post("/api/v1/replays", content=bundle).status_code == 200
    assert len(tokens) == 2 and tokens[0] != tokens[1]


def test_a_bundle_over_the_per_replay_quota_is_refused_and_writes_nothing(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    _evidence, replays = _enforced(monkeypatch, tmp_path)
    bundle, _sha = _evidence_bundle(tmp_path)
    created = []

    def small_root(base):
        created.append(ReplayRoot(base, per_replay=10, total=20))  # the blob is larger than 10 bytes
        return created[0]

    monkeypatch.setattr(server_mod, "ReplayRoot", small_root)
    with TestClient(create_app(receipt_registry())) as client:
        resp = client.post("/api/v1/replays", content=bundle)
    assert resp.status_code == 429 and resp.json()["error"]["code"] == "RATE_LIMITED"
    assert resp.headers["retry-after"] == "5"
    assert created[0].reserved == 0 and list(replays.iterdir()) == []



# --------------------------------------------------------------- admission before buffering

REPLAYS = "/api/v1/replays"
NOT_A_BUNDLE = b"PK\x03\x04not a bundle"


def _app(monkeypatch, slots: str | None = "1"):
    if slots is None:
        monkeypatch.delenv("VK_MAX_CONCURRENT_UPLOADS", raising=False)
    else:
        monkeypatch.setenv("VK_MAX_CONCURRENT_UPLOADS", slots)
    return create_app(receipt_registry())


def test_slot_is_taken_before_the_first_body_byte_is_read(monkeypatch):
    app = _app(monkeypatch)

    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()

        async def slow_body():
            yield b"PK"
            started.set()
            await release.wait()
            yield b"\x03\x04"

        first = asyncio.create_task(asgi_post(app, REPLAYS, slow_body()))
        await asyncio.wait_for(started.wait(), 10)
        body_was_read = []

        async def second_body():
            body_was_read.append(True)
            yield b"never consumed"

        rejected = await asgi_post(app, REPLAYS, second_body())
        assert rejected.status_code == 429 and rejected.json()["error"]["code"] == "RATE_LIMITED"
        assert rejected.headers["retry-after"] == "5"
        assert not body_was_read, "a rejected upload's body must not be read at all"
        release.set()
        assert (await first).status_code == 200
        again = await asgi_post(app, REPLAYS, NOT_A_BUNDLE)
        assert again.status_code == 200, "the slot must be free again after the first replay"

    asyncio.run(scenario())


def test_two_concurrent_uploads_are_admitted_by_default_and_a_third_is_not(monkeypatch):
    app = _app(monkeypatch, None)

    async def scenario():
        started = [asyncio.Event(), asyncio.Event()]
        gates = [asyncio.Event(), asyncio.Event()]

        def slow(i):
            async def body():
                yield b"PK"
                started[i].set()
                await gates[i].wait()
            return body()

        tasks = [asyncio.create_task(asgi_post(app, REPLAYS, slow(i))) for i in (0, 1)]
        for event in started:
            await asyncio.wait_for(event.wait(), 10)
        third = await asgi_post(app, REPLAYS, b"PK")
        assert third.status_code == 429
        for gate in gates:
            gate.set()
        assert [(await t).status_code for t in tasks] == [200, 200]

    asyncio.run(scenario())


def test_a_stalled_upload_is_cut_off_by_the_total_deadline_and_frees_its_slot(monkeypatch):
    monkeypatch.setattr(server_mod, "UPLOAD_DEADLINE_S", 0.3)
    app = _app(monkeypatch)

    async def scenario():
        async def stalled():
            yield b"PK"
            await asyncio.sleep(10)
            yield b"never"

        resp = await asyncio.wait_for(asgi_post(app, REPLAYS, stalled()), 5)
        assert resp.status_code == 408 and resp.json()["error"]["code"] == "UPLOAD_TIMEOUT"
        assert (await asgi_post(app, REPLAYS, NOT_A_BUNDLE)).status_code == 200

    asyncio.run(scenario())


def test_a_chunked_upload_over_the_cap_is_refused_and_frees_its_slot(monkeypatch):
    app = _app(monkeypatch)

    async def scenario():
        async def endless():
            for _ in range(MAX_BUNDLE // MIB + 2):
                yield b"x" * MIB

        resp = await asgi_post(app, REPLAYS, endless())  # no Content-Length
        assert resp.status_code == 413 and resp.json()["error"]["code"] == "BODY_TOO_LARGE"
        assert (await asgi_post(app, REPLAYS, NOT_A_BUNDLE)).status_code == 200

    asyncio.run(scenario())


def test_a_declared_oversize_upload_is_refused_before_its_body_is_read(monkeypatch):
    app = _app(monkeypatch)

    async def scenario():
        body_was_read = []

        async def body():
            body_was_read.append(True)
            yield b"x"

        resp = await asgi_post(app, REPLAYS, body(), headers={"content-length": str(MAX_BUNDLE + 1)})
        assert resp.status_code == 413
        assert not body_was_read

    asyncio.run(scenario())


def test_an_empty_upload_is_rejected_and_frees_its_slot(monkeypatch):
    app = _app(monkeypatch)

    async def scenario():
        empty = await asgi_post(app, REPLAYS, b"")
        assert empty.status_code == 422 and empty.json()["error"]["code"] == "SCHEMA_INVALID"
        assert (await asgi_post(app, REPLAYS, NOT_A_BUNDLE)).status_code == 200

    asyncio.run(scenario())


def test_spool_and_work_files_do_not_survive_the_request(monkeypatch, tmp_path):
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    app = _app(monkeypatch, "2")

    async def scenario():
        await asgi_post(app, REPLAYS, NOT_A_BUNDLE)
        await asgi_post(app, REPLAYS, b"x" * (MAX_BUNDLE + 1))

    asyncio.run(scenario())
    names = [p.name for p in tmp_path.iterdir()]
    assert [n for n in names if n.startswith(("vk-upload-", "vk-replay-"))] == [], "per-request scratch must go"
    (replay_root,) = [p for p in tmp_path.iterdir() if p.name.startswith("vk-replays-")]  # per-process root
    assert list(replay_root.iterdir()) == [], "no namespace may outlive its replay"