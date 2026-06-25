# SPEC-006-Blueprint-Engine.md

**Status:** Implemented  
**Owner:** blueprint-engineer  
**Phase:** 3 — Trust Layer  
**Date:** June 25, 2026  
**ADRs:** ADR-003 (CLI-First), ADR-008 (Deterministic), ADR-009 (Human-Readable), ADR-011 (Trust as primary metric)  
**Schemas:** schemas/blueprint.schema.json  
**Depends on:** SPEC-003 (Runtime), SPEC-004 (Contracts), SPEC-009 (Adapters)

---

## Purpose

Define the blueprint engine — the system that registers, installs, validates, and executes complete analytics blueprints.

A blueprint is not a connector.
A blueprint is a complete analytics system.
It is the primary product deliverable and the long-term moat.

Phase 3 ships Blueprint #001: Postgres → Snowflake.
The blueprint engine is the infrastructure that makes every future blueprint installable in under 60 minutes.

---

## Governing Rules

- Every blueprint is validated against `schemas/blueprint.schema.json`
- Blueprints are human-readable — YAML, SQL, Markdown only
- Blueprint files are version-controlled by the user
- The engine never modifies a blueprint after installation without explicit approval
- Blueprint execution delegates to existing runtime and adapter layers
- Blueprint #001 is the first and only blueprint in Phase 3

---

## Blueprint File Structure

Every blueprint lives under `blueprints/<blueprint-id>/`:

```
blueprints/
└── postgres-to-snowflake/
    ├── blueprint.json          Validated against schemas/blueprint.schema.json
    ├── ingestion/
    │   └── pipeline.py         dlt pipeline definition
    ├── transform/
    │   ├── dbt_project.yml
    │   ├── profiles.yml
    │   └── models/
    │       ├── staging/
    │       │   └── stg_orders.sql
    │       └── core/
    │           └── fct_orders.sql
    ├── contracts/
    │   └── orders.yaml         ContractDefinition YAML
    ├── quality/
    │   └── checks.yaml         Soda checks
    ├── alerts/
    │   └── config.yaml         Notification config
    └── docs/
        ├── README.md
        └── runbook.md
```

---

## blueprint.json — Canonical Metadata

Validated against `schemas/blueprint.schema.json`.
Required fields: `name`, `version`, `source`, `destination`, `contracts`

```json
{
  "name": "postgres-to-snowflake",
  "version": "1.0.0",
  "description": "Postgres → Snowflake trusted analytics pipeline",
  "source": {
    "type": "postgres",
    "dlt_source": "sql_database"
  },
  "destination": {
    "type": "snowflake",
    "dlt_destination": "snowflake"
  },
  "contracts": ["contracts/orders.yaml"],
  "tags": ["postgres", "snowflake", "product-analytics"],
  "kpis": ["Daily Orders", "Revenue", "Customers", "Order Value", "Retention"],
  "deploy_time_minutes": 60,
  "time_to_trusted_data_hours": 24
}
```

---

## Blueprint Registry

The registry is a simple directory scan — no remote registry in Phase 3.

```python
# src/pipelinekit/blueprints/registry.py

from pathlib import Path
from pipelinekit.blueprints.models import BlueprintMetadata

BLUEPRINTS_DIR = Path("blueprints")

class BlueprintRegistry:
    """Local registry — scans the blueprints/ directory.

    Phase 3: local only.
    Phase 4+: remote registry with versioned catalog.
    """

    def __init__(self, blueprints_dir: Path = BLUEPRINTS_DIR):
        self.blueprints_dir = blueprints_dir

    def list(self) -> list[BlueprintMetadata]:
        """Return all installed blueprints."""
        ...

    def get(self, name: str) -> BlueprintMetadata | None:
        """Return metadata for a named blueprint, or None if not found."""
        ...

    def exists(self, name: str) -> bool:
        """Return True if blueprint is installed."""
        ...
```

---

## Blueprint Validator

```python
# src/pipelinekit/blueprints/validator.py

import json
from pathlib import Path
from jsonschema import validate, ValidationError
from pipelinekit.core.errors import BlueprintError

SCHEMA_PATH = Path("schemas/blueprint.schema.json")

class BlueprintValidator:
    """Validates blueprint.json against schemas/blueprint.schema.json."""

    def validate(self, blueprint_path: Path) -> None:
        """
        Raises BlueprintError(PK-BLUEPRINT-001) if invalid.
        Raises BlueprintError(PK-BLUEPRINT-002) if blueprint.json not found.
        """
        ...
```

---

## Blueprint Models

```python
# src/pipelinekit/blueprints/models.py

from pydantic import BaseModel
from typing import Optional

class BlueprintSource(BaseModel):
    type: str
    dlt_source: str

class BlueprintDestination(BaseModel):
    type: str
    dlt_destination: str

class BlueprintMetadata(BaseModel):
    name: str
    version: str
    description: str = ""
    source: BlueprintSource
    destination: BlueprintDestination
    contracts: list[str] = []
    tags: list[str] = []
    kpis: list[str] = []
    deploy_time_minutes: int = 60
    time_to_trusted_data_hours: int = 24
```

---

## CLI Commands — Phase 3

```
pipelinekit blueprint list       List installed blueprints
pipelinekit blueprint validate   Validate blueprint structure
pipelinekit blueprint info       Show blueprint details
```

### pipelinekit blueprint list

