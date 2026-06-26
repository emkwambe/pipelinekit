# Runbook — Blueprint #001 (Postgres → Snowflake)

Operational guide for running, monitoring, and troubleshooting this pipeline.
This runbook is intentionally honest: it documents what can fail and exactly how
to recover.

---

## 1. Architecture & data flow

```
Postgres ──dlt──▶ Snowflake (raw) ──dbt staging──▶ stg_orders
                                   ──dbt core─────▶ fct_orders
                                                       │
                                              contracts (orders.yaml)
                                                       │
                                              quality checks (Soda)
                                                       │
                                              alerts (Resend, on failure)
```

Every stage is recorded in `.pipelinekit/state.db`. Failures never go silent:
they are written to state **and** dispatched as alerts.

---

## 2. Routine operation

| Action | Command |
|---|---|
| Validate config | `pipelinekit validate` |
| Validate contracts | `pipelinekit validate --contracts` |
| Validate blueprint structure | `pipelinekit blueprint validate` |
| Dry run (no data movement) | `pipelinekit run --dry-run` |
| Full run | `pipelinekit run` |
| Run history | `pipelinekit status` |

Recommended cadence: run on a schedule that keeps `updated_at` freshness under
the 12-hour contract SLA (e.g. every 6 hours).

---

## 3. Troubleshooting

### `[PK-ADAPTER-001]` — Source unreachable
**Cause:** PipelineKit cannot reach Postgres.
**Check:** `POSTGRES_CONN_STR`, host/port reachability, firewall, credentials.
**Recover:** Fix connectivity, re-run `pipelinekit run --dry-run` to confirm.

### `[PK-ADAPTER-002]` — Ingestion or transformation failed
**Cause:** dlt load error or a non-zero `dbt build`.
**Check:** Snowflake credentials/role/warehouse; dbt logs in `transform/target/`.
**Recover:** Resolve the failing model or load, then re-run.

### `[PK-CONTRACT-002]` — Freshness violation
**Cause:** Newest `updated_at` is older than 12 hours.
**Check:** Is the source pipeline running often enough? Is upstream data stale?
**Recover:** Increase run frequency or investigate the upstream system.

### `[PK-CONTRACT-001 / 003 / 004]` — Structural violations
**Cause:** Missing required column, duplicate `order_id`, or unexpected nulls.
**Check:** Upstream schema changes; the `stg_orders` casting logic.
**Recover:** Reconcile the source schema with `contracts/orders.yaml`.

### `[PK-NOTIFY-004]` — Alerts not delivered
**Cause:** `RESEND_API_KEY` missing or invalid.
**Check:** Environment variable is set; the key is active in Resend.
**Note:** Notification failure never blocks the pipeline — runs still complete
and are recorded; only the alert is missed.

---

## 4. KPI definitions

| KPI | Definition | Source |
|---|---|---|
| **Daily Orders** | Count of `order_id` grouped by `order_date` | `fct_orders` |
| **Revenue** | Sum of `amount` over the period | `fct_orders` |
| **Customers** | Distinct `customer_id` over the period | `fct_orders` |
| **Order Value** | Revenue ÷ Daily Orders (average order value) | `fct_orders` |
| **Retention** | Share of customers with orders in consecutive periods | `fct_orders` |

`fct_orders` excludes `status = 'cancelled'`, so all KPIs reflect non-cancelled
orders only. Adjust the `where` clause in `core/fct_orders.sql` if your
definition of revenue differs.

---

## 5. Escalation

1. Capture the failing run: `pipelinekit status` and the `[PK-*]` error code.
2. Inspect `transform/target/run_results.json` for dbt-level detail.
3. Re-run `pipelinekit validate --contracts` to isolate data vs. config issues.
4. If the failure is upstream (source schema/freshness), escalate to the system
   that owns the operational `orders` table.

---

## 6. Verified Deployments

This table records real end-to-end deployments of Blueprint #001.
Each row represents a verified run by a named tester on a real environment.
This is the evidence behind the `deploy_time_minutes: 60` claim in blueprint.json.

| Date | Tester | Postgres Version | Snowflake Tier | Rows Ingested | Deploy Time | Data Latency | Contracts | Status |
|---|---|---|---|---|---|---|---|---|
| TBD | Eddy Mkwambe | TBD | TBD | TBD | TBD | TBD | All passed | TBD |

### How to add a row

After running `scripts/verify-blueprint-001.ps1` successfully:
1. Fill in the row above with your actual results.
2. Commit: `git commit -m "Blueprint #001 verified — [date] by [name]"`.
3. This record is permanent institutional memory.

### Claim validation

| Claim in blueprint.json | Status | Evidence |
|---|---|---|
| `deploy_time_minutes: 60` | Unverified until first row above | — |
| `time_to_trusted_data_hours: 24` | Unverified until first row above | — |

| 2026-06-25 | Eddy Mkwambe | Local placeholder | Not reached | 0 | 0.4 min | N/A | FAILED — 3 gaps | DIAGNOSTIC |

### Diagnostic Run — 2026-06-25

Three gaps identified for Sprint 6-2:
1. dlt credential resolution — needs credential translation in adapter
2. contracts.directory defaults to repo root — should point to blueprint contracts/
3. SourceConfig missing user/password/warehouse as first-class fields

Verification run not counted until all three gaps resolved and dry-run + full run pass.
