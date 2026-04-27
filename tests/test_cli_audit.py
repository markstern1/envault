import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envault.cli_audit import audit_group


@pytest.fixture
def runner():
    return CliRunner()


SAMPLE_EVENTS = [
    {"timestamp": "2024-01-01T00:00:00", "action": "encrypt", "actor": "alice", "detail": ".env"},
    {"timestamp": "2024-01-02T00:00:00", "action": "decrypt", "actor": "bob", "detail": ".env"},
    {"timestamp": "2024-01-03T00:00:00", "action": "rotate", "actor": "alice", "detail": ".env"},
]


def test_audit_log_text_format(runner):
    with patch("envault.cli_audit.get_events", return_value=SAMPLE_EVENTS):
        result = runner.invoke(audit_group, ["log", "--env", ".env"])
    assert result.exit_code == 0
    assert "encrypt" in result.output
    assert "alice" in result.output
    assert "bob" in result.output


def test_audit_log_json_format(runner):
    with patch("envault.cli_audit.get_events", return_value=SAMPLE_EVENTS):
        result = runner.invoke(audit_group, ["log", "--env", ".env", "--format", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert len(parsed) == 3
    assert parsed[0]["action"] == "encrypt"


def test_audit_log_filter_by_actor(runner):
    with patch("envault.cli_audit.get_events", return_value=SAMPLE_EVENTS):
        result = runner.invoke(audit_group, ["log", "--env", ".env", "--actor", "alice"])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "bob" not in result.output


def test_audit_log_filter_by_action(runner):
    with patch("envault.cli_audit.get_events", return_value=SAMPLE_EVENTS):
        result = runner.invoke(audit_group, ["log", "--env", ".env", "--action", "rotate"])
    assert result.exit_code == 0
    assert "rotate" in result.output
    assert "decrypt" not in result.output


def test_audit_log_limit(runner):
    with patch("envault.cli_audit.get_events", return_value=SAMPLE_EVENTS):
        result = runner.invoke(audit_group, ["log", "--env", ".env", "--limit", "1"])
    assert result.exit_code == 0
    assert "rotate" in result.output
    assert "encrypt" not in result.output


def test_audit_log_empty(runner):
    with patch("envault.cli_audit.get_events", return_value=[]):
        result = runner.invoke(audit_group, ["log", "--env", ".env"])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_audit_clear(runner):
    audit_data = {"events": list(SAMPLE_EVENTS)}
    with patch("envault.cli_audit._load_audit", return_value=audit_data), \
         patch("envault.cli_audit._save_audit") as mock_save:
        result = runner.invoke(audit_group, ["clear", "--env", ".env"], input="y\n")
    assert result.exit_code == 0
    assert "Cleared 3" in result.output
    mock_save.assert_called_once()
    saved_data = mock_save.call_args[0][1]
    assert saved_data["events"] == []


def test_audit_export(runner, tmp_path):
    output_file = str(tmp_path / "audit_export.json")
    with patch("envault.cli_audit.get_events", return_value=SAMPLE_EVENTS):
        result = runner.invoke(audit_group, ["export", "--env", ".env", output_file])
    assert result.exit_code == 0
    assert "Exported 3" in result.output
    with open(output_file) as f:
        data = json.load(f)
    assert data["env"] == ".env"
    assert len(data["events"]) == 3
