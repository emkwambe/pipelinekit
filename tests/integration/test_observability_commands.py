"""Integration tests for ``pipelinekit observability`` — real SQLite state via CLI."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def _set_slo() -> list[str]:
    return [
        "observability",
        "slo",
        "set",
        "stripe-to-snowflake",
        "--table",
        "charges",
        "--type",
        "row_count",
        "--threshold",
        "1000",
    ]


def test_slo_set_exits_zero(project: str) -> None:
    """`observability slo set` runs without error."""
    result = runner.invoke(app, _set_slo())
    assert result.exit_code == 0


def test_slo_list_shows_defined_slos(project: str) -> None:
    """`observability slo list` shows a defined SLO."""
    runner.invoke(app, _set_slo())
    result = runner.invoke(app, ["observability", "slo", "list"])
    assert result.exit_code == 0
    assert "charges" in result.output
    assert "row_count" in result.output


def test_slo_check_no_data_status(project: str) -> None:
    """`observability slo check` returns NO_DATA before any pipeline data."""
    runner.invoke(app, _set_slo())
    result = runner.invoke(
        app, ["observability", "slo", "check", "stripe-to-snowflake"]
    )
    assert result.exit_code == 0
    assert "NO_DATA" in result.output


def test_slo_remove_exits_zero(project: str) -> None:
    """`observability slo remove` removes a defined SLO."""
    runner.invoke(app, _set_slo())
    result = runner.invoke(
        app,
        [
            "observability",
            "slo",
            "remove",
            "stripe-to-snowflake",
            "--table",
            "charges",
            "--type",
            "row_count",
        ],
    )
    assert result.exit_code == 0


def test_observability_dashboard_exits_zero(project: str) -> None:
    """`observability dashboard` runs and reports no history on fresh state."""
    result = runner.invoke(app, ["observability", "dashboard"])
    assert result.exit_code == 0
    assert "No SLO run history" in result.output
