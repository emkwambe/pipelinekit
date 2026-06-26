# ADR-018: AI Blueprint Generation Governance

**Status:** Accepted  
**Date:** June 26, 2026  
**Phase:** 6 — Sprint 6-5  
**ADR Number:** 018  
**Governs:** `src/pipelinekit/ai/blueprint_generator.py`, `src/pipelinekit/cli/generate.py`, `pipelinekit generate blueprint`

---

## Context

Phases 4 and 5 established that AI in PipelineKit observes and recommends — it never acts autonomously. Both phases enforced this through `can_auto_fix = False` and `can_auto_apply = False`.

Sprint 6-5 introduces a fundamentally different capability: AI generating new artifacts — dlt pipelines, dbt models, contracts, Soda checks — that did not previously exist. This is the first time AI moves from advisor to co-author.

This requires a new governance decision that cannot be derived from ADR-007 alone.

---

## The Core Question

> When AI generates a blueprint asset, when does it touch the filesystem?

Three positions:

**Position A — Generate then review:** AI writes all assets to a `drafts/` directory. User reviews and approves by moving files to `blueprints/<name>/`. Files exist before review.

**Position B — Generate and stream:** AI streams each asset to the terminal. User types `y` to write each one. Files are written only after per-asset approval.

**Position C — Plan then apply:** AI produces a `GenerationPlan` data structure (not files). User reviews the plan interactively. Only approved assets are written to disk. Nothing touches the filesystem during generation.

---

## Decision

**Position C — Plan then apply.**

Nothing touches the filesystem during generation. AI produces a `GenerationPlan`. Human reviews each asset interactively. Only approved assets are written to disk via `pipelinekit generate apply`.

---

## Why Position C Over A and B

**Position A** creates files before the user has reviewed them. Even in a `drafts/` directory, unreviewed AI output exists as real files — they can be accidentally committed, accidentally used, and are harder to discard than a data structure.

**Position B** is better but streams imply linear sequential review. If the user wants to re-review asset 3 after seeing asset 7, streaming makes that awkward.

**Position C** is cleanest: the plan is a data structure, not files. The user can review in any order, reject and re-generate individual assets, edit proposals, and only when satisfied does `apply` write to disk. This mirrors the `--dry-run` pattern already established in Phase 2.

---

## The Generation Boundary

```
AI MAY generate:
  ✓ blueprint.json structure
  ✓ pipelinekit.example.yaml with ${VAR} credential placeholders
  ✓ dlt ingestion pipeline scaffold
  ✓ dbt staging models (SELECT * with column renaming)
  ✓ dbt core models (joins and aggregations)
  ✓ sources.yml with env_var() references
  ✓ Contract definitions (required columns, uniqueness, freshness)
  ✓ Soda check templates
  ✓ alerts/config.yaml
  ✓ README.md and runbook.md templates

AI MAY NOT:
  ✗ Write any file to disk without explicit per-asset human approval
  ✗ Execute any pipeline
  ✗ Connect to any source or destination during generation
  ✗ Generate credentials, API keys, or connection strings
  ✗ Generate a blueprint that bypasses any of the 8 required assets
  ✗ Self-approve its own output (Smell 13 extended to generation)
```

---

## The Evidence Base for Generation

AI generates from patterns, not from imagination.

`BlueprintGenerator` reads:
1. Existing blueprints from `BlueprintRegistry` — what good looks like
2. `schemas/blueprint.schema.json` — structural constraints
3. `src/pipelinekit/config/schema.py` — available SourceConfig fields for the source type
4. User-provided source type, destination type, and table names

AI never connects to the source or destination during generation. It reasons from schemas and patterns. Incorrect generated SQL is caught by `dbt parse` in the verification step — not in production.

---

## The GenerationPlan

```python
@dataclass
class GeneratedAsset:
    asset_type: str      # "blueprint.json" | "example_yaml" | "dbt_model" | etc.
    filename: str        # relative path within the blueprint directory
    content: str         # the generated content as a string
    approved: bool = False
    edited: bool = False

@dataclass  
class GenerationPlan:
    blueprint_name: str
    source_type: str
    destination_type: str
    tables: list[str]
    assets: list[GeneratedAsset]  # all 8 required assets
    provider: str
    generated_at: str
    can_auto_apply: bool = False   # always False — human approval required
```

`can_auto_apply` is always False. This is the same constraint as Phases 4 and 5, applied to generation.

---

## The CLI Flow

```
pipelinekit generate blueprint \
  --source stripe \
  --destination snowflake \
  --tables charges,customers,subscriptions

→ Generating blueprint...
→ Reading existing blueprints as patterns...
→ Calling AI provider...
→ GenerationPlan ready — 8 assets

Asset 1/8: blueprint.json
───────────────────────────
{
  "name": "stripe-to-snowflake",
  "version": "1.0.0",
  ...
}
───────────────────────────
Accept [a], Edit [e], Reject [r], Skip [s]: a

Asset 2/8: pipelinekit.example.yaml
...

→ 7/8 assets accepted. 1 edited.
→ Run 'pipelinekit generate apply' to write to blueprints/stripe-to-snowflake/
→ Or 'pipelinekit generate show' to review again.

pipelinekit generate apply
→ Writing 8 assets to blueprints/stripe-to-snowflake/
→ ✓ blueprint.json
→ ✓ pipelinekit.example.yaml
...
→ Blueprint stripe-to-snowflake created.
→ Run 'pipelinekit blueprint validate' to verify.
```

---

## Schema Validation

Every generated asset is validated before being shown to the user:
- `blueprint.json` → validated against `schemas/blueprint.schema.json`
- `pipelinekit.example.yaml` → validated through `PipelineConfig`
- dbt models → validated by `dbt parse` after apply
- contracts → validated through `ContractValidator`

If any asset fails validation → it is flagged in the plan as invalid and shown with the error. The user can edit and re-generate that specific asset.

---

## Consequences

### Benefits
- Blueprint catalog grows as fast as AI can generate and humans can review
- The 8-asset requirement is enforced by the generator — incomplete blueprints cannot be generated
- Every generated blueprint goes through the same verification path as hand-crafted ones
- The review process creates a natural quality gate before anything touches disk

### Limitations
- Generated SQL will not be perfect — dbt staging models need human review for column names
- Generated contracts will be conservative — humans should review freshness thresholds and row count ranges
- First-time generation for a new source type (e.g. Salesforce) will be less accurate than for well-documented sources (e.g. Stripe)
- No real-time connection to source — AI cannot inspect actual table schemas

### The Verification Requirement Unchanged
Every AI-generated blueprint must still have a Verified Deployments row in its runbook before design partner outreach. Generation is not verification.

---

## Principle Alignment

- ADR-005 (BYOK) — generated configs use ${VAR} placeholders, never real credentials
- ADR-007 (AI is Operator not Owner) — extended: AI generates proposals, human applies them
- ADR-008 (Deterministic Before AI) — blueprint.schema.json validation is deterministic; AI fills in content
- ADR-009 (Human-Readable) — all generated content is human-readable Markdown, YAML, and SQL
- ADR-017 (PipelineKit owns config) — generated configs follow the same credential pattern
- Smell 13 (Observer Becomes Actor) — extended: AI proposes, human applies
- Smell 15 (Blueprint Shortcut) — generator enforces all 8 assets; partial generation is not possible
