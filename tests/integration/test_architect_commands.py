"""Integration tests for ``pipelinekit architect`` dependency + drift commands."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def _add_dependency() -> list[str]:
    return [
        "architect",
        "dependency",
        "add",
        "postgres-to-snowflake",
        "stripe-to-snowflake",
        "--type",
        "manual",
        "--reason",
        "orders feed stripe reconciliation",
    ]


def test_dependency_scan_exits_zero(project: str) -> None:
    """`architect dependency scan` runs without error."""
    result = runner.invoke(app, ["architect", "dependency", "scan"])
    assert result.exit_code == 0


def test_dependency_list_empty_initially(project: str) -> None:
    """`architect dependency list` reports none on fresh state."""
    result = runner.invoke(app, ["architect", "dependency", "list"])
    assert result.exit_code == 0
    assert "No dependencies" in result.output


def test_dependency_add_and_list(project: str) -> None:
    """`architect dependency add` then `list` shows both endpoints."""
    result = runner.invoke(app, _add_dependency())
    assert result.exit_code == 0

    result = runner.invoke(app, ["architect", "dependency", "list"])
    assert result.exit_code == 0
    assert "postgres-to-snowflake" in result.output
    assert "stripe-to-snowflake" in result.output


def test_dependency_impact_exits_zero(project: str) -> None:
    """`architect dependency impact` runs and reflects an added edge."""
    runner.invoke(app, _add_dependency())
    result = runner.invoke(
        app, ["architect", "dependency", "impact", "postgres-to-snowflake"]
    )
    assert result.exit_code == 0
    assert "stripe-to-snowflake" in result.output


def test_architect_drift_no_dependencies(project: str) -> None:
    """`architect drift` on fresh state reports nothing to check (exit 0)."""
    result = runner.invoke(app, ["architect", "drift"])
    assert result.exit_code == 0
    assert "No dependencies" in result.output


def test_architect_drift_clean_for_manual_edge(project: str) -> None:
    """`architect drift` treats a manual dependency as valid (exit 0)."""
    runner.invoke(app, _add_dependency())
    result = runner.invoke(app, ["architect", "drift"])
    assert result.exit_code == 0
    assert "0 drifted" in result.output
