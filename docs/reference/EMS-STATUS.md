# PipelineKit — EMS Capability Status

Public-facing status of PipelineKit's EMS (Engineering Management System) capabilities. Each capability maps to a versioned SPEC and ADR in the internal roadmap.

## Built and verified (as of July 2026)

### DC — Data Contract Management
| Capability | Code | Status |
|---|---|---|
| Contract definition and validation | DC-1..7 | ✅ v0.1.0 |
| Schema versioning | DC-8 | ✅ Phase 2 |
| Breaking change detection | DC-9 | ✅ Phase 2 |
| Consumer notification | DC-10 | ✅ Phase 2 |
| Contract lifecycle management | DC-11 | ✅ Phase 3 |

### QM — Quality Management
| Capability | Code | Status |
|---|---|---|
| Source and transform quality checks | QM-1..3 | ✅ v0.1.0 |
| Coverage monitoring | QM-4 | ✅ Phase 2 |
| Freshness SLA enforcement | QM-5 | ✅ Phase 3 |
| Volume anomaly detection | QM-6 | ✅ Phase 2 |
| Schema drift detection | QM-7 | ✅ Phase 2 |
| Quality scorecard | QM-8 | ✅ Phase 2 |
| Quality regression testing | QM-9 | ✅ Phase 3 |

### GM — Governance Management
| Capability | Code | Status |
|---|---|---|
| Ownership assignment | GM-1 | ✅ Phase 2 |
| Naming convention enforcement | GM-2 | ✅ Phase 2 |
| Approval workflow | GM-3 | ✅ Phase 2 |

### OM — Observability Management
| Capability | Code | Status |
|---|---|---|
| Health check, Slack, email alerting | OM-1..3 | ✅ v0.1.0 |
| SLO definition and evaluation | OM-4 | ✅ Phase 2 |
| SLO compliance dashboard | OM-5 | ✅ Phase 3 |

### AM — Architecture Management
| Capability | Code | Status |
|---|---|---|
| ADR templates, blueprint validation | AM-1..3 | ✅ v0.1.0 |
| Dependency analysis | AM-4 | ✅ Phase 2 |
| Architecture drift detection | AM-5 | ✅ Phase 3 |

### AI — AI Management
| Capability | Code | Status |
|---|---|---|
| Blueprint generation, diagnostics | AI-1..6 | ✅ v0.1.0 |
| Prompt governance | AI-7 | 📋 Planned (Phase 4) |
| Agent registry | AI-8 | 📋 Planned (Phase 4) |
| Evaluation pipeline | AI-9 | 📋 Planned (Phase 4) |
| EMS context injection | AI-13 | ✅ Phase 3 |
| Scorecard narrative | AI-14 | ✅ Phase 3 |
| EMS-aware confidence recalibration | AI-15 | ✅ Phase 3 |

Six AI providers are supported — Anthropic, OpenAI, Kimi (Moonshot AI), DeepSeek, Mistral, and Ollama (local) — with an ordered provider cascade (primary + fallbacks) for resilience and large-context routing.

### RM — Release Management
| Capability | Code | Status |
|---|---|---|
| Release coordination | RM-1..3 | ✅ v0.1.0 |

## Roadmap
Phase 3 capabilities (QM-9, OM-5, DC-11, AM-5, AI-13/14/15) are complete; no
capability is currently queued. New capabilities enter through the ADR process
(Constitution → ADR → SPEC → Contract → Schema), not this list.
