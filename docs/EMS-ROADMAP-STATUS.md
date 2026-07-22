# EMS Capability Status — PipelineKit
Last updated: June 29, 2026  
Tests passing: 343  
Active domains: 6 / 12  
Capabilities built: 22 / 109

## Status key
- ✅ Built — shipped and verified with passing tests
- 🔵 Ready — sprint package exists in C:\Users\HP\Downloads\
- ⬜ Queued — planned, no package yet
- ⬛ Not started — domain not yet begun

---

## DC — Data Contract Management (EMS-008)

| Capability | Code | Status | Sprint | Tests | Commit |
|---|---|---|---|---|---|
| Contract definition | DC-1 | ✅ Built | v0.1.0 | — | foundation |
| Contract validation | DC-2 | ✅ Built | v0.1.0 | — | foundation |
| Not-null enforcement | DC-3 | ✅ Built | v0.1.0 | — | foundation |
| Uniqueness enforcement | DC-4 | ✅ Built | v0.1.0 | — | foundation |
| Accepted values | DC-5 | ✅ Built | v0.1.0 | — | foundation |
| Row count enforcement | DC-6 | ✅ Built | v0.1.0 | — | foundation |
| Freshness enforcement | DC-7 | ✅ Built | v0.1.0 | — | foundation |
| Schema versioning | DC-8 | ✅ Built | Sprint 1 | +8 (315) | 1e4c4c9 |
| Breaking change detection | DC-9 | ✅ Built | Sprint 2 | +9 (324) | 3efeb9d |
| Consumer notification | DC-10 | 🔵 Ready | Sprint 8 | est. +9 | — |
| Contract lifecycle | DC-11 | ⬜ Queued | — | — | — |
| Producer/consumer registry | DC-12 | ⬜ Queued | — | — | — |

---

## QM — Quality Management (EMS-002)

| Capability | Code | Status | Sprint | Tests | Commit |
|---|---|---|---|---|---|
| Source quality checks | QM-1 | ✅ Built | v0.1.0 | — | foundation |
| Transform quality gates | QM-2 | ✅ Built | v0.1.0 | — | foundation |
| CI quality pipeline | QM-3 | ✅ Built | v0.1.0 | — | foundation |
| Coverage monitoring | QM-4 | ✅ Built | Sprint 3 | +10 (334) | 2a12756 |
| Freshness SLA | QM-5 | ⬜ Queued | — | — | — |
| Volume anomaly detection | QM-6 | 🔵 Ready | Sprint 5 | est. +10 | — |
| Schema drift detection | QM-7 | 🔵 Ready | Sprint 10 | est. +9 | — |
| Quality scorecard | QM-8 | 🔵 Ready | Sprint 11 | est. +9 | — |
| Regression testing | QM-9 | ⬜ Queued | — | — | — |

---

## AI — AI Management (EMS-010)

| Capability | Code | Status | Sprint | Tests | Commit |
|---|---|---|---|---|---|
| AI provider abstraction | AI-1 | ✅ Built | v0.1.0 | — | foundation |
| Blueprint generation | AI-2 | ✅ Built | v0.1.0 | — | foundation |
| Diagnostics engine | AI-3 | ✅ Built | v0.1.0 | — | foundation |
| Confidence scoring | AI-4 | ✅ Built | v0.1.0 | — | foundation |
| AI trust model | AI-5 | ✅ Built | v0.1.0 | — | foundation |
| Multi-provider routing | AI-6 | ✅ Built | v0.1.0 | — | foundation |
| Confidence improvement | AI-7 | ⬜ Queued | — | — | — |
| AI audit trail | AI-8 | ⬜ Queued | — | — | — |
| AI-9 through AI-12 | AI-9+ | ⬜ Queued | — | — | — |

---

## GM — Governance Management (EMS-001)

| Capability | Code | Status | Sprint | Tests | Commit |
|---|---|---|---|---|---|
| Ownership assignment | GM-1 | ✅ Built | Sprint 4 | +9 (343) | ffe01f2 |
| Naming conventions | GM-2 | 🔵 Ready | Sprint 9 | est. +9 | — |
| Approval workflow | GM-3 | 🔵 Ready | Sprint 12 | est. +9 | — |
| GM-4 through GM-6 | GM-4+ | ⬜ Queued | — | — | — |
| GM-7 through GM-9 | GM-7+ | ⬜ Queued | — | — | — |

---

## AM — Architecture Management (EMS-004)

| Capability | Code | Status | Sprint | Tests | Commit |
|---|---|---|---|---|---|
| ADR templates | AM-1 | ✅ Built | v0.1.0 | — | foundation |
| Blueprint validation | AM-2 | ✅ Built | v0.1.0 | — | foundation |
| Architecture patterns | AM-3 | ✅ Built | v0.1.0 | — | foundation |
| Dependency analysis | AM-4 | 🔵 Ready | Sprint 7 | est. +9 | — |
| AM-5 through AM-6 | AM-5+ | ⬜ Queued | — | — | — |
| AM-7 through AM-8 | AM-7+ | ⬜ Queued | — | — | — |

---

## OM — Observability Management (EMS-006)

| Capability | Code | Status | Sprint | Tests | Commit |
|---|---|---|---|---|---|
| Health check | OM-1 | ✅ Built | v0.1.0 | — | foundation |
| Slack alerting | OM-2 | ✅ Built | v0.1.0 | — | foundation |
| Email alerting | OM-3 | ✅ Built | v0.1.0 | — | foundation |
| SLO definition | OM-4 | 🔵 Ready | Sprint 6 | est. +10 | — |
| OM-5 through OM-6 | OM-5+ | ⬜ Queued | — | — | — |
| OM-7 through OM-9 | OM-7+ | ⬜ Queued | — | — | — |

---

## RM — Release Management (EMS-012)

| Capability | Code | Status | Sprint | Tests | Commit |
|---|---|---|---|---|---|
| RM-1 through RM-3 | RM-1+ | ✅ Built | v0.1.0 | — | foundation |
| RM-4 through RM-6 | RM-4+ | ⬜ Queued | — | — | — |
| RM-7 through RM-8 | RM-7+ | ⬜ Queued | — | — | — |

---

## Tier 3 — Not yet started

| Domain | Code | Capabilities | Target phase |
|---|---|---|---|
| Compliance Management | CM | 10 | Phase 3 |
| Knowledge Management | KM | 9 | Phase 3 |
| Security Management | SM | 7 | Phase 3 |
| Cost Management | CO | 8 | Phase 3 |
| Documentation Management | DM | 8 | Phase 3 |

---

## Update instructions

After each sprint verification passes:
1. Change status from 🔵 Ready → ✅ Built
2. Fill in Sprint column
3. Fill in Tests column (exact number in parentheses)
4. Fill in Commit column (first 7 chars)
5. Update "Tests passing" count at top of file
6. Commit: `docs: update EMS status — [capability code] complete`
