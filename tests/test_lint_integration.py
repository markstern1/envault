"""Integration tests for lint CLI + lint module together."""
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.lint_cli import lint_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _env(tmp_path: Path, content: str) -> Path:
    f = tmp_path / ".env"
    f.write_text(content)
    return f


def test_integration_clean_env(runner, tmp_path):
    env = _env(tmp_path, "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    result = runner.invoke(lint_group, ["run", str(env)])
    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_integration_invalid_assignment_exits_nonzero(runner, tmp_path):
    env = _env(tmp_path, "GOOD=ok\nBAD LINE\nANOTHER=fine\n")
    result = runner.invoke(lint_group, ["run", str(env)])
    assert result.exit_code == 1
    assert "[ERROR]" in result.output
    assert "line 2" in result.output


def test_integration_lowercase_warning_no_strict(runner, tmp_path):
    env = _env(tmp_path, "lowercase_key=value\n")
    result = runner.invoke(lint_group, ["run", str(env)])
    # warnings alone should not cause non-zero exit without --strict
    assert result.exit_code == 0
    assert "[WARNING]" in result.output


def test_integration_lowercase_warning_strict_exits(runner, tmp_path):
    env = _env(tmp_path, "lowercase_key=value\n")
    result = runner.invoke(lint_group, ["run", "--strict", str(env)])
    assert result.exit_code == 1


def test_integration_summary_counts(runner, tmp_path):
    env = _env(tmp_path, "bad line\nlowercase=x\nGOOD=ok\n")
    result = runner.invoke(lint_group, ["run", str(env)])
    assert "1 error(s)" in result.output
    assert "1 warning(s)" in result.output
