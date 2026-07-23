"""``pipelinekit governance`` — Governance Management System commands (GM-1).

Orchestration only: delegates ownership logic to ``governance.ownership`` and
renders results with Rich. Resolves the state database path but never issues SQL
itself (SPEC-023, ADR-024, ADR-003 CLI-first).
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.core.errors import GovernanceError
from pipelinekit.governance.convention import (
    add_convention,
    check_blueprint_conventions,
    get_conventions,
    remove_convention,
)
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

convention_app = typer.Typer(
    help="Naming convention management.",
    no_args_is_help=True,
    add_completion=False,
)
governance_app.add_typer(convention_app, name="convention")


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


# --- GM-2: naming convention enforcement ----------------------------------


@convention_app.command("add")
def convention_add_command(
    scope: str = typer.Option(
        ..., "--scope", help="blueprint | table | column | contract_file"
    ),
    pattern: str = typer.Option(..., "--pattern", help="Regex pattern."),
    description: Optional[str] = typer.Option(
        None, "--description", help="Human-readable description."
    ),
) -> None:
    """Add a naming convention."""
    try:
        convention = add_convention(scope, pattern, description, _db_path())
    except GovernanceError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    # markup=False so a bracketed regex (e.g. [a-z_]) is not parsed as Rich markup.
    console.print(
        f"✓ Convention added: {convention.scope} → {convention.pattern}",
        style="green",
        markup=False,
    )
    raise typer.Exit(0)


@convention_app.command("list")
def convention_list_command() -> None:
    """List all naming conventions."""
    conventions = get_conventions(_db_path())
    if not conventions:
        console.print("No naming conventions defined.")
        raise typer.Exit(0)

    console.print("Naming Conventions", style="bold")
    console.print("─" * 61)
    table = Table()
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Scope")
    table.add_column("Pattern")
    table.add_column("Description")
    for convention in conventions:
        # escape() so a bracketed regex is rendered literally, not as markup.
        table.add_row(
            convention.id,
            convention.scope,
            escape(convention.pattern),
            escape(convention.description or "—"),
        )
    console.print(table)
    raise typer.Exit(0)


@convention_app.command("check")
def convention_check_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to check."),
) -> None:
    """Check a blueprint's names against registered conventions."""
    result = check_blueprint_conventions(blueprint_name, _blueprints_dir(), _db_path())

    console.print(f"Convention Check — {blueprint_name}", style="bold")
    console.print("─" * 55)

    conventions = get_conventions(_db_path())
    if not conventions:
        console.print("No naming conventions defined.")
        console.print(
            "  Add one with 'pipelinekit governance convention add'.", style="dim"
        )
        raise typer.Exit(0)

    for violation in result.violations:
        console.print(
            f"⚠ {violation.name}   {violation.scope}   "
            f"does NOT match {violation.pattern}",
            style="yellow",
            markup=False,
        )

    if result.is_compliant:
        console.print(
            f"\n✓ All {result.checked_count} name(s) comply with "
            f"{len(conventions)} convention(s)",
            style="green",
        )
        raise typer.Exit(0)

    console.print(
        f"\n{result.violation_count} violation(s) found "
        f"across {result.checked_count} name(s) checked.",
        style="yellow",
    )
    raise typer.Exit(1)


@convention_app.command("remove")
def convention_remove_command(
    convention_id: str = typer.Argument(..., help="Convention ID to remove."),
) -> None:
    """Remove a naming convention by ID."""
    removed = remove_convention(convention_id, _db_path())
    if removed:
        console.print("✓ Convention removed", style="green")
    else:
        console.print(f"No convention found with ID {convention_id}")
    raise typer.Exit(0)
