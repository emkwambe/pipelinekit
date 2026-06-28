"""Tests for DC-9 breaking change detection (SPEC-021).

Deterministic, no AI. Every test uses a ``tmp_path`` database and temporary SQL
files — never the production ``state.db`` or real blueprints. CLI behaviour is
driven through ``typer.testing.CliRunner`` (no subprocess).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pipelinekit.cli import contract as contract_cli
from pipelinekit.cli.contract import contract_app
from pipelinekit.contracts.versioning import (
    detect_breaking_changes,
    get_contract_version,
    scan_dbt_impact,
    snapshot_contract,
)

runner = CliRunner()

_BP = "test-bp"
_CONTRACT = "charges.yaml"


def _db(tmp_path: Path) -> str:
    """Return a throwaway state.db path inside the test's tmp dir."""
    return str(tmp_path / "state.db")


def _write_sql(blueprint_dir: Path, relative: str, content: str) -> None:
    """Write a dbt model SQL file under the blueprint's transform/models tree."""
    path = blueprint_dir / "transform" / "models" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_dc9_no_breaking_change_returns_none(tmp_path: Path) -> None:
    """detect_breaking_changes returns None when diff is not MAJOR."""
    db_path = _db(tmp_path)
    baseline = {"required_columns": ["payment_id", "amount"]}
    snapshot_contract(_BP, _CONTRACT, baseline, db_path)

    # Additive change — a new optional column → PATCH, not breaking.
    additive = {
        "required_columns": ["payment_id", "amount"],
        "accepted_values": {"status": ["paid", "pending"]},
    }
    result = detect_breaking_changes(
        _BP, _CONTRACT, baseline, additive, str(tmp_path), db_path
    )

    assert result is None


def test_dc9_detects_removed_column_as_breaking(tmp_path: Path) -> None:
    """Removing a column returns BreakingChange with correct removed_columns."""
    db_path = _db(tmp_path)
    baseline = {"required_columns": ["payment_id", "amount"]}
    snapshot_contract(_BP, _CONTRACT, baseline, db_path)

    new_content = {"required_columns": ["payment_id"]}
    result = detect_breaking_changes(
        _BP, _CONTRACT, baseline, new_content, str(tmp_path), db_path
    )

    assert result is not None
    assert result.removed_columns == ["amount"]
    assert result.proposed_version == "2.0.0"
    assert result.current_version == "1.0.0"


def test_dc9_snapshot_blocks_on_breaking_change_without_force(
    tmp_path: Path, monkeypatch
) -> None:
    """snapshot exits non-zero when breaking change detected and no --force."""
    db_path = _db(tmp_path)
    snapshot_contract(_BP, _CONTRACT, {"required_columns": ["a", "b"]}, db_path)

    monkeypatch.setattr(contract_cli, "_db_path", lambda: db_path)
    monkeypatch.setattr(
        contract_cli,
        "_discover_contracts",
        lambda blueprint=None: [(_BP, _CONTRACT, {"required_columns": ["a"]})],
    )

    result = runner.invoke(contract_app, ["snapshot"])

    assert result.exit_code == 1
    # The breaking version was NOT written — baseline preserved.
    assert get_contract_version(_BP, _CONTRACT, db_path).version == "1.0.0"


def test_dc9_snapshot_proceeds_with_force_flag(tmp_path: Path, monkeypatch) -> None:
    """snapshot --force writes MAJOR version despite breaking change."""
    db_path = _db(tmp_path)
    snapshot_contract(_BP, _CONTRACT, {"required_columns": ["a", "b"]}, db_path)

    monkeypatch.setattr(contract_cli, "_db_path", lambda: db_path)
    monkeypatch.setattr(
        contract_cli,
        "_discover_contracts",
        lambda blueprint=None: [(_BP, _CONTRACT, {"required_columns": ["a"]})],
    )

    result = runner.invoke(contract_app, ["snapshot", "--force"])

    assert result.exit_code == 0
    assert get_contract_version(_BP, _CONTRACT, db_path).version == "2.0.0"


def test_dc9_scan_dbt_impact_finds_column_reference(tmp_path: Path) -> None:
    """scan_dbt_impact finds column name in a .sql file with correct line number."""
    blueprint_dir = tmp_path / "bp"
    _write_sql(
        blueprint_dir,
        "staging/stg_charges.sql",
        "select\n    payment_id,\n    payment_method_details\nfrom raw\n",
    )

    impacts = scan_dbt_impact(str(blueprint_dir), ["payment_method_details"])

    assert len(impacts) == 1
    assert impacts[0].column_name == "payment_method_details"
    assert impacts[0].line_number == 3
    assert impacts[0].model_file == "transform/models/staging/stg_charges.sql"


def test_dc9_scan_dbt_impact_returns_empty_when_no_transform_dir(
    tmp_path: Path,
) -> None:
    """scan_dbt_impact returns [] when transform/ does not exist."""
    assert scan_dbt_impact(str(tmp_path), ["any_column"]) == []


def test_dc9_scan_dbt_impact_returns_empty_when_column_not_referenced(
    tmp_path: Path,
) -> None:
    """scan_dbt_impact returns [] when column not found in any .sql."""
    blueprint_dir = tmp_path / "bp"
    _write_sql(blueprint_dir, "core/fct.sql", "select a, b from raw\n")

    assert scan_dbt_impact(str(blueprint_dir), ["receipt_url"]) == []


def test_dc9_check_breaking_command_shows_clean_when_no_changes(
    tmp_path: Path, monkeypatch
) -> None:
    """check-breaking subcommand exits 0 when no breaking changes."""
    db_path = _db(tmp_path)
    content = {"required_columns": ["payment_id", "amount"]}
    snapshot_contract(_BP, _CONTRACT, content, db_path)

    monkeypatch.setattr(contract_cli, "_db_path", lambda: db_path)
    monkeypatch.setattr(
        contract_cli,
        "_discover_contracts",
        lambda blueprint=None: [(_BP, _CONTRACT, content)],
    )

    result = runner.invoke(contract_app, ["check-breaking"])

    assert result.exit_code == 0
    assert "no breaking changes" in result.stdout


def test_dc9_breaking_change_includes_correct_dbt_impact(tmp_path: Path) -> None:
    """BreakingChange.dbt_impact contains correct model_file and line_number."""
    db_path = _db(tmp_path)
    blueprint_dir = tmp_path / "bp"
    _write_sql(
        blueprint_dir,
        "core/fct_payments.sql",
        "select\n    payment_id,\n    amount,\n    receipt_url\nfrom raw\n",
    )

    baseline = {"required_columns": ["payment_id", "receipt_url"]}
    snapshot_contract(_BP, _CONTRACT, baseline, db_path)

    new_content = {"required_columns": ["payment_id"]}
    result = detect_breaking_changes(
        _BP, _CONTRACT, baseline, new_content, str(blueprint_dir), db_path
    )

    assert result is not None
    matches = [
        i
        for i in result.dbt_impact
        if i.column_name == "receipt_url"
        and i.model_file == "transform/models/core/fct_payments.sql"
        and i.line_number == 4
    ]
    assert matches
