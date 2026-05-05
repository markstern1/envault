"""CLI tests for the validate command group."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_validate import validate_group
from envault.validate import ValidationIssue, ValidationResult


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_files(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("KEY=value\n")
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"KEY": {"required": True}}))
    return env, schema


def _clean_result() -> ValidationResult:
    return ValidationResult(issues=[])


def _error_result() -> ValidationResult:
    return ValidationResult(
        issues=[ValidationIssue(key="SECRET", message="required key is missing", severity="error")]
    )


def test_validate_run_success(runner: CliRunner, env_files) -> None:
    env, schema = env_files
    with patch("envault.cli_validate.validate_env", return_value=_clean_result()):
        result = runner.invoke(validate_group, ["run", str(env), str(schema)])
    assert result.exit_code == 0
    assert "passed" in result.output


def test_validate_run_reports_errors(runner: CliRunner, env_files) -> None:
    env, schema = env_files
    with patch("envault.cli_validate.validate_env", return_value=_error_result()):
        result = runner.invoke(validate_group, ["run", str(env), str(schema)])
    assert result.exit_code == 1
    assert "SECRET" in result.output


def test_validate_run_json_output(runner: CliRunner, env_files) -> None:
    env, schema = env_files
    with patch("envault.cli_validate.validate_env", return_value=_error_result()):
        result = runner.invoke(validate_group, ["run", str(env), str(schema), "--json"])
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["key"] == "SECRET"


def test_validate_run_strict_exits_on_warning(runner: CliRunner, env_files) -> None:
    env, schema = env_files
    warn_result = ValidationResult(
        issues=[ValidationIssue(key="DB", message="optional but empty", severity="warning")]
    )
    with patch("envault.cli_validate.validate_env", return_value=warn_result):
        result = runner.invoke(validate_group, ["run", str(env), str(schema), "--strict"])
    assert result.exit_code == 1


def test_validate_run_schema_error_shown(runner: CliRunner, env_files) -> None:
    env, schema = env_files
    from envault.validate import ValidateError
    with patch("envault.cli_validate.validate_env", side_effect=ValidateError("bad schema")):
        result = runner.invoke(validate_group, ["run", str(env), str(schema)])
    assert result.exit_code != 0
    assert "bad schema" in result.output
