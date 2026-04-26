"""Lint .env files for common issues before encryption."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


class LintError(Exception):
    """Raised when linting cannot be performed."""


@dataclass
class LintIssue:
    line_number: int
    message: str
    severity: str  # 'error' | 'warning'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line_number}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_ASSIGNMENT_RE = re.compile(r'^([^=]+)=(.*)$')


def lint_lines(lines: list[str]) -> LintResult:
    result = LintResult()
    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        if not line or line.lstrip().startswith("#"):
            continue

        m = _ASSIGNMENT_RE.match(line)
        if not m:
            result.issues.append(
                LintIssue(lineno, f"not a valid KEY=VALUE line: {line!r}", "error")
            )
            continue

        key, value = m.group(1).strip(), m.group(2)

        if not _VALID_KEY_RE.match(key):
            result.issues.append(
                LintIssue(lineno, f"key {key!r} should be UPPER_SNAKE_CASE", "warning")
            )

        if key in seen_keys:
            result.issues.append(
                LintIssue(
                    lineno,
                    f"duplicate key {key!r} (first seen on line {seen_keys[key]})",
                    "error",
                )
            )
        else:
            seen_keys[key] = lineno

        if value.startswith(' ') or value.endswith(' '):
            result.issues.append(
                LintIssue(lineno, f"value for {key!r} has leading/trailing spaces", "warning")
            )

    return result


def lint_file(path: Path) -> LintResult:
    if not path.exists():
        raise LintError(f"file not found: {path}")
    return lint_lines(path.read_text(encoding="utf-8").splitlines(keepends=True))
