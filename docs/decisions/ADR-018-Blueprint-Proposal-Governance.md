# ADR-018: AI Blueprint Proposal Governance

**Status:** Accepted  
**Date:** June 26, 2026  
**Phase:** 6 — Sprint 6-5  
**ADR Number:** 018  
**Version:** 2.0 — Refined from initial draft based on trust model analysis  
**Governs:** `src/pipelinekit/ai/blueprint_proposer.py`, `src/pipelinekit/cli/generate.py`, `pipelinekit generate blueprint`

---

## Context

Phases 4 and 5 established that AI in PipelineKit observes and recommends — it never acts autonomously. Sprint 6-5 introduces the first time AI proposes new artifacts. This requires the most precise governance of any decision in the project.

---

## Naming Decision — Blueprint Proposal, Not Blueprint Generation

This capability is called **AI Blueprint Proposal**.

The word "generation" implies the system creates production artifacts. It does not. It proposes artifacts that humans approve before they become part of the repository.

The correct architectural phrase is:

> **PipelineKit proposes blueprint artifacts. Humans approve what becomes part of the repository.**

Once the system proves itself through real usage — after design partners validate the quality of proposals — the capability may be called "generation." That transition requires a new ADR. For Sprint 6-5, this is a proposal system.

---

## Decision

**Position C — Plan then Apply, with artifact state tracking.**

AI produces a `BlueprintProposal` (not files). Every proposed artifact moves through explicit states before touching the filesystem:

```
proposed → approved → written → validated
```

No artifact may skip states. `proposed → written` is not a valid transition. Only `approved → written` is.

---

## The Command Model

No command called `generate` directly creates production blueprint files by default.

```powershell
# Step 1: Generate a plan ID (no files written)
pipelinekit generate blueprint \
  --source stripe \
  --destination snowflake \
  --tables charges,customers \
  --plan

# Output:
# Plan ID: plan-stripe-snowflake-20260626-143200
# 13 assets proposed. No files written.
# Review with: pipelinekit generate show plan-stripe-snowflake-20260626-143200
# Apply with:  pipelinekit apply plan plan-stripe-snowflake-20260626-143200

# Step 2a: Interactive review and apply
pipelinekit generate blueprint \
  --source stripe \
  --destination snowflake \
  --tables charges,customers \
  --interactive

# Step 2b: Apply from plan ID (after review)
pipelinekit apply plan plan-stripe-snowflake-20260626-143200
```

The `--plan` flag is the safe default. The `--interactive` flag combines proposal and review in one session.

---

## Artifact State Machine

```
┌──────────┐     human     ┌──────────┐   apply()   ┌─────────┐  validate()  ┌───────────┐
│ proposed │ ──────────── ▶│ approved │ ──────────▶ │ written │ ──────────▶  │ validated │
└──────────┘  approves     └──────────┘             └─────────┘              └───────────┘
     │                           │
     │ human                     │ human
     │ rejects                   │ edits
     ▼                           ▼
┌──────────┐              ┌──────────┐
│ rejected │              │  edited  │ ──── re-proposes ──▶ proposed
└──────────┘              └──────────┘
```

Valid transitions:
- `proposed → approved` (human approves)
- `proposed → rejected` (human rejects)
- `proposed → edited` (human edits)
- `edited → proposed` (re-proposed after edit)
- `approved → written` (apply() called)
- `written → validated` (blueprint validate passes)

Invalid transitions (enforced by code):
- `proposed → written` (cannot write without approval)
- `approved → validated` (must be written first)

---

## The Evidence Model

AI may only propose from:

| Evidence Source | What It Provides |
|---|---|
| Existing approved blueprints | Patterns of what good looks like |
| `schemas/blueprint.schema.json` | Structural constraints |
| `src/pipelinekit/config/schema.py` | Available SourceConfig fields per source type |
| `contracts/` directory | Contract format examples |
| Adapter capability registry | What each source/destination adapter supports |
| User-provided intent | Source type, destination type, table names |

**AI must not invent unsupported connector behavior.**

If a user asks for `--source oracle` and the dlt adapter does not support Oracle — the proposal fails with `PK-GEN-006: Source type 'oracle' not supported by the dlt adapter`. It never generates a blueprint for an unsupported source.

---

## Provenance Metadata

Every proposed artifact includes provenance metadata. This is not optional.

