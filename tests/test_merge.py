"""Tests for src/envault/merge.py"""
from pathlib import Path

import pytest

from envault.merge import (
    ConflictStrategy,
    MergeError,
    merge_env_files,
)


@pytest.fixture()
def env_pair(tmp_path: Path):
    base = tmp_path / ".env"
    other = tmp_path / ".env.other"
    base.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n")
    other.write_text("DB_HOST=remotehost\nDB_PORT=5432\nNEW_KEY=hello\n")
    return base, other, tmp_path


def test_merge_raises_when_base_missing(tmp_path: Path):
    other = tmp_path / "other.env"
    other.write_text("X=1\n")
    with pytest.raises(MergeError, match="Base file not found"):
        merge_env_files(tmp_path / "missing.env", other)


def test_merge_raises_when_other_missing(tmp_path: Path):
    base = tmp_path / "base.env"
    base.write_text("X=1\n")
    with pytest.raises(MergeError, match="Other file not found"):
        merge_env_files(base, tmp_path / "missing.env")


def test_merge_detects_conflict_raises_by_default(env_pair):
    base, other, _ = env_pair
    with pytest.raises(MergeError, match="Conflict on key 'DB_HOST'"):
        merge_env_files(base, other)


def test_merge_strategy_ours_keeps_base_value(env_pair):
    base, other, _ = env_pair
    result = merge_env_files(base, other, strategy=ConflictStrategy.OURS)
    assert result.merged["DB_HOST"] == "localhost"
    assert result.has_conflicts
    assert result.conflicts[0].key == "DB_HOST"


def test_merge_strategy_theirs_takes_other_value(env_pair):
    base, other, _ = env_pair
    result = merge_env_files(base, other, strategy=ConflictStrategy.THEIRS)
    assert result.merged["DB_HOST"] == "remotehost"


def test_merge_adds_new_keys_from_other(env_pair):
    base, other, _ = env_pair
    result = merge_env_files(base, other, strategy=ConflictStrategy.OURS)
    assert "NEW_KEY" in result.merged
    assert result.merged["NEW_KEY"] == "hello"
    assert "NEW_KEY" in result.added


def test_merge_reports_removed_keys(env_pair):
    base, other, _ = env_pair
    result = merge_env_files(base, other, strategy=ConflictStrategy.OURS)
    # SECRET is in base but not in other
    assert "SECRET" in result.removed
    assert "SECRET" in result.merged  # still present; merge keeps base keys


def test_merge_no_conflict_when_values_equal(tmp_path: Path):
    base = tmp_path / "base.env"
    other = tmp_path / "other.env"
    base.write_text("X=same\nY=1\n")
    other.write_text("X=same\nZ=2\n")
    result = merge_env_files(base, other)
    assert not result.has_conflicts
    assert result.merged["X"] == "same"
    assert result.merged["Z"] == "2"


def test_merge_writes_output_file(env_pair):
    base, other, tmp_path = env_pair
    out = tmp_path / "merged.env"
    merge_env_files(base, other, strategy=ConflictStrategy.THEIRS, output=out)
    assert out.exists()
    content = out.read_text()
    assert "DB_HOST=remotehost" in content
    assert "NEW_KEY=hello" in content


def test_merge_ignores_comments_and_blanks(tmp_path: Path):
    base = tmp_path / "base.env"
    other = tmp_path / "other.env"
    base.write_text("# comment\n\nA=1\n")
    other.write_text("B=2\n# another comment\n")
    result = merge_env_files(base, other)
    assert set(result.merged.keys()) == {"A", "B"}
