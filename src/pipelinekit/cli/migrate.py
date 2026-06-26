"""``pipelinekit migrate analyze`` — Migration Intelligence (SPEC-017, ADR-020).

Reads an existing pipeline config (Airbyte, Fivetran, custom Python, existing
pipelinekit.yaml) and proposes a PipelineKit migration. ``analyze`` writes
nothing; ``--apply`` writes ``pipelinekit.proposed.yaml`` (never
``pipelinekit.yaml``) and only when no blocking gap remains — ``--force``
overrides. AI reads — AI proposes — a human approves — apply writes.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from pipelinekit.ai.migration_analyzer import MigrationAnalyzer
from pipelinekit.ai.migration_models import MappingStatus, MigrationProposal
from pipelinekit.ai.providers import create_provider
from pipelinekit.config.loader import load_config
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import ConfigurationError, LLMError, MigrationError

console = Console()

migrate_app = typer.Typer(
    name="migrate",
    help="Migrate existing pipelines to PipelineKit.",
    no_args_is_help=True,
)


def _fallback_config(provider: str | None) -> PipelineConfig:
    """Build a minimal config when no pipelinekit.yaml exists yet.

    Migration is the path *to* a pipelinekit.yaml, so the working directory may
    not have one. The provider is taken from ``--provider`` (BYOK key from env).
    """
    return PipelineConfig.model_validate(
        {
            "pipeline": {"name": "migration"},
            "runtime": {},
            "ingestion": {
                "source": {"type": "unknown"},
                "destination": {"type": "unknown"},
            },
            "transformation": {},
            "contracts": {},
            "quality": {},
            "diagnostics": {"enabled": True, "provider": provider or "none"},
            "notifications": {},
        }
    )


def _build_analyzer(provider: str | None) -> MigrationAnalyzer:
    """Load config (or synthesise a minimal one) and build a MigrationAnalyzer."""
    try:
        config = load_config()
    except ConfigurationError:
        config = _fallback_config(provider)
    llm = create_provider(config, override=provider)
    return MigrationAnalyzer(config, llm)


_STATUS_GLYPH = {
    MappingStatus.CLEAN: "✓",
    MappingStatus.PARTIAL: "⚠",
    MappingStatus.MANUAL: "•",
    MappingStatus.UNSUPPORTED: "✗",
}


def _render(proposal: MigrationProposal) -> None:
    """Print the migration analysis."""
    counts = {status: 0 for status in MappingStatus}
    for mapping in proposal.mappings:
        counts[mapping.status] += 1

    console.print("\nMigration Analysis")
    console.print("━" * 56)
    console.print(f"\nSource tool: {proposal.source_tool}")
    conf_style = "yellow" if proposal.confidence < 0.7 else "green"
    console.print("Confidence:  ", end="")
    console.print(f"{proposal.confidence:.2f}", style=conf_style)
    console.print(
        f"Mapping:     {counts[MappingStatus.CLEAN]} clean · "
        f"{counts[MappingStatus.PARTIAL]} partial · "
        f"{counts[MappingStatus.UNSUPPORTED]} unsupported"
    )

    if proposal.blueprint_recommendation:
        installed = (
            "installed ✓"
            if _is_installed(proposal.blueprint_recommendation)
            else "not installed"
        )
        console.print(
            f"\nBlueprint recommendation:  {proposal.blueprint_recommendation} "
            f"({installed})"
        )

    if proposal.mappings:
        console.print("\nMappings:")
        for mapping in proposal.mappings:
            glyph = _STATUS_GLYPH.get(mapping.status, "•")
            target = mapping.pipelinekit_equivalent or "—"
            console.print(
                f"  {glyph} {mapping.field}: {mapping.source_value} → {target}"
            )
            if mapping.note:
                console.print(f"    Note: {mapping.note}", style="dim")

    if proposal.gaps:
        console.print(f"\nGaps ({proposal.blocking_gaps} blocking):")
        for gap in proposal.gaps:
            glyph = "✗" if gap.blocking else "•"
            console.print(f"  {glyph} {gap.gap_type.upper()}: {gap.description}")
            console.print(f"    Action: {gap.required_action}", style="dim")

    if proposal.assumptions:
        console.print("\nAssumptions:")
        for assumption in proposal.assumptions:
            console.print(f"  · {assumption}", style="dim")


def _is_installed(name: str) -> bool:
    """Return True if a blueprint of this name is installed locally."""
    from pipelinekit.blueprints.registry import BlueprintRegistry

    return BlueprintRegistry().exists(name)


@migrate_app.command("analyze")
def analyze_command(
    config: str = typer.Argument(..., help="Path to existing pipeline config"),
    provider: str = typer.Option(None, "--provider", "-p"),
    apply: bool = typer.Option(
        False, "--apply", help="Write draft pipelinekit.proposed.yaml after analysis"
    ),
    force: bool = typer.Option(
        False, "--force", help="Apply even if blocking gaps exist"
    ),
) -> None:
    """Analyse an existing pipeline config and propose a PipelineKit migration."""
    config_path = Path(config)
    console.print(f"Analyzing {config_path.name}...")

    analyzer = _build_analyzer(provider)
    try:
        proposal = analyzer.analyze(config_path)
    except MigrationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    except LLMError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    console.print(f"Detected: {proposal.source_tool}")
    _render(proposal)

    if not apply:
        console.print(
            "\nNo files written. Re-run with --apply to write "
            "pipelinekit.proposed.yaml.",
            style="dim",
        )
        raise typer.Exit(0)

    try:
        path = analyzer.apply(proposal, force=force)
    except MigrationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    console.print(f"\n✓ Draft written to: {path}", style="green")
    console.print(
        "Review it, fill in the gaps, then run: pipelinekit validate", style="dim"
    )
    raise typer.Exit(0)
