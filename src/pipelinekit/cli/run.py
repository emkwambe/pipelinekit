"""``pipelinekit run`` — execute the configured pipeline.

Orchestration only: the CLI loads config, calls ``PipelineRunner`` (the runtime
entry point — never its internals), and renders the returned ``PipelineResult``.
It never touches adapters or providers directly (SPEC-001, SPEC-003).
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.config.loader import load_config
from pipelinekit.core.errors import ConfigurationError
from pipelinekit.runtime.result import PipelineResult, PipelineStatus
from pipelinekit.runtime.runner import PipelineRunner

console = Console()


def _format_duration(duration_s: float) -> str:
    return f"{duration_s:.1f}s"


def _render_validation(result: PipelineResult) -> None:
    """Render a dry-run validation summary."""
    if result.status == PipelineStatus.VALID:
        console.print("✓ Dry run: configuration and adapters valid", style="green")
    else:
        console.print("✗ Dry run: validation reported problems", style="bold red")

    if not result.steps:
        console.print("  No adapters enabled for this pipeline.", style="dim")
        return

    table = Table(title="Adapter validation")
    table.add_column("Step", no_wrap=True)
    table.add_column("Status")
    table.add_column("Detail")
    for step in result.steps:
        detail = (
            f"[{step.error_code}] {step.error_msg}" if step.error_code else "reachable"
        )
        table.add_row(step.step, step.status.value, detail)
    console.print(table)


def _render_run(result: PipelineResult) -> None:
    """Render a full run summary."""
    if result.succeeded():
        console.print("✓ Pipeline completed successfully", style="green")
    else:
        console.print("✗ Pipeline failed", style="bold red")

    if not result.steps:
        console.print("  No steps were executed.", style="dim")
        return

    table = Table(title="Pipeline run")
    table.add_column("Step", no_wrap=True)
    table.add_column("Status")
    table.add_column("Duration", justify="right")
    table.add_column("Rows", justify="right")
    table.add_column("Error")
    for step in result.steps:
        error = f"[{step.error_code}] {step.error_msg}" if step.error_code else ""
        rows = f"{step.rows_processed:,}" if step.rows_processed else "—"
        table.add_row(
            step.step,
            step.status.value,
            _format_duration(step.duration_s),
            rows,
            error,
        )
    console.print(table)
    console.print(f"  Total: {_format_duration(result.duration_s)}", style="dim")


def run_command(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate adapters without executing the pipeline.",
    ),
) -> None:
    """Execute the configured pipeline."""
    try:
        config = load_config()
    except ConfigurationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    runner = PipelineRunner(config)

    if dry_run:
        _render_validation(runner.validate())
        raise typer.Exit(0)

    result = runner.run()
    _render_run(result)
    raise typer.Exit(0 if result.succeeded() else 1)
