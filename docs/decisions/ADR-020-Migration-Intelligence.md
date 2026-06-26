# ADR-020: Migration Intelligence Governance

**Status:** Accepted  
**Date:** June 26, 2026  
**Phase:** 6 — Sprint 6-7  
**ADR Number:** 020  
**Governs:** `src/pipelinekit/ai/migration.py`, `pipelinekit migrate analyze`

---

## Context

ICP-004 (Mixed-Stack Enterprise) is the largest revenue opportunity. Their primary blocker is migration cost — they run Airbyte, Fivetran, or custom Python pipelines and need a clear path to PipelineKit without rebuilding everything from scratch.

Migration Intelligence reads an existing pipeline definition and proposes a PipelineKit equivalent. It is the sales tool that closes ICP-004 deals.

---

## Decision

**Implement Migration Intelligence as a read-analyze-propose capability. PipelineKit reads existing pipeline configs, analyzes the migration path, and produces a MigrationProposal. Nothing is executed or written without human approval.**

Same trust model as Blueprint Proposal (ADR-018). AI reads — AI proposes — human approves — apply writes.

---

## Scope

**Phase 1 — supported source formats:**

| Tool | Config format | What PipelineKit reads |
|---|---|---|
| Airbyte | `connection.json` / Airbyte API export | source type, destination, streams, sync mode |
| Fivetran | `connector.json` / Fivetran export | connector type, schema, tables |
| Custom Python | `.py` file with dlt/SQLAlchemy patterns | source connections, table names |
| pipelinekit.yaml (existing) | native format | upgrade path analysis |

**What the MigrationProposal contains:**

1. **Mapping analysis** — what maps cleanly to PipelineKit, what needs manual work, what is unsupported
2. **Draft pipelinekit.yaml** — pre-populated from the existing config
3. **Blueprint recommendation** — which installed blueprint best fits the source/destination
4. **Gap list** — explicit list of what the human must fill in
5. **Confidence score** — per-section confidence

---

## The Migration Boundary

```
AI MAY:
  ✓ Read and parse existing pipeline configs
  ✓ Map source types to PipelineKit SourceConfig fields
  ✓ Propose a draft pipelinekit.yaml
  ✓ Recommend a matching blueprint
  ✓ List gaps and required human decisions

AI MAY NOT:
  ✗ Execute any existing pipeline
  ✗ Connect to any source or destination
  ✗ Write any file without human approval
  ✗ Claim 100% compatibility without evidence
```

---

## Consequences

### Benefits
- ICP-004 enterprises have a migration path — not just a blank slate
- Reduces migration time from days to hours
- Surfaces incompatibilities before they become production incidents

### Limitations
- Custom Python parsing is best-effort — complex pipelines may have low confidence
- Config formats change between tool versions — parsing may need updates
- AI cannot verify that the proposed config actually works — only human verification can

---

## Principle Alignment

- ADR-007 (AI is Operator not Owner) — proposes migration, never executes
- ADR-008 (Deterministic Before AI) — config parsing is deterministic; AI interprets gaps
- ADR-018 (Blueprint Proposal) — same trust model extended to migration
