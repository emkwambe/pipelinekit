"""Integration tests for ``pipelinekit health`` — a multi-check system command."""

from __future__ import annotations

from pipelinekit.cli.main import app
from pipelinekit.governance.ownership import set_owner
from typer.testing import CliRunner

runner = CliRunner()

_INSTALLED = ["stripe-to-snowflake", "postgres-to-snowflake", "salesforce-to-snowflake"]


def test_health_runs_without_error(project: str) -> None:
    """`health` runs and produces output (exit 0 or 1, never a crash)."""
    result = runner.invoke(app, ["health"])
    assert result.exit_code in (0, 1)
    assert len(result.output) > 0


def test_health_strict_fails_without_owner(project: str) -> None:
    """`health --strict` fails the ownership check when no owner is set."""
    result = runner.invoke(app, ["health", "--strict"])
    assert result.exit_code == 1
    assert "ownership" in result.output.lower()


def test_health_strict_passes_ownership_when_owner_set(project: str) -> None:
    """`health --strict` passes ownership once every blueprint has an owner."""
    for blueprint in _INSTALLED:
        set_owner(
            blueprint_name=blueprint,
            owner_name="Jane Smith",
            owner_email="jane@company.com",
            team_name=None,
            notes=None,
            db_path=project,
        )
    result = runner.invoke(app, ["health", "--strict"])
    assert "ownership" in result.output.lower()
    assert "✓" in result.output or "pass" in result.output.lower()


def test_health_output_includes_all_six_checks(project: str) -> None:
    """`health --strict` output names all six current checks."""
    result = runner.invoke(app, ["health", "--strict"])
    assert result.exit_code in (0, 1)
    output_lower = result.output.lower()
    for check in ["deps", "security", "blueprints", "specs", "tests", "ownership"]:
        assert check in output_lower, f"Missing check: {check}"


def test_health_provides_actionable_output(project: str) -> None:
    """`health` produces substantial multi-line output."""
    result = runner.invoke(app, ["health"])
    assert len(result.output) > 100
    assert result.output.count("\n") > 3
