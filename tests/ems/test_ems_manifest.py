"""Tests for the EMS manifest and ``pipelinekit ems`` commands (Sprint 23).

Deterministic, no AI, no state.db. The manifest is declarative data; the CLI is
exercised through Typer's ``CliRunner``.
"""

from __future__ import annotations

from pipelinekit.cli.ems import ems_app
from pipelinekit.ems.manifest import (
    EMS_MANIFEST,
    compute_coverage,
    get_all_ems,
    get_ems,
)
from typer.testing import CliRunner

runner = CliRunner()


def test_ems_manifest_has_twelve_systems() -> None:
    """EMS_MANIFEST contains exactly 12 EMS definitions."""
    assert len(EMS_MANIFEST) == 12
    assert len(get_all_ems()) == 12


def test_get_ems_returns_correct_definition() -> None:
    """get_ems('DC') returns Data Contract Management (EMS-008)."""
    ems = get_ems("DC")
    assert ems is not None
    assert ems.name == "Data Contract Management"
    assert ems.ems_id == "EMS-008"


def test_get_ems_case_insensitive() -> None:
    """get_ems('dc') and get_ems('DC') return the same definition."""
    assert get_ems("dc") is get_ems("DC")


def test_get_ems_returns_none_for_unknown_code() -> None:
    """get_ems('XX') returns None."""
    assert get_ems("XX") is None


def test_compute_coverage_dc_is_complete() -> None:
    """DC has 11+ built capabilities out of 12 planned."""
    ems = get_ems("DC")
    assert ems is not None
    built, planned = compute_coverage(ems)
    assert planned == 12
    assert built >= 11


def test_compute_coverage_km_is_zero() -> None:
    """KM has 0 built capabilities (not started)."""
    ems = get_ems("KM")
    assert ems is not None
    built, _ = compute_coverage(ems)
    assert built == 0


def test_all_ems_have_total_planned() -> None:
    """Every EMS declares a positive total_planned."""
    assert all(e.total_planned > 0 for e in EMS_MANIFEST)


def test_ems_list_command_runs() -> None:
    """`pipelinekit ems list` runs without error."""
    result = runner.invoke(ems_app, ["list"])
    assert result.exit_code == 0
    assert "Engineering Management Systems" in result.stdout


def test_ems_status_dc_runs() -> None:
    """`pipelinekit ems status dc` runs and shows the DC system."""
    result = runner.invoke(ems_app, ["status", "dc"])
    assert result.exit_code == 0
    assert "Data Contract Management" in result.stdout


def test_ems_status_unknown_exits_1() -> None:
    """`pipelinekit ems status xx` exits with code 1."""
    result = runner.invoke(ems_app, ["status", "xx"])
    assert result.exit_code == 1
