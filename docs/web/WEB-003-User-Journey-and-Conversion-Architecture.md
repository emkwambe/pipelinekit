# WEB-003 — PipelineKit User Journey & Conversion Architecture

**Version:** 1.0  
**Date:** June 27, 2026  
**Author:** Command Center (Claude Chat) + Eddy Mkwambe  
**Status:** Approved — governs all CTAs and conversion decisions

---

## Governing Principle

Every visitor is at a stage. Every stage has a question. Every question has one primary answer and one primary CTA.

This document maps the complete journey from first contact to enterprise expansion. It governs what goes on every page, what every button says, and what success looks like at each stage.

---

## The Full Journey

```
Visitor → Interest → Evaluation → Trial → Activation → Success → Training → Certification → Enterprise → Expansion
```

---

## Stage 1: VISITOR

**Who:** Someone who heard about PipelineKit — from LinkedIn, Twitter, a conference, a colleague, or search.

**Primary question:** "What is PipelineKit?"

**Time available:** 10-30 seconds before they leave or stay.

**What they need:**
- Immediate clarity on what the product does
- One sentence that lands
- One visual that confirms it

**What they do NOT need:**
- A long explanation
- A pricing table
- A demo request form

**Trust signals needed:**
- Real CLI output (not a mockup)
- Test count (303 passing tests — visible precision)
- Registry URL (registry.pipelinekit.dev — live infrastructure)

**Primary CTA:** `Install PipelineKit →`  
**Secondary CTA:** `Browse Blueprint Catalog`

**Success metric:** Scroll depth > 50% on landing page  
**Drop-off risk:** Vague headline. Visitor cannot answer "what is this?" in 10 seconds.

**Page:** pipelinekit.dev/

---

## Stage 2: INTEREST

**Who:** Visitor stayed. They scrolled. They are reading the lifecycle section or the blueprint cards.

**Primary question:** "Is this relevant to my situation?"

**Time available:** 2-5 minutes.

**What they need:**
- Recognition — "this describes my problem"
- Specificity — actual CLI commands, not marketing language
- The three blueprints with verified test counts

**ICP matching signals:**
- ICP-001 (Solo engineer): "I build the same postgres→snowflake pipeline for every client"
- ICP-002 (Consultancy): "We have no standard architecture across projects"
- ICP-003 (Internal team): "Our pipeline failures have no root cause visibility"
- ICP-004 (Airbyte/Fivetran user): "Migration cost is too high"

**Trust signals needed:**
- Blueprint cards with real test counts (7/7, 9/9, 43/43)
- The trust model (AI proposes, human approves)
- Five AI providers (they can use the one they already have)

**Primary CTA:** `Read the docs →`  
**Secondary CTA:** `See how migration works →`

**Success metric:** Click to /platform or /blueprints or /migration  
**Drop-off risk:** Generic feature list with no specificity to their stack

---

## Stage 3: EVALUATION

**Who:** They read the platform page or the migration page. They are asking "can this actually do what it says?"

**Primary question:** "Can this replace weeks of work?"

**Time available:** 10-30 minutes across multiple sessions.

**What they need:**
- Blueprint demonstration (real dbt test output)
- Migration analysis example (real Airbyte config → pipelinekit.yaml)
- Architecture credibility (five-layer architecture diagram)
- The error code taxonomy (shows depth of engineering)

**What they are checking:**
- Is this production-grade or a demo project?
- Does it support my stack (Snowflake, BigQuery, DuckDB)?
- What happens when it fails?
- How do I get help?

**Trust signals needed:**
- dbt test output (PASS=43 WARN=0 ERROR=0)
- The verification standard (8 required assets, local verification)
- GitHub repo (shows real commits, real history)
- Founder credibility (MS in Strategic Analytics, 12 years engineering)

**Primary CTA:** `Run Blueprint #001 →` (quickstart docs)  
**Secondary CTA:** `Apply to be a design partner →`

**Success metric:** GitHub repo visit OR docs quickstart visit  
**Drop-off risk:** No proof of production use. No case study. Evaluator cannot verify claims.

**Mitigation:** The 43/43 dbt test output IS the proof. Show it verbatim.

---

## Stage 4: TRIAL

**Who:** They installed PipelineKit. They are running `pipelinekit --help` for the first time.

**Primary question:** "Can I make this work?"

**Time available:** 30 minutes to 2 hours.

