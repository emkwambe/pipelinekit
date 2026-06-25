"""Tests for ``pipelinekit status`` (SPEC-001, SPEC-007)."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_status_no_runs(tmp_path, monkeypatch):
    """status prints 'No runs recorded yet.' on fresh state."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["status"])
    assert "No runs recorded yet." in result.output


def test_status_exits_zero(tmp_path, monkeypatch):
    """status exits 0 even with no runs."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0


def test_status_initializes_db(tmp_path, monkeypatch):
    """status creates .pipelinekit/state.db if not present."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["status"])
    assert (tmp_path / ".pipelinekit" / "state.db").is_file()


def test_status_shows_run_table(tmp_path, monkeypatch):
    """status renders a table row once a run has been recorded."""
    monkeypatch.chdir(tmp_path)
    from pipelinekit.state import db

    db.insert_run("run-abcd1234", "demo", cwd=tmp_path)
    db.update_run("run-abcd1234", "success", 4.2, cwd=tmp_path)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "run-abcd1234" in result.output
    assert "success" in result.output
