"""Tests for envault.redact and cli_redact."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.redact import RedactError, redact_file, redact_lines
from envault.cli_redact import redact_group


# ---------------------------------------------------------------------------
# redact_lines
# ---------------------------------------------------------------------------

def test_redact_lines_sensitive_key():
    lines = ["API_KEY=supersecret", "NAME=alice"]
    result = redact_lines(lines)
    assert "API_KEY=***" in result.lines
    assert "NAME=alice" in result.lines
    assert result.redacted_count == 1


def test_redact_lines_always_redact():
    lines = ["NAME=alice", "CITY=London"]
    result = redact_lines(lines, always_redact=True)
    assert result.redacted_count == 2
    assert all("***" in l for l in result.lines)


def test_redact_lines_specific_keys():
    lines = ["FOO=bar", "BAZ=qux"]
    result = redact_lines(lines, keys=["FOO"])
    assert "FOO=***" in result.lines
    assert "BAZ=qux" in result.lines
    assert result.redacted_count == 1


def test_redact_lines_preserves_comments_and_blanks():
    lines = ["# comment", "", "TOKEN=abc"]
    result = redact_lines(lines)
    assert result.lines[0] == "# comment"
    assert result.lines[1] == ""
    assert "TOKEN=***" in result.lines


def test_redact_lines_custom_placeholder():
    lines = ["SECRET=hunter2"]
    result = redact_lines(lines, placeholder="<REDACTED>")
    assert result.lines[0] == "SECRET=<REDACTED>"


def test_redact_lines_empty_value_not_counted():
    lines = ["PASSWORD="]
    result = redact_lines(lines)
    assert result.redacted_count == 0


# ---------------------------------------------------------------------------
# redact_file
# ---------------------------------------------------------------------------

def test_redact_file_missing_raises(tmp_path):
    with pytest.raises(RedactError, match="not found"):
        redact_file(tmp_path / "missing.env")


def test_redact_file_writes_output(tmp_path):
    src = tmp_path / ".env"
    src.write_text("DB_PASSWORD=secret\nAPP_NAME=myapp\n")
    out = tmp_path / ".env.redacted"
    result = redact_file(src, output=out)
    assert out.exists()
    content = out.read_text()
    assert "DB_PASSWORD=***" in content
    assert "APP_NAME=myapp" in content
    assert result.redacted_count == 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_TOKEN=abc123\nDEBUG=true\n")
    return p


def test_cli_redact_stdout(runner, env_file):
    res = runner.invoke(redact_group, ["run", str(env_file)])
    assert res.exit_code == 0
    assert "API_TOKEN=***" in res.output
    assert "DEBUG=true" in res.output


def test_cli_redact_output_file(runner, env_file, tmp_path):
    out = tmp_path / "out.env"
    res = runner.invoke(redact_group, ["run", str(env_file), "-o", str(out)])
    assert res.exit_code == 0
    assert "Redacted 1" in res.output
    assert out.exists()


def test_cli_redact_all_flag(runner, env_file):
    res = runner.invoke(redact_group, ["run", str(env_file), "--all"])
    assert res.exit_code == 0
    assert "DEBUG=***" in res.output
