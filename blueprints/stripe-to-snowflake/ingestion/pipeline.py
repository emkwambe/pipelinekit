"""Stripe to Snowflake ingestion pipeline using dlt.

This pipeline loads Stripe charges and customers into Snowflake
using incremental loading based on the 'created' timestamp.

Environment variables required:
    STRIPE_API_KEY            - Stripe secret API key
    SNOWFLAKE_ACCOUNT         - Snowflake account identifier
    SNOWFLAKE_USERNAME        - Snowflake username
    SNOWFLAKE_PASSWORD        - Snowflake password
    SNOWFLAKE_ROLE            - Snowflake role
    SNOWFLAKE_WAREHOUSE       - Snowflake warehouse
    SNOWFLAKE_DATABASE        - Snowflake destination database
    SNOWFLAKE_SCHEMA          - Snowflake destination schema
    PIPELINE_DATASET_NAME     - dlt dataset name (default: stripe_raw)
"""

import os

import dlt

# NOTE: Verify the exact import path against the dlt Stripe verified source.
# It may be: from stripe_analytics import stripe_source
# or: from dlt.sources.stripe import stripe_source
# Adjust the import below before deploying.
try:
    from stripe_analytics import stripe_source
except ImportError as e:
    raise ImportError(
        "Could not import Stripe dlt source. "
        "Install with: pip install dlt[stripe] or pip install dlt-stripe-analytics. "
        "Verify the correct package name in the dlt registry."
    ) from e


def build_pipeline() -> dlt.Pipeline:
    """Construct and return the configured dlt pipeline."""
    return dlt.pipeline(
        pipeline_name="stripe_to_snowflake",
        destination=dlt.destinations.snowflake(
            credentials={
                "account": os.environ["SNOWFLAKE_ACCOUNT"],
                "username": os.environ["SNOWFLAKE_USERNAME"],
                "password": os.environ["SNOWFLAKE_PASSWORD"],
                "role": os.environ["SNOWFLAKE_ROLE"],
                "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
                "database": os.environ["SNOWFLAKE_DATABASE"],
                "schema": os.environ["SNOWFLAKE_SCHEMA"],
            }
        ),
        dataset_name=os.environ.get("PIPELINE_DATASET_NAME", "stripe_raw"),
        progress="log",
    )


def build_source():
    """Construct and return the Stripe dlt source scoped to required tables."""
    return stripe_source(
        api_key=os.environ["STRIPE_API_KEY"],
        # Limit to only the tables required by this blueprint.
        # Remove or extend this list if additional Stripe tables are needed.
        endpoints=["charges", "customers"],
    )


def run() -> None:
    """Execute the Stripe to Snowflake pipeline."""
    pipeline = build_pipeline()
    source = build_source()

    load_info = pipeline.run(
        source,
        write_disposition="merge",
        primary_key={"charges": "id", "customers": "id"},
    )

    print(load_info)

    # Surface any load errors immediately for alerting.
    if load_info.has_failed_jobs:
        failed = [str(j) for j in load_info.failed_jobs]
        raise RuntimeError(
            f"Stripe ingestion pipeline completed with failed jobs: {failed}"
        )


if __name__ == "__main__":
    run()
