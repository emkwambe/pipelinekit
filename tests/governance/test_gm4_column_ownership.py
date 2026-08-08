"""Tests for GM-4 column-level domain ownership (SPEC-032).

Deterministic, no AI. Every test builds its own blueprint tree and contract YAML
under ``tmp_path`` and uses a ``tmp_path`` database — the real ``blueprints/`` is
never read. Follows the GM-1 pattern in ``test_gm1_ownership.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.cli.main import app
from pipelinekit.core.errors import GovernanceError
from pipelinekit.governance.column_ownership import (
    get_all_column_owners,
    get_column_owner,
    get_column_ownership_report,
    remove_column_owner,
    set_column_owner,
)
from typer.testing import CliRunner

runner = CliRunner()

_CONTRACT = """version: 1
table: charges
required_columns:
  - charge_id
  - amount
  - currency
  - status
uniqueness:
  - charge_id
"""

_COLUMNS = ["amount", "charge_id", "currency", "status"]


def _db(tmp_path: Path) -> str:
    """Return a throwaway state.db path inside the test's tmp dir."""
    return str(tmp_path / "state.db")


def _install(tmp_path: Path, name: str = "test-blueprint") -> str:
    """Create a blueprint with one contract; return the blueprints dir path."""
    contracts = tmp_path / "blueprints" / name / "contracts"
    contracts.mkdir(parents=True, exist_ok=True)
    (tmp_path / "blueprints" / name / "blueprint.json").write_text(
        f'{{"name": "{name}"}}', encoding="utf-8"
    )
    (contracts / "charges.yaml").write_text(_CONTRACT, encoding="utf-8")
    return str(tmp_path / "blueprints")


def test_gm4_set_column_owner_creates_record(tmp_path: Path) -> None:
    """set_column_owner creates a ColumnOwner with the correct fields."""
    _install(tmp_path)

    owner = set_column_owner(
        "test-blueprint",
        "charges.yaml",
        "amount",
        "finance",
        "finance@company.com",
        "Charge amount in minor units",
        _db(tmp_path),
    )

    assert owner.blueprint_name == "test-blueprint"
    assert owner.contract_file == "charges.yaml"
    assert owner.column_name == "amount"
    assert owner.owner_domain == "finance"
    assert owner.owner_email == "finance@company.com"
    assert owner.id
    assert owner.created_at == owner.updated_at


def test_gm4_set_column_owner_updates_existing(tmp_path: Path) -> None:
    """Re-setting a column replaces the row, preserving id and created_at."""
    _install(tmp_path)
    db_path = _db(tmp_path)

    first = set_column_owner(
        "test-blueprint", "charges.yaml", "amount", "finance", None, None, db_path
    )
    second = set_column_owner(
        "test-blueprint",
        "charges.yaml",
        "amount",
        "engineering",
        "eng@company.com",
        None,
        db_path,
    )

    assert second.owner_domain == "engineering"
    assert second.id == first.id  # same row, preserved id
    assert second.created_at == first.created_at  # creation time preserved
    assert len(get_all_column_owners(db_path)) == 1


def test_gm4_get_column_owner_returns_owner(tmp_path: Path) -> None:
    """get_column_owner returns the stored domain and email."""
    _install(tmp_path)
    db_path = _db(tmp_path)
    set_column_owner(
        "test-blueprint",
        "charges.yaml",
        "currency",
        "finance",
        "finance@company.com",
        None,
        db_path,
    )

    owner = get_column_owner("test-blueprint", "charges.yaml", "currency", db_path)

    assert owner is not None
    assert owner.owner_domain == "finance"
    assert owner.owner_email == "finance@company.com"


def test_gm4_get_column_owner_returns_none_when_not_set(tmp_path: Path) -> None:
    """get_column_owner returns None when the column has no owner."""
    assert (
        get_column_owner("test-blueprint", "charges.yaml", "amount", _db(tmp_path))
        is None
    )


def test_gm4_get_all_column_owners_returns_all(tmp_path: Path) -> None:
    """get_all_column_owners returns every declared column across blueprints."""
    _install(tmp_path, "bp_a")
    _install(tmp_path, "bp_b")
    db_path = _db(tmp_path)
    set_column_owner("bp_a", "charges.yaml", "amount", "finance", None, None, db_path)
    set_column_owner(
        "bp_b", "charges.yaml", "charge_id", "engineering", None, None, db_path
    )

    owners = get_all_column_owners(db_path)

    assert len(owners) == 2
    assert {o.blueprint_name for o in owners} == {"bp_a", "bp_b"}


