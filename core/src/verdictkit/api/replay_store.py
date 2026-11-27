"""Replay namespaces and byte quotas. Design DD8-3.

An uploaded bundle never writes into the trusted evidence root that live cases use. Each replay
gets a server-generated namespace (32 lowercase hex characters) below a separate replay root. The
namespace is removed in ``finally`` and orphans are swept at start. The examiner reads one
namespace read-only, named by the validated token, and re-hashes every blob on read.

Quotas (owner-approved): 64 MiB per replay and 128 MiB across concurrent replays. Capacity is
reserved atomically before anything is written, so concurrent uploads cannot jointly exceed it.
"""
from __future__ import annotations

import os
import re
import secrets
import shutil
import stat
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

NAMESPACE = re.compile(r"^[0-9a-f]{32}$")
MAX_REPLAY_BYTES = 64 * 1024 * 1024
MAX_TOTAL_REPLAY_BYTES = 128 * 1024 * 1024


class ReplayCapacityError(RuntimeError):
    """Replay storage quota exhausted. The message is fixed text."""

    def __init__(self) -> None:
        super().__init__("replay capacity exhausted")


class ReplayRoot:
    def __init__(self, root: str | os.PathLike, *, per_replay: int = MAX_REPLAY_BYTES,
                 total: int = MAX_TOTAL_REPLAY_BYTES) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._per_replay = per_replay
        self._total = total
        self._reserved = 0
        self._lock = threading.Lock()
        self.swept = self._sweep_orphans()

    def _sweep_orphans(self) -> int:
        """Remove namespaces left by a crashed process. Links and foreign names are left alone."""
        removed = 0
        for child in self.root.iterdir():
            if not NAMESPACE.fullmatch(child.name):
                continue
            try:
                if not stat.S_ISDIR(os.lstat(child).st_mode):
                    continue
                shutil.rmtree(child)
                removed += 1
            except OSError:
                continue
        return removed

    @property
    def reserved(self) -> int:
        with self._lock:
            return self._reserved

    @contextmanager
    def namespace(self, nbytes: int) -> Iterator[tuple[str, Path]]:
        """Reserve ``nbytes`` atomically, create a fresh namespace, and always clean up."""
        if not isinstance(nbytes, int) or nbytes < 0 or nbytes > self._per_replay:
            raise ReplayCapacityError()
        with self._lock:
            if self._reserved + nbytes > self._total:
                raise ReplayCapacityError()
            self._reserved += nbytes
        token = secrets.token_hex(16)
        path = self.root / token
        try:
            os.mkdir(path)  # exclusive: an existing name is an error, never reused
            # Access control is the replay root (0750, owned by the custodian, group examiner), as
            # for the shared evidence store. The examiner is a different OS user and needs r-x below
            # it; a 0750 namespace would carry the custodian's primary group and lock it out.
            os.chmod(path, 0o755)
            yield token, path
        finally:
            shutil.rmtree(path, ignore_errors=True)
            with self._lock:
                self._reserved -= nbytes
