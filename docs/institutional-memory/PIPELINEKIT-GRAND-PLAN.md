# PipelineKit — Grand Plan
## A Meaningful Sequence from Operating System to Platform

**Document type:** Strategic roadmap  
**Date:** June 26, 2026  
**Author:** Command Center (Claude Chat) + Eddy Mkwambe  
**Current state:** Phase 6 complete — 289 tests, 81.43% coverage, 13 CLI commands, 3 blueprints  
**Main branch:** `2503d00`

---

## The Governing Principle

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Every item in this plan either strengthens that sentence or it does not belong.

---

## Where We Are

```
✅ Built and verified:
   CLI: 13 commands across 6 groups
   Blueprints: 3 (2 hand-crafted, 1 AI-proposed)
   AI providers: 5 (US ×2, EU ×1, China ×1, Local ×1)
   Trust model: proposed → approved → written → validated
   Registry: code complete, infrastructure pending
   Migration: Airbyte/Fivetran/Python → pipelinekit.proposed.yaml
   Documentation: 10 guides + 12 diagrams
   Tests: 289 | Coverage: 81.43%

⏳ Immediate gaps before design partner outreach:
   Registry deploy (registry.pipelinekit.dev — 30 min infrastructure)
   Blueprint #003 local verification (dbt parse + synthetic seed)
   ANTHROPIC_API_KEY rotation (key exposed in session)
```

---

## The Plan — Six Phases

```
Phase 6  ← COMPLETE (current)
Phase 7  ← Infrastructure + Synthetic Data Foundation
Phase 8  ← Market Entry (Design Partners → Revenue)
Phase 9  ← Platform (MCP + Academy)
Phase 10 ← Scale (Enterprise + Ecosystem)
Phase 11 ← Defensibility (AI Fine-Tuning + Owned Intelligence)
```

---

## PHASE 7: Infrastructure + Synthetic Data Foundation
**Duration:** 4-6 weeks  
**Theme:** Make everything that was built actually work end-to-end  
**Outcome:** PipelineKit is demo-ready, registry is live, synthetic data foundation is laid

### 7-A: Registry Deploy (Week 1 — 30 min + 2 hours)
**What:** Deploy `registry.pipelinekit.dev` — the last infrastructure gap from Sprint 6-6

```
Tasks:
□ Create pipelinekit-registry GitHub repo (public)
□ author v1/catalog.json with 3 blueprint entries
□ Zip each blueprint directory:
    postgres-to-snowflake-1.0.0.zip
    salesforce-to-snowflake-1.0.0.zip
    stripe-to-snowflake-1.0.0.zip
□ Deploy to Cloudflare Pages at registry.pipelinekit.dev
□ Verify: pipelinekit blueprint search stripe → real results
□ Verify: pipelinekit blueprint install postgres-to-snowflake → downloads and installs
□ Record verified test in PROJECT-STATUS
```

**Resources:** Cloudflare Pages (already in use), GitHub (already in use)  
**Cost:** $0 — Cloudflare Pages free tier  
**Blocks:** Design partner demo of `pipelinekit blueprint install`

---

### 7-B: Synthetic Data Foundation (Weeks 1-3)
**What:** Build the RealityDB packs that replace placeholder seeds

**Priority order from PIPELINEKIT-SYNTHETIC-DATA-REQUIREMENTS-v2.md:**

```
Week 1: pipelinekit-orders pack (P0)
  - 10,000 rows, SQR 97/100
  - Replaces Docker seed that caused 'confirmed' status incident
  - Exact enum values match dbt accepted_values tests
  - Verifies Blueprint #001 with research-backed distributions

Week 2: pipelinekit-payments pack (P0)
  - 10,000 rows, SQR 97/100
  - Enables Blueprint #003 local verification (none exists yet)
  - Stripe-specific: integer cents, Unix epoch timestamps
  - Requires: scripts/verify-blueprint-003.ps1 (new script)

Week 3: pipelinekit-crm pack (P1)
  - 5,000 rows, SQR 97/100
  - Replaces inline Python seed in Blueprint #002 verification
  - stage_name values must exactly match contracts/opportunities.yaml
```

