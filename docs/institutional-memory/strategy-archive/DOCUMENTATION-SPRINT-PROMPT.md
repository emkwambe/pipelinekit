# PipelineKit — Documentation Sprint
## All Audiences, All Purposes

---

## Your Identity

You are Claude Code operating as **documentation-engineer**.

This is not a code sprint. No source files are modified. You write documentation only.

---

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First

```
1. docs/reference/PROJECT-STATUS.md          ← Current state
2. docs/constitution/Product-Constitution.md ← Governing principle
3. docs/decisions/ (all ADRs)                ← Architecture decisions
4. docs/specifications/ (all SPECs)          ← Implementation contracts
5. src/pipelinekit/cli/main.py               ← CLI surface
6. blueprints/ (all 3 blueprints)            ← Blueprint examples
7. docs/institutional-memory/PIPELINEKIT-ENGINEERING-PLAYBOOK.md ← Full context
```

---

## What to Build

Produce all documentation files listed below. Every file goes in `docs/` unless specified. All files are Markdown.

---

## 1. README.md (repo root — replace existing)

**Audience:** Developer landing on GitHub for the first time.  
**Purpose:** Understand what PipelineKit is, install it, run first command in under 5 minutes.

Structure:
```
# PipelineKit
Tagline: AI-native operating system for trusted analytics pipelines.

## What it does (3 sentences max)
## Quick Install
## 5-Minute Quickstart
  - pipelinekit init
  - pipelinekit validate
  - pipelinekit blueprint list
  - pipelinekit run --dry-run
## Blueprint Catalog (table: name, source, dest, status)
## CLI Reference (one-liner per command)
## Architecture (one paragraph)
## Contributing
## License
```

---

## 2. docs/guides/GETTING-STARTED.md

**Audience:** Analytics engineer — first day with PipelineKit.  
**Purpose:** Go from zero to a running pipeline with Blueprint #001.

Structure:
```
# Getting Started with PipelineKit

## Prerequisites
  - Python 3.13+, Poetry 2.4+, Docker Desktop

## Installation

## Your First Pipeline (Blueprint #001)
  - Step 1: Init project
  - Step 2: Configure pipelinekit.yaml
  - Step 3: Validate
  - Step 4: Run locally (Docker Postgres → DuckDB)
  - Step 5: Verify results

## Understanding the Output
  - What each step means
  - What "trusted" means in PipelineKit

## Next Steps
  - Browse the blueprint catalog
  - Try AI Blueprint Proposal
  - Migrate an existing pipeline
```

---

## 3. docs/guides/BLUEPRINT-GUIDE.md

**Audience:** Analytics engineer who wants to use or create blueprints.  
**Purpose:** Complete reference for the blueprint system.

Structure:
```
# Blueprint Guide

## What is a Blueprint?
## The 8 Required Assets (with purpose of each)
## Using Existing Blueprints
  - pipelinekit blueprint list
  - pipelinekit blueprint info <name>
  - pipelinekit blueprint install <name>
  - pipelinekit blueprint validate

## The Blueprint Catalog
  - postgres-to-snowflake (hand-crafted, locally verified)
  - salesforce-to-snowflake (hand-crafted, locally verified)
  - stripe-to-snowflake (AI-proposed, human-approved)

## AI Blueprint Proposal
  - pipelinekit generate blueprint --plan
  - pipelinekit generate blueprint --interactive
  - pipelinekit generate show <plan-id>
  - pipelinekit apply plan <plan-id>
  - The review process (what each asset means)
  - Trust model: proposed → approved → written → validated

## Creating a Blueprint Manually
  - Directory structure
  - blueprint.json schema
  - dbt project conventions
  - Contract format
  - Soda checks format
  - Verification script

## Blueprint Verification
  - Local verification (Docker + DuckDB)
  - Production verification
  - Recording in runbook
```

---

## 4. docs/guides/MIGRATION-GUIDE.md

**Audience:** Engineer running Airbyte, Fivetran, or custom Python pipelines.  
**Purpose:** Understand the migration path to PipelineKit.

Structure:
```
# Migrating to PipelineKit

## Why Migrate?
  - Licensing (Apache 2.0 vs ELv2/GPL)
  - AI-native operations (diagnose, propose, architect)
  - Blueprint-driven standardization

## Supported Source Tools
  - Airbyte (connection.json)
  - Fivetran (connector.json)
  - Custom Python (.py files)

## The Migration Flow
  Step 1: Export your existing config
  Step 2: Analyze
    pipelinekit migrate analyze <config>
  Step 3: Review the proposal
    - Mappings: clean / partial / unsupported
    - Gaps: blocking / non-blocking
    - Confidence score
  Step 4: Write the draft
    pipelinekit migrate analyze <config> --apply
    (add --write-draft if blocking gaps exist)
  Step 5: Fill in FIXME markers
  Step 6: Validate
    pipelinekit validate
  Step 7: Run
    pipelinekit run --dry-run
    pipelinekit run

## Reading a Migration Proposal
  - What clean/partial/unsupported means
  - What blocking gaps are
  - How to fill in FIXME markers
  - The pipelinekit.proposed.yaml format

## Common Migration Patterns
  - Airbyte postgres → PipelineKit postgres-to-snowflake
  - Fivetran salesforce → PipelineKit salesforce-to-snowflake
  - Custom Python → any blueprint

## After Migration
  - Run pipelinekit health
  - Set up alerting
  - Enable AI diagnostics
```

