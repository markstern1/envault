"""Diff support for comparing .env file versions."""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .crypto import decrypt_file, CryptoError


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffResult:
    old_path: str
    new_path: str
    lines: List[str]

    @property
    def has_changes(self) -> bool:
        return any(l.startswith(('+', '-')) and not l.startswith(('+++', '---')) for l in self.lines)

    def as_text(self) -> str:
        return ''.join(self.lines)


def diff_files(old_path: Path, new_path: Path) -> DiffResult:
    """Return a unified diff between two plain-text .env files."""
    try:
        old_lines = old_path.read_text().splitlines(keepends=True)
    except OSError as exc:
        raise DiffError(f"Cannot read {old_path}: {exc}") from exc

    try:
        new_lines = new_path.read_text().splitlines(keepends=True)
    except OSError as exc:
        raise DiffError(f"Cannot read {new_path}: {exc}") from exc

    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(old_path),
            tofile=str(new_path),
        )
    )
    return DiffResult(old_path=str(old_path), new_path=str(new_path), lines=diff)


def diff_encrypted(
    old_enc: Path,
    new_enc: Path,
    identity: Path,
    tmp_dir: Path,
) -> DiffResult:
    """Decrypt both encrypted files to a temp dir and diff them."""
    old_plain = tmp_dir / "old.env"
    new_plain = tmp_dir / "new.env"

    try:
        decrypt_file(old_enc, old_plain, identity)
    except CryptoError as exc:
        raise DiffError(f"Failed to decrypt {old_enc}: {exc}") from exc

    try:
        decrypt_file(new_enc, new_plain, identity)
    except CryptoError as exc:
        raise DiffError(f"Failed to decrypt {new_enc}: {exc}") from exc

    return diff_files(old_plain, new_plain)
