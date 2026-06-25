# ADR-016: AI Provider Diversity Policy

**Status:** Accepted  
**Date:** June 25, 2026  
**Phase:** 5 — Architecture Layer (immediate) + Phase 6 (Kimi)  
**ADR Number:** 016  
**Governs:** `src/pipelinekit/ai/providers/`, provider selection in `pipelinekit.yaml`

---

## Context

PipelineKit's initial three AI providers (OpenAI, Anthropic, Ollama) are all US-headquartered or US-aligned. This creates three real risks:

1. **Data sovereignty** — enterprises in regulated markets (EU, East Africa, Southeast Asia) cannot send diagnostic evidence to US-based APIs without legal review
2. **Cost accessibility** — US API pricing is prohibitive in many markets PipelineKit targets, particularly ICP-004 Mixed-Stack Enterprises in emerging markets
3. **Vendor concentration** — three providers from one regulatory jurisdiction is a single point of geopolitical risk

PipelineKit's governing principle — *the AI-native operating system for trusted analytics pipelines* — requires that "trusted" applies to the AI layer itself. A diagnostic engine that can only be trusted by US-based organizations is not a trusted analytics operating system.

---

## Decision

**Add DeepSeek and Mistral as Phase 5 providers. Maintain Kimi (Moonshot AI) as a Phase 6 candidate pending SDK maturity validation.**

**Establish the Provider Diversity Rule: PipelineKit must always offer at least one non-US-headquartered AI provider option at every tier.**

---

## Provider Assessment

### DeepSeek — Phase 5 ✅

**Headquarters:** China (DeepSeek AI)  
**Models:** DeepSeek-V3, DeepSeek-R1  
**Technical fit:** Excellent — DeepSeek-V3 demonstrates strong structured JSON output, which is the primary requirement for `DiagnosticResult` and `ArchitectureResult` schema compliance. R1 adds chain-of-thought reasoning suitable for architectural analysis.  
**SDK:** `deepseek` Python SDK available, clean API compatible with OpenAI client pattern  
**Key variable:** `DEEPSEEK_API_KEY`  
**Data residency:** API calls processed in China — document clearly for enterprise customers  
**Verdict:** Add in Phase 5

### Mistral — Phase 5 ✅

**Headquarters:** France (EU)  
**Models:** Mistral Large, Mistral Medium  
**Technical fit:** Strong — EU data residency satisfies GDPR requirements. Mistral Large handles structured output reliably. Open weights (Apache 2.0) available via Ollama for air-gapped deployments.  
**SDK:** `mistralai` Python SDK, clean and stable  
**Key variable:** `MISTRAL_API_KEY`  
**Data residency:** EU (France) — GDPR compliant by design  
**Verdict:** Add in Phase 5

### Kimi (Moonshot AI) — Phase 6 📋

**Headquarters:** China (Moonshot AI)  
**Models:** moonshot-v1-128k, moonshot-v1-8k  
**Technical fit:** Partial — exceptional long context (128k tokens) suits evidence-heavy diagnostics. English structured JSON output reliability less validated than DeepSeek or Mistral at time of this ADR.  
**SDK:** Available but less mature than the Phase 5 candidates  
**Verdict:** Defer to Phase 6 — re-evaluate SDK maturity and structured output quality

---

## The Provider Diversity Rule

At every phase, PipelineKit must offer:

| Category | Requirement | Current |
|---|---|---|
| US-based cloud | At least one | OpenAI, Anthropic ✅ |
| Non-US cloud | At least one | DeepSeek (CN), Mistral (EU) ✅ |
| Local/air-gapped | At least one | Ollama ✅ |

This rule is enforced by policy — not by code. Any PR that removes the last non-US provider must include an ADR explaining why.

---

## Implementation

Two new files in `src/pipelinekit/ai/providers/`:

```
deepseek.py    DeepSeekProvider — implements LLMProvider Protocol
mistral.py     MistralProvider  — implements LLMProvider Protocol
```

Both follow the exact same pattern as `anthropic.py` and `openai.py`:
- All provider imports isolated inside the file
- API key from environment variable only
- `diagnose()` + `summarize()` + `recommend()` + `architect()` implemented
- Schema validation enforced — invalid output raises `LLMError(PK-AI-002)`
- `can_auto_fix` and `can_auto_apply` always corrected to False

Updated `pipelinekit.yaml` provider options:
```yaml
diagnostics:
  provider: anthropic  # openai | anthropic | ollama | deepseek | mistral
```

---

## Documentation Requirement

Every provider must document its data residency in its adapter file docstring:

```python
class DeepSeekProvider:
    """DeepSeek AI provider.

    Data residency: China (DeepSeek AI servers).
    Suitable for: cost-sensitive deployments, Asian market customers.
    Not suitable for: deployments with EU GDPR or US FedRAMP requirements.
    API key: DEEPSEEK_API_KEY environment variable.
    """
```

This is the trust principle applied to the AI layer itself.

---

## Consequences

### Benefits
- East African and Asian market customers have a cost-effective, regionally appropriate provider
- EU customers have a GDPR-compliant provider (Mistral)
- Air-gapped enterprises retain Ollama
- Provider diversity reduces geopolitical concentration risk

### Limitations
- Two new provider files add maintenance surface
- DeepSeek API availability can be intermittent during high demand periods
- Data residency documentation responsibility falls on the user — PipelineKit documents, but cannot enforce customer compliance

---

## Principle Alignment

- ADR-005 (BYOK) — customer provides all API keys
- ADR-007 (AI is Operator not Owner) — same boundary applies to all providers
- ADR-009 (Human-Readable) — provider data residency documented in plain English
- Governing Principle — "trusted" must apply globally, not just in US markets
