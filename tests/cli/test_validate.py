"""Tests for ``pipelinekit validate`` (SPEC-001, SPEC-002)."""

from __future__ import annotations

from pipelinekit.cli.main import app
from pipelinekit.config.loader import write_default_config
from typer.testing import CliRunner

runner = CliRunner()


def test_validate_exits_zero_on_valid_config(tmp_path, monkeypatch):
    """validate exits 0 on a valid pipelinekit.yaml."""
    monkeypatch.chdir(tmp_path)
    write_default_config(tmp_path)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "valid" in result.output


def test_validate_exits_one_on_missing_file(tmp_path, monkeypatch):
    """validate exits 1 when pipelinekit.yaml is not found."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    assert "PK-CONFIG-003" in result.output


def test_validate_exits_one_on_invalid_yaml(tmp_path, monkeypatch):
    """validate exits 1 on malformed YAML."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pipelinekit.yaml").write_text(
        "pipeline: [unclosed\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1
    assert "PK-CONFIG-004" in result.output


def test_validate_exits_one_on_missing_section(tmp_path, monkeypatch):
    """validate exits 1 when a required section is absent."""
    monkeypatch.chdir(tmp_path)
    # Valid YAML, but missing every section except pipeline.
    (tmp_path / "pipelinekit.yaml").write_text(
        "pipeline:\n  name: demo\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 1


def test_validate_prints_error_code(tmp_path, monkeypatch):
    """validate prints a PK error code on schema failure."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pipelinekit.yaml").write_text(
        "pipeline:\n  name: demo\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["validate"])
    assert "PK-CONFIG-001" in result.output
