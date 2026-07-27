# postgres-to-duckdb Blueprint

Extract data from PostgreSQL, load to a local DuckDB file.
No cloud credentials required.

## Use cases
- Local development and testing without cloud accounts
- PipelineKit evaluation with synthetic data (RealityDB)
- Rapid prototyping of data pipelines

## Prerequisites
- PostgreSQL source database (or use RealityDB to generate one)
- No destination credentials needed — DuckDB is a local file

## Environment variables
Required:
  POSTGRES_HOST      PostgreSQL host (default: localhost)
  POSTGRES_USER      PostgreSQL username
  POSTGRES_PASSWORD  PostgreSQL password
  POSTGRES_DB        Database name

Optional:
  DUCKDB_PATH        DuckDB file path (default: ./pipeline.duckdb)

## Running with RealityDB synthetic data
1. Generate synthetic data: realitydb generate --template ecommerce
2. Load into local Postgres: realitydb load --target postgres
3. Run this blueprint: pipelinekit run --blueprint postgres-to-duckdb
4. Check quality: pipelinekit quality scorecard
5. Full health: pipelinekit health --strict

## Best practices implemented
This blueprint is the reference implementation of PipelineKit best
practices. Every model has:
- Primary key (unique + not_null) tests
- Source freshness declarations
- Full column descriptions
- 100% column test coverage
- accepted_values on categorical columns
- dbt naming convention (stg_{source}__{entity})
- PipelineKit contract for every model
