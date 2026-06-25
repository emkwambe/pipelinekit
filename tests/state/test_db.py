"""Tests for the SQLite state store (SPEC-007)."""

from __future__ import annotations

import pytest
from pipelinekit.core.errors import StateError
from pipelinekit.state import db


def test_initialize_creates_db(tmp_path):
    """initialize creates .pipelinekit/state.db."""
    db.initialize(cwd=tmp_path)
    assert (tmp_path / ".pipelinekit" / "state.db").is_file()


def test_initialize_idempotent(tmp_path):
    """initialize called twice does not raise or corrupt the db."""
    db.initialize(cwd=tmp_path)
    db.initialize(cwd=tmp_path)
    assert db.get_recent_runs(cwd=tmp_path) == []


def test_get_recent_runs_empty(tmp_path):
    """get_recent_runs returns [] on a fresh database."""
    assert db.get_recent_runs(cwd=tmp_path) == []


def test_insert_and_retrieve_run(tmp_path):
    """insert_run followed by get_recent_runs returns the run."""
    db.insert_run("run-12345678", "demo", cwd=tmp_path)
    runs = db.get_recent_runs(cwd=tmp_path)
    assert len(runs) == 1
    assert runs[0]["id"] == "run-12345678"
    assert runs[0]["pipeline"] == "demo"
    assert runs[0]["status"] == "pending"


def test_update_run_records_status(tmp_path):
    """update_run sets the final status and duration on a run."""
    db.insert_run("run-12345678", "demo", cwd=tmp_path)
    db.update_run("run-12345678", "success", 4.2, cwd=tmp_path)
    runs = db.get_recent_runs(cwd=tmp_path)
    assert runs[0]["status"] == "success"
    assert runs[0]["duration_s"] == 4.2


def test_state_error_on_bad_path(tmp_path):
    """initialize raises StateError(PK-STATE-001) on an unwritable path."""
    not_a_dir = tmp_path / "afile"
    not_a_dir.write_text("i am a file", encoding="utf-8")
    with pytest.raises(StateError) as exc_info:
        db.initialize(cwd=not_a_dir)
    assert exc_info.value.code == "PK-STATE-001"


def test_insert_duplicate_run_raises(tmp_path):
    """A duplicate run id is a write error surfaced as PK-STATE-002."""
    db.insert_run("run-dup12345", "demo", cwd=tmp_path)
    with pytest.raises(StateError) as exc_info:
        db.insert_run("run-dup12345", "demo", cwd=tmp_path)
    assert exc_info.value.code == "PK-STATE-002"


def test_ensure_gitignore_error_on_bad_path(tmp_path):
    """ensure_gitignore_entry raises PK-STATE-002 when it cannot write."""
    not_a_dir = tmp_path / "afile"
    not_a_dir.write_text("i am a file", encoding="utf-8")
    with pytest.raises(StateError) as exc_info:
        db.ensure_gitignore_entry(cwd=not_a_dir)
    assert exc_info.value.code == "PK-STATE-002"


def test_ensure_gitignore_creates_file(tmp_path):
    """ensure_gitignore_entry creates .gitignore with the state entry."""
    db.ensure_gitignore_entry(cwd=tmp_path)
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".pipelinekit/" in content


def test_ensure_gitignore_appends_without_duplicate(tmp_path):
    """ensure_gitignore_entry appends once and never duplicates."""
    (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    db.ensure_gitignore_entry(cwd=tmp_path)
    db.ensure_gitignore_entry(cwd=tmp_path)
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert content.count(".pipelinekit/") == 1
    assert "__pycache__/" in content
