# WEB-002 — PipelineKit Academy Design Specification

**Version:** 1.0  
**Date:** June 27, 2026  
**Author:** Command Center (Claude Chat) + Eddy Mkwambe  
**Status:** Draft — Phase 2 implementation  
**Domain:** academy.pipelinekit.dev (or learn.pipelinekit.dev initially)

---

## Governing Principle

The Academy exists to reduce engineering cognitive load.

The Academy teaches systems thinking — not isolated commands.

Every lesson increases independent engineering capability.

Learners do not study PipelineKit. They operate it — against synthetic enterprises that behave like real production systems.

---

## Strategic Position

**Why this matters:**

Most vendor training is documentation in disguise. It teaches commands, not judgment.

The Academy's differentiator is RealityDB — synthetic enterprises that generate research-backed, deterministic failures. Learners do not read about pipeline failures. They diagnose them. They fix them. They prevent the next one.

This is the only analytics engineering training platform where the data itself is part of the curriculum.

**Revenue potential:**
- Individual: $299/month
- University license: $5,000-25,000/semester
- Corporate training: $10,000-50,000/cohort
- Certification: $199 per exam

---

## Audience

**Primary:** Analytics engineers with 0-3 years experience  
**Secondary:** Data engineers migrating from manual ETL to modern stacks  
**Tertiary:** Universities and bootcamps teaching data engineering  
**Enterprise:** Corporate training for internal data teams

---

## The Learning Philosophy

**Principle 1: Operate first, understand second.**
Students run real pipelines before reading theory. Failure is the curriculum.

**Principle 2: Synthetic enterprises, not toy datasets.**
Every lab uses a RealityDB-generated synthetic enterprise. The data is realistic. The failures are deterministic. The diagnosis is real.

**Principle 3: Certification means demonstrated capability.**
A PipelineKit Certified Engineer has recovered 12 deterministic incidents across 6 synthetic enterprises. Not passed a multiple choice test.

**Principle 4: Systems thinking over tool mastery.**
The Academy teaches the lifecycle (Design → Build → Operate → Diagnose → Govern) not a list of commands.

---

## The Synthetic Enterprise Library

Each enterprise is a RealityDB pack — research-backed, deterministic, reproducible.

```
Enterprise 1: FinCore Analytics (B2B SaaS, 100K rows)
  Domain: Financial services analytics platform
  Pack:   pipelinekit-saas-demo (99/100 HIGH confidence)
  Focus:  Subscription billing, user sessions, feature adoption

Enterprise 2: RetailPulse (E-commerce, 50K rows)
  Domain: Multi-brand retail analytics
  Pack:   pipelinekit-orders (100/100 MEDIUM)
  Focus:  Order fulfillment, inventory, customer tiers

Enterprise 3: PayStream (Payments, 30K rows)
  Domain: Payment processing analytics
  Pack:   pipelinekit-payments (97/100 MEDIUM)
  Focus:  Transaction processing, refunds, fraud signals

Enterprise 4: MedCore (Healthcare, planned)
  Domain: Patient analytics (anonymized synthetic)
  Pack:   pipelinekit-medcore (planned)
  Focus:  HIPAA-adjacent data handling, compliance contracts

Enterprise 5: LogiTrack (Logistics, planned)
  Domain: Supply chain analytics
  Pack:   pipelinekit-logistics (planned)
  Focus:  Delivery SLAs, carrier performance, volume spikes

Enterprise 6: GovMetrics (Public sector, planned)
  Domain: Municipal data analytics
  Pack:   pipelinekit-gov (planned)
  Focus:  Open data standards, audit requirements
```

---

## Certification Track

**PipelineKit Certified Analytics Engineer (PCAE)**

Requirement: Recover 12 incidents across at least 3 synthetic enterprises.

```
Tier 1 — Foundation (Incidents 1-4)
  INCIDENT-001: Schema drift (column renamed in source)
  INCIDENT-002: Null explosion (40% of status column NULL)
  INCIDENT-003: Duplicate PKs (source INSERT bug)
  INCIDENT-004: Late arriving data (freshness breach)

Tier 2 — Practitioner (Incidents 5-8)
  INCIDENT-005: Volume spike (10x normal batch)
  INCIDENT-006: Type mismatch (integer column receives strings)
  INCIDENT-007: Contract accepted_values failure (new enum value)
  INCIDENT-008: Incremental cursor missing (full scan triggered)

Tier 3 — Expert (Incidents 9-12)
  INCIDENT-009: Cross-db compatibility failure (dialect mismatch)
  INCIDENT-010: Logical contradiction (start_date > end_date)
  INCIDENT-011: JSON structural mutation (object becomes array)
  INCIDENT-012: Timezone offset cascade (silent data shift)
```

Each incident:
1. Story Enforcer injects the failure deterministically
2. Student runs `pipelinekit diagnose`
3. Student interprets evidence
4. Student applies fix
5. Student re-runs verification
6. Pass/fail scored automatically

---

## Learning Paths

### Path 1: Analytics Engineering Foundations
**Duration:** 4 weeks | **Enterprise:** RetailPulse  
**Outcome:** First production-ready pipeline

