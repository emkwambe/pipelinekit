"""QM-7 — schema drift detection between contracts and ``schema.yml`` (SPEC-029).

Compares two existing sources of truth without a warehouse connection:

* what the data contracts declare (DC-8 ``dc_contract_versions.contract_content``)
* what the dbt ``schema.yml`` files actually define (QM-4 ``scan_dbt_coverage``)

For each dbt model, QM-7 finds the matching contract (by table name) and reports
columns that appear in ``schema.yml`` but not the contract (``column_added``) or
in the contract but not ``schema.yml`` (``column_removed``). A model with no
matching contract snapshot is ``NO_BASELINE`` — not an error. Read-only and
deterministic — no AI, no new ``state.db`` tables.

See: SPEC-029, ADR-030.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pipelinekit.quality.coverage import scan_dbt_coverage
from pipelinekit.state import db

# Contract keys that hold a list of column names, in priority order. Real
# contracts use ``required_columns``; the SPEC test fixture uses ``columns``.
_COLUMN_KEYS = ("columns", "required_columns")


class DriftType(str, Enum):
    """The kind of schema drift detected for a single name."""

    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"


@dataclass
class DriftItem:
    """One drifted column between a contract and its ``schema.yml`` model."""

    drift_type: DriftType
    name: str
    detail: str


@dataclass
class TableDriftResult:
    """Drift outcome for one table (dbt model) of a blueprint."""

    blueprint_name: str
    table_name: str
    contract_version: str | None
    drift_items: list[DriftItem]
    status: str  # "CLEAN" | "DRIFTED" | "NO_BASELINE"
    has_drift: bool


@dataclass
class DriftReport:
    """Aggregate schema-drift report across blueprints."""

    blueprints: list[str]
    results: list[TableDriftResult]
    total_tables: int
    drifted_tables: int
    no_baseline_tables: int
    generated_at: str


def _extract_contract_columns(contract_content: dict) -> set[str]:
    """Return the set of column names declared by a contract.

    Handles both the real contract shape (``required_columns``) and the test
    shape (``columns``). Returns an empty set for any unexpected structure.
    """
    if not isinstance(contract_content, dict):
        return set()
    for key in _COLUMN_KEYS:
        value = contract_content.get(key)
        if isinstance(value, list):
            return {str(name) for name in value if isinstance(name, str)}
    return set()


def _contract_table_name(contract_file: str, contract_content: dict) -> str:
    """Resolve a contract's table name from its content or filename."""
    if isinstance(contract_content, dict):
        table = contract_content.get("table")
        if isinstance(table, str) and table:
            return table
    return Path(contract_file).stem


def _diff_columns(contract_cols: set[str], schema_cols: set[str]) -> list[DriftItem]:
    """Build drift items for column additions and removals."""
    items: list[DriftItem] = []
    for name in sorted(schema_cols - contract_cols):
        items.append(
            DriftItem(
                DriftType.COLUMN_ADDED,
                name,
                f"{name} (in schema.yml, not in contract)",
            )
        )
    for name in sorted(contract_cols - schema_cols):
        items.append(
            DriftItem(
                DriftType.COLUMN_REMOVED,
                name,
                f"{name} (in contract, not in schema.yml)",
            )
        )
    return items


def check_blueprint_drift(
    blueprint_name: str,
    blueprint_dir: str,
    db_path: str,
) -> list[TableDriftResult]:
    """Compare each dbt model of a blueprint against its contract snapshot.

    Returns one ``TableDriftResult`` per dbt model. A model whose table has a
    contract snapshot is ``CLEAN`` or ``DRIFTED``; a model with no matching
    snapshot is ``NO_BASELINE``. Returns an empty list when the blueprint has no
    dbt models to check.
    """
    # Latest contract snapshot per contract file, indexed by table name.
    contracts_by_table: dict[str, tuple[str, set[str]]] = {}
    for row in db.get_latest_contracts_for_blueprint(blueprint_name, db_path):
        content = json.loads(row["contract_content"])
        table_name = _contract_table_name(row["contract_file"], content)
        contracts_by_table[table_name] = (
            row["version"],
            _extract_contract_columns(content),
        )

    results: list[TableDriftResult] = []
    for model in scan_dbt_coverage(blueprint_dir):
        schema_cols = {col.name for col in model.columns}
        match = contracts_by_table.get(model.name)
        if match is None:
            results.append(
                TableDriftResult(
                    blueprint_name=blueprint_name,
                    table_name=model.name,
                    contract_version=None,
                    drift_items=[],
                    status="NO_BASELINE",
                    has_drift=False,
                )
            )
            continue

        version, contract_cols = match
        drift_items = _diff_columns(contract_cols, schema_cols)
        results.append(
            TableDriftResult(
                blueprint_name=blueprint_name,
                table_name=model.name,
                contract_version=version,
                drift_items=drift_items,
                status="DRIFTED" if drift_items else "CLEAN",
                has_drift=bool(drift_items),
            )
        )
    return results


def check_all_drift(blueprints_dir: str, db_path: str) -> DriftReport:
    """Run drift detection across every installed blueprint.

    Each immediate subdirectory of ``blueprints_dir`` is treated as an installed
    blueprint. Returns a ``DriftReport`` with aggregate counts.
    """
    root = Path(blueprints_dir)
    names: list[str] = []
    results: list[TableDriftResult] = []
    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                names.append(entry.name)
                results.extend(check_blueprint_drift(entry.name, str(entry), db_path))

    drifted = sum(1 for r in results if r.status == "DRIFTED")
    no_baseline = sum(1 for r in results if r.status == "NO_BASELINE")
    return DriftReport(
        blueprints=names,
        results=results,
        total_tables=len(results),
        drifted_tables=drifted,
        no_baseline_tables=no_baseline,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
