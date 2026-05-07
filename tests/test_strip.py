"""Tests for src/envault/strip.py."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.strip import StripError, StripResult, strip_lines, strip_file


# ---------------------------------------------------------------------------
# strip_lines
# ---------------------------------------------------------------------------

def _lines(*raw: str) -> list[str]:
    return [f"{l}\n" for l in raw]


def test_strip_lines_removes_comments():
    lines = _lines("# comment", "KEY=value", "# another")
    result = strip_lines(lines)
    assert result.output == ["KEY=value"]
    assert result.removed_lines == 2


def test_strip_lines_removes_blanks():
    lines = _lines("", "KEY=value", "   ")
    result = strip_lines(lines)
    assert result.output == ["KEY=value"]
    assert result.removed_lines == 2


def test_strip_lines_keeps_comments_when_disabled():
    lines = _lines("# comment", "KEY=value")
    result = strip_lines(lines, remove_comments=False)
    assert "# comment" in result.output
    assert result.kept_lines == 2


def test_strip_lines_keeps_blanks_when_disabled():
    lines = _lines("", "KEY=value")
    result = strip_lines(lines, remove_blanks=False)
    assert result.kept_lines == 2


def test_strip_lines_original_count_is_accurate():
    lines = _lines("# c", "A=1", "", "B=2")
    result = strip_lines(lines)
    assert result.original_lines == 4
    assert result.kept_lines == 2


def test_strip_result_summary():
    result = StripResult(original_lines=5, kept_lines=3, removed_lines=2, output=[])
    assert "5" in result.summary()
    assert "3" in result.summary()
    assert "2" in result.summary()


def test_strip_result_ok_is_true_for_valid():
    result = StripResult(original_lines=2, kept_lines=1, removed_lines=1, output=["A=1"])
    assert result.ok is True


# ---------------------------------------------------------------------------
# strip_file
# ---------------------------------------------------------------------------

def test_strip_file_writes_cleaned_output(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("# comment\nKEY=value\n\nOTHER=123\n")
    result = strip_file(src)
    content = src.read_text()
    assert "# comment" not in content
    assert "KEY=value" in content
    assert result.removed_lines == 2


def test_strip_file_writes_to_dest(tmp_path: Path):
    src = tmp_path / ".env"
    dest = tmp_path / ".env.clean"
    src.write_text("# hi\nA=1\n")
    strip_file(src, dest)
    assert dest.exists()
    assert "# hi" not in dest.read_text()
    # source unchanged
    assert "# hi" in src.read_text()


def test_strip_file_raises_on_missing_source(tmp_path: Path):
    with pytest.raises(StripError, match="not found"):
        strip_file(tmp_path / "nonexistent.env")


def test_strip_file_empty_result_still_writes(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("# only comments\n# more\n")
    result = strip_file(src)
    assert result.kept_lines == 0
    assert src.read_text() == ""
