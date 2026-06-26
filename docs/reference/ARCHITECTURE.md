# PipelineKit Architecture

How PipelineKit is structured, and the decisions that shape it. For contributors and anyone building on PipelineKit.

---

## The Governing Principle

> PipelineKit is the AI-native operating system for trusted analytics pipelines.

Every capability must make that sentence more true. The product has exactly five capabilities — pipeline definition, validation, execution, diagnosis, and intelligence (safe remediation) — and the architecture exists to deliver them deterministically, locally, and from the terminal.

---

## The Five Layers

**Layer 1 — Foundation.** The CLI (Typer), configuration (`pipelinekit.yaml` + Pydantic models), structured errors (`PK-*` codes), and the local SQLite state store. Everything else is built on this. The CLI orchestrates only — it never performs file, database, or provider logic directly.

**Layer 2 — Data Layer.** Ingestion (dlt), transformation (dbt), and quality (Soda), each behind an adapter. The `PipelineRunner` coordinates them; callers never touch a tool's internals.

**Layer 3 — Trust Layer.** Data contracts and blueprints. Contracts define what "correct" means for a table; blueprints package a whole verified pipeline. This is where "the pipeline ran" becomes "the data is correct."

**Layer 4 — Intelligence Layer.** The `LLMProvider` contract plus AI diagnostics, blueprint proposal, and migration intelligence. AI observes and proposes; it never executes.

**Layer 5 — Architecture Layer.** AI reasoning about the stack itself (`pipelinekit architect`): tool selection, cost, ADR compliance, stack evolution, blueprint selection. Advisory only — PipelineKit never applies an architecture change.

---

## The Adapter Pattern

**Why everything is behind an adapter.** PipelineKit is vendor-neutral: customers own their cloud, warehouse, models, and credentials. Each external tool (dlt, dbt, Soda, each AI vendor, the notifier) sits behind a stable interface so the rest of the system depends on the interface, not the vendor. Supported providers may change; the architecture does not.

**How to add a new AI provider.** Implement the `LLMProvider` interface in a new module under `src/pipelinekit/ai/providers/`, keep the vendor SDK import isolated inside that module, and register it in the provider factory. The diagnostics, architecture, proposal, and migration engines call the interface only — they need no changes.

**How to add a new source.** Add the connector to the adapter capability registry (source type, dlt source name, credential fields, verified flag) and provide the ingestion adapter behind the existing interface. The proposal system consults the registry *before* any AI call, so an unsupported connector fails fast with `PK-GEN-006`.

Generalize exactly one level: build a `WarehouseAdapter`, not a `SnowflakeLoader`; an `LLMProvider`, not an `OpenAIDiagnostics`. An abstraction must serve at least two concrete implementations before it earns its place.

---

## The Blueprint System

A blueprint is a complete, verifiable pipeline package. It must provide **eight required assets**: the `blueprint.json` manifest, ingestion, transform (dbt), contracts, quality (Soda), alerts, a readme, and a runbook. The registry verifies all eight are present before writing a blueprint to disk (layout is lenient, so both the hand-crafted `transform/` and the AI-proposed `dbt/` layouts validate).

**The verification requirement.** A blueprint is only "verified" once it has been run end-to-end and the result recorded in its `docs/runbook.md`. Local verification runs against a local source and DuckDB; production verification runs against the real warehouse. Verification that is not recorded does not count.

See the [Blueprint Guide](../guides/BLUEPRINT-GUIDE.md).

---

## The AI Boundary

**What AI can do:** inspect, diagnose, recommend, summarize, classify, and generate proposals.

**What AI cannot do:** silently deploy, delete, migrate, or modify production. Every production change requires explicit human approval.

This is structural, not advisory:

- **The evidence architecture.** AI is always handed structured evidence — an `EvidencePackage`, a parsed migration config, or architecture context — never raw, unbounded input. Diagnoses cite the evidence they used and never invent facts.
- **Schema validation as a trust boundary.** AI output is parsed and validated before it is trusted. Malformed output surfaces as `PK-AI-002` (or `PK-GEN-001` / `PK-MIGRATE-004`), never as a crash.
- **Always-false flags.** `can_auto_fix` and `can_auto_apply` are forced `false` at the model boundary and again by the engine. The only code paths that write are explicit `apply()` calls a human triggers.

---

## The State Store

State is metadata only — never pipeline data — stored in local SQLite at `.pipelinekit/state.db`. All access goes through `src/pipelinekit/state/db.py`; the CLI and runtime never issue SQL directly. The schema defines **eight tables**:

| Table | Purpose |
|---|---|
| `pipeline_runs` | Run history: status, timing, error code/message |
| `validation_runs` | Configuration validation runs |
| `contract_results` | Per-table data-contract validation results |
| `diagnostic_results` | AI diagnostic results (finding, confidence, evidence, actions) |
| `architecture_results` | AI architecture reasoning results |
| `health_runs` | Health-check runs (per-check and overall status) |
| `blueprint_proposals` | AI blueprint proposals — the audit record, reloadable for `show`/`apply` |
| `installed_blueprints` | Blueprints installed from the remote registry |

`initialize()` is idempotent and applies the schema on every startup.

---

## Key Architectural Decisions

Architecture decisions live in `docs/decisions/`. The current set:

| ADR | Decision |
|---|---|
| ADR-000 | Foundational architecture decisions |
| ADR-001 | Drop Airbyte |
| ADR-002 | Drop Sling |
| ADR-003 | Adopt dlt for ingestion |
| ADR-004 | BYOK AI policy — customers own their models and keys |
| ADR-005 | Apache-2.0 license preference |
| ADR-013 | Resend MCP (notifications) |
| ADR-014 | AI provider layer — the `LLMProvider` contract and provider isolation |
| ADR-015 | Architecture Intelligence (`pipelinekit architect`) |
| ADR-016 | Provider diversity (DeepSeek, Mistral — non-US and EU regions) |
| ADR-017 | dlt credential integration policy (`${VAR}` interpolation) |
| ADR-018 | Blueprint Proposal governance (propose → approve → write) |
| ADR-019 | Remote Blueprint Registry |
| ADR-020 | Migration Intelligence |

Read the full text of any ADR in `docs/decisions/`. Each governs specific code and is paired with one or more SPECs in `docs/specifications/`.

---

## The Document Chain

Architecture lives only in version-controlled documents, never in a prompt or a conversation:

```
Constitution → ADR → SPEC → Contract → Schema → Code
```

When a need for new architecture is identified, it is flagged and returned to the Command Center, which writes the ADR. The ADR is committed, then a SPEC, then implementation proceeds. A prompt suggestion never becomes architecture by itself — and when a document and a prompt conflict, the document wins. Code must match its SPEC; drift is treated as a defect and reconciled before a change is complete.
