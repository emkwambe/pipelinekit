"""``pipelinekit staging`` — staging → production promotion (RM-4).

Orchestration only: delegates promotion logic to ``staging.promoter`` and
renders results with Rich (ADR-003 CLI-first).

``promote`` mutates production, so it is never implicit — the operator asks for
it, and the command refuses when the recorded run is not in a promotable state.
"""

from __future__ import annotations

import typer
from rich.console import Console

from pipelinekit.config.loader import load_config
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import ConfigurationError, ReleaseError
from pipelinekit.staging.promoter import (
    BUILDING,
    PROMOTED,
    ROLLED_BACK,
    TESTS_PASSING,
    StagingPromoter,
)
from pipelinekit.state import db

console = Console()

staging_app = typer.Typer(
    help="Staging → production promotion.",
    no_args_is_help=True,
    add_completion=False,
)

# A run may be promoted while it is still building or once its tests pass —
# anything already promoted or rolled back is terminal.
_PROMOTABLE = (BUILDING, TESTS_PASSING)


def _config() -> PipelineConfig:
    """Load config, or exit 1 with a structured error."""
    try:
        return load_config()
    except ConfigurationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc


def _promoter(config: PipelineConfig) -> StagingPromoter:
    """Build a promoter for the configured DuckDB destination, or exit 1."""
    destination = config.ingestion.destination
    if destination.type != "duckdb" or not destination.path:
        console.print(
            "✗ [PK-RM-005] Staging promotion currently supports DuckDB "
            f"destinations only (destination type: {destination.type}).",
            style="bold red",
        )
        raise typer.Exit(1)
    return StagingPromoter(destination.path, str(db.get_db_path()))


@staging_app.command("status")
def staging_status() -> None:
    """Show current staging run status."""
    config = _config()
    promoter = _promoter(config)
    run = promoter.get_staging_status(config.pipeline.name)

    if run is None:
        console.print("No staging runs recorded.")
        if not config.transformation.staging.enabled:
            console.print(
                "  Staging is disabled. Enable it under "
                "transformation.staging.enabled in pipelinekit.yaml.",
                style="dim",
            )
        raise typer.Exit(0)

    style = {
        PROMOTED: "green",
        ROLLED_BACK: "yellow",
    }.get(run.status, "cyan")

    console.print(f"Staging Run — {run.pipeline_name}", style="bold cyan")
    console.print("─" * 45)
    console.print(f"  Status:      [{style}]{run.status}[/{style}]")
    console.print(f"  Staging:     {run.staging_schema}")
    console.print(f"  Production:  {run.production_schema}")
    console.print(f"  Started:     {run.started_at}")
    console.print(f"  Promoted:    {run.promoted_at or '—'}")
    console.print(
        f"  Rows staged: {run.rows_staged:,}"
        if run.rows_staged is not None
        else "  Rows staged: —"
    )
    if run.error:
        console.print(f"  Error:       {run.error}", style="red")
    raise typer.Exit(0)


@staging_app.command("promote")
def staging_promote() -> None:
    """Manually promote staging to production."""
    config = _config()
    promoter = _promoter(config)
    run = promoter.get_staging_status(config.pipeline.name)

    if run is None:
        console.print("No staging run to promote.")
        raise typer.Exit(1)
    if run.status not in _PROMOTABLE:
        console.print(
            f"✗ Staging run is '{run.status}' — nothing to promote.",
            style="bold red",
        )
        raise typer.Exit(1)

    try:
        promoted = promoter.promote_to_production(
            run.staging_schema, run.production_schema, run.id
        )
    except ReleaseError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if not promoted:
        current = promoter.get_staging_status(config.pipeline.name)
        detail = current.error if current and current.error else "promotion failed"
        console.print(f"✗ {detail}", style="bold red")
        console.print("  Production is unchanged.", style="dim")
        raise typer.Exit(1)

    console.print(
        f"✓ Promoted {run.staging_schema} → {run.production_schema}", style="green"
    )
    raise typer.Exit(0)


@staging_app.command("rollback")
def staging_rollback() -> None:
    """Rollback: drop staging, production untouched."""
    config = _config()
    promoter = _promoter(config)
    run = promoter.get_staging_status(config.pipeline.name)

    if run is None:
        console.print("No staging run to roll back.")
        raise typer.Exit(1)

    try:
        rolled_back = promoter.rollback(
            run.staging_schema, run.production_schema, run.id
        )
    except ReleaseError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if not rolled_back:
        console.print("✗ Rollback failed.", style="bold red")
        raise typer.Exit(1)

    console.print(f"✓ Dropped staging schema {run.staging_schema}", style="green")
    console.print(f"  Production {run.production_schema} untouched.", style="dim")
    raise typer.Exit(0)
