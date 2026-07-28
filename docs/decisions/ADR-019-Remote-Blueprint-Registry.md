# ADR-019: Remote Blueprint Registry Governance

**Status:** Accepted  
**Date:** June 26, 2026  
**Phase:** 6 — Sprint 6-6  
**ADR Number:** 019  
**Governs:** `src/pipelinekit/blueprints/remote.py`, `pipelinekit blueprint install/search/publish`

---

## Context

Sprint 6-5 proved that AI Blueprint Proposal works — Blueprint #003 (stripe-to-snowflake) was proposed, reviewed, and applied in under 15 minutes. But the proposal quality is bounded by the local blueprint library. A user starting fresh has zero patterns to draw from.

The Remote Blueprint Registry solves this: a curated catalog of verified blueprints installable via CLI. It also solves distribution — design partners can install production-ready blueprints in one command instead of building from scratch.

---

## Decision

**Implement a Remote Blueprint Registry backed by a simple HTTPS endpoint, with CLI commands for search, install, and publish. All installed blueprints are verified against `schemas/blueprint.schema.json` before being written to disk.**

---

## Registry Architecture

The registry is intentionally simple. Phase 1: a static JSON catalog hosted at a known URL. No authentication required for read operations. Authentication required for publish.

```
Registry URL: https://registry.pipelinekit.dev/v1/

Endpoints:
  GET /catalog.json          — full catalog of available blueprints
  GET /blueprints/<name>.zip — blueprint archive
  POST /blueprints/          — publish (authenticated, future)
```

The catalog is a JSON file:

```json
{
  "version": "1.0",
  "updated_at": "2026-06-26T00:00:00Z",
  "blueprints": [
    {
      "name": "postgres-to-snowflake",
      "version": "1.0.0",
      "description": "...",
      "source": "postgres",
      "destination": "snowflake",
      "verified": true,
      "verified_at": "2026-06-26",
      "verified_by": "mpingo-systems",
      "downloads": 0,
      "tags": ["postgres", "snowflake", "sql"],
      "url": "https://registry.pipelinekit.dev/v1/blueprints/postgres-to-snowflake-1.0.0.zip"
    }
  ]
}
```

---

## Trust Model

Every blueprint installed from the registry is:

1. Downloaded as a zip archive
2. Extracted to a temp directory
3. Validated against `schemas/blueprint.schema.json`
4. Verified to contain all 8 required assets (Smell 15)
5. Only written to `blueprints/<name>/` after validation passes

If validation fails → `PK-REGISTRY-002` is raised. Nothing is written to disk.

**Verified blueprints** (marked `"verified": true`) have been run end-to-end by the Mpingo Systems team and have a Verified Deployments row in their runbook. Unverified blueprints can still be installed but show a warning.

---

## Phase 1 Registry Hosting

Phase 1: the registry catalog and blueprint archives are hosted as static files on Cloudflare Pages (consistent with Mpingo Systems' existing infrastructure). No server-side logic required.

The `catalog.json` and blueprint zip files are committed to a separate `pipelinekit-registry` repository and deployed via Cloudflare Pages.

Phase 2 (future): a proper registry API with user accounts, ratings, and community contributions.

---

## The Proposal Flywheel

Every installed blueprint becomes a pattern source for `pipelinekit generate blueprint`. The more blueprints installed, the better every proposal gets.

```
Install blueprint → Better proposals → Better blueprints → Install more blueprints
```

This is why Sprint 6-6 is more critical than Sprint 6-7. The registry is the engine that makes the proposal system improve over time.

---

## Consequences

### Benefits
- Design partners install blueprints in one command
- AI proposals improve as catalog grows
- Blueprint quality is verifiable — the verified badge means something
- Cloudflare Pages hosting is free and already in use

### Limitations
- Phase 1 static registry requires manual catalog updates
- No user accounts or ratings in Phase 1
- Publish command is Phase 2 — Phase 1 is read-only for users

---

## Principle Alignment

- ADR-005 (BYOK) — installed blueprints never contain credentials
- ADR-008 (Deterministic) — schema validation before write
- ADR-009 (Human-Readable) — catalog.json is human-readable
- Smell 15 (Blueprint Shortcut) — 8-asset validation on every install
- Smell 16 (Control Plane Inversion) — registry serves blueprints; PipelineKit remains the OS
