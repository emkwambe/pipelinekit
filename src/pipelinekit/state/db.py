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

import sqlite3
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
