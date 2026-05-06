"""Rename keys across a .env file with optional dry-run support."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class RenameError(Exception):
    """Raised when a rename operation fails."""


@dataclass
class RenameResult:
    renamed: list[tuple[str, str]] = field(default_factory=list)  # (old, new)
    skipped: list[str] = field(default_factory=list)  # keys not found

    @property
    def ok(self) -> bool:
        return len(self.skipped) == 0

    def summary(self) -> str:
        lines = []
        for old, new in self.renamed:
            lines.append(f"  {old} -> {new}")
        for key in self.skipped:
            lines.append(f"  {key} (not found)")
        return "\n".join(lines) if lines else "  (nothing to do)"


def rename_key(
    path: Path,
    old_key: str,
    new_key: str,
    *,
    dry_run: bool = False,
    output: Optional[Path] = None,
) -> RenameResult:
    """Rename *old_key* to *new_key* in *path*.

    Parameters
    ----------
    path:     Source .env file.
    old_key:  Key to rename.
    new_key:  Replacement key name.
    dry_run:  When True, return the result without writing any files.
    output:   Destination file; defaults to *path* (in-place).
    """
    if not path.exists():
        raise RenameError(f"File not found: {path}")
    if not old_key.strip():
        raise RenameError("old_key must not be empty")
    if not new_key.strip():
        raise RenameError("new_key must not be empty")

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    result = RenameResult()
    found = False
    new_lines: list[str] = []

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key, _, rest = stripped.partition("=""")
        key = key.strip()
        if key == old_key:
            found = True
            new_lines.append(line.replace(f"{old_key}=", f"{new_key}=", 1))
        else:
            new_lines.append(line)

    if found:
        result.renamed.append((old_key, new_key))
    else:
        result.skipped.append(old_key)

    if found and not dry_run:
        dest = output or path
        dest.write_text("".join(new_lines), encoding="utf-8")

    return result
