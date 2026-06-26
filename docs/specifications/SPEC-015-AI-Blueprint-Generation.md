# SPEC-015-AI-Blueprint-Generation.md

**Status:** Approved  
**Owner:** diagnostics-engineer (AI layer) + blueprint-engineer  
**Phase:** 6 — Sprint 6-5  
**Date:** June 26, 2026  
**ADRs:** ADR-018 (Blueprint Generation Governance), ADR-007 (AI is Operator not Owner), ADR-005 (BYOK)  
**Schemas:** schemas/blueprint.schema.json, schemas/generation_plan.schema.json (new)  
**Depends on:** SPEC-005 (AI Diagnostics — LLMProvider pattern), SPEC-006 (Blueprint Engine), SPEC-013 (Blueprint #002 — pattern source)  
**Extends:** LLMProvider Protocol (provider.py)

---

## Purpose

Define the AI Blueprint Generation subsystem — the capability that allows PipelineKit to propose complete blueprint assets from a source/destination/tables specification.

This is the first time AI in PipelineKit generates new artifacts. ADR-018 governs the boundary: AI proposes, human approves, only approved assets touch the filesystem.

---

## What Gets Built

### New files

```
src/pipelinekit/ai/
├── blueprint_generator.py    BlueprintGenerator
└── generation_models.py      GenerationPlan, GeneratedAsset, GenerationContext

src/pipelinekit/cli/
└── generate.py               pipelinekit generate blueprint / apply / show

schemas/
└── generation_plan.schema.json   Output contract for generation plans

tests/ai/
└── test_blueprint_generator.py
tests/cli/
└── test_generate.py
```

### Modified files

```
src/pipelinekit/ai/provider.py        Add generate_blueprint() method to LLMProvider Protocol
src/pipelinekit/ai/providers/openai.py       Implement generate_blueprint()
src/pipelinekit/ai/providers/anthropic.py    Implement generate_blueprint()
src/pipelinekit/ai/providers/ollama.py       Implement generate_blueprint()
src/pipelinekit/ai/providers/deepseek.py     Implement generate_blueprint()
src/pipelinekit/ai/providers/mistral.py      Implement generate_blueprint()
src/pipelinekit/cli/main.py           Register generate command group
src/pipelinekit/state/db.py           Add generation_plans table
docs/reference/Error-Codes.md        Add PK-GEN-* codes
```

---

## Data Models

### GeneratedAsset

```python
# src/pipelinekit/ai/generation_models.py

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class GeneratedAsset:
    asset_type: str           # see asset types below
    filename: str             # relative path within blueprint directory
    content: str              # generated content as string
    approved: bool = False
    edited: bool = False
    validation_error: Optional[str] = None

# Asset types
ASSET_TYPES = [
    "blueprint_json",
    "example_yaml",
    "ingestion_pipeline",
    "dbt_project",
    "dbt_profiles",
    "dbt_sources",
    "dbt_staging_models",
    "dbt_core_models",
    "contracts",
    "quality_checks",
    "alerts_config",
    "readme",
    "runbook",
]

@dataclass
class GenerationContext:
    source_type: str
    destination_type: str
    tables: list[str]
    existing_blueprints: list[dict]    # patterns from BlueprintRegistry
    source_config_fields: list[str]    # available fields from SourceConfig
    blueprint_schema: dict             # schemas/blueprint.schema.json

@dataclass
class GenerationPlan:
    blueprint_name: str
    source_type: str
    destination_type: str
    tables: list[str]
    assets: list[GeneratedAsset]
    provider: str
    generated_at: str
    can_auto_apply: bool = False    # always False — ADR-018
    applied: bool = False
```

---

## generation_plan.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PipelineKit Generation Plan",
  "type": "object",
  "required": ["blueprint_name", "source_type", "destination_type", "tables", "assets"],
  "properties": {
    "blueprint_name": {"type": "string"},
    "source_type": {"type": "string"},
    "destination_type": {"type": "string"},
    "tables": {"type": "array", "items": {"type": "string"}},
    "assets": {
      "type": "array",
      "minItems": 8,
      "items": {
        "type": "object",
        "required": ["asset_type", "filename", "content"],
        "properties": {
          "asset_type": {"type": "string"},
          "filename": {"type": "string"},
          "content": {"type": "string"},
          "approved": {"type": "boolean", "default": false},
          "edited": {"type": "boolean", "default": false}
        }
      }
    },
    "can_auto_apply": {"type": "boolean", "default": false}
  }
}
```

---

## LLMProvider Extension

Add `generate_blueprint()` to the `LLMProvider` Protocol:

```python
# src/pipelinekit/ai/provider.py

