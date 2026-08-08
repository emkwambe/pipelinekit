"""Ingestion for the data-mesh-contracts reference blueprint.

Loads the contract backbone plus one raw table per domain (finance, sales,
product) into a local DuckDB file — no cloud account or destination credentials
required. Each domain's raw table becomes exactly one Detail model downstream,
which is what keeps column ownership unambiguous.

This is a thin dlt pipeline definition; PipelineKit's dlt adapter runs it via
``pipelinekit run``.
"""

from __future__ import annotations

import os

import dlt  # type: ignore[import-untyped]
from dlt.sources.sql_database import sql_database  # type: ignore[import-untyped]

TABLES = (
    "contracts",
    "finance_contract_data",
    "sales_contract_data",
    "product_contract_data",
)


def run() -> None:
    """Load the configured PostgreSQL tables into a local DuckDB file."""
    duckdb_path = os.environ.get("DUCKDB_PATH", "./pipeline.duckdb")
    pipeline = dlt.pipeline(
        pipeline_name="data_mesh_contracts",
        destination=dlt.destinations.duckdb(duckdb_path),
        dataset_name="pipelinekit_pipeline_raw",
    )
    source = sql_database().with_resources(*TABLES)
    load_info = pipeline.run(source, write_disposition="replace")
    print(load_info)


if __name__ == "__main__":
    run()
