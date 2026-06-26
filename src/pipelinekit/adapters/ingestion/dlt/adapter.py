"""dlt-based ingestion adapter.

Wraps dlt pipeline execution behind the stable :class:`BaseAdapter` interface.
**All dlt imports stay inside this file** (lazily, inside methods) — never in
runtime, cli, config, state, or core (SPEC-009, Smell 2).

Credentials come from ``PipelineConfig`` (ADR-017): the adapter translates
``SourceConfig`` fields into a Postgres connection string and dlt destination
credentials. ``pipelinekit.yaml`` is the single source of credential truth —
the adapter never reads ``.dlt/secrets.toml`` or dlt's own env convention.

dlt exceptions never propagate raw: connectivity failures map to
``PK-ADAPTER-001`` and execution failures to ``PK-ADAPTER-002``.
"""

from __future__ import annotations

import socket
import time
from typing import Any

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.config.schema import IngestionSection, SourceConfig
from pipelinekit.core.errors import PipelineKitError
from pipelinekit.runtime.result import PipelineStatus, StepResult

_STEP = "ingestion"
_DEFAULT_PORTS = {"postgres": 5432}


class DltIngestionAdapter(BaseAdapter):
    """dlt ingestion adapter. dlt is the standard ingestion framework (ADR-001)."""

    def __init__(self, config: IngestionSection) -> None:
        self.config = config
        self._initialized = False
        self._pipeline: Any = None

    # -- naming (human-readable, version-controllable per ADR-009) -----------

    def _pipeline_name(self, project: str = "pipeline") -> str:
        return f"pipelinekit_{project}"

    def _dataset_name(self, project: str = "pipeline") -> str:
        return f"pipelinekit_{project}_raw"

    # -- BaseAdapter ---------------------------------------------------------

    def initialize(self) -> None:
        """Build the dlt pipeline object from config.

        The runtime does not require ``initialize`` before ``validate`` or
        ``execute`` (the executor calls those directly), but building the
        pipeline here keeps the adapter contract complete and lets ``execute``
        reuse the object. dlt source/destination credentials are resolved
        lazily so a dry-run never needs live destination credentials.
        """
        import dlt  # type: ignore  # provider lib: treated as Any, not followed

        self._pipeline = dlt.pipeline(
            pipeline_name=self._pipeline_name(),
            destination=self._destination(),
            dataset_name=self._dataset_name(),
        )
        self._initialized = True

    def _check_connectivity(self) -> None:
        """Probe TCP reachability of the source without loading data.

        A lightweight reachability check (no credentials, no data) suitable for
        ``validate``/``--dry-run``. Raises OSError if the source is unreachable.
        """
        source = self.config.source
        host = source.host or "localhost"
        port = source.port or _DEFAULT_PORTS.get(source.type, 0)
        with socket.create_connection((host, port), timeout=3.0):
            return

    def validate(self) -> StepResult:
        """Validate source connectivity without loading data."""
        start = time.perf_counter()
        try:
            self._check_connectivity()
        except Exception as exc:
            return StepResult(
                _STEP,
                PipelineStatus.INVALID,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-001",
                error_msg=f"Source unreachable: {exc}",
            )
        return StepResult(_STEP, PipelineStatus.VALID, time.perf_counter() - start)

    def execute(self) -> StepResult:
        """Run the dlt pipeline and report rows processed.

        Builds a real ``sql_database`` source when the source declares tables;
        otherwise runs an empty source (nothing to ingest). All dlt failures —
        including a missing ``sql_database`` extra — map to ``PK-ADAPTER-002``.
        """
        start = time.perf_counter()
        try:
            import dlt  # type: ignore  # provider lib: treated as Any, not followed

            pipeline = self._pipeline
            if pipeline is None:
                pipeline = dlt.pipeline(
                    pipeline_name=self._pipeline_name(),
                    destination=self._destination(),
                    dataset_name=self._dataset_name(),
                )
            # First local verification loads all rows, not just incremental
            # updates — replace ensures a clean, deterministic full load.
            pipeline.run(self._build_source(), write_disposition="replace")
            rows = self._rows_loaded(pipeline)
        except PipelineKitError:
            raise
        except Exception as exc:
            return StepResult(
                _STEP,
                PipelineStatus.FAILED,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-002",
                error_msg=f"dlt ingestion failed: {exc}",
            )
        return StepResult(
            _STEP,
            PipelineStatus.SUCCESS,
            time.perf_counter() - start,
            rows_processed=rows,
        )

    def status(self) -> dict:
        """Return adapter status as a structured dict."""
        return {
            "adapter": "dlt",
            "step": _STEP,
            "initialized": self._initialized,
            "source": self.config.source.type,
            "destination": self.config.destination.type,
        }

    # -- credential + source wiring (ADR-017) --------------------------------

    def _build_postgres_conn_str(self, source: SourceConfig) -> str:
        """Build a ``postgresql://`` connection string from ``SourceConfig``."""
        return (
            f"postgresql://{source.user}:{source.password}"
            f"@{source.host}:{source.port or 5432}/{source.database}"
        )

    def _build_snowflake_credentials(self, dest: SourceConfig) -> dict:
        """Build a Snowflake credentials dict for dlt from ``SourceConfig``."""
        return {
            "account": dest.account,
            "user": dest.user,
            "password": dest.password,
            "database": dest.database,
            "warehouse": dest.warehouse,
            "schema": dest.schema_name or "raw",
        }

    def _destination(self) -> object:
        """Resolve the dlt destination.

        Snowflake is built with explicit credentials from config (ADR-017);
        other destinations (duckdb, bigquery) are passed by type name and let
        dlt resolve them. Snowflake credentials are constructed lazily here so a
        non-Snowflake destination never imports Snowflake-specific dlt code.
        """
        dest = self.config.destination
        if dest.type == "snowflake":
            import dlt  # type: ignore  # provider lib: treated as Any

            return dlt.destinations.snowflake(
                credentials=self._build_snowflake_credentials(dest)
            )
        if dest.type == "duckdb" and dest.path:
            import dlt  # type: ignore  # provider lib: treated as Any

            # Honor the configured DuckDB file so dlt and dbt share one database
            # (ADR-017). Without a path, dlt uses its default <pipeline>.duckdb.
            return dlt.destinations.duckdb(dest.path)
        return dest.type

    def _build_source(self) -> object:
        """Build the dlt source from config.

        When the Postgres source declares tables, build a real ``sql_database``
        source (requires the dlt ``sql_database`` extra / SQLAlchemy at runtime).
        With no tables there is nothing to ingest, so return an empty source —
        this keeps validate/dry-run and unit tests free of a live database.
        """
        source = self.config.source
        tables = source.tables or []
        if source.type == "postgres" and tables:
            from dlt.sources.sql_database import (  # type: ignore  # provider lib
                sql_database,
            )

            conn_str = self._build_postgres_conn_str(source)
            return sql_database(conn_str).with_resources(*tables)
        return []

    @staticmethod
    def _rows_loaded(pipeline: Any) -> int:
        """Sum real data-table row counts from dlt's last normalize step.

        dlt ``load_info`` reports completed *jobs*, not rows; the actual
        per-table row counts live on the pipeline trace
        (``last_trace.last_normalize_info.row_counts``). dlt bookkeeping tables
        (``_dlt_*``) are excluded. Missing/partial trace data counts as zero —
        never raises.
        """
        try:
            normalize_info = pipeline.last_trace.last_normalize_info
            counts = dict(normalize_info.row_counts) if normalize_info else {}
        except Exception:
            return 0
        return sum(
            int(n) for table, n in counts.items() if not table.startswith("_dlt")
        )
