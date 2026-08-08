"""GM-4 — column-level domain ownership (SPEC-032).

Extends GM-1 blueprint ownership down to the column level: each column declared
by a contract can name the domain that can authoritatively say what it means and
guarantee its accuracy. Purely deterministic — no AI. Like GM-1, ownership is
organizational state, so it lives in ``state.db`` (``gm_column_owners``) rather
than in the contract YAML (ADR-024).

Unowned columns are a governance gap, never a blocker — the audit surfaces them,
callers decide what to do about it.

See: SPEC-023 and ADR-024 for the GM-1 pattern this follows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml  # type: ignore[import-untyped]

# The contract "column universe" is defined once, in the contracts layer: a
# contract names columns through ``required_columns`` and through its constraint
# blocks. GM-4 reuses that definition rather than restating it, so an audit can
# never disagree with contract validation about which columns exist.
from pipelinekit.contracts.versioning import _columns as _contract_columns
from pipelinekit.core.errors import GovernanceError
from pipelinekit.governance.ownership import BLUEPRINTS_DIR
from pipelinekit.state import db

CONTRACTS_DIR = "contracts"


@dataclass
class ColumnOwner:
    """The domain that owns a single column of a single contract."""

    id: str
    blueprint_name: str
    contract_file: str
    column_name: str
    owner_domain: str
    owner_email: str | None
    description: str | None
    created_at: str
    updated_at: str


@dataclass
class ColumnOwnershipReport:
    """Column-ownership coverage for one contract file."""

    blueprint_name: str
    contract_file: str
    total_columns: int
    owned_columns: int
    unowned_columns: list[str]
    coverage_pct: float


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_column_owner(row: dict) -> ColumnOwner:
    """Rebuild a ``ColumnOwner`` from a stored ``gm_column_owners`` row."""
    return ColumnOwner(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        contract_file=row["contract_file"],
        column_name=row["column_name"],
        owner_domain=row["owner_domain"],
        owner_email=row["owner_email"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def contract_path(
    blueprint_name: str, contract_file: str, blueprints_dir: str | Path
) -> Path:
    """Return the path to a blueprint's contract file."""
    return Path(blueprints_dir) / blueprint_name / CONTRACTS_DIR / contract_file


def list_contract_files(blueprint_name: str, blueprints_dir: str | Path) -> list[str]:
    """Return the names of every contract YAML in a blueprint, sorted.

    An absent ``contracts/`` directory yields an empty list — not every blueprint
    declares contracts, and that is not an error.
    """
    root = Path(blueprints_dir) / blueprint_name / CONTRACTS_DIR
    if not root.is_dir():
        return []
    return sorted(
        entry.name
        for entry in root.iterdir()
        if entry.is_file() and entry.suffix in (".yaml", ".yml")
    )


def get_contract_columns(
    blueprint_name: str, contract_file: str, blueprints_dir: str | Path
) -> list[str]:
    """Return every column a contract references, sorted.

    Raises:
        GovernanceError: ``PK-GM-007`` if the contract file is missing or is not
            readable as YAML.
    """
    path = contract_path(blueprint_name, contract_file, blueprints_dir)
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise GovernanceError(
            "PK-GM-007",
            f"Contract not found: {blueprint_name}/{contract_file}",
            {"blueprint_name": blueprint_name, "contract_file": contract_file},
        ) from exc
    except yaml.YAMLError as exc:
        raise GovernanceError(
            "PK-GM-007",
            f"Contract is not valid YAML: {blueprint_name}/{contract_file}",
            {"blueprint_name": blueprint_name, "contract_file": contract_file},
        ) from exc

    if not isinstance(content, dict):
        raise GovernanceError(
            "PK-GM-007",
            f"Contract is not a YAML mapping: {blueprint_name}/{contract_file}",
            {"blueprint_name": blueprint_name, "contract_file": contract_file},
        )

    _required, all_columns = _contract_columns(content)
    return sorted(all_columns | _declared_columns_block(content))


