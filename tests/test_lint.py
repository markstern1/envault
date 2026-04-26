"""Tests for src/envault/lint.py"""
from pathlib import Path

import pytest

from envault.lint import LintError, LintResult, lint_file, lint_lines


def _lines(*lines: str) -> list[str]:
    return [l + "\n" for l in lines]


def test_lint_clean_file_returns_ok():
    result = lint_lines(_lines("FOO=bar", "BAR=baz"))
    assert result.ok
    assert not result.has_errors


def test_lint_ignores_comments_and_blanks():
    result = lint_lines(_lines("# comment", "", "FOO=1"))
    assert result.ok


def test_lint_detects_invalid_assignment():
    result = lint_lines(_lines("NOTANASSIGNMENT"))
    assert result.has_errors
    assert any("not a valid" in i.message for i in result.issues)


def test_lint_warns_on_lowercase_key():
    result = lint_lines(_lines("foo=bar"))
    assert not result.has_errors
    assert any("UPPER_SNAKE_CASE" in i.message for i in result.issues)
    assert result.issues[0].severity == "warning"


def test_lint_detects_duplicate_keys():
    result = lint_lines(_lines("FOO=1", "FOO=2"))
    assert result.has_errors
    assert any("duplicate key" in i.message for i in result.issues)


def test_lint_warns_on_trailing_spaces_in_value():
    result = lint_lines(["FOO=bar   \n"])
    assert not result.has_errors
    warnings = [i for i in result.issues if "trailing" in i.message or "spaces" in i.message]
    assert warnings


def test_lint_warns_on_leading_spaces_in_value():
    result = lint_lines(["FOO=  bar\n"])
    warnings = [i for i in result.issues if "spaces" in i.message]
    assert warnings
    assert warnings[0].severity == "warning"


def test_lint_issue_str_format():
    result = lint_lines(_lines("NOTVALID"))
    assert result.issues
    text = str(result.issues[0])
    assert "[ERROR]" in text
    assert "line 1" in text


def test_lint_file_reads_from_disk(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nBAR=baz\n")
    result = lint_file(env)
    assert result.ok


def test_lint_file_raises_on_missing(tmp_path: Path):
    with pytest.raises(LintError, match="file not found"):
        lint_file(tmp_path / "nonexistent.env")


def test_lint_multiple_issues_accumulate():
    result = lint_lines(_lines("foo=1", "foo=2", "BADLINE"))
    assert len(result.issues) >= 3
