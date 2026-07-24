"""Tests for QM-7 schema drift detection (SPEC-029).

Deterministic, no AI, read-only. Every test uses a ``tmp_path`` SQLite database
and minimal blueprint fixtures under ``tmp_path`` — the real ``blueprints/``
directory and project ``state.db`` are never touched. Contract snapshots are
seeded through the DC-8 db layer; ``schema.yml`` files are written by hand.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.contracts.versioning import ContractVersion
from pipelinekit.quality.drift import (
    DriftType,
    _extract_contract_columns,
    check_all_drift,
    check_blueprint_drift,
)
from pipelinekit.state import db


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def _write_schema(blueprint_dir: Path, model_name: str, columns: list[str]) -> None:
    """Write a minimal dbt ``schema.yml`` with one model and its columns."""
    models = blueprint_dir / "transform" / "models"
    models.mkdir(parents=True, exist_ok=True)
    lines = ["version: 2", "models:", f"  - name: {model_name}", "    columns:"]
    for column in columns:
        lines.append(f"      - name: {column}")
    (models / "schema.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _seed_contract(
    db_path: str,
    blueprint_name: str,
    table_name: str,
    columns: list[str],
    version: str = "1.0.0",
) -> None:
    """Seed a DC-8 contract snapshot declaring ``columns`` for ``table_name``."""
    version_obj = ContractVersion(
        id=f"{blueprint_name}-{table_name}-{version}",
        blueprint_name=blueprint_name,
        contract_file=f"{table_name}.yaml",
        version=version,
        version_major=1,
        version_minor=0,
        version_patch=0,
        content_hash="hash",
        contract_content={"table": table_name, "columns": columns},
        created_at="2026-01-01T00:00:00+00:00",
        created_by="test",
    )
    db.insert_contract_version(version_obj, db_path)


def test_qm7_no_drift_when_contract_matches_schema(tmp_path: Path) -> None:
    """No drift when the contract columns match the schema.yml exactly."""
    db_path = _db(tmp_path)
    bp = tmp_path / "blueprints" / "test-bp"
    _write_schema(bp, "orders", ["order_id", "customer_id", "amount"])
    _seed_contract(db_path, "test-bp", "orders", ["order_id", "customer_id", "amount"])

    results = check_blueprint_drift("test-bp", str(bp), db_path)

    assert len(results) == 1
    assert results[0].status == "CLEAN"
    assert results[0].has_drift is False
    assert results[0].drift_items == []


def test_qm7_detects_column_added_in_schema(tmp_path: Path) -> None:
    """A column present in schema.yml but not the contract is column_added."""
    db_path = _db(tmp_path)
    bp = tmp_path / "blueprints" / "test-bp"
    _write_schema(bp, "orders", ["order_id", "customer_id", "new_column"])
    _seed_contract(db_path, "test-bp", "orders", ["order_id", "customer_id"])

    results = check_blueprint_drift("test-bp", str(bp), db_path)

    assert results[0].status == "DRIFTED"
    added = [
        i for i in results[0].drift_items if i.drift_type == DriftType.COLUMN_ADDED
    ]
    assert [i.name for i in added] == ["new_column"]


def test_qm7_detects_column_removed_from_schema(tmp_path: Path) -> None:
    """A column in the contract but not schema.yml is column_removed."""
    db_path = _db(tmp_path)
    bp = tmp_path / "blueprints" / "test-bp"
    _write_schema(bp, "orders", ["order_id", "customer_id"])
    _seed_contract(db_path, "test-bp", "orders", ["order_id", "customer_id", "amount"])

    results = check_blueprint_drift("test-bp", str(bp), db_path)

    assert results[0].status == "DRIFTED"
    removed = [
        i for i in results[0].drift_items if i.drift_type == DriftType.COLUMN_REMOVED
    ]
    assert [i.name for i in removed] == ["amount"]


def test_qm7_returns_no_baseline_when_no_contract_snapshot(tmp_path: Path) -> None:
    """A model with no contract snapshot yields NO_BASELINE, not an error."""
    db_path = _db(tmp_path)
    bp = tmp_path / "blueprints" / "test-bp"
    _write_schema(bp, "orders", ["order_id"])

    results = check_blueprint_drift("test-bp", str(bp), db_path)

    assert len(results) == 1
    assert results[0].status == "NO_BASELINE"
    assert results[0].contract_version is None
    assert results[0].has_drift is False


def test_qm7_drift_report_aggregates_all_blueprints(tmp_path: Path) -> None:
    """check_all_drift includes results from every installed blueprint."""
    db_path = _db(tmp_path)
    blueprints = tmp_path / "blueprints"
    _write_schema(blueprints / "bp-a", "orders", ["order_id"])
    _seed_contract(db_path, "bp-a", "orders", ["order_id"])
    _write_schema(blueprints / "bp-b", "sales", ["sale_id"])
    _seed_contract(db_path, "bp-b", "sales", ["sale_id"])

    report = check_all_drift(str(blueprints), db_path)

    assert report.blueprints == ["bp-a", "bp-b"]
    assert report.total_tables == 2
    assert {r.blueprint_name for r in report.results} == {"bp-a", "bp-b"}


def test_qm7_drift_report_counts_drifted_tables_correctly(tmp_path: Path) -> None:
    """check_all_drift counts DRIFTED and NO_BASELINE tables correctly."""
    db_path = _db(tmp_path)
    blueprints = tmp_path / "blueprints"
    # bp-a drifts (extra column), bp-b clean, bp-c has no contract (NO_BASELINE).
    _write_schema(blueprints / "bp-a", "orders", ["order_id", "extra"])
    _seed_contract(db_path, "bp-a", "orders", ["order_id"])
    _write_schema(blueprints / "bp-b", "sales", ["sale_id"])
    _seed_contract(db_path, "bp-b", "sales", ["sale_id"])
    _write_schema(blueprints / "bp-c", "leads", ["lead_id"])

    report = check_all_drift(str(blueprints), db_path)

    assert report.total_tables == 3
    assert report.drifted_tables == 1
    assert report.no_baseline_tables == 1


def test_qm7_extract_contract_columns_returns_correct_set() -> None:
    """_extract_contract_columns reads both 'columns' and 'required_columns'."""
    assert _extract_contract_columns({"columns": ["a", "b", "c"]}) == {"a", "b", "c"}
    assert _extract_contract_columns({"required_columns": ["x", "y"]}) == {"x", "y"}


def test_qm7_extract_contract_columns_handles_empty_content() -> None:
    """_extract_contract_columns returns an empty set for unexpected content."""
    assert _extract_contract_columns({}) == set()
    assert _extract_contract_columns({"table": "orders"}) == set()
    assert _extract_contract_columns({"columns": "not-a-list"}) == set()


def test_qm7_clean_status_when_no_drift_items(tmp_path: Path) -> None:
    """status is CLEAN (has_drift False) when there are no drift items."""
    db_path = _db(tmp_path)
    bp = tmp_path / "blueprints" / "test-bp"
    _write_schema(bp, "orders", ["order_id", "customer_id"])
    _seed_contract(db_path, "test-bp", "orders", ["order_id", "customer_id"])

    results = check_blueprint_drift("test-bp", str(bp), db_path)

    assert results[0].status == "CLEAN"
    assert results[0].drift_items == []
    assert results[0].has_drift is False