def generate_blueprint(
    self,
    context: "GenerationContext",
) -> "GenerationPlan":
    """
    Generate a complete blueprint plan from source/destination/tables.
    Returns GenerationPlan — never writes files.
    Output validates against schemas/generation_plan.schema.json.
    Raises LLMError(PK-AI-001) if provider unavailable.
    Raises LLMError(PK-AI-002) if response fails schema validation.
    can_auto_apply is always False in the returned plan.
    """
    ...
```

---

## BlueprintGenerator

```python
# src/pipelinekit/ai/blueprint_generator.py

class BlueprintGenerator:
    """Orchestrates blueprint generation context → AI → validation → GenerationPlan.

    Nothing touches the filesystem during generation.
    AI proposes — human approves — apply writes.
    ADR-018: Plan then apply pattern.
    """

    def __init__(self, config: PipelineConfig, provider: LLMProvider):
        self.config = config
        self.provider = provider
        self.registry = BlueprintRegistry()

    def generate(
        self,
        source_type: str,
        destination_type: str,
        tables: list[str],
        cwd: Path | None = None,
    ) -> GenerationPlan:
        """
        1. Build GenerationContext (existing blueprints, schema, SourceConfig fields)
        2. Call provider.generate_blueprint(context)
        3. Validate each asset
        4. Validate overall plan against generation_plan.schema.json
        5. Force can_auto_apply = False
        6. Store plan in state.db
        7. Return GenerationPlan — no files written
        """
        ...

    def apply(
        self,
        plan: GenerationPlan,
        cwd: Path | None = None,
    ) -> list[str]:
        """
        Write approved assets to blueprints/<name>/.
        Returns list of written file paths.
        Raises GenerationError(PK-GEN-003) if no assets approved.
        Raises GenerationError(PK-GEN-004) if blueprint directory already exists.
        Never writes unapproved assets.
        """
        ...

    def _build_context(
        self,
        source_type: str,
        destination_type: str,
        tables: list[str],
        cwd: Path | None = None,
    ) -> GenerationContext:
        """
        Assemble generation context from:
        - BlueprintRegistry (existing blueprints as patterns)
        - schemas/blueprint.schema.json
        - SourceConfig field names for the source type
        """
        ...
```

---

## Provider Implementation Pattern

All 5 providers implement `generate_blueprint()`. Same isolation pattern as `diagnose()` and `architect()`.

**System prompt for all providers:**

```python
GENERATION_SYSTEM_PROMPT = """You are a PipelineKit blueprint engineer.
Generate a complete analytics pipeline blueprint from the provided specification.

You must generate ALL of these assets:
1. blueprint.json — blueprint manifest
2. pipelinekit.example.yaml — reference config with ${VAR} credential placeholders
3. ingestion/pipeline.py — dlt source definition
4. transform/dbt_project.yml — dbt project config
5. transform/profiles.yml — Snowflake prod + DuckDB local targets
6. transform/models/sources.yml — with env_var() for database/schema
7. transform/models/staging/*.sql — one per source table
8. transform/models/core/*.sql — business logic models
9. contracts/*.yaml — ContractDefinition format
10. quality/checks.yaml — Soda checks
11. alerts/config.yaml — notification config
12. docs/README.md — overview and prerequisites
13. docs/runbook.md — with empty Verified Deployments table

Rules:
- All credentials use ${VAR} interpolation — never hardcoded values
- All dbt sources use {{ env_var('DBT_SOURCE_DATABASE') }} and {{ env_var('DBT_SOURCE_SCHEMA') }}
- All staging models use {{ source('source_name', 'table') }}
- All core models use {{ ref('staging_model') }}
- Contracts must use required_columns, uniqueness, not_null, freshness fields
- can_auto_apply must always be false
- Use existing blueprints in context as the pattern for style and structure

Return a JSON array of assets where each asset has:
{
  "asset_type": "...",
  "filename": "relative/path/in/blueprint",
  "content": "full file content as string"
}"""
```

---

## CLI Commands

```python
# src/pipelinekit/cli/generate.py

generate_app = typer.Typer(
    name="generate",
    help="AI-powered blueprint generation.",
    no_args_is_help=True,
)

@generate_app.command("blueprint")
def generate_blueprint_command(
    source: str = typer.Option(..., "--source", "-s",
        help="Source type: postgres | salesforce | stripe | hubspot"),
    destination: str = typer.Option(..., "--destination", "-d",
        help="Destination type: snowflake | bigquery | duckdb"),
    tables: str = typer.Option(..., "--tables", "-t",
        help="Comma-separated table names: charges,customers,subscriptions"),
    provider: str = typer.Option(None, "--provider", "-p"),
    output: str = typer.Option(None, "--output", "-o",
        help="Blueprint name (default: {source}-to-{destination})"),
):
    """Generate a complete blueprint using AI. Review each asset before applying."""

@generate_app.command("apply")
def apply_command(
    name: str = typer.Argument(..., help="Blueprint name from last generation"),
    yes: bool = typer.Option(False, "--yes", "-y",
        help="Apply all approved assets without confirmation"),
):
    """Write approved assets to blueprints/<name>/."""

