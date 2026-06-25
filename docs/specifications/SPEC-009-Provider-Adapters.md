# SPEC-009-Provider-Adapters.md

**Status:** Approved  
**Owner:** runtime-engineer  
**Phase:** 2 — Data Layer  
**Date:** June 25, 2026  
**ADRs:** ADR-001 (Adopt dlt), ADR-002 (Remove Sling), ADR-005 (BYOK), ADR-008 (Deterministic), ADR-009 (Human-Readable)  
**Contracts:** contracts/adapter.yaml, contracts/provider.yaml  
**Depends on:** SPEC-003 (Runtime), SPEC-002 (Config)

---

## Purpose

Define the provider adapter layer — the stable interfaces that isolate all provider-specific code from PipelineKit core.

No vendor logic exists outside adapters.
Every adapter implements the same interface.
Every adapter is replaceable.
This is ADR-005 (BYOK) and ADR-012 (Product Boundary) made concrete.

---

## Governing Rules (from contracts/adapter.yaml and contracts/provider.yaml)

- Adapters must implement stable interfaces
- Adapters must return structured results
- Adapters must not bypass contracts
- Providers must be replaceable
- Provider-specific code must not leak into core runtime
- Provider errors must map to PipelineKit error codes
- Adapters never call each other
- Adapters never call CLI
- Adapters never call AI layer

---

## Adapter Types (Phase 2)

| Type | Provider | Phase |
|---|---|---|
| Ingestion | dlt (Postgres source) | 2 |
| Ingestion | dlt (Snowflake destination) | 2 |
| Ingestion | dlt (BigQuery destination) | 2 |
| Transformation | dbt Core | 2 |
| Quality | Soda | 2 |
| Notification | Resend | 3 |
| AI | LLMProvider | 4 |

---

## Base Adapter Interface

Every adapter implements this interface exactly.
From `contracts/provider.yaml`: required methods are `initialize`, `validate`, `execute`, `status`.

```python
# src/pipelinekit/adapters/base.py

from abc import ABC, abstractmethod
from pipelinekit.runtime.result import StepResult

class BaseAdapter(ABC):
    """Base interface for all PipelineKit adapters.

    Every adapter is replaceable. Provider-specific code
    never leaks into the runtime or CLI.

    Contract: contracts/provider.yaml
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the adapter — validate credentials, check connectivity."""
        ...

    @abstractmethod
    def validate(self) -> StepResult:
        """Validate adapter configuration without executing."""
        ...

    @abstractmethod
    def execute(self) -> StepResult:
        """Execute the adapter's primary operation."""
        ...

    @abstractmethod
    def status(self) -> dict:
        """Return current adapter status as a structured dict."""
        ...
```

---

## Ingestion Adapter — dlt

Phase 2 implements dlt as the ingestion adapter.
dlt is the standard per ADR-001 (Apache 2.0, Python-native, low operational complexity).

```python
# src/pipelinekit/adapters/ingestion/dlt/adapter.py

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.config.schema import IngestionSection
from pipelinekit.runtime.result import StepResult

class DltIngestionAdapter(BaseAdapter):
    """dlt-based ingestion adapter.

    Wraps dlt pipeline execution behind the stable BaseAdapter interface.
    All dlt-specific imports stay inside this file — never in runtime or CLI.

    ADR-001: dlt is the standard ingestion framework.
    """

    def __init__(self, config: IngestionSection):
        self.config = config
        self._pipeline = None

    def initialize(self) -> None:
        """Build the dlt pipeline object from config."""
        ...

    def validate(self) -> StepResult:
        """Validate source and destination connectivity."""
        ...

    def execute(self) -> StepResult:
        """Run the dlt pipeline. Returns StepResult with rows_processed."""
        ...

    def status(self) -> dict:
        """Return dlt pipeline state."""
        ...
```

### dlt Source Support — Phase 2

| Source | Status |
|---|---|
| PostgreSQL | Phase 2 |
| MySQL | Phase 3 |
| REST API | Phase 3 |
| Salesforce | Phase 3 |
| Stripe | Phase 3 |

### dlt Destination Support — Phase 2

| Destination | Status |
|---|---|
| Snowflake | Phase 2 |
| BigQuery | Phase 2 |
| DuckDB (local testing) | Phase 2 |

### dlt Pipeline Naming Convention

```python
pipeline_name = f"pipelinekit_{config.pipeline.name}"
dataset_name  = f"pipelinekit_{config.pipeline.name}_raw"
```

Human-readable, version-controllable per ADR-009.

---

## Transformation Adapter — dbt Core

```python
# src/pipelinekit/adapters/transformation/dbt/adapter.py

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.config.schema import TransformationSection
from pipelinekit.runtime.result import StepResult

class DbtTransformationAdapter(BaseAdapter):
    """dbt Core transformation adapter.

    Executes dbt build and parses run_results.json.
    All dbt-specific logic stays inside this file.
    """

    def __init__(self, config: TransformationSection):
        self.config = config

    def initialize(self) -> None:
        """Verify dbt project directory exists and dbt is available."""
        ...

    def validate(self) -> StepResult:
        """Run dbt parse to validate project without executing."""
        ...

    def execute(self) -> StepResult:
        """
        Run: dbt build --project-dir <config.project_dir>
        Parse: run_results.json
        Return: StepResult with pass/fail counts
        """
        ...

    def status(self) -> dict:
        """Return last dbt run summary from run_results.json."""
        ...
```

### dbt Execution Rules

- dbt is invoked via `subprocess` — never imported as a Python library
- Command: `dbt build --project-dir <path> --profiles-dir <path>`
- Parse `run_results.json` for structured results
- Parse `manifest.json` for model metadata (Phase 3)
- All dbt output captured and stored — never streamed raw to console
- dbt exit code 0 = success, non-zero = failure → map to `PK-ADAPTER-002`

