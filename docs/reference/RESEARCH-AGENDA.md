# PipelineKit — Research Agenda
## What we must know before we build, position, or sell

**Version:** 1.0  
**Date:** June 28, 2026  
**Owner:** Eddy Mkwambe + Command Center  
**Classification:** Internal — pipelinekit-internal  
**Purpose:** Every SPEC, every positioning claim, every design partner conversation must be grounded in research. This document lists what we do not yet know well enough to build with confidence.

---

## The Governing Principle

> We do not build features. We solve verified problems for known people in specific situations.

Every item on this list is a gap between what we assume and what we know. The research closes the gap. Closed gaps produce better SPECs, stronger positioning, more convincing design partner conversations, and capabilities that actually get used.

---

## Category 1: Market and Customer Research

### R-001: The Real Cost of Pipeline Setup
**What we assume:** Engineers spend 2 weeks on setup before writing business logic.  
**What we need to know:**
- Is 2 weeks the median, mean, or outlier?
- What percentage of that time is ingestion vs transformation vs quality vs governance?
- What does it cost in dollars per engineer per project at $150/hr blended rate?
- Does setup time increase or decrease with team size?

**Why it matters:** The "2-week setup tax" is our primary pain statement. If the real number is 3 days or 6 weeks, our positioning is wrong. The dollar cost makes the ROI calculation concrete.

**Research method:** Ask design partners this question directly. Also: dbt community surveys, Stack Overflow developer survey (data engineering section), LinkedIn polls.

**Target:** A defensible number with a source we can cite on the website and in investor conversations.

---

### R-002: Who Actually Makes the Buy Decision
**What we assume:** The analytics engineer who uses the tool also decides to pay for it.  
**What we need to know:**
- At consultancies: does the engineer choose or does the firm principal?
- At internal teams: is it the engineer, the data engineering manager, or the CTO?
- What is the typical approval threshold below which no procurement process is needed?
- Who writes the check for $99/month vs $499/month vs $2,500/month?

**Why it matters:** Our outreach targets the wrong person if the engineer does not have budget authority. ICP-002 and ICP-003 may require a completely different conversation with a different person.

**Research method:** Ask directly in design partner conversations. Also: LinkedIn job posting analysis (who approves data tools purchases in JDs), Gartner data engineering buyer journey reports.

---

### R-003: The Airbyte/Fivetran Migration Trigger
**What we assume:** Pricing changes are the primary migration trigger.  
**What we need to know:**
- What percentage of Airbyte users are actively considering migration right now?
- Is pricing the #1 trigger or is it reliability, support quality, or feature gaps?
- What has stopped people who considered migration from completing it?
- What is the average number of connectors a migrating team needs to port?
- How long do teams estimate migration would take without tooling?

**Why it matters:** ICP-004 is our fastest conversion path. The better we understand the trigger and the blocker, the sharper the migration CLI positioning.

**Research method:** Reddit r/dataengineering thread analysis (last 6 months). dbt Slack #tools-and-rants. Direct LinkedIn outreach to people who posted about Airbyte pricing. Survey of 20 engineers.

---

### R-004: The East African Data Engineering Market
**What we assume:** East African fintechs and banks have the same data problems as Western companies plus regulatory complexity.  
**What we need to know:**
- How many data engineers are currently employed in Kenya, Tanzania, Nigeria, South Africa?
- What tools are dominant (Snowflake vs BigQuery vs Postgres-only vs no warehouse at all)?
- What is the regulatory compliance burden for data pipelines under CBK, FSCA, BOT?
- What is the typical team size for a data team at a Kenyan fintech?
- What is a realistic price point (PPP-adjusted) for PipelineKit in EA markets?
- Are there existing data engineering communities (Slack, WhatsApp, meetups) in Nairobi/Dar/Lagos?

**Why it matters:** East Africa is Eddy's strategic differentiator. But we are building blind if we do not know the actual market size, tooling landscape, and regulatory requirements.