**Resources:** RealityDB CLI v2.38.0, DATA-GENERATION-GUIDE.md v2.0  
**Builds on:** MedCore lessons (single temporal anchor, no "none" in enums, BOM-free UTF-8)  
**Output:** 3 RealityDB packs + 1 new verification script

---

### 7-C: Blueprint #003 Verification (Week 2)
**What:** Verify the AI-proposed stripe-to-snowflake blueprint end-to-end

```
Tasks:
□ Author scripts/verify-blueprint-003.ps1 -Local
  (uses pipelinekit-payments pack as synthetic seed)
□ Run: dbt parse against blueprint #003 transform/
□ Run: verify-blueprint-003.ps1 -Local
□ Record verified deployment in blueprints/stripe-to-snowflake/docs/runbook.md
□ Update catalog entry: verified: true
□ Normalize blueprint #003 layout:
    rename dbt/ → transform/
    move RUNBOOK.md → docs/runbook.md
    (matches Blueprint #001 and #002 standard layout)
```

**Resources:** Docker Postgres, DuckDB, poetry  
**Blocks:** Blueprint #003 being marked verified in registry catalog

---

### 7-D: Design Partner Demo Dataset (Week 3)
**What:** `pipelinekit-saas-demo` pack — 50,000 rows, 99/100 HIGH confidence

```
Purpose: The showcase dataset for the first design partner conversation.
         Shows PipelineKit handling production-realistic analytics data.
         Not toy orders. Not placeholder names. Real-looking B2B SaaS.

Schema: organizations → users → sessions → subscriptions → invoices
        50,000 rows total, 99/100 SQR HIGH confidence
        Citations: OpenView SaaS Benchmarks 2024, Bessemer Cloud Index
```

**Resources:** RealityDB CLI v2.38.0  
**Output:** `pipelinekit-saas-demo` pack + 50K row SQL baseline

---

### 7-E: Housekeeping (Week 1 — parallel)
**What:** Close all open items from Phase 6

```
□ Rotate ANTHROPIC_API_KEY (exposed in session — immediate priority)
□ Archive ADR-018-Blueprint-Generation-Governance.md (superseded)
□ Archive SPEC-015-AI-Blueprint-Generation.md (superseded)
□ SPEC-013 drift reconciliation (blueprint.json + contracts shape)
□ ADR-020 filename note reconciled
□ ICP-001, ICP-002, ICP-003 stub documents
□ CI green confirmed on GitHub Actions
□ pipelinekit health --strict → all gates green
```

---

### Phase 7 Exit Criteria

```
✅ registry.pipelinekit.dev live and serving 3 blueprints
✅ pipelinekit blueprint install postgres-to-snowflake works against real URL
✅ Blueprint #001 verification uses pipelinekit-orders pack (not placeholder seed)
✅ Blueprint #002 verification uses pipelinekit-crm pack
✅ Blueprint #003 locally verified + runbook entry
✅ pipelinekit-saas-demo pack ready for design partner demo
✅ All Phase 6 housekeeping complete
✅ ANTHROPIC_API_KEY rotated
✅ CI green
```

---

## PHASE 8: Market Entry
**Duration:** 6-8 weeks  
**Theme:** First revenue, first design partners, product-market fit signal  
**Outcome:** 3-5 paying design partners, $5-15K MRR, product feedback loop active

### 8-A: ICP Identification and Outreach (Weeks 1-2)

**ICP-001: Solo Analytics Engineer / Consultant**
- Pain: builds the same postgres→snowflake pipeline for every client
- Solution: `pipelinekit blueprint install postgres-to-snowflake` in 30 seconds
- Channel: Twitter/X, dbt Slack, LinkedIn
- Price point: $49-99/month (individual)
- Demo: 5-minute quickstart, Blueprint #001 running locally

