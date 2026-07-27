"""Tests for AM-5 architecture drift detection (SPEC-037).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database and minimal
blueprint fixtures under ``tmp_path/blueprints`` — the real ``blueprints/``
directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pipelinekit.architecture.dependency import (
    add_dependency,
    scan_dependencies,
)
from pipelinekit.architecture.drift import (
    check_dependency_still_holds,
    detect_architecture_drift,
)


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def _make_blueprint(tmp_path: Path, name: str) -> Path:
    """Create a bare installed blueprint directory and return its path."""
    directory = tmp_path / "blueprints" / name
    directory.mkdir(parents=True)
    (directory / "blueprint.json").write_text(f'{{"name": "{name}"}}', encoding="utf-8")
    return directory


def _make_contract(blueprint_dir: Path, table: str) -> None:
    """Give a blueprint a contract that declares it produces ``table``."""
    contracts = blueprint_dir / "contracts"
    contracts.mkdir(parents=True, exist_ok=True)
    (contracts / f"{table}.yaml").write_text(f"table: {table}\n", encoding="utf-8")


def _make_ingestion(blueprint_dir: Path, name: str, tables: list[str]) -> None:
    """Rewrite a blueprint.json so its ingestion declares ``tables``."""
    table_list = ", ".join(f'"{t}"' for t in tables)
    (blueprint_dir / "blueprint.json").write_text(
        f'{{"name": "{name}", "tables": [{table_list}]}}', encoding="utf-8"
    )


def _linked_pair(tmp_path: Path) -> str:
    """Create bp-a (produces ``charges``) → bp-b (ingests ``charges``).

    Returns the state db path with the auto-detected contract dependency stored.
    """
    a = _make_blueprint(tmp_path, "bp-a")
    b = _make_blueprint(tmp_path, "bp-b")
    _make_contract(a, "charges")
    _make_ingestion(b, "bp-b", ["charges"])
    db_path = _db(tmp_path)
    scan_dependencies(str(tmp_path / "blueprints"), db_path)
    return db_path


def test_am5_manual_dependency_always_clean(tmp_path: Path) -> None:
    """A manual dependency is always considered valid (human declared)."""
    _make_blueprint(tmp_path, "bp-a")
    _make_blueprint(tmp_path, "bp-b")
    db_path = _db(tmp_path)
    bp_dir = str(tmp_path / "blueprints")
    add_dependency("bp-a", "bp-b", "manual", "a feeds b", bp_dir, db_path)

    report = detect_architecture_drift(str(tmp_path / "blueprints"), db_path)

    assert report.drifted_dependencies == []
    assert report.clean_dependencies == 1


def test_am5_missing_blueprint_detected_as_blueprint_missing(tmp_path: Path) -> None:
    """A non-manual edge whose endpoint is uninstalled is BLUEPRINT_MISSING."""
    db_path = _linked_pair(tmp_path)
    shutil.rmtree(tmp_path / "blueprints" / "bp-b")  # downstream uninstalled

    report = detect_architecture_drift(str(tmp_path / "blueprints"), db_path)

    assert len(report.drifted_dependencies) == 1
    assert report.drifted_dependencies[0].drift_type == "BLUEPRINT_MISSING"


def test_am5_dependency_broken_when_table_no_longer_referenced(
    tmp_path: Path,
) -> None:
    """Both blueprints present but the link is gone → DEPENDENCY_BROKEN."""
    db_path = _linked_pair(tmp_path)
    # Downstream no longer ingests the produced table.
    _make_ingestion(tmp_path / "blueprints" / "bp-b", "bp-b", [])

    report = detect_architecture_drift(str(tmp_path / "blueprints"), db_path)

    assert len(report.drifted_dependencies) == 1
    assert report.drifted_dependencies[0].drift_type == "DEPENDENCY_BROKEN"


def test_am5_drift_report_counts_clean_correctly(tmp_path: Path) -> None:
    """A still-valid contract dependency is counted as clean, not drifted."""
    db_path = _linked_pair(tmp_path)

    report = detect_architecture_drift(str(tmp_path / "blueprints"), db_path)

    assert report.drifted_dependencies == []
    assert report.clean_dependencies == 1
    assert report.total_dependencies == 1


def test_am5_drift_report_generated_at_is_set(tmp_path: Path) -> None:
    """The report carries a timezone-aware ISO timestamp."""
    db_path = _linked_pair(tmp_path)

    report = detect_architecture_drift(str(tmp_path / "blueprints"), db_path)

    assert report.generated_at
    assert "T" in report.generated_at and "+" in report.generated_at


def test_am5_detect_drift_empty_when_no_dependencies(tmp_path: Path) -> None:
    """With no documented dependencies the report is empty and clean."""
    _make_blueprint(tmp_path, "bp-a")
    db_path = _db(tmp_path)

    report = detect_architecture_drift(str(tmp_path / "blueprints"), db_path)

    assert report.total_dependencies == 0
    assert report.drifted_dependencies == []
    assert report.clean_dependencies == 0


def test_am5_check_dependency_holds_returns_true_for_valid(tmp_path: Path) -> None:
    """check_dependency_still_holds is True for an intact contract edge."""
    db_path = _linked_pair(tmp_path)
    from pipelinekit.architecture.dependency import get_dependencies

    dep = get_dependencies(db_path)[0]

    assert check_dependency_still_holds(dep, str(tmp_path / "blueprints")) is True


def test_am5_check_dependency_holds_returns_false_for_missing_dir(
    tmp_path: Path,
) -> None:
    """check_dependency_still_holds is False when a blueprint dir is missing."""
    db_path = _linked_pair(tmp_path)
    from pipelinekit.architecture.dependency import get_dependencies

    dep = get_dependencies(db_path)[0]
    shutil.rmtree(tmp_path / "blueprints" / "bp-a")

    assert check_dependency_still_holds(dep, str(tmp_path / "blueprints")) is False


def test_am5_drift_command_exits_1_when_drift_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI drift command exits 1 when any drift is detected."""
    import pipelinekit.cli.architect as architect_cli
    from typer.testing import CliRunner

    db_path = _linked_pair(tmp_path)
    shutil.rmtree(tmp_path / "blueprints" / "bp-b")

    # Point the CLI resolvers at this test's isolated fixtures. monkeypatch.setattr
    # (not direct assignment) so these module globals are restored after the test
    # and never leak into later tests in the session.
    monkeypatch.setattr(architect_cli, "_db_path", lambda: db_path)
    monkeypatch.setattr(
        architect_cli, "_blueprints_dir", lambda: str(tmp_path / "blueprints")
    )

    result = CliRunner().invoke(architect_cli.architect_app, ["drift"])

    assert result.exit_code == 1
    assert "BLUEPRINT_MISSING" in result.stdout
