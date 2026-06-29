"""``pipelinekit governance`` — Governance Management System commands (GM-1).

Orchestration only: delegates ownership logic to ``governance.ownership`` and
renders results with Rich. Resolves the state database path but never issues SQL
itself (SPEC-023, ADR-024, ADR-003 CLI-first).
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.core.errors import GovernanceError
from pipelinekit.governance.ownership import (
    get_owner,
    get_ownership_report,
    remove_owner,
    set_owner,
)
from pipelinekit.state import db

console = Console()

governance_app = typer.Typer(
    help="Governance Management System commands.",
    no_args_is_help=True,
    add_completion=False,
)
owner_app = typer.Typer(
    help="Blueprint ownership commands.",
    no_args_is_help=True,
    add_completion=False,
)
governance_app.add_typer(owner_app, name="owner")


def _db_path() -> str:
    """Resolve the local state database path as a string."""
    return str(db.get_db_path())


def _blueprints_dir() -> str:
    """Resolve the installed-blueprints directory as a string."""
    return str(BlueprintRegistry().blueprints_dir)


@owner_app.command("set")
def set_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to assign an owner."),
    name: str = typer.Option(..., "--name", help="Owner name."),
    email: str = typer.Option(..., "--email", help="Owner email."),
    team: Optional[str] = typer.Option(None, "--team", help="Team name."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes."),
) -> None:
    """Assign or update the owner of a blueprint."""
    try:
        owner = set_owner(blueprint_name, name, email, team, notes, _db_path())
    except GovernanceError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print(
        f"✓ Owner set for {owner.blueprint_name}: "
        f"{owner.owner_name} <{owner.owner_email}>",
        style="green",
    )
    raise typer.Exit(0)


@owner_app.command("get")
def get_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to look up."),
) -> None:
    """Show the owner of a blueprint."""
    owner = get_owner(blueprint_name, _db_path())
    if owner is None:
        console.print(f"No owner assigned for {blueprint_name}.")
        raise typer.Exit(0)

    console.print(f"Owner: {owner.blueprint_name}", style="bold cyan")
    console.print("─" * 37)
    console.print(f"  Name:    {owner.owner_name}")
    console.print(f"  Email:   {owner.owner_email}")
    console.print(f"  Team:    {owner.team_name or '—'}")
    console.print(f"  Notes:   {owner.notes or '—'}")
    console.print(f"  Set at:  {owner.updated_at}")
    raise typer.Exit(0)


@owner_app.command("list")
def list_command() -> None:
    """List all installed blueprints with their ownership status."""
    report = get_ownership_report(_blueprints_dir(), _db_path())
    if report.total_blueprints == 0:
        console.print("No blueprints installed.")
        raise typer.Exit(0)

    owners_by_name = {o.blueprint_name: o for o in report.owners}
    all_names = sorted(set(owners_by_name) | set(report.unowned_blueprints))

    console.print("Blueprint Ownership")
    console.print("─" * 61)
    table = Table()
    table.add_column("Blueprint", style="cyan", no_wrap=True)
    table.add_column("Owner")
    table.add_column("Email")
    table.add_column("Team")
    for name in all_names:
        owner = owners_by_name.get(name)
        if owner is not None:
            table.add_row(
                name, owner.owner_name, owner.owner_email, owner.team_name or "—"
            )
        else:
            table.add_row(name, "—", "—", "—")
    console.print(table)

    if report.unowned_blueprints:
        console.print(
            f"⚠ {len(report.unowned_blueprints)} blueprint(s) have no owner assigned.",
            style="yellow",
        )
        console.print(
            "  Run: pipelinekit governance owner set <blueprint> "
            "--name <name> --email <email>",
            style="dim",
        )
    raise typer.Exit(0)


@owner_app.command("remove")
def remove_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to remove the owner."),
) -> None:
    """Remove the owner from a blueprint."""
    try:
        removed = remove_owner(blueprint_name, _db_path())
    except GovernanceError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if removed:
        console.print(f"✓ Owner removed from {blueprint_name}", style="green")
    else:
        console.print(f"No owner was set for {blueprint_name}")
    raise typer.Exit(0)