**ICP-002: Analytics Consultancy (2-10 engineers)**
- Pain: no standardized pipeline architecture across client projects
- Solution: Blueprint catalog + team blueprint sharing via registry
- Channel: dbt community, Modern Data Stack Slack, direct outreach
- Price point: $299-599/month (team)
- Demo: propose a new blueprint for their most common client stack

**ICP-003: Internal Data Team (enterprise, 5-50 engineers)**
- Pain: pipeline failures with no root cause visibility
- Solution: `pipelinekit diagnose` + AI root cause with 5 provider options
- Channel: LinkedIn, conference talks (dbt Coalesce), warm intros
- Price point: $2,000-8,000/month (team + enterprise)
- Demo: diagnose a real pipeline failure they experienced

**ICP-004: Mixed-Stack Enterprise (Airbyte/Fivetran users)**
- Pain: migration cost and complexity from current tool
- Solution: `pipelinekit migrate analyze airbyte-connection.json`
- Channel: Airbyte community, direct LinkedIn to Data Engineering leads
- Price point: $3,000-15,000/month (migration + ongoing)
- Demo: analyze their actual Airbyte config live in the call

---

### 8-B: Sprint 7-1 — Slack Alerting Adapter (Week 2)
**Why now:** Every design partner conversation will ask "does it alert to Slack?"  
**What:** Add Slack webhook as a second notification channel

```
ADR: ADR-021 (MCP Integration Governance — partial, Slack only)
SPEC: SPEC-018-Slack-Alerting

New file: src/pipelinekit/notifications/adapters/slack.py
Modified: src/pipelinekit/notifications/dispatcher.py
Modified: docs/guides/CONFIGURATION-REFERENCE.md

Config:
notifications:
  enabled: true
  channels:
    - type: resend
      api_key: ${RESEND_API_KEY}
    - type: slack
      webhook_url: ${SLACK_WEBHOOK_URL}
```

**Resources:** Slack incoming webhooks (free), 1 sprint  
**Tests:** Mock webhook calls — no real Slack in CI  
**Effort:** 1 sprint, ~1 day Claude Code

---

### 8-C: Sprint 7-2 — pipelinekit validate <path> (Week 3)
**Why now:** Design partners will want to validate a draft config before running  
**What:** Extend `pipelinekit validate` to accept an optional path argument

```
Current:  pipelinekit validate          → validates pipelinekit.yaml
New:      pipelinekit validate <path>   → validates any config file

Primary use case:
  pipelinekit migrate analyze airbyte-connection.json --apply --write-draft
  # fills in FIXME markers manually
  pipelinekit validate pipelinekit.proposed.yaml
  # validates the proposed config before renaming to pipelinekit.yaml
```

**Effort:** Small — 1 day Claude Code  
**ADR:** Not required — this is a CLI extension, not an architectural decision

---

### 8-D: Blueprint Expansion via Proposal System (Weeks 3-6)
**Why now:** A catalog of 3 blueprints is a proof of concept. A catalog of 10 is a product.  
**What:** Use `pipelinekit generate blueprint --interactive` to propose and verify 7 new blueprints

```
Priority order (use proposal system for each):

Sprint 7-3: stripe-to-bigquery
  Source: pipelinekit-payments pack (already built in Phase 7)
  Destination: BigQuery (DuckDB local proxy)
  Verify: verify-blueprint-004.ps1 -Local

Sprint 7-4: hubspot-to-snowflake
  Source: pipelinekit-hubspot pack (new — HubSpot CRM schema)
  Destination: Snowflake
  Verify: verify-blueprint-005.ps1 -Local

Sprint 7-5: mysql-to-snowflake
  Source: pipelinekit-orders pack (mysql schema variant)
  Destination: Snowflake
  Verify: verify-blueprint-006.ps1 -Local

Sprint 7-6: shopify-to-snowflake
  Source: pipelinekit-ecommerce pack (new — Shopify schema)
  Destination: Snowflake
  Verify: verify-blueprint-007.ps1 -Local

Sprint 7-7: postgres-to-bigquery
  Source: pipelinekit-orders pack
  Destination: BigQuery
  Verify: verify-blueprint-008.ps1 -Local
```

