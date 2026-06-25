# SPEC-005-AI-Diagnostics.md

**Status:** Placeholder
**Owner:** diagnostics-engineer
**Phase:** 4 — Intelligence Layer
**Activation:** When Phase 4 sprint begins and ADR-014 is committed to main
**ADRs:** ADR-007 (AI is Operator not Owner), ADR-014 (AI provider MCP layer — to write)
**Schemas:** schemas/diagnostic.schema.json

---

## Purpose

Define the AI diagnostics subsystem for PipelineKit Phase 4. This SPEC will specify
the LLMProvider Protocol, EvidenceCollector, DiagnosticsEngine, and `pipelinekit diagnose`
CLI command that together deliver AI-assisted root cause analysis for pipeline failures.

## Phase 4 Preview — What Will Be Built

- `src/pipelinekit/ai/provider.py` — LLMProvider Protocol (interface, not concrete provider)
- `src/pipelinekit/ai/evidence.py` — EvidenceCollector (reads state.db, assembles diagnostic context)
- `src/pipelinekit/ai/diagnostics.py` — DiagnosticsEngine (orchestrates evidence → LLM → validated output)
- `src/pipelinekit/ai/providers/openai.py` — OpenAI adapter
- `src/pipelinekit/ai/providers/anthropic.py` — Anthropic adapter
- `src/pipelinekit/ai/providers/ollama.py` — Ollama adapter (local/air-gapped enterprise)
- `src/pipelinekit/cli/diagnose.py` — `pipelinekit diagnose` command
- `.mcp/servers/` — full AI provider MCP layer

## Critical Constraint — AI Boundary (ADR-007)

AI may: inspect, diagnose, recommend, summarize, classify, generate
AI may not: deploy, delete, migrate, modify production, rotate secrets, approve releases

Every AI recommendation requires explicit human approval before any production action.
This boundary is enforced by design — the DiagnosticsEngine returns recommendations only.
Execution paths are not exposed to the AI layer.

## Diagnostic Schema

All AI output must validate against `schemas/diagnostic.schema.json`.
This schema is already defined. The DiagnosticsEngine must reject any output that fails validation.

## Full SPEC

To be written by Command Center before Phase 4 sprint prompt is sent to Claude Code.