"""Unit tests for envault.inject."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.inject import inject_run, InjectError, _decrypt_to_env


@pytest.fixture()
def env_files(tmp_path: Path):
    enc = tmp_path / "secrets.env.age"
    enc.write_bytes(b"fake-age-data")
    identity = tmp_path / "key.txt"
    identity.write_text("AGE-SECRET-KEY-1FAKE")
    return enc, identity


def _patch_decrypt(env_dict: dict[str, str]):
    return patch("envault.inject._decrypt_to_env", return_value=env_dict)


def test_inject_run_missing_encrypted(tmp_path: Path):
    with pytest.raises(InjectError, match="not found"):
        inject_run(tmp_path / "missing.age", tmp_path / "key.txt", ["echo", "hi"])


def test_inject_run_missing_identity(env_files):
    enc, _ = env_files
    with pytest.raises(InjectError, match="Identity file not found"):
        inject_run(enc, enc.parent / "no_key.txt", ["echo"])


def test_inject_run_empty_command(env_files):
    enc, identity = env_files
    with pytest.raises(InjectError, match="No command"):
        inject_run(enc, identity, [])


def test_inject_run_success(env_files):
    enc, identity = env_files
    fake_env = {"MY_VAR": "hello", "OTHER": "world"}
    mock_proc = MagicMock(returncode=0)
    with _patch_decrypt(fake_env), patch("subprocess.run", return_value=mock_proc) as mock_run:
        result = inject_run(enc, identity, ["printenv"])

    assert result.ok
    assert result.returncode == 0
    assert set(result.injected_keys) == {"MY_VAR", "OTHER"}
    mock_run.assert_called_once()


def test_inject_run_nonzero_exit(env_files):
    enc, identity = env_files
    mock_proc = MagicMock(returncode=1)
    with _patch_decrypt({"A": "1"}), patch("subprocess.run", return_value=mock_proc):
        result = inject_run(enc, identity, ["false"])

    assert not result.ok
    assert result.returncode == 1


def test_inject_run_override_flag(env_files, monkeypatch):
    enc, identity = env_files
    monkeypatch.setenv("EXISTING", "original")
    fake_env = {"EXISTING": "overridden"}
    captured: dict = {}

    def fake_run(cmd, env):
        captured["env"] = env
        return MagicMock(returncode=0)

    with _patch_decrypt(fake_env), patch("subprocess.run", side_effect=fake_run):
        inject_run(enc, identity, ["env"], override=True)

    assert captured["env"]["EXISTING"] == "overridden"


def test_inject_run_no_override_preserves_existing(env_files, monkeypatch):
    enc, identity = env_files
    monkeypatch.setenv("EXISTING", "original")
    captured: dict = {}

    def fake_run(cmd, env):
        captured["env"] = env
        return MagicMock(returncode=0)

    with _patch_decrypt({"EXISTING": "new_value"}), patch("subprocess.run", side_effect=fake_run):
        inject_run(enc, identity, ["env"], override=False)

    assert captured["env"]["EXISTING"] == "original"


def test_inject_run_extra_env(env_files):
    enc, identity = env_files
    captured: dict = {}

    def fake_run(cmd, env):
        captured["env"] = env
        return MagicMock(returncode=0)

    with _patch_decrypt({"BASE": "1"}), patch("subprocess.run", side_effect=fake_run):
        inject_run(enc, identity, ["env"], extra_env={"EXTRA": "yes"})

    assert captured["env"]["EXTRA"] == "yes"
    assert captured["env"]["BASE"] == "1"