**Resource model:** Each blueprint uses the proposal system (10 min) + human review (20 min) + local verification (30 min) = ~1 hour per blueprint. 7 blueprints = 7 hours total.

**By end of Phase 8:** 10 production blueprints. The catalog is a moat.

---

### 8-E: Pricing and Billing (Week 4)
**What:** Stripe integration for subscription billing

```
Tiers:
  Solo:       $99/month   — 1 user, 3 blueprints, community support
  Team:       $499/month  — 5 users, unlimited blueprints, email support
  Enterprise: $2,500+/mo  — unlimited users, private registry, SLA, Slack support

Implementation:
  Lemon Squeezy (consistent with CraftLauncher stack)
  OR Stripe directly (more control)
  
  Gate: pipelinekit blueprint install --registry-auth ${PK_LICENSE_KEY}
  Private blueprints only available on Team+ plan
```

---

### 8-F: Funding Applications (Weeks 1-8, parallel)
**What:** Apply to grants and programs that do not require pausing product work

```
Immediate (deadline-driven):
  □ IES SBIR Phase IB (deadline check — tied to SafeSQL Pro, June 29)
  □ NC IDEA SEED — $50K, opens July 27
    Use case: Blueprint catalog expansion + Academy development
  □ YC W27 — deadline July 27
    Pitch: AI-native analytics OS + simulation-based Academy

Infrastructure credits (applications in flight):
  □ Cloudflare Workers Launchpad (submitted)
  □ Cloudflare for Startups — $250K credits (submitted)
  □ Anthropic Startups Program (submitted)

New applications:
  □ AWS Activate — up to $100K credits for registry hosting
  □ Snowflake Startup Program — free Snowflake credits for Blueprint #001 production verification
  □ dbt Labs Partnership — co-marketing opportunity
```

---

### Phase 8 Exit Criteria

```
✅ 3-5 paying design partners
✅ $5-15K MRR
✅ Slack alerting live
✅ 10 production blueprints in catalog
✅ pipelinekit validate <path> works
✅ At least one NC IDEA or YC application submitted
✅ Product feedback documented from design partners
```

---

## PHASE 9: Platform
**Duration:** 8-12 weeks  
**Theme:** PipelineKit becomes a platform, not just a CLI  
**Outcome:** MCP server live, Academy beta, $50-100K ARR

### 9-A: Sprint 8-1 — PipelineKit as MCP Server (ADR-021)
**What:** Expose PipelineKit as an MCP server — every AI tool becomes a client

```
ADR-021: MCP Integration Governance
SPEC-019: PipelineKit MCP Server

MCP tools exposed (read/propose only):
  pipelinekit_validate()
  pipelinekit_diagnose(run_id?)
  pipelinekit_health()
  pipelinekit_blueprint_info(name)
  pipelinekit_blueprint_search(query)
  pipelinekit_migrate_analyze(config_path)
  pipelinekit_status()

NOT exposed as MCP (require human confirmation):
  pipelinekit_run()          ← executes pipeline
  pipelinekit_blueprint_install() ← writes to filesystem
  pipelinekit_apply_plan()   ← writes blueprint assets

Deployment: pipelinekit serve --mcp --port 3000
Integration: Claude Desktop, Cursor, any MCP-capable client
```

**Strategic impact:** Every Claude Desktop user becomes a potential PipelineKit user. Zero additional marketing required — the MCP ecosystem does the distribution.

---

### 9-B: Sprint 8-2 — MCP Schema Discovery
**What:** BlueprintProposer calls source MCP servers to discover real schemas

