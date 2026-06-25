# PipelineKit — Phase 3 Claude Code Implementation Prompt
## Trust Layer Sprint: Observability + Notifications + Blueprint #001 + CI

---

## Your Identity

You are Claude Code operating as three agents simultaneously:

**Primary:** blueprint-engineer — owns `src/pipelinekit/blueprints/`, `blueprints/`  
**Secondary:** release-engineer — owns `.github/workflows/`, CI pipeline  
**Supporting:** runtime-engineer — extends runner.py for notifications only

Your agent definitions:
- `agents/blueprint-engineer/AGENT.md` + `SYSTEM.md`
- `agents/release-engineer/AGENT.md` + `SYSTEM.md`
- `agents/runtime-engineer/AGENT.md` (notifications extension only)

You do not own the CLI. You do not own the AI layer. You do not own Phase 4.

---

## Repository

```
Local path: C:\Users\HP\Documents\pipelinekit
GitHub:     https://github.com/emkwambe/pipelinekit
```

---

## Read First — In This Exact Order

Before writing a single line of code:

```
1.  .claude/CLAUDE.md
2.  docs/constitution/Product-Constitution.md
3.  docs/decisions/ADR-000-Foundational-Architecture-Decisions.md
4.  agents/blueprint-engineer/AGENT.md
5.  agents/blueprint-engineer/SYSTEM.md
6.  agents/release-engineer/AGENT.md
7.  agents/release-engineer/SYSTEM.md
8.  docs/specifications/SPEC-006-Blueprint-Engine.md       ← Primary spec
9.  docs/specifications/SPEC-008-Notification-System.md    ← Notification spec
10. docs/specifications/SPEC-003-Pipeline-Runtime.md       ← Runner extension
11. docs/specifications/SPEC-010-Testing-and-Quality-Gates.md
12. docs/reference/PROJECT-STATUS.md
13. docs/reference/Error-Codes.md
14. contracts/notification.yaml
15. schemas/blueprint.schema.json
16. schemas/diagnostic.schema.json
17. src/pipelinekit/runtime/runner.py                      ← Extend for notifications
18. src/pipelinekit/adapters/base.py                       ← BaseAdapter you implement
19. src/pipelinekit/contracts/models.py                    ← ContractResult you use
20. src/pipelinekit/core/errors.py                         ← Add BlueprintError only
21. docs/specifications/archive/SPEC-006-OLD-Blueprint-Catalog.md
22. docs/specifications/archive/SPEC-003-OLD-Blueprint-001-Postgres-to-Snowflake.md
```

---

## Sprint Goal

Deliver Phase 3 such that all of the following work:

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry run pipelinekit blueprint list
poetry run pipelinekit blueprint validate
poetry run pipelinekit blueprint info postgres-to-snowflake
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

**Plus** — all 87 Phase 1 + Phase 2 tests must still pass.
**Plus** — CI pipeline must pass on push to GitHub.

---

## Files You Are Allowed To Create

```
src/pipelinekit/
├── blueprints/
│   ├── __init__.py
│   ├── models.py          BlueprintMetadata, BlueprintSource, BlueprintDestination
│   ├── registry.py        BlueprintRegistry (local directory scan)
│   └── validator.py       BlueprintValidator (jsonschema against blueprint.schema.json)
├── notifications/
│   ├── __init__.py
│   ├── models.py          Notification, NotificationResult, enums
│   ├── dispatcher.py      NotificationDispatcher
│   └── templates.py       Message template builders
├── adapters/
│   └── alerts/
│       ├── __init__.py
│       └── resend/
│           ├── __init__.py
│           └── adapter.py     ResendNotificationAdapter
└── cli/
    └── blueprint.py       blueprint list, validate, info commands

blueprints/
└── postgres-to-snowflake/
    ├── blueprint.json
    ├── ingestion/
    │   └── pipeline.py
    ├── transform/
    │   ├── dbt_project.yml
    │   ├── profiles.yml
    │   └── models/
    │       ├── staging/
    │       │   └── stg_orders.sql
    │       └── core/
    │           └── fct_orders.sql
    ├── contracts/
    │   └── orders.yaml
    ├── quality/
    │   └── checks.yaml
    ├── alerts/
    │   └── config.yaml
    └── docs/
        ├── README.md
        └── runbook.md

.github/
└── workflows/
    └── ci.yml

tests/
├── blueprints/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_registry.py
│   └── test_validator.py
└── notifications/
    ├── __init__.py
    ├── test_models.py
    ├── test_dispatcher.py
    └── test_resend_adapter.py
```

