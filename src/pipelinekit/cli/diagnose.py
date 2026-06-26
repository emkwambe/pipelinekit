"""``pipelinekit diagnose`` — AI-assisted root cause analysis.

Orchestration only: loads config, builds a provider via the AI provider factory,
runs the ``DiagnosticsEngine``, and renders the ``DiagnosticResult`` with Rich.
The CLI never executes a recommended action — actions are shown for human review
(ADR-007, Smell 13).
"""

from __future__ import annotations

import typer
from rich.console import Console

from pipelinekit.ai.diagnostics import DiagnosticsEngine
from pipelinekit.ai.evidence import EvidenceCollector
from pipelinekit.ai.models import DiagnosticResult
from pipelinekit.ai.providers import create_provider
from pipelinekit.config.loader import load_config
from pipelinekit.core.errors import ConfigurationError, DiagnosticsError, LLMError

console = Console()


def _render(result: DiagnosticResult) -> None:
    """Render a diagnostic result with Rich."""
    if result.status == "inconclusive":
        console.print(
            f"⚠ Diagnosis inconclusive (confidence: {result.confidence:.2f})",
            style="yellow",
        )
        console.print(
            "\nInsufficient evidence to determine root cause.\n"
            "Run 'pipelinekit status' to check recent run history.",
            style="dim",
        )
        return

    console.print(f"Finding:     {result.finding_type}")
    console.print(f"Confidence:  {result.confidence:.2f}")
    console.print(f"Status:      {result.status}")
    if result.explanation:
        console.print("\nExplanation:")
        console.print(f"  {result.explanation}")

    if result.evidence:
        console.print("\nEvidence used:")
        for item in result.evidence:
            detail = item.get("detail") or item.get("type") or str(item)
            console.print(f"  · {detail}")

    if result.recommended_actions:
        console.print("\nRecommended actions:")
        for i, action in enumerate(result.recommended_actions, start=1):
            console.print(f"  {i}. [{action.risk_level} risk] {action.action}")
        console.print(
            "\nRun with --approve to review actions interactively.", style="dim"
        )


def _review_actions(result: DiagnosticResult) -> None:
    """Present recommended actions for human approval. Never executes them."""
    if not result.recommended_actions:
        console.print("No recommended actions to review.", style="dim")
        return
    approved: list[str] = []
    total = len(result.recommended_actions)
    for i, action in enumerate(result.recommended_actions, start=1):
        console.print(
            f"\nAction {i} of {total}: {action.action}\n"
            f"Risk: {action.risk_level} | Reversible: "
            f"{'yes' if action.reversible else 'no'}"
        )
        if typer.confirm("Approve?", default=False):
            approved.append(action.action)
    console.print(
        f"\n{len(approved)} action(s) approved. Execute them manually — "
        "PipelineKit records approval but never runs actions.",
        style="dim",
    )


def diagnose_command(
    run_id: str = typer.Argument(
        None, help="Run ID to diagnose. Defaults to the most recent run."
    ),
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="AI provider override: anthropic | openai | ollama | deepseek | mistral",
    ),
    approve: bool = typer.Option(
        False, "--approve", help="Interactively review recommended actions."
    ),
) -> None:
    """Diagnose a pipeline run using AI-assisted root cause analysis."""
    try:
        config = load_config()
    except ConfigurationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if not config.diagnostics.enabled:
        console.print("AI diagnostics are disabled.", style="yellow")
        console.print(
            "  Set diagnostics.enabled: true and diagnostics.provider in "
            "pipelinekit.yaml to enable.",
            style="dim",
        )
        raise typer.Exit(0)

    try:
        resolved_run_id = run_id or EvidenceCollector().get_most_recent_run_id()
        console.print(f"Diagnosing {resolved_run_id}...\n")
        llm_provider = create_provider(config, override=provider)
        engine = DiagnosticsEngine(config, llm_provider)
        result = engine.diagnose(resolved_run_id)
    except (DiagnosticsError, LLMError) as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print("✓ Evidence collected\n", style="green")
    _render(result)
    if approve:
        _review_actions(result)
    raise typer.Exit(0)
