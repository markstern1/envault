"""Redact sensitive values from .env files for safe logging or display."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class RedactError(Exception):
    """Raised when redaction fails."""


_SENSITIVE_PATTERNS = re.compile(
    r"(password|secret|token|key|api|auth|credential|private|pwd)",
    re.IGNORECASE,
)


@dataclass
class RedactResult:
    lines: List[str] = field(default_factory=list)
    redacted_count: int = 0

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _should_redact(key: str, always_redact: bool) -> bool:
    if always_redact:
        return True
    return bool(_SENSITIVE_PATTERNS.search(key))


def redact_lines(
    lines: List[str],
    placeholder: str = "***",
    always_redact: bool = False,
    keys: Optional[List[str]] = None,
) -> RedactResult:
    """Return a RedactResult with sensitive values replaced by placeholder."""
    result_lines: List[str] = []
    redacted_count = 0
    force_keys = set(keys or [])

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            result_lines.append(line)
            continue

        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", stripped)
        if not match:
            result_lines.append(line)
            continue

        key, value = match.group(1), match.group(2)
        if value and (key in force_keys or _should_redact(key, always_redact)):
            result_lines.append(f"{key}={placeholder}")
            redacted_count += 1
        else:
            result_lines.append(line.rstrip())

    return RedactResult(lines=result_lines, redacted_count=redacted_count)


def redact_file(
    path: Path,
    output: Optional[Path] = None,
    placeholder: str = "***",
    always_redact: bool = False,
    keys: Optional[List[str]] = None,
) -> RedactResult:
    """Redact a .env file and optionally write to output path."""
    if not path.exists():
        raise RedactError(f"File not found: {path}")

    raw_lines = path.read_text().splitlines()
    result = redact_lines(raw_lines, placeholder=placeholder, always_redact=always_redact, keys=keys)

    if output:
        output.write_text(result.text + "\n")

    return result
