# Utility Tables

This directory is for team-specific downstream tables that combine
Core table data with additional business logic.

Examples from Smartsheet:
- finance_utility.late_contracts    (Finance team)
- sales_utility.priority_contracts  (Sales team)
- product_utility.users_by_contract (Product team)

How to add a utility table:
1. Create a subdirectory: `utility/{team_name}/`
2. Create your model: `{team_name}_utility_{use_case}.sql`
3. Base it on core_contracts: `select * from {{ ref('core_contracts') }}`
4. Add it to `schema.yml` with your team as owner
5. Run: `pipelinekit quality check-best-practices --blueprint data-mesh-contracts`

Utility tables should:
  ✓ Start from the Core table, not raw sources
  ✓ Have a declared column owner for every column (GM-4)
  ✓ Have a description explaining the business purpose
  ✓ Have primary key tests if they produce one row per entity

A note on the last point: QM-10 checks BP-001 (primary key integrity) on every
model it finds. A utility model that aggregates — one row per employee rather
than per contract — still needs a `unique` + `not_null` pair on whatever its
grain key is, or the blueprint drops below Grade A.
