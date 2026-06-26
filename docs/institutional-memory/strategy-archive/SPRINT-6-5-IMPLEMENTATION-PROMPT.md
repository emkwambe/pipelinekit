# PipelineKit — Sprint 6-5 Implementation Prompt
## AI Blueprint Generation

---

## Your Identity

You are Claude Code operating as **diagnostics-engineer** (AI layer) + **blueprint-engineer**.

Primary ADR: `docs/decisions/ADR-018-Blueprint-Generation-Governance.md`  
Primary SPEC: `docs/specifications/SPEC-015-AI-Blueprint-Generation.md`

---

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

---

## Sprint Goal

```powershell
poetry run pipelinekit generate --help
poetry run pipelinekit generate blueprint --help
poetry run pipelinekit generate apply --help
poetry run pipelinekit generate show --help
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

All 229 prior tests must still pass.

---

## Files You Are Allowed To Create

```
schemas/
└── generation_plan.schema.json

src/pipelinekit/ai/
├── generation_models.py      GenerationPlan, GeneratedAsset, GenerationContext
└── blueprint_generator.py    BlueprintGenerator

src/pipelinekit/cli/
└── generate.py               generate blueprint / apply / show

tests/ai/
└── test_blueprint_generator.py

tests/cli/
└── test_generate.py
```

You may also modify:
```
src/pipelinekit/ai/provider.py              Add generate_blueprint() to LLMProvider Protocol
src/pipelinekit/ai/providers/anthropic.py   Implement generate_blueprint()
src/pipelinekit/ai/providers/openai.py      Implement generate_blueprint()
src/pipelinekit/ai/providers/ollama.py      Implement generate_blueprint()
src/pipelinekit/ai/providers/deepseek.py    Implement generate_blueprint()
src/pipelinekit/ai/providers/mistral.py     Implement generate_blueprint()
src/pipelinekit/cli/main.py                 Register generate command group
src/pipelinekit/state/db.py                 Add generation_plans table + insert function
src/pipelinekit/core/errors.py              Add GenerationError
docs/reference/Error-Codes.md              Add PK-GEN-001 to 005
```

---

## Files You Must Not Modify

```
docs/reference/PROJECT-STATUS.md    ← NEVER — Command Center owns it
blueprints/                         ← READ ONLY — existing blueprints are patterns, not targets
schemas/blueprint.schema.json       ← READ ONLY
schemas/diagnostic.schema.json      ← READ ONLY
schemas/architecture.schema.json    ← READ ONLY
src/pipelinekit/ai/diagnostics.py   ← READ ONLY
src/pipelinekit/ai/arch_engine.py   ← READ ONLY
src/pipelinekit/ai/models.py        ← READ ONLY
src/pipelinekit/ai/arch_models.py   ← READ ONLY
All existing test files             ← READ ONLY
contracts/                          ← READ ONLY
agents/                             ← READ ONLY
```

---

## Implementation Requirements

### 1. schemas/generation_plan.schema.json

Create exactly as specified in SPEC-015. Key constraint: `assets` array must have `minItems: 8`.

---

### 2. src/pipelinekit/ai/generation_models.py

```python
from dataclasses import dataclass, field
from typing import Optional