```
Before: BlueprintProposer assumes column names → confidence 0.82
After:  BlueprintProposer calls Salesforce MCP → real schema → confidence 0.95+

Implementation:
  BlueprintProposer._build_context() → optional MCP discovery
  If source MCP server available: call describe_schema()
  Include real column names in ProposalContext
  Provenance: source_evidence includes MCP discovery record

pipelinekit generate blueprint \
  --source salesforce \
  --destination snowflake \
  --discover-schema \    ← new flag: calls Salesforce MCP
  --interactive
```

---

### 9-C: PipelineKit Academy Beta (Weeks 4-12)
**What:** The simulation-based analytics engineering platform

```
Phase 9 Academy scope (beta, not full product):

Module 1: Core Pipeline Engineering
  Enterprise: academy-fincore (100K rows, 99/100 SQR)
  Week 1: First pipeline (Blueprint #001 equivalent)
  Week 2: INCIDENT-001 (Schema Drift) — student fixes
  Week 3: INCIDENT-003 (Duplicate PKs) — student investigates
  Week 4: INCIDENT-004 (Late Arriving Data) — student sets up freshness alert
  Assessment: ASSESS-001 (revenue mismatch, deterministic)

Beta audience: 10-20 students from:
  - ECPI University (Eddy's existing relationship)
  - dbt community learners
  - Data engineering bootcamp graduates

Beta pricing: Free for beta cohort in exchange for feedback
Post-beta pricing: $299/month per student, $2,500/month per team

Infrastructure needed:
  - academy-fincore RealityDB pack (from ACADEMY-SYNTHETIC-DATA-REQUIREMENTS.md)
  - 5 Story Enforcer scripts (INCIDENT-001 through INCIDENT-005)
  - Assessment dataset (ASSESS-001, seed=42, pre-computed outcomes)
  - LMS platform: Atelier (existing product) or simple web app
```

---

### 9-D: Private Blueprint Registry (Enterprise Feature)
**What:** Organizations host their own blueprint registry — internal blueprints not shared publicly

```
Config:
  registries:
    - url: https://registry.pipelinekit.dev  # public
    - url: https://blueprints.acmecorp.com   # private
      auth: ${PRIVATE_REGISTRY_TOKEN}

pipelinekit blueprint install acme-internal-postgres-snowflake
  → pulls from private registry
  → same validation before write
```

**Revenue model:** Private registry = Enterprise plan feature  
**Implementation:** Same RemoteRegistry code, configurable URL + auth header

---

### Phase 9 Exit Criteria

```
✅ PipelineKit MCP server live — Claude Desktop can call pipelinekit_diagnose()
✅ MCP schema discovery raises BlueprintProposer confidence to 0.90+
✅ Academy beta cohort complete (10-20 students, feedback collected)
✅ Private blueprint registry working for at least one enterprise customer
✅ $50-100K ARR
✅ academy-fincore pack (100K rows, 99/100) complete
```

---

## PHASE 10: Scale
**Duration:** 12-16 weeks  
**Theme:** Enterprise sales, team features, geographic expansion  
**Outcome:** $500K ARR, 10+ enterprise customers, East African market entry

### 10-A: Enterprise Features
```
□ SSO (SAML/OIDC) — required for enterprise procurement
□ Audit log — every pipeline run, every blueprint install, every proposal
□ Role-based access control — who can install blueprints, who can run pipelines
□ SLA dashboard — uptime, freshness, contract compliance over time
□ Team blueprint sharing — private registry for enterprise teams
```

### 10-B: East African Market Entry
**Why Eddy is uniquely positioned:**
- Built Kipochi/Miamala (M-Pesa, WhatsApp, chama groups)
- Understands East African fintech infrastructure
- Personal network in Nairobi/Dar es Salaam data engineering community

```
East African ICP:
  - Kenyan fintechs (M-Pesa data pipelines)
  - East African banks (CBK-regulated data)
  - Telecom analytics (Safaricom, MTN, Airtel)

Blueprint needed: mpesa-to-bigquery
  Source: M-Pesa transaction API
  Destination: BigQuery (most common in East Africa)
  Regulatory: CBK data residency requirements
  RealityDB pack: pipelinekit-mpesa (Kenyan fintech distributions)
    Citations: CBK Annual Report 2024, GSMA Mobile Money 2024

Pricing: $199/month (solo), $999/month (team)
  Lower than US pricing — PPP adjustment for EA market
```

