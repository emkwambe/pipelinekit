# SPEC-017-Migration-Intelligence.md

**Status:** Approved  
**Owner:** diagnostics-engineer  
**Phase:** 6 — Sprint 6-7  
**Date:** June 26, 2026  
**ADRs:** ADR-020 (Migration Intelligence Governance), ADR-007, ADR-018  
**Depends on:** SPEC-005 (AI Diagnostics — LLMProvider pattern), SPEC-015 (Blueprint Proposal)

---

## Purpose

Migration Intelligence reads existing pipeline configurations (Airbyte, Fivetran, custom Python) and proposes a PipelineKit equivalent. It reduces migration time from days to hours for ICP-004 (Mixed-Stack Enterprise) customers.

---

## New Files

```
src/pipelinekit/ai/
├── migration_models.py      MigrationProposal, MappingResult, MigrationGap
├── migration_analyzer.py    MigrationAnalyzer
└── config_parsers.py        AirbyteParser, FivetranParser, PythonParser

src/pipelinekit/cli/
└── migrate.py               pipelinekit migrate analyze

tests/ai/
├── test_migration_models.py
├── test_migration_analyzer.py
└── test_config_parsers.py
```

## Modified Files

```
src/pipelinekit/ai/provider.py         Add analyze_migration() to LLMProvider Protocol
src/pipelinekit/ai/providers/*.py      Implement analyze_migration() in all 5 providers
src/pipelinekit/cli/main.py            Register migrate command group
src/pipelinekit/core/errors.py         Add MigrationError
docs/reference/Error-Codes.md         Add PK-MIGRATE-* codes
```

---

## Data Models

```python
# src/pipelinekit/ai/migration_models.py

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class MappingStatus(Enum):
    CLEAN    = "clean"      # maps directly to PipelineKit
    PARTIAL  = "partial"    # maps with minor adjustments
    MANUAL   = "manual"     # requires significant human work
    UNSUPPORTED = "unsupported"  # no PipelineKit equivalent

@dataclass
class MappingResult:
    field: str
    source_value: str
    pipelinekit_equivalent: Optional[str]
    status: MappingStatus
    note: str = ""

@dataclass
class MigrationGap:
    gap_type: str       # "credential" | "table" | "transform" | "schedule" | "feature"
    description: str
    required_action: str
    blocking: bool = True   # blocks deployment if not resolved

@dataclass
class MigrationProposal:
    source_tool: str          # "airbyte" | "fivetran" | "python" | "pipelinekit"
    source_file: str
    draft_yaml: str           # proposed pipelinekit.yaml content
    blueprint_recommendation: Optional[str]  # name of matching blueprint
    mappings: list[MappingResult]
    gaps: list[MigrationGap]
    confidence: float         # 0.0–1.0
    blocking_gaps: int        # count of gaps that block deployment
    can_auto_apply: bool = False   # always False
    assumptions: list[str] = field(default_factory=list)
```

---

## Config Parsers

```python
# src/pipelinekit/ai/config_parsers.py

class AirbyteParser:
    """Parse Airbyte connection.json export."""
    def parse(self, path: Path) -> dict:
        """Extract: source_type, destination_type, streams, sync_mode, namespace."""

class FivetranParser:
    """Parse Fivetran connector.json export."""
    def parse(self, path: Path) -> dict:
        """Extract: connector_type, schema, tables, sync_frequency."""

class PythonParser:
    """Best-effort parse of Python pipeline files."""
    def parse(self, path: Path) -> dict:
        """
        Look for dlt/SQLAlchemy/psycopg2 patterns.
        Extract: connection strings, table names, destination hints.
        Returns partial results with low confidence if parsing is ambiguous.
        Never executes the Python file.
        """

class MigrationConfigParser:
    """Router — detects format and delegates to correct parser."""
    def parse(self, path: Path) -> tuple[str, dict]:
        """Returns (tool_name, parsed_config)."""
        # Detect by file extension and content
        # .json → try Airbyte then Fivetran
        # .py → Python parser
        # .yaml/.yml → check for pipelinekit markers
```

---

## MigrationAnalyzer

```python
# src/pipelinekit/ai/migration_analyzer.py

class MigrationAnalyzer:
    """Read existing pipeline config → analyze → propose PipelineKit equivalent.

    ADR-020: reads and proposes — never executes.
    Same trust model as BlueprintProposer (ADR-018).
    """

    def __init__(self, config: PipelineConfig, provider: LLMProvider):
        self.config = config
        self.provider = provider
        self.parser = MigrationConfigParser()
        self.registry = BlueprintRegistry()

    def analyze(
        self,
        config_path: Path,
        cwd: Path | None = None,
    ) -> MigrationProposal:
        """
        1. Parse existing config file
        2. Build migration context (parsed config + available blueprints)
        3. Call provider.analyze_migration(context)
        4. Validate proposal
        5. Force can_auto_apply = False
        6. Return MigrationProposal — no files written
        """

    def apply(
        self,
        proposal: MigrationProposal,
        cwd: Path | None = None,
    ) -> str:
        """
        Write draft pipelinekit.yaml to disk after human review.
        Returns path written.
        Raises MigrationError(PK-MIGRATE-003) if blocking gaps exist and --force not set.
        """
```