---

## Quality Adapter — Soda

```python
# src/pipelinekit/adapters/quality/soda/adapter.py

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.config.schema import QualitySection
from pipelinekit.runtime.result import StepResult

class SodaQualityAdapter(BaseAdapter):
    """Soda quality check adapter.

    Executes Soda checks and returns structured pass/fail results.
    All Soda-specific logic stays inside this file.
    """

    def __init__(self, config: QualitySection):
        self.config = config

    def initialize(self) -> None:
        """Verify checks directory exists and Soda is available."""
        ...

    def validate(self) -> StepResult:
        """Parse check files without executing against database."""
        ...

    def execute(self) -> StepResult:
        """
        Run Soda checks from config.checks_dir.
        Return StepResult with pass/fail/warn counts.
        """
        ...

    def status(self) -> dict:
        """Return last Soda scan summary."""
        ...
```

---

## AdapterFactory

The runtime uses `AdapterFactory` to create adapters — it never instantiates them directly.
This is the single point where adapter selection logic lives.

```python
# src/pipelinekit/adapters/factory.py

from pipelinekit.config.schema import PipelineConfig
from pipelinekit.adapters.base import BaseAdapter

class AdapterFactory:
    """Creates adapter instances from PipelineConfig.

    The runtime calls this factory — it never instantiates
    adapters directly. This keeps provider selection logic
    in one place and makes adapters replaceable.
    """

    @staticmethod
    def create_ingestion(config: PipelineConfig) -> BaseAdapter | None:
        """Return dlt ingestion adapter, or None if ingestion not configured."""
        ...

    @staticmethod
    def create_transformation(config: PipelineConfig) -> BaseAdapter | None:
        """Return dbt adapter, or None if transformation.enabled=False."""
        ...

    @staticmethod
    def create_quality(config: PipelineConfig) -> BaseAdapter | None:
        """Return Soda adapter, or None if quality.enabled=False."""
        ...
```

---

## File Structure

```
src/pipelinekit/
└── adapters/
    ├── __init__.py
    ├── base.py                     BaseAdapter ABC
    ├── factory.py                  AdapterFactory
    ├── ingestion/
    │   ├── __init__.py
    │   └── dlt/
    │       ├── __init__.py
    │       └── adapter.py          DltIngestionAdapter
    ├── transformation/
    │   ├── __init__.py
    │   └── dbt/
    │       ├── __init__.py
    │       └── adapter.py          DbtTransformationAdapter
    └── quality/
        ├── __init__.py
        └── soda/
            ├── __init__.py
            └── adapter.py          SodaQualityAdapter
```

---

## pyproject.toml additions — Phase 2

```toml
[tool.poetry.dependencies]
dlt = {extras = ["snowflake", "bigquery", "duckdb"], version = "^1.0"}
dbt-core = "^1.8"
dbt-snowflake = "^1.8"
dbt-bigquery = "^1.8"
soda-core = "^3.0"
soda-core-postgres = "^3.0"
```

**Important:** dlt, dbt, and Soda are only imported inside their adapter files.
They are never imported in `runtime/`, `cli/`, `config/`, `state/`, or `core/`.
If an import of dlt, dbt, or Soda appears outside `adapters/`, it is a violation.

---

## Test Strategy for Adapters

Adapter tests must not require real database connections.
All adapter tests use mocking or stub implementations.

```python
# tests/adapters/ingestion/test_dlt_adapter.py

from unittest.mock import patch, MagicMock
from pipelinekit.adapters.ingestion.dlt.adapter import DltIngestionAdapter

def test_execute_returns_step_result(mock_ingestion_config):
    with patch("dlt.pipeline") as mock_pipeline:
        mock_pipeline.return_value.run.return_value = MagicMock(load_packages=[])
        adapter = DltIngestionAdapter(mock_ingestion_config)
        adapter.initialize()
        result = adapter.execute()
        assert result.status.value == "success"
        assert result.step == "ingestion"
```

---

## Error Code Mapping

Every provider error must map to a PK error code:

| Provider Error | PK Code |
|---|---|
| dlt connection refused | `PK-ADAPTER-001` |
| dlt execution failed | `PK-ADAPTER-002` |
| dbt project not found | `PK-ADAPTER-001` |
| dbt build failed | `PK-ADAPTER-002` |
| dbt invalid result | `PK-ADAPTER-003` |
| Soda checks not found | `PK-ADAPTER-001` |
| Soda check failed | `PK-ADAPTER-002` |

---

## Constraints

- All provider imports isolated inside adapter files
- No adapter imports from another adapter
- No adapter imports from CLI
- No adapter imports from AI layer
- All adapters return `StepResult` — never raw provider objects
- All adapter errors mapped to PK error codes before propagating
- Adapters are synchronous in Phase 2

---

## Acceptance Criteria

```
✓ BaseAdapter interface implemented and enforced
✓ DltIngestionAdapter implements all 4 required methods
✓ DbtTransformationAdapter implements all 4 required methods
✓ SodaQualityAdapter implements all 4 required methods
✓ AdapterFactory creates correct adapter per config
✓ No dlt/dbt/Soda imports outside adapters/ directory
✓ All adapter tests pass without real database connections
✓ All provider errors map to PK error codes
✓ poetry run pytest tests/adapters/ → all tests pass
✓ coverage >= 80% on src/pipelinekit/adapters/
```

---

## Out of Scope

- Salesforce, HubSpot, Stripe adapters — Phase 3
- Notification adapter (Resend) — Phase 3
- AI adapter (LLMProvider) — Phase 4
- Async adapter execution — Phase 3+
- Adapter retry logic — Phase 3
- Adapter connection pooling — Phase 3+
