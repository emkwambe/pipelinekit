# PipelineKit — Sustainability Policy

**File:** `docs/reference/Sustainability-Policy.md`  
**Owner:** Command Center + Eddy (Founder)  
**Status:** Approved  
**Version:** 2.0 — DeepSeek + Mistral added (ADR-016); health command system added (SPEC-012)  
**Date:** June 25, 2026  
**Review Cadence:** Quarterly

---

## Why This Document Exists

PipelineKit has deep dependency surface across five layers:

```
Python runtime        (3.13+)
Core framework        (Typer, Pydantic v2, Rich, PyYAML)
Data layer            (dlt 1.28, dbt-core 1.x, soda-core 3.x)
AI providers          (openai, anthropic, deepseek, mistral, ollama)
Notification          (resend ^2.0)
Validation            (jsonschema ^4.0)
Dev tooling           (pytest, ruff, black, mypy, poetry, pip-audit)
```

This policy defines the habits, cadences, and decision rules that keep PipelineKit healthy. It exists in two forms: this document (the policy) and `pipelinekit health` (the programmed enforcement). Both must stay in sync.

---

## The Programmed Policy — pipelinekit health

Every maintenance habit in this document has a corresponding CLI command:

| Habit | Command | Cadence |
|---|---|---|
| Check outdated deps | `pipelinekit health deps` | Monthly |
| Check security advisories | `pipelinekit health security` | Monthly |
| Validate blueprints | `pipelinekit health blueprints` | Monthly |
| Check SPEC drift | `pipelinekit health specs` | After each phase |
| Verify test suite | `pipelinekit health tests` | Before any release |
| Full health summary | `pipelinekit health` | Quarterly |

See SPEC-012 for the full implementation specification.

---

## 1. Dependency Governance

### The Dependency Tiers

| Tier | Examples | Policy |
|---|---|---|
| **Core** | typer, pydantic, rich, pyyaml | Pin minor, allow patch. Review on every minor release. |
| **Data providers** | dlt, dbt-core, soda-core | Pin minor. Test before upgrading. Breaking changes require ADR. |
| **AI providers** | openai, anthropic, deepseek, mistral, ollama | Pin minor. Test each upgrade in isolation. Breaking changes are frequent. |
| **Notification** | resend | Pin minor. Test against live Resend sandbox before upgrading. |
| **Dev tooling** | pytest, ruff, black, mypy, poetry, pip-audit | Allow minor upgrades. Run full gate before merging. |
| **Python runtime** | Python 3.13+ | Upgrade only when a new LTS is stable AND all tier 1–3 deps support it. |

### The Pinning Rule

```toml
dlt = "^1.28"        # >=1.28, <2.0
openai = "^1.0"
anthropic = "^0.25"
deepseek = "^1.0"    # Phase 5 addition
mistral = "^1.0"     # Phase 5 addition — mistralai SDK
pydantic = "^2.0"
```

Never use `*` or unbounded `>=` for data or AI provider dependencies.

---

## 2. AI Provider Diversity (ADR-016)

PipelineKit must always offer at least one provider in each category:

| Category | Providers | Data Residency |
|---|---|---|
| US-based cloud | OpenAI, Anthropic | United States |
| EU-based cloud | Mistral | France (GDPR compliant) |
| Asia-based cloud | DeepSeek | China |
| Local/air-gapped | Ollama | Customer-controlled |
| Phase 6 candidate | Kimi (Moonshot AI) | China — deferred |

### Provider Model Defaults

| Provider | Default Model | Review Trigger |
|---|---|---|
| Anthropic | claude-sonnet-4-6 | New Sonnet/Opus release |
| OpenAI | gpt-4o | New GPT-4 class release |
| DeepSeek | deepseek-v3 | New V-series release |
| Mistral | mistral-large-latest | New Large release |
| Ollama | llama3 | New Llama major version |

**Model upgrade rule:** Test 10 synthetic evidence packages through new model. Compare `DiagnosticResult` schema compliance rate against current default. Only upgrade if compliance is equal or better.

### Provider Data Residency — Customer Responsibility

PipelineKit documents data residency per provider. Customers are responsible for ensuring their chosen provider complies with their regulatory requirements. PipelineKit does not enforce this — it informs.

