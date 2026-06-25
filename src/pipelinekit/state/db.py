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

from pipelinekit.core.errors import StateError

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
