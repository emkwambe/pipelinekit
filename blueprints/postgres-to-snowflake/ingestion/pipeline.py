"""dlt ingestion pipeline for Blueprint #001 (Postgres -> Snowflake).

This is a blueprint asset, not part of the PipelineKit package. It is executed
by the dlt ingestion adapter at run time. Connection strings are supplied by the
operator (BYOK) — never hardcoded here.
"""

import dlt
from dlt.sources.sql_database import sql_database


def postgres_to_snowflake_pipeline(
    pg_conn_str: str,
    tables: list[str],
    dataset_name: str = "pipelinekit_raw",
):
    """Build the dlt pipeline and source for Postgres -> Snowflake ingestion.

    Args:
        pg_conn_str: PostgreSQL connection string (from the environment).
        tables: Tables to replicate (e.g. ``["orders"]``).
        dataset_name: Destination dataset name in Snowflake.

    Returns:
        A ``(pipeline, source)`` tuple ready to run.
    """
    source = sql_database(pg_conn_str).with_resources(*tables)
    pipeline = dlt.pipeline(
        pipeline_name="postgres_to_snowflake",
        destination="snowflake",
        dataset_name=dataset_name,
    )
    return pipeline, source
