"""``pipelinekit architect`` — AI-native architecture reasoning (SPEC-011).

Orchestration only: loads config, builds a provider via the AI provider factory,
runs the ``ArchitectureEngine``, and renders the ``ArchitectureResult`` with Rich.
The CLI never applies a recommendation — recommendations are shown for human
review and decisions are recorded, never executed (ADR-007, ADR-015, Smell 13).
"""

from __future__ import annotations

import typer
from rich.console import Console

from pipelinekit.ai.arch_engine import ArchitectureEngine
from pipelinekit.ai.arch_models import ArchitectureResult
from pipelinekit.ai.providers import create_provider
from pipelinekit.config.loader import load_config
from pipelinekit.core.errors import ArchitectureError, ConfigurationError, LLMError

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