def test_gm4_remove_column_owner_returns_true(tmp_path: Path) -> None:
    """remove_column_owner returns True when an owner existed, False after."""
    _install(tmp_path)
    db_path = _db(tmp_path)
    set_column_owner(
        "test-blueprint", "charges.yaml", "amount", "finance", None, None, db_path
    )

    assert remove_column_owner("test-blueprint", "charges.yaml", "amount", db_path)
    assert get_column_owner("test-blueprint", "charges.yaml", "amount", db_path) is None
    assert not remove_column_owner("test-blueprint", "charges.yaml", "amount", db_path)


def test_gm4_ownership_report_counts_correctly(tmp_path: Path) -> None:
    """The report counts declared columns against the contract's column set."""
    blueprints_dir = _install(tmp_path)
    db_path = _db(tmp_path)
    set_column_owner(
        "test-blueprint", "charges.yaml", "amount", "finance", None, None, db_path
    )
    set_column_owner(
        "test-blueprint",
        "charges.yaml",
        "charge_id",
        "engineering",
        None,
        None,
        db_path,
    )

    report = get_column_ownership_report(
        "test-blueprint", "charges.yaml", blueprints_dir, db_path
    )

    assert report.total_columns == len(_COLUMNS)
    assert report.owned_columns == 2
    assert report.coverage_pct == 50.0


def test_gm4_ownership_report_lists_unowned_columns(tmp_path: Path) -> None:
    """Unowned columns are listed; a stale owner never inflates coverage."""
    blueprints_dir = _install(tmp_path)
    db_path = _db(tmp_path)
    set_column_owner(
        "test-blueprint", "charges.yaml", "amount", "finance", None, None, db_path
    )
    # A column the contract no longer declares must not count toward coverage.
    set_column_owner(
        "test-blueprint", "charges.yaml", "dropped_col", "finance", None, None, db_path
    )

    report = get_column_ownership_report(
        "test-blueprint", "charges.yaml", blueprints_dir, db_path
    )

    assert report.unowned_columns == ["charge_id", "currency", "status"]
    assert report.owned_columns == 1
    assert report.total_columns == len(_COLUMNS)


def test_gm4_ownership_report_raises_pk_gm_007_for_missing_contract(
    tmp_path: Path,
) -> None:
    """PK-GM-007 raised when the contract file does not exist."""
    blueprints_dir = _install(tmp_path)

    with pytest.raises(GovernanceError) as exc_info:
        get_column_ownership_report(
            "test-blueprint", "ghost.yaml", blueprints_dir, _db(tmp_path)
        )

    assert exc_info.value.code == "PK-GM-007"


def test_gm4_set_column_owner_raises_pk_gm_008_for_empty_domain(
    tmp_path: Path,
) -> None:
    """PK-GM-008 raised when the owning domain is blank."""
    _install(tmp_path)

    with pytest.raises(GovernanceError) as exc_info:
        set_column_owner(
            "test-blueprint", "charges.yaml", "amount", "   ", None, None, _db(tmp_path)
        )

    assert exc_info.value.code == "PK-GM-008"


def test_gm4_report_reads_columns_block_contract_shape(tmp_path: Path) -> None:
    """A contract using a ``columns:`` block is read, not reported as empty.

    postgres-to-duckdb uses this shape; the constraint-based shape alone would
    report 0/0 and hide the blueprint from column governance entirely.
    """
    blueprints_dir = _install(tmp_path)
    contract = tmp_path / "blueprints" / "test-blueprint" / "contracts" / "orders.yaml"
    contract.write_text(
        """table: orders
columns:
  - name: order_id
    type: integer
  - name: amount
    type: integer
""",
        encoding="utf-8",
    )

    report = get_column_ownership_report(
        "test-blueprint", "orders.yaml", blueprints_dir, _db(tmp_path)
    )

    assert report.total_columns == 2
    assert report.unowned_columns == ["amount", "order_id"]


def test_gm4_audit_command_exits_1_when_unowned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`owner column audit` exits 1 and flags columns with no owner."""
    _install(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app, ["governance", "owner", "column", "audit", "test-blueprint"]
    )

    assert result.exit_code == 1
    assert "no owner" in result.output


def test_gm4_audit_command_exits_0_when_all_owned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`owner column audit` exits 0 once every contract column is declared."""
    _install(tmp_path)
    monkeypatch.chdir(tmp_path)
    for column in _COLUMNS:
        runner.invoke(
            app,
            [
                "governance",
                "owner",
                "column",
                "set",
                "test-blueprint",
                "--contract",
                "charges.yaml",
                "--column",
                column,
                "--domain",
                "finance",
            ],
        )

    result = runner.invoke(
        app, ["governance", "owner", "column", "audit", "test-blueprint"]
    )

    assert result.exit_code == 0
    assert "4/4 columns declared" in result.output
