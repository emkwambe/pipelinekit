# WEB-001 — PipelineKit Marketing Website Design Specification

**Version:** 1.0  
**Date:** June 27, 2026  
**Author:** Command Center (Claude Chat) + Eddy Mkwambe  
**Status:** Approved — ready for implementation  
**Domain:** pipelinekit.dev  
**Stack:** Cloudflare Pages (static HTML/CSS/JS — no framework required for Phase 1)

---

## Governing Principles

The website exists to communicate authority.

Visitors should conclude within 30 seconds that PipelineKit is the AI-native operating system for trusted analytics pipelines.

**The website reduces uncertainty.**  
**The website increases trust.**  
**The website drives product adoption.**

Every word, every section, every CTA must serve one of these three goals. If it does not — it does not ship.

---

## Brand Identity

**Product name:** PipelineKit  
**Tagline:** The AI-native operating system for trusted analytics pipelines  
**Company:** Mpingo Systems LLC  
**Voice:** Precise. Confident. Engineering-first. No hype. No fluff.  
**Audience:** People who build and operate data pipelines professionally.

**What PipelineKit is NOT:**
- A no-code tool
- A SaaS dashboard
- Another dbt wrapper
- A Fivetran competitor

**What PipelineKit IS:**
- The operating system layer above dlt, dbt, and Soda
- The lifecycle platform: Design → Build → Distribute → Operate → Observe → Diagnose → Migrate → Govern → Learn
- AI-native: the AI proposes, the human approves, the system applies
- CLI-first: every capability is a command

---

## The Nine-Verb Lifecycle (Core Messaging Framework)

This is the product story. Every page references it.

```
DESIGN     → AI-assisted blueprint creation. Minutes not days.
BUILD      → Trusted pipelines without becoming infrastructure experts.
DISTRIBUTE → Proven architectures reused across every project.
OPERATE    → Run pipelines with confidence.
OBSERVE    → See what is failing, slow, or at risk — across all pipelines.
DIAGNOSE   → AI finds root causes instead of you searching logs.
MIGRATE    → Modernize Airbyte/Fivetran pipelines without starting over.
GOVERN     → Keep analytics trustworthy as systems evolve.
LEARN      → Train engineers on synthetic enterprises — not toy examples.
```

---

## Information Architecture

### Phase 1 (Launch — now)

```
pipelinekit.dev/                    ← Landing page
pipelinekit.dev/platform            ← The nine verbs, deep
pipelinekit.dev/blueprints          ← Blueprint catalog overview
pipelinekit.dev/migration           ← Migration Intelligence feature page
pipelinekit.dev/pricing             ← Three tiers
pipelinekit.dev/docs                ← Redirect to docs.pipelinekit.dev
pipelinekit.dev/about               ← Company + mission
pipelinekit.dev/contact             ← Design partner inquiry form
```

### Phase 2 (Growth)

```
pipelinekit.dev/enterprise          ← Enterprise feature page
pipelinekit.dev/blog                ← Engineering blog
pipelinekit.dev/changelog           ← Product updates
```

### Phase 3 (Platform)

```
pipelinekit.dev/academy             ← Link to academy.pipelinekit.dev
pipelinekit.dev/community           ← Link to community.pipelinekit.dev
```

---

## Navigation

```
[PipelineKit logo]    Platform  Blueprints  Migration  Pricing  Docs    [Get Started →]
```

Mobile: hamburger menu. The `Get Started →` CTA is always visible.

---

## Landing Page — `/`

### Hero Section

**Headline (H1):**
```
The AI-native operating system
for trusted analytics pipelines.
```

**Subheadline:**
```
Design, build, distribute, operate, diagnose, migrate, and govern
analytics pipelines — from a single CLI with verifiable trust at every step.
```

**CTAs:**
- Primary: `Install PipelineKit →` (links to docs quickstart)
- Secondary: `Browse Blueprint Catalog` (links to registry.pipelinekit.dev)

