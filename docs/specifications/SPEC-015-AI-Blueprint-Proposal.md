# SPEC-015-AI-Blueprint-Proposal.md

**Status:** Approved  
**Version:** 2.0  
**Owner:** diagnostics-engineer (AI layer) + blueprint-engineer  
**Phase:** 6 — Sprint 6-5  
**Date:** June 26, 2026  
**ADRs:** ADR-018 v2 (Blueprint Proposal Governance), ADR-007, ADR-005  
**Schemas:** schemas/blueprint.schema.json, schemas/blueprint_proposal.schema.json (new)  
**Depends on:** SPEC-005, SPEC-006, SPEC-013

---

## Purpose

Define the AI Blueprint Proposal subsystem.

**Naming:** This is a proposal system, not a generation system. PipelineKit proposes blueprint artifacts. Humans approve what becomes part of the repository.

Every proposed artifact moves through explicit states:
```
proposed → approved → written → validated
```

Nothing skips states. Nothing touches the filesystem without explicit human approval.

---

## New Files

```
src/pipelinekit/ai/
├── proposal_models.py        BlueprintProposal, ProposedAsset, ProposalContext
├── blueprint_proposer.py     BlueprintProposer
└── adapter_registry.py       AdapterCapabilityRegistry

src/pipelinekit/cli/
└── generate.py               pipelinekit generate blueprint / show
                              pipelinekit apply plan

schemas/
└── blueprint_proposal.schema.json

tests/ai/
└── test_blueprint_proposer.py

tests/cli/
└── test_generate_and_apply.py
```

## Modified Files

```
src/pipelinekit/ai/provider.py         Add propose_blueprint() to LLMProvider Protocol
src/pipelinekit/ai/providers/*.py      Implement propose_blueprint() in all 5 providers
src/pipelinekit/cli/main.py            Register generate + apply command groups
src/pipelinekit/state/db.py            Add blueprint_proposals table
src/pipelinekit/core/errors.py         Add ProposalError
docs/reference/Error-Codes.md         Add PK-GEN-* codes
```

---

## Data Models

### ProposedAsset

```python
# src/pipelinekit/ai/proposal_models.py

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class AssetState(Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED   = "edited"
    WRITTEN  = "written"
    VALIDATED = "validated"

@dataclass
class AssetProvenance:
    generated_by: str = "pipelinekit"
    generation_mode: str = "ai_proposed"
    model: str = ""
    plan_id: str = ""
    source_evidence: list[dict] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unsupported_areas: list[str] = field(default_factory=list)
    requires_human_decisions: list[str] = field(default_factory=list)
    requires_human_approval: bool = True

@dataclass
class ProposedAsset:
    asset_type: str
    filename: str            # relative path within blueprint directory
    content: str             # proposed file content
    state: AssetState = AssetState.PROPOSED
    provenance: Optional[AssetProvenance] = None
    validation_error: Optional[str] = None
    edit_history: list[str] = field(default_factory=list)

    def approve(self) -> None:
        """Transition proposed → approved."""
        if self.state != AssetState.PROPOSED and self.state != AssetState.EDITED:
            raise ValueError(f"Cannot approve asset in state {self.state}")
        self.state = AssetState.APPROVED

    def reject(self) -> None:
        """Transition proposed → rejected."""
        self.state = AssetState.REJECTED

    def mark_written(self) -> None:
        """Transition approved → written. Called by BlueprintProposer.apply() only."""
        if self.state != AssetState.APPROVED:
            raise ValueError(f"Cannot write asset in state {self.state}")
        self.state = AssetState.WRITTEN
```

### ProposalContext

```python
@dataclass
class ProposalContext:
    source_type: str
    destination_type: str
    tables: list[str]
    existing_blueprints: list[dict]      # patterns from BlueprintRegistry
    source_config_fields: list[str]      # from SourceConfig + AdapterCapabilityRegistry
    supported_tables: list[str]          # from AdapterCapabilityRegistry
    blueprint_schema: dict               # schemas/blueprint.schema.json
    contract_examples: list[dict]        # from contracts/ directory
```

### BlueprintProposal

