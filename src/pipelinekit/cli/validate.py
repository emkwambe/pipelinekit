"""``pipelinekit validate`` — validate ``pipelinekit.yaml``.

Orchestration only: delegates loading and validation to ``config.loader`` and
renders the structured result with Rich.

See: SPEC-001, SPEC-002.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from pipelinekit.config.loader import load_config
from pipelinekit.core.errors import ConfigurationError

console = Console()


def validate_command() -> None:
    """Validate pipelinekit.yaml configuration."""
    try:
        config = load_config()
    except ConfigurationError as exc:
        lines = [f"[{exc.code}] {exc.message}"]
        for detail in exc.context.get("errors", []):
            lines.append(f"  • {detail}")
        console.print(
            Panel(
                "\n".join(lines),
                title="✗ Configuration validation failed",
                border_style="red",
                expand=False,
            )
        )
        raise typer.Exit(1) from exc

    console.print(
        Panel(
            f"Project: {config.pipeline.name} (v{config.pipeline.version})",
            title="✓ pipelinekit.yaml is valid",
            border_style="green",
            expand=False,
        )
    )
    raise typer.Exit(0)
