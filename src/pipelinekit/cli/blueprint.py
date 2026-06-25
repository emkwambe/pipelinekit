"""``pipelinekit blueprint`` — manage installed blueprints.

Orchestration only: delegates to ``blueprints.registry`` and
``blueprints.validator`` and renders results with Rich. The CLI never executes a
blueprint itself — execution delegates to the runtime (SPEC-006).
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.blueprints.validator import BlueprintValidator
from pipelinekit.core.errors import BlueprintError

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


def _count_contracts(blueprint_dir: Path) -> int:
    contracts_dir = blueprint_dir / "contracts"
    if not contracts_dir.is_dir():
        return 0
    return len(list(contracts_dir.glob("*.yaml")))


def _has_quality(blueprint_dir: Path) -> bool:
    quality_dir = blueprint_dir / "quality"
    return quality_dir.is_dir() and any(quality_dir.glob("*.yaml"))