```python
@dataclass
class BlueprintProposal:
    plan_id: str
    blueprint_name: str
    source_type: str
    destination_type: str
    tables: list[str]
    assets: list[ProposedAsset]
    confidence: float                    # 0.0–1.0
    assumptions: list[str]
    unsupported_areas: list[str]
    requires_human_decisions: list[str]
    provider: str
    generated_at: str
    can_auto_apply: bool = False         # always False
    applied: bool = False
```

---

## AdapterCapabilityRegistry

```python
# src/pipelinekit/ai/adapter_registry.py

SUPPORTED_SOURCES = {
    "postgres": {
        "dlt_source": "sql_database",
        "credential_fields": ["host", "port", "database", "user", "password"],
        "tables": "configurable",
        "notes": "Any PostgreSQL table is supported",
    },
    "salesforce": {
        "dlt_source": "salesforce",
        "credential_fields": ["username", "password", "security_token"],
        "tables": ["accounts", "opportunities", "contacts", "leads", "cases"],
    },
    "stripe": {
        "dlt_source": "stripe_analytics",
        "credential_fields": ["api_key"],
        "tables": ["charges", "customers", "subscriptions", "invoices", "events", "refunds"],
    },
}

SUPPORTED_DESTINATIONS = {
    "snowflake": {
        "dlt_destination": "snowflake",
        "credential_fields": ["account", "user", "password", "database", "warehouse"],
    },
    "bigquery": {
        "dlt_destination": "bigquery",
        "credential_fields": ["project", "dataset", "credentials_path"],
    },
    "duckdb": {
        "dlt_destination": "duckdb",
        "credential_fields": ["path"],
        "notes": "Local only — for development and testing",
    },
}

class AdapterCapabilityRegistry:
    def is_source_supported(self, source_type: str) -> bool: ...
    def is_destination_supported(self, destination_type: str) -> bool: ...
    def get_source_info(self, source_type: str) -> dict: ...
    def get_destination_info(self, destination_type: str) -> dict: ...
    def get_supported_tables(self, source_type: str) -> list[str] | str: ...
```

---

## LLMProvider Extension

Add `propose_blueprint()` to the Protocol (note: renamed from generate_blueprint):

```python
def propose_blueprint(
    self,
    context: "ProposalContext",
) -> "BlueprintProposal":
    """
    Propose a complete blueprint from context.
    Returns BlueprintProposal — never writes files (ADR-018).
    Every asset includes provenance metadata.
    can_auto_apply is always False.
    """
    ...
```

---

## BlueprintProposer

```python
# src/pipelinekit/ai/blueprint_proposer.py

class BlueprintProposer:
    """AI Blueprint Proposal orchestrator.

    Proposes. Does not write.
    ADR-018: proposed → approved → written → validated.
    AI proposes — human approves — apply() writes.
    """

    def __init__(self, config: PipelineConfig, provider: LLMProvider):
        self.config = config
        self.provider = provider
        self.registry_reader = BlueprintRegistry()
        self.adapter_registry = AdapterCapabilityRegistry()

    def propose(
        self,
        source_type: str,
        destination_type: str,
        tables: list[str],
        cwd: Path | None = None,
    ) -> BlueprintProposal:
        """
        1. Check adapter support (fail fast with PK-GEN-006 if unsupported)
        2. Build ProposalContext
        3. Call provider.propose_blueprint(context)
        4. Attach provenance to each asset
        5. Validate blueprint.json asset against schema
        6. Force can_auto_apply = False
        7. Store proposal in state.db
        8. Return BlueprintProposal — no files written
        """

    def apply(
        self,
        proposal: BlueprintProposal,
        cwd: Path | None = None,
    ) -> list[str]:
        """
        Write ONLY approved assets to blueprints/<name>/.
        Strip provenance metadata from each asset before writing.
        Transition each written asset state: approved → written.
        Raises ProposalError(PK-GEN-003) if no assets approved.
        Raises ProposalError(PK-GEN-004) if blueprint directory already exists.
        Returns list of written paths.
        """

    def _build_context(self, ...) -> ProposalContext: ...
    def _attach_provenance(self, asset: ProposedAsset, plan_id: str, ...) -> None: ...
    def _strip_provenance(self, content: str) -> str: ...
    def _validate_blueprint_json(self, content: str) -> Optional[str]: ...
```

---

## Provider System Prompt

