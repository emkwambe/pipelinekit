# Data Mesh Pattern — data-mesh-contracts Blueprint

## The Smartsheet Insight

> "If everyone owns a table, no one owns the table."
> — Nate Sooter, Smartsheet Analytics Engineering

The solution: ownership at the COLUMN level, not the table level.

## Structure

```
Frame Table      → one row per entity (contract_id)
Detail Tables    → one per domain, each owns their columns
Core Table       → joined wide table for analytics
Utility Tables   → team-specific downstream views
```

## How to Read This Blueprint

Each domain team owns specific columns:

| Domain | Columns |
|---|---|
| Engineering | contract_id, status, type, created_at |
| Finance | renewal_date, payment_status, arr_value, payment_terms |
| Sales | employee_owners, opportunity_value, account_tier |
| Product | active_users, licensed_users, licenses_purchased, last_active_at |

To see column ownership:

```bash
pipelinekit governance owner column audit data-mesh-contracts
```

## Declaring Column Ownership (GM-4)

The `owner_domain` field in each contract records the *intended* owner and
travels with the blueprint. The audit above reads PipelineKit's own ownership
records, which live in `state.db` rather than in the blueprint — ownership is
organizational state, not blueprint state (ADR-024). So a freshly installed
blueprint audits as unowned until the domains are declared:

```bash
pipelinekit governance owner column set data-mesh-contracts \
    --contract finance_contracts.yaml \
    --column arr_value \
    --domain finance \
    --email finance-data@company.com
```

Repeat per column, then re-run the audit. The intended assignments are the
`owner_domain` values in `contracts/*.yaml`.

## Why the Frame Table Matters

Every Detail table LEFT JOINs to the Frame on `contract_id`. Because all
domains share one key with one row per contract, the Core table is a series of
simple joins with no fan-out and no deduplication step. That is the whole trick:
the Frame makes the joins boring, and boring joins are what let each domain ship
independently.

Do not add domain columns to the Frame. The moment Finance adds `arr_value` to
`frame_contracts`, two domains have a claim on one table and the ownership
question is back.

## A Note on not_null in the Core Table

`core_contracts` asserts `not_null` on domain columns even though they arrive
through a LEFT JOIN and could be null. That is deliberate: the mesh contract is
that every domain provides a row for every contract in the Frame. A null means a
domain is missing data, which should fail the build loudly rather than reach
analytics consumers as a silent gap.

If a domain legitimately covers only some contracts, drop the `not_null` on that
domain's columns in both `core/schema.yml` and the domain's Detail schema — and
say why in the model description, so the next reader knows it was a decision
rather than an oversight.

## How to Extend

Add a new domain:

1. Create `detail/{your_domain}/detail_{domain}_contracts.sql`
2. Add your domain's columns with a LEFT JOIN on `contract_id`
3. Add a `schema.yml` with a description, a `unique` + `not_null` pair on
   `contract_id`, and a test on every column
4. Declare column ownership: `pipelinekit governance owner column set ...`
5. Add your columns to `core_contracts.sql` and `core/schema.yml`
6. Add a contract in `contracts/{domain}_contracts.yaml`
7. Run: `pipelinekit quality check-best-practices --blueprint data-mesh-contracts`

The Core table remains Grade A because every new column is owned, documented,
tested, and covered by a contract. Skip any one of those and the grade drops —
which is the point.
