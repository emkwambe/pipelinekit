"""Local-first state store backed by stdlib ``sqlite3``.

State is metadata only — never pipeline data — and lives at
``<cwd>/.pipelinekit/state.db``. All reads and writes go through this module;
the CLI and runtime never issue SQL directly. ``initialize`` is idempotent and
safe to call on every startup.

The ``cwd`` parameters resolve ``Path.cwd()`` at call time (see the note in
``config/loader.py``) so behaviour is correct under ``chdir`` and in tests.

See: SPEC-007, ADR-004 (local-first), docs/reference/Error-Codes.md.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from pipelinekit.core.errors import StateError

if TYPE_CHECKING:
    from pipelinekit.contracts.versioning import ContractVersion

STATE_DIR = ".pipelinekit"
STATE_DB = "state.db"
GITIGNORE_ENTRY = ".pipelinekit/"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id          TEXT PRIMARY KEY,
    pipeline    TEXT NOT NULL,
    status      TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    duration_s  REAL,
    error_code  TEXT,
    error_msg   TEXT
);

CREATE TABLE IF NOT EXISTS validation_runs (
    id          TEXT PRIMARY KEY,
    status      TEXT NOT NULL,
    ran_at      TEXT NOT NULL,
    error_count INTEGER DEFAULT 0,
    errors      TEXT
);

CREATE TABLE IF NOT EXISTS contract_results (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    status          TEXT NOT NULL,
    violation_count INTEGER DEFAULT 0,
    violations      TEXT,
    checked_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diagnostic_results (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    status          TEXT NOT NULL,
    finding_type    TEXT NOT NULL,
    confidence      REAL NOT NULL,
    explanation     TEXT,
    evidence        TEXT,
    actions         TEXT,
    can_auto_fix    INTEGER DEFAULT 0,
    diagnosed_at    TEXT NOT NULL,
    provider        TEXT
);

CREATE TABLE IF NOT EXISTS architecture_results (
    id              TEXT PRIMARY KEY,
    reasoning_type  TEXT NOT NULL,
    question        TEXT,
    confidence      REAL NOT NULL,
    recommendation  TEXT,
    tradeoffs       TEXT,
    adr_compliance  TEXT,
    can_auto_apply  INTEGER DEFAULT 0,
    analyzed_at     TEXT NOT NULL,
    provider        TEXT
);

CREATE TABLE IF NOT EXISTS health_runs (
    id                TEXT PRIMARY KEY,
    ran_at            TEXT NOT NULL,
    deps_status       TEXT,
    security_status   TEXT,
    blueprints_status TEXT,
    specs_status      TEXT,
    tests_status      TEXT,
    overall_status    TEXT,
    summary           TEXT
);

CREATE TABLE IF NOT EXISTS blueprint_proposals (
    plan_id          TEXT PRIMARY KEY,
    blueprint_name   TEXT NOT NULL,
    source_type      TEXT NOT NULL,
    destination_type TEXT NOT NULL,
    tables           TEXT,
    assets           TEXT,
    confidence       REAL,
    assumptions      TEXT,
    unsupported      TEXT,
    decisions        TEXT,
    provider         TEXT,
    can_auto_apply   INTEGER DEFAULT 0,
    applied          INTEGER DEFAULT 0,
    proposed_at      TEXT NOT NULL,
    applied_at       TEXT
);

CREATE TABLE IF NOT EXISTS installed_blueprints (
    name            TEXT PRIMARY KEY,
    version         TEXT NOT NULL,
    source          TEXT,
    destination     TEXT,
    verified        INTEGER DEFAULT 0,
    installed_at    TEXT NOT NULL,
    registry_url    TEXT
);

CREATE TABLE IF NOT EXISTS blueprint_versions (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    from_version TEXT,
    to_version   TEXT NOT NULL,
    action       TEXT NOT NULL,
    backup_path  TEXT,
    applied_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dc_contract_versions (
    id TEXT PRIMARY KEY,
    blueprint_name TEXT NOT NULL,
    contract_file TEXT NOT NULL,
    version TEXT NOT NULL,
    version_major INTEGER NOT NULL,
    version_minor INTEGER NOT NULL,
    version_patch INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    contract_content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT 'pipelinekit'
);

CREATE INDEX IF NOT EXISTS idx_dc_contract_versions_blueprint
    ON dc_contract_versions(blueprint_name, contract_file, created_at);
"""


