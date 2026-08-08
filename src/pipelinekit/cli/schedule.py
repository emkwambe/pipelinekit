"""``pipelinekit schedule`` — pipeline schedule management (RM-5).

Orchestration only: delegates schedule logic to ``scheduling.scheduler`` and
renders results with Rich. Resolves the config and state paths but never issues
SQL itself (ADR-003 CLI-first).

The pipeline name always comes from ``pipelinekit.yaml`` — a project has one
configured pipeline, so naming it again on every command would only create a way
for the two to disagree.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.config.loader import load_config
from pipelinekit.core.errors import ConfigurationError, ReleaseError
from pipelinekit.scheduling.scheduler import (
    disable_schedule,
    enable_schedule,
    format_next_run,
    generate_platform_scheduler_entry,
    get_all_schedules,
    get_schedule,
    get_schedule_history,
    remove_schedule,
    set_schedule,
)
from pipelinekit.state import db

console = Console()

schedule_app = typer.Typer(
    help="Pipeline schedule management.",
    no_args_is_help=True,
    add_completion=False,
)


def _db_path() -> str:
    """Resolve the local state database path as a string."""
    return str(db.get_db_path())


def _pipeline_name() -> str:
    """Return the configured pipeline name, or exit 1 with a structured error."""
    try:
        return load_config().pipeline.name
    except ConfigurationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc


def _executable_path() -> str:
    """Return the pipelinekit executable path for generated scheduler entries."""
    found = shutil.which("pipelinekit")
    return found if found else f"{Path(sys.executable).parent / 'pipelinekit'}"


@schedule_app.command("set")
def schedule_set(
    every: float = typer.Option(
        ..., "--every", help="Run interval in hours (e.g. 8 for every 8 hours)."
    ),
    timezone: str = typer.Option(
        "UTC", "--timezone", help="Timezone for scheduling (e.g. America/New_York)."
    ),
) -> None:
    """Schedule automatic pipeline runs."""
    pipeline_name = _pipeline_name()
    try:
        schedule = set_schedule(pipeline_name, every, timezone, _db_path())
    except ReleaseError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    entry = generate_platform_scheduler_entry(
        pipeline_name, every, _executable_path(), str(Path.cwd())
    )

    console.print(f"✓ Schedule set for {pipeline_name}", style="green")
    console.print(f"  Interval:  every {every:g} hours")
    console.print(f"  Timezone:  {schedule.timezone}")
    console.print(f"  Next run:  {format_next_run(schedule)}")
    console.print()
    console.print("To activate on this system:")
    console.print(f"  {entry['instruction']}", style="dim")
    console.print(
        "  PipelineKit records the schedule; it does not install it for you.",
        style="dim",
    )
    raise typer.Exit(0)


@schedule_app.command("list")
def schedule_list() -> None:
    """List all pipeline schedules."""
    schedules = get_all_schedules(_db_path())
    if not schedules:
        console.print("No pipeline schedules set.")
        console.print(
            "  Run: pipelinekit schedule set --every <hours>",
            style="dim",
        )
        raise typer.Exit(0)

    console.print("Pipeline Schedules")
    console.print("─" * 61)
    table = Table()
    table.add_column("Pipeline", style="cyan", no_wrap=True)
    table.add_column("Interval")
    table.add_column("Timezone")
    table.add_column("Status")
    table.add_column("Next run")
    for schedule in schedules:
        status_style = "green" if schedule.is_active() else "yellow"
        table.add_row(
            schedule.pipeline_name,
            f"every {schedule.interval_hours:g}h",
            schedule.timezone,
            f"[{status_style}]{schedule.status}[/{status_style}]",
            format_next_run(schedule) if schedule.is_active() else "—",
        )
    console.print(table)
    raise typer.Exit(0)


@schedule_app.command("history")
def schedule_history(
    limit: int = typer.Option(10, "--limit", help="Number of runs to show."),
    all_pipelines: bool = typer.Option(
        False, "--all", help="Show history across every pipeline."
    ),
) -> None:
    """Show recent scheduled run history."""
    name: Optional[str] = None if all_pipelines else _pipeline_name()
    runs = get_schedule_history(name, limit, _db_path())
    if not runs:
        console.print("No scheduled runs recorded yet.")
        raise typer.Exit(0)

    console.print("Scheduled Run History")
    console.print("─" * 61)
    table = Table()
    table.add_column("Started", no_wrap=True)
    table.add_column("Pipeline", style="cyan")
    table.add_column("Trigger")
    table.add_column("Status")
    table.add_column("Rows", justify="right")
    for run in runs:
        status_style = "green" if run.status == "success" else "red"
        table.add_row(
            run.started_at,
            run.pipeline_name,
            run.triggered_by,
            f"[{status_style}]{run.status}[/{status_style}]",
            f"{run.rows_loaded:,}" if run.rows_loaded is not None else "—",
        )
    console.print(table)
    raise typer.Exit(0)


@schedule_app.command("disable")
def schedule_disable() -> None:
    """Pause the pipeline schedule."""
    pipeline_name = _pipeline_name()
    if disable_schedule(pipeline_name, _db_path()):
        console.print(f"✓ Schedule paused for {pipeline_name}", style="green")
    else:
        console.print(f"No schedule set for {pipeline_name}.")
    raise typer.Exit(0)


@schedule_app.command("enable")
def schedule_enable() -> None:
    """Resume a paused pipeline schedule."""
    pipeline_name = _pipeline_name()
    db_path = _db_path()
    if not enable_schedule(pipeline_name, db_path):
        console.print(f"No schedule set for {pipeline_name}.")
        raise typer.Exit(0)

    schedule = get_schedule(pipeline_name, db_path)
    console.print(f"✓ Schedule resumed for {pipeline_name}", style="green")
    if schedule is not None:
        console.print(f"  Next run:  {format_next_run(schedule)}")
    raise typer.Exit(0)


@schedule_app.command("remove")
def schedule_remove() -> None:
    """Remove the pipeline schedule entirely."""
    pipeline_name = _pipeline_name()
    if remove_schedule(pipeline_name, _db_path()):
        console.print(f"✓ Schedule removed for {pipeline_name}", style="green")
        console.print(
            "  Any OS scheduler entry must be removed separately.", style="dim"
        )
    else:
        console.print(f"No schedule set for {pipeline_name}.")
    raise typer.Exit(0)