```python
PROPOSAL_SYSTEM_PROMPT = """You are a PipelineKit blueprint engineer.
Propose a complete analytics pipeline blueprint from the provided specification.

You are PROPOSING, not generating. Your output will be reviewed by a human before
any file is written. Be explicit about your assumptions and limitations.

Return a JSON object with this structure:
{
  "confidence": 0.0-1.0,
  "assumptions": ["list of what you assumed about the source schema"],
  "unsupported_areas": ["list of what you could not propose"],
  "requires_human_decisions": ["list of decisions the human must make"],
  "assets": [
    {
      "asset_type": "blueprint_json|example_yaml|ingestion_pipeline|...",
      "filename": "relative/path/in/blueprint",
      "content": "full file content",
      "confidence_note": "why you are or are not confident about this asset"
    }
  ]
}

Required assets (all 13):
blueprint_json, example_yaml, ingestion_pipeline, dbt_project, dbt_profiles,
dbt_sources, dbt_staging_models, dbt_core_models, contracts, quality_checks,
alerts_config, readme, runbook

Critical rules:
- All credentials use ${VAR} interpolation — NEVER hardcoded values
- dbt sources use {{ env_var('DBT_SOURCE_DATABASE') }} and {{ env_var('DBT_SOURCE_SCHEMA') }}
- Staging models use {{ source('source_name', 'table') }}
- Core models use {{ ref('staging_model') }}
- can_auto_apply must be false
- Only use tables and columns from the adapter capability registry provided
- If you are uncertain about a column name, mark it in requires_human_decisions
- Follow existing blueprint patterns exactly for structure

Return ONLY the JSON object. No markdown. No preamble."""
```

---

## CLI Commands

### pipelinekit generate blueprint

```python
@generate_app.command("blueprint")
def generate_blueprint_command(
    source: str = typer.Option(..., "--source", "-s"),
    destination: str = typer.Option(..., "--destination", "-d"),
    tables: str = typer.Option(..., "--tables", "-t"),
    provider: str = typer.Option(None, "--provider", "-p"),
    name: str = typer.Option(None, "--name", "-n"),
    plan: bool = typer.Option(False, "--plan",
        help="Generate plan only, no interactive review."),
    interactive: bool = typer.Option(False, "--interactive",
        help="Generate and review interactively in one session."),
):
    """Propose a blueprint using AI. Review before applying."""
```

**`--plan` output:**
```
Proposing stripe-to-snowflake blueprint...
Reading adapter capabilities...
Reading 2 existing blueprints as patterns...
Calling anthropic...

Blueprint Proposal Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plan ID:     plan-stripe-snowflake-20260626-143200
Blueprint:   stripe-to-snowflake
Source:      stripe (charges, customers)
Destination: snowflake
Assets:      13 proposed
Confidence:  0.87

Assumptions:
  · Stripe charges table has: id, amount, currency, status, created
  · Snowflake destination uses raw schema for dlt landing

Requires your decision:
  · Verify column names match your Stripe API version
  · Set freshness SLA in contracts/charges.yaml

No files written.

Review:  pipelinekit generate show plan-stripe-snowflake-20260626-143200
Apply:   pipelinekit apply plan plan-stripe-snowflake-20260626-143200
```

**`--interactive` review loop:**
```
Asset 1 of 13: blueprint.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[content shown]
Confidence: 0.95 — Strong pattern match from postgres-to-snowflake

[a]ccept  [r]eject  [e]dit  [x]explain  [y-all]accept remaining  [q]quit: 
```

**`x` explain option:**
```
[x]explain:
  This blueprint.json was proposed based on:
  · postgres-to-snowflake/blueprint.json (pattern)
  · salesforce-to-snowflake/blueprint.json (pattern)
  · schemas/blueprint.schema.json (structural constraints)
  
  I adapted the source type and table list for Stripe.
  The deploy_time_minutes claim of 60 is an estimate — verify after your first run.
```

### pipelinekit apply plan

```python
@apply_app.command("plan")
def apply_plan_command(
    plan_id: str = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes", "-y",
        help="Apply all approved assets without confirmation."),
):
    """Write approved assets from a proposal plan to blueprints/<name>/."""
```

---

## State Extension

