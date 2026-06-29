"""Tests for GM-1 ownership assignment (SPEC-023).

Deterministic, no AI. Every test uses a ``tmp_path`` database, and a minimal
blueprint directory under ``tmp_path/blueprints/`` (with ``monkeypatch.chdir``)
where blueprint-existence is checked — the real ``blueprints/`` is never used.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipelinekit.core.errors import GovernanceError
from pipelinekit.governance.ownership import (
    get_ownership_report,
    get_owner,
    remove_owner,
    set_owner,
    validate_email,
)

_EMAIL = "eddy@mpingo.ai"


def _db(tmp_path: Path) -> str:
    """Return a throwaway state.db path inside the test's tmp dir."""
    return str(tmp_path / "state.db")


def _install(tmp_path: Path, name: str = "test-blueprint") -> None:
    """Create a minimal installed blueprint under tmp_path/blueprints/<name>."""
    bp = tmp_path / "blueprints" / name
    bp.mkdir(parents=True, exist_ok=True)
    (bp / "blueprint.json").write_text(f'{{"name": "{name}"}}', encoding="utf-8")


def test_gm1_set_owner_creates_new_owner(tmp_path: Path, monkeypatch) -> None:
    """set_owner creates a BlueprintOwner with correct fields."""
    monkeypatch.chdir(tmp_path)
    _install(tmp_path)

    owner = set_owner(
        "test-blueprint", "Eddy Mkwambe", _EMAIL, "Data Engineering", "n", _db(tmp_path)
    )

    assert owner.blueprint_name == "test-blueprint"
    assert owner.owner_name == "Eddy Mkwambe"
    assert owner.owner_email == _EMAIL
    assert owner.team_name == "Data Engineering"
    assert owner.id
    assert owner.created_at == owner.updated_at


def test_gm1_set_owner_updates_existing_owner(tmp_path: Path, monkeypatch) -> None:
    """set_owner overwrites previous owner for same blueprint."""
    monkeypatch.chdir(tmp_path)
    _install(tmp_path)
    db_path = _db(tmp_path)

    first = set_owner("test-blueprint", "Eddy", _EMAIL, None, None, db_path)
    second = set_owner(
        "test-blueprint", "New Owner", "new@mpingo.ai", "Platform", None, db_path
    )

    assert second.owner_name == "New Owner"
    assert second.owner_email == "new@mpingo.ai"
    assert second.id == first.id  # same row, preserved id
    assert second.created_at == first.created_at  # creation time preserved
    # Only one owner row remains for the blueprint.
    report = get_ownership_report(str(tmp_path / "blueprints"), db_path)
    assert report.owned_count == 1


def test_gm1_set_owner_raises_pk_gm_001_for_unknown_blueprint(
    tmp_path: Path, monkeypatch
) -> None:
    """PK-GM-001 raised when blueprint is not installed."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "blueprints").mkdir()  # blueprints dir exists, but no such blueprint

    with pytest.raises(GovernanceError) as exc_info:
        set_owner("ghost-blueprint", "Eddy", _EMAIL, None, None, _db(tmp_path))

    assert exc_info.value.code == "PK-GM-001"


def test_gm1_get_owner_returns_none_when_not_set(tmp_path: Path) -> None:
    """get_owner returns None when no owner assigned."""
    assert get_owner("test-blueprint", _db(tmp_path)) is None


def test_gm1_get_owner_returns_correct_fields(tmp_path: Path, monkeypatch) -> None:
    """get_owner returns BlueprintOwner with correct name/email/team."""
    monkeypatch.chdir(tmp_path)
    _install(tmp_path)
    db_path = _db(tmp_path)
    set_owner(
        "test-blueprint", "Eddy Mkwambe", _EMAIL, "Data Engineering", None, db_path
    )

    owner = get_owner("test-blueprint", db_path)

    assert owner is not None
    assert owner.owner_name == "Eddy Mkwambe"
    assert owner.owner_email == _EMAIL
    assert owner.team_name == "Data Engineering"


def test_gm1_remove_owner_returns_true_when_found(tmp_path: Path, monkeypatch) -> None:
    """remove_owner returns True when owner exists."""
    monkeypatch.chdir(tmp_path)
    _install(tmp_path)
    db_path = _db(tmp_path)
    set_owner("test-blueprint", "Eddy", _EMAIL, None, None, db_path)

    assert remove_owner("test-blueprint", db_path) is True
    assert get_owner("test-blueprint", db_path) is None


def test_gm1_remove_owner_returns_false_when_not_found(
    tmp_path: Path, monkeypatch
) -> None:
    """remove_owner returns False when no owner set."""
    monkeypatch.chdir(tmp_path)
    _install(tmp_path)

    assert remove_owner("test-blueprint", _db(tmp_path)) is False


def test_gm1_ownership_report_identifies_unowned_blueprints(
    tmp_path: Path, monkeypatch
) -> None:
    """get_ownership_report lists blueprints with no owner."""
    monkeypatch.chdir(tmp_path)
    _install(tmp_path, "bp_a")
    _install(tmp_path, "bp_b")
    db_path = _db(tmp_path)
    set_owner("bp_a", "Eddy", _EMAIL, None, None, db_path)

    report = get_ownership_report(str(tmp_path / "blueprints"), db_path)

    assert report.total_blueprints == 2
    assert report.owned_count == 1
    assert report.unowned_blueprints == ["bp_b"]
    assert report.coverage_pct == 50.0


def test_gm1_validate_email_raises_pk_gm_002_for_invalid_email() -> None:
    """PK-GM-002 raised for email without @ or domain."""
    with pytest.raises(GovernanceError) as exc_info:
        validate_email("not-an-email")
    assert exc_info.value.code == "PK-GM-002"

    # No dot in the domain is also invalid.
    with pytest.raises(GovernanceError) as exc_info2:
        validate_email("eddy@localhost")
    assert exc_info2.value.code == "PK-GM-002"
