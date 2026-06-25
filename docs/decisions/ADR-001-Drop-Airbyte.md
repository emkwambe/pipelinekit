# ADR-001: Drop Airbyte

Status: Accepted

Date: 2026-06-24

## Context

PipelineKit originally included Airbyte.

Airbyte introduces ELv2 licensing considerations.

## Decision

Adopt dlt as the primary ingestion framework.

## Consequences

### Benefits

- Apache 2.0
- Simpler architecture
- Lower operational complexity

### Costs

- Smaller connector ecosystem
