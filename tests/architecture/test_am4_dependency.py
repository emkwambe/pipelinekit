"""Tests for AM-4 blueprint dependency analysis (SPEC-026).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database and minimal
blueprint fixtures under ``tmp_path/blueprints`` reached via ``monkeypatch.chdir``
— the real ``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.architecture.dependency import (
    BlueprintDependency,
    add_dependency,
    get_dependencies,
    get_impact_report,
    remove_dependency,
    scan_dependencies,
)
from pipelinekit.core.errors import ArchitectureError


@pytest.fixture
def blueprint_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create minimal installed blueprints and chdir into their project root."""
    monkeypatch.chdir(tmp_path)
    for name in ("bp-a", "bp-b", "bp-c"):
        directory = tmp_path / "blueprints" / name
        directory.mkdir(parents=True)
        (directory / "blueprint.json").write_text(
            f'{{"name": "{name}"}}', encoding="utf-8"
        )
    return tmp_path


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def test_am4_scan_dependencies_returns_empty_for_unrelated_blueprints(
    blueprint_dirs: Path,
) -> None:
    """scan_dependencies returns [] when no relationships detected — valid."""
    detected = scan_dependencies("blueprints", _db(blueprint_dirs))

    assert detected == []


def test_am4_add_manual_dependency_creates_record(blueprint_dirs: Path) -> None:
    """add_dependency creates BlueprintDependency with correct fields."""
    db_path = _db(blueprint_dirs)

    dep = add_dependency("bp-a", "bp-b", "manual", "a feeds b", "blueprints", db_path)

    assert isinstance(dep, BlueprintDependency)
    assert dep.from_blueprint == "bp-a"
    assert dep.to_blueprint == "bp-b"
    assert dep.dependency_type == "manual"
    assert dep.reason == "a feeds b"
    assert dep.id
    assert dep.detected_at


def test_am4_add_dependency_raises_pk_am_001_for_missing_blueprint(
    blueprint_dirs: Path,
) -> None:
    """ArchitectureError PK-AM-001 raised when a blueprint directory is missing."""
    db_path = _db(blueprint_dirs)

    with pytest.raises(ArchitectureError) as exc_info:
        add_dependency("bp-a", "bp-missing", "manual", None, "blueprints", db_path)

    assert exc_info.value.code == "PK-AM-001"


def test_am4_add_dependency_raises_pk_am_002_for_invalid_type(
    blueprint_dirs: Path,
) -> None:
    """ArchitectureError PK-AM-002 raised for an unknown dependency type."""
    db_path = _db(blueprint_dirs)

    with pytest.raises(ArchitectureError) as exc_info:
        add_dependency("bp-a", "bp-b", "bogus", None, "blueprints", db_path)

    assert exc_info.value.code == "PK-AM-002"


def test_am4_get_dependencies_returns_all(blueprint_dirs: Path) -> None:
    """get_dependencies returns all stored dependencies."""
    db_path = _db(blueprint_dirs)
    add_dependency("bp-a", "bp-b", "manual", None, "blueprints", db_path)
    add_dependency("bp-b", "bp-c", "manual", None, "blueprints", db_path)

    deps = get_dependencies(db_path)

    assert len(deps) == 2
    assert {(d.from_blueprint, d.to_blueprint) for d in deps} == {
        ("bp-a", "bp-b"),
        ("bp-b", "bp-c"),
    }


def test_am4_remove_dependency_returns_true_when_found(blueprint_dirs: Path) -> None:
    """remove_dependency returns True when the dependency exists."""
    db_path = _db(blueprint_dirs)
    add_dependency("bp-a", "bp-b", "manual", None, "blueprints", db_path)

    removed = remove_dependency("bp-a", "bp-b", db_path)

    assert removed is True
    assert get_dependencies(db_path) == []


def test_am4_remove_dependency_returns_false_when_not_found(
    blueprint_dirs: Path,
) -> None:
    """remove_dependency returns False when the dependency does not exist."""
    db_path = _db(blueprint_dirs)

    assert remove_dependency("bp-a", "bp-b", db_path) is False


def test_am4_impact_report_lists_affected_blueprints(blueprint_dirs: Path) -> None:
    """get_impact_report identifies blueprints that depend on the target."""
    db_path = _db(blueprint_dirs)
    add_dependency("bp-a", "bp-b", "manual", "a feeds b", "blueprints", db_path)

    report = get_impact_report("bp-a", db_path)

    assert report.blueprint_name == "bp-a"
    assert report.total_affected == 1
    assert report.affected_blueprints[0].to_blueprint == "bp-b"


def test_am4_impact_report_empty_when_no_dependents(blueprint_dirs: Path) -> None:
    """get_impact_report returns an empty list when nothing depends on target."""
    db_path = _db(blueprint_dirs)

    report = get_impact_report("bp-c", db_path)

    assert report.total_affected == 0
    assert report.affected_blueprints == []
