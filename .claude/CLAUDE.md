# PipelineKit Claude Code Instructions

PipelineKit is an AI-native, CLI-first trusted analytics infrastructure project.

## Primary Mission

Reduce Time-to-Trusted-Data.

## Product Definition

PipelineKit is a terminal-first system for building, validating, diagnosing, and operating trusted data pipelines.

PipelineKit is not:
- a BI dashboard
- a hosted cloud platform
- a general AI chatbot
- a notebook platform
- a data warehouse
- a workflow scheduler replacement

## Authoritative Documents

When making implementation decisions, read in this order:

1. docs/constitution/Product-Constitution.md
2. docs/decisions/
3. docs/specifications/
4. docs/reference/
5. docs/ai/
6. contracts/
7. schemas/

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

## Default Stack

- Python
- Typer for CLI
- Pydantic for typed models
- SQLite for local state
- dlt for ingestion
- dbt Core for transformation
- Soda or equivalent for data quality
- pytest for testing
- ruff for linting
- mypy for type checking

## Before Implementing

For any feature:
1. Identify the relevant SPEC file.
2. Check applicable ADRs.
3. Check contracts and schemas.
4. Implement the smallest useful version.
5. Add tests.
6. Update docs only when necessary.

## Definition of Done

A feature is done only when:
- tests pass
- errors are structured
- behavior is deterministic
- CLI usage is documented
- no production mutation happens without explicit user approval
