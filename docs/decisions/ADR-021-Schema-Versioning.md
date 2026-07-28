# ADR-021 — Schema Versioning for Data Contracts

**Date:** June 28, 2026  
**Status:** Accepted  
**Capability:** DC-8  
**Author:** Eddy Mkwambe + Command Center  
**Deciders:** Eddy Mkwambe

---

## Context

PipelineKit v0.1.0 ships DC-1 through DC-7 — data contract enforcement at runtime
(not-null, uniqueness, accepted values, row counts, freshness). These capabilities
validate that data meets its contract but do not track how contracts evolve over time.

As pipelines mature, schemas change. A column gets renamed. A new field is added.
An accepted value is added or removed. Without versioning, there is no way to:
- Know what the contract looked like at a previous point in time
- Detect when a schema change breaks an existing contract
- Roll back a contract change if it causes downstream failures
- Communicate contract changes to downstream consumers

DC-8 adds schema versioning to the contract lifecycle. DC-9 (Breaking Change Detection)
and DC-10 (Consumer Notification) depend on DC-8 existing first.

---

## Decision

Store contract versions in `state.db` with a new `dc_contract_versions` table.

Every time `pipelinekit validate` runs and succeeds, the current contract schema is
snapshotted and stored with:
- a version number (semantic: MAJOR.MINOR.PATCH)
- a SHA-256 hash of the contract content
- the timestamp of the snapshot
- the blueprint name it belongs to
- the full contract content as JSON

Version numbers follow semantic versioning rules:
- PATCH: additive changes (new optional column, new accepted value)
- MINOR: new required fields or tightened constraints
- MAJOR: removed fields, renamed fields, type changes

Version bumping is AI-assisted (proposes the version bump type) but human-approved
(Eddy confirms before the version is written). This preserves the trust model.

The CLI surface is:
```
pipelinekit contract version          # show current version of all contracts
pipelinekit contract version --history # show version history
pipelinekit contract version --diff v1.0.0 v1.1.0  # diff two versions
pipelinekit contract snapshot          # manually snapshot current contracts
```

---

## Alternatives Considered

**Alternative 1: Git-based versioning**
Use git history of the contract YAML files as the version store.
Rejected: requires git to be installed and accessible at runtime, creates coupling
between PipelineKit's operational state and the user's git configuration.

**Alternative 2: External version registry**
Use a remote registry (like registry.pipelinekit.dev) to store contract versions.
Rejected: adds network dependency to a local operation, creates privacy concerns
(contract schemas may contain sensitive field names).

**Alternative 3: No versioning — manual diffs**
Leave versioning to the user via git diff on the YAML files.
Rejected: this is the current state and it is exactly the problem DC-8 solves.
Design partners will need contract history for compliance and audit purposes.

---

## Consequences

**Positive:**
- Enables DC-9 (Breaking Change Detection) — the highest-value Phase 2 capability
- Enables DC-10 (Consumer Notification) and DC-11 (Contract Lifecycle)
- Provides audit trail for compliance (CM-1 SOC 2, CM-5 CBK)
- Makes `pipelinekit health` more informative about contract drift

**Negative:**
- Adds state.db migration (new table) — must be handled gracefully for existing installs
- AI version bump proposal adds one extra step to the validate workflow
- Version numbers must be maintained carefully — wrong MAJOR bump is confusing

**Neutral:**
- Contract YAML files themselves do not change format
- Existing DC-1 through DC-7 capabilities are unaffected

---

## Implementation Notes

- New table: `dc_contract_versions` in state.db
- Migration: add table if not exists (non-destructive, safe for existing installs)
- Hash algorithm: SHA-256 of the normalized contract JSON (sorted keys)
- Version comparison: use `packaging.version` (already in dependencies)
- AI version bump: uses existing AI provider abstraction (AI-1) with a short prompt
- Trust model: `can_auto_apply = False` — version bump always requires human confirmation

---

## References

- SPEC-020-DC-8-Schema-Versioning.md (this sprint)
- ADR-016-Data-Contract-Architecture.md (existing)
- EMS-BUILD-SEQUENCE.md Phase 2 (DC-8 is item #27)
- EMS-CAPABILITY-TAXONOMY.md DC-8