```
Installed blueprints:

  Name                    Version   Source      Destination
  ─────────────────────   ───────   ──────      ───────────
  postgres-to-snowflake   1.0.0     postgres    snowflake
```

### pipelinekit blueprint validate

```
✓ Blueprint postgres-to-snowflake is valid
  schema:    valid
  contracts: 1 found
  dbt:       project detected
  quality:   checks found
```

### pipelinekit blueprint info

```
postgres-to-snowflake v1.0.0
─────────────────────────────
Description:  Postgres → Snowflake trusted analytics pipeline
Source:       postgres
Destination:  snowflake
Contracts:    1
KPIs:         Daily Orders, Revenue, Customers, Order Value, Retention
Deploy time:  < 60 minutes
Time-to-Trusted-Data: < 24 hours
```

---

## Blueprint #001 — Postgres → Snowflake

This is the first production blueprint. It ships with Phase 3.

### Included assets:

**ingestion/pipeline.py** — dlt pipeline using `sql_database` source
```python
import dlt
from dlt.sources.sql_database import sql_database

def postgres_to_snowflake_pipeline(
    pg_conn_str: str,
    tables: list[str],
    dataset_name: str = "pipelinekit_raw"
):
    source = sql_database(pg_conn_str).with_resources(*tables)
    pipeline = dlt.pipeline(
        pipeline_name="postgres_to_snowflake",
        destination="snowflake",
        dataset_name=dataset_name,
    )
    return pipeline, source
```

**transform/models/staging/stg_orders.sql**
```sql
-- stg_orders: standardize raw orders from Postgres
select
    order_id,
    customer_id,
    cast(amount as numeric(18,2)) as amount,
    status,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at
from {{ source('pipelinekit_raw', 'orders') }}
```

**transform/models/core/fct_orders.sql**
```sql
-- fct_orders: trusted analytics-ready orders fact table
select
    order_id,
    customer_id,
    amount,
    status,
    created_at,
    updated_at,
    date_trunc('day', created_at) as order_date
from {{ ref('stg_orders') }}
where status != 'cancelled'
```

**contracts/orders.yaml**
```yaml
version: 1
table: orders
description: "Order transaction records"
freshness:
  max_age_hours: 12
  column: updated_at
required_columns:
  - order_id
  - customer_id
  - amount
  - status
uniqueness:
  - order_id
not_null:
  - order_id
  - customer_id
  - amount
row_count:
  min: 1
```

**docs/runbook.md** — operational runbook covering:
- Prerequisites (Postgres access, Snowflake account, dbt profiles)
- Installation steps
- First run walkthrough
- Troubleshooting guide
- KPI definitions

---

## Error Codes — Phase 3 Blueprint

| Code | Meaning |
|---|---|
| `PK-BLUEPRINT-001` | blueprint.json fails schema validation |
| `PK-BLUEPRINT-002` | blueprint.json not found |
| `PK-BLUEPRINT-003` | Blueprint directory not found |
| `PK-BLUEPRINT-004` | Blueprint dbt project invalid |

---

## File Structure

```
src/pipelinekit/
└── blueprints/
    ├── __init__.py
    ├── models.py       BlueprintMetadata, BlueprintSource, BlueprintDestination
    ├── registry.py     BlueprintRegistry
    └── validator.py    BlueprintValidator

blueprints/
└── postgres-to-snowflake/
    ├── blueprint.json
    ├── ingestion/pipeline.py
    ├── transform/
    ├── contracts/orders.yaml
    ├── quality/checks.yaml
    ├── alerts/config.yaml
    └── docs/

src/pipelinekit/cli/
└── blueprint.py        blueprint list, validate, info commands
```

---

## core/errors.py Addition

```python
class BlueprintError(PipelineKitError):
    """Raised when a blueprint is missing, invalid, or cannot be executed."""
```

---

## Constraints

- Blueprint files are YAML, SQL, JSON, Markdown only — no binary files
- Blueprint engine never calls AI — Phase 4
- Blueprint engine delegates execution to `PipelineRunner` — no direct adapter calls
- Blueprint validator uses `jsonschema` against `schemas/blueprint.schema.json`
- `blueprints/` directory is user-owned — never auto-modified by PipelineKit
- Phase 3 ships exactly one blueprint: `postgres-to-snowflake`

---

## AI Guardrails

- No AI calls in Phase 3 blueprint engine
- `blueprint generate` is a Phase 4 AI command
- Blueprint files are human-authored and human-readable — this is the moat

---

## Acceptance Criteria

```
✓ blueprints/postgres-to-snowflake/blueprint.json validates against schema
✓ pipelinekit blueprint list shows installed blueprints
✓ pipelinekit blueprint validate exits 0 on valid blueprint
✓ pipelinekit blueprint validate exits 1 with PK-BLUEPRINT-001 on invalid
✓ pipelinekit blueprint info shows blueprint details
✓ BlueprintValidator raises BlueprintError on schema violation
✓ BlueprintRegistry.list() returns [] when blueprints/ is empty
✓ poetry run pytest tests/blueprints/ → all tests pass
✓ coverage >= 80% on src/pipelinekit/blueprints/
```

---

## Out of Scope

- Remote blueprint registry — Phase 4
- `pipelinekit blueprint install <name>` from remote — Phase 4
- AI-generated blueprints — Phase 4
- Blueprint versioning and upgrades — Phase 4
- Blueprint marketplace — Phase 4+