**Visual:** Terminal animation showing:
```bash
$ pipelinekit generate blueprint \
    --source stripe \
    --destination snowflake \
    --interactive

Proposing stripe-to-snowflake blueprint...

Plan ID:     plan-stripe-snowflake-20260627
Assets:      18 proposed
Confidence:  0.92

[a]ccept  [r]eject  [e]edit  [x]explain  [y]accept all
```

This is not a mockup. This is real output from the system.

---

### Trust Bar (below hero)

One line. No logos (no customers yet). Instead — verifiable facts:

```
3 production blueprints  ·  303 passing tests  ·  5 AI providers  ·  registry.pipelinekit.dev live
```

---

### The Lifecycle Section

**Headline:** `The complete pipeline lifecycle — in one platform.`

Nine cards in a vertical flow with connecting arrows. Each card:
- Verb (DESIGN, BUILD, DISTRIBUTE...)
- One sentence of value
- The CLI command(s)
- A micro-example of output

**DESIGN**
> AI-assisted blueprint creation. Design production-ready pipelines in minutes.
> `pipelinekit generate blueprint --interactive`

**BUILD**
> Initialize, validate, and configure trusted pipelines without becoming infrastructure experts.
> `pipelinekit init` · `pipelinekit validate`

**DISTRIBUTE**
> Install proven blueprints from the registry. Upgrade with governance. Roll back with confidence.
> `pipelinekit blueprint install` · `pipelinekit blueprint upgrade`

**OPERATE**
> Run pipelines with verifiable step results, contract enforcement, and quality checks.
> `pipelinekit run` · `pipelinekit status`

**OBSERVE**
> See what is failing, slow, or at risk — across all pipelines. Freshness SLAs. Contract violations. Volume anomalies.
> `pipelinekit health` · `pipelinekit observe` *(coming soon)*

**DIAGNOSE**
> AI finds root causes. You approve the fix. Evidence-first. Provider-agnostic.
> `pipelinekit diagnose --provider anthropic`

**MIGRATE**
> Translate Airbyte, Fivetran, or custom Python pipelines to PipelineKit in one command.
> `pipelinekit migrate analyze airbyte-connection.json`

**GOVERN**
> Data contracts. Quality checks. Freshness SLAs. Alert routing. Audit trail.
> `pipelinekit validate --contracts`

**LEARN**
> Train engineers on synthetic enterprises — not toy examples. Powered by RealityDB.
> `academy.pipelinekit.dev` *(coming soon)*

---

### The Trust Model Section

**Headline:** `AI proposes. You approve. Apply writes.`

**Body:**
```
PipelineKit's AI systems never execute without human confirmation.
Every proposal carries a confidence score, a list of assumptions,
and the decisions only you can make.

The system is your copilot — not your autopilot.
```

**Visual:** Three-column flow:
```
[AI Proposes]          [Human Approves]        [Apply Writes]
Confidence: 0.92       18 assets reviewed       Files written to disk
18 assets              Assumptions confirmed    Blueprint validated
10 decisions           Decisions made           Version recorded
```

---

### The Blueprint Section

**Headline:** `Verified blueprints. Production-ready from day one.`

**Three blueprint cards:**

```
┌─────────────────────────────┐
│ postgres → snowflake        │
│ v1.0.0 · ✅ Verified        │
│ 7/7 dbt tests · 0.7 min    │
│ [Install blueprint →]       │
└─────────────────────────────┘

┌─────────────────────────────┐
│ salesforce → snowflake      │
│ v1.0.0 · ✅ Verified        │
│ 9/9 dbt tests · 0.2 min    │
│ [Install blueprint →]       │
└─────────────────────────────┘

┌─────────────────────────────┐
│ stripe → snowflake          │
│ v1.0.0 · ✅ Verified        │
│ 43/43 dbt tests · 1 min    │
│ [Install blueprint →]       │
└─────────────────────────────┘
```

