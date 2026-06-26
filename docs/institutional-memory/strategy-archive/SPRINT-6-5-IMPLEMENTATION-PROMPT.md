# PipelineKit — Sprint 6-5 Implementation Prompt v2
## AI Blueprint Proposal

---

## Naming Convention

This sprint implements **Blueprint Proposal**, not Blueprint Generation.

| User-facing (CLI) | Internal (code) |
|---|---|
| `pipelinekit generate blueprint` | `BlueprintProposer` |
| `pipelinekit apply plan` | `BlueprintProposal` |
| "generate" | `propose()` |
| — | `ProposedAsset` |
| — | `propose_blueprint()` on LLMProvider |

---

## Your Identity

You are Claude Code operating as **diagnostics-engineer** + **blueprint-engineer**.

Primary ADR: `docs/decisions/ADR-018-Blueprint-Proposal-Governance.md`  
Primary SPEC: `docs/specifications/SPEC-015-AI-Blueprint-Proposal.md`

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
poetry run pipelinekit generate show --help
poetry run pipelinekit apply --help
poetry run pipelinekit apply plan --help
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
└── blueprint_proposal.schema.json

src/pipelinekit/ai/
├── proposal_models.py        BlueprintProposal, ProposedAsset, AssetState, ProposalContext, AssetProvenance
├── blueprint_proposer.py     BlueprintProposer
└── adapter_registry.py       AdapterCapabilityRegistry

src/pipelinekit/cli/
└── generate.py               generate blueprint / show / apply plan

tests/ai/
├── test_blueprint_proposer.py
└── test_adapter_registry.py

tests/cli/
└── test_generate_and_apply.py
```

You may also modify:
```
src/pipelinekit/ai/provider.py              Add propose_blueprint() to Protocol
src/pipelinekit/ai/providers/anthropic.py   Implement propose_blueprint()
src/pipelinekit/ai/providers/openai.py      Implement propose_blueprint()
src/pipelinekit/ai/providers/ollama.py      Implement propose_blueprint()
src/pipelinekit/ai/providers/deepseek.py    Implement propose_blueprint()
src/pipelinekit/ai/providers/mistral.py     Implement propose_blueprint()
src/pipelinekit/cli/main.py                 Register generate + apply command groups
src/pipelinekit/state/db.py                 Add blueprint_proposals table
src/pipelinekit/core/errors.py              Add ProposalError
docs/reference/Error-Codes.md              Add PK-GEN-001 to 007
```

---

## Files You Must Not Modify

```
docs/reference/PROJECT-STATUS.md    ← NEVER
blueprints/                         ← READ ONLY — pattern source only
schemas/blueprint.schema.json       ← READ ONLY
schemas/diagnostic.schema.json      ← READ ONLY
schemas/architecture.schema.json    ← READ ONLY
All Phase 1-5 AI files              ← READ ONLY (except provider.py + 5 providers above)
All existing test files             ← READ ONLY
contracts/                          ← READ ONLY
```

---

## The Asset State Machine — Enforce By Code

```python
class AssetState(Enum):
    PROPOSED  = "proposed"
    APPROVED  = "approved"
    REJECTED  = "rejected"
    EDITED    = "edited"
    WRITTEN   = "written"
    VALIDATED = "validated"
```

**Valid transitions only:**
- `PROPOSED → APPROVED` (human approves)
- `PROPOSED → REJECTED` (human rejects)
- `PROPOSED → EDITED` (human edits)
- `EDITED → PROPOSED` (re-proposed)
- `APPROVED → WRITTEN` (apply() writes)
- `WRITTEN → VALIDATED` (blueprint validate passes)

**Invalid transitions — raise `ProposalError(PK-GEN-007)`:**
- `PROPOSED → WRITTEN` (cannot write without approval)
- Any other transition not listed above

The `mark_written()` method must check state == APPROVED before proceeding.

---

## AdapterCapabilityRegistry — Check Before AI Call

```python
SUPPORTED_SOURCES = {
    "postgres": {
        "dlt_source": "sql_database",
        "credential_fields": ["host", "port", "database", "user", "password"],
        "tables": "configurable",
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
    },
}
```

`BlueprintProposer.propose()` checks the registry FIRST:
- If source not supported → raise `ProposalError(PK-GEN-006, f"Source type '{source}' not supported. Supported: {list(SUPPORTED_SOURCES.keys())}")`
- If destination not supported → raise same with destination list
- Never call the AI provider for unsupported sources

---

## Provenance Metadata

Every `ProposedAsset` carries an `AssetProvenance` object:

```python
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
```

**On write:** `_strip_provenance()` removes the provenance block from content before writing to disk. The provenance lives in `state.db` and in the interactive review display — not in the final file.

---

## Provider System Prompt

```python
PROPOSAL_SYSTEM_PROMPT = """You are a PipelineKit blueprint engineer.
Propose a complete analytics pipeline blueprint from the provided specification.

Return a JSON object:
{
  "confidence": 0.0-1.0,
  "assumptions": ["what you assumed about the source schema"],
  "unsupported_areas": ["what you could not propose"],
  "requires_human_decisions": ["decisions the human must make"],
  "assets": [
    {
      "asset_type": "blueprint_json|example_yaml|ingestion_pipeline|dbt_project|dbt_profiles|dbt_sources|dbt_staging_models|dbt_core_models|contracts|quality_checks|alerts_config|readme|runbook",
      "filename": "relative/path",
      "content": "full file content",
      "confidence_note": "confidence note for this specific asset"
    }
  ]
}

Critical rules:
- All credentials use ${VAR} interpolation — NEVER hardcoded
- dbt sources use {{ env_var('DBT_SOURCE_DATABASE') }} and {{ env_var('DBT_SOURCE_SCHEMA') }}
- Staging models use {{ source('source_name', 'table') }}
- Core models use {{ ref('staging_model') }}
- Only use tables from the adapter capability registry provided
- can_auto_apply must be false in returned JSON
- Follow existing blueprint patterns exactly
- Return ONLY the JSON object. No markdown. No preamble."""
```

---

## CLI Design

### pipelinekit generate blueprint

```python
generate_app = typer.Typer(name="generate", help="AI-powered blueprint proposals.")
apply_app = typer.Typer(name="apply", help="Apply approved blueprint proposals.")