You may also modify:
```
src/pipelinekit/core/errors.py        Add BlueprintError only
src/pipelinekit/cli/main.py           Register blueprint command group only
src/pipelinekit/runtime/runner.py     Add notification dispatch in finally block only
src/pipelinekit/config/schema.py      Extend NotificationsSection if needed
pyproject.toml                        Add resend, jsonschema dependencies only
.mcp/registry/servers.md             Add Resend MCP entry only
```

---

## Files You Must Not Modify

```
docs/                                    ← READ ONLY
docs/reference/PROJECT-STATUS.md        ← NEVER TOUCH — Command Center owns this
contracts/                               ← READ ONLY
schemas/                                 ← READ ONLY
agents/                                  ← READ ONLY
.claude/                                 ← READ ONLY
prompts/                                 ← READ ONLY
skills/                                  ← READ ONLY
runtime/                                 ← READ ONLY (scaffold)
examples/                                ← READ ONLY
scripts/                                 ← READ ONLY
README.md                                ← READ ONLY
LICENSE                                  ← READ ONLY
src/pipelinekit/core/errors.py           ← ADD BlueprintError only
src/pipelinekit/config/schema.py         ← EXTEND NotificationsSection only
src/pipelinekit/adapters/base.py         ← READ ONLY
src/pipelinekit/adapters/factory.py      ← READ ONLY
src/pipelinekit/adapters/ingestion/      ← READ ONLY
src/pipelinekit/adapters/transformation/ ← READ ONLY
src/pipelinekit/adapters/quality/        ← READ ONLY
src/pipelinekit/contracts/               ← READ ONLY
src/pipelinekit/state/                   ← READ ONLY
src/pipelinekit/cli/init.py              ← READ ONLY
src/pipelinekit/cli/validate.py          ← READ ONLY
src/pipelinekit/cli/status.py            ← READ ONLY
src/pipelinekit/cli/run.py               ← READ ONLY
tests/cli/                               ← READ ONLY
tests/config/                            ← READ ONLY
tests/state/                             ← READ ONLY
tests/runtime/                           ← READ ONLY
tests/adapters/                          ← READ ONLY
tests/contracts/                         ← READ ONLY
```

---

## pyproject.toml — Phase 3 Additions Only

```toml
[tool.poetry.dependencies]
resend = "^2.0"
jsonschema = "^4.0"
```

All Resend imports stay inside `src/pipelinekit/adapters/alerts/resend/adapter.py`.
Zero Resend imports anywhere else.

---

## Implementation Requirements

### 1. src/pipelinekit/core/errors.py — Addition Only

Add one class after the existing error hierarchy:

```python
class BlueprintError(PipelineKitError):
    """Raised when a blueprint is missing, invalid, or cannot be executed."""
```

Do not change any existing class.

---

### 2. src/pipelinekit/blueprints/models.py

Implement exactly as in SPEC-006:
- `BlueprintSource` — type, dlt_source
- `BlueprintDestination` — type, dlt_destination
- `BlueprintMetadata` — full Pydantic model matching blueprint.json structure

---

### 3. src/pipelinekit/blueprints/registry.py

`BlueprintRegistry` scans the local `blueprints/` directory.
Phase 3: local only — no remote registry.

```python
class BlueprintRegistry:
    def __init__(self, blueprints_dir: Path = Path("blueprints")):
        ...

    def list(self) -> list[BlueprintMetadata]:
        """Scan blueprints/ and return all valid blueprints."""
        ...

    def get(self, name: str) -> BlueprintMetadata | None:
        """Return named blueprint metadata or None."""
        ...

    def exists(self, name: str) -> bool:
        ...
```

`list()` returns `[]` when `blueprints/` is empty or does not exist — never raises.

---

### 4. src/pipelinekit/blueprints/validator.py

`BlueprintValidator` validates `blueprint.json` against `schemas/blueprint.schema.json`.
Uses `jsonschema` library — imported only in this file.

```python
class BlueprintValidator:
    def validate(self, blueprint_path: Path) -> None:
        """
        Raises BlueprintError(PK-BLUEPRINT-001) on schema violation.
        Raises BlueprintError(PK-BLUEPRINT-002) if blueprint.json not found.
        """
        ...
```

---

### 5. blueprints/postgres-to-snowflake/ — Blueprint #001

Build the complete blueprint directory per SPEC-006.

**blueprint.json** must validate against `schemas/blueprint.schema.json`.
Required fields: `name`, `version`, `source`, `destination`, `contracts`

```json
{
  "name": "postgres-to-snowflake",
  "version": "1.0.0",
  "description": "Postgres to Snowflake trusted analytics pipeline",
  "source": {"type": "postgres", "dlt_source": "sql_database"},
  "destination": {"type": "snowflake", "dlt_destination": "snowflake"},
  "contracts": ["contracts/orders.yaml"],
  "tags": ["postgres", "snowflake", "product-analytics"],
  "kpis": ["Daily Orders", "Revenue", "Customers", "Order Value", "Retention"],
  "deploy_time_minutes": 60,
  "time_to_trusted_data_hours": 24
}
```