@generate_app.command("show")
def show_command(
    name: str = typer.Argument(..., help="Blueprint name to review"),
):
    """Show the current generation plan for review."""
```

### Interactive review flow

```
pipelinekit generate blueprint --source stripe --destination snowflake --tables charges,customers

Generating stripe-to-snowflake blueprint...
Reading 2 existing blueprints as patterns...
Calling anthropic...

Generation plan ready — 13 assets

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Asset 1 of 13: blueprint.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "name": "stripe-to-snowflake",
  "version": "1.0.0",
  ...
}

[a]ccept  [e]dit  [r]eject  [s]kip  [q]uit: a
✓ Accepted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Asset 2 of 13: pipelinekit.example.yaml
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...

Summary: 12/13 accepted, 1 rejected
Run 'pipelinekit generate apply stripe-to-snowflake' to write accepted assets.
```

### Apply flow

```
pipelinekit generate apply stripe-to-snowflake

Writing 12 assets to blueprints/stripe-to-snowflake/...
  ✓ blueprint.json
  ✓ pipelinekit.example.yaml
  ✓ ingestion/pipeline.py
  ✓ transform/dbt_project.yml
  ✓ transform/profiles.yml
  ✓ transform/models/sources.yml
  ✓ transform/models/staging/stg_charges.sql
  ✓ transform/models/staging/stg_customers.sql
  ✓ transform/models/core/fct_revenue.sql
  ✓ contracts/charges.yaml
  ✓ quality/checks.yaml
  ✓ docs/runbook.md
  ✗ alerts/config.yaml (rejected — skipped)

Blueprint stripe-to-snowflake created.
Run 'pipelinekit blueprint validate' to verify structure.
Run 'pipelinekit run --dry-run' to test connectivity.
```

---

## State Extension

```sql
CREATE TABLE IF NOT EXISTS generation_plans (
    id              TEXT PRIMARY KEY,
    blueprint_name  TEXT NOT NULL,
    source_type     TEXT NOT NULL,
    destination_type TEXT NOT NULL,
    tables          TEXT,      -- JSON array
    assets          TEXT,      -- JSON array of GeneratedAsset
    provider        TEXT,
    can_auto_apply  INTEGER DEFAULT 0,
    applied         INTEGER DEFAULT 0,
    generated_at    TEXT NOT NULL,
    applied_at      TEXT
);
```

---

## Error Codes

| Code | Meaning |
|---|---|
| `PK-GEN-001` | Generation failed — AI provider error |
| `PK-GEN-002` | Generated plan failed schema validation |
| `PK-GEN-003` | Apply failed — no assets approved |
| `PK-GEN-004` | Blueprint directory already exists |
| `PK-GEN-005` | Generated blueprint.json failed schema validation |

Add `GenerationError` to `core/errors.py`.

---

## Test Requirements

All 229 prior tests must pass. All AI tests mock providers.

**tests/ai/test_blueprint_generator.py** — 5 tests:
- `generate()` returns `GenerationPlan` with 8+ assets (mocked provider)
- `can_auto_apply` always False in returned plan
- `apply()` writes only approved assets to disk (tmp_path)
- `apply()` raises `GenerationError(PK-GEN-003)` when no assets approved
- `apply()` raises `GenerationError(PK-GEN-004)` when blueprint already exists

**tests/cli/test_generate.py** — 3 tests:
- `pipelinekit generate blueprint --help` exits 0
- `pipelinekit generate apply --help` exits 0
- `pipelinekit generate show --help` exits 0

---

## Verification — What Success Looks Like

```powershell
# Generate Blueprint #003 (Stripe → Snowflake) using AI
pipelinekit generate blueprint `
  --source stripe `
  --destination snowflake `
  --tables charges,customers,subscriptions

# Review and accept all assets interactively

# Apply approved assets
pipelinekit generate apply stripe-to-snowflake

# Verify the generated blueprint
pipelinekit blueprint validate
pipelinekit blueprint info stripe-to-snowflake

# Run local verification (with -Local synthetic seed)
.\scripts\verify-blueprint-003.ps1 -Local
```

If that sequence works — AI Blueprint Generation is real. Blueprint #003 was generated, not hand-crafted.

---

## The Strategic Significance

Before Sprint 6-5: 2 blueprints (hand-crafted, ~2 hours each)  
After Sprint 6-5: N blueprints (AI-generated, ~10 minutes each including review)

This is the capability that makes the catalog defensible. The moat is not the two blueprints we built — it is the system that generates unlimited blueprints from a specification.

---

## Out of Scope

- Automatic blueprint improvement from real run data — Phase 7+
- Multi-turn generation (AI asks clarifying questions) — Phase 7+
- Remote generation (generate from registry) — Sprint 6-6
- can_auto_apply = True — requires ADR-019 with reversibility mechanism
