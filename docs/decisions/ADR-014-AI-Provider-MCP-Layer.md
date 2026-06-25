# ADR-014: AI Provider MCP Layer

**Status:** Accepted  
**Date:** June 25, 2026  
**Phase:** 4 — Intelligence Layer  
**ADR Number:** 014  
**Governs:** `src/pipelinekit/ai/providers/`, `.mcp/servers/` AI entries, `pipelinekit diagnose`

---

## Context

Phase 4 introduces AI-assisted diagnostics — the first time PipelineKit calls an external AI provider. This creates architectural decisions that must be recorded before a single line of AI code is written:

1. Which AI providers to support
2. How provider-specific code is isolated
3. How API keys are managed (BYOK — ADR-005)
4. What the AI layer is permitted to do
5. How AI output is validated before reaching the user
6. Whether MCPs are used for AI provider access and how

The AI strategy is already defined in `docs/ai/PIPELINEKIT-AI & Model Strategy Standard.md` and ADR-007. This ADR operationalizes those decisions for Phase 4 implementation.

---

## Decision

**Implement a three-provider AI layer (OpenAI, Anthropic, Ollama) behind a stable LLMProvider Protocol, with all provider-specific code isolated in adapter files, all output validated against `schemas/diagnostic.schema.json`, and all recommended actions requiring explicit human approval before execution.**

---

## The LLMProvider Protocol

The protocol is the stable interface. No code outside `src/pipelinekit/ai/providers/` imports any AI provider library.

```
DiagnosticsEngine → LLMProvider (Protocol)
                         ↓
              ┌──────────┼──────────┐
              │          │          │
        OpenAI      Anthropic    Ollama
       (adapter)    (adapter)   (adapter)
```

This is the same pattern as Phase 2 adapters. The DiagnosticsEngine never knows which provider is active. Providers are replaceable.

---

## Provider Selection

Three providers in Phase 4:

| Provider | Use Case | Key Source |
|---|---|---|
| Anthropic | Default recommended — best reasoning for diagnostic tasks | `ANTHROPIC_API_KEY` |
| OpenAI | Alternative for organizations already on OpenAI | `OPENAI_API_KEY` |
| Ollama | Local/air-gapped enterprises — no external API calls | `OLLAMA_HOST` |

Provider is selected via `pipelinekit.yaml`:
```yaml
diagnostics:
  enabled: true
  provider: anthropic
  confidence_threshold: 0.7
```

---

## MCP Governance for AI Providers

The AI providers in Phase 4 are accessed via direct API calls, not MCP servers.

**Rationale:** MCP servers add operational complexity — they require running processes, network configuration, and auth management. For Phase 4 diagnostic calls (which are synchronous, user-triggered, and low-frequency), direct API calls via the adapter pattern are simpler, more reliable, and more auditable.

**MCP enters for AI in Phase 5** — when Architecture Intelligence requires multi-model coordination, streaming responses, and persistent context across sessions. That use case justifies MCP complexity. Phase 4 diagnostics do not.

**The `.mcp/` infrastructure is prepared but not populated for AI in Phase 4.** A placeholder entry is added to `.mcp/registry/servers.md` documenting Phase 5 intent.

---

## The AI Boundary (ADR-007 Operationalized)

This boundary is load-bearing. It must be enforced by design, not by convention.

```
AI may:
  ✓ Read evidence from state.db (via EvidenceCollector)
  ✓ Analyze evidence and return DiagnosticResult
  ✓ Recommend actions (stored in DiagnosticResult.recommended_actions)
  ✓ Summarize logs and contract violations
  ✓ Classify failure types

AI may not:
  ✗ Write to state.db
  ✗ Execute any pipeline command
  ✗ Modify pipelinekit.yaml
  ✗ Access credentials or API keys (other than its own)
  ✗ Make network calls outside its own provider API
  ✗ Set can_auto_fix = True without an ADR authorizing it
```

`can_auto_fix` in `DiagnosticResult` is always `False` in Phase 4.  
No code path exists in Phase 4 that auto-executes a recommended action.  
Architectural Smell 13 (Observer Becomes Actor) governs this permanently.