REQUIRED_ASSET_TYPES = [
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
class GeneratedAsset:
    asset_type: str
    filename: str
    content: str
    approved: bool = False
    edited: bool = False
    validation_error: Optional[str] = None

@dataclass
class GenerationContext:
    source_type: str
    destination_type: str
    tables: list[str]
    existing_blueprints: list[dict]
    source_config_fields: list[str]
    blueprint_schema: dict

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

### 3. src/pipelinekit/ai/provider.py — Add generate_blueprint() Only

Add one method to the existing `LLMProvider` Protocol. Do not change existing methods.

```python
def generate_blueprint(
    self,
    context: "GenerationContext",
) -> "GenerationPlan":
    """
    Generate a complete blueprint plan from context.
    Returns GenerationPlan — never writes files (ADR-018).
    Output validates against schemas/generation_plan.schema.json.
    Raises LLMError(PK-AI-001) if provider unavailable.
    Raises LLMError(PK-AI-002) if response fails schema validation.
    can_auto_apply is always False in returned plan.
    """
    ...
```

---

### 4. Provider Implementation — All 5 Providers

Add `generate_blueprint()` to each provider. All provider-specific imports stay inside the method.

**System prompt (same for all providers):**

```python
GENERATION_SYSTEM_PROMPT = """You are a PipelineKit blueprint engineer.
Generate a complete analytics pipeline blueprint from the provided specification.

You must generate ALL required assets as a JSON array. Each asset:
{
  "asset_type": "blueprint_json|example_yaml|ingestion_pipeline|dbt_project|dbt_profiles|dbt_sources|dbt_staging_models|dbt_core_models|contracts|quality_checks|alerts_config|readme|runbook",
  "filename": "relative/path/within/blueprint/directory",
  "content": "complete file content as a string"
}

Critical rules:
- All credentials use ${VAR} interpolation — never hardcoded values
- dbt sources use {{ env_var('DBT_SOURCE_DATABASE') }} and {{ env_var('DBT_SOURCE_SCHEMA') }}
- Staging models use {{ source('source_name', 'table') }}
- Core models use {{ ref('staging_model') }}
- Contracts use required_columns, uniqueness/not_null/freshness fields
- can_auto_apply must always be false
- Follow existing blueprint patterns exactly for structure and style
- Return ONLY the JSON array — no preamble, no markdown, no explanation"""
```

The user message includes:
- Source type, destination type, tables
- Existing blueprint examples (postgres-to-snowflake, salesforce-to-snowflake) as context
- SourceConfig available fields for the source type
- blueprint.schema.json for structural constraints

---

### 5. src/pipelinekit/ai/blueprint_generator.py

```python
class BlueprintGenerator:
    """Orchestrates generation context → AI → validation → GenerationPlan.

    Nothing touches the filesystem during generation.
    AI proposes — human approves — apply() writes.
    ADR-018: Plan then apply pattern.
    Smell 13: Generator never becomes Actor.
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
        1. Build GenerationContext
        2. Call provider.generate_blueprint(context)
        3. Validate each asset (blueprint.json against schema)
        4. Validate plan against generation_plan.schema.json
        5. Force can_auto_apply = False regardless of provider response
        6. Store in state.db
        7. Return GenerationPlan — no files written
        """

    def apply(
        self,
        plan: GenerationPlan,
        cwd: Path | None = None,
    ) -> list[str]:
        """
        Write ONLY approved assets to blueprints/<name>/.
        Raises GenerationError(PK-GEN-003) if no assets approved.
        Raises GenerationError(PK-GEN-004) if directory already exists.
        Creates parent directories as needed.
        Returns list of written paths.
        """

    def _build_context(
        self,
        source_type: str,
        destination_type: str,
        tables: list[str],
        cwd: Path | None = None,
    ) -> GenerationContext:
        """
        Read existing blueprints, source config fields, blueprint schema.
        Returns GenerationContext for provider.
        """

    def _load_blueprint_schema(self) -> dict:
        """Read schemas/blueprint.schema.json."""

    def _get_source_config_fields(self, source_type: str) -> list[str]:
        """Return available SourceConfig fields for the given source type."""

    def _validate_blueprint_json(self, content: str) -> Optional[str]:
        """Validate generated blueprint.json against schema. Returns error or None."""
```

---

### 6. src/pipelinekit/cli/generate.py

```python
generate_app = typer.Typer(
    name="generate",
    help="AI-powered blueprint generation.",
    no_args_is_help=True,
)

@generate_app.command("blueprint")
def generate_blueprint_command(
    source: str = typer.Option(..., "--source", "-s"),
    destination: str = typer.Option(..., "--destination", "-d"),
    tables: str = typer.Option(..., "--tables", "-t",
        help="Comma-separated: charges,customers,subscriptions"),
    provider: str = typer.Option(None, "--provider", "-p"),
    name: str = typer.Option(None, "--name", "-n",
        help="Blueprint name (default: {source}-to-{destination})"),
):
    """Generate a complete blueprint using AI. Review each asset interactively."""

@generate_app.command("apply")
def apply_command(
    name: str = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes", "-y"),
):
    """Write approved assets to blueprints/<name>/."""

@generate_app.command("show")  
def show_command(
    name: str = typer.Argument(...),
):
    """Show generation plan for review."""
```

**Interactive review loop (generate blueprint command):**

After AI returns the plan — show each asset with Rich panel, prompt for `[a]ccept [e]dit [r]eject [s]kip [q]uit`. Store approval state in the plan. Show summary at end. Save plan to state.db.

**Non-interactive mode flag:**
`--yes` on apply accepts all non-rejected assets without prompting.

---

### 7. state/db.py — Addition Only

Add generation_plans table to `_SCHEMA` and one new function:

```python
def insert_generation_plan(
    plan: dict,
    cwd: Path | None = None,
) -> None:
    """Store generation plan. Called by BlueprintGenerator only."""

def get_generation_plan(
    blueprint_name: str,
    cwd: Path | None = None,
) -> Optional[dict]:
    """Retrieve most recent generation plan for a blueprint name."""
```

---

## Test Requirements

All 229 prior tests must pass. All AI tests mock providers.

**tests/ai/test_blueprint_generator.py** — 5 tests:

```python
def test_generate_returns_plan(mock_provider, tmp_path):
    """generate() returns GenerationPlan with assets — no files written."""
    # Verify no files exist in tmp_path after generate()

def test_can_auto_apply_always_false(mock_provider, tmp_path):
    """can_auto_apply is False even if provider returns True."""

def test_apply_writes_approved_assets(mock_plan, tmp_path):
    """apply() writes only approved assets to tmp_path/blueprints/<name>/."""

def test_apply_raises_on_no_approved(mock_plan, tmp_path):
    """apply() raises GenerationError(PK-GEN-003) when no assets approved."""

def test_apply_raises_on_existing_blueprint(mock_plan, tmp_path):
    """apply() raises GenerationError(PK-GEN-004) when directory exists."""
```

**tests/cli/test_generate.py** — 3 tests:
- `--help` exits 0 for all three subcommands

---

## Validation Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry install

# Verify commands exist
poetry run pipelinekit generate --help
poetry run pipelinekit generate blueprint --help
poetry run pipelinekit generate apply --help
poetry run pipelinekit generate show --help

# Quality gates
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

```
✓ schemas/generation_plan.schema.json exists and valid
✓ GenerationPlan, GeneratedAsset, GenerationContext defined
✓ BlueprintGenerator.generate() returns plan — no files written
✓ BlueprintGenerator.apply() writes only approved assets
✓ can_auto_apply always False — engine corrects any True from provider
✓ GenerationError(PK-GEN-003) on no approved assets
✓ GenerationError(PK-GEN-004) on existing blueprint directory
✓ All 5 providers implement generate_blueprint()
✓ pipelinekit generate blueprint shows interactive review
✓ pipelinekit generate apply writes files after review
✓ pipelinekit generate show displays plan for review
✓ Generation plan stored in state.db
✓ All 229 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
✓ Existing blueprints untouched
```

---

## Stop and Ask Before

- Writing any file to disk during generation (only apply() writes)
- Setting can_auto_apply = True anywhere
- Modifying existing blueprints
- Touching PROJECT-STATUS.md
- Adding any MCP (ADR-014 — direct API calls only)
- Self-approving any architectural decision

---

## The Strategic Purpose

This sprint makes Blueprint #003 (Stripe → Snowflake) generatable — not hand-craftable.

After this sprint, the test is:
```powershell
pipelinekit generate blueprint --source stripe --destination snowflake --tables charges,customers
# Review and accept assets
pipelinekit generate apply stripe-to-snowflake
pipelinekit blueprint validate
```

If that sequence produces a valid blueprint — AI Blueprint Generation works. Every future blueprint can be generated, not hand-crafted. The catalog is now limitless.

---

## Commit Message

```
feat: Sprint 6-5 — AI Blueprint Generation (ADR-018, SPEC-015)

- src/pipelinekit/ai/generation_models.py — GenerationPlan, GeneratedAsset, GenerationContext
- src/pipelinekit/ai/blueprint_generator.py — BlueprintGenerator (generate + apply)
- src/pipelinekit/cli/generate.py — pipelinekit generate blueprint/apply/show
- schemas/generation_plan.schema.json — output contract
- All 5 providers — generate_blueprint() implemented
- state/db.py — generation_plans table
- core/errors.py — GenerationError

ADR-018 satisfied: Plan then apply pattern.
AI proposes — human approves — apply() writes.
can_auto_apply always False.
```