def _resolve(cwd: Path | None) -> Path:
    """Resolve the working directory at call time."""
    return cwd if cwd is not None else Path.cwd()


def _utc_now() -> str:
    """Return the current time as an ISO 8601 UTC string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_db_path(cwd: Path | None = None) -> Path:
    """Return the path to ``state.db``, creating ``.pipelinekit/`` if needed.

    Raises:
        StateError: ``PK-STATE-001`` if the directory cannot be created.
    """
    state_dir = _resolve(cwd) / STATE_DIR
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StateError(
            "PK-STATE-001",
            f"Cannot create state directory at {state_dir}",
            {"path": str(state_dir), "detail": str(exc)},
        ) from exc
    return state_dir / STATE_DB


def initialize(cwd: Path | None = None) -> None:
    """Create ``state.db`` and apply the schema. Idempotent.

    Raises:
        StateError: ``PK-STATE-001`` if the database cannot be opened or
            initialized.
    """
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.executescript(_SCHEMA)
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-001",
            f"Cannot open or initialize state database at {db_path}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def get_recent_runs(n: int = 5, cwd: Path | None = None) -> list[dict]:
    """Return the most recent ``n`` pipeline runs, newest first.

    Returns an empty list on a fresh database; never raises on emptiness.

    Raises:
        StateError: ``PK-STATE-001`` if the database is unavailable.
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, pipeline, status, started_at, finished_at,
                       duration_s, error_code, error_msg
                FROM pipeline_runs
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (n,),
            ).fetchall()
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-001",
            f"Cannot read state database at {db_path}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc
    return [dict(row) for row in rows]