**ingestion/pipeline.py** — dlt pipeline definition (see SPEC-006 for exact code)

**transform/models/staging/stg_orders.sql** — staging model

**transform/models/core/fct_orders.sql** — core fact model

**contracts/orders.yaml** — ContractDefinition with freshness, required_columns,
uniqueness, not_null, row_count rules

**quality/checks.yaml** — Soda checks for orders table

**alerts/config.yaml** — notification config for this blueprint

**docs/README.md** — prerequisites, installation steps, first run

**docs/runbook.md** — operational runbook covering troubleshooting, KPI definitions

---

### 6. src/pipelinekit/notifications/models.py

Implement exactly as SPEC-008:
- `NotificationSeverity` enum (info, warning, error, critical)
- `NotificationChannel` enum (email; slack/webhook Phase 4 stubs)
- `Notification` Pydantic model — must satisfy contracts/notification.yaml
  required fields: channel, recipient, severity, message, evidence
- `NotificationResult` Pydantic model

---

### 7. src/pipelinekit/notifications/templates.py

Build notification message templates for three events:
- `pipeline_failed_notification(result)` → `Notification`
- `contract_violated_notification(result, contract_results)` → `Notification`
- `pipeline_succeeded_notification(result)` → `Notification`

Templates must produce human-readable subject + message (see SPEC-008 examples).
Evidence dict must be structured for Phase 4 AI diagnostics — not free-form text.

---

### 8. src/pipelinekit/notifications/dispatcher.py

`NotificationDispatcher` routes to the correct adapter.

Critical rules from SPEC-008:
- `dispatch()` never raises — always returns `NotificationResult`
- Notification failure must never block pipeline state recording
- Only dispatches when `notifications.enabled=True`
- `notify_pipeline_result()` dispatches based on pipeline outcome and config

---

### 9. src/pipelinekit/adapters/alerts/resend/adapter.py

`ResendNotificationAdapter` implements `BaseAdapter` + adds `send()`.

All `resend` library imports inside this file only.
`send()` never raises — returns `NotificationResult` with `sent=False` on failure.
Maps Resend errors to `PK-NOTIFY-*` codes.

API key from environment variable: `RESEND_API_KEY`
Never hardcode credentials. Never log credentials.

---

### 10. src/pipelinekit/runtime/runner.py — Extension Only

Add notification dispatch in the `finally` block of `run()`, after state update:

```python
finally:
    # 1. Always update state first
    state.db.update_run(run_id, ...)

    # 2. Then dispatch notifications — failure must not corrupt state
    if self.config.notifications.enabled:
        try:
            dispatcher = NotificationDispatcher(self.config.notifications)
            dispatcher.initialize()
            dispatcher.notify_pipeline_result(result, contract_results)
        except Exception:
            pass  # Notification failure is logged, never propagated
```

Do not change any other part of `runner.py`.

---

### 11. src/pipelinekit/cli/blueprint.py

Register a Typer command group for blueprint commands:

```python
blueprint_app = typer.Typer(
    name="blueprint",
    help="Manage PipelineKit blueprints.",
    no_args_is_help=True,
)
```

Three commands:

**blueprint list** — table of installed blueprints (name, version, source, destination)

**blueprint validate** — validate blueprint structure, exits 0 or 1

**blueprint info <name>** — show blueprint details (description, KPIs, deploy time)

Register in `src/pipelinekit/cli/main.py`:
```python
from pipelinekit.cli.blueprint import blueprint_app
app.add_typer(blueprint_app, name="blueprint")
```

---

### 12. .github/workflows/ci.yml — CI Pipeline

release-engineer activates here. Create the CI pipeline:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        run: poetry install

      - name: Lint
        run: poetry run ruff check .

      - name: Format check
        run: poetry run black --check .

      - name: Type check
        run: poetry run mypy src/pipelinekit

      - name: Test
        run: poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
```

---

### 13. .mcp/registry/servers.md — Resend Entry

Add Resend to the MCP registry:

```markdown
## Resend

