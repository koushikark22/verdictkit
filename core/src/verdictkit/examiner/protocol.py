"""Custodian <-> Examiner wire format. Requirements: core 2.4, 4.3. Properties P2, P3.

Frames: 4-byte big-endian length + canonical JSON. Maximum frame 8 MiB.
Only two message types exist: ``task`` (Custodian -> Examiner) and ``result``
(Examiner -> Custodian). There is no message type that can carry outcomes.
"""
from __future__ import annotations

import re
from decimal import Decimal

from ..canonical import canonical_bytes, parse_canonical
from ..model import Assumption, AssumptionKind, BlindedTask, Origin
from ..plugin import Examination, PointResult

MAX_FRAME_BYTES = 8 * 1024 * 1024


class FrameTooLargeError(ValueError):
    pass


def _assumption_to_dict(a: Assumption) -> dict:
    d: dict = {
        "name": a.name,
        "kind": a.kind.value,
        "origin": a.origin.value,
    }
    if a.kind is AssumptionKind.FIXED:
        d["value"] = format(a.value, "f") if isinstance(a.value, Decimal) else str(a.value) if a.value is not None else None
    elif a.kind is AssumptionKind.RANGE:
        d["minimum"] = format(a.minimum, "f")
        d["maximum"] = format(a.maximum, "f")
        d["step"] = format(a.step, "f")
    elif a.kind is AssumptionKind.SET:
        d["values"] = [
            format(v, "f") if isinstance(v, Decimal) else str(v)
            for v in a.values
        ]
    return d


def _assumption_from_dict(d: dict) -> Assumption:
    kind = AssumptionKind(d["kind"])
    origin = Origin(d["origin"])
    kwargs: dict = {"name": d["name"], "kind": kind, "origin": origin}
    if kind is AssumptionKind.FIXED:
        raw = d.get("value")
        kwargs["value"] = Decimal(raw) if raw is not None else None
    elif kind is AssumptionKind.RANGE:
        kwargs["minimum"] = Decimal(d["minimum"])
        kwargs["maximum"] = Decimal(d["maximum"])
        kwargs["step"] = Decimal(d["step"])
    elif kind is AssumptionKind.SET:
        kwargs["values"] = tuple(Decimal(v) for v in d["values"])
    return Assumption(**kwargs)


_NAMESPACE = re.compile(r"^[0-9a-f]{32}$")


def encode_task(task: BlindedTask, namespace: str | None = None) -> bytes:
    """Canonical JSON bytes of ``{"type": "task", "task": <task>}`` (no length prefix).

    ``namespace`` (32 lowercase hex characters) names a replay evidence namespace the worker
    may read instead of the shared evidence root (design DD8-3). It carries no outcome data."""
    task_dict = {
        "case_id": task.case_id,
        "claim_type": task.claim_type,
        "schema_version": task.schema_version,
        "spec_hash": task.spec_hash,
        "params": dict(task.params),
        "assumptions": [_assumption_to_dict(a) for a in task.assumptions],
        "evidence_refs": list(task.evidence_refs),
    }
    message: dict = {"type": "task", "task": task_dict}
    if namespace is not None:
        if not isinstance(namespace, str) or _NAMESPACE.fullmatch(namespace) is None:
            raise ValueError("invalid evidence namespace")
        message["namespace"] = namespace
    return canonical_bytes(message)


def decode_namespace(data: bytes) -> str | None:
    """The validated replay namespace of a task frame, or ``None``. Raises ``ValueError`` when
    the field is present but is not exactly 32 lowercase hexadecimal characters."""
    obj = parse_canonical(data)
    namespace = obj.get("namespace") if isinstance(obj, dict) else None
    if namespace is None:
        return None
    if not isinstance(namespace, str) or _NAMESPACE.fullmatch(namespace) is None:
        raise ValueError("invalid evidence namespace")
    return namespace


def decode_task(data: bytes) -> BlindedTask:
    obj = parse_canonical(data)
    assert obj["type"] == "task"
    t = obj["task"]
    return BlindedTask(
        case_id=t["case_id"],
        claim_type=t["claim_type"],
        schema_version=t["schema_version"],
        spec_hash=t["spec_hash"],
        params=t["params"],
        assumptions=tuple(_assumption_from_dict(a) for a in t["assumptions"]),
        evidence_refs=tuple(t.get("evidence_refs", [])),
    )


def encode_result(examination: Examination) -> bytes:
    result_dict = {
        "spec_hash": examination.spec_hash,
        "shared": dict(examination.shared),
        "points": [
            {"point": dict(p.point), "values": dict(p.values)}
            for p in examination.points
        ],
        "missing_assumptions": list(examination.missing_assumptions),
    }
    return canonical_bytes({"type": "result", "result": result_dict})


def decode_result(data: bytes) -> Examination:
    obj = parse_canonical(data)
    assert obj["type"] == "result"
    r = obj["result"]
    return Examination(
        spec_hash=r["spec_hash"],
        shared=r["shared"],
        points=tuple(
            PointResult(point=p["point"], values=p["values"])
            for p in r["points"]
        ),
        missing_assumptions=tuple(r.get("missing_assumptions", [])),
    )


def frame(payload: bytes) -> bytes:
    """Prefix with length; raise FrameTooLargeError above MAX_FRAME_BYTES."""
    if len(payload) > MAX_FRAME_BYTES:
        raise FrameTooLargeError(
            f"payload size {len(payload)} exceeds max frame size {MAX_FRAME_BYTES}"
        )
    import struct
    return struct.pack(">I", len(payload)) + payload
