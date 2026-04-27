import json
import click
from envault.audit import get_events, record_event, _load_audit, _save_audit


@click.group("audit")
def audit_group():
    """View and manage the audit log."""
    pass


@audit_group.command("log")
@click.option("--env", default=".env", show_default=True, help="Base name of the env file.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
@click.option("--actor", default=None, help="Filter entries by actor.")
@click.option("--action", default=None, help="Filter entries by action.")
@click.option("--limit", default=0, type=int, help="Limit number of entries shown (0 = all).")
def audit_log(env, fmt, actor, action, limit):
    """Display the audit log for an env file."""
    events = get_events(env)

    if actor:
        events = [e for e in events if e.get("actor") == actor]
    if action:
        events = [e for e in events if e.get("action") == action]
    if limit and limit > 0:
        events = events[-limit:]

    if not events:
        click.echo("No audit events found.")
        return

    if fmt == "json":
        click.echo(json.dumps(events, indent=2))
    else:
        for entry in events:
            _print_entry(entry)


def _print_entry(entry: dict) -> None:
    ts = entry.get("timestamp", "unknown")
    action = entry.get("action", "unknown")
    actor = entry.get("actor") or "<unknown>"
    detail = entry.get("detail") or ""
    line = f"[{ts}] {action} by {actor}"
    if detail:
        line += f" — {detail}"
    click.echo(line)


@audit_group.command("clear")
@click.option("--env", default=".env", show_default=True, help="Base name of the env file.")
@click.confirmation_option(prompt="Are you sure you want to clear the audit log?")
def audit_clear(env):
    """Clear all audit log entries for an env file."""
    audit_data = _load_audit(env)
    count = len(audit_data.get("events", []))
    audit_data["events"] = []
    _save_audit(env, audit_data)
    click.echo(f"Cleared {count} audit event(s) for '{env}'.")


@audit_group.command("export")
@click.option("--env", default=".env", show_default=True, help="Base name of the env file.")
@click.argument("output", type=click.Path())
def audit_export(env, output):
    """Export the audit log to a JSON file."""
    events = get_events(env)
    with open(output, "w") as f:
        json.dump({"env": env, "events": events}, f, indent=2)
    click.echo(f"Exported {len(events)} event(s) to '{output}'.")
