"""Schema-based validation for .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import json


class ValidateError(Exception):
    """Raised when the schema file cannot be loaded or parsed."""


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def _load_schema(schema_path: Path) -> dict[str, Any]:
    try:
        return json.loads(schema_path.read_text())
    except FileNotFoundError:
        raise ValidateError(f"Schema file not found: {schema_path}")
    except json.JSONDecodeError as exc:
        raise ValidateError(f"Invalid JSON schema: {exc}") from exc


def _parse_env(env_path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        env[key.strip()] = value.strip().strip('"\'')
    return env


def validate_env(env_path: Path, schema_path: Path) -> ValidationResult:
    """Validate *env_path* against a JSON schema file.

    Schema format::

        {
          "KEY_NAME": {
            "required": true,
            "pattern": "^[A-Z]+$",
            "min_length": 8
          }
        }
    """
    schema = _load_schema(schema_path)
    env = _parse_env(env_path)
    result = ValidationResult()

    for key, rules in schema.items():
        value = env.get(key)
        required = rules.get("required", False)

        if value is None:
            if required:
                result.issues.append(ValidationIssue(key, "required key is missing"))
            continue

        if not value and required:
            result.issues.append(ValidationIssue(key, "required key has empty value"))
            continue

        if pattern := rules.get("pattern"):
            if not re.fullmatch(pattern, value):
                result.issues.append(
                    ValidationIssue(key, f"value does not match pattern '{pattern}'")
                )

        if min_len := rules.get("min_length"):
            if len(value) < min_len:
                result.issues.append(
                    ValidationIssue(key, f"value shorter than min_length {min_len}")
                )

        if allowed := rules.get("allowed_values"):
            if value not in allowed:
                result.issues.append(
                    ValidationIssue(key, f"value '{value}' not in allowed list")
                )

    return result
