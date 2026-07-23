"""``pipelinekit contract`` — schema versioning for data contracts (DC-8/DC-9).

Orchestration only: discovers contract YAML files in installed blueprints,
delegates versioning and breaking-change detection to ``contracts.versioning``,
and renders results with Rich. The CLI never computes versions or touches
``state.db`` directly beyond resolving the database path (SPEC-020, SPEC-021,
ADR-003 CLI-first).
"""

from __future__ import annotations

import json
from typing import Optional, Tuple

import typer
import yaml  # type: ignore[import-untyped]
from rich.console import Console
from rich.table import Table

from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.contracts.notification import (
    create_notifications,
    get_consumers,
    get_pending_notifications,
    mark_all_read,
    register_consumer,
    remove_consumer,
)
from pipelinekit.contracts.versioning import (
    BreakingChange,
    detect_breaking_changes,
    diff_contract_versions,
    get_contract_history,
    get_contract_version,
    snapshot_contract,
)
from pipelinekit.core.errors import ContractError
from pipelinekit.state import db

console = Console()

contract_app = typer.Typer(
    name="contract",
    help="Version and audit data contracts (DC-8).",
    no_args_is_help=True,
    add_completion=False,
)


def _db_path() -> str:
    """Resolve the local state database path as a string."""
    return str(db.get_db_path())


def _discover_contracts(blueprint: Optional[str]) -> list[tuple[str, str, dict]]:
    """Return ``(blueprint_name, contract_file, content)`` for installed contracts.

    Scans ``blueprints/<name>/contracts/*.yaml``. A blueprint filter narrows the
    scan to a single blueprint. Unparseable contract files are skipped.
    """
    registry = BlueprintRegistry()
    names = [blueprint] if blueprint else [bp.name for bp in registry.list()]
    found: list[tuple[str, str, dict]] = []
    for name in names:
        contracts_dir = registry.blueprints_dir / name / "contracts"
        if not contracts_dir.is_dir():
            continue
        for path in sorted(contracts_dir.glob("*.yaml")):
            try:
                content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            if isinstance(content, dict):
                found.append((name, path.name, content))
    return found


@contract_app.command("version")
def version_command(
    history: bool = typer.Option(False, "--history", help="Show full version history."),
    blueprint: Optional[str] = typer.Option(
        None, "--blueprint", help="Filter by blueprint name."
    ),
    diff: Optional[Tuple[str, str]] = typer.Option(
        None, "--diff", help="Diff two versions, e.g. --diff v1.0.0 v1.1.0."
    ),
) -> None:
    """Show contract versions: latest by default, history, or a diff."""
    db_path = _db_path()

    if diff is not None:
        if not blueprint:
            console.print(
                "✗ --diff requires --blueprint to identify the contract.",
                style="bold red",
            )
            raise typer.Exit(1)
        _render_diff(blueprint, diff[0], diff[1], db_path)
        raise typer.Exit(0)

    if history:
        _render_history(blueprint, db_path)
        raise typer.Exit(0)

    _render_latest(blueprint, db_path)
    raise typer.Exit(0)


def _render_latest(blueprint: Optional[str], db_path: str) -> None:
    """Render the latest stored version of every discovered contract."""
    rows = []
    for name, contract_file, _content in _discover_contracts(blueprint):
        version = get_contract_version(name, contract_file, db_path)
        if version is not None:
            rows.append(version)

    if not rows:
        console.print("No contract versions recorded yet.")
        console.print(
            "  Run 'pipelinekit contract snapshot' to create the first version.",
            style="dim",
        )
        return

    console.print("Contract Versions")
    console.print("─" * 56)
    table = Table()
    table.add_column("Blueprint", style="cyan", no_wrap=True)
    table.add_column("Contract")
    table.add_column("Version")
    table.add_column("Hash")
    table.add_column("Updated")
    for v in rows:
        table.add_row(
            v.blueprint_name,
            v.contract_file,
            f"v{v.version}",
            v.content_hash,
            v.created_at[:10],
        )
    console.print(table)


def _render_history(blueprint: Optional[str], db_path: str) -> None:
    """Render the full version history for discovered contracts."""
    any_history = False
    for name, contract_file, _content in _discover_contracts(blueprint):
        versions = get_contract_history(name, contract_file, db_path)
        if not versions:
            continue
        any_history = True
        console.print(f"\n{name} / {contract_file}", style="bold cyan")
        table = Table()
        table.add_column("Version")
        table.add_column("Hash")
        table.add_column("Created")
        for v in versions:
            table.add_row(f"v{v.version}", v.content_hash, v.created_at)
        console.print(table)

    if not any_history:
        console.print("No contract version history recorded yet.")


