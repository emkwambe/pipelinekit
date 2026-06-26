"""``pipelinekit generate`` / ``pipelinekit apply`` — AI Blueprint Proposal.

Orchestration only (SPEC-015, ADR-018). ``generate blueprint`` proposes; it
never writes by default. ``--plan`` (the safe default) prints a plan and stops.
``--interactive`` reviews each asset and applies the approved ones. ``apply
plan`` writes the assets a human approved. AI proposes — a human approves —
``apply()`` writes. ``can_auto_apply`` is always False.
"""

from __future__ import annotations

import click
import typer
from rich.console import Console
from rich.panel import Panel

from pipelinekit.ai.adapter_registry import AdapterCapabilityRegistry
from pipelinekit.ai.blueprint_proposer import BlueprintProposer
from pipelinekit.ai.proposal_models import BlueprintProposal
from pipelinekit.ai.providers import create_provider
from pipelinekit.config.loader import load_config
from pipelinekit.core.errors import ConfigurationError, LLMError, ProposalError
from pipelinekit.state import db

console = Console()

generate_app = typer.Typer(
    name="generate",
    help="AI-powered blueprint proposals. Review before applying.",
    no_args_is_help=True,
)
apply_app = typer.Typer(
    name="apply",
    help="Apply approved blueprint proposals.",
    no_args_is_help=True,
)


def _load_proposer(provider: str | None):
    """Load config and build a BlueprintProposer, or exit with guidance."""
    try:
        config = load_config()
    except ConfigurationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    if not config.diagnostics.enabled:
        console.print("AI blueprint proposal is disabled.", style="yellow")
        console.print(
            "  Set diagnostics.enabled: true and diagnostics.provider in "
            "pipelinekit.yaml to enable.",
            style="dim",
        )
        raise typer.Exit(0)
    llm = create_provider(config, override=provider)
    return BlueprintProposer(config, llm)


def _render_summary(proposal: BlueprintProposal) -> None:
    """Print the plan summary (no files written)."""
    console.print("\nBlueprint Proposal Ready")
    console.print("━" * 56)
    console.print(f"\nPlan ID:     {proposal.plan_id}")
    console.print(f"Blueprint:   {proposal.blueprint_name}")
    console.print(f"Source:      {proposal.source_type} ({', '.join(proposal.tables)})")
    console.print(f"Destination: {proposal.destination_type}")
    console.print(f"Assets:      {len(proposal.assets)} proposed")
    conf_style = "yellow" if proposal.confidence < 0.7 else "green"
    console.print("Confidence:  ", end="")
    console.print(f"{proposal.confidence:.2f}", style=conf_style)
    if proposal.confidence < 0.7:
        console.print(
            "⚠ Lower confidence than usual — review all assets carefully.",
            style="yellow",
        )
    if proposal.assumptions:
        console.print("\nAssumptions:")
        for a in proposal.assumptions:
            console.print(f"  · {a}", style="dim")
    if proposal.requires_human_decisions:
        console.print("\nRequires your decision:")
        for d in proposal.requires_human_decisions:
            console.print(f"  · {d}", style="dim")
    console.print("\nNo files written.", style="bold")
    console.print(
        f"\nReview:  pipelinekit generate show {proposal.plan_id}", style="dim"
    )
    console.print(f"Apply:   pipelinekit apply plan {proposal.plan_id}", style="dim")


def _explain(asset) -> None:
    """Show provenance for one asset (the [x]explain option)."""
    prov = asset.provenance
    console.print("\n[x]explain:", style="cyan")
    if prov is None:
        console.print("  No provenance recorded.", style="dim")
        return
    console.print("  This asset was proposed based on:")
    for ev in prov.source_evidence:
        console.print(f"  · {ev.get('name')} ({ev.get('type')})", style="dim")
    if prov.assumptions:
        console.print("  Assumptions:")
        for a in prov.assumptions:
            console.print(f"  · {a}", style="dim")
    if prov.requires_human_decisions:
        console.print("  Requires your decision:")
        for d in prov.requires_human_decisions:
            console.print(f"  · {d}", style="dim")


