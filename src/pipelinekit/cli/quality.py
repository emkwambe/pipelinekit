"""``pipelinekit quality`` — Quality Management System commands (QM-4, QM-6).

Orchestration only: delegates coverage scanning to ``quality.coverage`` and
volume anomaly detection to ``quality.anomaly``, rendering results with Rich.
Coverage is read-only; QM-6 records row-count snapshots in ``state.db`` but the
CLI resolves the path and never issues SQL itself (SPEC-022, SPEC-024, ADR-023,
ADR-025, ADR-003 CLI-first).
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
from pipelinekit.quality.anomaly import (
    check_volume_anomalies,
    compute_baseline,
    compute_deviation_pct,
    get_row_count_history,
    record_row_counts,
)
from pipelinekit.quality.coverage import (
    BlueprintCoverage,
    CoverageReport,
    compute_coverage_report,
)
from pipelinekit.state import db

console = Console()

quality_app = typer.Typer(
    help="Quality Management System commands.",
    no_args_is_help=True,
    add_completion=False,
)


def _blueprints_dir() -> str:
    """Resolve the installed-blueprints directory as a string."""
    return str(BlueprintRegistry().blueprints_dir)


def _db_path() -> str:
    """Resolve the local state database path as a string."""
    return str(db.get_db_path())


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


def _parse_table_count(entry: str) -> tuple[str, int]:
    """Parse a ``table:count`` pair, e.g. ``charges:45231``.

    Splits on the last colon so table names remain intact.

    Raises:
        ValueError: if the format is invalid or the count is not an integer.
    """
    name, sep, count = entry.rpartition(":")
    if not sep or not name.strip() or not count.strip():
        raise ValueError(f"Expected table:count, got {entry!r}")
    try:
        return name.strip(), int(count.strip())
    except ValueError as exc:
        raise ValueError(f"Row count is not an integer in {entry!r}") from exc


@quality_app.command("record-counts")
def record_counts(
    blueprint: str = typer.Option(..., "--blueprint", help="Blueprint name."),
    table: list[str] = typer.Option(
        [], "--table", help="table:count pairs e.g. charges:45231"
    ),
) -> None:
    """Record row counts for pipeline tables."""
    if not table:
        console.print(
            "✗ No tables given. Use --table <name>:<count> at least once.",
            style="bold red",
        )
        raise typer.Exit(1)

    try:
        table_counts = dict(_parse_table_count(entry) for entry in table)
    except ValueError as exc:
        console.print(f"✗ Invalid --table value: {exc}", style="bold red")
        raise typer.Exit(1) from exc

    record_row_counts(blueprint, table_counts, _db_path())
    # Re-check against the (now updated) baseline to report per-table status.
    results = check_volume_anomalies(blueprint, table_counts, _db_path())

    console.print(f"✓ Recorded row counts for {blueprint}", style="green")
    width = max((len(t) for t in table_counts), default=0)
    for result in results:
        label = f"{result.table_name}:".ljust(width + 1)
        if result.status == "ESTABLISHING":
            baseline_note = (
                f"baseline: establishing — {result.snapshot_count}/3 snapshots"
            )
        elif result.status == "ANOMALY":
            baseline_note = (
                f"baseline: {result.baseline_avg:,.0f} avg — "
                f"⚠ anomaly ({result.deviation_pct:+.1f}%)"
            )
        else:
            baseline_note = (
                f"baseline: {result.baseline_avg:,.0f} avg — within threshold"
            )
        console.print(f"  {label} {result.current_count:>12,} rows  ({baseline_note})")
    raise typer.Exit(0)


@quality_app.command("check-anomalies")
def check_anomalies(
    blueprint: str = typer.Option(..., "--blueprint", help="Blueprint name."),
    threshold: float = typer.Option(20.0, "--threshold", help="Deviation threshold %."),
) -> None:
    """Check for volume anomalies against baseline."""
    db_path = _db_path()
    tables = db.get_all_tables_for_blueprint(blueprint, db_path)
    if not tables:
        console.print(f"No row count history for {blueprint}.")
        console.print("  Run 'pipelinekit quality record-counts' first.", style="dim")
        raise typer.Exit(0)

    # Current count = the most recent snapshot recorded for each table.
    current_counts: dict[str, int] = {}
    for table_name in tables:
        history = get_row_count_history(blueprint, table_name, db_path, limit=1)
        if history:
            current_counts[table_name] = history[0].row_count

    results = check_volume_anomalies(
        blueprint, current_counts, db_path, threshold_pct=threshold
    )

    console.print(f"Volume Anomaly Check — {blueprint}", style="bold")
    console.print("─" * 43)
    render = Table()
    render.add_column("Table", style="cyan", no_wrap=True)
    render.add_column("Current", justify="right")
    render.add_column("Baseline", justify="right")
    render.add_column("Deviation", justify="right")
    render.add_column("Status")
    for result in results:
        if result.status == "ESTABLISHING":
            baseline_cell = "establishing"
            deviation_cell = f"{result.snapshot_count}/3"
        else:
            baseline_cell = f"{result.baseline_avg:,.0f}"
            deviation_cell = f"{result.deviation_pct:+.1f}%"
        render.add_row(
            result.table_name,
            f"{result.current_count:,}",
            baseline_cell,
            deviation_cell,
            result.status,
        )
    console.print(render)

    anomalies = [r for r in results if r.is_anomaly]
    if anomalies:
        console.print(
            f"⚠ [PK-QM-003] Volume anomaly detected in {blueprint}",
            style="bold yellow",
        )
        for result in anomalies:
            direction = "above" if result.deviation_pct > 0 else "below"
            console.print(
                f"  {result.table_name}: expected ~{result.baseline_avg:,.0f} rows, "
                f"got {result.current_count:,} "
                f"({abs(result.deviation_pct):.1f}% {direction} baseline)",
                style="yellow",
            )
        console.print(
            "  This may indicate: missing partition, failed extraction, "
            "or truncated load.",
            style="dim",
        )
        raise typer.Exit(1)

    console.print("✓ No volume anomalies detected.", style="green")
    raise typer.Exit(0)


@quality_app.command("row-count-history")
def row_count_history(
    blueprint: str = typer.Option(..., "--blueprint", help="Blueprint name."),
    table: str = typer.Option(..., "--table", help="Table name."),
    limit: int = typer.Option(10, "--limit", help="Number of snapshots."),
) -> None:
    """Show row count history for a specific table."""
    history = get_row_count_history(blueprint, table, _db_path(), limit=limit)
    if not history:
        console.print(f"No row count history for {blueprint} / {table}.")
        raise typer.Exit(0)

    mean = compute_baseline(history)
    console.print(f"Row Count History — {blueprint} / {table}", style="bold")
    console.print("─" * 49)
    render = Table()
    render.add_column("Recorded At", style="cyan", no_wrap=True)
    render.add_column("Row Count", justify="right")
    render.add_column("Deviation from mean", justify="right")
    for snapshot in history:
        deviation = compute_deviation_pct(snapshot.row_count, mean)
        render.add_row(
            snapshot.recorded_at,
            f"{snapshot.row_count:,}",
            f"{deviation:+.1f}%",
        )
    console.print(render)
    console.print(f"  Mean over shown snapshots: {mean:,.0f}", style="dim")
    raise typer.Exit(0)