```sql
CREATE TABLE IF NOT EXISTS blueprint_proposals (
    plan_id         TEXT PRIMARY KEY,
    blueprint_name  TEXT NOT NULL,
    source_type     TEXT NOT NULL,
    destination_type TEXT NOT NULL,
    tables          TEXT,           -- JSON array
    assets          TEXT,           -- JSON array with state
    confidence      REAL,
    assumptions     TEXT,           -- JSON array
    unsupported     TEXT,           -- JSON array
    decisions       TEXT,           -- JSON array
    provider        TEXT,
    can_auto_apply  INTEGER DEFAULT 0,
    applied         INTEGER DEFAULT 0,
    proposed_at     TEXT NOT NULL,
    applied_at      TEXT
);
```

---

## Error Codes

| Code | Meaning |
|---|---|
| `PK-GEN-001` | Proposal failed — AI provider error |
| `PK-GEN-002` | Proposed plan failed schema validation |
| `PK-GEN-003` | Apply failed — no assets in approved state |
| `PK-GEN-004` | Blueprint directory already exists |
| `PK-GEN-005` | Proposed blueprint.json failed schema validation |
| `PK-GEN-006` | Source or destination type not supported by adapter registry |
| `PK-GEN-007` | Asset state transition violation |

---

## Test Requirements

All 229 prior tests must pass.

**tests/ai/test_blueprint_proposer.py** — 6 tests:
- `propose()` returns `BlueprintProposal` — no files written (tmp_path verified)
- `can_auto_apply` always False
- `apply()` writes only approved assets (state = APPROVED)
- `apply()` raises `ProposalError(PK-GEN-003)` when no assets approved
- `apply()` raises `ProposalError(PK-GEN-004)` when blueprint directory exists
- Unsupported source raises `ProposalError(PK-GEN-006)` before AI call

**tests/ai/test_adapter_registry.py** — 3 tests:
- `is_source_supported()` returns True for postgres, salesforce, stripe
- `is_source_supported()` returns False for oracle, mysql
- `get_supported_tables()` returns correct tables for salesforce

**tests/cli/test_generate_and_apply.py** — 4 tests:
- `pipelinekit generate blueprint --help` exits 0
- `pipelinekit generate show --help` exits 0
- `pipelinekit apply plan --help` exits 0
- `pipelinekit generate blueprint --source oracle` fails with PK-GEN-006 message

---

## Definition of Done

```
✓ AdapterCapabilityRegistry — postgres, salesforce, stripe, snowflake, bigquery, duckdb
✓ BlueprintProposal with confidence, assumptions, unsupported_areas, requires_human_decisions
✓ Every ProposedAsset has AssetState machine (proposed/approved/rejected/edited/written)
✓ propose() returns plan — verified no files written in tmp_path
✓ apply() writes only approved assets (state = APPROVED)
✓ can_auto_apply always False
✓ PK-GEN-006 fires before AI call for unsupported sources
✓ Provenance metadata attached to every asset, stripped on write
✓ pipelinekit generate blueprint --plan shows plan ID, no files
✓ pipelinekit generate blueprint --interactive shows per-asset review
✓ pipelinekit apply plan <id> writes approved assets
✓ [x]explain option shows provenance for any asset
✓ [y-all] batch approve option available after full review
✓ All 229 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
✓ Existing blueprints untouched
```

---

## The Test That Defines Success

```powershell
# Propose Blueprint #003 (Stripe → Snowflake) using AI
pipelinekit generate blueprint `
  --source stripe `
  --destination snowflake `
  --tables charges,customers `
  --plan

# Review the proposal
pipelinekit generate show plan-stripe-snowflake-*

# Apply approved assets interactively
pipelinekit apply plan plan-stripe-snowflake-* --interactive

# Validate the proposed blueprint
pipelinekit blueprint validate
pipelinekit blueprint info stripe-to-snowflake

# Verify locally
.\scripts\verify-blueprint-003.ps1 -Local
```

When that sequence produces a valid, locally-verified blueprint — Blueprint #003 was proposed by AI and approved by a human. The catalog grows without hand-crafting.

---

## Strategic Significance

**Before Sprint 6-5:** 2 blueprints, hand-crafted, ~2 hours each  
**After Sprint 6-5:** N blueprints, AI-proposed, ~10 minutes including human review

The moat is not the catalog size. It is the proposal system.

The naming matters too. Telling a design partner:

> "PipelineKit proposed this blueprint based on your source schema. You reviewed and approved each asset before it was written."

That is a trust statement. It is the product.