---

## 3. Upgrade Cadence

### Monthly (first Monday of each month)

```powershell
cd C:\Users\HP\Documents\pipelinekit
poetry run pipelinekit health deps
poetry run pipelinekit health security
poetry run pipelinekit health blueprints
```

Review results. Upgrade dev tooling and patch versions if clean.

### Quarterly (every 3 months)

```powershell
poetry run pipelinekit health
```

Full health check. Review all tier 1–3 minor versions. Test provider SDK upgrades in isolation. Update version pins if tests pass. Review Python runtime.

### On Security Advisory (immediate)

```powershell
poetry run pip-audit
```

HIGH/CRITICAL → patch within 48 hours.  
MEDIUM → patch within 2 weeks.  
LOW → include in next monthly cycle.

---

## 4. AI Provider SDK Upgrade Protocol

AI SDKs release breaking changes frequently. The adapter isolation pattern means upgrades only touch one file per provider.

```
anthropic ^0.25 → ^1.0:
  Edit: src/pipelinekit/ai/providers/anthropic.py only
  Test: poetry run pytest tests/ai/providers/test_anthropic.py
  Full gate: poetry run pytest
  Commit: chore: upgrade anthropic SDK to ^1.0
```

Same pattern for openai, deepseek, mistral, ollama.

---

## 5. dlt / dbt / Soda Upgrade Protocol

**dlt:** Test against DuckDB first (local, no credentials). If clean → test against Snowflake in staging. Only `adapters/ingestion/dlt/adapter.py` changes.

**dbt-core:** Check release notes for `run_results.json` schema changes. Only `adapters/transformation/dbt/adapter.py` changes.

**Blueprint #001 is the canary:** If it deploys cleanly after an upgrade, the upgrade is safe.

---

## 6. Architecture Evolution Rules

### When to Write a New ADR

| Trigger | Action |
|---|---|
| New major dependency version | ADR required |
| New MCP | ADR required |
| New AI provider | ADR required (ADR-016 pattern) |
| `can_auto_apply = True` | ADR-017 required |
| New CLI command within existing SPEC | No ADR needed |
| New blueprint | No ADR needed |
| Contract file change | Version bump + ADR if breaking |

### SPEC Maintenance

Run `pipelinekit health specs` after every phase to detect status drift.  
Fix drift in the same session — never carry stale SPEC status into a new phase.

---

## 7. Version Roadmap

| Version | Target | Status |
|---|---|---|
| 0.1.0 | Phase 1 Foundation | ✅ Done |
| 0.2.0 | Phase 2 Data Layer | ✅ Done |
| 0.3.0 | Phase 3 Trust Layer | ✅ Done |
| 0.4.0 | Phase 4 Intelligence | ✅ Done |
| 0.5.0 | Phase 5 Architecture + Health | ⏳ Current |
| 1.0.0 | First design partner live | After beta validation |
| 1.1.0 | Blueprint #002 (Salesforce → Snowflake) | Phase 6 |
| 2.0.0 | Architecture Intelligence GA | After Phase 5 beta |

---

## 8. The Sustainability Habits — Summary

**Daily:** Nothing required.

**Weekly (active development):**
- Run full quality gate before any commit to main
- Check CI status on GitHub

**Monthly:**
- `pipelinekit health deps`
- `pipelinekit health security`
- `pipelinekit health blueprints`
- Environment health check (`python --version`, `poetry --version`)

**Quarterly:**
- `pipelinekit health` — full check
- AI model version review
- Architectural smells review (all 16)
- Update HANDOVER document

**Every phase completion:**
- Update PROJECT-STATUS.md
- Update HANDOVER document
- `pipelinekit health specs` — fix drift
- Run full quality gate

**Before every design partner demo:**
- Fresh `poetry install`
- Blueprint #001 end-to-end deploy
- `pipelinekit diagnose` smoke test (mocked provider)
- All 4 quality gates green
- `pipelinekit health` — all checks pass

---

## CHANGELOG

| Date | Version | Change |
|---|---|---|
| 2026-06-25 | 1.0 | Document created |
| 2026-06-25 | 2.0 | DeepSeek + Mistral added (ADR-016); health command system added (SPEC-012); Kimi deferred to Phase 6 |
