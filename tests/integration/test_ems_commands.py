"""Integration tests for ``pipelinekit ems`` — the EMS packaging layer.

Pure-data commands: no state.db, no blueprints needed.
"""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()

_ALL_CODES = ["DC", "QM", "GM", "OM", "AM", "AI", "RM", "KM", "CM", "SM", "CO", "DM"]


def test_ems_list_exits_zero() -> None:
    """`ems list` runs without error."""
    result = runner.invoke(app, ["ems", "list"])
    assert result.exit_code == 0


def test_ems_list_shows_all_twelve_systems() -> None:
    """`ems list` output contains all 12 EMS codes."""
    result = runner.invoke(app, ["ems", "list"])
    assert result.exit_code == 0
    for code in _ALL_CODES:
        assert code in result.output


def test_ems_list_shows_coverage_percentage() -> None:
    """`ems list` includes percentage coverage and a total line."""
    result = runner.invoke(app, ["ems", "list"])
    assert result.exit_code == 0
    assert "%" in result.output
    assert "Total" in result.output


def test_ems_status_dc_exits_zero() -> None:
    """`ems status dc` runs without error."""
    result = runner.invoke(app, ["ems", "status", "dc"])
    assert result.exit_code == 0


def test_ems_status_dc_shows_built_capabilities() -> None:
    """`ems status dc` shows the built DC capabilities."""
    result = runner.invoke(app, ["ems", "status", "dc"])
    assert result.exit_code == 0
    for code in ["DC-8", "DC-9", "DC-10", "DC-11"]:
        assert code in result.output


def test_ems_status_qm_shows_complete() -> None:
    """`ems status qm` shows Quality Management at 100%."""
    result = runner.invoke(app, ["ems", "status", "qm"])
    assert result.exit_code == 0
    assert "Quality Management" in result.output
    assert "100%" in result.output


def test_ems_status_km_shows_not_started() -> None:
    """`ems status km` shows Knowledge Management at 0%."""
    result = runner.invoke(app, ["ems", "status", "km"])
    assert result.exit_code == 0
    assert "Knowledge Management" in result.output
    assert "0%" in result.output


def test_ems_status_unknown_code_exits_one() -> None:
    """`ems status xx` exits 1 for an unknown EMS."""
    result = runner.invoke(app, ["ems", "status", "xx"])
    assert result.exit_code == 1


def test_ems_status_case_insensitive() -> None:
    """`ems status DC` and `ems status dc` both succeed."""
    assert runner.invoke(app, ["ems", "status", "DC"]).exit_code == 0
    assert runner.invoke(app, ["ems", "status", "dc"]).exit_code == 0


def test_ems_status_ai_shows_reconciled_codes() -> None:
    """`ems status ai` reflects the ADR-043 reconciliation (AI-13/14/15 built)."""
    result = runner.invoke(app, ["ems", "status", "ai"])
    assert result.exit_code == 0
    assert "AI-13" in result.output
    assert "AI-15" in result.output