```yaml
# Example: blueprint.json metadata block
_provenance:
  generated_by: pipelinekit
  generation_mode: ai_proposed
  model: claude-sonnet-4-6
  generated_at: "2026-06-26T14:32:00Z"
  plan_id: plan-stripe-snowflake-20260626-143200
  source_evidence:
    - type: blueprint_pattern
      name: postgres-to-snowflake
      version: "1.0.0"
    - type: schema
      name: blueprint.schema.json
    - type: source_config
      name: StripeSourceConfig
  confidence: 0.89
  assumptions:
    - "Stripe charges table has id, amount, currency, status, created columns"
    - "Snowflake destination uses raw schema for dlt landing"
  unsupported_areas:
    - "Stripe webhook ingestion — not supported by dlt[stripe] source"
  requires_human_decisions:
    - "Verify column names match your actual Stripe API version"
    - "Set freshness SLA threshold in contracts/charges.yaml"
  requires_human_approval: true
```

**The provenance block is stripped from the final file when the asset is written.** It exists in the proposal to inform the human reviewer. It does not ship in the blueprint.

---

## Confidence and Assumptions

Every `BlueprintProposal` includes a top-level confidence score and assumption list:

```python
@dataclass
class BlueprintProposal:
    plan_id: str
    blueprint_name: str
    source_type: str
    destination_type: str
    tables: list[str]
    assets: list[ProposedAsset]
    confidence: float              # 0.0–1.0
    assumptions: list[str]         # what AI assumed about the source
    unsupported_areas: list[str]   # what AI could not generate
    requires_human_decisions: list[str]  # explicit decisions the human must make
    provider: str
    generated_at: str
    can_auto_apply: bool = False   # always False
    applied: bool = False
```

Low confidence proposals (< 0.7) are shown with a prominent warning:

```
⚠ Confidence: 0.61 — This proposal has lower confidence than usual.
  The Stripe source type has limited pattern examples in your blueprint library.
  Review all assets carefully before applying.
```

---

## The Adapter Capability Registry

Before generating, the `BlueprintProposer` checks what the dlt adapter actually supports:

```python
# src/pipelinekit/ai/adapter_registry.py

SUPPORTED_SOURCES = {
    "postgres": {
        "dlt_source": "sql_database",
        "credential_fields": ["host", "port", "database", "user", "password"],
        "tables": "configurable",
    },
    "salesforce": {
        "dlt_source": "salesforce",
        "credential_fields": ["username", "password", "security_token"],
        "tables": ["accounts", "opportunities", "contacts", "leads"],
    },
    "stripe": {
        "dlt_source": "stripe_analytics",
        "credential_fields": ["api_key"],
        "tables": ["charges", "customers", "subscriptions", "invoices", "events"],
    },
}

SUPPORTED_DESTINATIONS = {
    "snowflake": {...},
    "bigquery": {...},
    "duckdb": {...},
}
```

If source or destination not in registry → fail with `PK-GEN-006` before calling AI. Never waste an AI call on an unsupported connector.

---

## The Guardrails Summary

Generated artifacts must:

```
✓ Validate against schemas/blueprint.schema.json
✓ Pass ContractValidator structural check
✓ Include provenance metadata (stripped on write)
✓ Include confidence score
✓ Include assumptions list
✓ Include unsupported_areas list
✓ Include requires_human_decisions list
✓ State requires_human_approval: true
✓ Move through proposed → approved → written → validated
✗ Never skip states
✗ Never invent unsupported connector behavior
✗ Never write without explicit human approval
```

---

## Consequences

### Benefits
- Trust model is explicit — humans know exactly what AI assumed and where it is uncertain
- Audit trail — every proposal, approval, and rejection is in state.db
- Provenance — every generated asset traces to its evidence
- Capability-bounded — AI never proposes what the system cannot execute
- Blueprint catalog grows from 2 to N without hand-crafting

### Limitations
- First proposals for new source types will have lower confidence (fewer patterns)
- Provenance metadata adds review overhead (by design — it is the trust mechanism)
- `--interactive` mode requires human attention for each asset

### The Trust Progression

```
Sprint 6-5:  AI proposes → human approves each asset → apply writes
[future]:    AI proposes → human spot-checks → batch apply available
[far future] After proven track record: auto-apply for low-risk assets (requires ADR-019)
```

---

## Principle Alignment

- ADR-005 (BYOK) — generated configs use ${VAR} placeholders
- ADR-007 (AI is Operator not Owner) — AI proposes, human approves, apply writes
- ADR-008 (Deterministic Before AI) — schema validation is deterministic; AI fills content
- ADR-009 (Human-Readable) — provenance metadata is plain English
- ADR-017 (PipelineKit owns config) — generated configs follow credential pattern
- Smell 13 (Observer Becomes Actor) — `BlueprintProposer` proposes, `apply()` writes on human approval only
- Smell 15 (Blueprint Shortcut) — proposer enforces all 8 assets; partial proposals not possible
