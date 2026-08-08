"""RM-4 — atomic staging → production promotion for DuckDB destinations.

Transformations build into a staging schema. Production is updated only after
the whole build succeeds, inside a single transaction, so a reader either sees
the entire previous run or the entire new one — never a half-promoted mixture.
A failed build leaves production untouched.

Why this is not ``ALTER SCHEMA … RENAME``
-----------------------------------------
The obvious implementation — rename production aside, rename staging into its
place, drop the old — is not available: DuckDB (verified on 1.5.5) answers both
``ALTER SCHEMA … RENAME TO`` and ``ALTER TABLE … SET SCHEMA`` with "not yet
supported". Promotion therefore copies each staging table into production with
``CREATE OR REPLACE TABLE … AS SELECT``, wrapped in one transaction. DuckDB's
DDL is transactional (also verified), so the guarantee is preserved: on any
failure the transaction rolls back and production keeps its previous contents.

The cost relative to a rename is that promotion copies data rather than
repointing a catalog entry. For the local-first DuckDB destination this is an
acceptable trade; a warehouse adapter with real schema swaps would want its own
implementation, which is why this class is DuckDB-specific rather than a
premature abstraction.

No AI. Deterministic. Never promotes without an explicit caller.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from pipelinekit.core.errors import ReleaseError
from pipelinekit.state import db

# Lifecycle of a staging run.
BUILDING = "building"
TESTS_PASSING = "tests_passing"
PROMOTING = "promoting"
PROMOTED = "promoted"
FAILED = "failed"
ROLLED_BACK = "rolled_back"


@dataclass
class StagingRun:
    """One staging build and its promotion outcome."""

    id: str
    pipeline_name: str
    staging_schema: str
    production_schema: str
    status: str
    started_at: str
    promoted_at: str | None
    rows_staged: int | None
    error: str | None


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_run(row: dict) -> StagingRun:
    """Rebuild a ``StagingRun`` from a stored ``rm_staging_runs`` row."""
    return StagingRun(
        id=row["id"],
        pipeline_name=row["pipeline_name"],
        staging_schema=row["staging_schema"],
        production_schema=row["production_schema"],
        status=row["status"],
        started_at=row["started_at"],
        promoted_at=row["promoted_at"],
        rows_staged=row["rows_staged"],
        error=row["error"],
    )


def _quote(identifier: str) -> str:
    """Quote a SQL identifier, rejecting anything that cannot be a schema name.

    Schema names reach here from configuration, so they are not free-form user
    input — but they are still interpolated into DDL that cannot be
    parameterized. Validating the shape keeps that interpolation safe.

    Raises:
        ReleaseError: ``PK-RM-003`` if the identifier is not a plain name.
    """
    if not identifier or not identifier.replace("_", "").isalnum():
        raise ReleaseError(
            "PK-RM-003",
            f"Invalid schema name: {identifier!r}. Use letters, digits, and "
            "underscores only.",
            {"schema": identifier},
        )
    return f'"{identifier}"'


class StagingPromoter:
    """Manages atomic staging → production promotion for DuckDB destinations."""

    def __init__(self, duckdb_path: str, db_path: str) -> None:
        self.duckdb_path = duckdb_path
        self.db_path = db_path

    # -- connection ----------------------------------------------------------

    def _connect(self):  # type: ignore[no-untyped-def]
        """Open the destination DuckDB database.

        Raises:
            ReleaseError: ``PK-RM-004`` if DuckDB is unavailable or the file
                cannot be opened.
        """
        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover — duckdb is a dependency
            raise ReleaseError(
                "PK-RM-004",
                "DuckDB is not installed; staging promotion requires it.",
                {"duckdb_path": self.duckdb_path},
            ) from exc
        try:
            return duckdb.connect(self.duckdb_path)
        except Exception as exc:
            raise ReleaseError(
                "PK-RM-004",
                f"Cannot open DuckDB database at {self.duckdb_path}: {exc}",
                {"duckdb_path": self.duckdb_path},
            ) from exc

    @staticmethod
    def _tables_in(conn, schema: str) -> list[str]:  # type: ignore[no-untyped-def]
        """Return the table names present in a schema."""
        rows = conn.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = ? ORDER BY table_name
            """,
            (schema,),
        ).fetchall()
        return [row[0] for row in rows]

    # -- lifecycle -----------------------------------------------------------

    def create_staging_schema(
        self, staging_schema: str, pipeline_name: str, production_schema: str
    ) -> StagingRun:
        """Create an empty staging schema and record the run as ``building``.

        Any previous staging schema is dropped first: a staging schema left over
        from an earlier failed run must not contribute stale tables to this run's
        promotion.
        """
        quoted = _quote(staging_schema)
        conn = self._connect()
        try:
            conn.execute(f"DROP SCHEMA IF EXISTS {quoted} CASCADE")
            conn.execute(f"CREATE SCHEMA {quoted}")
        finally:
            conn.close()

        run = StagingRun(
            id=str(uuid.uuid4()),
            pipeline_name=pipeline_name,
            staging_schema=staging_schema,
            production_schema=production_schema,
            status=BUILDING,
            started_at=_utc_now(),
            promoted_at=None,
            rows_staged=None,
            error=None,
        )
        db.insert_staging_run(run, self.db_path)
        return run

    def promote_to_production(
        self, staging_schema: str, production_schema: str, run_id: str
    ) -> bool:
        """Atomically promote staging into production. Return True on success.

        Every staging table is copied into production inside one transaction. If
        anything fails the transaction rolls back and production is unchanged.

        An empty staging schema is refused rather than promoted: it means the
        build wrote somewhere else (or wrote nothing), and promoting it would
        silently leave production stale while reporting success.
        """
        staging_q = _quote(staging_schema)
        production_q = _quote(production_schema)

        conn = self._connect()
        try:
            tables = self._tables_in(conn, staging_schema)
            if not tables:
                message = (
                    f"Staging schema {staging_schema!r} is empty — nothing to "
                    "promote. Check that the transformation wrote to the staging "
                    "schema."
                )
                db.update_staging_run(run_id, FAILED, None, None, message, self.db_path)
                return False

            db.update_staging_run(run_id, PROMOTING, None, None, None, self.db_path)

            rows_staged = 0
            try:
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {production_q}")
                conn.execute("BEGIN")
                for table in tables:
                    table_q = _quote(table)
                    conn.execute(
                        f"CREATE OR REPLACE TABLE {production_q}.{table_q} AS "
                        f"SELECT * FROM {staging_q}.{table_q}"
                    )
                    count = conn.execute(
                        f"SELECT COUNT(*) FROM {staging_q}.{table_q}"
                    ).fetchone()
                    rows_staged += int(count[0]) if count else 0
                conn.execute("COMMIT")
            except Exception as exc:
                try:
                    conn.execute("ROLLBACK")
                except Exception:  # pragma: no cover — rollback of a dead txn
                    pass
                db.update_staging_run(
                    run_id, FAILED, None, None, str(exc), self.db_path
                )
                return False

            # Production is updated; the staging copy has served its purpose.
            conn.execute(f"DROP SCHEMA IF EXISTS {staging_q} CASCADE")
        finally:
            conn.close()

        db.update_staging_run(
            run_id, PROMOTED, _utc_now(), rows_staged, None, self.db_path
        )
        return True

    def rollback(
        self, staging_schema: str, production_schema: str, run_id: str
    ) -> bool:
        """Drop staging and leave production untouched. Return True on success.

        Called when the build fails. Production is never read or written here —
        that is the whole point of the staging design.
        """
        staging_q = _quote(staging_schema)
        conn = self._connect()
        try:
            conn.execute(f"DROP SCHEMA IF EXISTS {staging_q} CASCADE")
        except Exception as exc:
            db.update_staging_run(run_id, FAILED, None, None, str(exc), self.db_path)
            return False
        finally:
            conn.close()

        db.update_staging_run(run_id, ROLLED_BACK, None, None, None, self.db_path)
        return True

    def mark_tests_passing(self, run_id: str) -> bool:
        """Record that the build's tests passed and promotion may proceed."""
        return db.update_staging_run(
            run_id, TESTS_PASSING, None, None, None, self.db_path
        )

    def get_staging_status(self, pipeline_name: str | None = None) -> StagingRun | None:
        """Return the most recent staging run, or None if there is none."""
        row = db.get_latest_staging_run(pipeline_name, self.db_path)
        return _row_to_run(row) if row is not None else None
