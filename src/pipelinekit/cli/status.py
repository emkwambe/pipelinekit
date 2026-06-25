"""``pipelinekit status`` — show recent pipeline run history.

Orchestration only: delegates all state access to ``state.db`` and renders the
result with Rich.

See: SPEC-001, SPEC-007.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.core.errors import StateError
from pipelinekit.state.db import get_recent_runs, initialize

console = Console()


def _format_duration(duration_s: float | None) -> str:
    """Render a duration in seconds, or ``-`` when not yet recorded."""
    if duration_s is None:
        return "-"
    return f"{duration_s:.1f}s"


def status_command() -> None:
    """Show recent pipeline run history."""
    try:
        initialize()
        runs = get_recent_runs(n=5)
    except StateError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if not runs:
        console.print("No runs recorded yet.")
        console.print("Run 'pipelinekit run' to execute your pipeline.", style="dim")
        raise typer.Exit(0)

    table = Table(title="Recent pipeline runs")
    table.add_column("Run ID", style="cyan", no_wrap=True)
    table.add_column("Status")
    table.add_column("Started")
    table.add_column("Duration", justify="right")
    for run in runs:
        table.add_row(
            run["id"],
            run["status"],
            run["started_at"],
            _format_duration(run["duration_s"]),
        )
    console.print(table)
    raise typer.Exit(0)