### 10-C: Academy Scale
```
Full Academy product launch:
  6 synthetic enterprises (all from ACADEMY spec)
  12 incidents in library
  Certification: 12 incidents recovered = PipelineKit Certified Engineer
  
Partnerships:
  University programs (course adoption)
  Bootcamp partnerships (curriculum licensing)
  Corporate training (team onboarding packages)
  
Revenue model:
  Individual: $299/month
  University license: $5,000-25,000/semester
  Corporate training: $10,000-50,000 per cohort
```

---

## PHASE 11: Defensibility — AI Fine-Tuning + Owned Intelligence
**Duration:** Ongoing from Phase 10  
**Theme:** PipelineKit's AI gets better from use — no competitor can replicate this  
**Outcome:** Fine-tuned local models that outperform API providers on PipelineKit tasks

### 11-A: DiagnosticsEngine Corpus (600 labeled pairs)
```
Build order:
  P0 patterns (F-001 through F-006): use pipelinekit-orders pack
  P1 patterns (F-007 through F-020): use domain-specific packs
  P2 patterns (F-021 through F-028): new patterns per DIAGNOSTICS-FAILURE-CORPUS-SPEC-v2.md

Timeline: 80-120 hours of human labeling
  Labeling rate: ~5 examples/hour
  With Eddy labeling: 16-24 weeks part-time

Output: diagnostics-failure-corpus JSONL (600 pairs)
```

### 11-B: BlueprintProposer Corpus (120 labeled pairs)
```
Source: 12 source/destination combinations × 10 verified blueprints each
Each ground truth blueprint: must pass dbt parse + pipelinekit blueprint validate
Timeline: 12 blueprints × 4 hours each = 48 hours
Output: blueprint-proposal-corpus JSONL (120 pairs)
```

### 11-C: MigrationAnalyzer Corpus (500 labeled pairs)
```
Python generator: 500 synthetic Airbyte/Fivetran/Python configs
Human labeling: correct mapping + valid draft YAML for each
Timeline: 40 hours generation + 80 hours labeling = 120 hours total
Output: migration-corpus JSONL (500 pairs)
```

### 11-D: Fine-Tuning Pipeline
```
Base model: Llama 3.1 8B (Apache 2.0, fine-tunable, runs in Ollama)
Fine-tuning method: LoRA (Low-Rank Adaptation) — efficient, small delta weights
Infrastructure: RunPod or Lambda Labs GPU ($2-4/hour for fine-tuning runs)

Training runs:
  DiagnosticsEngine: 600 pairs → ~2 hours training → evaluate on held-out 15%
  Expected: accuracy 0.71 (base Llama) → 0.89+ (fine-tuned)

Deployment: Ollama model tag pipelinekit/diagnostics:v1
  Users: poetry run pipelinekit diagnose --provider ollama-ft
  Air-gap: yes — no API calls, runs locally
  Cost: $0/month after fine-tuning (vs $0.01-0.05 per API diagnosis)
```

### 11-E: The Enterprise Pitch After Fine-Tuning
```
"PipelineKit's diagnostic intelligence is trained on 600 labeled pipeline failures.
It runs entirely on your infrastructure — no data leaves your environment.
Confidence: 0.89 on your pipeline failures.
Cost: $0 per diagnosis.
Air-gap capable: yes."

This is the ICP-003 enterprise sale. Regulated industries cannot send
pipeline failure evidence to Anthropic or OpenAI. Fine-tuned local models
are the only path to AI diagnostics for that customer segment.
```

---

## Resource Map

### Human Resources (Eddy — current)
```
Role split:
  40% Product + Strategy (Command Center, ADRs, SPECs, design partner conversations)
  35% Implementation (Claude Code verification, PowerShell, commits)
  15% Marketing + Sales (LinkedIn, community, outreach)
  10% Operations (billing, grants, legal)

Leverage points:
  Claude Chat (Command Center) — strategy and documentation at 10x speed
  Claude Code — implementation at 10x speed
  RealityDB — synthetic data at 10x speed vs manual seeding
```

