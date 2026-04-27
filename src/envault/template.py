"""Template generation: create a .env.template from an encrypted or plain .env file."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class TemplateError(Exception):
    """Raised when template generation fails."""


_ASSIGNMENT_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=.*$')


def _parse_keys(lines: list[str]) -> list[tuple[str, str]]:
    """Return (key, original_comment) pairs from env lines."""
    result: list[tuple[str, str]] = []
    pending_comment: list[str] = []
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith('#'):
            pending_comment.append(stripped)
            continue
        if not stripped:
            pending_comment.clear()
            continue
        m = _ASSIGNMENT_RE.match(stripped)
        if m:
            result.append((m.group(1), '\n'.join(pending_comment)))
        pending_comment.clear()
    return result


def generate_template(
    source: Path,
    output: Optional[Path] = None,
    placeholder: str = "",
) -> Path:
    """Generate a .env.template from *source*.

    Each variable is written as ``KEY=<placeholder>``.
    Comments immediately preceding a key are preserved.
    """
    if not source.exists():
        raise TemplateError(f"Source file not found: {source}")

    lines = source.read_text(encoding="utf-8").splitlines()
    keys = _parse_keys(lines)

    if not keys:
        raise TemplateError(f"No valid KEY=VALUE assignments found in {source}")

    out_lines: list[str] = []
    for key, comment in keys:
        if comment:
            out_lines.append(comment)
        out_lines.append(f"{key}={placeholder}")
        out_lines.append("")

    dest = output or source.with_suffix(".template")
    dest.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
    return dest