def _review_loop(proposal: BlueprintProposal) -> None:
    """Interactive per-asset review. Mutates asset states in place."""
    source_verified = AdapterCapabilityRegistry().is_source_verified(
        proposal.source_type
    )
    accept_all = False
    total = len(proposal.assets)
    for i, asset in enumerate(proposal.assets, start=1):
        console.print(f"\nAsset {i} of {total}: {asset.filename}")
        console.print("━" * 56)
        console.print(Panel(asset.content, title=asset.asset_type, expand=False))
        if not source_verified:
            console.print(
                "⚠ Unverified adapter source — verify import path before " "deploying.",
                style="yellow",
            )
        if asset.confidence_note:
            console.print(f"Confidence: {asset.confidence_note}", style="dim")
        if asset.validation_error:
            console.print(f"⚠ validation: {asset.validation_error}", style="yellow")

        if accept_all:
            asset.approve()
            continue

        while True:
            choice = (
                typer.prompt(
                    "[a]ccept [r]eject [e]dit [x]explain [y-all]accept remaining "
                    "[q]uit",
                    default="a",
                )
                .strip()
                .lower()
            )
            if choice in ("a", "accept"):
                asset.approve()
                break
            if choice in ("r", "reject"):
                asset.reject()
                break
            if choice in ("e", "edit"):
                new_content = click.edit(asset.content) or asset.content
                asset.edit(new_content)
                asset.repropose()  # edited → proposed (review again next loop)
                asset.approve()
                break
            if choice in ("x", "explain"):
                _explain(asset)
                continue
            if choice in ("y-all", "y"):
                accept_all = True
                asset.approve()
                break
            if choice in ("q", "quit"):
                console.print("Review stopped. Progress saved.", style="dim")
                return
            console.print("  Unrecognized option.", style="dim")


@generate_app.command("blueprint")
def generate_blueprint_command(
    source: str = typer.Option(..., "--source", "-s"),
    destination: str = typer.Option(..., "--destination", "-d"),
    tables: str = typer.Option(..., "--tables", "-t"),
    provider: str = typer.Option(None, "--provider", "-p"),
    name: str = typer.Option(None, "--name", "-n"),
    plan: bool = typer.Option(False, "--plan", help="Plan only, no review."),
    interactive: bool = typer.Option(
        False, "--interactive", help="Review and apply in one session."
    ),
) -> None:
    """Propose a blueprint using AI. Review before applying."""
    proposer = _load_proposer(provider)
    table_list = [t.strip() for t in tables.split(",") if t.strip()]
    console.print(f"Proposing {source}-to-{destination} blueprint...")
    try:
        proposal = proposer.propose(source, destination, table_list)
    except ProposalError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    except LLMError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc

    if interactive:
        _review_loop(proposal)
        db.insert_blueprint_proposal(proposal.to_dict())  # persist approvals
        approved = proposal.approved_assets()
        if approved and typer.confirm(
            f"\nApply {len(approved)} approved asset(s)?", default=False
        ):
            written = proposer.apply(proposal)
            console.print(f"✓ Wrote {len(written)} asset(s).", style="green")
        else:
            console.print(
                f"\nApply later: pipelinekit apply plan {proposal.plan_id}",
                style="dim",
            )
        raise typer.Exit(0)

    # --plan (the safe default): summary only, no files.
    _render_summary(proposal)
    raise typer.Exit(0)


@generate_app.command("show")
def show_command(plan_id: str = typer.Argument(...)) -> None:
    """Show a stored blueprint proposal for review."""
    data = db.get_blueprint_proposal(plan_id)
    if data is None:
        console.print(f"✗ Plan not found: {plan_id}", style="bold red")
        raise typer.Exit(1)
    proposal = BlueprintProposal.from_dict(data)
    _render_summary(proposal)
    console.print("\nAssets:")
    for asset in proposal.assets:
        console.print(f"  [{asset.state.value}] {asset.filename}")
    raise typer.Exit(0)


@apply_app.command("plan")
def apply_plan_command(
    plan_id: str = typer.Argument(...),
    interactive: bool = typer.Option(
        False, "--interactive", help="Review each asset before writing."
    ),
) -> None:
    """Write approved assets from a proposal to blueprints/<name>/.

    Review is required (ADR-018, Smell 13). With ``--interactive`` you review
    each asset, then approved ones are written. Without it, only assets already
    APPROVED from a prior ``generate blueprint --interactive`` session are
    written — otherwise this fails with ``PK-GEN-003``. There is no
    generate → auto-apply shortcut.
    """
    data = db.get_blueprint_proposal(plan_id)
    if data is None:
        console.print(f"✗ Plan not found: {plan_id}", style="bold red")
        raise typer.Exit(1)
    proposal = BlueprintProposal.from_dict(data)

    try:
        config = load_config()
    except ConfigurationError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    proposer = BlueprintProposer(config, provider=None)  # type: ignore[arg-type]

    if interactive:
        _review_loop(proposal)
        db.insert_blueprint_proposal(proposal.to_dict())  # persist approvals

    approved = proposal.approved_assets()
    if not approved:
        console.print(
            "✗ [PK-GEN-003] No approved assets. Use "
            "'generate blueprint --interactive' to review first.",
            style="bold red",
        )
        raise typer.Exit(1)

    try:
        written = proposer.apply(proposal)
    except ProposalError as exc:
        console.print(f"✗ [{exc.code}] {exc.message}", style="bold red")
        raise typer.Exit(1) from exc
    console.print(f"✓ Wrote {len(written)} asset(s):", style="green")
    for path in written:
        console.print(f"  {path}", style="dim")
    raise typer.Exit(0)
