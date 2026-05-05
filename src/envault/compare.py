"""Compare two encrypted .env files without fully decrypting to disk."""
from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .crypto import decrypt_file, CryptoError
from .diff import diff_files, DiffResult, DiffError


class CompareError(Exception):
    """Raised when comparison cannot be completed."""


@dataclass
class CompareResult:
    old_file: str
    new_file: str
    diff: DiffResult
    identity: str

    @property
    def has_changes(self) -> bool:
        return self.diff.has_changes

    def summary(self) -> str:
        added = len(self.diff.added)
        removed = len(self.diff.removed)
        modified = len(self.diff.modified)
        if not self.has_changes:
            return "No differences found."
        parts: List[str] = []
        if added:
            parts.append(f"+{added} added")
        if removed:
            parts.append(f"-{removed} removed")
        if modified:
            parts.append(f"~{modified} modified")
        return ", ".join(parts)


def compare_encrypted(
    old_enc: Path,
    new_enc: Path,
    identity: Path,
    mask: bool = True,
) -> CompareResult:
    """Decrypt both files into temp files, diff them, then clean up."""
    if not old_enc.exists():
        raise CompareError(f"File not found: {old_enc}")
    if not new_enc.exists():
        raise CompareError(f"File not found: {new_enc}")
    if not identity.exists():
        raise CompareError(f"Identity file not found: {identity}")

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            old_plain = tmp_path / "old.env"
            new_plain = tmp_path / "new.env"

            try:
                decrypt_file(old_enc, old_plain, identity)
                decrypt_file(new_enc, new_plain, identity)
            except CryptoError as exc:
                raise CompareError(f"Decryption failed: {exc}") from exc

            try:
                result = diff_files(old_plain, new_plain, mask_values=mask)
            except DiffError as exc:
                raise CompareError(f"Diff failed: {exc}") from exc

            return CompareResult(
                old_file=str(old_enc),
                new_file=str(new_enc),
                diff=result,
                identity=str(identity),
            )
    except CompareError:
        raise
    except Exception as exc:
        raise CompareError(f"Unexpected error during compare: {exc}") from exc
