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
from pipelinekit.governance.approval import (
    approve_request,
    create_request,
    get_approver,
    get_pending_requests,
    reject_request,
    set_approver,
)
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

approver_app = typer.Typer(
    help="Blueprint approver management.",
    no_args_is_help=True,
    add_completion=False,
)
governance_app.add_typer(approver_app, name="approver")

approval_app = typer.Typer(
    help="Pipeline change approval workflow.",
    no_args_is_help=True,
    add_completion=False,
)
governance_app.add_typer(approval_app, name="approval")


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


# --- GM-3: approval workflow -----------------------------------------------


@approver_app.command("set")
def approver_set_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to assign an approver."),
    name: str = typer.Option(..., "--name", help="Approver name."),
    email: str = typer.Option(..., "--email", help="Approver email."),
) -> None:
    """Assign or update the approver of a blueprint."""
    approver = set_approver(blueprint_name, name, email, _db_path())
    console.print(
        f"✓ Approver set for {approver.blueprint_name}: "
        f"{approver.approver_name} <{approver.approver_email}>",
        style="green",
    )
    raise typer.Exit(0)


@approver_app.command("get")
def approver_get_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to look up."),
) -> None:
    """Show the approver of a blueprint."""
    approver = get_approver(blueprint_name, _db_path())
    if approver is None:
        console.print(f"No approver set for {blueprint_name}")
        raise typer.Exit(0)

    console.print(f"Approver: {approver.blueprint_name}", style="bold cyan")
    console.print("─" * 37)
    console.print(f"  Name:    {approver.approver_name}")
    console.print(f"  Email:   {approver.approver_email}")
    console.print(f"  Set at:  {approver.updated_at}")
    raise typer.Exit(0)


@approval_app.command("request")
def approval_request_command(
    blueprint: str = typer.Option(..., "--blueprint", help="Blueprint name."),
    change: str = typer.Option(..., "--change", help="Description of the change."),
    requested_by: str = typer.Option(
        ..., "--requested-by", help="Email of the requester."
    ),
) -> None:
    """Create an approval request for a pipeline change."""
    db_path = _db_path()
    request = create_request(blueprint, change, requested_by, db_path)

    console.print(f"✓ Approval request created: {request.request_code}", style="green")
    console.print(f"  Blueprint:    {request.blueprint_name}")
    console.print(f"  Change:       {request.change_description}")
    console.print(f"  Requested by: {request.requested_by}")

    approver = get_approver(blueprint, db_path)
    if approver is not None:
        console.print(
            f"  Awaiting approval from: {approver.approver_name} "
            f"<{approver.approver_email}>"
        )
    else:
        console.print("  No approver set for this blueprint", style="yellow")
    raise typer.Exit(0)


@approval_app.command("list")
def approval_list_command() -> None:
    """List pending approval requests."""
    pending = get_pending_requests(_db_path())
    if not pending:
        console.print("No pending approval requests.")
        raise typer.Exit(0)

    console.print("Pending Approval Requests", style="bold")
    console.print("─" * 61)
    table = Table()
    table.add_column("Code", style="cyan", no_wrap=True)
    table.add_column("Blueprint")
    table.add_column("Change")
    table.add_column("Requested By")
    table.add_column("Status")
    table.add_column("Created")
    for request in pending:
        table.add_row(
            request.request_code,
            request.blueprint_name,
            request.change_description,
            request.requested_by,
            request.status,
            request.created_at,
        )
    console.print(table)
    raise typer.Exit(0)


@approval_app.command("approve")
def approval_approve_command(
    request_code: str = typer.Argument(..., help="Request code, e.g. REQ-001."),
    decided_by: str = typer.Option(
        "CLI user", "--decided-by", help="Who approved the request."
    ),
) -> None:
    """Approve a pending request."""
    try:
        approve_request(request_code, decided_by, _db_path())
    except GovernanceError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print(f"✓ {request_code} approved", style="green")
    raise typer.Exit(0)


@approval_app.command("reject")
def approval_reject_command(
    request_code: str = typer.Argument(..., help="Request code, e.g. REQ-001."),
    decided_by: str = typer.Option(
        "CLI user", "--decided-by", help="Who rejected the request."
    ),
    reason: Optional[str] = typer.Option(
        None, "--reason", help="Reason for rejection."
    ),
) -> None:
    """Reject a pending request."""
    try:
        reject_request(request_code, decided_by, reason, _db_path())
    except GovernanceError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if reason:
        console.print(f"✓ {request_code} rejected: {reason}", style="green")
    else:
        console.print(f"✓ {request_code} rejected", style="green")
    raise typer.Exit(0)
