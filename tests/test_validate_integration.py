"""Integration tests for validate: real files, no mocks."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_validate import validate_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def setup(tmp_path: Path):
    env = tmp_path / ".env"
    schema = tmp_path / "schema.json"
    return env, schema


def test_integration_valid_env_exits_zero(runner: CliRunner, setup) -> None:
    env, schema = setup
    env.write_text('API_KEY=abcdefgh\nENV=production\n')
    schema.write_text(json.dumps({
        "API_KEY": {"required": True, "min_length": 8},
        "ENV": {"allowed_values": ["production", "staging", "development"]},
    }))
    result = runner.invoke(validate_group, ["run", str(env), str(schema)])
    assert result.exit_code == 0
    assert "passed" in result.output


def test_integration_missing_required_exits_nonzero(runner: CliRunner, setup) -> None:
    env, schema = setup
    env.write_text("UNRELATED=value\n")
    schema.write_text(json.dumps({"API_KEY": {"required": True}}))
    result = runner.invoke(validate_group, ["run", str(env), str(schema)])
    assert result.exit_code == 1
    assert "API_KEY" in result.output


def test_integration_json_output_valid(runner: CliRunner, setup) -> None:
    env, schema = setup
    env.write_text("KEY=x\n")
    schema.write_text(json.dumps({"KEY": {"min_length": 10}}))
    result = runner.invoke(validate_group, ["run", str(env), str(schema), "--json"])
    data = json.loads(result.output)
    assert any(item["key"] == "KEY" for item in data)


def test_integration_pattern_enforcement(runner: CliRunner, setup) -> None:
    env, schema = setup
    env.write_text("PORT=not_a_number\n")
    schema.write_text(json.dumps({"PORT": {"pattern": "^[0-9]+$"}}))
    result = runner.invoke(validate_group, ["run", str(env), str(schema)])
    assert result.exit_code == 1
    assert "pattern" in result.output
