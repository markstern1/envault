"""Tests for src/envault/search.py and src/envault/cli_search.py."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.search import SearchError, _mask_value, search_file, search_files
from envault.cli_search import search_group


# ---------------------------------------------------------------------------
# Unit tests – search.py
# ---------------------------------------------------------------------------

def test_mask_value_short():
    assert _mask_value("abc") == "***"


def test_mask_value_long():
    result = _mask_value("supersecret")
    assert result.startswith("supers")
    assert "*" in result


def test_search_file_finds_key(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    result = search_file(env, "DATABASE")
    assert result.found
    assert result.matches[0].key == "DATABASE_URL"


def test_search_file_no_match(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    result = search_file(env, "MISSING")
    assert not result.found


def test_search_file_keys_only_skips_value_match(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=match_this_value\n")
    result = search_file(env, "match", keys_only=True)
    assert not result.found


def test_search_file_ignore_case(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("database_url=postgres://localhost\n")
    result = search_file(env, "DATABASE", ignore_case=True)
    assert result.found


def test_search_file_missing_raises(tmp_path: Path):
    with pytest.raises(SearchError, match="File not found"):
        search_file(tmp_path / "nonexistent.env", "KEY")


def test_search_file_invalid_regex(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    with pytest.raises(SearchError, match="Invalid pattern"):
        search_file(env, "[invalid")


def test_search_files_aggregates(tmp_path: Path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("API_KEY=secret1\n")
    b.write_text("API_SECRET=secret2\n")
    result = search_files([a, b], "API")
    assert len(result.matches) == 2


def test_search_ignores_comments_and_blanks(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("# API_KEY comment\n\nREAL_KEY=value\n")
    result = search_file(env, "API")
    assert not result.found


# ---------------------------------------------------------------------------
# CLI tests – cli_search.py
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_search_run_success(runner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("SECRET_KEY=topsecret\nDEBUG=true\n")
    result = runner.invoke(search_group, ["run", "SECRET", str(env)])
    assert result.exit_code == 0
    assert "SECRET_KEY" in result.output


def test_cli_search_run_no_match_exits_one(runner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    result = runner.invoke(search_group, ["run", "MISSING", str(env)])
    assert result.exit_code == 1
    assert "No matches found" in result.output


def test_cli_search_count_flag(runner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("KEY_ONE=a\nKEY_TWO=b\nOTHER=c\n")
    result = runner.invoke(search_group, ["run", "--count", "KEY", str(env)])
    assert result.exit_code == 0
    assert result.output.strip() == "2"


def test_cli_search_invalid_regex_shows_error(runner, tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    result = runner.invoke(search_group, ["run", "[bad", str(env)])
    assert result.exit_code != 0
    assert "Invalid pattern" in result.output
