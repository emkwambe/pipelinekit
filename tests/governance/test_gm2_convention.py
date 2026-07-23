"""Tests for GM-2 naming convention enforcement (SPEC-028).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database and minimal
blueprint fixtures reached via ``monkeypatch.chdir`` — the real ``blueprints/``
directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.core.errors import GovernanceError
from pipelinekit.governance.convention import (
    NamingConvention,
    add_convention,
    check_blueprint_conventions,
    extract_names_for_scope,
    get_conventions,
    remove_convention,
)

_SCHEMA_YML = """\
version: 2
models:
  - name: stg_orders
    columns:
      - name: order_id
        tests: [unique, not_null]
      - name: customer_id
"""


@pytest.fixture
def blueprint_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a minimal installed blueprint and chdir into its project root."""
    monkeypatch.chdir(tmp_path)
    bp = tmp_path / "blueprints" / "test-bp"
    bp.mkdir(parents=True)
    (bp / "blueprint.json").write_text('{"name": "test-bp"}', encoding="utf-8")

    models = bp / "transform" / "models" / "staging"
    models.mkdir(parents=True)
    (models / "schema.yml").write_text(_SCHEMA_YML, encoding="utf-8")

    contracts = bp / "contracts"
    contracts.mkdir(parents=True)
    (contracts / "orders.yaml").write_text("table: orders", encoding="utf-8")

    return tmp_path


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def test_gm2_add_convention_creates_record(tmp_path: Path) -> None:
    """add_convention creates NamingConvention with correct fields."""
    db_path = _db(tmp_path)

    convention = add_convention("table", "^stg_[a-z_]+", "table prefix", db_path)

    assert isinstance(convention, NamingConvention)
    assert convention.scope == "table"
    assert convention.pattern == "^stg_[a-z_]+"
    assert convention.description == "table prefix"
    assert convention.id
    assert convention.created_at


def test_gm2_add_convention_raises_pk_gm_003_for_invalid_scope(tmp_path: Path) -> None:
    """GovernanceError with PK-GM-003 raised for an unknown scope."""
    db_path = _db(tmp_path)

    with pytest.raises(GovernanceError) as exc_info:
        add_convention("bogus", "^stg_", None, db_path)

    assert exc_info.value.code == "PK-GM-003"


def test_gm2_add_convention_raises_pk_gm_004_for_invalid_regex(tmp_path: Path) -> None:
    """GovernanceError with PK-GM-004 raised for an invalid regex pattern."""
    db_path = _db(tmp_path)

    with pytest.raises(GovernanceError) as exc_info:
        add_convention("table", "[unclosed(", None, db_path)

    assert exc_info.value.code == "PK-GM-004"


def test_gm2_get_conventions_returns_all(tmp_path: Path) -> None:
    """get_conventions returns all stored conventions."""
    db_path = _db(tmp_path)
    add_convention("table", "^stg_[a-z_]+", None, db_path)
    add_convention("column", "^[a-z_]+$", None, db_path)

    conventions = get_conventions(db_path)

    assert len(conventions) == 2
    assert {c.scope for c in conventions} == {"table", "column"}


def test_gm2_remove_convention_returns_true_when_found(tmp_path: Path) -> None:
    """remove_convention returns True when the convention exists."""
    db_path = _db(tmp_path)
    convention = add_convention("table", "^stg_[a-z_]+", None, db_path)

    removed = remove_convention(convention.id, db_path)

    assert removed is True
    assert get_conventions(db_path) == []
    # Removing an unknown id returns False.
    assert remove_convention("does-not-exist", db_path) is False


def test_gm2_check_finds_no_violations_for_compliant_names(blueprint_dir: Path) -> None:
    """check_blueprint_conventions returns is_compliant=True when all pass."""
    db_path = _db(blueprint_dir)
    add_convention("table", "^(stg|fct|dim)_[a-z_]+", None, db_path)

    result = check_blueprint_conventions("test-bp", "blueprints", db_path)

    assert result.is_compliant is True
    assert result.violation_count == 0
    assert result.checked_count == 1  # one model: stg_orders


def test_gm2_check_finds_violation_for_noncompliant_name(blueprint_dir: Path) -> None:
    """check_blueprint_conventions returns a violation for a non-matching name."""
    db_path = _db(blueprint_dir)
    add_convention("table", "^fct_[a-z_]+", None, db_path)

    result = check_blueprint_conventions("test-bp", "blueprints", db_path)

    assert result.is_compliant is False
    assert result.violation_count == 1
    assert result.violations[0].name == "stg_orders"
    assert result.violations[0].scope == "table"


def test_gm2_check_blueprint_scope_validates_blueprint_name(
    blueprint_dir: Path,
) -> None:
    """blueprint scope validates the blueprint name itself."""
    db_path = _db(blueprint_dir)
    # The blueprint name "test-bp" does not match a required prod_ prefix.
    add_convention("blueprint", "^prod_[a-z]+", None, db_path)

    result = check_blueprint_conventions("test-bp", "blueprints", db_path)

    assert result.is_compliant is False
    assert result.violations[0].name == "test-bp"
    assert result.violations[0].scope == "blueprint"


def test_gm2_extract_names_returns_table_names_from_schema_yml(
    blueprint_dir: Path,
) -> None:
    """extract_names_for_scope returns model names for the table scope."""
    names = extract_names_for_scope("test-bp", "table", "blueprints")

    assert names == ["stg_orders"]