**CTA below:** `Browse full catalog →` (links to registry.pipelinekit.dev)

---

### The Five Providers Section

**Headline:** `Bring your own AI. Own your intelligence.`

**Body:**
```
PipelineKit works with every major AI provider — or none at all.
Run air-gapped on Ollama. Use Anthropic for diagnostics. Switch providers
without touching your pipeline configuration.
```

**Five provider badges:**
```
Anthropic (US)  ·  OpenAI (US)  ·  Mistral (EU)  ·  DeepSeek (China)  ·  Ollama (Local)
```

---

### Migration Section (teaser)

**Headline:** `Already running Airbyte or Fivetran?`

**Body:**
```
Analyze your existing configuration in one command.
PipelineKit maps every connection, identifies gaps,
and generates a draft pipelinekit.yaml — ready to validate.
```

**CTA:** `See how migration works →` (links to /migration)

---

### Design Partner Section

**Headline:** `We are looking for design partners.`

**Body:**
```
PipelineKit is production-ready and seeking 3-5 design partners
to shape the roadmap. You get direct access to the engineering team,
priority support, and pricing locked at the design partner rate.
```

**Requirements (honest):**
```
✓ You have existing analytics pipelines
✓ You are using Snowflake, BigQuery, or DuckDB
✓ You have experienced at least one pipeline failure in production
✓ You want to be part of shaping a platform
```

**CTA:** `Apply to be a design partner →` (links to /contact)

---

### Footer

```
PipelineKit by Mpingo Systems LLC
Raleigh, NC

Product          Resources        Company
Platform         Docs             About
Blueprints       Changelog        Contact
Migration        GitHub           Blog
Pricing          Registry

© 2026 Mpingo Systems LLC · Built with Cloudflare Pages
```

---

## Platform Page — `/platform`

Full expansion of the nine-verb lifecycle with:
- Deep description of each verb
- Real CLI output examples
- The architecture diagram (from docs/diagrams/02-five-layer-architecture.mmd)
- The trust model in detail

---

## Blueprints Page — `/blueprints`

- What a blueprint is (8 required assets)
- The verification standard (dbt tests, contracts, quality checks)
- The three current blueprints with full details
- How to install: `pipelinekit blueprint install postgres-to-snowflake`
- How to propose: `pipelinekit generate blueprint --interactive`
- Link to registry.pipelinekit.dev

---

## Migration Page — `/migration`

**Headline:** `Modernize your pipeline stack — without starting over.`

The migration story:
- Show an Airbyte config going in
- Show a pipelinekit.yaml coming out
- Show the gap analysis
- Show the confidence score

**The three supported sources:**
- Airbyte connection.json
- Fivetran connector config
- Custom Python (dlt, SQLAlchemy, psycopg2)

**CTA:** `Try migration analysis →` (links to docs quickstart)

---

## Pricing Page — `/pricing`

Three tiers. Honest. No "contact us for pricing" for the first two.

```
Solo                    Team                    Enterprise
$99/month               $499/month              Custom
────────────            ────────────            ────────────
1 user                  5 users                 Unlimited users
3 blueprints            Unlimited blueprints    Private registry
Community support       Email support           SLA + Slack support
All CLI commands        All CLI commands        Air-gap deployment
Public registry         Private registry        SSO + audit log
                        access                  BYOK AI providers

[Start free trial →]    [Start free trial →]    [Talk to us →]
```

**Design partner note:**
```
Currently accepting design partners at $0/month for 90 days
in exchange for feedback and case study rights.
[Apply →]
```

---

## About Page — `/about`

**The mission:**
```
Analytics pipelines are the infrastructure of modern business intelligence.
They fail silently, break without warning, and resist diagnosis.

PipelineKit exists to make analytics pipelines trustworthy — by design,
not by accident.
```