---

## Schema Validation as Trust Boundary

Every AI response is validated against `schemas/diagnostic.schema.json` before it reaches the CLI.

This is not optional. It is the mechanism that prevents hallucinated, malformed, or dangerous AI output from reaching the user.

If validation fails → `LLMError(PK-AI-002)` is raised.  
The user sees a clean error, not raw AI output.  
The failure is recorded in state.db for future diagnosis.

---

## Confidence Threshold

AI confidence is a first-class concept in Phase 4.

- Results above threshold (`default: 0.7`) → `status: "diagnosed"`
- Results below threshold → `status: "inconclusive"` — still shown, never suppressed
- Threshold is configurable per project via `pipelinekit.yaml`
- `PK-AI-003` is raised when confidence is below threshold AND the user requested high-confidence only

Inconclusive diagnoses are honest. They tell the user "the AI found evidence but is not certain." That is more trustworthy than false confidence.

---

## BYOK (ADR-005 Application)

All AI provider keys are customer-provided via environment variables:

```
ANTHROPIC_API_KEY
OPENAI_API_KEY
OLLAMA_HOST
```

PipelineKit never stores, logs, transmits, or manages API keys.  
Keys are read at runtime from environment only.  
If a key is missing → `LLMError(PK-AI-001)` with a clear message: "Set ANTHROPIC_API_KEY to use the Anthropic provider."

---

## Alternatives Considered

**Single provider (Anthropic only)**  
Rejected — locks customers into one vendor. ADR-005 (BYOK) and the provider-replaceable architecture require multiple options.

**LangChain or similar framework**  
Rejected — adds significant dependency weight, abstracts the provider boundary in ways that are hard to audit, and conflicts with the principle of explicit interfaces over hidden behavior. Direct provider SDKs behind the LLMProvider Protocol is cleaner and more auditable.

**MCP for all AI provider access in Phase 4**  
Rejected — Phase 4 diagnostics are synchronous and user-triggered. MCP complexity is not justified until Phase 5 multi-model coordination. See MCP governance section above.

**Auto-execution of low-risk recommended actions**  
Rejected — even "low risk" auto-execution requires the user to understand what was changed and why. The audit trail and human approval pattern is more important than convenience. This can be revisited in Phase 5 with an explicit ADR (ADR-016) and a reversibility mechanism.

---

## Consequences

### Benefits
- AI diagnostics are auditable — evidence, output, and approval all recorded in state.db
- Providers are replaceable — switching from OpenAI to Anthropic is one config change
- Schema validation prevents AI hallucination from reaching the user
- BYOK maintains customer data sovereignty
- Ollama support serves air-gapped enterprise customers who cannot use cloud APIs

### Limitations
- No auto-fix in Phase 4 — every recommendation requires manual execution
- Three provider SDKs add dependency weight to pyproject.toml
- Local Ollama requires the customer to run and maintain Ollama
- Diagnostic quality depends on evidence richness — early customers with sparse state.db history will get less precise diagnoses

### Phase 5 Implications
- `can_auto_fix` will be revisited in ADR-016 when Phase 5 begins
- MCP-based AI coordination will be specified in ADR-015 (Architecture Intelligence)
- Model fine-tuning on customer pipeline patterns is a Phase 5+ capability

---

## Principle Alignment

- ADR-005 (BYOK) — customer provides all API keys
- ADR-007 (AI is Operator not Owner) — recommendations only, human approval required
- ADR-008 (Deterministic Before AI) — evidence from deterministic systems, AI interprets
- ADR-009 (Human-Readable) — diagnostic output is plain English, not JSON blobs
- ADR-010 (Explainability Before Automation) — explanation always shown before recommended actions
- Architectural Smell 7 — MCP without ADR — Phase 4 AI uses direct APIs, not MCPs. Phase 5 MCP will require ADR-015
- Architectural Smell 13 — Observer Becomes Actor — AI observes evidence, never executes
