"""``pipelinekit validate`` — validate ``pipelinekit.yaml`` and optionally contracts.

Orchestration only: delegates config loading to ``config.loader`` and contract
loading/validation to ``contracts``. Renders structured results with Rich.

The ``--contracts`` flag (Phase 2) loads and structurally validates the data
contracts declared by the project. Data-level checks against a live warehouse
run during ``pipelinekit run`` (they require a database connection); this flag
verifies the contract definitions are present and well-formed.

See: SPEC-001, SPEC-002, SPEC-004.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from pipelinekit.config.loader import load_config
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.contracts.validator import ContractValidator
from pipelinekit.core.errors import ConfigurationError, ContractError

console = Console()


def _validate_contracts(config: PipelineConfig) -> int:
    """Load and structurally validate data contracts. Returns an exit code."""
    if not config.contracts.enabled:
        console.print(
            "ℹ Contracts are disabled (contracts.enabled = false).", style="dim"
        )
        return 0

    contracts_dir = Path(config.contracts.directory)
    validator = ContractValidator(contracts_dir)
    try:
        definitions = validator.load_all_contracts()
    except ContractError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        return 1

    if not definitions:
        console.print(f"✓ No data contracts found in {contracts_dir}.", style="green")
        return 0

    table_names = ", ".join(d.table for d in definitions)
    console.print(
        Panel(
            f"Loaded {len(definitions)} contract(s): {table_names}\n"
            "Definitions are well-formed. Data-level checks run during "
            "'pipelinekit run'.",
            title="✓ Data contracts valid",
            border_style="green",
            expand=False,
        )
    )
    return 0


def validate_command(
    contracts: bool = typer.Option(
        False,
        "--contracts",
        help="Also validate data contracts declared by the project.",
    ),
) -> None:
    """Validate pipelinekit.yaml and optionally data contracts."""
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

    if not contracts:
        raise typer.Exit(0)

    raise typer.Exit(_validate_contracts(config))
