"""``pipelinekit contract`` — schema versioning for data contracts (DC-8).

Orchestration only: discovers contract YAML files in installed blueprints,
delegates versioning to ``contracts.versioning``, and renders results with Rich.
The CLI never computes versions or touches ``state.db`` directly beyond resolving
the database path (SPEC-020, ADR-003 CLI-first).
"""

from __future__ import annotations

from typing import Optional, Tuple

import typer
import yaml  # type: ignore[import-untyped]
from rich.console import Console
from rich.table import Table

from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.contracts.versioning import (
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


@contract_app.command("snapshot")
def snapshot_command() -> None:
    """Snapshot every contract in installed blueprints, versioning each."""
    db_path = _db_path()
    contracts = _discover_contracts(None)
    if not contracts:
        console.print("No contracts found in installed blueprints")
        raise typer.Exit(0)

    results = []
    for name, contract_file, content in contracts:
        latest = get_contract_version(name, contract_file, db_path)
        before = latest.version if latest is not None else None
        version = snapshot_contract(name, contract_file, content, db_path)
        is_new = before is None
        unchanged = before is not None and before == version.version
        if is_new:
            label = "new"
        elif unchanged:
            label = "unchanged"
        else:
            label = f"{before} → {version.version}"
        results.append((contract_file, version.version, label))

    console.print(f"✓ Snapshotted {len(results)} contract(s)", style="green")
    width = max(len(f) for f, _v, _l in results)
    for contract_file, version_str, label in results:
        console.print(
            f"  {contract_file.ljust(width)}  → v{version_str} ({label})",
            style="dim",
        )
    raise typer.Exit(0)
