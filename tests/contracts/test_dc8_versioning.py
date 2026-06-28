"""Tests for DC-8 schema versioning (SPEC-020).

Deterministic, no AI. Every test uses a ``tmp_path`` database — never the
production ``state.db``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.contracts.versioning import (
    diff_contract_versions,
    get_contract_history,
    get_contract_version,
    snapshot_contract,
)
from pipelinekit.core.errors import ContractError

_BLUEPRINT = "stripe-to-snowflake"
_CONTRACT = "payments.yaml"


def _db(tmp_path: Path) -> str:
    """Return a throwaway state.db path inside the test's tmp dir."""
    return str(tmp_path / "state.db")


def test_dc8_snapshot_creates_new_version_for_new_contract(tmp_path: Path) -> None:
    """First snapshot of a contract creates v1.0.0."""
    db_path = _db(tmp_path)
    content = {"required_columns": ["payment_id", "amount"]}

    version = snapshot_contract(_BLUEPRINT, _CONTRACT, content, db_path)

    assert version.version == "1.0.0"
    assert (version.version_major, version.version_minor, version.version_patch) == (
        1,
        0,
        0,
    )
    assert version.content_hash


def test_dc8_snapshot_is_idempotent_when_contract_unchanged(tmp_path: Path) -> None:
    """Snapshotting the same contract twice returns the same version."""
    db_path = _db(tmp_path)
    content = {"required_columns": ["payment_id"]}

    first = snapshot_contract(_BLUEPRINT, _CONTRACT, content, db_path)
    second = snapshot_contract(_BLUEPRINT, _CONTRACT, content, db_path)

    assert second.version == first.version == "1.0.0"
    assert second.id == first.id
    # No second row was written.
    assert len(get_contract_history(_BLUEPRINT, _CONTRACT, db_path)) == 1


def test_dc8_snapshot_bumps_patch_on_additive_change(tmp_path: Path) -> None:
    """Adding an optional column bumps PATCH version."""
    db_path = _db(tmp_path)
    snapshot_contract(
        _BLUEPRINT, _CONTRACT, {"required_columns": ["payment_id"]}, db_path
    )

    # 'status' is a new, non-required (optional) column.
    bumped = snapshot_contract(
        _BLUEPRINT,
        _CONTRACT,
        {
            "required_columns": ["payment_id"],
            "accepted_values": {"status": ["paid", "pending"]},
        },
        db_path,
    )

    assert bumped.version == "1.0.1"


def test_dc8_snapshot_bumps_major_on_column_removal(tmp_path: Path) -> None:
    """Removing a column bumps MAJOR version."""
    db_path = _db(tmp_path)
    snapshot_contract(
        _BLUEPRINT,
        _CONTRACT,
        {"required_columns": ["payment_id", "customer_id"]},
        db_path,
    )

    bumped = snapshot_contract(
        _BLUEPRINT, _CONTRACT, {"required_columns": ["payment_id"]}, db_path
    )

    assert bumped.version == "2.0.0"


def test_dc8_get_version_returns_none_when_no_history(tmp_path: Path) -> None:
    """get_contract_version returns None when no snapshot exists."""
    db_path = _db(tmp_path)

    assert get_contract_version(_BLUEPRINT, _CONTRACT, db_path) is None


def test_dc8_get_history_returns_versions_newest_first(tmp_path: Path) -> None:
    """Version history is ordered newest first."""
    db_path = _db(tmp_path)
    snapshot_contract(
        _BLUEPRINT,
        _CONTRACT,
        {"required_columns": ["payment_id", "customer_id"]},
        db_path,
    )
    snapshot_contract(
        _BLUEPRINT, _CONTRACT, {"required_columns": ["payment_id"]}, db_path
    )

    history = get_contract_history(_BLUEPRINT, _CONTRACT, db_path)

    assert [v.version for v in history] == ["2.0.0", "1.0.0"]


def test_dc8_diff_shows_added_and_removed_fields(tmp_path: Path) -> None:
    """diff_contract_versions correctly identifies changes."""
    db_path = _db(tmp_path)
    snapshot_contract(
        _BLUEPRINT,
        _CONTRACT,
        {"required_columns": ["payment_id", "old_col"]},
        db_path,
    )
    snapshot_contract(
        _BLUEPRINT,
        _CONTRACT,
        {"required_columns": ["payment_id", "new_col"]},
        db_path,
    )

    diff = diff_contract_versions(_BLUEPRINT, _CONTRACT, "1.0.0", "2.0.0", db_path)

    assert "new_col" in diff.added_fields
    assert "old_col" in diff.removed_fields
    assert diff.change_type == "major"


def test_dc8_raises_pk_dc_008_when_version_not_found(tmp_path: Path) -> None:
    """PK-DC-008 is raised when --diff references a non-existent version."""
    db_path = _db(tmp_path)
    snapshot_contract(
        _BLUEPRINT, _CONTRACT, {"required_columns": ["payment_id"]}, db_path
    )

    with pytest.raises(ContractError) as exc_info:
        diff_contract_versions(_BLUEPRINT, _CONTRACT, "1.0.0", "9.9.9", db_path)

    assert exc_info.value.code == "PK-DC-008"
