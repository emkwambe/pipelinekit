"""Tests for DC-11 contract lifecycle management (SPEC-036).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database — the real
``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.contracts.lifecycle import (
    ContractLifecycleState,
    get_all_lifecycle_states,
    get_lifecycle_state,
    set_lifecycle_state,
)
from pipelinekit.core.errors import ContractError


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def test_dc11_set_lifecycle_state_creates_record(tmp_path: Path) -> None:
    """set_lifecycle_state creates a ContractLifecycleState record."""
    db_path = _db(tmp_path)

    result = set_lifecycle_state(
        "test-bp", "charges.yaml", "ACTIVE", "jane", "go live", db_path
    )

    assert isinstance(result, ContractLifecycleState)
    assert result.blueprint_name == "test-bp"
    assert result.contract_file == "charges.yaml"
    assert result.state == "ACTIVE"
    assert result.changed_by == "jane"
    assert result.change_reason == "go live"
    assert result.id
    assert result.created_at
    assert result.updated_at


def test_dc11_valid_transition_draft_to_active(tmp_path: Path) -> None:
    """An implicit-DRAFT contract can transition to ACTIVE."""
    db_path = _db(tmp_path)

    result = set_lifecycle_state(
        "test-bp", "charges.yaml", "ACTIVE", None, None, db_path
    )

    assert result.state == "ACTIVE"


def test_dc11_valid_transition_active_to_deprecated(tmp_path: Path) -> None:
    """ACTIVE can transition to DEPRECATED."""
    db_path = _db(tmp_path)
    set_lifecycle_state("test-bp", "charges.yaml", "ACTIVE", None, None, db_path)

    result = set_lifecycle_state(
        "test-bp", "charges.yaml", "DEPRECATED", None, None, db_path
    )

    assert result.state == "DEPRECATED"


def test_dc11_valid_transition_deprecated_to_retired(tmp_path: Path) -> None:
    """DEPRECATED can transition to RETIRED."""
    db_path = _db(tmp_path)
    set_lifecycle_state("test-bp", "charges.yaml", "ACTIVE", None, None, db_path)
    set_lifecycle_state("test-bp", "charges.yaml", "DEPRECATED", None, None, db_path)

    result = set_lifecycle_state(
        "test-bp", "charges.yaml", "RETIRED", None, None, db_path
    )

    assert result.state == "RETIRED"


def test_dc11_invalid_transition_raises_pk_dc_013(tmp_path: Path) -> None:
    """An invalid transition (DRAFT→DEPRECATED) raises ContractError PK-DC-013."""
    db_path = _db(tmp_path)

    with pytest.raises(ContractError) as exc_info:
        set_lifecycle_state(
            "test-bp", "charges.yaml", "DEPRECATED", None, None, db_path
        )

    assert exc_info.value.code == "PK-DC-013"


def test_dc11_get_lifecycle_returns_none_when_not_set(tmp_path: Path) -> None:
    """get_lifecycle_state returns None when no state has been set."""
    db_path = _db(tmp_path)

    assert get_lifecycle_state("test-bp", "charges.yaml", db_path) is None


def test_dc11_get_all_lifecycle_states_returns_all(tmp_path: Path) -> None:
    """get_all_lifecycle_states returns every recorded state."""
    db_path = _db(tmp_path)
    set_lifecycle_state("test-bp", "charges.yaml", "ACTIVE", None, None, db_path)
    set_lifecycle_state("test-bp", "customers.yaml", "ACTIVE", None, None, db_path)

    states = get_all_lifecycle_states(db_path)

    assert len(states) == 2
    assert {s.contract_file for s in states} == {"charges.yaml", "customers.yaml"}


def test_dc11_cannot_go_backwards_from_deprecated_to_active(tmp_path: Path) -> None:
    """A DEPRECATED contract cannot go back to ACTIVE (PK-DC-013)."""
    db_path = _db(tmp_path)
    set_lifecycle_state("test-bp", "charges.yaml", "ACTIVE", None, None, db_path)
    set_lifecycle_state("test-bp", "charges.yaml", "DEPRECATED", None, None, db_path)

    with pytest.raises(ContractError) as exc_info:
        set_lifecycle_state("test-bp", "charges.yaml", "ACTIVE", None, None, db_path)

    assert exc_info.value.code == "PK-DC-013"


def test_dc11_draft_to_retired_is_valid_emergency_transition(tmp_path: Path) -> None:
    """DRAFT can go straight to RETIRED (emergency/abandon transition)."""
    db_path = _db(tmp_path)

    result = set_lifecycle_state(
        "test-bp", "charges.yaml", "RETIRED", None, "abandoned", db_path
    )

    assert result.state == "RETIRED"