---

## LLMProvider Extension

```python
def analyze_migration(
    self,
    context: dict,   # parsed config + available blueprints + adapter registry
) -> "MigrationProposal":
    """
    Analyze existing pipeline config and propose PipelineKit migration.
    Returns MigrationProposal — never writes files.
    """
    ...
```

---

## CLI Command

```python
# src/pipelinekit/cli/migrate.py

migrate_app = typer.Typer(name="migrate", help="Migrate existing pipelines to PipelineKit.")

@migrate_app.command("analyze")
def analyze_command(
    config: str = typer.Argument(..., help="Path to existing pipeline config"),
    provider: str = typer.Option(None, "--provider", "-p"),
    apply: bool = typer.Option(False, "--apply",
        help="Write draft pipelinekit.yaml after analysis"),
    force: bool = typer.Option(False, "--force",
        help="Apply even if blocking gaps exist"),
):
    """Analyze an existing pipeline config and propose a PipelineKit migration."""
```

**Output format:**

```
Analyzing airbyte-connection.json...
Detected: Airbyte — postgres → snowflake

Migration Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Confidence:  0.84
Mapping:     8 clean · 2 partial · 0 unsupported

Blueprint recommendation:  postgres-to-snowflake (installed ✓)

Clean mappings:
  ✓ source.type: postgres → ingestion.source.type: postgres
  ✓ source.host → ingestion.source.host: ${PG_HOST}
  ✓ destination.type: snowflake → ingestion.destination.type: snowflake
  ... (5 more)

Partial mappings:
  ⚠ streams[*].sync_mode: incremental → write_disposition: append
    Note: review incremental cursor strategy

Gaps (2 blocking):
  ✗ CREDENTIAL: Airbyte stores credentials in secrets manager
    Action: set PG_USER, PG_PASSWORD, SNOWFLAKE_* env vars

  ✗ SCHEDULE: Airbyte sync frequency not mapped
    Action: configure your scheduler (Airflow, cron) separately

Draft pipelinekit.yaml written to: ./pipelinekit.proposed.yaml
Review it, fill in the gaps, then run: pipelinekit validate
```

---

## Error Codes

| Code | Meaning |
|---|---|
| `PK-MIGRATE-001` | Config file not found |
| `PK-MIGRATE-002` | Config format not recognized |
| `PK-MIGRATE-003` | Blocking gaps exist — use --force to apply anyway |
| `PK-MIGRATE-004` | AI analysis failed |
| `PK-MIGRATE-005` | Python file parsing failed (syntax error) |

---

## Test Requirements

All 268 prior tests must pass.

**tests/ai/test_config_parsers.py** — 4 tests:
- `AirbyteParser.parse()` extracts source/destination/streams from sample JSON
- `FivetranParser.parse()` extracts connector/schema/tables
- `PythonParser.parse()` extracts connection hints from sample .py
- `MigrationConfigParser.parse()` routes correctly by file type

**tests/ai/test_migration_analyzer.py** — 4 tests:
- `analyze()` returns `MigrationProposal` — no files written
- `can_auto_apply` always False
- `apply()` raises `MigrationError(PK-MIGRATE-003)` when blocking gaps exist
- `apply()` writes `pipelinekit.proposed.yaml` when gaps are non-blocking

**tests/ai/test_migration_models.py** — 2 tests:
- `MigrationProposal` serializes correctly
- `blocking_gaps` count matches gaps with `blocking=True`

---

## Acceptance Criteria

```
✓ pipelinekit migrate analyze <airbyte-config.json> exits 0
✓ pipelinekit migrate analyze <fivetran-config.json> exits 0
✓ pipelinekit migrate analyze <pipeline.py> exits 0
✓ MigrationProposal shows confidence, mappings, gaps
✓ Blueprint recommendation shown when matching blueprint installed
✓ --apply writes pipelinekit.proposed.yaml (not pipelinekit.yaml)
✓ Blocking gaps prevent apply without --force
✓ can_auto_apply always False
✓ All 268 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

---

## Commit Message

```
feat: Sprint 6-7 — Migration Intelligence (ADR-020, SPEC-017)

- src/pipelinekit/ai/migration_models.py — MigrationProposal, MappingResult, MigrationGap
- src/pipelinekit/ai/migration_analyzer.py — MigrationAnalyzer (analyze + apply)
- src/pipelinekit/ai/config_parsers.py — Airbyte, Fivetran, Python parsers
- src/pipelinekit/cli/migrate.py — pipelinekit migrate analyze
- All 5 providers — analyze_migration() implemented

ADR-020 satisfied. ICP-004 migration path: read existing config → propose PipelineKit equivalent.
AI reads and proposes — human approves — apply writes pipelinekit.proposed.yaml.
```
