"""``pipelinekit blueprint`` — manage installed blueprints.

Orchestration only: delegates to ``blueprints.registry`` and
``blueprints.validator`` and renders results with Rich. The CLI never executes a
blueprint itself — execution delegates to the runtime (SPEC-006).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.blueprints.remote import RemoteRegistry
from pipelinekit.blueprints.validator import BlueprintValidator
from pipelinekit.core.errors import BlueprintError, RegistryError
from pipelinekit.state import db

console = Console()

blueprint_app = typer.Typer(
    name="blueprint",
    help="Manage PipelineKit blueprints.",
    no_args_is_help=True,
    add_completion=False,
)


@blueprint_app.command("list")
def list_command() -> None:
    """List installed blueprints."""
    blueprints = BlueprintRegistry().list()
    if not blueprints:
        console.print("No blueprints installed.")
        console.print(
            "  Add a blueprint under ./blueprints/ to get started.", style="dim"
        )
        raise typer.Exit(0)

    table = Table(title="Installed blueprints")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version")
    table.add_column("Source")
    table.add_column("Destination")
    for bp in blueprints:
        table.add_row(bp.name, bp.version, bp.source.type, bp.destination.type)
    console.print(table)
    raise typer.Exit(0)


@blueprint_app.command("validate")
def validate_command(
    name: str = typer.Argument(
        None, help="Blueprint to validate. Defaults to all installed blueprints."
    ),
) -> None:
    """Validate blueprint structure against the schema."""
    registry = BlueprintRegistry()
    validator = BlueprintValidator()

    targets = [name] if name else [bp.name for bp in registry.list()]
    if not targets:
        console.print("No blueprints to validate.")
        raise typer.Exit(0)

    failures = 0
    for target in targets:
        blueprint_dir = registry.blueprints_dir / target
        try:
            validator.validate(blueprint_dir)
        except BlueprintError as exc:
            console.print(f"✗ [{exc.code}] {target}: {exc.message}", style="bold red")
            failures += 1
            continue

        contracts = _count_contracts(blueprint_dir)
        dbt = "detected" if (blueprint_dir / "transform").is_dir() else "none"
        quality = "found" if _has_quality(blueprint_dir) else "none"
        console.print(f"✓ Blueprint {target} is valid", style="green")
        console.print("  schema:    valid", style="dim")
        console.print(f"  contracts: {contracts} found", style="dim")
        console.print(f"  dbt:       project {dbt}", style="dim")
        console.print(f"  quality:   checks {quality}", style="dim")

    raise typer.Exit(1 if failures else 0)


@blueprint_app.command("info")
def info_command(name: str = typer.Argument(..., help="Blueprint name.")) -> None:
    """Show details for a single blueprint."""
    blueprint = BlueprintRegistry().get(name)
    if blueprint is None:
        console.print(
            f"✗ [PK-BLUEPRINT-003] Blueprint not found: {name}", style="bold red"
        )
        raise typer.Exit(1)

    console.print(f"{blueprint.name} v{blueprint.version}", style="bold cyan")
    console.print("─" * 40, style="dim")
    console.print(f"Description:  {blueprint.description}")
    console.print(f"Source:       {blueprint.source.type}")
    console.print(f"Destination:  {blueprint.destination.type}")
    console.print(f"Contracts:    {len(blueprint.contracts)}")
    console.print(f"KPIs:         {', '.join(blueprint.kpis) or '—'}")
    console.print(f"Deploy time:  < {blueprint.deploy_time_minutes} minutes")
    console.print(
        f"Time-to-Trusted-Data: < {blueprint.time_to_trusted_data_hours} hours"
    )
    raise typer.Exit(0)


@blueprint_app.command("search")
def search_command(
    query: str = typer.Argument(
        ..., help="Search term: source, destination, name, or tag."
    ),
    verified_only: bool = typer.Option(
        False, "--verified", help="Show only verified blueprints."
    ),
) -> None:
    """Search the remote blueprint registry."""
    try:
        results = RemoteRegistry().search(query)
    except RegistryError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if verified_only:
        results = [r for r in results if r.verified]

    console.print(f'Blueprint Registry Search: "{query}"')
    console.print("─" * 36)
    if not results:
        console.print("\nNo blueprints found.", style="dim")
        raise typer.Exit(0)

    table = Table()
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version")
    table.add_column("Source")
    table.add_column("Destination")
    table.add_column("Verified")
    for entry in results:
        table.add_row(
            entry.name,
            entry.version,
            entry.source,
            entry.destination,
            "✓" if entry.verified else "—",
        )
    console.print(table)
    console.print(
        f"\n{len(results)} blueprint(s) found. "
        "Install with: pipelinekit blueprint install <name>",
        style="dim",
    )
    raise typer.Exit(0)


@blueprint_app.command("install")
def install_command(
    name: str = typer.Argument(..., help="Blueprint name to install."),
    version: str = typer.Option(None, "--version", "-v"),
    force: bool = typer.Option(
        False, "--force", help="Overwrite if already installed."
    ),
) -> None:
    """Install a blueprint from the registry (validated before write)."""
    registry = RemoteRegistry()
    console.print(f"Installing {name}{f' v{version}' if version else ''}...")
    try:
        installed_version = registry.install(name, version, force=force)
    except RegistryError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    # Record the install and surface verification status (best-effort, cached).
    entry = registry.fetch_catalog().get(name, installed_version)
    if entry is not None:
        db.insert_installed_blueprint(
            entry.name,
            installed_version,
            entry.source,
            entry.destination,
            entry.verified,
            entry.url,
        )

    console.print("  ✓ Validated blueprint schema", style="green")
    console.print("  ✓ Verified required assets", style="green")
    console.print(f"  ✓ Written to blueprints/{name}/", style="green")
    verified = entry.verified if entry else False
    if verified:
        console.print(
            f"\n{name} v{installed_version} installed. ✓ Verified blueprint.",
            style="green",
        )
    else:
        console.print(f"\n{name} v{installed_version} installed.", style="green")
        console.print(
            "⚠ This blueprint has not been verified by the Mpingo Systems team.\n"
            "  Review all assets carefully before deploying to production.",
            style="yellow",
        )
    console.print(f"Run 'pipelinekit blueprint info {name}' for details.", style="dim")
    raise typer.Exit(0)


@blueprint_app.command("outdated")
def outdated_command(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show installed blueprint versions against the registry."""
    registry = RemoteRegistry()
    try:
        statuses = registry.version_status()
    except RegistryError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if as_json:
        payload = {
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "blueprints": statuses,
        }
        console.print_json(json.dumps(payload))
        raise typer.Exit(0)

    if not statuses:
        console.print("No installed blueprints to check.")
        console.print(
            "  Install one with: pipelinekit blueprint install <name>", style="dim"
        )
        raise typer.Exit(0)

    console.print("Blueprint Version Status")
    console.print("─" * 56)
    table = Table()
    table.add_column("Blueprint", style="cyan", no_wrap=True)
    table.add_column("Installed")
    table.add_column("Registry")
    table.add_column("Status")
    outdated_count = 0
    for status in statuses:
        if status["outdated"]:
            outdated_count += 1
            label = "⚠ Update available"
        elif status["registry_version"] is None:
            label = "· Not in registry"
        else:
            label = "✓ Up to date"
        table.add_row(
            status["name"],
            status["installed_version"],
            status["registry_version"] or "—",
            label,
        )
    console.print(table)

    if outdated_count:
        console.print(f"\n{outdated_count} blueprint(s) can be upgraded.")
        console.print("Run: pipelinekit blueprint upgrade <name>", style="dim")
    else:
        console.print("\nAll blueprints are up to date.", style="green")
    raise typer.Exit(0)