@generate_app.command("blueprint")
def generate_blueprint_command(
    source: str = typer.Option(..., "--source", "-s"),
    destination: str = typer.Option(..., "--destination", "-d"),
    tables: str = typer.Option(..., "--tables", "-t"),
    provider: str = typer.Option(None, "--provider", "-p"),
    name: str = typer.Option(None, "--name", "-n"),
    plan: bool = typer.Option(False, "--plan"),
    interactive: bool = typer.Option(False, "--interactive"),
):
    """Propose a blueprint using AI."""

@generate_app.command("show")
def show_command(plan_id: str = typer.Argument(...)):
    """Show a blueprint proposal for review."""

@apply_app.command("plan")
def apply_plan_command(
    plan_id: str = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes", "-y"),
):
    """Write approved assets from a proposal to blueprints/<name>/."""
```

Register both in `cli/main.py`:
```python
app.add_typer(generate_app, name="generate")
app.add_typer(apply_app, name="apply")
```

### Interactive review loop (--interactive mode)

Show each asset with Rich Panel. Options:
- `a` = accept (state → APPROVED)
- `r` = reject (state → REJECTED)
- `e` = edit (open content in Rich prompt, state → EDITED → re-proposed)
- `x` = explain (show provenance details)
- `y-all` = accept all remaining assets
- `q` = quit (saves current state to db, stops review)

After review — show summary and next steps.

---

## Test Requirements

All 229 prior tests must pass.

**tests/ai/test_blueprint_proposer.py** — 6 tests:
```python
def test_propose_returns_plan_no_files_written(mock_provider, tmp_path):
    """propose() returns BlueprintProposal. No files in tmp_path after."""

def test_can_auto_apply_always_false(mock_provider, tmp_path):
    """can_auto_apply = False even if provider returns True."""

def test_apply_writes_only_approved(mock_proposal, tmp_path):
    """apply() writes assets with state=APPROVED only."""

def test_apply_raises_on_no_approved(mock_proposal, tmp_path):
    """ProposalError(PK-GEN-003) when no APPROVED assets."""

def test_apply_raises_on_existing_directory(mock_proposal, tmp_path):
    """ProposalError(PK-GEN-004) when blueprint dir exists."""

def test_unsupported_source_raises_before_ai_call(tmp_path):
    """ProposalError(PK-GEN-006) for 'oracle' without calling provider."""
```

**tests/ai/test_adapter_registry.py** — 3 tests:
- Supported sources return True
- Unsupported sources return False
- get_supported_tables returns correct list

**tests/cli/test_generate_and_apply.py** — 4 tests:
- `--help` exits 0 for all commands
- Unsupported source produces PK-GEN-006 in output

---

## Definition of Done

```
✓ AdapterCapabilityRegistry with postgres, salesforce, stripe, snowflake, bigquery, duckdb
✓ AssetState enum with 6 states + transition enforcement
✓ BlueprintProposal with confidence, assumptions, unsupported_areas, requires_human_decisions
✓ ProposedAsset with state machine (approve/reject/mark_written enforce valid transitions)
✓ propose() returns plan — zero files written (verified in tests with tmp_path)
✓ PK-GEN-006 fires BEFORE AI call for unsupported sources
✓ Provenance attached to every asset; stripped on write
✓ apply() writes only APPROVED assets
✓ can_auto_apply always False
✓ pipelinekit generate blueprint --plan shows plan ID, no files
✓ pipelinekit generate blueprint --interactive shows per-asset review
✓ pipelinekit apply plan <id> writes approved assets
✓ [x]explain shows provenance in interactive mode
✓ [y-all] batch approve available
✓ blueprint_proposals table in state.db
✓ All 229 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
✓ Existing blueprints untouched
```

---

## Commit Message

```
feat: Sprint 6-5 — AI Blueprint Proposal (ADR-018, SPEC-015)

- src/pipelinekit/ai/proposal_models.py — BlueprintProposal, ProposedAsset, AssetState
- src/pipelinekit/ai/blueprint_proposer.py — BlueprintProposer (propose + apply)
- src/pipelinekit/ai/adapter_registry.py — AdapterCapabilityRegistry
- src/pipelinekit/cli/generate.py — pipelinekit generate blueprint/show + apply plan
- schemas/blueprint_proposal.schema.json — output contract
- All 5 providers — propose_blueprint() implemented
- state/db.py — blueprint_proposals table
- core/errors.py — ProposalError

ADR-018 satisfied: proposed → approved → written → validated.
AI proposes — human approves — apply() writes.
Naming: Blueprint Proposal, not Generation.
```
