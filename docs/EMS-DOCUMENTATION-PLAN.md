# PipelineKit EMS Documentation Plan
## Instructions for Claude Code

**Date:** June 29, 2026  
**Owner:** Eddy Mkwambe  
**Purpose:** Commit the EMS roadmap diagram to the public repo and
maintain it as capabilities are built.

---

## Part 1 — What to commit

The EMS roadmap diagram lives in two places:

```
pipelinekit (public repo):
  docs/diagrams/ems-roadmap.mmd        ← Mermaid source (human-readable)
  docs/diagrams/ems-roadmap.svg        ← Rendered SVG (GitHub renders this)

pipelinekit-internal (private repo):
  reference/EMS-ROADMAP-STATUS.md      ← Capability status table (authoritative)
```

---

## Part 2 — EMS-ROADMAP-STATUS.md (authoritative capability table)

Save this file to `pipelinekit-internal/reference/EMS-ROADMAP-STATUS.md`:

```markdown
# EMS Capability Status — PipelineKit
Last updated: June 29, 2026

## Status key
✅ Built     — shipped and verified with passing tests
🔵 Ready     — sprint package exists in C:\Users\HP\Downloads\
⬜ Queued    — planned, no package yet
⬛ Not started — domain not yet begun

## Domain: DC — Data Contract Management (EMS-008)
| Capability | Code  | Status  | Sprint | Tests added | Commit  |
|---|---|---|---|---|---|
| Contract definition      | DC-1  | ✅ Built  | v0.1.0 | — | foundation |
| Contract validation      | DC-2  | ✅ Built  | v0.1.0 | — | foundation |
| Not-null enforcement     | DC-3  | ✅ Built  | v0.1.0 | — | foundation |
| Uniqueness enforcement   | DC-4  | ✅ Built  | v0.1.0 | — | foundation |
| Accepted values          | DC-5  | ✅ Built  | v0.1.0 | — | foundation |
| Row count enforcement    | DC-6  | ✅ Built  | v0.1.0 | — | foundation |
| Freshness enforcement    | DC-7  | ✅ Built  | v0.1.0 | — | foundation |
| Schema versioning        | DC-8  | ✅ Built  | Sprint 1 | +8 (315 total) | 1e4c4c9 |
| Breaking change detect   | DC-9  | ✅ Built  | Sprint 2 | +9 (324 total) | [dc9-hash] |
| Consumer notification    | DC-10 | 🔵 Ready  | Sprint 8 | est. +9 | — |
| Contract lifecycle       | DC-11 | ⬜ Queued | — | — | — |
| Producer/consumer reg    | DC-12 | ⬜ Queued | — | — | — |

## Domain: QM — Quality Management (EMS-002)
| Capability | Code  | Status  | Sprint | Tests added | Commit  |
|---|---|---|---|---|---|
| Source quality checks    | QM-1  | ✅ Built  | v0.1.0 | — | foundation |
| Transform quality gates  | QM-2  | ✅ Built  | v0.1.0 | — | foundation |
| CI quality pipeline      | QM-3  | ✅ Built  | v0.1.0 | — | foundation |
| Coverage monitoring      | QM-4  | ✅ Built  | Sprint 3 | +10 (334 total) | 2a12756 |
| Freshness SLA            | QM-5  | ⬜ Queued | — | — | — |
| Volume anomaly detection | QM-6  | 🔵 Ready  | Sprint 5 | est. +10 | — |
| Schema drift detection   | QM-7  | 🔵 Ready  | Sprint 10 | est. +9 | — |
| Quality scorecard        | QM-8  | 🔵 Ready  | Sprint 11 | est. +9 | — |
| Regression testing       | QM-9  | ⬜ Queued | — | — | — |

## Domain: AI — AI Management (EMS-010)
| Capability | Code  | Status  | Sprint | Tests added | Commit  |
|---|---|---|---|---|---|
| AI provider abstraction  | AI-1  | ✅ Built  | v0.1.0 | — | foundation |
| Blueprint generation     | AI-2  | ✅ Built  | v0.1.0 | — | foundation |
| Diagnostics engine       | AI-3  | ✅ Built  | v0.1.0 | — | foundation |
| Confidence scoring       | AI-4  | ✅ Built  | v0.1.0 | — | foundation |
| AI trust model           | AI-5  | ✅ Built  | v0.1.0 | — | foundation |
| Multi-provider routing   | AI-6  | ✅ Built  | v0.1.0 | — | foundation |
| Confidence improvement   | AI-7  | ⬜ Queued | — | — | — |
| AI audit trail           | AI-8  | ⬜ Queued | — | — | — |
| AI-9 through AI-12       | AI-9+ | ⬜ Queued | — | — | — |

## Domain: GM — Governance Management (EMS-001)
| Capability | Code  | Status  | Sprint | Tests added | Commit  |
|---|---|---|---|---|---|
| Ownership assignment     | GM-1  | ✅ Built  | Sprint 4 | +9 (343 total) | ffe01f2 |
| Naming conventions       | GM-2  | 🔵 Ready  | Sprint 9 | est. +9 | — |
| Approval workflow        | GM-3  | 🔵 Ready  | Sprint 12 | est. +9 | — |
| GM-4 through GM-9        | GM-4+ | ⬜ Queued | — | — | — |

## Domain: AM — Architecture Management (EMS-004)
| Capability | Code  | Status  | Sprint | Tests added | Commit  |
|---|---|---|---|---|---|
| ADR templates            | AM-1  | ✅ Built  | v0.1.0 | — | foundation |
| Blueprint validation     | AM-2  | ✅ Built  | v0.1.0 | — | foundation |
| Architecture patterns    | AM-3  | ✅ Built  | v0.1.0 | — | foundation |
| Dependency analysis      | AM-4  | 🔵 Ready  | Sprint 7 | est. +9 | — |
| AM-5 through AM-8        | AM-5+ | ⬜ Queued | — | — | — |

## Domain: OM — Observability Management (EMS-006)
| Capability | Code  | Status  | Sprint | Tests added | Commit  |
|---|---|---|---|---|---|
| Health check             | OM-1  | ✅ Built  | v0.1.0 | — | foundation |
| Slack alerting           | OM-2  | ✅ Built  | v0.1.0 | — | foundation |
| Email alerting           | OM-3  | ✅ Built  | v0.1.0 | — | foundation |
| SLO definition           | OM-4  | 🔵 Ready  | Sprint 6 | est. +10 | — |
| OM-5 through OM-9        | OM-5+ | ⬜ Queued | — | — | — |

## Domain: RM — Release Management (EMS-012)
| Capability | Code  | Status | Sprint | Tests added | Commit |
|---|---|---|---|---|---|
| RM-1 through RM-3        | RM-1+ | ✅ Built | v0.1.0 | — | foundation |
| RM-4 through RM-8        | RM-4+ | ⬜ Queued | — | — | — |

## Domains not yet started
| Domain | Code | Capabilities | Target phase |
|---|---|---|---|
| Compliance Management | CM | 10 | Phase 3 |
| Knowledge Management  | KM | 9  | Phase 3 |
| Security Management   | SM | 7  | Phase 3 |
| Cost Management       | CO | 8  | Phase 3 |
| Documentation Mgmt    | DM | 8  | Phase 3 |
```

