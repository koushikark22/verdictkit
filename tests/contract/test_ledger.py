"""P6 ledger ordering, P7 tamper evidence. Core requirement 8.

The reference automaton below is written independently of verdictkit.custody.ledger.
"""
import dataclasses

import pytest
from hypothesis import given
from hypothesis import strategies as st

from verdictkit.custody.ledger import EntryKind as K
from verdictkit.custody.ledger import Ledger, LedgerOrderError

MAIN = [
    K.CASE_OPENED, K.CLAIM_FROZEN, K.OUTCOMES_COMMITTED, K.EVIDENCE_ACQUIRED,
    K.EXAMINATION_COMMITTED, K.OUTCOMES_REVEALED, K.VERDICT_SEALED,
]


def reference_allowed(prev):
    if prev is None:
        return {K.CASE_OPENED}
    if prev in (K.BUNDLE_WRITTEN, K.CASE_ABORTED):
        return set()
    if prev in (K.VERDICT_SEALED, K.DIAGNOSTICS_APPENDED):
        return {K.DIAGNOSTICS_APPENDED, K.BUNDLE_WRITTEN}
    i = MAIN.index(prev)
    return {MAIN[i + 1], K.CASE_ABORTED}


def clock():
    return "2026-11-22T00:00:00Z"


HAPPY = MAIN + [K.DIAGNOSTICS_APPENDED, K.BUNDLE_WRITTEN]


@given(st.lists(st.sampled_from(list(K)), max_size=14))
def test_order_enforced(kinds):
    """P6: invalid appends raise and leave the ledger unchanged; valid ones succeed."""
    led = Ledger(clock)
    prev = None
    for k in kinds:
        before = led.entries
        if k in reference_allowed(prev):
            led.append(k, {"k": k.value})
            prev = k
        else:
            with pytest.raises(LedgerOrderError):
                led.append(k, {"k": k.value})
            assert led.entries == before
    assert led.verify().ok


def test_reveal_before_examination_impossible():
    led = Ledger(clock)
    for k in MAIN[:4]:
        led.append(k, {})
    with pytest.raises(LedgerOrderError):
        led.append(K.OUTCOMES_REVEALED, {})


def test_diagnostics_before_verdict_impossible():
    led = Ledger(clock)
    for k in MAIN[:6]:
        led.append(k, {})
    with pytest.raises(LedgerOrderError):
        led.append(K.DIAGNOSTICS_APPENDED, {})


def _happy_ledger():
    led = Ledger(clock)
    for k in HAPPY:
        led.append(k, {"kind": k.value})
    return led


@given(st.integers(0, len(HAPPY) - 1))
def test_tamper_detected_at_exact_seq(i):
    """P7: altering one payload hash breaks verification at that sequence number."""
    entries = list(_happy_ledger().entries)
    entries[i] = dataclasses.replace(entries[i], payload_hash="f" * 64)
    check = Ledger.from_entries(entries, clock).verify()
    assert not check.ok and check.first_invalid_seq == i


@given(st.integers(0, len(HAPPY) - 1))
def test_recorded_at_not_hashed(i):
    """Req 8.3: changing recorded_at does not affect verification."""
    entries = list(_happy_ledger().entries)
    entries[i] = dataclasses.replace(entries[i], recorded_at="1999-01-01T00:00:00Z")
    assert Ledger.from_entries(entries, clock).verify().ok


def test_chain_links():
    e = _happy_ledger().entries
    assert e[0].prev_hash == "0" * 64
    assert all(e[j].prev_hash == e[j - 1].entry_hash for j in range(1, len(e)))
    assert [x.seq for x in e] == list(range(len(e)))