**What they need:**
- A working quickstart in < 10 minutes
- Blueprint #001 running locally with the Docker seed
- Clear error messages with error codes that explain what went wrong
- `pipelinekit health` showing green across all dependencies

**Friction points:**
- Docker not running → `pipelinekit health deps` catches this
- ANTHROPIC_API_KEY not set → `PK-AI-001` with clear message
- dbt not installed → `pipelinekit health deps` catches this

**Primary CTA:** `pipelinekit blueprint install postgres-to-snowflake`  
**Secondary CTA:** (none — do not distract from getting to first success)

**Success metric:** First successful `pipelinekit run` with PASS status  
**Drop-off risk:** Any error in the first 10 minutes that is not immediately explained

**Mitigation:** `pipelinekit health --strict` should be step 1 of every quickstart. It catches all dependency issues before the user hits a confusing error.

---

## Stage 5: ACTIVATION

**Who:** They ran Blueprint #001 successfully. They got PASS=7 WARN=0 ERROR=0. They want more.

**Primary question:** "Can I use this for my actual pipeline?"

**Time available:** Days to weeks.

**What they need:**
- `pipelinekit generate blueprint --interactive` for their source/destination
- Confidence score ≥ 0.85 on their specific stack
- `pipelinekit migrate analyze` if they have an existing config
- Clear docs on adding their own contracts

**This is the moment they become a real user:**
- They propose a blueprint for their stack
- They review the AI proposal interactively
- They apply it
- They validate it locally

**Primary CTA:** `pipelinekit generate blueprint --source <their source> --destination <their dest> --interactive`  
**Secondary CTA:** `Join the design partner program` (for early users)

**Success metric:** First AI-proposed blueprint applied and validated  
**Drop-off risk:** Proposal confidence too low (< 0.70) for their source type. They feel unsupported.

**Mitigation:** Design partner program — direct access to engineering team for any source/destination not yet in the catalog.

---

## Stage 6: SUCCESS

**Who:** They are running PipelineKit in production (or staging). They have used `pipelinekit diagnose` at least once. They trust the system.

**Primary question:** "Can my team use this?"

**Time available:** Ongoing.

**What they need:**
- Team pricing (Team tier — $499/month)
- Private registry access (for internal blueprints)
- Slack alerting (Sprint 8-1 — now live)
- Documentation for onboarding teammates

**Trust signals needed:**
- Their own successful run history
- The diagnostic evidence from their real failures
- The upgrade/rollback audit trail

**Primary CTA:** `Upgrade to Team →`  
**Secondary CTA:** `Enroll your team in the Academy →` (Phase 2)

**Success metric:** Conversion from Solo to Team tier  
**Drop-off risk:** Team onboarding friction — teammate cannot get to first success in < 30 minutes

---

## Stage 7: TRAINING

**Who:** Team is using PipelineKit. They want to level up their engineers.

**Primary question:** "How do my engineers become experts?"

**What they need:**
- Academy paths aligned to their team's skill gaps
- Synthetic enterprise that matches their industry
- Certification to demonstrate capability
- Instructor dashboard to track progress

**Primary CTA:** `Enroll team in Academy →`  
**Secondary CTA:** `Request corporate training package →`

**Success metric:** First learner completes a certification path  
**Drop-off risk:** Academy not yet built (Phase 2 problem)

---

## Stage 8: CERTIFICATION

**Who:** Engineers completing Academy paths.

**Primary question:** "What does certification mean for my career?"

**What they need:**
- Verifiable credential (not just a PDF)
- Skill demonstration (12 incidents recovered)
- Portfolio artifact (their capstone blueprint)
- LinkedIn badge

**Primary CTA:** `Register for PCAE exam →`

**Success metric:** PCAE certification issued  
**Drop-off risk:** Certification perceived as "just another vendor cert"

**Mitigation:** The certification requires demonstrated capability — 12 real incident recoveries. It is not a multiple choice test. This is the differentiator.

---

## Stage 9: ENTERPRISE

**Who:** Organization with 10+ engineers, compliance requirements, or air-gap needs.

**Primary question:** "Can this work at our scale with our security requirements?"

**What they need:**
- SSO (SAML/OIDC)
- Private registry
- Air-gap deployment (Ollama-based AI, no external API calls)
- Audit log (every pipeline run, every blueprint install, every proposal)
- SLA guarantee
- Professional services for migration

**Primary CTA:** `Talk to us →` (routes to enterprise inquiry form)