### Financial Resources
```
Current: Bootstrapped (Mpingo Systems LLC)

Phase 7 costs:
  Cloudflare Pages: $0 (free tier)
  RealityDB pack authoring: $0 (existing CLI)
  Claude API (AI diagnosis testing): ~$10-20/month

Phase 8 costs:
  Stripe/Lemon Squeezy: 2.9% + $0.30 per transaction
  Marketing: $500-1,000/month (LinkedIn ads, community)
  
Grants pipeline:
  NC IDEA SEED: $50K (July 27 opening)
  YC W27: equity, network, $500K standard deal
  Cloudflare for Startups: $250K credits (submitted)
  Anthropic Startups: API credits (submitted)
  Snowflake Startup: free compute for production verification
  AWS Activate: $100K credits

Phase 8 revenue target: $5-15K MRR by end of Phase 8
  Break-even: ~$3K MRR covers basic operational costs
```

### Technical Resources
```
Infrastructure (current, all on Cloudflare):
  mpingo.ai: Cloudflare Pages
  safesqlpro.dev: Cloudflare Pages + Workers
  craftlauncher.dev: Cloudflare Workers + Lemon Squeezy
  registry.pipelinekit.dev: Cloudflare Pages (Phase 7)

Compute:
  Local: Windows 11, Docker Desktop, Ollama
  Cloud: Neon (Postgres), D1 (SQLite), R2 (object storage)

AI API budget:
  Anthropic: primary for Claude Chat (Command Center) + testing
  DeepSeek: cost-sensitive testing ($0.001/1K tokens vs $0.015)
  Ollama: local testing, air-gap demos, fine-tuning target
```

---

## The Sequence Logic

**Why this order:**

Phase 7 before Phase 8 — you cannot sell what you cannot demo. The registry, synthetic data, and Blueprint #003 verification are prerequisites for credible design partner conversations.

Phase 8 before Phase 9 — MCP server and Academy require market signal. Build for the ICPs you have confirmed, not the ones you imagine.

Phase 9 before Phase 10 — Platform features (MCP, Academy) create the moat that justifies enterprise pricing. Without them, PipelineKit is a CLI competing on features. With them, it is an ecosystem.

Phase 10 before Phase 11 — Fine-tuning requires a corpus. The corpus requires usage. Usage requires customers. Do not fine-tune in a vacuum — fine-tune on real failure patterns from real customer pipelines (anonymized and with consent).

Phase 11 is ongoing — there is no "done" for AI fine-tuning. Each version of the fine-tuned model is better than the last. This becomes PipelineKit's compounding advantage.

---

## The Competitive Moat — Built in Sequence

```
After Phase 7:  Verified blueprints + live registry
  → Competitors have connectors. You have trusted, verified blueprints.

After Phase 8:  10 blueprints + paying customers + feedback loop
  → Competitors have users. You have design partners who shaped the product.

After Phase 9:  MCP server + Academy + simulation
  → Competitors have tools. You have an ecosystem and a training ground.

After Phase 10: East Africa + enterprise + certifications
  → Competitors have markets. You have markets competitors have not entered.

After Phase 11: Fine-tuned models + owned intelligence
  → Competitors rent AI from OpenAI/Anthropic. You own intelligence
     trained on your corpus. It gets better every day. It works air-gapped.
     No competitor can replicate your training data.
```

---

## The One-Sentence Version

> Build the verified catalog → find design partners → expand the platform → enter new markets → own the intelligence.

Every phase enables the next. Nothing is wasted. The moat compounds.

---

*Document: PIPELINEKIT-GRAND-PLAN.md*  
*Owner: Command Center (Claude Chat) + Eddy Mkwambe*  
*Review trigger: After each phase exit criteria are met*