@blueprint_app.command("upgrade")
def upgrade_command(
    name: str = typer.Argument(..., help="Blueprint to upgrade."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show the upgrade without writing."
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip the confirmation prompt."),
) -> None:
    """Upgrade a blueprint to the latest registry version (with backup)."""
    registry = RemoteRegistry()

    try:
        entry = registry.fetch_catalog().get(name)
    except RegistryError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    if entry is None:
        console.print(
            f"✗ [PK-REGISTRY-004] Blueprint not found in catalog: {name}",
            style="bold red",
        )
        raise typer.Exit(1)

    current = next(
        (s["installed_version"] for s in _safe_status(registry) if s["name"] == name),
        None,
    )
    arrow = f"{current} → {entry.version}" if current else f"→ {entry.version}"

    # Validate the upgrade is available (raises PK-REGISTRY-004 / 006).
    try:
        registry.upgrade(name, dry_run=True)
    except RegistryError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if dry_run:
        console.print(f"Would upgrade {name} {arrow}")
        console.print("No files written.", style="dim")
        raise typer.Exit(0)

    console.print(f"Upgrading {name} {arrow}...")
    changelog = entry.changelog.get(entry.version) if entry.changelog else None
    if changelog:
        console.print(f"\nChanges in {entry.version}:")
        for line in changelog:
            console.print(f"  • {line}", style="dim")

    if not yes and not typer.confirm(
        f"\nUpgrade {name} to v{entry.version}?", default=False
    ):
        console.print("Upgrade cancelled. No files written.", style="dim")
        raise typer.Exit(0)

    try:
        new_version = registry.upgrade(name, yes=yes)
    except RegistryError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print(f"\n✓ {name} upgraded to v{new_version}.", style="green")
    console.print(f"Rollback: pipelinekit blueprint rollback {name}", style="dim")
    raise typer.Exit(0)


@blueprint_app.command("rollback")
def rollback_command(
    name: str = typer.Argument(..., help="Blueprint to roll back."),
    version: str = typer.Option(
        None, "--version", "-v", help="A specific backed-up version to restore."
    ),
) -> None:
    """Restore a blueprint from a local backup created during upgrade."""
    registry = RemoteRegistry()
    suffix = f" to {version}" if version else ""
    console.print(f"Rolling back {name}{suffix}...")
    try:
        restored = registry.rollback(name, version)
    except RegistryError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    console.print(f"✓ {name} rolled back to v{restored}.", style="green")
    raise typer.Exit(0)


def _safe_status(registry: RemoteRegistry) -> list[dict]:
    """Return version status, or an empty list if the registry is unreachable."""
    try:
        return registry.version_status()
    except RegistryError:
        return []


def _count_contracts(blueprint_dir: Path) -> int:
    contracts_dir = blueprint_dir / "contracts"
    if not contracts_dir.is_dir():
        return 0
    return len(list(contracts_dir.glob("*.yaml")))


def _has_quality(blueprint_dir: Path) -> bool:
    quality_dir = blueprint_dir / "quality"
    return quality_dir.is_dir() and any(quality_dir.glob("*.yaml"))