**Type:** Notification  
**Phase:** 3  
**Purpose:** Email delivery for pipeline alerts and contract violation notifications  
**API:** https://api.resend.com  
**Auth:** RESEND_API_KEY environment variable  
**Status:** Active (Phase 3)
```

---

## Test Requirements

**All 87 Phase 1 + Phase 2 tests must continue to pass.**

No network calls in any test. No real Resend API calls. Mock all external services.

### Minimum tests required:

**tests/blueprints/test_models.py** — 3 tests:
- Valid blueprint.json loads into BlueprintMetadata
- Missing required field raises ValidationError
- Source and destination models load correctly

**tests/blueprints/test_registry.py** — 4 tests:
- `list()` returns empty list when blueprints/ absent
- `list()` returns BlueprintMetadata for valid blueprint
- `get()` returns metadata for existing blueprint
- `get()` returns None for missing blueprint

**tests/blueprints/test_validator.py** — 3 tests:
- Valid blueprint.json passes validation
- Invalid blueprint.json raises BlueprintError(PK-BLUEPRINT-001)
- Missing blueprint.json raises BlueprintError(PK-BLUEPRINT-002)

**tests/notifications/test_models.py** — 3 tests:
- Notification satisfies contracts/notification.yaml required fields
- NotificationResult.sent is False on delivery failure
- Evidence dict is structured (not empty string)

**tests/notifications/test_dispatcher.py** — 4 tests:
- `dispatch()` never raises on adapter failure
- `notify_pipeline_result()` sends notification on FAILED result
- `notify_pipeline_result()` does nothing when enabled=False
- `notify_pipeline_result()` sends contract violation notification

**tests/notifications/test_resend_adapter.py** — 3 tests:
- `send()` returns NotificationResult with sent=True on success (mocked)
- `send()` returns NotificationResult with sent=False on Resend error (mocked)
- No resend imports detectable outside adapter file

---

## Architecture Rules — Non-Negotiable

```
All Resend imports inside adapters/alerts/resend/adapter.py only
Notification failure never raises out of dispatcher              (SPEC-008)
Notification dispatch happens after state update                 (SPEC-008)
Blueprint engine never calls adapters directly                   (SPEC-006)
Blueprint engine delegates execution to PipelineRunner           (SPEC-006)
blueprints/ files are YAML/SQL/JSON/Markdown only               (SPEC-006)
No AI calls anywhere in Phase 3                                  (Constitution)
No hardcoded API keys or credentials                             (ADR-005)
PROJECT-STATUS.md never touched                                  (Command Center)
CI must pass on push before Phase 3 is closed                   (release-engineer)
```

---

## Validation Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry install

# Verify Phase 1 + 2 still works
poetry run pipelinekit --help
poetry run pipelinekit init
poetry run pipelinekit validate
poetry run pipelinekit status
poetry run pipelinekit run --dry-run

# Verify Phase 3 works
poetry run pipelinekit blueprint list
poetry run pipelinekit blueprint validate
poetry run pipelinekit blueprint info postgres-to-snowflake

# Full quality gate
poetry run pytest --cov=src/pipelinekit --cov-report=term-missing --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

Phase 3 is complete when ALL of the following are true:

```
✓ poetry install completes with no errors
✓ All 87 Phase 1 + Phase 2 tests still pass
✓ pipelinekit blueprint list shows postgres-to-snowflake
✓ pipelinekit blueprint validate exits 0 on valid blueprint
✓ pipelinekit blueprint validate exits 1 with PK-BLUEPRINT-001 on invalid
✓ pipelinekit blueprint info postgres-to-snowflake shows details
✓ blueprints/postgres-to-snowflake/blueprint.json validates against schema
✓ NotificationDispatcher never raises on delivery failure
✓ ResendNotificationAdapter maps all errors to PK-NOTIFY-* codes
✓ PipelineRunner dispatches notifications after state update
✓ .github/workflows/ci.yml exists and is valid YAML
✓ .mcp/registry/servers.md updated with Resend entry
✓ pytest passes — all tests green (Phase 1 + 2 + 3)
✓ coverage >= 80% across src/pipelinekit/
✓ ruff check passes — zero errors
✓ black --check passes — zero errors
✓ mypy passes — zero errors
✓ No API keys, credentials, or secrets in any file
✓ PROJECT-STATUS.md untouched
```

---

## Stop and Ask Before

- Adding any dependency not listed above (resend, jsonschema)
- Creating any file not in the allowed list
- Importing resend outside `adapters/alerts/resend/adapter.py`
- Touching PROJECT-STATUS.md for any reason
- Modifying any Phase 1 or Phase 2 test
- Implementing Phase 4 features (AI, pipelinekit diagnose, MCP AI layer)
- Making any external network call in source code or tests
- Hardcoding any API key, credential, or secret

---

## Final Instruction

Phase 3 is called the Trust Layer for a reason.

Blueprints make trusted analytics deployable in under 60 minutes.
Notifications make failures visible before they become business problems.
CI makes the codebase trustworthy on every push.

These three things together — Blueprint #001, notifications, CI — are what
transforms PipelineKit from a CLI tool into a trusted analytics platform.

Blueprint #001 is the first thing a design partner will install.
Make it production-quality. Make the runbook honest. Make the contracts real.

The product is Trusted Analytics Infrastructure.
Phase 3 is where that name becomes true.