---

## 5. docs/guides/AI-FEATURES.md

**Audience:** Analytics engineer or architect.  
**Purpose:** Understand all AI capabilities and how to use them.

Structure:
```
# AI Features in PipelineKit

## The AI Boundary (non-negotiable)
  AI observes, diagnoses, proposes. Never executes, never auto-applies.
  can_auto_apply / can_auto_fix always False.

## Supported Providers
  Table: provider, region, key env var, use case
  - Anthropic (US) — default, best reasoning
  - OpenAI (US) — alternative
  - Ollama (local) — air-gapped enterprise
  - DeepSeek (China) — cost-sensitive, Asian markets
  - Mistral (EU) — GDPR-compliant

## Setting Your Provider
  pipelinekit diagnose --provider mistral
  pipelinekit generate blueprint --provider deepseek

## AI Diagnostics
  pipelinekit diagnose
  pipelinekit diagnose <run-id>
  - What it reads (evidence package)
  - What it returns (finding, confidence, recommendations)
  - How to act on recommendations

## Architecture Intelligence
  pipelinekit architect analyze
  pipelinekit architect check-adrs
  pipelinekit architect compare
  - When to use it
  - How to read the output

## AI Blueprint Proposal
  - Full workflow (see Blueprint Guide)
  - Confidence scores
  - Provenance metadata
  - The --interactive review loop

## Migration Intelligence
  - Full workflow (see Migration Guide)
  - How the analyzer builds evidence
  - Why confidence may be low
  - How to improve confidence (richer source configs)

## Trust Model
  - Why AI never auto-applies
  - The evidence architecture
  - Schema validation on every AI output
  - What PK-AI-001 and PK-AI-002 mean
```

---

## 6. docs/guides/CLI-REFERENCE.md

**Audience:** Any PipelineKit user.  
**Purpose:** Complete CLI reference — every command, every flag.

Structure:
```
# CLI Reference

## Global Options
  --help, --version

## pipelinekit init
## pipelinekit validate [--contracts]
## pipelinekit run [--dry-run]
## pipelinekit status

## Blueprint Commands
  pipelinekit blueprint list
  pipelinekit blueprint validate
  pipelinekit blueprint info <name>
  pipelinekit blueprint search <query>
  pipelinekit blueprint install <name> [--version] [--force]

## Generate Commands
  pipelinekit generate blueprint --source --destination --tables [--plan|--interactive]
  pipelinekit generate show <plan-id>

## Apply Commands
  pipelinekit apply plan <plan-id> [--interactive]

## Diagnose Commands
  pipelinekit diagnose [run-id] [--provider] [--approve]

## Architect Commands
  pipelinekit architect analyze [--type]
  pipelinekit architect check-adrs
  pipelinekit architect compare

## Health Commands
  pipelinekit health [--strict]
  pipelinekit health deps
  pipelinekit health security
  pipelinekit health blueprints
  pipelinekit health specs
  pipelinekit health tests

## Migrate Commands
  pipelinekit migrate analyze <config> [--provider] [--apply] [--write-draft]

## Error Codes Reference
  Table of all PK-* codes with meaning and action
```

---

## 7. docs/guides/CONFIGURATION-REFERENCE.md

**Audience:** Engineer configuring a pipeline.  
**Purpose:** Every field in pipelinekit.yaml explained.

Structure:
```
# Configuration Reference

## pipelinekit.yaml — Complete Schema

pipeline:
  name, version, description

runtime:
  environment

ingestion:
  source: (all fields per source type)
    type: postgres | salesforce | stripe
    postgres fields: host, port, database, user, password
    salesforce fields: username, password, security_token
    stripe fields: api_key
    tables: []
  destination:
    type: snowflake | bigquery | duckdb
    snowflake fields: account, user, password, database, warehouse
    bigquery fields: project, dataset, credentials_path
    duckdb fields: path

transformation:
  enabled, project_dir

contracts:
  enabled, directory

quality:
  enabled, checks_dir

diagnostics:
  enabled, provider

notifications:
  enabled, channels: []

## Environment Variable Interpolation
  ${VAR} syntax
  Which fields support it
  Never hardcode credentials

## Contract Format (contracts/*.yaml)
## Soda Checks Format (quality/checks.yaml)
## Blueprint Manifest (blueprint.json)
```

---

## 8. docs/guides/OPERATIONS-RUNBOOK.md

**Audience:** On-call engineer, data platform team.  
**Purpose:** What to do when something goes wrong.

