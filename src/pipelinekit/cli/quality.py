"""``pipelinekit quality`` — Quality Management System commands (QM-4).

Orchestration only: delegates coverage scanning to ``quality.coverage`` and
renders results with Rich. Read-only — never writes ``state.db`` (SPEC-022,
ADR-023, ADR-003 CLI-first).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.core.errors import QualityError
from pipelinekit.quality.coverage import (
    BlueprintCoverage,
    CoverageReport,
    compute_coverage_report,
)

console = Console()

quality_app = typer.Typer(
    help="Quality Management System commands.",
    no_args_is_help=True,
    add_completion=False,
)


def _blueprints_dir() -> str:
    """Resolve the installed-blueprints directory as a string."""
    return str(BlueprintRegistry().blueprints_dir)


@quality_app.command("coverage")
def coverage(
    blueprint: Optional[str] = typer.Option(
        None, "--blueprint", help="Filter by blueprint name."
    ),
    format: str = typer.Option(
        "table", "--format", help="Output format: table or json."
    ),
) -> None:
    """Show quality coverage for installed blueprints."""
    if format not in ("table", "json"):
        console.print(
            f"✗ Unknown format: {format}. Use 'table' or 'json'.", style="bold red"
        )
        raise typer.Exit(1)

    report = compute_coverage_report(_blueprints_dir())

    if not report.blueprints:
        error = QualityError(
            "PK-QM-001",
            "No blueprints found for coverage scan",
            {"blueprints_dir": _blueprints_dir()},
        )
        console.print(f"✗ [{error.code}] {error.message}", style="bold red")
        console.print(
            "  Run 'pipelinekit blueprint install <name>' first.", style="dim"
        )
        raise typer.Exit(1)

    if blueprint is not None:
        matches = [bc for bc in report.blueprints if bc.blueprint_name == blueprint]
        if not matches:
            console.print(f"✗ Blueprint not found: {blueprint}", style="bold red")
            raise typer.Exit(1)
        report = CoverageReport(blueprints=matches, generated_at=report.generated_at)

    if format == "json":
        typer.echo(json.dumps(asdict(report), indent=2))
        raise typer.Exit(0)

    _render_table(report)
    raise typer.Exit(0)


def _render_table(report: CoverageReport) -> None:
    """Render the coverage report as Rich tables and summaries."""
    console.print("Quality Coverage Report", style="bold")
    console.print("─" * 59)
    for bc in report.blueprints:
        _render_blueprint(bc)


def _render_blueprint(bc: BlueprintCoverage) -> None:
    """Render a single blueprint's coverage section."""
    console.print(f"\n{bc.blueprint_name}", style="bold cyan")

    console.print("  dbt test coverage")
    table = Table()
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Columns", justify="right")
    table.add_column("Tested Columns", justify="right")
    table.add_column("Coverage", justify="right")
    for model in bc.models:
        table.add_row(
            model.name,
            str(model.total_columns),
            str(model.tested_columns),
            f"{model.coverage_pct:.1f}%",
        )
    console.print(table)
    console.print(
        f"  Blueprint dbt coverage: {bc.blueprint_coverage_pct:.1f}% "
        f"({bc.total_tested_columns}/{bc.total_columns} columns tested)"
    )

    for soda in bc.soda_checks:
        counts = Counter(soda.check_types)
        summary = "   ".join(f"{name}: {count}" for name, count in counts.items())
        console.print(f"\n  Soda checks ({soda.table_name})")
        console.print(f"    {summary}   Total checks: {soda.total_checks}", style="dim")

    if bc.untested_columns:
        width = max(len(model_name) for model_name, _col in bc.untested_columns)
        console.print("\n  Untested columns:")
        for model_name, col in bc.untested_columns:
            console.print(f"    {model_name.ljust(width)}  → {col}", style="dim")