def _render_diff(blueprint: str, version_a: str, version_b: str, db_path: str) -> None:
    """Render the diff between two versions of a blueprint's contract(s)."""
    contracts = _discover_contracts(blueprint)
    if not contracts:
        console.print(f"No contracts found for blueprint '{blueprint}'.", style="dim")
        raise typer.Exit(0)

    shown = False
    last_error: Optional[ContractError] = None
    for name, contract_file, _content in contracts:
        try:
            result = diff_contract_versions(
                name, contract_file, version_a, version_b, db_path
            )
        except ContractError as exc:
            last_error = exc
            continue
        shown = True
        console.print(
            f"\n{name} / {contract_file}: "
            f"v{result.version_a} → v{result.version_b} ({result.change_type})",
            style="bold cyan",
        )
        for added in result.added_fields:
            console.print(f"  + {added}", style="green")
        for removed in result.removed_fields:
            console.print(f"  - {removed}", style="red")
        for changed in result.changed_constraints:
            console.print(f"  ~ {changed}", style="yellow")

    if not shown and last_error is not None:
        console.print(f"✗ [{last_error.code}] {last_error.message}", style="bold red")
        raise typer.Exit(1)


def _label(before: Optional[str], after: str) -> str:
    """Describe a version transition for snapshot output."""
    if before is None:
        return "new"
    if before == after:
        return "unchanged"
    return f"{before} → {after}"


def _detect(name: str, contract_file: str, content: dict, db_path: str):
    """Return a BreakingChange for this contract, or None (DC-9)."""
    latest = db.get_latest_contract_version(name, contract_file, db_path)
    if latest is None:
        return None
    old_content = json.loads(latest["contract_content"])
    blueprint_dir = str(BlueprintRegistry().blueprints_dir / name)
    return detect_breaking_changes(
        name, contract_file, old_content, content, blueprint_dir, db_path
    )


def _render_breaking(bc: BreakingChange) -> None:
    """Render the DC-9 breaking-change warning block (SPEC-021)."""
    console.print(
        "\n⚠ [PK-DC-011] Breaking change detected — snapshot blocked",
        style="bold yellow",
    )
    console.print("─" * 45, style="yellow")
    console.print(f"  Contract:    {bc.blueprint_name} / {bc.contract_file}")
    console.print(
        f"  Change:      v{bc.current_version} → v{bc.proposed_version} (MAJOR)"
    )
    console.print(f"\n  Removed columns ({len(bc.removed_columns)}):")
    for col in bc.removed_columns:
        console.print(f"    • {col}")
    if bc.dbt_impact:
        console.print(f"\n  dbt model impact ({len(bc.dbt_impact)} references found):")
        for impact in bc.dbt_impact:
            console.print(
                f"    • {impact.model_file}  "
                f"(line {impact.line_number}: {impact.column_name})"
            )
    else:
        console.print("\n  dbt model impact: none found.")
    console.print(
        "\n  Re-run with --force to accept this breaking change and proceed.",
        style="dim",
    )
    console.print(
        f"  Existing version v{bc.current_version} is preserved until you confirm.",
        style="dim",
    )


@contract_app.command("snapshot")
def snapshot_command(
    force: bool = typer.Option(
        False, "--force", help="Accept breaking changes and proceed."
    ),
) -> None:
    """Snapshot every contract, blocking on breaking changes unless --force."""
    db_path = _db_path()
    contracts = _discover_contracts(None)
    if not contracts:
        console.print("No contracts found in installed blueprints")
        raise typer.Exit(0)

    written: list[tuple[str, str, str]] = []
    forced: list[tuple[str, str, int]] = []
    blocked: list[BreakingChange] = []

    for name, contract_file, content in contracts:
        breaking = _detect(name, contract_file, content, db_path)
        if breaking is not None and not force:
            blocked.append(breaking)
            continue

        before = get_contract_version(name, contract_file, db_path)
        before_version = before.version if before is not None else None
        version = snapshot_contract(name, contract_file, content, db_path)
        if breaking is not None and force:
            # DC-10: a forced MAJOR change is real breaking change — notify any
            # consumers watching the affected table. No consumers → empty list.
            table_name = content.get("table", "") if isinstance(content, dict) else ""
            notifications = create_notifications(
                blueprint_name=name,
                contract_file=contract_file,
                table_name=table_name,
                old_version=before_version or "",
                new_version=version.version,
                change_type="MAJOR",
                db_path=db_path,
            )
            forced.append((contract_file, version.version, len(notifications)))
        written.append(
            (contract_file, version.version, _label(before_version, version.version))
        )

    if written:
        console.print(f"✓ Snapshotted {len(written)} contract(s)", style="green")
        width = max(len(f) for f, _v, _l in written)
        for contract_file, version_str, label in written:
            console.print(
                f"  {contract_file.ljust(width)}  → v{version_str} ({label})",
                style="dim",
            )

    for contract_file, version_str, notified in forced:
        console.print(
            f"⚠ Breaking change accepted (--force). Wrote v{version_str}.",
            style="yellow",
        )
        if notified:
            console.print(f"  ✉ {notified} consumer(s) notified", style="dim")

    for breaking in blocked:
        _render_breaking(breaking)

    raise typer.Exit(1 if blocked else 0)


