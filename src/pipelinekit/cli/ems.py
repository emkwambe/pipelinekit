"""EMS packaging layer CLI — ``ems list`` and ``ems status``.

Read-only navigation over the declarative EMS manifest. Turns the flat command
surface into the twelve named Engineering Management Systems with per-system
capability coverage. No state, no AI, no side effects.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.ems.manifest import compute_coverage, get_all_ems, get_ems

ems_app = typer.Typer(
    help="Engineering Management System (EMS) catalog and status.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

STATUS_SYMBOL = {
    "built": "✅",
    "partial": "◑",
    "planned": "📋",
    "not_started": "○",
}


def _fmt(n: float) -> str:
    """Render a coverage count without a trailing ``.0`` (9.0→9, 11.5→11.5)."""
    return str(int(n)) if n == int(n) else str(n)


@ems_app.command("list")
def ems_list() -> None:
    """List all twelve Engineering Management Systems with coverage."""
    table = Table(
        title="PipelineKit — Engineering Management Systems",
        show_header=True,
        header_style="bold",
    )
    table.add_column("EMS", style="bold", width=4, no_wrap=True)
    table.add_column("System", width=24)
    table.add_column("Built", justify="right", width=5, no_wrap=True)
    table.add_column("Plan", justify="right", width=4, no_wrap=True)
    table.add_column("Coverage", width=15, no_wrap=True)
    table.add_column("Commands", width=20)

    total_built = 0.0
    total_planned = 0

    for ems in get_all_ems():
        built, planned = compute_coverage(ems)
        total_built += built
        total_planned += planned
        pct = int(built / planned * 100) if planned > 0 else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        commands = " | ".join(ems.cli_commands) if ems.cli_commands else "—"
        table.add_row(
            ems.code,
            ems.name,
            _fmt(built),
            str(planned),
            f"{bar} {pct}%",
            commands,
        )

    console.print(table)
    total_pct = int(total_built / total_planned * 100) if total_planned else 0
    console.print(
        f"\n[bold]Total:[/bold] {_fmt(total_built)}/{total_planned} "
        f"capabilities built ({total_pct}% of full EMS vision)"
    )


@ems_app.command("status")
def ems_status(
    ems_code: str = typer.Argument(..., help="EMS code (e.g. dc, qm, gm)."),
) -> None:
    """Show detailed capability status for one EMS."""
    ems = get_ems(ems_code)
    if ems is None:
        console.print(
            f"[bold red]Unknown EMS code: '{ems_code}'.[/bold red] "
            "Run 'pipelinekit ems list' to see valid codes."
        )
        raise typer.Exit(1)

    built, planned = compute_coverage(ems)
    pct = int(built / planned * 100) if planned > 0 else 0

    console.print(f"\n[bold]{ems.name}[/bold] ({ems.ems_id})")
    console.print(f"{ems.description}\n")
    console.print(f"Coverage: {_fmt(built)}/{planned} capabilities ({pct}%)\n")

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("", width=3)
    table.add_column("Code", width=10)
    table.add_column("Capability", width=36)
    table.add_column("Phase", width=10)
    for cap in ems.capabilities:
        symbol = STATUS_SYMBOL.get(cap.status, "?")
        table.add_row(symbol, cap.code, cap.name, cap.phase or "—")
    console.print(table)

    if ems.cli_commands:
        joined = " | ".join(f"pipelinekit {c}" for c in ems.cli_commands)
        console.print(f"\n[bold]CLI:[/bold] {joined}")
    if ems.state_tables:
        console.print(f"[bold]State:[/bold] {', '.join(ems.state_tables)}")
    console.print()
    raise typer.Exit(0)
