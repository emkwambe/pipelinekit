# Changelog

All notable changes to PipelineKit are documented in this file.

## [Unreleased]

### Added — Phase 2 Sprint 5 (QM-6 Volume Anomaly Detection)
- `pipelinekit quality record-counts` — record row counts for pipeline tables
- `pipelinekit quality check-anomalies` — detect volume anomalies vs rolling baseline
- `pipelinekit quality row-count-history` — show row count history per table
- Rolling baseline: 20% default threshold, 7-snapshot window, 3-snapshot minimum
- ESTABLISHING status shown when fewer than 3 snapshots exist
- New error code: PK-QM-003
- New state.db table: qm_row_counts


### Added — Phase 2 Sprint 4 (GM-1 Ownership Assignment)
- `pipelinekit governance owner set` — assign owner to a blueprint
- `pipelinekit governance owner get` — view owner details
- `pipelinekit governance owner list` — list all blueprints with ownership status
- `pipelinekit governance owner remove` — remove owner from a blueprint
- `pipelinekit health --strict` now includes ownership check (6th check)
- New error codes: PK-GM-001, PK-GM-002
- New governance module: src/pipelinekit/governance/


### Added — Phase 2 Sprint 3 (QM-4 Coverage Monitoring)
- `pipelinekit quality coverage` — dbt test and Soda check coverage per blueprint
- `pipelinekit quality coverage --blueprint <name>` — filter by blueprint
- `pipelinekit quality coverage --format json` — machine-readable output
- Coverage metrics: column coverage %, untested columns, Soda check inventory
- New error codes: PK-QM-001, PK-QM-002
- New quality module: src/pipelinekit/quality/


### Added — Phase 2 Sprint 1 (DC-8 Schema Versioning)
- `pipelinekit contract version` — show current semantic version of all installed contracts
- `pipelinekit contract version --history` — full version history per contract  
- `pipelinekit contract version --diff v1.0.0 v1.1.0` — diff two contract versions
- `pipelinekit contract snapshot` — snapshot all contracts with semantic versioning
- Deterministic version bump rules: PATCH (additive) / MINOR (tightened) / MAJOR (breaking)
- New error codes: PK-DC-008, PK-DC-009, PK-DC-010
- New state.db table: `dc_contract_versions`

### Added — Phase 2 Sprint 2 (DC-9 Breaking Change Detection)
- `pipelinekit contract snapshot` detects breaking changes before writing MAJOR versions
- `pipelinekit contract snapshot --force` — accept breaking change and proceed
- `pipelinekit contract check-breaking` — check all contracts without snapshotting
- dbt model impact scan — identifies which .sql models reference removed columns
- New error code: PK-DC-011 (breaking change blocked without --force)

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-28

### Added
- Blueprint registry (registry.pipelinekit.dev)
- 3 verified blueprints (postgres, salesforce, stripe → snowflake)
- AI blueprint proposal (5 providers)
- Migration intelligence (Airbyte/Fivetran/Python)
- Blueprint version management (outdated/upgrade/rollback)
- Slack alerting adapter
- Cross-database compatibility macros
