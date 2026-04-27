"""Tests for the lint CLI commands."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envault.lint_cli import lint_group
from envault.lint import LintResult, LintIssue


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    return f


def _make_result(issues=None):
    r = MagicMock(spec=LintResult)
    r.issues = issues or []
    r.has_errors.return_value = any(i.level == "error" for i in (issues or []))
    r.has_warnings.return_value = any(i.level == "warning" for i in (issues or []))
    return r


def test_lint_run_clean_file(runner, env_file):
    with patch("envault.lint_cli.lint_file", return_value=_make_result()) as mock_lint:
        result = runner.invoke(lint_group, ["run", str(env_file)])
    assert result.exit_code == 0
    assert "No issues found" in result.output
    mock_lint.assert_called_once_with(env_file)


def test_lint_run_reports_errors(runner, env_file):
    issues = [
        LintIssue(line=2, level="error", message="invalid assignment"),
    ]
    with patch("envault.lint_cli.lint_file", return_value=_make_result(issues)):
        result = runner.invoke(lint_group, ["run", str(env_file)])
    assert result.exit_code == 1
    assert "[ERROR]" in result.output
    assert "invalid assignment" in result.output


def test_lint_run_strict_fails_on_warnings(runner, env_file):
    issues = [
        LintIssue(line=1, level="warning", message="lowercase key"),
    ]
    with patch("envault.lint_cli.lint_file", return_value=_make_result(issues)):
        result = runner.invoke(lint_group, ["run", "--strict", str(env_file)])
    assert result.exit_code == 1


def test_lint_run_quiet_suppresses_summary(runner, env_file):
    with patch("envault.lint_cli.lint_file", return_value=_make_result()):
        result = runner.invoke(lint_group, ["run", "--quiet", str(env_file)])
    assert "No issues found" not in result.output
    assert result.exit_code == 0


def test_lint_run_lint_error_raises_click_exception(runner, env_file):
    from envault.lint import LintError
    with patch("envault.lint_cli.lint_file", side_effect=LintError("unreadable")):
        result = runner.invoke(lint_group, ["run", str(env_file)])
    assert result.exit_code != 0
    assert "unreadable" in result.output