```
Week 1: Design — blueprint proposal, AI workflow, human approval
Week 2: Build — init, validate, run, status
Week 3: Operate — contracts, quality checks, freshness SLAs
Week 4: Diagnose — INCIDENT-001 + INCIDENT-002 recovery
```

### Path 2: Pipeline Operations
**Duration:** 4 weeks | **Enterprise:** FinCore Analytics  
**Outcome:** Operating and diagnosing complex pipelines

```
Week 1: Registry — search, install, outdated, upgrade, rollback
Week 2: Operate — multi-blueprint environments, scheduling
Week 3: Diagnose — INCIDENT-003 through INCIDENT-006
Week 4: Govern — contracts deep dive, SLA design
```

### Path 3: Migration Specialist
**Duration:** 2 weeks | **Enterprise:** PayStream  
**Outcome:** Migrating existing Airbyte/Fivetran pipelines

```
Week 1: Migration Intelligence — analyze, map, fill gaps
Week 2: Verification — local testing, contract validation, go-live
```

### Path 4: Enterprise Data Platform
**Duration:** 8 weeks | **Enterprise:** All 6 enterprises  
**Outcome:** PCAE certification

```
Weeks 1-2: Foundations path (compressed)
Weeks 3-4: Operations path (compressed)
Weeks 5-6: Expert incidents (INCIDENT-009 through INCIDENT-012)
Weeks 7-8: Capstone — design a new blueprint for an enterprise problem
```

---

## Course Catalog (Phase 1 — 4 courses)

### Course 1: Your First Trusted Pipeline
**Length:** 5 lessons | **Enterprise:** RetailPulse  
**Level:** Beginner

```
Lesson 1: What makes a pipeline trusted (theory, 15 min)
Lesson 2: pipelinekit init + configure (hands-on, 30 min)
Lesson 3: pipelinekit run against RetailPulse data (hands-on, 30 min)
Lesson 4: Reading pipeline results (hands-on, 20 min)
Lesson 5: Your first contract violation — what happened? (diagnostic, 30 min)
```

### Course 2: Blueprint Engineering
**Length:** 6 lessons | **Enterprise:** FinCore Analytics  
**Level:** Intermediate

```
Lesson 1: Blueprint anatomy — 8 required assets (theory, 20 min)
Lesson 2: Installing from registry (hands-on, 20 min)
Lesson 3: Generating with AI — interactive workflow (hands-on, 45 min)
Lesson 4: Reviewing AI proposals — what to check (judgment, 30 min)
Lesson 5: Verifying locally with DuckDB (hands-on, 30 min)
Lesson 6: Publishing to a private registry (hands-on, 20 min)
```

### Course 3: Pipeline Diagnostics
**Length:** 5 lessons | **Enterprise:** RetailPulse  
**Level:** Intermediate

```
Lesson 1: How the DiagnosticsEngine works (theory, 15 min)
Lesson 2: Reading an EvidencePackage (hands-on, 20 min)
Lesson 3: INCIDENT-001 — Schema drift recovery (lab, 45 min)
Lesson 4: INCIDENT-002 — Null explosion recovery (lab, 45 min)
Lesson 5: Writing your own diagnostic runbook (project, 60 min)
```

### Course 4: Migration Intelligence
**Length:** 4 lessons | **Enterprise:** PayStream  
**Level:** Intermediate

```
Lesson 1: The migration problem (theory, 15 min)
Lesson 2: Analyzing an Airbyte config (hands-on, 30 min)
Lesson 3: Filling FIXME markers and validating (hands-on, 45 min)
Lesson 4: Running your migrated pipeline (hands-on, 30 min)
```

---

## Platform Features

**Student Dashboard:**
- Current path progress
- Incidents recovered (toward certification)
- Time spent per enterprise
- Skill radar (Design / Build / Operate / Diagnose / Migrate / Govern)

**Lab Environment:**
- Synthetic enterprise data pre-loaded
- PipelineKit CLI available in browser terminal (or local)
- Story Enforcer injects failures deterministically (seed-based)
- Verification runs automatically on student submission

**Instructor Dashboard (Phase 2):**
- Class progress overview
- Common failure patterns across students
- Custom incident authoring
- Assessment scoring

**Corporate Dashboard (Phase 3):**
- Team skill gaps by capability area
- Certification pipeline
- Learning ROI metrics

---

## Technology Stack

```
Frontend:    Next.js 14 + Tailwind (consistent with existing products)
Backend:     Supabase (auth, progress, completions)
Billing:     Lemon Squeezy (consistent with CraftLauncher)
Labs:        WebAssembly DuckDB in browser OR remote lab environment
Data:        RealityDB packs (all pre-generated, seed 42, deterministic)
CLI:         Browser-embedded terminal (xterm.js) OR local install
```

---

## Subdomain Plan

```
Phase 1: learn.pipelinekit.dev (simple, faster to ship)
Phase 2: academy.pipelinekit.dev (full platform, certification)
```

---

*Document: WEB-002-Academy-Website-Specification.md*  
*Location: docs/web/WEB-002-Academy-Website-Specification.md*  
*Owner: Command Center + Eddy Mkwambe*
