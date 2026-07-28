# ADR-013: Resend as Phase 3 Notification MCP

**Status:** Accepted  
**Date:** June 25, 2026  
**Phase:** 3 — Trust Layer  
**Governs:** `.mcp/registry/servers.md` Resend entry, `adapters/alerts/resend/`

---

## Context

Phase 3 introduces the first external service integration beyond data providers: email notification delivery. When pipelines fail, contracts are violated, or quality checks do not pass, operators need to be notified through a channel they already monitor.

PipelineKit's governing principle requires that providers be replaceable and that no provider-specific logic leak outside adapters (ADR-005). This principle applies equally to notification providers.

The question was not whether to add notifications — that is required by the trust layer mission. The question was which provider to use first and how to govern it.

---

## Decision

**Use Resend as the Phase 3 notification provider, accessed through the adapter pattern.**

Resend is registered in `.mcp/registry/servers.md` as the first MCP in the PipelineKit stack.

All Resend-specific code is isolated inside `src/pipelinekit/adapters/alerts/resend/adapter.py`.  
The `NotificationDispatcher` calls `BaseAdapter` methods — it never calls Resend directly.  
API key is provided via `RESEND_API_KEY` environment variable — never hardcoded (ADR-005, BYOK).  
Phase 3 scope: email only.

---

## Alternatives Considered

**SendGrid** — larger, more enterprise features, higher complexity. Resend is developer-first, simpler API, aligns better with PipelineKit's developer-first audience.

**SMTP direct** — no dependency, maximum portability. Rejected because it requires customers to manage SMTP credentials and infrastructure. Resend handles deliverability.

**Slack** — real-time channel notifications. Deferred to Phase 4. Email is the universal baseline. Slack requires workspace setup and is not universally available.

**No notifications in Phase 3** — rejected. A pipeline that fails silently cannot be trusted. Notifications are a trust layer requirement, not a nice-to-have.

---

## Consequences

### Benefits
- Developers can receive failure alerts without infrastructure setup
- BYOK — customers bring their own Resend API key, no PipelineKit vendor lock-in
- Resend adapter implements BaseAdapter — swappable for any future email provider
- Notification failure never corrupts pipeline state (dispatcher never raises)

### Limitations
- Requires a Resend account and API key — one more credential to manage
- Email only in Phase 3 — Slack, webhook, PagerDuty are Phase 4+
- No notification history UI — state records exist but no viewer yet

### MCP Governance Rule Established
This ADR formalizes the rule that every new MCP requires an ADR. This is ADR-013 — the first MCP ADR. All future MCPs follow this pattern.

---

## Principle Alignment

- ADR-005 (BYOK) — customer provides API key
- ADR-009 (Human-Readable) — notification messages are human-readable, not JSON blobs
- ADR-010 (Explainability Before Automation) — notifications include evidence, not just subject lines
- Architectural Smell 7 — MCP without ADR is now resolved for Resend
