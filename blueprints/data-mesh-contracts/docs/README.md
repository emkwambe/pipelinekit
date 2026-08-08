# data-mesh-contracts Blueprint

Reference implementation of the Data Mesh Frame → Detail → Core → Utility
pattern, using the contract object as the worked example.
Extract from PostgreSQL, load to a local DuckDB file. No cloud credentials
required.

**Status: proposed.** This blueprint has not been run end-to-end against a live
source, so it carries no quality baseline yet. Its structure is verified by
tests and by `check-best-practices`; its data is not.

## Use cases
- Reference architecture for column-level domain ownership
- Starting point for design-partner conversations about data mesh
- Local evaluation of the pattern without cloud accounts

## Prerequisites
- PostgreSQL source with `contracts`, `finance_contract_data`,
  `sales_contract_data`, and `product_contract_data` tables
- No destination credentials needed — DuckDB is a local file

## Environment variables
Required:
  POSTGRES_HOST      PostgreSQL host (default: localhost)
  POSTGRES_USER      PostgreSQL username
  POSTGRES_PASSWORD  PostgreSQL password
  POSTGRES_DB        Database name

Optional:
  DUCKDB_PATH        DuckDB file path (default: ./pipeline.duckdb)
  PK_DBT_SCHEMA      dbt output schema (set by RM-4 staging promotion)

## Layout

```
transform/models/
  staging/sources.yml     raw sources + freshness thresholds
  frame/                  one row per contract_id (Engineering)
  detail/finance/         Finance-owned columns
  detail/sales/           Sales-owned columns
  detail/product/         Product-owned columns
  core/                   wide analytics table
  utility/                team-specific downstream tables (see its README)
```

## Verifying

```bash
pipelinekit blueprint list
pipelinekit quality check-best-practices --blueprint data-mesh-contracts
pipelinekit governance owner column audit data-mesh-contracts
```

The audit reports every column as unowned until the domains are declared —
ownership lives in `state.db`, not in the blueprint. See
[DATA-MESH-PATTERN.md](DATA-MESH-PATTERN.md) for the declaration commands and
the intended owner of each column.

## Reading order

1. [DATA-MESH-PATTERN.md](DATA-MESH-PATTERN.md) — the pattern and why it works
2. `transform/models/frame/frame_contracts.sql` — the shared backbone
3. `transform/models/detail/*/` — one domain at a time
4. `transform/models/core/core_contracts.sql` — how they join
5. `transform/models/utility/README.md` — how to extend
