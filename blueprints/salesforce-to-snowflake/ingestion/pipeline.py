"""dlt ingestion pipeline for Blueprint #002 (Salesforce -> Snowflake).

This is a blueprint asset, not part of the PipelineKit package. It is executed
by the dlt ingestion adapter at run time. Salesforce credentials are supplied by
the operator (BYOK, ADR-005) — never hardcoded here.

Requires the ``dlt[salesforce]`` extra at run time.
"""

import dlt
from dlt.sources.salesforce import salesforce_source


def salesforce_to_snowflake_pipeline(
    username: str,
    password: str,
    security_token: str,
    tables: list[str],
    dataset_name: str = "pipelinekit_raw",
):
    """Build the dlt pipeline and source for Salesforce -> Snowflake ingestion.

    Args:
        username: Salesforce username (from the environment).
        password: Salesforce password (from the environment).
        security_token: Salesforce security token (from the environment).
        tables: Salesforce objects to replicate (e.g. ``["accounts",
            "opportunities", "contacts"]``).
        dataset_name: Destination dataset name in Snowflake.

    Returns:
        A ``(pipeline, source)`` tuple ready to run.
    """
    source = salesforce_source(
        username=username,
        password=password,
        security_token=security_token,
    ).with_resources(*tables)
    pipeline = dlt.pipeline(
        pipeline_name="salesforce_to_snowflake",
        destination="snowflake",
        dataset_name=dataset_name,
    )
    return pipeline, source
