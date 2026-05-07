"""Strip comments and blank lines from .env files, producing a clean output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


class StripError(Exception):
    """Raised when stripping fails."""


@dataclass
class StripResult:
    original_lines: int
    kept_lines: int
    removed_lines: int
    output: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.kept_lines >= 0

    def summary(self) -> str:
        return (
            f"Stripped {self.removed_lines} line(s) "
            f"({self.original_lines} → {self.kept_lines})"
        )


_BLANK_RE = re.compile(r"^\s*$")
_COMMENT_RE = re.compile(r"^\s*#")


def strip_lines(
    lines: list[str],
    *,
    remove_comments: bool = True,
    remove_blanks: bool = True,
) -> StripResult:
    """Filter a list of raw .env lines according to the requested options."""
    kept: list[str] = []
    for raw in lines:
        line = raw.rstrip("\n")
        if remove_comments and _COMMENT_RE.match(line):
            continue
        if remove_blanks and _BLANK_RE.match(line):
            continue
        kept.append(line)

    return StripResult(
        original_lines=len(lines),
        kept_lines=len(kept),
        removed_lines=len(lines) - len(kept),
        output=kept,
    )


def strip_file(
    source: Path,
    dest: Path | None = None,
    *,
    remove_comments: bool = True,
    remove_blanks: bool = True,
) -> StripResult:
    """Strip a .env file and write the result to *dest* (or overwrite *source*)."""
    if not source.exists():
        raise StripError(f"Source file not found: {source}")

    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    result = strip_lines(
        lines,
        remove_comments=remove_comments,
        remove_blanks=remove_blanks,
    )

    out_path = dest if dest is not None else source
    out_path.write_text("\n".join(result.output) + ("\n" if result.output else ""), encoding="utf-8")
    return result
