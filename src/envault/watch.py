"""File watching support: detect changes to .env files and trigger re-encryption."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when file watching encounters an unrecoverable error."""


@dataclass
class WatchEvent:
    path: Path
    checksum: str
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.timestamp))
        return f"[{ts}] changed: {self.path}  sha256={self.checksum[:12]}…"


def _checksum(path: Path) -> str:
    """Return hex SHA-256 of *path*."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def watch_file(
    path: Path,
    callback: Callable[[WatchEvent], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *path* every *interval* seconds and call *callback* on change.

    Parameters
    ----------
    path:
        The file to watch.  Must exist before calling this function.
    callback:
        Invoked with a :class:`WatchEvent` whenever the file content changes.
    interval:
        Polling interval in seconds.
    max_iterations:
        Stop after this many iterations (useful for testing).  ``None`` means
        run indefinitely.
    """
    if not path.exists():
        raise WatchError(f"File not found: {path}")

    last = _checksum(path)
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        time.sleep(interval)
        iterations += 1
        if not path.exists():
            raise WatchError(f"File disappeared during watch: {path}")
        current = _checksum(path)
        if current != last:
            last = current
            callback(WatchEvent(path=path, checksum=current))
