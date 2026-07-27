"""Integration tests for ``pipelinekit quality`` — real SQLite state via CLI."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()

_INSTALLED = ["stripe-to-snowflake", "postgres-to-snowflake", "salesforce-to-snowflake"]


def test_quality_record_counts_exits_zero(project: str) -> None:
    """`quality record-counts` runs without error."""
    result = runner.invoke(
        app,
        [
            "quality",
            "record-counts",
            "--blueprint",
            "stripe-to-snowflake",
            "--table",
            "charges:45231",
            "--table",
            "customers:12840",
        ],
    )
    assert result.exit_code == 0


def test_quality_check_anomalies_establishing_with_no_history(project: str) -> None:
    """`check-anomalies` reports ESTABLISHING with fewer than 3 snapshots."""
    runner.invoke(
        app,
        [
            "quality",
            "record-counts",
            "--blueprint",
            "stripe-to-snowflake",
            "--table",
            "charges:45231",
        ],
    )
    result = runner.invoke(
        app, ["quality", "check-anomalies", "--blueprint", "stripe-to-snowflake"]
    )
    assert result.exit_code == 0
    assert "ESTABLISHING" in result.output


def test_quality_coverage_exits_zero(project: str) -> None:
    """`quality coverage` runs and reports on installed blueprints."""
    result = runner.invoke(app, ["quality", "coverage"])
    assert result.exit_code == 0
    assert "Coverage" in result.output


def test_quality_scorecard_exits_zero(project: str) -> None:
    """`quality scorecard` runs without error."""
    result = runner.invoke(app, ["quality", "scorecard"])
    assert result.exit_code == 0


def test_quality_scorecard_shows_blueprint_names(project: str) -> None:
    """`quality scorecard` lists at least one installed blueprint."""
    result = runner.invoke(app, ["quality", "scorecard"])
    assert result.exit_code == 0
    assert any(bp in result.output for bp in _INSTALLED)


def test_quality_check_regression_no_baseline(project: str) -> None:
    """`check-regression` reports clean when history is insufficient."""
    result = runner.invoke(app, ["quality", "check-regression"])
    assert result.exit_code == 0
    assert "no regression" in result.output.lower()


def test_quality_freshness_set_and_list(project: str) -> None:
    """`freshness set` then `list` shows the requirement."""
    result = runner.invoke(
        app,
        [
            "quality",
            "freshness",
            "set",
            "stripe-to-snowflake",
            "--table",
            "charges",
            "--hours",
            "6",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(app, ["quality", "freshness", "list"])
    assert result.exit_code == 0
    assert "charges" in result.output
    assert "6" in result.output
