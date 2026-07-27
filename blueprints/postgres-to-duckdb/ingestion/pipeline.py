"""Ingestion for the postgres-to-duckdb reference blueprint.

Extracts the configured PostgreSQL tables and loads them into a local DuckDB
file — no cloud account or credentials for the destination are required. This is
a thin dlt pipeline definition; PipelineKit's dlt adapter runs it via
``pipelinekit run``. Kept intentionally minimal for local development and
RealityDB-generated synthetic data.
"""

from __future__ import annotations

import os

import dlt  # type: ignore[import-untyped]
from dlt.sources.sql_database import sql_database  # type: ignore[import-untyped]

TABLES = ("orders", "customers")


def run() -> None:
    """Load the configured PostgreSQL tables into a local DuckDB file."""
    duckdb_path = os.environ.get("DUCKDB_PATH", "./pipeline.duckdb")
    pipeline = dlt.pipeline(
        pipeline_name="postgres_to_duckdb",
        destination=dlt.destinations.duckdb(duckdb_path),
        dataset_name="postgres_raw",
    )
    source = sql_database().with_resources(*TABLES)
    load_info = pipeline.run(source, write_disposition="replace")
    print(load_info)


if __name__ == "__main__":
    run()
