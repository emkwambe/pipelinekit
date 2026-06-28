# Troubleshooting

The ten errors you are most likely to hit right after installing PipelineKit, with the exact fix for each. Every failure carries a `PK-[AREA]-[NUMBER]` code — the full registry is in [`docs/reference/Error-Codes.md`](../reference/Error-Codes.md). For broader operational guidance, see the [Operations Runbook](OPERATIONS-RUNBOOK.md).

---

## Error 1 — PK-AI-001: ANTHROPIC_API_KEY not set

**Symptom**

```
[PK-AI-001] Set ANTHROPIC_API_KEY to use the Anthropic provider.
```

**Cause**

`pipelinekit diagnose` needs an API key for the configured AI provider, and the environment variable is not set.

**Fix**

Set the key for your provider, then re-run the command.

```powershell
# PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

```bash
# bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Error 2 — PK-REGISTRY-001: HTTP 403 Forbidden

**Symptom**

```
[PK-REGISTRY-001] Registry unreachable: https://registry.pipelinekit.dev/... (HTTP Error 403: Forbidden)
```

**Cause**

Old PipelineKit versions sent no `User-Agent` header, so Cloudflare in front of the registry rejected the request with HTTP 403.

**Fix**

Upgrade to v0.1.0 or later — the client now sends an explicit `User-Agent` and the fix is already shipped.

```powershell
pip install --upgrade pipelinekit
```

---

## Error 3 — PK-GEN-001: AI proposal not valid JSON

**Symptom**

```
[PK-GEN-001] AI proposal response was not valid JSON
```

**Cause**

The AI provider response was truncated mid-JSON because the old `max_tokens` ceiling was too low for a full blueprint proposal.

**Fix**

Upgrade to v0.1.0 or later — the `max_tokens` ceiling was raised to 32000 and the fix is already shipped.

```powershell
pip install --upgrade pipelinekit
```

---

## Error 4 — dbt profile target `local` not found

**Symptom**

```
Runtime Error
  Could not find profile named 'pipelinekit'
  (or the profile has no target named 'local')
```

**Cause**

The blueprint's `profiles.yml` is missing a `local` DuckDB target for offline verification.

**Fix**

Add a `local` target to `profiles.yml`:

```yaml
pipelinekit:
  outputs:
    local:
      type: duckdb
      path: "{{ env_var('DUCKDB_PATH', 'pipelinekit_pipeline.duckdb') }}"
      schema: "{{ env_var('DBT_SOURCE_SCHEMA', 'pipelinekit_pipeline_raw') }}"
  target: local
```

---

## Error 5 — `to_timestamp_ntz` does not exist on DuckDB

**Symptom**

```
Catalog Error: Scalar Function with name to_timestamp_ntz does not exist!
```

**Cause**

`to_timestamp_ntz` is Snowflake-only; DuckDB (used for offline verification) does not support it.

**Fix**

Replace the Snowflake-specific call with the cross-database macro:

```sql
-- before
to_timestamp_ntz(event_time)

-- after
{{ to_timestamp('event_time') }}
```

---

## Error 6 — `CREATE OR REPLACE TABLE IF NOT EXISTS` syntax error

**Symptom**

```
Parser Error: syntax error at or near "IF"
```

**Cause**

`CREATE OR REPLACE` and `IF NOT EXISTS` cannot be combined — neither DuckDB nor Snowflake accepts both clauses on the same statement.

**Fix**

Drop `IF NOT EXISTS` and keep `CREATE OR REPLACE TABLE`:

```sql
-- before
CREATE OR REPLACE TABLE IF NOT EXISTS staging_orders ( ... )

-- after
CREATE OR REPLACE TABLE staging_orders ( ... )
```

---

## Error 7 — `_dlt_load_id` column not found

**Symptom**

```
Catalog Error: Referenced column "_dlt_load_id" not found in FROM clause!
```

**Cause**

The `dlt` metadata columns (`_dlt_load_id`, `_dlt_id`) exist on raw tables but must not be selected in staging or core models.

**Fix**

Remove every `_dlt_*` column from the `SELECT` in your staging and core SQL models (and from any `SELECT *` expansion).

```sql
select
    order_id,
    customer_id,
    order_total
    -- _dlt_load_id,   <- remove
    -- _dlt_id         <- remove
from {{ source('raw', 'orders') }}
```

---

## Error 8 — Docker not running, health check fails

**Symptom**

```
pipelinekit health --strict
  deps: FAIL — connection refused
```

(or the verification script fails to start the Postgres container).

**Cause**

Docker Desktop is not running, so the Postgres container the check depends on cannot start.

**Fix**

Start Docker Desktop, wait ~30 seconds for the engine to come up, then re-run:

```powershell
.\scripts\verify-blueprint-001.ps1 -Local
```

---

## Error 9 — BOM encoding error on Windows

**Symptom**

```
SyntaxError: invalid character '﻿'
```

(or a YAML parser failing on the first character of the file).

**Cause**

`Set-Content` on PowerShell writes UTF-8 **with** a byte-order mark by default, and Python and YAML parsers reject the leading BOM.

**Fix**

Always write files as BOM-free UTF-8:

```powershell
[System.IO.File]::WriteAllText(
    "C:\path\to\file.yaml",
    $content,
    [System.Text.UTF8Encoding]::new($false)
)
```

---

## Error 10 — PK-REGISTRY-003: blueprint already installed

**Symptom**

```
[PK-REGISTRY-003] Blueprint already installed: postgres-to-snowflake. Use --force to overwrite.
```

**Cause**

The blueprint directory already exists locally from a previous install.

**Fix**

Re-run the install with `--force` to overwrite the existing copy:

```powershell
pipelinekit blueprint install postgres-to-snowflake --force
```
