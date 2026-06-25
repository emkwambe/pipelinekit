"""Tests for the health CLI group (SPEC-012). Checkers are mocked — no I/O."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

from pipelinekit.cli.health import health_app
from pipelinekit.health import OK, WARNING, HealthCheckResult
from pipelinekit.state import db
from typer.testing import CliRunner

runner = CliRunner()

_NAMES = ["deps", "security", "blueprints", "specs", "tests"]


def _all_ok() -> list[HealthCheckResult]:
    return [HealthCheckResult(n, OK, f"{n} ok") for n in _NAMES]


def test_full_run_exits_zero(tmp_path, monkeypatch):
    """pipelinekit health runs all checks and exits 0."""
    monkeypatch.chdir(tmp_path)
    with patch("pipelinekit.cli.health._run_all", return_value=_all_ok()):
        result = runner.invoke(health_app, [])
    assert result.exit_code == 0
    assert "Health Check" in result.stdout


def test_full_run_records_health_run(tmp_path, monkeypatch):
    """A full run is recorded in the health_runs table."""
    monkeypatch.chdir(tmp_path)
    with patch("pipelinekit.cli.health._run_all", return_value=_all_ok()):
        runner.invoke(health_app, [])
    with sqlite3.connect(db.get_db_path(tmp_path)) as conn:
        rows = conn.execute("SELECT overall_status FROM health_runs").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == OK


def test_strict_exits_one_on_warning(tmp_path, monkeypatch):
    """--strict exits 1 when any check is a warning."""
    monkeypatch.chdir(tmp_path)
    results = [HealthCheckResult("deps", WARNING, "outdated")] + [
        HealthCheckResult(n, OK, "ok") for n in _NAMES[1:]
    ]
    with patch("pipelinekit.cli.health._run_all", return_value=results):
        result = runner.invoke(health_app, ["--strict"])
    assert result.exit_code == 1


def test_deps_subcommand_renders(tmp_path, monkeypatch):
    """The deps subcommand renders a single result and exits 0."""
    monkeypatch.chdir(tmp_path)
    fake = MagicMock()
    fake.return_value.check.return_value = HealthCheckResult("deps", OK, "all current")
    with patch("pipelinekit.cli.health.DepsChecker", fake):
        result = runner.invoke(health_app, ["deps"])
    assert result.exit_code == 0
    assert "all current" in result.stdout


def test_specs_fix_subcommand(tmp_path, monkeypatch):
    """specs --fix reports the number of headers updated and exits 0."""
    monkeypatch.chdir(tmp_path)
    fake = MagicMock()
    fake.return_value.fix.return_value = 2
    with patch("pipelinekit.cli.health.SpecDriftChecker", fake):
        result = runner.invoke(health_app, ["specs", "--fix"])
    assert result.exit_code == 0
    assert "Updated 2" in result.stdout
