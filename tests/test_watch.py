"""Tests for envault.watch and envault.cli_watch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli_watch import watch_run
from envault.watch import WatchError, WatchEvent, _checksum, watch_file


# ---------------------------------------------------------------------------
# Unit tests – watch.py
# ---------------------------------------------------------------------------

def test_checksum_returns_hex_string(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    result = _checksum(f)
    assert len(result) == 64
    assert result.isalnum()


def test_watch_file_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(WatchError, match="not found"):
        watch_file(tmp_path / "missing.env", lambda e: None, max_iterations=1)


def test_watch_file_calls_callback_on_change(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    events: list[WatchEvent] = []

    call_count = 0

    def _patched_sleep(_: float) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            env.write_text("A=2\n")  # mutate on first iteration

    with patch("envault.watch.time.sleep", side_effect=_patched_sleep):
        watch_file(env, events.append, interval=0, max_iterations=2)

    assert len(events) == 1
    assert events[0].path == env


def test_watch_file_no_callback_when_unchanged(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    events: list[WatchEvent] = []

    with patch("envault.watch.time.sleep"):
        watch_file(env, events.append, interval=0, max_iterations=3)

    assert events == []


def test_watch_event_str_contains_path(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    ev = WatchEvent(path=env, checksum="abc123" + "0" * 58)
    assert str(env) in str(ev)
    assert "abc123" in str(ev)


def test_watch_file_raises_if_file_disappears(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\n")

    def _delete_then_sleep(_: float) -> None:
        env.unlink()

    with patch("envault.watch.time.sleep", side_effect=_delete_then_sleep):
        with pytest.raises(WatchError, match="disappeared"):
            watch_file(env, lambda e: None, interval=0, max_iterations=1)


# ---------------------------------------------------------------------------
# Unit tests – cli_watch.py
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_watch_run_missing_file_exits_nonzero(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        watch_run,
        [str(tmp_path / "no.env"), "-r", "age1abc"],
    )
    assert result.exit_code != 0


def test_watch_run_invokes_watch_file(runner: CliRunner, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("K=v\n")

    with patch("envault.cli_watch.watch_file") as mock_watch:
        result = runner.invoke(
            watch_run,
            [str(env), "-r", "age1test", "--interval", "0.5"],
        )

    mock_watch.assert_called_once()
    _args, kwargs = mock_watch.call_args
    assert kwargs["interval"] == 0.5
    assert result.exit_code == 0


def test_watch_run_keyboard_interrupt_exits_cleanly(runner: CliRunner, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("K=v\n")

    with patch("envault.cli_watch.watch_file", side_effect=KeyboardInterrupt):
        result = runner.invoke(watch_run, [str(env), "-r", "age1test"])

    assert result.exit_code == 0
    assert "stopped" in result.output
