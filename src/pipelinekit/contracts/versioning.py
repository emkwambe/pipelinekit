"""DC-8 — schema versioning for data contracts (SPEC-020).

Tracks how a data contract evolves over time. Each snapshot computes a SHA-256
hash of the contract, assigns a semantic version (``MAJOR.MINOR.PATCH``), and
stores it in ``state.db`` via the ``state.db`` module. Version bumping is purely
deterministic — no AI (the AI-assisted bump proposal is DC-11, not DC-8; see the
explicit scope note in SPEC-020).

Version bump rules (deterministic):

    New contract (no prior version):  -> 1.0.0 / "new"
    Added optional column:            -> PATCH
    Added required column:            -> MINOR
    Removed / renamed column:         -> MAJOR
    Changed column type:              -> MAJOR (see note below)
    Added accepted value:             -> PATCH
    Removed accepted value:           -> MINOR
    Tightened constraint (not_null):  -> MINOR
    Loosened constraint:              -> PATCH
    No change (same hash):            -> same version / "none"

Note on column types: the ``ContractDefinition`` schema (SPEC-004) does not carry
per-column types, so "changed column type" is not detectable from contract
content and never triggers a MAJOR bump on its own. This is flagged in the DC-8
build report as a SPEC deviation.

See: SPEC-020, ADR-021.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.core.errors import ContractError
from pipelinekit.state import db

_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@dataclass
class ContractVersion:
    """A single stored snapshot of a contract at a point in time."""

    id: str
    blueprint_name: str
    contract_file: str
    version: str
    version_major: int
    version_minor: int
    version_patch: int
    content_hash: str
    contract_content: dict
    created_at: str
    created_by: str = "pipelinekit"


@dataclass
class ContractDiff:
    """The difference between two stored versions of a contract."""

    version_a: str
    version_b: str
    added_fields: list[str] = field(default_factory=list)
    removed_fields: list[str] = field(default_factory=list)
    changed_constraints: list[str] = field(default_factory=list)
    change_type: str = "none"  # "patch" | "minor" | "major" | "none"


def _utc_now() -> str:
    """Return the current time as an ISO 8601 UTC string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compute_hash(content: dict) -> str:
    """Return a stable 12-char SHA-256 over the normalized contract JSON."""
    normalized = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse ``MAJOR.MINOR.PATCH`` (optional leading ``v``).

    Raises:
        ContractError: ``PK-DC-009`` if the string is not a valid semver.
    """
    match = _SEMVER_RE.match(version.strip())
    if match is None:
        raise ContractError(
            "PK-DC-009",
            f"Version format invalid: '{version}'. Expected MAJOR.MINOR.PATCH.",
            {"version": version},
        )
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _columns(content: dict) -> tuple[set[str], set[str]]:
    """Return ``(required_columns, all_referenced_columns)`` for a contract.

    A contract references columns through ``required_columns`` and through its
    constraints (``not_null``, ``uniqueness``, ``accepted_values`` keys, and the
    ``freshness`` column). The union is the contract's column universe; columns
    in the universe but not required are treated as optional.
    """
    required = set(content.get("required_columns") or [])
    constraint_cols = (
        set(content.get("not_null") or [])
        | set(content.get("uniqueness") or [])
        | set((content.get("accepted_values") or {}).keys())
    )
    freshness = content.get("freshness") or {}
    if isinstance(freshness, dict) and freshness.get("column"):
        constraint_cols.add(freshness["column"])
    return required, required | constraint_cols


def _accepted_values_removed(old: dict, new: dict) -> bool:
    """True if any previously-accepted value was dropped from a column."""
    old_av = old.get("accepted_values") or {}
    new_av = new.get("accepted_values") or {}
    for col, allowed in old_av.items():
        if col in new_av and (set(allowed) - set(new_av[col])):
            return True
    return False


def _classify_change(old: dict, new: dict) -> str:
    """Classify a contract change as ``major``, ``minor``, or ``patch``.

    Precedence is MAJOR > MINOR > PATCH. Assumes the two contents differ.
    """
    old_required, old_all = _columns(old)
    new_required, new_all = _columns(new)

    # MAJOR — a column was removed or renamed (a rename drops the old name).
    if old_all - new_all:
        return "major"

    # MINOR — newly required columns, tightened not_null, or removed values.
    added_required = new_required - old_required
    tightened_not_null = set(new.get("not_null") or []) - set(old.get("not_null") or [])
    if added_required or tightened_not_null or _accepted_values_removed(old, new):
        return "minor"

    # PATCH — added optional column, added accepted value, loosened constraint.
    return "patch"


def compute_next_version(
    current: str | None,
    old_content: dict | None,
    new_content: dict,
) -> tuple[str, str]:
    """Compute the next semantic version deterministically (no AI — DC-8).

    Returns ``(version_string, change_type)`` where ``change_type`` is one of
    ``"new"``, ``"patch"``, ``"minor"``, ``"major"``, or ``"none"``.
    """
    if current is None or old_content is None:
        return "1.0.0", "new"

    if _compute_hash(old_content) == _compute_hash(new_content):
        return current, "none"

    major, minor, patch = _parse_semver(current)
    change_type = _classify_change(old_content, new_content)
    if change_type == "major":
        major, minor, patch = major + 1, 0, 0
    elif change_type == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}", change_type


def snapshot_contract(
    blueprint_name: str,
    contract_file: str,
    contract_content: dict,
    db_path: str | Path,
) -> ContractVersion:
    """Snapshot a contract, assigning the next version (idempotent on no-op).

    If the content hash matches the latest stored version, the existing version
    is returned and nothing is written.
    """
    latest = db.get_latest_contract_version(blueprint_name, contract_file, db_path)
    new_hash = _compute_hash(contract_content)

    if latest is not None and latest["content_hash"] == new_hash:
        return _row_to_version(latest)

    current = latest["version"] if latest is not None else None
    old_content = json.loads(latest["contract_content"]) if latest is not None else None
    next_version, _change = compute_next_version(current, old_content, contract_content)
    major, minor, patch = _parse_semver(next_version)

    version = ContractVersion(
        id=str(uuid.uuid4()),
        blueprint_name=blueprint_name,
        contract_file=contract_file,
        version=next_version,
        version_major=major,
        version_minor=minor,
        version_patch=patch,
        content_hash=new_hash,
        contract_content=contract_content,
        created_at=_utc_now(),
    )
    db.insert_contract_version(version, db_path)
    return version


def get_contract_version(
    blueprint_name: str,
    contract_file: str,
    db_path: str | Path,
) -> ContractVersion | None:
    """Return the latest version of a contract, or None if none exists."""
    latest = db.get_latest_contract_version(blueprint_name, contract_file, db_path)
    return _row_to_version(latest) if latest is not None else None


def get_contract_history(
    blueprint_name: str,
    contract_file: str,
    db_path: str | Path,
) -> list[ContractVersion]:
    """Return every version of a contract, newest first."""
    rows = db.get_contract_version_history(blueprint_name, contract_file, db_path)
    return [_row_to_version(row) for row in rows]


def diff_contract_versions(
    blueprint_name: str,
    contract_file: str,
    version_a: str,
    version_b: str,
    db_path: str | Path,
) -> ContractDiff:
    """Compare two stored versions of a contract.

    Raises:
        ContractError: ``PK-DC-009`` if a version string is malformed,
            ``PK-DC-008`` if either version is not stored.
    """
    # Validate format first so a malformed argument fails fast (PK-DC-009).
    _parse_semver(version_a)
    _parse_semver(version_b)

    row_a = db.get_contract_version_by_semver(
        blueprint_name, contract_file, version_a.lstrip("v"), db_path
    ) or db.get_contract_version_by_semver(
        blueprint_name, contract_file, version_a, db_path
    )
    row_b = db.get_contract_version_by_semver(
        blueprint_name, contract_file, version_b.lstrip("v"), db_path
    ) or db.get_contract_version_by_semver(
        blueprint_name, contract_file, version_b, db_path
    )
    if row_a is None or row_b is None:
        missing = version_a if row_a is None else version_b
        raise ContractError(
            "PK-DC-008",
            f"Contract version not found: {missing}",
            {
                "blueprint_name": blueprint_name,
                "contract_file": contract_file,
                "version": missing,
            },
        )

    old = json.loads(row_a["contract_content"])
    new = json.loads(row_b["contract_content"])
    _old_required, old_all = _columns(old)
    _new_required, new_all = _columns(new)

    same = _compute_hash(old) == _compute_hash(new)
    change_type = "none" if same else _classify_change(old, new)

    return ContractDiff(
        version_a=row_a["version"],
        version_b=row_b["version"],
        added_fields=sorted(new_all - old_all),
        removed_fields=sorted(old_all - new_all),
        changed_constraints=_constraint_changes(old, new),
        change_type=change_type,
    )


def _constraint_changes(old: dict, new: dict) -> list[str]:
    """Return human-readable descriptions of constraint-level changes."""
    changes: list[str] = []
    for key in ("not_null", "uniqueness", "required_columns"):
        old_set = set(old.get(key) or [])
        new_set = set(new.get(key) or [])
        for added in sorted(new_set - old_set):
            changes.append(f"{key}: +{added}")
        for removed in sorted(old_set - new_set):
            changes.append(f"{key}: -{removed}")

    old_av = old.get("accepted_values") or {}
    new_av = new.get("accepted_values") or {}
    for col in sorted(set(old_av) | set(new_av)):
        before = set(old_av.get(col) or [])
        after = set(new_av.get(col) or [])
        for added in sorted(after - before):
            changes.append(f"accepted_values[{col}]: +{added}")
        for removed in sorted(before - after):
            changes.append(f"accepted_values[{col}]: -{removed}")
    return changes


def _row_to_version(row: dict) -> ContractVersion:
    """Rebuild a ``ContractVersion`` from a stored ``dc_contract_versions`` row."""
    return ContractVersion(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        contract_file=row["contract_file"],
        version=row["version"],
        version_major=row["version_major"],
        version_minor=row["version_minor"],
        version_patch=row["version_patch"],
        content_hash=row["content_hash"],
        contract_content=json.loads(row["contract_content"]),
        created_at=row["created_at"],
        created_by=row["created_by"],
    )