**Research method:** GSMA Mobile Economy Sub-Saharan Africa 2024. CBK Annual Report 2024. Direct network conversations (Eddy's existing EA contacts). LinkedIn search for "data engineer" in Kenya, Tanzania, Nigeria.

---

### R-005: The Analytics Consultancy Business Model
**What we assume:** Consultancies want repeatable delivery to improve margin.  
**What we need to know:**
- What is the typical project structure for a data consultancy engagement (weeks, team size, deliverables)?
- How do consultancies currently handle "this pipeline pattern we've built before" — copy/paste, internal templates, or from scratch each time?
- What is the margin pressure point — what does an extra week of setup cost in lost margin?
- Do consultancy principals see standardization as a competitive advantage or a commodity?
- How many active data consultancies exist in the US with 2-20 engineers?

**Why it matters:** ICP-002 is a key design partner target and a potentially lucrative Team tier customer. The business model determines what value proposition resonates.

**Research method:** Consulting firm directories (Clutch.co, G2). dbt Partner directory. LinkedIn search for "data consultancy" + "dbt". Direct conversations with 5 consultancy principals.

---

## Category 2: Competitive and Ecosystem Research

### R-006: The True Competitive Landscape
**What we assume:** PipelineKit's primary competition is "doing it manually."  
**What we need to know:**
- What other tools claim to be a "coordination layer" or "operating system" for data pipelines?
- What does Prefect, Dagster, Airflow offer that overlaps with PipelineKit's value?
- What does dbt Cloud's governance features cover vs what PipelineKit adds?
- What does Monte Carlo, Bigeye, or Soda Cloud offer in the observability/quality space?
- What are the top 5 objections a prospect has already considered before talking to us?
- Are there any direct blueprint registry competitors?

**Why it matters:** "We do not compete with dbt" only works if we know precisely where dbt ends and PipelineKit begins. A prospect who has used Dagster will ask how we are different from Dagster. We need a crisp, honest answer.

**Research method:** Product deep-dive on Prefect, Dagster, dbt Cloud, Monte Carlo, Bigeye, Soda Cloud. G2 category comparisons. Stack Overflow trends. dbt community sentiment analysis.

---

### R-007: The dlt Ecosystem and Adoption Rate
**What we assume:** dlt is the right ingestion layer and is widely adopted enough that prospects know it.  
**What we need to know:**
- What is dlt's current GitHub star count, PyPI download rate, and growth trajectory?
- What percentage of data engineers have heard of dlt vs used it?
- What are the most common complaints about dlt that affect PipelineKit blueprints?
- What are the top 20 dlt sources by usage?
- Is dlt Hub (hub.getdlt.io) the right source for blueprint source packages?

**Why it matters:** If a design partner has never heard of dlt, the blueprint installation step creates friction before they even get to PipelineKit's value. We need to know how much dlt education is part of the onboarding.

**Research method:** dlt GitHub stars/downloads. dlt Discord. dlt-hub.io analytics. Direct questions to design partners.

---

### R-008: The Soda vs Great Expectations vs dbt Tests Landscape
**What we assume:** Soda is the right quality layer.  
**What we need to know:**
- What quality tool do most data engineers already use (dbt tests, Great Expectations, Soda, custom)?
- What is the adoption rate of Soda Core vs Soda Cloud vs competitors?
- What are the most common Soda complaints that affect blueprint quality checks?
- Would a prospect who uses Great Expectations feel alienated by a Soda-first approach?

**Why it matters:** If 60% of our design partners already use dbt tests and have never heard of Soda, our quality layer causes friction. We may need to support both or lead with dbt tests instead.

**Research method:** dbt community survey results. Stack Overflow trends. Direct design partner questions about current quality tooling.

---

## Category 3: Technical and Standards Research

### R-009: Data Contract Standards Landscape
**What we assume:** Our YAML-based contract format is the right approach.  
**What we need to know:**
- What is the adoption rate of the Open Data Contract Standard (ODCS)?
- How does our contract format compare to ODCS, Soda contracts, and dbt contracts?
- Should PipelineKit contracts be ODCS-compatible?
- What are the top 5 fields that engineers actually enforce in production contracts?
- What contract violations are most commonly caught in real pipelines?

**Why it matters:** If the industry converges on ODCS and we have a proprietary format, we create switching cost in the wrong direction. If we adopt ODCS now, we align with the standard.

**Research method:** Open Data Contract Standard GitHub. dbt contracts documentation. Soda contracts documentation. Data Council talks on contracts 2024.

---

### R-010: The MCP Ecosystem and PipelineKit's Position
**What we assume:** Exposing PipelineKit as an MCP server will drive adoption through Claude Desktop and other MCP clients.  
**What we need to know:**
- How many engineers currently use Claude Desktop as a development tool?
- What MCP servers are most commonly installed today?
- What actions do engineers most commonly perform via MCP vs CLI?
- Is there a registry for MCP servers that PipelineKit should be listed in?
- What is the expected MCP ecosystem growth trajectory in 2026-2027?

**Why it matters:** Sprint 9-A (PipelineKit as MCP server) is a major investment. The ROI depends on how many engineers will actually discover and use PipelineKit through MCP clients.

**Research method:** Anthropic MCP documentation. Claude Desktop user surveys. MCP server registry (if exists). Developer community sentiment on MCP adoption.

---

### R-011: Blueprint Verification Standards
**What we assume:** 43/43 dbt tests is a meaningful proof of verification.  
**What we need to know:**
- What do engineers consider "verified" in the context of a data pipeline template?
- Is test count the right metric or is it coverage, specific test types, or production runs?
- What would make an engineer trust a blueprint enough to use it on a client project?
- Are there existing standards for data pipeline template certification?

**Why it matters:** "Verified blueprints" is a core trust signal. If what we mean by verified does not match what the market means, the signal is empty.

**Research method:** dbt package hub standards. Direct design partner questions: "What would make you trust a blueprint from a registry?"

---

### R-012: AI Diagnosis Accuracy Benchmarks
**What we assume:** Confidence 0.85 is a meaningful and trustworthy score.  
**What we need to know:**
- What confidence threshold do engineers actually trust for AI-generated recommendations?
- How does our DiagnosticsEngine accuracy compare to what engineers expect from AI diagnosis?
- What failure patterns does the DiagnosticsEngine currently miss or misdiagnose?
- What is the right format for presenting AI diagnosis output to maximize trust and adoption?

**Why it matters:** If engineers dismiss confidence scores below 0.90 and our median is 0.82, the diagnosis feature will be underused. If 0.70 is considered reliable, we are over-engineering.

**Research method:** User research with design partners. A/B test different confidence score presentations. Review of AI diagnostic tools in adjacent spaces (software debugging, infrastructure monitoring).

---

## Category 4: Regulatory and Compliance Research

### R-013: SOC 2 Pipeline Requirements
**What we assume:** Enterprise buyers need SOC 2 compliance in their data pipelines.  
**What we need to know:**
- What specific SOC 2 Type II controls apply to data pipeline infrastructure?
- What evidence do auditors actually request for data pipeline compliance?
- What is the most common SOC 2 pipeline failure point?
- Which of our 12 EMS capabilities map to which SOC 2 control families?
- What tools do SOC 2-compliant organizations currently use for pipeline evidence collection?

**Why it matters:** CM-1 (SOC 2 Control Mapping) is the enterprise gate. If we map to the wrong controls, the compliance sale fails at the audit stage.

**Research method:** AICPA SOC 2 Trust Services Criteria. Vanta and Drata compliance documentation. Direct conversations with compliance-focused design partners.

---

### R-014: CBK and East African Regulatory Data Requirements
**What we assume:** CBK has data pipeline-relevant regulations.  
**What we need to know:**
- What specific CBK regulations require data pipeline governance (data residency, audit trails, access controls)?
- What equivalent regulations exist in Tanzania (BOT), Uganda (BOU), Nigeria (CBN)?
- What is the penalty structure for non-compliance?
- Are there existing compliance frameworks we should map to (ISO 27001, NIST)?
- What data localization requirements exist (must data stay in Kenya/Tanzania/Nigeria)?

**Why it matters:** CM-5 (CBK Compliance Package) is our East African competitive moat. It must be accurate. A compliance package that does not match actual regulatory requirements destroys trust permanently.

**Research method:** CBK Prudential Guidelines for Regulated Entities. BOT Data Protection Guidelines. Direct conversations with compliance officers at Kenyan fintechs.

---

## Category 5: Pricing and Business Model Research

### R-015: Data Engineering Tool Pricing Benchmarks
**What we assume:** $99/Solo, $499/Team, $2,500/Enterprise is the right price structure.  
**What we need to know:**
- What do comparable tools charge (dbt Cloud, Monte Carlo, Soda Cloud, Prefect)?
- What is the typical data engineering tool budget for a 5-person team?
- What is the maximum a solo consultant will pay for a productivity tool before it needs manager approval?
- What pricing model converts best for CLI tools (per seat, per pipeline, per usage, flat fee)?
- What does the East African market actually pay for SaaS tools (PPP-adjusted)?

**Why it matters:** Mispriced tools either leave money on the table or kill the sales conversation before it starts. The right price structure requires knowing what comparable solutions cost and what the market will bear.

**Research method:** G2 pricing pages for all competitors. Baremetrics public SaaS benchmarks. Direct pricing conversations with design partners. EA market pricing analysis.

---

### R-016: The Academy Revenue Model
**What we assume:** $299/month per student, $5,000-25,000/semester for university licenses.  
**What we need to know:**
- What do comparable data engineering courses charge (DataCamp, dbt Learn, Coursera data engineering)?
- What is the university budget cycle for technology curriculum licensing?
- What evidence does a university need to adopt a new tool in their curriculum?
- What is the corporate training budget for data engineering upskilling per employee?
- What certification is most valued in the data engineering job market today?

**Why it matters:** The Academy is a Phase 9+ revenue stream. Mispriced too high, no adoption. Mispriced too low, no revenue. The dbt Certified Developer model is the benchmark.

**Research method:** DataCamp pricing. dbt Learn (free but certification paid). Coursera data engineering specialization pricing. University procurement conversations.

---

## Category 6: User Experience Research

### R-017: The CLI vs GUI Preference Split
**What we assume:** Our target users are CLI-first and prefer terminal over UI.  
**What we need to know:**
- What percentage of analytics engineers use CLI tools daily vs prefer GUI tools?
- At what team size does the preference shift from CLI to GUI?
- What CLI tools do data engineers already use daily (dbt, git, poetry, docker)?
- What is the biggest friction point in our current CLI experience?
- Would a PipelineKit VS Code extension drive more adoption than CLI improvements?

**Why it matters:** If 40% of our ICP-002 (consultancy) target prefers GUI, a CLI-only product loses half the market at a critical growth stage.

**Research method:** Stack Overflow developer survey. dbt community survey. Direct questions to design partners.

---

### R-018: The First 10 Minutes Experience
**What we assume:** A new user can get to a successful pipelinekit run in under 10 minutes.  
**What we need to know:**
- What is the actual median time from git clone to first successful run?
- Where do new users get stuck (install, config, blueprint, first run, contracts)?
- What error messages cause the most confusion?
- What do users do when they get stuck (read docs, search, give up, ask community)?
- What does the ideal first-run experience feel like?

**Why it matters:** Every design partner that installs PipelineKit and does not get to a successful run in session 1 is a churned design partner. The 10-minute claim must be verified, not assumed.

**Research method:** Record screen shares with the first 3 design partners (with permission). Measure time to first successful run. Observe where they get stuck.

---

## Research Priority Order

Ordered by impact on current decisions:

| Priority | Code | Research item | Blocks |
|---|---|---|---|
| 🔴 P0 | R-001 | Real cost of pipeline setup | Website hero claim |
| 🔴 P0 | R-003 | Airbyte migration trigger | ICP-004 outreach |
| 🔴 P0 | R-018 | First 10 minutes experience | Design partner success |
| 🔴 P0 | R-006 | True competitive landscape | Sales conversations |
| 🟠 P1 | R-002 | Who makes buy decision | Outreach targeting |
| 🟠 P1 | R-007 | dlt ecosystem adoption | Blueprint onboarding |
| 🟠 P1 | R-008 | Soda vs alternatives | Quality layer choice |
| 🟠 P1 | R-015 | Pricing benchmarks | Pricing page |
| 🟡 P2 | R-009 | Data contract standards | DC SPEC accuracy |
| 🟡 P2 | R-011 | Blueprint verification standards | Trust positioning |
| 🟡 P2 | R-012 | AI diagnosis benchmarks | Confidence score UX |
| 🟡 P2 | R-017 | CLI vs GUI preference | Product roadmap |
| 🟢 P3 | R-004 | East African market | Phase 10 entry |
| 🟢 P3 | R-005 | Consultancy business model | ICP-002 depth |
| 🟢 P3 | R-010 | MCP ecosystem | Phase 9 investment |
| 🟢 P3 | R-013 | SOC 2 requirements | Phase 4 compliance |
| 🟢 P3 | R-014 | CBK regulations | Phase 4 East Africa |
| 🟢 P3 | R-016 | Academy revenue model | Phase 9 Academy |

---

## Research Methods Available

| Method | Best for | Cost | Time |
|---|---|---|---|
| Design partner conversations | R-001, R-002, R-018 | $0 | 30 min per session |
| LinkedIn polls | R-001, R-007, R-017 | $0 | 1 week to results |
| Reddit/dbt Slack analysis | R-003, R-006, R-008 | $0 | 2-3 hours |
| Public pricing pages | R-006, R-015, R-016 | $0 | 2-3 hours |
| GitHub/PyPI analytics | R-007, R-010 | $0 | 1 hour |
| Regulatory documents | R-013, R-014 | $0 | 4-8 hours per reg |
| Stack Overflow survey | R-001, R-017 | $0 | Report exists |
| dbt community survey | R-007, R-008, R-017 | $0 | Report exists |
| Direct network conversations | R-004, R-005 | $0 | 30 min per conversation |

---

## How Research Feeds Back into the Framework

```
Research finding
      ↓
Updates positioning claim OR SPEC assumption OR EMS priority
      ↓
Command Center revises relevant document
      ↓
Document committed to pipelinekit-internal
      ↓
Next sprint uses updated assumptions
```

**Example:**
R-008 finds that 70% of design partners use dbt tests not Soda.
→ SPEC for QM-1 updated to lead with dbt tests, make Soda optional
→ Blueprint quality checks restructured
→ Website "Quality Management" description updated
→ ICP-001 outreach message updated to reference dbt tests

---

## Research Log

Track completed research here:

| Date | Code | Finding | Document updated |
|---|---|---|---|
| | R-001 | | |
| | R-003 | | |
| | R-018 | | |

---

*Document: RESEARCH-AGENDA.md*  
*Location: pipelinekit-internal/reference/*  
*Owner: Eddy Mkwambe + Command Center*  
*Review: After each design partner conversation — add findings to Research Log*  
*Next review: After first 3 design partners onboarded*
