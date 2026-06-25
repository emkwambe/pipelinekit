"""``pipelinekit init`` — create a new project configuration.

Orchestration only: delegates file generation to ``config.loader`` and the
``.gitignore`` update to ``state.db``.

See: SPEC-001, SPEC-007.
"""

from __future__ import annotations

import typer
from rich.console import Console

from pipelinekit.config.loader import config_exists, write_default_config
from pipelinekit.core.errors import PipelineKitError
from pipelinekit.state.db import ensure_gitignore_entry

console = Console()


def init_command() -> None:
    """Initialize a new PipelineKit project in the current directory."""
    if config_exists():
        console.print(
            "⚠ pipelinekit.yaml already exists. Not overwritten.",
            style="yellow",
        )
        console.print(
            "  Run 'pipelinekit validate' to check your configuration.",
            style="dim",
        )
        raise typer.Exit(0)

    try:
        write_default_config()
        ensure_gitignore_entry()
    except PipelineKitError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print("✓ Created pipelinekit.yaml", style="green")
    console.print("  Edit this file to configure your pipeline.", style="dim")
    console.print(
        "  Run 'pipelinekit validate' to check your configuration.",
        style="dim",
    )
    raise typer.Exit(0)