**The founder:**
```
Eddy Mkwambe
Founder & Technical Director, Mpingo Systems LLC

MS Strategic Analytics, Brandeis University
MS Mathematical Modeling, University of Dar es Salaam
12 years mathematics education

Built for practitioners. Grounded in evidence. Deployed from Raleigh, NC.
```

---

## Contact Page — `/contact`

**Design partner inquiry form:**
- Name
- Email
- Company
- Current pipeline stack (Airbyte / Fivetran / Custom / dbt only)
- Biggest pipeline pain point (text field)
- Monthly pipeline runs (estimate)
- How did you hear about PipelineKit

**Response commitment:** "We respond to every inquiry within 48 hours."

---

## Design Language

**Colors:**
```
Background:    #0a0a0a (near black — engineering aesthetic)
Surface:       #111111
Border:        #222222
Primary:       #00d4aa (teal — precision, trust)
Text primary:  #ffffff
Text secondary:#888888
Code:          #1a1a2e (dark blue)
Success:       #22c55e
Warning:       #f59e0b
Error:         #ef4444
```

**Typography:**
```
Headings:  Inter (700, 600)
Body:      Inter (400, 500)
Code:      JetBrains Mono (400)
```

**Spacing:** 8px base grid. Generous white space. Content never wider than 1200px.

**Tone of visuals:**
- Terminal output (real, not mocked)
- CLI commands (copy-pasteable)
- Diagrams from docs/diagrams/ (Mermaid rendered)
- No stock photography
- No abstract gradients
- No "enterprise software" blue gradients

---

## Performance Budget

- First Contentful Paint: < 1.2s
- Largest Contentful Paint: < 2.0s
- Total page weight (home): < 200KB
- No JavaScript frameworks
- No external fonts (use system font stack fallback)
- Cloudflare CDN handles the rest

---

## SEO

**Target keywords (Phase 1):**
- "analytics pipeline CLI"
- "dbt pipeline framework"
- "Airbyte migration tool"
- "data pipeline operating system"
- "pipelinekit"

**Meta tags for home:**
```html
<title>PipelineKit — AI-native operating system for trusted analytics pipelines</title>
<meta name="description" content="Design, build, distribute, operate, diagnose, migrate, and govern analytics pipelines from a single CLI. Verified blueprints. AI diagnostics. Production-ready.">
```

---

## Analytics Events (Phase 1)

Simple. Privacy-respecting. Cloudflare Web Analytics (no cookie banner needed).

Track:
- Page views by URL
- CTA clicks (Get Started, Install, Browse Catalog, Apply Design Partner)
- Blueprint card clicks
- Time on platform page

---

## Implementation Order

```
Week 1: index.html (landing page)
Week 2: /pricing, /about, /contact
Week 3: /platform (full lifecycle page)
Week 4: /blueprints, /migration
```

Deploy each page as it is ready. Cloudflare Pages auto-deploys on push to main.

---

## Subdomain Architecture (full)

```
pipelinekit.dev              ← this spec (Phase 1 now)
docs.pipelinekit.dev         ← Phase 1 (redirect to GitHub docs initially)
registry.pipelinekit.dev     ← ✅ LIVE
learn.pipelinekit.dev        ← Phase 2
blueprints.pipelinekit.dev   ← Phase 2 (marketplace UI)
playground.pipelinekit.dev   ← Phase 2 (interactive demo)
enterprise.pipelinekit.dev   ← Phase 2
academy.pipelinekit.dev      ← Phase 3
community.pipelinekit.dev    ← Phase 3
status.pipelinekit.dev       ← Phase 3
api.pipelinekit.dev          ← Phase 3
auth.pipelinekit.dev         ← Phase 4
cloud.pipelinekit.dev        ← Phase 4
ai.pipelinekit.dev           ← Phase 4
mcp.pipelinekit.dev          ← Phase 4
```

---

*Document: WEB-001-Marketing-Website-Specification.md*  
*Location: docs/web/WEB-001-Marketing-Website-Specification.md*  
*Owner: Command Center + Eddy Mkwambe*