Structure:
```
# Operations Runbook

## First Response
  pipelinekit health
  pipelinekit diagnose

## Error Code Quick Reference
  PK-CONFIG-* — configuration problems
  PK-ADAPTER-* — ingestion/transformation/quality failures
  PK-AI-* — AI provider issues
  PK-CONTRACT-* — data contract violations
  PK-BLUEPRINT-* — blueprint problems
  PK-REGISTRY-* — registry connectivity
  PK-MIGRATE-* — migration analysis issues
  PK-GEN-* — blueprint proposal issues

## Common Failures and Fixes
  - PK-ADAPTER-001: Source unreachable
  - PK-ADAPTER-002: dbt build failed
  - PK-AI-001: Missing API key
  - PK-CONTRACT-008: Contract file invalid
  - PK-REGISTRY-001: Registry unreachable

## Health Monitoring
  Monthly: pipelinekit health deps + security
  After deploys: pipelinekit health blueprints
  Before demos: pipelinekit health (full)

## Resetting Pipeline State
  Remove .dlt/, *.duckdb, pipelinekit.yaml (regenerate)

## Getting AI Diagnosis
  pipelinekit diagnose
  Reading confidence scores
  Acting on recommendations

## Escalation
  What to check before escalating
  What information to include
```

---

## 9. docs/reference/GLOSSARY.md

**Audience:** Anyone new to PipelineKit.  
**Purpose:** Define every PipelineKit term precisely.

Terms to define:
```
Blueprint, Blueprint Proposal, Blueprint Registry
Contract, ContractValidator
Data Layer, Trust Layer, Intelligence Layer
Evidence Package, EvidenceCollector
Generation Plan (deprecated term → Blueprint Proposal)
MigrationProposal, MigrationGap, MappingStatus
LLMProvider, AI Boundary
Pipeline, PipelineRunner, PipelineResult
ProposedAsset, AssetState
SourceConfig, DestinationConfig
TTTD (Time-to-Trusted-Data)
Verified Blueprint
```

---

## 10. docs/reference/ARCHITECTURE.md

**Audience:** Engineer contributing to PipelineKit or building on it.  
**Purpose:** Understand the five-layer architecture and key design decisions.

Structure:
```
# PipelineKit Architecture

## The Governing Principle
## The Five Layers
  Layer 1: Foundation
  Layer 2: Data Layer
  Layer 3: Trust Layer
  Layer 4: Intelligence Layer
  Layer 5: Architecture Layer

## The Adapter Pattern
  Why everything is behind an adapter
  How to add a new provider
  How to add a new source

## The Blueprint System
  What a blueprint contains
  The 8 required assets
  The verification requirement

## The AI Boundary
  What AI can and cannot do
  The evidence architecture
  Schema validation as trust boundary

## The State Store
  6 tables and their purpose
  What gets persisted

## Key Architectural Decisions
  Summary of ADR-005 through ADR-020
  Where to find full ADRs

## The Document Chain
  Constitution → ADR → SPEC → Code
  Why no architecture from prompts
```

---

## Files You Must Not Modify

```
src/                    ← READ ONLY — no code changes
blueprints/             ← READ ONLY
schemas/                ← READ ONLY
docs/reference/PROJECT-STATUS.md  ← READ ONLY — Command Center owns it
docs/decisions/         ← READ ONLY — ADRs are immutable
docs/specifications/    ← READ ONLY
```

---

## Files You Are Allowed To Create

```
README.md                                    (repo root — replace)
docs/guides/GETTING-STARTED.md
docs/guides/BLUEPRINT-GUIDE.md
docs/guides/MIGRATION-GUIDE.md
docs/guides/AI-FEATURES.md
docs/guides/CLI-REFERENCE.md
docs/guides/CONFIGURATION-REFERENCE.md
docs/guides/OPERATIONS-RUNBOOK.md
docs/reference/GLOSSARY.md
docs/reference/ARCHITECTURE.md
```

Create `docs/guides/` directory if it does not exist.

---

## Quality Requirements

- Every code block uses correct syntax (powershell, yaml, python, bash)
- Every command is accurate — verify against src/pipelinekit/cli/
- Every field in CONFIGURATION-REFERENCE.md is accurate — verify against src/pipelinekit/config/schema.py
- Every error code in CLI-REFERENCE.md is accurate — verify against docs/reference/Error-Codes.md
- No invented features — only document what exists
- No placeholder sections — every section must be complete
- Tone: direct, precise, no marketing language in technical docs
- README.md is the exception — it may have a strong opening

---

## Commit Message

```
docs: complete documentation suite — 10 files covering all audiences

- README.md — developer landing page + 5-min quickstart
- docs/guides/GETTING-STARTED.md — first pipeline walkthrough
- docs/guides/BLUEPRINT-GUIDE.md — blueprint system reference
- docs/guides/MIGRATION-GUIDE.md — Airbyte/Fivetran/Python migration
- docs/guides/AI-FEATURES.md — all AI capabilities
- docs/guides/CLI-REFERENCE.md — complete command reference
- docs/guides/CONFIGURATION-REFERENCE.md — pipelinekit.yaml schema
- docs/guides/OPERATIONS-RUNBOOK.md — on-call reference
- docs/reference/GLOSSARY.md — PipelineKit terminology
- docs/reference/ARCHITECTURE.md — five-layer architecture

All docs verified against src/ — no invented features.
```