def _declared_columns_block(content: dict) -> set[str]:
    """Return column names from a contract's explicit ``columns:`` block.

    This repo carries two contract shapes: the constraint-based shape that
    ``contracts.versioning`` understands (``required_columns`` plus ``not_null``
    and friends), and a ``columns:`` block listing each column. GM-4 must see
    both, or a blueprint using the second shape would silently report zero
    columns and appear to need no column governance at all.

    Accepts either a list of names or a list of ``{name: ...}`` mappings.
    """
    raw = content.get("columns")
    if not isinstance(raw, list):
        return set()

    names: set[str] = set()
    for entry in raw:
        if isinstance(entry, str):
            names.add(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
            names.add(entry["name"])
    return names


def set_column_owner(
    blueprint_name: str,
    contract_file: str,
    column_name: str,
    owner_domain: str,
    owner_email: str | None,
    description: str | None,
    db_path: str,
) -> ColumnOwner:
    """Assign or update the domain that owns one contract column.

    Re-setting an existing column preserves its ``id`` and ``created_at``, exactly
    as GM-1 ``set_owner`` does.

    Raises:
        GovernanceError: ``PK-GM-008`` if ``owner_domain`` is empty.
    """
    if not owner_domain or not owner_domain.strip():
        raise GovernanceError(
            "PK-GM-008",
            "Owner domain must not be empty.",
            {"blueprint_name": blueprint_name, "column_name": column_name},
        )

    existing = db.get_column_owner(blueprint_name, contract_file, column_name, db_path)
    now = _utc_now()
    if existing is not None:
        owner_id = existing["id"]
        created_at = existing["created_at"]
    else:
        owner_id = str(uuid.uuid4())
        created_at = now

    owner = ColumnOwner(
        id=owner_id,
        blueprint_name=blueprint_name,
        contract_file=contract_file,
        column_name=column_name,
        owner_domain=owner_domain.strip(),
        owner_email=owner_email,
        description=description,
        created_at=created_at,
        updated_at=now,
    )
    db.upsert_column_owner(owner, db_path)
    return owner


def get_column_owner(
    blueprint_name: str, contract_file: str, column_name: str, db_path: str
) -> ColumnOwner | None:
    """Return one column's owner, or None if that column has no owner."""
    row = db.get_column_owner(blueprint_name, contract_file, column_name, db_path)
    return _row_to_column_owner(row) if row is not None else None


def get_all_column_owners(db_path: str) -> list[ColumnOwner]:
    """Return every declared column owner, across all blueprints."""
    return [_row_to_column_owner(row) for row in db.get_all_column_owners(db_path)]


def get_column_owners_for_contract(
    blueprint_name: str, contract_file: str, db_path: str
) -> list[ColumnOwner]:
    """Return every declared column owner for one contract file."""
    rows = db.get_column_owners_for_contract(blueprint_name, contract_file, db_path)
    return [_row_to_column_owner(row) for row in rows]


def get_column_ownership_report(
    blueprint_name: str,
    contract_file: str,
    blueprints_dir: str,
    db_path: str,
) -> ColumnOwnershipReport:
    """Compare declared column owners against the contract's columns.

    Only columns the contract actually declares count toward coverage: a stored
    owner for a column that the contract no longer references is ignored here, so
    coverage can never exceed 100%.

    Raises:
        GovernanceError: ``PK-GM-007`` if the contract cannot be read.
    """
    columns = get_contract_columns(blueprint_name, contract_file, blueprints_dir)
    owned = {
        owner.column_name
        for owner in get_column_owners_for_contract(
            blueprint_name, contract_file, db_path
        )
    }

    unowned = [column for column in columns if column not in owned]
    total = len(columns)
    owned_count = total - len(unowned)
    coverage_pct = (owned_count / total * 100) if total > 0 else 0.0
    return ColumnOwnershipReport(
        blueprint_name=blueprint_name,
        contract_file=contract_file,
        total_columns=total,
        owned_columns=owned_count,
        unowned_columns=unowned,
        coverage_pct=coverage_pct,
    )


def get_blueprint_column_reports(
    blueprint_name: str, blueprints_dir: str, db_path: str
) -> list[ColumnOwnershipReport]:
    """Return one coverage report per contract in a blueprint.

    Contracts that cannot be read are skipped rather than aborting the audit — a
    single malformed contract must not hide the governance state of the rest.
    """
    reports: list[ColumnOwnershipReport] = []
    for contract_file in list_contract_files(blueprint_name, blueprints_dir):
        try:
            reports.append(
                get_column_ownership_report(
                    blueprint_name, contract_file, blueprints_dir, db_path
                )
            )
        except GovernanceError:
            continue
    return reports


def remove_column_owner(
    blueprint_name: str, contract_file: str, column_name: str, db_path: str
) -> bool:
    """Remove one column's owner. Return True if an owner was removed."""
    return db.delete_column_owner(blueprint_name, contract_file, column_name, db_path)


def blueprint_has_contracts(blueprint_name: str, blueprints_dir: str) -> bool:
    """Return True if the blueprint declares at least one contract file."""
    return bool(list_contract_files(blueprint_name, blueprints_dir))


__all__ = [
    "BLUEPRINTS_DIR",
    "CONTRACTS_DIR",
    "ColumnOwner",
    "ColumnOwnershipReport",
    "blueprint_has_contracts",
    "contract_path",
    "get_all_column_owners",
    "get_blueprint_column_reports",
    "get_column_owner",
    "get_column_owners_for_contract",
    "get_column_ownership_report",
    "get_contract_columns",
    "list_contract_files",
    "remove_column_owner",
    "set_column_owner",
]