def insert_run(run_id: str, pipeline_name: str, cwd: Path | None = None) -> None:
    """Insert a new run record with ``status=pending``.

    Called by the runtime in Phase 2.

    Raises:
        StateError: ``PK-STATE-002`` if the record cannot be written.
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO pipeline_runs (id, pipeline, status, started_at)
                VALUES (?, ?, 'pending', ?)
                """,
                (run_id, pipeline_name, _utc_now()),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot write run {run_id} to state database",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def update_run(
    run_id: str,
    status: str,
    duration_s: float,
    error_code: str | None = None,
    error_msg: str | None = None,
    cwd: Path | None = None,
) -> None:
    """Update a run record on completion or failure.

    Called by the runtime in Phase 2.

    Raises:
        StateError: ``PK-STATE-002`` if the record cannot be updated.
    """
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                UPDATE pipeline_runs
                SET status = ?, finished_at = ?, duration_s = ?,
                    error_code = ?, error_msg = ?
                WHERE id = ?
                """,
                (status, _utc_now(), duration_s, error_code, error_msg, run_id),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot update run {run_id} in state database",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def insert_contract_result(
    run_id: str,
    table_name: str,
    status: str,
    violation_count: int,
    violations_json: str,
    cwd: Path | None = None,
) -> None:
    """Store a contract validation result for a table (SPEC-004)."""
    initialize(cwd)
    db_path = get_db_path(cwd)
    result_id = f"cr-{uuid.uuid4().hex[:8]}"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO contract_results (
                    id, run_id, table_name, status,
                    violation_count, violations, checked_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    run_id,
                    table_name,
                    status,
                    violation_count,
                    violations_json,
                    _utc_now(),
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot write contract result for {table_name}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def insert_diagnostic_result(
    run_id: str,
    result: dict,
    provider: str,
    cwd: Path | None = None,
) -> None:
    """Store an AI diagnostic result (SPEC-005). Called by DiagnosticsEngine only.

    ``result`` is a serialized ``DiagnosticResult`` (its ``model_dump``). Evidence
    and recommended actions are stored as JSON. The AI layer never writes state
    directly — it goes through this function (ADR-007, ADR-014).
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    result_id = f"diag-{uuid.uuid4().hex[:8]}"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO diagnostic_results (
                    id, run_id, status, finding_type, confidence,
                    explanation, evidence, actions, can_auto_fix,
                    diagnosed_at, provider
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    run_id,
                    result.get("status", ""),
                    result.get("finding_type", ""),
                    float(result.get("confidence", 0.0)),
                    result.get("explanation", ""),
                    json.dumps(result.get("evidence", [])),
                    json.dumps(result.get("recommended_actions", [])),
                    1 if result.get("can_auto_fix") else 0,
                    _utc_now(),
                    provider,
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot write diagnostic result for run {run_id}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def insert_architecture_result(
    reasoning_type: str,
    result: dict,
    provider: str,
    question: str | None = None,
    cwd: Path | None = None,
) -> None:
    """Store an architecture result (SPEC-011). Called by ArchitectureEngine only.

    ``result`` is a serialized ``ArchitectureResult`` (its ``model_dump``).
    Recommendation, tradeoffs, and ADR compliance are stored as JSON. The AI
    layer never writes state directly — it goes through this function
    (ADR-007, ADR-015). ``can_auto_apply`` is always stored as 0 in Phase 5.
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    result_id = f"arch-{uuid.uuid4().hex[:8]}"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO architecture_results (
                    id, reasoning_type, question, confidence,
                    recommendation, tradeoffs, adr_compliance,
                    can_auto_apply, analyzed_at, provider
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    reasoning_type,
                    question,
                    float(result.get("confidence", 0.0)),
                    json.dumps(result.get("recommendation", {})),
                    json.dumps(result.get("tradeoffs", [])),
                    json.dumps(result.get("adr_compliance", [])),
                    1 if result.get("can_auto_apply") else 0,
                    _utc_now(),
                    provider,
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot write architecture result for {reasoning_type}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def insert_health_run(results: dict, cwd: Path | None = None) -> None:
    """Store a health run result (SPEC-012). Called by the health command only.

    ``results`` carries the per-check statuses, the overall status, and a JSON
    ``summary``. Lets ``pipelinekit status`` surface the last health check date.
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    result_id = f"health-{uuid.uuid4().hex[:8]}"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO health_runs (
                    id, ran_at, deps_status, security_status,
                    blueprints_status, specs_status, tests_status,
                    overall_status, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    _utc_now(),
                    results.get("deps_status"),
                    results.get("security_status"),
                    results.get("blueprints_status"),
                    results.get("specs_status"),
                    results.get("tests_status"),
                    results.get("overall_status"),
                    results.get("summary"),
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            "Cannot write health run to state database",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def insert_blueprint_proposal(proposal: dict, cwd: Path | None = None) -> None:
    """Store a blueprint proposal (SPEC-015). Called by BlueprintProposer only.

    ``proposal`` is a serialized ``BlueprintProposal`` (its ``to_dict``). The
    full asset list — with per-asset state — is stored as JSON so ``show`` and
    ``apply plan`` can reload the exact proposal. No files are written here; this
    is the audit record of what AI proposed (ADR-018).
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO blueprint_proposals (
                    plan_id, blueprint_name, source_type, destination_type,
                    tables, assets, confidence, assumptions, unsupported,
                    decisions, provider, can_auto_apply, applied,
                    proposed_at, applied_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal["plan_id"],
                    proposal["blueprint_name"],
                    proposal["source_type"],
                    proposal["destination_type"],
                    json.dumps(proposal.get("tables", [])),
                    json.dumps(proposal.get("assets", [])),
                    float(proposal.get("confidence", 0.0)),
                    json.dumps(proposal.get("assumptions", [])),
                    json.dumps(proposal.get("unsupported_areas", [])),
                    json.dumps(proposal.get("requires_human_decisions", [])),
                    proposal.get("provider", ""),
                    1 if proposal.get("can_auto_apply") else 0,
                    1 if proposal.get("applied") else 0,
                    proposal.get("generated_at") or _utc_now(),
                    None,
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot write blueprint proposal {proposal.get('plan_id')}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def get_blueprint_proposal(plan_id: str, cwd: Path | None = None) -> dict | None:
    """Return the stored proposal for ``plan_id``, or None if not found.

    The returned dict is shaped like ``BlueprintProposal.to_dict`` so the caller
    can rebuild it via ``BlueprintProposal.from_dict``.
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM blueprint_proposals WHERE plan_id = ?", (plan_id,)
            ).fetchone()
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-001",
            f"Cannot read blueprint proposal {plan_id}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc
    if row is None:
        return None
    return {
        "plan_id": row["plan_id"],
        "blueprint_name": row["blueprint_name"],
        "source_type": row["source_type"],
        "destination_type": row["destination_type"],
        "tables": json.loads(row["tables"] or "[]"),
        "assets": json.loads(row["assets"] or "[]"),
        "confidence": row["confidence"],
        "assumptions": json.loads(row["assumptions"] or "[]"),
        "unsupported_areas": json.loads(row["unsupported"] or "[]"),
        "requires_human_decisions": json.loads(row["decisions"] or "[]"),
        "provider": row["provider"],
        "generated_at": row["proposed_at"],
        "can_auto_apply": bool(row["can_auto_apply"]),
        "applied": bool(row["applied"]),
    }


def mark_proposal_applied(
    plan_id: str, assets: list[dict], cwd: Path | None = None
) -> None:
    """Mark a proposal applied and persist the post-write asset states."""
    initialize(cwd)
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                UPDATE blueprint_proposals
                SET applied = 1, applied_at = ?, assets = ?
                WHERE plan_id = ?
                """,
                (_utc_now(), json.dumps(assets), plan_id),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot update blueprint proposal {plan_id}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def insert_installed_blueprint(
    name: str,
    version: str,
    source: str,
    destination: str,
    verified: bool,
    registry_url: str | None,
    cwd: Path | None = None,
) -> None:
    """Record a blueprint installed from the remote registry (SPEC-016)."""
    initialize(cwd)
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO installed_blueprints (
                    name, version, source, destination, verified,
                    installed_at, registry_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    version,
                    source,
                    destination,
                    1 if verified else 0,
                    _utc_now(),
                    registry_url,
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot record installed blueprint {name}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def get_installed_blueprints(cwd: Path | None = None) -> list[dict]:
    """Return every recorded installed blueprint, sorted by name (SPEC-018).

    Returns an empty list on a fresh database; never raises on emptiness.

    Raises:
        StateError: ``PK-STATE-001`` if the database is unavailable.
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT name, version, source, destination, verified,
                       installed_at, registry_url
                FROM installed_blueprints
                ORDER BY name
                """
            ).fetchall()
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-001",
            "Cannot read installed blueprints from state database",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc
    return [dict(row) for row in rows]


def insert_blueprint_version(
    name: str,
    from_version: str | None,
    to_version: str,
    action: str,
    backup_path: str | None = None,
    cwd: Path | None = None,
) -> None:
    """Record one blueprint version transition (SPEC-018).

    ``action`` is ``install`` | ``upgrade`` | ``rollback``. This is an audit log
    of version changes; it never moves files itself.

    Raises:
        StateError: ``PK-STATE-002`` if the record cannot be written.
    """
    initialize(cwd)
    db_path = get_db_path(cwd)
    record_id = f"bv-{uuid.uuid4().hex[:8]}"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO blueprint_versions (
                    id, name, from_version, to_version, action,
                    backup_path, applied_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    name,
                    from_version,
                    to_version,
                    action,
                    backup_path,
                    _utc_now(),
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-002",
            f"Cannot record version change for blueprint {name}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


_CONTRACT_VERSIONS_DDL = """
CREATE TABLE IF NOT EXISTS dc_contract_versions (
    id TEXT PRIMARY KEY,
    blueprint_name TEXT NOT NULL,
    contract_file TEXT NOT NULL,
    version TEXT NOT NULL,
    version_major INTEGER NOT NULL,
    version_minor INTEGER NOT NULL,
    version_patch INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    contract_content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT 'pipelinekit'
);

CREATE INDEX IF NOT EXISTS idx_dc_contract_versions_blueprint
    ON dc_contract_versions(blueprint_name, contract_file, created_at);
"""


def _connect_versions(db_path: str | Path) -> sqlite3.Connection:
    """Open ``db_path`` and ensure the ``dc_contract_versions`` table exists.

    DC-8 (SPEC-020) threads an explicit ``db_path`` rather than ``cwd`` so the
    versioning layer is testable against a ``tmp_path`` database. The table DDL
    is idempotent, so a raw path with no prior ``initialize`` still works.
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(_CONTRACT_VERSIONS_DDL)
    return conn


def insert_contract_version(version: ContractVersion, db_path: str | Path) -> None:
    """Persist one contract version snapshot (DC-8, SPEC-020).

    Raises:
        StateError: ``PK-DC-010`` if the snapshot cannot be written.
    """
    try:
        with _connect_versions(db_path) as conn:
            conn.execute(
                """
                INSERT INTO dc_contract_versions (
                    id, blueprint_name, contract_file, version,
                    version_major, version_minor, version_patch,
                    content_hash, contract_content, created_at, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version.id,
                    version.blueprint_name,
                    version.contract_file,
                    version.version,
                    version.version_major,
                    version.version_minor,
                    version.version_patch,
                    version.content_hash,
                    json.dumps(version.contract_content, sort_keys=True),
                    version.created_at,
                    version.created_by,
                ),
            )
    except sqlite3.Error as exc:
        raise StateError(
            "PK-DC-010",
            f"Cannot write contract version for {version.contract_file}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc


def get_latest_contract_version(
    blueprint_name: str, contract_file: str, db_path: str | Path
) -> dict | None:
    """Return the most recent stored version of a contract, or None (DC-8)."""
    try:
        with _connect_versions(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM dc_contract_versions
                WHERE blueprint_name = ? AND contract_file = ?
                ORDER BY created_at DESC, version_major DESC,
                         version_minor DESC, version_patch DESC
                LIMIT 1
                """,
                (blueprint_name, contract_file),
            ).fetchone()
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-001",
            f"Cannot read contract version for {contract_file}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc
    return dict(row) if row is not None else None


def get_contract_version_history(
    blueprint_name: str, contract_file: str, db_path: str | Path
) -> list[dict]:
    """Return all stored versions of a contract, newest first (DC-8)."""
    try:
        with _connect_versions(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM dc_contract_versions
                WHERE blueprint_name = ? AND contract_file = ?
                ORDER BY created_at DESC, version_major DESC,
                         version_minor DESC, version_patch DESC
                """,
                (blueprint_name, contract_file),
            ).fetchall()
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-001",
            f"Cannot read contract history for {contract_file}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc
    return [dict(row) for row in rows]


def get_contract_version_by_semver(
    blueprint_name: str, contract_file: str, version: str, db_path: str | Path
) -> dict | None:
    """Return a specific stored version by semver string, or None (DC-8)."""
    try:
        with _connect_versions(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM dc_contract_versions
                WHERE blueprint_name = ? AND contract_file = ? AND version = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (blueprint_name, contract_file, version),
            ).fetchone()
    except sqlite3.Error as exc:
        raise StateError(
            "PK-STATE-001",
            f"Cannot read contract version {version} for {contract_file}",
            {"path": str(db_path), "detail": str(exc)},
        ) from exc
    return dict(row) if row is not None else None


def ensure_gitignore_entry(cwd: Path | None = None) -> None:
    """Ensure ``.gitignore`` ignores the ``.pipelinekit/`` state directory.

    Creates ``.gitignore`` if absent; appends the entry if missing; does
    nothing if it is already present. SPEC-007 mandates this on ``init``; it
    lives here (not in the CLI) so the CLI performs no direct file I/O.

    Raises:
        StateError: ``PK-STATE-002`` if ``.gitignore`` cannot be written.
    """
    gitignore = _resolve(cwd) / ".gitignore"
    block = f"# PipelineKit state\n{GITIGNORE_ENTRY}\n"
    try:
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8")
            already = any(
                line.strip() == GITIGNORE_ENTRY for line in content.splitlines()
            )
            if already:
                return
            separator = "" if content == "" or content.endswith("\n") else "\n"
            gitignore.write_text(content + separator + "\n" + block, encoding="utf-8")
        else:
            gitignore.write_text(block, encoding="utf-8")
    except OSError as exc:
        raise StateError(
            "PK-STATE-002",
            "Cannot update .gitignore",
            {"path": str(gitignore), "detail": str(exc)},
        ) from exc