**Success metric:** Enterprise contract signed  
**Drop-off risk:** No case study. No reference customer. No proof at enterprise scale.

**Mitigation:** Design partner program converts to reference customers. The first 3 design partners become the first 3 case studies.

---

## Stage 10: EXPANSION

**Who:** Existing enterprise customer adding teams, use cases, or geographic markets.

**Primary question:** "How do we expand PipelineKit across the organization?"

**What they need:**
- Multi-team registry (different blueprints per team)
- East African market pricing (PPP adjustment)
- Academy for new teams
- Professional services for custom blueprint development

**Primary CTA:** `Talk to your account manager →`

---

## CTA Strategy Summary

| Stage | Primary CTA | Secondary CTA |
|---|---|---|
| Visitor | Install PipelineKit → | Browse Blueprint Catalog |
| Interest | Read the docs → | See how migration works → |
| Evaluation | Run Blueprint #001 → | Apply as design partner → |
| Trial | (in CLI — no website CTA) | — |
| Activation | (in CLI — blueprint propose) | Join design partner program |
| Success | Upgrade to Team → | Enroll team in Academy → |
| Training | Enroll in Academy → | Request corporate training → |
| Certification | Register for PCAE exam → | — |
| Enterprise | Talk to us → | — |
| Expansion | Talk to your account manager → | — |

---

## ICP-Specific Journey Variations

### ICP-001: Solo Analytics Engineer / Consultant

```
Discovery:  Twitter/X, dbt Slack, personal referral
Stage 1→2:  "This is exactly what I rebuild for every client"
Stage 3→4:  Quickstart works first try → Blueprint #001 in 10 min
Stage 4→5:  Proposes postgres→bigquery blueprint for new client
Conversion: Solo tier $99/month
Path:       Visitor → Trial → Activation in < 1 week
```

### ICP-002: Analytics Consultancy

```
Discovery:  LinkedIn, dbt community, conference
Stage 1→2:  "Standard architecture across all our projects"
Stage 3→4:  CTO evaluates, forwards to senior engineer to trial
Stage 4→5:  Team proposes 3 blueprints for top 3 client stacks
Conversion: Team tier $499/month
Path:       Visitor → Evaluation → Trial → Success in 2-4 weeks
```

### ICP-003: Internal Data Team (Enterprise)

```
Discovery:  LinkedIn, conference talk, analyst report
Stage 1→2:  "AI root cause for pipeline failures"
Stage 3→4:  POC with one pipeline, present to manager
Stage 4→5:  Migrate one Airbyte connection successfully
Conversion: Enterprise tier custom
Path:       Visitor → Evaluation → POC → Enterprise in 4-8 weeks
```

### ICP-004: Airbyte/Fivetran User

```
Discovery:  Search "Airbyte migration", LinkedIn ad, community
Stage 1→2:  "Modernize without starting over"
Stage 3→4:  Run pipelinekit migrate analyze against their config
Stage 4→5:  Successfully migrate first connection
Conversion: Team or Enterprise based on size
Path:       Visitor → Evaluation → Migration POC in 1-2 weeks
```

---

## Metrics Framework

| Stage | Metric | Target (Phase 8) |
|---|---|---|
| Visitor | Bounce rate | < 60% |
| Interest | Scroll depth > 50% | > 40% of visitors |
| Evaluation | GitHub click or docs click | > 15% of visitors |
| Trial | Install → first run | > 50% of installers |
| Activation | First AI blueprint applied | > 30% of trial users |
| Success | Paid conversion | > 20% of activated users |
| Training | Academy enrollment | > 30% of team tier |
| Enterprise | Sales cycle | < 60 days |

---

## The Design Partner Conversion Path

This is Phase 8's primary revenue strategy. Design partners bypass the normal funnel.

```
Direct outreach (LinkedIn, community, referral)
↓
Design partner inquiry form (/contact)
↓
48-hour response from Eddy
↓
30-minute discovery call
↓
Design partner agreement ($0 for 90 days)
↓
Onboarding (direct Slack channel, weekly check-in)
↓
Feedback collected, product shaped
↓
Convert to paid tier after 90 days
↓
Case study published (with permission)
↓
Reference customer for enterprise sales
```

**Target:** 3-5 design partners by end of Phase 8.

---

*Document: WEB-003-User-Journey-and-Conversion-Architecture.md*  
*Location: docs/web/WEB-003-User-Journey-and-Conversion-Architecture.md*  
*Owner: Command Center + Eddy Mkwambe*
