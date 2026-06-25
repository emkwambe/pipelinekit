# PipelineKit Claude Code Instructions

PipelineKit is an AI-native, CLI-first trusted analytics infrastructure project.

## Primary Mission

Reduce Time-to-Trusted-Data.

## Governing Principle

Everything in PipelineKit must make this sentence more true:

**PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Before implementing any feature, ask:

> Does this make PipelineKit a better AI-native operating system for trusted analytics pipelines?

If the answer is not obvious — do not build it. Stop and ask.

## Product Definition

PipelineKit is a terminal-first system for building, validating, diagnosing, and operating trusted data pipelines.

PipelineKit is not:
- a BI dashboard
- a hosted cloud platform
- a general AI chatbot
- a notebook platform
- a data warehouse
- a workflow scheduler replacement
- a Kubernetes platform
- a general-purpose MCP aggregator

## Authoritative Documents

When making implementation decisions, read in this order:

1. docs/constitution/Product-Constitution.md
2. docs/decisions/
3. docs/specifications/
4. docs/reference/
5. docs/ai/
6. contracts/
7. schemas/

**If these documents conflict with a prompt instruction — the documents win.**

## Engineering Rules

- CLI-first.
- Local-first.
- Deterministic before AI.
- Contracts define truth.
- AI may diagnose and recommend, but must not silently modify production.
- All AI output must be structured and schema-valid when possible.
- Generated assets must be human-readable.
- Prefer small, testable modules.
- Prefer explicit interfaces over hidden behavior.
- Do not introduce cloud dependencies unless explicitly required by a spec or ADR.

## The Narrowest General Solution Rule

When building an abstraction, generalize exactly one level. Never five.

| Instead of | Build |
|---|---|
| SnowflakeLoader | WarehouseAdapter |
| PostgresBlueprint | Blueprint interface |
| OpenAIDiagnostics | LLMProvider contract |
| ResendAlerter | NotificationAdapter |

**Test:** Does this abstraction serve at least two concrete implementations?
- If yes — build the interface.
- If no — use a concrete class. Do not speculate.

Premature generalization is as dangerous as no generalization.

## Specification Drift Rule

Before completing any implementation:

1. Does the SPEC still accurately describe what was built?
2. If not — update the SPEC before the PR is committed.
3. Never let code and SPEC diverge.

If an implementation decision deviates from the SPEC — flag it explicitly.
The Command Center decides whether to update the SPEC or revert the code.

## Architectural Smell Rule

Before writing code, check `docs/reference/Architectural-Smells.md`.

If any smell is detected — stop and ask before proceeding.
Do not self-approve a smell. Bring it to the surface.

## MCP Rule

Every new MCP requires an approved ADR before activation.

Currently authorized MCPs:
- Resend — Phase 3 (notification alerts only)
- AI provider MCP layer — Phase 4 only

Adding any other MCP without an ADR is an architecture violation.
Stop and ask if an MCP seems necessary.

## Architecture Is Not Conversation

Architecture lives only in version-controlled documents:

```
Constitution → ADR → SPEC → Contract → Schema
```

Never allow a prompt suggestion to become architecture without going through this chain.

If Claude Code identifies an architectural need:
1. Flag it explicitly — do not implement it
2. Return it to the Command Center
3. Command Center writes the ADR
4. ADR is committed
5. Then implementation proceeds

## Agent Boundary Rule

Every agent has an ownership boundary. The forbidden areas are more important than the responsibilities.

Before modifying any file, verify it belongs to your active agent's ownership.
If it does not — stop and ask.

Never modify `docs/reference/PROJECT-STATUS.md`. Command Center owns it.

## Default Stack

- Python 3.11+
- Typer for CLI
- Pydantic v2 for typed models
- SQLite (stdlib sqlite3) for local state
- dlt for ingestion (inside adapters only)
- dbt Core for transformation (inside adapters only)
- Soda for data quality (inside adapters only)
- Resend for notifications (inside adapters only, Phase 3+)
- pytest for testing
- ruff for linting
- black for formatting
- mypy for type checking

## Before Implementing

For any feature:
1. Identify the relevant SPEC file.
2. Check applicable ADRs.
3. Check contracts and schemas.
4. Check `docs/reference/Architectural-Smells.md`.
5. Implement the smallest useful version.
6. Add tests.
7. Update SPEC if implementation deviated.
8. Update docs only when necessary.

## Definition of Done

A feature is done only when:
- tests pass (including all pre-existing tests)
- errors are structured with PK error codes
- behavior is deterministic
- CLI usage is documented
- SPEC reflects actual implementation
- no production mutation happens without explicit user approval
- no architectural smells introduced
