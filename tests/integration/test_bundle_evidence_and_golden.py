"""Licence-aware evidence embedding and offline replay (core req 9.2-9.4, task 11.1) and
the committed golden stub bundle (task 12.2)."""
from __future__ import annotations

import hashlib
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from contract.receipt_claimtype import ReceiptClaimType, raw_claim
from verdictkit.bundle import ReplayStatus, replay_bundle, write_bundle
from verdictkit.examiner.client import InProcessExaminer
from verdictkit.model import EvidenceItem, LicenseClass, SourceClass, compute_verdict_hash
from verdictkit.pipeline import run_case
from verdictkit.plugin import Registry, examination_payload

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "examples/stub_claimtype/golden.vkb"
REPRODUCED = (ReplayStatus.REPRODUCED, ReplayStatus.REPRODUCED_ACROSS_ENV)


def clock():
    return "2026-11-19T00:00:00Z"


def _registry():
    r = Registry()
    r.register(ReceiptClaimType())
    return r


def _item(data: bytes, lic: LicenseClass, sid: str) -> EvidenceItem:
    return EvidenceItem(source_id=sid, source_class=SourceClass.DOCUMENT,
                        uri=f"https://example.invalid/{sid}", retrieved_at=clock(),
                        sha256=hashlib.sha256(data).hexdigest(), media_type="text/plain",
                        license_class=lic)


EMBED, REFETCH = b"redistributable bytes\n", b"refetch-only bytes\n"


def _case_with_evidence(tmp_path):
    reg = _registry()
    case = run_case(raw_claim(["10.00", "5.50"], "15.50", None), registry=reg,
                    examiner=InProcessExaminer(reg), workdir=tmp_path / "w", clock=clock,
                    case_id="case-ev", vault_key=bytes(32), network=False)
    a = _item(EMBED, LicenseClass.REDISTRIBUTABLE, "a")
    b = _item(REFETCH, LicenseClass.REFETCH_ONLY, "b")
    verdict_hash = compute_verdict_hash(
        spec_hash=case.frozen.spec_hash, evidence_hashes=[a.sha256, b.sha256],
        examination=examination_payload(case.examination), outcomes=dict(case.outcomes),
        findings=case.verdict.findings)
    return replace(case, evidence=(a, b), evidence_blobs={a.sha256: EMBED},
                   verdict=replace(case.verdict, verdict_hash=verdict_hash)), a, b


def test_only_licensed_evidence_is_embedded_and_offline_replay_needs_it(tmp_path):
    case, a, b = _case_with_evidence(tmp_path)
    path = write_bundle(case, tmp_path / "ev.vkb", clock=clock)
    names = set(zipfile.ZipFile(path).namelist())
    assert f"evidence/blobs/{a.sha256}" in names
    assert f"evidence/blobs/{b.sha256}" not in names  # REFETCH_ONLY: URI + hash only

    offline = replay_bundle(path, registry=_registry(), workdir=tmp_path / "r1")
    assert offline.status is ReplayStatus.UNVERIFIABLE
    assert any("required evidence absent" in n for n in offline.notes)

    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / b.sha256).write_bytes(REFETCH)
    cached = replay_bundle(path, registry=_registry(), workdir=tmp_path / "r2", evidence_cache=cache)
    assert cached.status in REPRODUCED, cached.notes

    (cache / b.sha256).write_bytes(b"tampered")
    bad = replay_bundle(path, registry=_registry(), workdir=tmp_path / "r3", evidence_cache=cache)
    assert bad.status is ReplayStatus.UNVERIFIABLE


def test_missing_or_wrong_embeddable_bytes_refuse_to_bundle(tmp_path):
    case, a, _b = _case_with_evidence(tmp_path)
    with pytest.raises(ValueError):
        write_bundle(replace(case, evidence_blobs={}), tmp_path / "x.vkb", clock=clock)
    with pytest.raises(ValueError):
        write_bundle(replace(case, evidence_blobs={a.sha256: b"other"}), tmp_path / "y.vkb", clock=clock)


def test_golden_stub_bundle_replays_offline(tmp_path):
    """Task 12.2: the committed golden bundle replays in CI without network."""
    from verdictkit.cli import _load_registry
    report = replay_bundle(GOLDEN, registry=_load_registry(), workdir=tmp_path)
    assert report.ledger_ok and report.commitment_ok and report.manifest_ok and report.spec_hash_ok
    assert report.status in REPRODUCED, report.notes
