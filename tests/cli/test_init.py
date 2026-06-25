"""Tests for ``pipelinekit init`` (SPEC-001, SPEC-007)."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_init_creates_config(tmp_path, monkeypatch):
    """init creates pipelinekit.yaml when not present."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / "pipelinekit.yaml").is_file()


def test_init_does_not_overwrite(tmp_path, monkeypatch):
    """init does not overwrite an existing pipelinekit.yaml."""
    monkeypatch.chdir(tmp_path)
    sentinel = "pipeline:\n  name: do-not-touch\n"
    (tmp_path / "pipelinekit.yaml").write_text(sentinel, encoding="utf-8")
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / "pipelinekit.yaml").read_text(encoding="utf-8") == sentinel


def test_init_exits_zero(tmp_path, monkeypatch):
    """init exits 0 on success."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0


def test_init_exits_zero_when_exists(tmp_path, monkeypatch):
    """init exits 0 even when the file already exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pipelinekit.yaml").write_text("pipeline:\n", encoding="utf-8")
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "already exists" in result.output


def test_init_creates_gitignore_entry(tmp_path, monkeypatch):
    """init adds .pipelinekit/ to .gitignore."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".pipelinekit/" in gitignore


def test_init_does_not_duplicate_gitignore_entry(tmp_path, monkeypatch):
    """init does not append .pipelinekit/ twice when already present."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text(".pipelinekit/\n", encoding="utf-8")
    runner.invoke(app, ["init"])
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert gitignore.count(".pipelinekit/") == 1
