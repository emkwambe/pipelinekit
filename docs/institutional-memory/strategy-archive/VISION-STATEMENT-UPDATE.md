# PipelineKit — Vision Statement Update
## Post-dbt/Fivetran Merger Reshaping — Version 2

**Date:** June 25, 2026  
**Supersedes:** VISION-STATEMENT-UPDATE.md (v1 — June 25, 2026)  
**Type:** Vision clarification — governing principle unchanged  
**Owner:** Command Center

---

## What Changed from v1

Version 1 introduced "control plane" as the primary positioning term. That language is technically accurate but strategically weak — Dagster, Kestra, Prefect, and Microsoft Fabric all use control plane language. It puts PipelineKit in the same mental bucket as orchestrators.

Version 2 removes "control plane" as a positioning term and replaces it with "intelligence layer" and "operating system" — language that is already in the governing principle and is broader, more accurate, and more differentiated.

Version 2 also replaces "using AI" with "AI-native engineering" in the vision statement — a category, not a feature.

Version 2 removes negative definitions ("PipelineKit is not an ingestion tool") and replaces them with positive definitions of what PipelineKit provides.

---

## The Governing Principle — Unchanged

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

This does not change. Everything else evolves beneath it.

---

## Updated Vision Statement

**Previous (v1):**
> PipelineKit enables organizations to design, validate, operate, and continuously improve trusted analytics pipelines using AI — coordinating across whatever infrastructure they already run.

**Updated (v2):**
> PipelineKit enables organizations to design, validate, operate, and continuously evolve trusted analytics pipelines through AI-native engineering.

**Why the change:**
- "Using AI" is a feature description. "AI-native engineering" is a category.
- "Continuously improve" is generic. "Continuously evolve" implies architectural maturity — systems that adapt, not just systems that get tuned.
- Removed the "coordinating across whatever infrastructure" clause — it is accurate but leads readers toward orchestrator comparisons. The PRD executive summary handles the heterogeneous stack story more precisely.

---

## Positioning Language — What to Use and Avoid

### Use

> PipelineKit provides the intelligence layer that designs, validates, governs, diagnoses, and continuously improves trusted analytics pipelines throughout their lifecycle.

> PipelineKit operates across the analytics stack — coordinating infrastructure, enforcing standards, validating architecture, and enabling AI-driven development regardless of the underlying tools.

> PipelineKit is designed for organizations that run heterogeneous data environments and need a single operating model above their tools.

### Avoid

| Avoid | Because | Use instead |
|---|---|---|
| "Control plane" | Puts PipelineKit with Dagster/Kestra/Prefect | "Intelligence layer" or "operating system" |
| "PipelineKit is not an ingestion tool" | Negative definition, competitor-first framing | Describe what PipelineKit provides positively |
| "PipelineKit sits above them" | Implies subordination rather than coordination | "PipelineKit operates across the stack" |
| "Using AI" | Generic feature description | "AI-native engineering" |
| "Replaces existing infrastructure" | Creates resistance | "Operates above existing infrastructure" |

---

## The TTTD Optimization Metric

Time-to-Trusted-Data is the primary metric. It is already in the Constitution, PRD, and CLI help text.

The five dimensions are **design principles**, not promised benchmarks:

1. **Design speed** — how quickly from requirements to deployable pipeline
2. **Validation speed** — how quickly correctness is confirmed
3. **Deployment safety** — how confidently changes are deployed
4. **Diagnostic speed** — how quickly failures are explained
5. **Pipeline confidence** — how certain teams are about analytics correctness

These are stated as design intent. Numbers are earned from real usage, not asserted upfront.

Every new feature evaluation asks: which of these five dimensions does this improve?
If it improves none — it does not belong in PipelineKit.

---

## Documents to Update

1. `docs/prd/PipelineKit — Final Product Requirements Document.md`
   — Replace executive summary with PRD-Executive-Summary-v2.md content
   — Add TTTD dimensions table
   — Update version to 2.0

2. `docs/institutional-memory/strategy-archive/Strategic-Operating-Document.md`
   — Add market context section (already drafted in VISION-STATEMENT-UPDATE v1)
   — Remove "PipelineKit is not..." language from positioning sections
   — Add intelligence layer framing

3. `docs/constitution/Product-Constitution.md`
   — Add TTTD five dimensions as design principles under the Mission section
   — Do not change the governing principle

All three are documentation updates — no code change, no SPEC change, no ADR required.
