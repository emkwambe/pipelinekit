# ADR-015: Architecture Intelligence Scope and Governance

**Status:** Accepted  
**Date:** June 25, 2026  
**Phase:** 5 — Architecture Layer  
**ADR Number:** 015  
**Governs:** `src/pipelinekit/ai/arch_*.py`, `src/pipelinekit/cli/architect.py`, `schemas/architecture.schema.json`

---

## Context

Phase 4 delivered AI-assisted diagnostics — answering "why did this pipeline fail?"

The dbt/Fivetran merger and broader market consolidation revealed a decision layer that no current tool owns: architectural reasoning above the tool stack. Enterprises running heterogeneous environments need guidance on tool selection, cost optimization, ADR compliance, and stack evolution that no single platform vendor can provide without bias.

This ADR defines what Architecture Intelligence is, what it is not, what it may do, and what governance constraints apply.

---

## Decision

**Implement Architecture Intelligence as a Phase 5 capability that extends the existing LLMProvider Protocol with an `architect` method, adds the `pipelinekit architect` command group, and introduces a new `architecture.schema.json` output contract.**

Architecture Intelligence reasons about architecture decisions. It does not make them.

---

## What Architecture Intelligence Is

Architecture Intelligence is the AI reasoning layer that answers:

- "Should this pipeline use dbt or SQLMesh?"
- "Should this use Fivetran or dlt?"
- "Will this proposed change violate our ADRs?"
- "What is the cheapest reliable architecture for this data volume?"
- "What changed in our stack that needs attention?"

It operates above the tool layer — not as a tool itself, but as a reasoning system that understands the tradeoffs between tools and the constraints of a specific organization's architecture.

---

## What Architecture Intelligence Is Not

- It is not a blueprint generator (that is Phase 6+)
- It is not an auto-refactoring tool
- It is not a vendor recommendation engine with commercial bias
- It is not a replacement for architectural judgment
- It does not contact any vendor API except the configured LLM provider

---

## The Architecture Intelligence Boundary

Extending ADR-007 for Phase 5:

```
AI may:
  ✓ Read config, blueprints, ADRs, run history, contract violations
  ✓ Reason about tool tradeoffs
  ✓ Check ADR compliance for proposed changes
  ✓ Compare tools against the organization's specific data profile
  ✓ Return structured ArchitectureResult with recommendations
  ✓ Explain reasoning in plain English

AI may not:
  ✗ Modify pipelinekit.yaml
  ✗ Modify any ADR file
  ✗ Install or remove tools
  ✗ Execute any pipeline change
  ✗ Set can_auto_apply = True (requires ADR-016)
  ✗ Contact vendor APIs to retrieve pricing (uses static knowledge)
```

`can_auto_apply` is always `False` in Phase 5. ADR-016 will govern if and when auto-apply becomes appropriate, with full reversibility requirements.

---

## Why Extend LLMProvider Rather Than Create a Separate Protocol

The three existing providers (OpenAI, Anthropic, Ollama) already implement `LLMProvider`. Adding an `architect` method to the Protocol means:

- No new provider infrastructure
- Same BYOK pattern (ADR-005)
- Same isolation pattern (provider imports inside providers/)
- Same schema validation trust boundary
- Backward compatible — `diagnose` and `summarize` unchanged

Architectural Smell 8 (Single-Implementation Abstraction) guided this decision: the same three providers serve both diagnostic and architectural reasoning. A separate protocol for the same providers would be premature abstraction.

---

## Why a New Schema Rather Than Extending diagnostic.schema.json

Architectural results carry fundamentally different structure:

- `diagnostic.schema.json` captures: what failed, why, what to fix
- `architecture.schema.json` captures: current state, proposed state, tradeoffs, ADR compliance

Extending the diagnostic schema would bloat it and make both purposes harder to validate. A separate schema per output type is cleaner and more auditable.

---

## ADR Parsing Governance

Phase 5 reads `docs/decisions/` to power compliance checking. This introduces a new dependency on documentation structure. Rules:

- ADR files are read-only — `ADRReader` never writes, creates, or deletes
- ADR parsing failures produce `PK-ARCH-003` — they never crash silently
- Unreadable or malformed ADR files are skipped with a warning — not treated as violations
- ADR compliance checks are advisory — they flag potential conflicts, not definitive rulings

---

## Relationship to the dbt/Fivetran Merger

The merger was the market signal that validated this capability. The merged platform owns ingestion + transformation. Architecture Intelligence owns the reasoning layer above them — helping teams decide whether to use that platform, when to use something else, and how to manage the transition.

PipelineKit does not compete with Fivetran or dbt. It helps teams make better decisions about using them alongside everything else they run.

---

## Consequences

### Benefits
- PipelineKit becomes the first tool to own the architectural decision layer
- ICP-004 (Mixed-Stack Enterprise) has a direct capability serving their core pain
- Builds on Phase 4 infrastructure — minimal new dependencies
- ADR compliance checking creates a tight loop between documentation and practice

### Limitations
- Architecture recommendations depend on LLM quality — bounded by provider capability
- Cost estimates use static LLM knowledge — not live vendor pricing APIs
- ADR parsing requires consistent ADR format — malformed ADRs reduce compliance accuracy
- `can_auto_apply = False` means users must manually act on recommendations

### Phase 6+ Implications
- ADR-016 will define when `can_auto_apply = True` is appropriate with reversibility
- Blueprint generation from scratch (AI designs new blueprints) is a natural Phase 6 capability
- Remote blueprint registry with community-contributed patterns is Phase 6+

---

## Principle Alignment

- ADR-005 (BYOK) — same provider keys, no new credentials
- ADR-007 (AI is Operator not Owner) — recommendations only, human applies
- ADR-008 (Deterministic Before AI) — ADR compliance is rule-based, AI interprets edge cases
- ADR-009 (Human-Readable) — recommendations in plain English with explicit tradeoffs
- ADR-010 (Explainability Before Automation) — every recommendation explains its reasoning
- ADR-011 (Trust as primary metric) — ADR compliance checking increases architectural trust
- ADR-014 (Direct API calls, not MCP for Phase 4/5) — same pattern, no new MCP infrastructure
- Architectural Smell 13 (Observer Becomes Actor) — architect observes and recommends, never applies
- Architectural Smell 16 (Control Plane Inversion) — PipelineKit reasons above tools, never becomes one
