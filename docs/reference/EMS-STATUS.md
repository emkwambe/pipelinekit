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

### QM — Quality Management
| Capability | Code | Status |
|---|---|---|
| Source and transform quality checks | QM-1..3 | ✅ v0.1.0 |
| Coverage monitoring | QM-4 | ✅ Phase 2 |
| Volume anomaly detection | QM-6 | ✅ Phase 2 |

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

### AM — Architecture Management
| Capability | Code | Status |
|---|---|---|
| ADR templates, blueprint validation | AM-1..3 | ✅ v0.1.0 |
| Dependency analysis | AM-4 | ✅ Phase 2 |

### AI — AI Management
| Capability | Code | Status |
|---|---|---|
| Blueprint generation, diagnostics | AI-1..6 | ✅ v0.1.0 |

### RM — Release Management
| Capability | Code | Status |
|---|---|---|
| Release coordination | RM-1..3 | ✅ v0.1.0 |

## Roadmap (Phase 2 continuing)
- QM-7: Schema drift detection
- QM-8: Quality scorecard
- OM-5: SLO dashboard
- AM-5+: Architecture drift detection
