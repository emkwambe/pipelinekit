"""``pipelinekit health`` — the programmed Sustainability Policy (SPEC-012).

Orchestration only: each subcommand runs one checker and renders its result;
the no-argument form runs all five, prints a summary, and records the run in
state.db. Health is non-blocking — it exits 0 even with warnings so it can run
in any cadence without breaking scripts. Only ``--strict`` exits 1 on warnings.
"""

from __future__ import annotations

import json

import typer
from rich.console import Console

from pipelinekit.health import ERROR, INFO, OK, WARNING, HealthCheckResult
from pipelinekit.health.blueprints import BlueprintHealthChecker
from pipelinekit.health.deps import DepsChecker
from pipelinekit.health.ownership import OwnershipHealthChecker
from pipelinekit.health.security import SecurityChecker
from pipelinekit.health.specs import SpecDriftChecker
from pipelinekit.health.tests import TestsChecker
from pipelinekit.state import db

console = Console()

_GLYPH = {OK: "✓", WARNING: "⚠", ERROR: "✗", INFO: "·"}
_STYLE = {OK: "green", WARNING: "yellow", ERROR: "bold red", INFO: "dim"}

health_app = typer.Typer(
    name="health",
    help="Check PipelineKit installation and project health.",
    no_args_is_help=False,
)


def _run_all() -> list[HealthCheckResult]:
    """Run every health check in display order."""
    return [
        DepsChecker().check(),
        SecurityChecker().check(),
        BlueprintHealthChecker().check(),
        SpecDriftChecker().check(),
        TestsChecker().check(),
        OwnershipHealthChecker().check(),
    ]


def _overall(results: list[HealthCheckResult]) -> str:
    """Reduce per-check statuses to a single overall status."""
    statuses = {r.status for r in results}
    if ERROR in statuses:
        return ERROR
    if WARNING in statuses:
        return WARNING
    return OK


def _glyph(status: str) -> str:
    """Return the styled glyph markup for a status."""
    return f"[{_STYLE.get(status, 'dim')}]{_GLYPH.get(status, '?')}[/]"


def _render_one(result: HealthCheckResult) -> None:
    """Render a single check's result with its details."""
    console.print(f"{_glyph(result.status)}  {result.message}")
    for detail in result.details or []:
        console.print(f"    {detail}", style="dim")
    if result.fix_hint:
        console.print(f"\n  {result.fix_hint}", style="dim")


def _render_summary(results: list[HealthCheckResult]) -> None:
    """Render the full-run summary table and any issues."""
    console.print("PipelineKit Health Check")
    console.print("────────────────────────\n")
    for result in results:
        console.print(f"  {result.name:<12} {_glyph(result.status)}  {result.message}")

    passed = sum(1 for r in results if r.status in (OK, INFO))
    console.print(f"\n{passed}/{len(results)} checks passed")

    issues = [r for r in results if r.status in (WARNING, ERROR)]
    if issues:
        console.print("\nIssues:")
        for result in issues:
            console.print(f"  {result.name}: {result.message}", style="dim")
            if result.fix_hint:
                console.print(f"    {result.fix_hint}", style="dim")

    console.print("\nRun 'pipelinekit health <check>' for details.", style="dim")


def _record(results: list[HealthCheckResult]) -> None:
    """Persist the health run to state.db. Recording never blocks the command."""
    by_name = {r.name: r for r in results}
    summary = {
        "deps_status": by_name["deps"].status,
        "security_status": by_name["security"].status,
        "blueprints_status": by_name["blueprints"].status,
        "specs_status": by_name["specs"].status,
        "tests_status": by_name["tests"].status,
        "overall_status": _overall(results),
        "summary": json.dumps([r.to_dict() for r in results]),
    }
    try:
        db.insert_health_run(summary)
    except Exception:
        # State recording is best-effort here; a check command must still report.
        console.print("  (could not record health run to state.db)", style="dim")


@health_app.callback(invoke_without_command=True)
def health_command(
    ctx: typer.Context,
    strict: bool = typer.Option(
        False, "--strict", help="Exit 1 if any check is a warning or error."
    ),
) -> None:
    """Run all health checks. Use a subcommand for an individual check."""
    if ctx.invoked_subcommand is not None:
        return
    results = _run_all()
    _render_summary(results)
    _record(results)
    if strict and any(r.status in (WARNING, ERROR) for r in results):
        raise typer.Exit(1)
    raise typer.Exit(0)


@health_app.command("deps")
def deps_command() -> None:
    """Check for outdated dependencies."""
    _render_one(DepsChecker().check())
    raise typer.Exit(0)


@health_app.command("security")
def security_command() -> None:
    """Check for known security vulnerabilities (requires pip-audit)."""
    _render_one(SecurityChecker().check())
    raise typer.Exit(0)


@health_app.command("blueprints")
def blueprints_command() -> None:
    """Validate all installed blueprints against their schemas."""
    _render_one(BlueprintHealthChecker().check())
    raise typer.Exit(0)


@health_app.command("specs")
def specs_command(
    fix: bool = typer.Option(
        False, "--fix", help="Rewrite drifted SPEC status headers to Implemented."
    ),
) -> None:
    """Check SPEC status headers for drift (Approved vs Implemented)."""
    checker = SpecDriftChecker()
    if fix:
        count = checker.fix()
        console.print(f"✓ Updated {count} SPEC status header(s).", style="green")
        raise typer.Exit(0)
    _render_one(checker.check())
    raise typer.Exit(0)


@health_app.command("tests")
def tests_command() -> None:
    """Report the last test run's coverage."""
    _render_one(TestsChecker().check())
    raise typer.Exit(0)


@health_app.command("ownership")
def ownership_command() -> None:
    """Warn about installed blueprints that have no assigned owner."""
    _render_one(OwnershipHealthChecker().check())
    raise typer.Exit(0)