@contract_app.command("check-breaking")
def check_breaking_command() -> None:
    """Check all contracts for breaking changes without snapshotting (DC-9)."""
    db_path = _db_path()
    console.print("Breaking Change Check")
    console.print("─" * 21)
    console.print("Comparing current contracts against latest snapshots...\n")

    contracts = _discover_contracts(None)
    if not contracts:
        console.print("No contracts found in installed blueprints")
        raise typer.Exit(0)

    width = max(len(contract_file) for _n, contract_file, _c in contracts)
    any_breaking = False
    for name, contract_file, content in contracts:
        latest = db.get_latest_contract_version(name, contract_file, db_path)
        if latest is None:
            console.print(
                f"· {contract_file.ljust(width)} — no baseline (run snapshot first)",
                style="dim",
            )
            continue
        breaking = _detect(name, contract_file, content, db_path)
        if breaking is None:
            console.print(
                f"✓ {contract_file.ljust(width)} — no breaking changes",
                style="green",
            )
        else:
            any_breaking = True
            console.print(
                f"⚠ {contract_file.ljust(width)} — BREAKING: "
                f"{len(breaking.removed_columns)} column(s) removed",
                style="yellow",
            )

    if any_breaking:
        console.print(
            "\nRun 'pipelinekit contract snapshot' to see full impact details.",
            style="dim",
        )
        raise typer.Exit(1)
    raise typer.Exit(0)


# --- DC-10: consumer registration + change notifications ------------------

consumer_app = typer.Typer(
    help="Contract consumer management.",
    no_args_is_help=True,
    add_completion=False,
)
contract_app.add_typer(consumer_app, name="consumer")


@consumer_app.command("add")
def consumer_add_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to watch."),
    email: str = typer.Option(..., "--email", help="Consumer email."),
    table: str = typer.Option(..., "--table", help="Contract table to watch."),
) -> None:
    """Register a consumer to watch a contract table."""
    consumer = register_consumer(blueprint_name, table, email, _db_path())
    console.print(
        f"✓ Consumer registered: {consumer.consumer_email} watching "
        f"{consumer.table_name} ({consumer.blueprint_name})",
        style="green",
    )
    raise typer.Exit(0)


@consumer_app.command("list")
def consumer_list_command() -> None:
    """List all registered contract consumers."""
    registry = BlueprintRegistry()
    db_path = _db_path()
    consumers = [c for bp in registry.list() for c in get_consumers(bp.name, db_path)]
    if not consumers:
        console.print("No consumers registered.")
        raise typer.Exit(0)

    console.print("Contract Consumers", style="bold")
    console.print("─" * 61)
    table = Table()
    table.add_column("Blueprint", style="cyan", no_wrap=True)
    table.add_column("Table")
    table.add_column("Consumer Email")
    table.add_column("Registered At")
    for consumer in consumers:
        table.add_row(
            consumer.blueprint_name,
            consumer.table_name,
            consumer.consumer_email,
            consumer.created_at,
        )
    console.print(table)
    raise typer.Exit(0)


@consumer_app.command("remove")
def consumer_remove_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to stop watching."),
    email: str = typer.Option(..., "--email", help="Consumer email."),
    table: str = typer.Option(..., "--table", help="Contract table."),
) -> None:
    """Remove a registered consumer."""
    removed = remove_consumer(blueprint_name, table, email, _db_path())
    if removed:
        console.print("✓ Consumer removed", style="green")
    else:
        console.print(f"No consumer found for {blueprint_name}/{table}/{email}")
    raise typer.Exit(0)


@contract_app.command("notifications")
def notifications_command(
    clear: bool = typer.Option(
        False, "--clear", help="Mark all pending notifications as read."
    ),
) -> None:
    """View pending contract change notifications."""
    db_path = _db_path()

    if clear:
        count = mark_all_read(db_path)
        console.print(f"✓ {count} notification(s) marked as read", style="green")
        raise typer.Exit(0)

    pending = get_pending_notifications(db_path)
    if not pending:
        console.print("No pending notifications.")
        raise typer.Exit(0)

    console.print("Pending Notifications", style="bold")
    console.print("─" * 70)
    table = Table()
    table.add_column("Blueprint", style="cyan", no_wrap=True)
    table.add_column("Table")
    table.add_column("Change")
    table.add_column("Consumer")
    table.add_column("Created")
    for note in pending:
        table.add_row(
            note.blueprint_name,
            note.table_name,
            f"v{note.old_version}→v{note.new_version}",
            note.consumer_email,
            note.created_at,
        )
    console.print(table)
    console.print(
        f"{len(pending)} pending notification(s). Run with --clear to mark as read."
    )
    raise typer.Exit(0)
