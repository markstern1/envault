"""Unit tests for src/envault/validate.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.validate import ValidateError, validate_env


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text('DB_URL=postgres://localhost/mydb\nSECRET_KEY=supersecret\nDEBUG=false\n')
    return p


@pytest.fixture()
def schema_file(tmp_path: Path) -> Path:
    schema = {
        "DB_URL": {"required": True},
        "SECRET_KEY": {"required": True, "min_length": 8},
        "DEBUG": {"allowed_values": ["true", "false"]},
    }
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(schema))
    return p


def test_validate_clean_env_returns_ok(env_file: Path, schema_file: Path) -> None:
    result = validate_env(env_file, schema_file)
    assert result.ok
    assert result.issues == []


def test_validate_missing_required_key(tmp_path: Path, schema_file: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DEBUG=true\n")
    result = validate_env(env, schema_file)
    keys = [i.key for i in result.errors()]
    assert "DB_URL" in keys
    assert "SECRET_KEY" in keys


def test_validate_pattern_mismatch(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("PORT=abc\n")
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"PORT": {"pattern": "^[0-9]+$"}}))
    result = validate_env(env, schema)
    assert not result.ok
    assert any("pattern" in i.message for i in result.issues)


def test_validate_min_length_violation(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("SECRET_KEY=short\n")
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"SECRET_KEY": {"required": True, "min_length": 12}}))
    result = validate_env(env, schema)
    assert not result.ok
    assert any("min_length" in i.message for i in result.issues)


def test_validate_allowed_values_violation(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("LOG_LEVEL=TRACE\n")
    schema = tmp_path / "schema.json"
    schema.write_text(
        json.dumps({"LOG_LEVEL": {"allowed_values": ["DEBUG", "INFO", "WARN", "ERROR"]}})
    )
    result = validate_env(env, schema)
    assert not result.ok


def test_validate_missing_schema_raises(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    with pytest.raises(ValidateError, match="not found"):
        validate_env(env, tmp_path / "nonexistent.json")


def test_validate_bad_json_schema_raises(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    schema = tmp_path / "schema.json"
    schema.write_text("{not valid json")
    with pytest.raises(ValidateError, match="Invalid JSON"):
        validate_env(env, schema)


def test_validate_optional_missing_key_is_ok(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"OPTIONAL_KEY": {"required": False, "min_length": 4}}))
    result = validate_env(env, schema)
    assert result.ok