---

## Part 3 — Claude Code instructions

### Task: Commit EMS status doc to private repo

```powershell
# Run this in PowerShell (not Claude Code — just copy-paste)
Copy-Item "C:\Users\HP\Downloads\EMS-ROADMAP-STATUS.md" `
    "C:\Users\HP\Documents\pipelinekit-internal\reference\"

cd C:\Users\HP\Documents\pipelinekit-internal
git add reference\EMS-ROADMAP-STATUS.md
git commit -m "docs: EMS capability status table — June 29 2026 baseline"
git push origin main
```

---

### Task: Add EMS diagram to public repo docs/diagrams/

Open a fresh Claude Code session in `C:\Users\HP\Documents\pipelinekit`
and paste this prompt:

---

**CLAUDE CODE PROMPT — EMS Diagram Documentation**

Read these files first:
```
1. README.md
2. docs/diagrams/   ← list what exists here
```

Task: Add the EMS capability roadmap as a Mermaid diagram to the docs.

Step 1 — Check if docs/diagrams/ exists:
```bash
Test-Path docs\diagrams
```
If not, create it:
```bash
New-Item -ItemType Directory -Path docs\diagrams
```

Step 2 — Create `docs/diagrams/ems-roadmap.md` with this content:

```markdown
# PipelineKit EMS Capability Roadmap

