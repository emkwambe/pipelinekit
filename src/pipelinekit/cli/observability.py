"""``pipelinekit observability`` — Observability Management System (OM-4).

Orchestration only: delegates SLO logic to ``observability.slo`` and renders
results with Rich. Resolves the state database path but never issues SQL itself
(SPEC-025, ADR-026, ADR-003 CLI-first).
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.core.errors import ObservabilityError
from pipelinekit.observability.slo import (
    check_slos,
    get_all_slos,
    remove_slo,
    set_slo,
)
from pipelinekit.state import db

console = Console()

observability_app = typer.Typer(
    help="Observability Management System (OM) commands.",
    no_args_is_help=True,
    add_completion=False,
)
slo_app = typer.Typer(
    help="Service Level Objective (SLO) management.",
    no_args_is_help=True,
    add_completion=False,
)
observability_app.add_typer(slo_app, name="slo")


def _db_path() -> str:
    """Resolve the local state database path as a string."""
    return str(db.get_db_path())


def _threshold_label(slo_type: str, threshold: float, unit: str | None) -> str:
    """Render a human threshold like ``< 6h`` or ``>= 1000``."""
    if slo_type == "freshness":
        return f"< {threshold:g}h"
    if slo_type == "coverage":
        return f">= {threshold:g}%"
    return f">= {threshold:g}"


@slo_app.command("set")
def set_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to assign an SLO."),
    table: str = typer.Option(..., "--table", help="Table or model name."),
    type: str = typer.Option(
        ..., "--type", help="SLO type: freshness | row_count | coverage."
    ),
    threshold: float = typer.Option(..., "--threshold", help="SLO threshold."),
    unit: Optional[str] = typer.Option(
        None, "--unit", help="Unit: hours | rows | percent."
    ),
) -> None:
    """Assign or update an SLO for a blueprint/table."""
    try:
        slo = set_slo(blueprint_name, table, type, threshold, unit, _db_path())
    except ObservabilityError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    label = _threshold_label(slo.slo_type, slo.threshold, slo.unit)
    console.print(
        f"✓ SLO set: {slo.blueprint_name} / {slo.table_name} / "
        f"{slo.slo_type} {label}",
        style="green",
    )
    raise typer.Exit(0)


@slo_app.command("list")
def list_command() -> None:
    """List all defined SLOs."""
    slos = get_all_slos(_db_path())
    if not slos:
        console.print(
            "No SLOs defined. Run 'pipelinekit observability slo set' to add one."
        )
        raise typer.Exit(0)

    console.print("Service Level Objectives", style="bold")
    console.print("─" * 61)
    table = Table()
    table.add_column("Blueprint", style="cyan", no_wrap=True)
    table.add_column("Table")
    table.add_column("Type")
    table.add_column("Threshold", justify="right")
    table.add_column("Unit")
    for slo in slos:
        table.add_row(
            slo.blueprint_name,
            slo.table_name,
            slo.slo_type,
            _threshold_label(slo.slo_type, slo.threshold, slo.unit),
            slo.unit or "—",
        )
    console.print(table)
    raise typer.Exit(0)


@slo_app.command("check")
def check_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to evaluate."),
) -> None:
    """Evaluate SLOs against current state.db data."""
    results = check_slos(blueprint_name, _db_path())
    if not results:
        console.print(f"No SLOs defined for {blueprint_name}.")
        console.print(
            "  Run 'pipelinekit observability slo set' to add one.", style="dim"
        )
        raise typer.Exit(0)

    console.print(f"SLO Check — {blueprint_name}", style="bold")
    console.print("─" * 49)
    render = Table()
    render.add_column("Table", style="cyan", no_wrap=True)
    render.add_column("Type")
    render.add_column("Current", justify="right")
    render.add_column("Threshold", justify="right")
    render.add_column("Status")
    for result in results:
        slo = result.slo
        threshold_cell = _threshold_label(slo.slo_type, slo.threshold, slo.unit)
        if result.status == "NO_DATA":
            current_cell = "—"
        elif slo.slo_type == "freshness":
            current_cell = f"{result.current_value:.1f}h ago"
        elif slo.slo_type == "coverage":
            current_cell = f"{result.current_value:.1f}%"
        else:  # row_count
            current_cell = f"{result.current_value:,.0f}"
        render.add_row(
            slo.table_name,
            slo.slo_type,
            current_cell,
            threshold_cell,
            result.status,
        )
    console.print(render)

    violated = [r for r in results if r.status == "VIOLATED"]
    no_data = [r for r in results if r.status == "NO_DATA"]
    if violated:
        console.print(
            f"⚠ [PK-OM-001] {len(violated)} SLO(s) violated for {blueprint_name}",
            style="bold yellow",
        )
        for result in violated:
            console.print(
                f"  {result.slo.table_name} / {result.slo.slo_type}: "
                f"{result.message}",
                style="yellow",
            )
    if no_data:
        console.print(
            f"— {len(no_data)} SLO(s) have no data yet (NO_DATA).", style="dim"
        )
    if not violated:
        console.print("✓ No SLO violations.", style="green")

    raise typer.Exit(1 if violated else 0)


@slo_app.command("remove")
def remove_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to remove an SLO from."),
    table: str = typer.Option(..., "--table", help="Table or model name."),
    type: str = typer.Option(..., "--type", help="SLO type."),
) -> None:
    """Remove an SLO from a blueprint/table."""
    try:
        removed = remove_slo(blueprint_name, table, type, _db_path())
    except ObservabilityError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if removed:
        console.print(
            f"✓ SLO removed: {blueprint_name} / {table} / {type}", style="green"
        )
    else:
        console.print(f"No SLO found for {blueprint_name}/{table}/{type}")
    raise typer.Exit(0)
