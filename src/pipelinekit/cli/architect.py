"""``pipelinekit architect`` — AI-native architecture reasoning (SPEC-011) and
blueprint dependency analysis (AM-4, SPEC-026).

Orchestration only: loads config, builds a provider via the AI provider factory,
runs the ``ArchitectureEngine``, and renders the ``ArchitectureResult`` with Rich.
The CLI never applies a recommendation — recommendations are shown for human
review and decisions are recorded, never executed (ADR-007, ADR-015, Smell 13).
The ``dependency`` sub-app delegates to ``architecture.dependency`` and resolves
the state database path but never issues SQL itself (SPEC-026, ADR-027).
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pipelinekit.ai.arch_engine import ArchitectureEngine
from pipelinekit.ai.arch_models import ArchitectureResult
from pipelinekit.ai.providers import create_provider
from pipelinekit.architecture.dependency import (
    add_dependency,
    get_dependencies,
    get_impact_report,
    remove_dependency,
    scan_dependencies,
)
from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.config.loader import load_config
from pipelinekit.core.errors import ArchitectureError, ConfigurationError, LLMError
from pipelinekit.state import db

console = Console()

architect_app = typer.Typer(
    name="architect",
    help="AI-native architecture reasoning for your analytics stack.",
    no_args_is_help=True,
)

_VALID_TYPES = (
    "tool_selection",
    "cost_optimization",
    "adr_compliance",
    "stack_evolution",
    "blueprint_selection",
)


def _render(result: ArchitectureResult) -> None:
    """Render an architecture result with Rich."""
    rec = result.recommendation
    console.print(f"Reasoning type:  {result.reasoning_type}")
    console.print(f"Confidence:      {result.confidence:.2f}")
    console.print("\nRecommendation:")
    console.print(f"  {rec.action}")
    if rec.tool_from or rec.tool_to:
        console.print(f"  ({rec.tool_from or '—'} → {rec.tool_to or '—'})", style="dim")
    if rec.rationale:
        console.print("\nRationale:")
        console.print(f"  {rec.rationale}")

    if result.tradeoffs:
        console.print("\nTradeoffs:")
        for t in result.tradeoffs:
            console.print(f"  {t.dimension:<14} {t.direction}  ({t.evidence})")

    if result.adr_compliance:
        console.print("\nADR compliance:")
        for c in result.adr_compliance:
            mark = "✓ compliant" if c.compliant else "✗ conflict"
            note = f" — {c.note}" if c.note else ""
            console.print(f"  {c.adr_id}: {mark}{note}")

    if result.explanation:
        console.print("\nExplanation:")
        console.print(f"  {result.explanation}")

    console.print(
        "\nThis is advisory. PipelineKit never applies architecture changes.",
        style="dim",
    )


def _review(result: ArchitectureResult) -> None:
    """Present the recommendation for human approval. Never executes it."""
    rec = result.recommendation
    console.print(
        f"\nProposed change: {rec.action}\n"
        f"Effort: {rec.effort} | Reversible: {'yes' if rec.reversible else 'no'}"
    )
    decision = typer.confirm("Record approval of this recommendation?", default=False)
    verdict = "approved" if decision else "declined"
    console.print(
        f"\nDecision recorded: {verdict}. PipelineKit records the decision but "
        "never applies architecture changes — act on it manually.",
        style="dim",
    )


def _run(
    reasoning_type: str,
    question: str | None,
    provider: str | None,
    approve: bool = False,
) -> None:
    """Shared orchestration for every architect subcommand."""
    try:
        config = load_config()
    except ConfigurationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if not config.diagnostics.enabled:
        console.print("AI architecture reasoning is disabled.", style="yellow")
        console.print(
            "  Set diagnostics.enabled: true and diagnostics.provider in "
            "pipelinekit.yaml to enable.",
            style="dim",
        )
        raise typer.Exit(0)

    if reasoning_type not in _VALID_TYPES:
        console.print(
            f"✗ Unknown reasoning type: '{reasoning_type}'. "
            f"Choose one of: {', '.join(_VALID_TYPES)}.",
            style="bold red",
        )
        raise typer.Exit(1)

    console.print("Analyzing architecture...\n")
    try:
        llm_provider = create_provider(config, override=provider)
        engine = ArchitectureEngine(config, llm_provider)
        result = engine.analyze(reasoning_type, question=question)
    except ArchitectureError as exc:
        if exc.code == "PK-ARCH-004":
            # Insufficient history is expected on young projects — not an error.
            console.print(f"⚠ {exc.message}", style="yellow")
            console.print("  Run more pipelines, then try again.", style="dim")
            raise typer.Exit(0) from exc
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    except LLMError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print("✓ Context collected\n", style="green")
    _render(result)
    if approve:
        _review(result)
    raise typer.Exit(0)


@architect_app.command("analyze")
def analyze_command(
    question: str = typer.Argument(
        None, help="Natural language architecture question."
    ),
    type_: str = typer.Option(
        "tool_selection",
        "--type",
        "-t",
        help="tool_selection | cost_optimization | adr_compliance | "
        "stack_evolution | blueprint_selection",
    ),
    provider: str = typer.Option(None, "--provider", "-p"),
    approve: bool = typer.Option(
        False, "--approve", help="Review the recommendation and record a decision."
    ),
) -> None:
    """Analyze your analytics architecture and get AI-powered recommendations."""
    _run(type_, question, provider, approve=approve)


@architect_app.command("check-adrs")
def check_adrs_command(
    change: str = typer.Argument(
        ..., help="Proposed change to check for ADR compliance."
    ),
    provider: str = typer.Option(None, "--provider", "-p"),
) -> None:
    """Check whether a proposed change complies with your ADRs."""
    _run("adr_compliance", change, provider)


@architect_app.command("compare")
def compare_command(
    tool_a: str = typer.Argument(...),
    tool_b: str = typer.Argument(...),
    provider: str = typer.Option(None, "--provider", "-p"),
) -> None:
    """Compare two tools for your specific stack and data profile."""
    question = f"Compare {tool_a} versus {tool_b} for this data profile."
    _run("tool_selection", question, provider)


# --- AM-4: blueprint dependency analysis ----------------------------------

dep_app = typer.Typer(
    help="Blueprint dependency management.",
    no_args_is_help=True,
    add_completion=False,
)
architect_app.add_typer(dep_app, name="dependency")


def _db_path() -> str:
    """Resolve the local state database path as a string."""
    return str(db.get_db_path())


def _blueprints_dir() -> str:
    """Resolve the installed-blueprints directory as a string."""
    return str(BlueprintRegistry().blueprints_dir)


@dep_app.command("scan")
def scan_command() -> None:
    """Auto-detect dependencies from blueprint files."""
    blueprints_dir = _blueprints_dir()
    root = BlueprintRegistry().blueprints_dir
    count = sum(1 for entry in root.glob("*") if entry.is_dir()) if root.is_dir() else 0
    console.print(f"Scanning {count} blueprint(s) for dependencies...")
    detected = scan_dependencies(blueprints_dir, _db_path())
    if detected:
        console.print(
            f"✓ Found {len(detected)} auto-detected dependency(ies)", style="green"
        )
        for dep in detected:
            console.print(
                f"  {dep.from_blueprint} → {dep.to_blueprint} "
                f"({dep.dependency_type})",
                style="dim",
            )
    else:
        console.print(
            "✓ No auto-detected dependencies found "
            "(add manual dependencies with 'dependency add')",
            style="green",
        )
    raise typer.Exit(0)


@dep_app.command("list")
def list_command() -> None:
    """List all blueprint dependencies."""
    deps = get_dependencies(_db_path())
    if not deps:
        console.print("No dependencies defined.")
        raise typer.Exit(0)

    console.print("Blueprint Dependencies", style="bold")
    console.print("─" * 61)
    table = Table()
    table.add_column("From", style="cyan", no_wrap=True)
    table.add_column("To", no_wrap=True)
    table.add_column("Type")
    table.add_column("Reason")
    table.add_column("Detected")
    for dep in deps:
        table.add_row(
            dep.from_blueprint,
            dep.to_blueprint,
            dep.dependency_type,
            dep.reason or "—",
            dep.detected_at,
        )
    console.print(table)
    raise typer.Exit(0)


@dep_app.command("add")
def add_command(
    from_blueprint: str = typer.Argument(..., help="Upstream (producer) blueprint."),
    to_blueprint: str = typer.Argument(..., help="Downstream (consumer) blueprint."),
    type: str = typer.Option(
        ..., "--type", help="Dependency type: contract | dbt_source | manual."
    ),
    reason: Optional[str] = typer.Option(
        None, "--reason", help="Why the dependency exists."
    ),
) -> None:
    """Add a manual blueprint dependency."""
    try:
        dep = add_dependency(
            from_blueprint, to_blueprint, type, reason, _blueprints_dir(), _db_path()
        )
    except ArchitectureError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print(
        f"✓ Dependency added: {dep.from_blueprint} → {dep.to_blueprint} "
        f"({dep.dependency_type})",
        style="green",
    )
    raise typer.Exit(0)


@dep_app.command("remove")
def remove_command(
    from_blueprint: str = typer.Argument(..., help="Upstream (producer) blueprint."),
    to_blueprint: str = typer.Argument(..., help="Downstream (consumer) blueprint."),
) -> None:
    """Remove a blueprint dependency."""
    removed = remove_dependency(from_blueprint, to_blueprint, _db_path())
    if removed:
        console.print(
            f"✓ Dependency removed: {from_blueprint} → {to_blueprint}", style="green"
        )
    else:
        console.print(f"No dependency found for {from_blueprint} → {to_blueprint}")
    raise typer.Exit(0)


@dep_app.command("impact")
def impact_command(
    blueprint_name: str = typer.Argument(..., help="Blueprint to analyze."),
) -> None:
    """Show which blueprints are affected if this blueprint changes."""
    report = get_impact_report(blueprint_name, _db_path())

    console.print(f"Impact Analysis — {blueprint_name}", style="bold")
    console.print("─" * 49)
    if report.total_affected == 0:
        console.print(f"No blueprints depend on {blueprint_name}")
        raise typer.Exit(0)

    console.print(f"If {blueprint_name} changes, these blueprints may be affected:")
    for dep in report.affected_blueprints:
        reason = f": {dep.reason}" if dep.reason else ""
        console.print(f"  → {dep.to_blueprint} ({dep.dependency_type}{reason})")
    console.print(f"{report.total_affected} blueprint(s) depend on {blueprint_name}")
    raise typer.Exit(0)