12 Engineering Management System domains. 109 total capabilities.

## Status legend
- ✅ Built and verified
- 🔵 Sprint package ready to execute
- ⬜ Queued — planned, no package yet
- ⬛ Not started

## Tier 1 — Core EMS

| Domain | Built | Ready | Queued | Total |
|---|---|---|---|---|
| DC — Data Contract  | DC-1..9 (9) | DC-10 | DC-11,12 | 12 |
| QM — Quality        | QM-1..4 (4) | QM-6,7,8 | QM-5,9 | 9 |
| AI — AI Management  | AI-1..6 (6) | — | AI-7..12 | 12 |

## Tier 2 — Expansion EMS

| Domain | Built | Ready | Queued | Total |
|---|---|---|---|---|
| GM — Governance     | GM-1 (1) | GM-2,3 | GM-4..9 | 9 |
| AM — Architecture   | AM-1..3 (3) | AM-4 | AM-5..8 | 8 |
| OM — Observability  | OM-1..3 (3) | OM-4 | OM-5..9 | 9 |

## Tier 3 — Platform EMS

| Domain | Built | Ready | Queued | Total |
|---|---|---|---|---|
| RM — Release        | RM-1..3 (3) | — | RM-4..8 | 8 |
| CM — Compliance     | — | — | CM-1..10 | 10 |
| KM — Knowledge      | — | — | KM-1..9 | 9 |
| SM — Security       | — | — | SM-1..7 | 7 |
| CO — Cost           | — | — | CO-1..8 | 8 |
| DM — Documentation  | — | — | DM-1..8 | 8 |

## Current state (June 29, 2026)

- 22 capabilities built across 6 active domains
- 8 sprint packages ready to execute
- 343 tests passing
- Phase 2 in progress
```

Step 3 — Commit:
```bash
git add docs\diagrams\ems-roadmap.md
git commit -m "docs: EMS capability roadmap — June 29 2026"
git push origin main
```

Step 4 — Return: commit hash and confirmation that file was created.

---

### Task: Update EMS status after each sprint

After every sprint verification passes, update
`pipelinekit-internal/reference/EMS-ROADMAP-STATUS.md`:

1. Change the capability's status from 🔵 Ready to ✅ Built
2. Fill in the Sprint column (Sprint N)
3. Fill in the Tests added column (exact count)
4. Fill in the Commit column (first 7 chars of commit hash)

This takes 2 minutes and keeps the table accurate.

The PowerShell post-sprint scripts (POST-SPRINT-QM6.ps1 etc.) will
remind you to do this — add it to each post-sprint script after
the CHANGELOG update.

---

## Part 4 — Diagram update policy

The diagram needs updating when:
- A sprint verification passes → change status ✅
- A new sprint package is produced → add 🔵
- A domain is started for the first time → add to table

The diagram does NOT need updating when:
- Tests run without new capabilities
- Docs are updated without code changes
- Design partner sessions happen

Target: update the status table within 24 hours of each sprint
completing. The diagram in the public repo updates once per week
or when a major milestone is hit.
