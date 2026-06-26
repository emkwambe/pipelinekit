# PipelineKit Engineering Playbook
## The Complete Guide to Building, Extending, and Operating PipelineKit

**Version:** 1.0  
**Date:** June 26, 2026  
**Author:** Command Center (Claude Chat) + Eddy Mkwambe  
**Repository:** https://github.com/emkwambe/pipelinekit  
**Status:** Living document — updated after each phase

---

## Table of Contents

1. What PipelineKit Is
2. The Governing Principle
3. The Architecture
4. The Development Trio
5. The Workflow
6. The Document Chain
7. The Adapter Pattern
8. The Blueprint Pattern
9. The AI Layer
10. The Credential System
11. The Quality System
12. The Health System
13. The Test Strategy
14. The Error System
15. Architectural Smells — All 16
16. The Decision Log
17. Lessons Learned
18. What Breaks and Why
19. The Sprint Pattern
20. Design Partner Readiness

---

## 1. What PipelineKit Is

PipelineKit is a CLI-first, AI-native analytics pipeline operating system. It does not replace ingestion tools, transformation tools, or quality tools. It operates above them — coordinating, validating, governing, diagnosing, and reasoning about analytics pipelines regardless of which tools are underneath.

It was built to answer three questions:

- **Why did this pipeline fail?** (Phase 4 — AI Diagnostics)
- **What architecture should this pipeline use?** (Phase 5 — Architecture Intelligence)
- **Is this pipeline trusted?** (Phases 1-3 — Foundation, Data Layer, Trust Layer)

The product a user interacts with is a CLI:

```powershell
pipelinekit init
pipelinekit validate --contracts
pipelinekit run
pipelinekit blueprint list
pipelinekit diagnose
pipelinekit architect analyze
pipelinekit health
```

Everything else — adapters, contracts, blueprints, AI providers, state — exists to make those commands reliable, deterministic, and trustworthy.

---

## 2. The Governing Principle

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

This sentence is immutable. It was written before the first line of code and it has not changed through 5 phases, 225 tests, 5 AI providers, and a major market merger.

Every decision traces to it or does not get made.

**What it means:**

- **AI-native** — AI is not a feature added on top. It is designed in from Phase 1. The diagnostic schema, the evidence architecture, the LLMProvider protocol — all were designed before the AI code was written.
- **Operating system** — not a tool. An OS coordinates other tools. It provides policies, lifecycle management, diagnostics, and resource management. PipelineKit does not replace dlt, dbt, or Soda — it operates above them.
- **Trusted** — correctness is verifiable. Contracts define truth. Quality checks enforce it. AI interprets evidence. Humans approve action.
- **Analytics pipelines** — the scope is specific. Not general automation. Not ML infrastructure. Analytics pipelines: ingestion, transformation, quality, governance.

---

## 3. The Architecture

### Five Layers

```
Layer 5: Architecture Intelligence  ← "What architecture should I use?"
Layer 4: Intelligence Layer         ← "Why did this fail?"
Layer 3: Trust Layer                ← Blueprints + Notifications + CI
Layer 2: Data Layer                 ← Runtime + Adapters + Contracts
Layer 1: Foundation                 ← CLI + Config + State + Errors
```

Each layer is complete before the next begins. This is not a convention — it is a hard rule. Phase 2 cannot start until Phase 1 is green with tests, coverage, and quality gates passing.

### Source Structure

```
src/pipelinekit/
├── core/           Error hierarchy
├── config/         PipelineConfig (Pydantic v2), loader, ${VAR} interpolation
├── state/          SQLite state store (6 tables)
├── cli/            11 commands across 4 groups
├── runtime/        PipelineRunner, PipelineResult, executor
├── adapters/       dlt, dbt, Soda, Resend — all behind BaseAdapter
├── contracts/      ContractValidator (6 checks)
├── blueprints/     BlueprintRegistry, BlueprintValidator
├── notifications/  NotificationDispatcher, templates
├── health/         5 health checkers
└── ai/             LLMProvider, EvidenceCollector, DiagnosticsEngine,
                    ArchitectureEngine, ADRReader, 5 providers
```

### The State Store

SQLite at `.pipelinekit/state.db`. Six tables:

| Table | Added | Purpose |
|---|---|---|
| pipeline_runs | Phase 1 | Every run result |
| validation_runs | Phase 1 | Every validate result |
| contract_results | Phase 2 | Per-table contract outcomes |
| diagnostic_results | Phase 4 | AI diagnostic outputs |
| architecture_results | Phase 5 | Architecture recommendations |
| health_runs | Sprint 6-1 | Health check history |

All tables use `CREATE TABLE IF NOT EXISTS` — safe on every startup and on pre-existing databases.

---

## 4. The Development Trio

Every sprint uses this exact three-role model:

```
Command Center (Claude Chat)
  → Strategy, SPECs, ADRs, sprint prompts, PROJECT-STATUS
  → Writes no code
  → Owns exactly one file: docs/reference/PROJECT-STATUS.md

Claude Code
  → Implementation, testing, commits
  → Reads SPECs and documents before writing anything
  → Flags decisions, never self-approves architectural changes
  → Branches every sprint, fast-forwards to main after verification

Eddy (Founder)
  → Verification, PowerShell, final commit authority
  → Runs quality gates locally
  → Pastes output back to Command Center
  → Commits PROJECT-STATUS after Command Center produces it
```

**Why this works:**

The Command Center thinks before Claude Code acts. SPECs are written before code. ADRs are written before SPECs. The document chain governs everything. Claude Code never makes architectural decisions — it flags them and waits.

This separation prevented every major architectural error in the project:
- Provider factory location (Phase 4) — Claude Code flagged, documents won
- dlt credential mechanism (Sprint 6-2a) — Claude Code stopped, ADR-017 was written
- adr_compliance schema conflict (Sprint 6-1) — Claude Code stopped and asked
- Soda API dead mock (Sprint 6-2a) — Claude Code flagged false confidence
- Blueprint #001 verification — Claude Code did Option 3, not Option 1

---

## 5. The Workflow

**The 8-Step Trio Loop — runs every sprint without exception:**

```
1. Read Claude Code output completely
   Never skim. The flagged decisions are the most important lines.

2. Evaluate each flagged decision
   - Is it correct? (documents win over prompt — CLAUDE.md v3)
   - Does it introduce drift? (SPEC, contract, schema, error code)
   - Does it trigger any of the 16 smells?
   - Verdict: approved / needs fix / needs ADR

3. Check the boundary
   - Only allowed files were modified
   - PROJECT-STATUS.md untouched
   - No provider imports leaked outside adapters

4. Give Claude Code the commit instruction
   Exact commit message. Branch name. Fast-forward to main. Delete branch.

5. Wait for push confirmation
   Never produce PROJECT-STATUS until Eddy pastes the hash on main.

6. Produce updated PROJECT-STATUS
   New hash, what was built, quality gates, decisions, hardening checklist, next sprint.

7. Give Eddy the commit command for PROJECT-STATUS
   Copy-Item, git add, git commit, git push.

8. State the next action clearly
   One sentence. No ambiguity.
```

**The pre-flight (runs before every sprint prompt is written):**

Check all 16 architectural smells. All must pass. Any failure → stop, resolve, then proceed.

---

## 6. The Document Chain

Architecture lives only in version-controlled documents. The chain is:

```
Constitution → ADR → SPEC → Contract → Schema → Code
```

**Never skip a step.** A prompt suggestion is not architecture. A Claude Code flag is not an ADR. A SPEC stub is not a SPEC.

### Constitution (`docs/constitution/Product-Constitution.md`)
The governing principle and mission. Updated only by Eddy.

### ADRs (`docs/decisions/`)
Every architectural decision. Format: context → decision → alternatives → consequences.
17 ADRs as of Sprint 6-2a. Key ones:

| ADR | Decision |
|---|---|
| ADR-005 | BYOK — customer provides all API keys |
| ADR-007 | AI is Operator not Owner — recommends, never acts |
| ADR-008 | Deterministic before AI |
| ADR-009 | Human-readable output |
| ADR-013 | Resend MCP governance |
| ADR-014 | AI provider MCP layer (direct API, not MCP in Phase 4/5) |
| ADR-015 | Architecture Intelligence scope |
| ADR-016 | Provider diversity — non-US required |
| ADR-017 | dlt credential integration — PipelineKit owns config |

### SPECs (`docs/specifications/`)
Implementation contracts. Written before code. Never deviate without updating the SPEC.
13 SPECs as of Sprint 6-3. Key ones:

| SPEC | What it governs |
|---|---|
| SPEC-001 | CLI framework |
| SPEC-002 | Configuration system |
| SPEC-003 | Pipeline runtime |
| SPEC-004 | Contracts |
| SPEC-005 | AI diagnostics |
| SPEC-006 | Blueprint engine |
| SPEC-012 | Health command system |
| SPEC-013 | Blueprint #002 |

### PROJECT-STATUS (`docs/reference/PROJECT-STATUS.md`)
Current state. Updated after every completed phase or verified sprint. Never mid-sprint. Command Center owns it exclusively.

---

## 7. The Adapter Pattern

Every external tool is behind an adapter. This is the single most important architectural decision in the codebase.

```
CLI → Runtime → AdapterFactory → BaseAdapter → [dlt | dbt | Soda | Resend | AI provider]
```

**The rule:** Provider-specific imports live only inside the adapter file. Zero leakage.

```python
# CORRECT — dlt import inside adapter
class DltIngestionAdapter(BaseAdapter):
    def execute(self) -> StepResult:
        import dlt  # inside the method, inside the adapter
        ...

# WRONG — dlt import at module level, outside adapter
import dlt  # never
```

**Why this matters:**

1. SDK upgrades touch one file — `anthropic ^0.25` → `^1.0` means editing `ai/providers/anthropic.py` only
2. Provider replacement is config-driven — switching from OpenAI to DeepSeek is one YAML change
3. Tests mock at the protocol level — no real API calls in CI
4. The CLI never knows which provider is active — it calls the interface

**The pattern for adding a new provider:**

1. Create `src/pipelinekit/ai/providers/newprovider.py`
2. Implement all methods in `LLMProvider` Protocol
3. Register in `providers/__init__.py` factory
4. Add API key env var to documentation
5. Document data residency in the class docstring
6. Write 3 tests (diagnose, missing key, import isolation)

No ADR needed for providers that follow ADR-016 (non-US requirement). An ADR IS needed if adding a provider from a region already represented.

---

## 8. The Blueprint Pattern

A blueprint is a complete analytics system — not a connector, not a template.

**The 8 required assets (Smell 15 enforces this):**

```
blueprints/<name>/
├── blueprint.json          ← Manifest — name, version, source, dest, tables, claims
├── pipelinekit.example.yaml ← Reference config — all 8 sections, ${VAR} only
├── ingestion/pipeline.py   ← dlt source definition
├── transform/              ← Complete dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml        ← Both prod and local targets
│   └── models/
│       ├── sources.yml     ← env_var() for database/schema — never hardcoded
│       ├── staging/        ← One model per source table
│       └── core/           ← Business logic models
├── contracts/              ← One contract file per key table
├── quality/checks.yaml     ← Soda checks
├── alerts/config.yaml      ← Notification config
└── docs/
    ├── README.md
    └── runbook.md          ← Must include Verified Deployments table
```

**The verification requirement:**

Every blueprint must have a Verified Deployments row in its runbook before design partner outreach. A claim in `blueprint.json` (`deploy_time_minutes: 60`) is an assertion until there is a real run record.

**Blueprint #001 verification arc lessons:**

- The dlt adapter was a Phase 2 scaffold — it returned `[]` and passed no credentials. Never ship a scaffold as production code.
- `pipelinekit validate` passing does not mean the pipeline runs — it means the config is valid. Real end-to-end verification requires real infrastructure.
- Docker Postgres is the correct local testing baseline. Use it from the start, not after debugging cloud failures.
- The `--local` flag on the verification script (DuckDB destination) eliminates cloud credential requirements for local testing.
- dbt `sources.yml` must be inside `models/` — not in `transform/`. dbt only reads sources from within the model paths.
- dlt schema names follow the pattern `pipelinekit_pipeline_raw` (pipeline name + `_raw`). Match this in `sources.yml`.

---

## 9. The AI Layer

### The AI Boundary (ADR-007 — non-negotiable)

```
AI MAY:      inspect, diagnose, recommend, summarize, classify, architect
AI MAY NOT:  execute, deploy, modify production, rotate secrets, auto-apply
```

This boundary is enforced by design, not by convention:
- `can_auto_fix = False` in `DiagnosticResult` — engine corrects any True from provider
- `can_auto_apply = False` in `ArchitectureResult` — same enforcement
- No code path exists to execute a `RecommendedAction`
- `test_no_action_is_auto_executed` asserts this in the test suite

### The Evidence Architecture

AI quality is bounded by evidence quality. Garbage in, garbage out.

`EvidencePackage` assembles structured evidence from `state.db` before any AI call:
- `pipeline_result` — what ran
- `step_results` — per-step outcomes
- `contract_results` — what failed validation
- `validation_results` — what was checked
- `recent_runs` — last 5 runs for pattern detection
- `config_snapshot` — what was configured
- `error_codes` — all PK-* codes from this run

Evidence is read-only. `EvidenceCollector` never writes to state.db.

### The Schema Validation Trust Boundary

Every AI output validates against its schema before reaching the CLI:

- `schemas/diagnostic.schema.json` — 5 required fields for DiagnosticResult
- `schemas/architecture.schema.json` — 7 required fields for ArchitectureResult

If validation fails → `LLMError(PK-AI-002)` is raised. The user sees a clean error, never raw AI output. This is the trust boundary. It is not optional.

### The Five Providers

| Provider | Region | Key | Use Case |
|---|---|---|---|
| Anthropic | US | `ANTHROPIC_API_KEY` | Default — best reasoning |
| OpenAI | US | `OPENAI_API_KEY` | Alternative US cloud |
| Ollama | Local | `OLLAMA_HOST` | Air-gapped enterprise |
| DeepSeek | China | `DEEPSEEK_API_KEY` | Cost-sensitive, Asian markets |
| Mistral | EU/France | `MISTRAL_API_KEY` | GDPR-compliant EU deployments |

Provider diversity is policy (ADR-016). PipelineKit must always offer at least one non-US cloud provider.

---

## 10. The Credential System

**ADR-017: PipelineKit owns credential configuration.**

`pipelinekit.yaml` is the single source of truth. Credentials live in `SourceConfig` as first-class fields. The config loader interpolates `${VAR}` before Pydantic validation.

```yaml
# pipelinekit.yaml
ingestion:
  source:
    type: postgres
    host: "${PG_HOST}"
    port: 5432
    database: "${PG_DATABASE}"
    user: "${PG_USER}"
    password: "${PG_PASSWORD}"
```

```python
# config/loader.py
raw = yaml.safe_load(f)
raw = _interpolate_env_vars(raw)   # expands ${VAR} before validation
config = PipelineConfig(**raw)
```

**The BYOK principle (ADR-005):**
- Customers provide all credentials via environment variables
- PipelineKit reads them through the config loader
- Credentials are never stored, logged, or transmitted
- API keys are never in code or committed files

**What goes in `.gitignore`:**
```
pipelinekit.yaml
*.duckdb
.dlt/
.env
```

---

## 11. The Quality System

Three quality layers. All deterministic. AI interprets — never replaces.

### Layer 1: Contracts (Pydantic + custom validators)

6 contract checks per table:
- Required columns
- Uniqueness
- Not-null
- Accepted values
- Row count range
- Freshness SLA

Contracts define truth. If a contract fails — the pipeline has failed, regardless of what the data looks like.

### Layer 2: Soda Quality Checks

YAML-defined checks run after transformation. Soda scans the destination table.

**Critical learning:** Soda's API changed between versions. `get_checks_pass_count()`, `get_checks_fail_count()`, `get_checks_warn_count()` were removed. Use `get_scan_results()` and count `outcome` fields. If tests mock removed methods — they are testing dead code, which is worse than no test.

### Layer 3: dbt Tests

Source tests in `sources.yml` run before model building. Model tests in `schema.yml` run after.

**dbt gotchas learned the hard way:**
- `sources.yml` must be inside `models/` — not in the project root or transform root
- `accepted_values` in dbt 1.12+ requires arguments wrapped under `arguments:` key
- Source database and schema must use `env_var()` — never hardcoded
- `profiles.yml` must have both `prod` and `local` targets with env-driven default

---

## 12. The Health System

`pipelinekit health` is the programmed sustainability policy (SPEC-012).

5 checks:

| Check | Command | What it does |
|---|---|---|
| deps | `pipelinekit health deps` | `poetry show --outdated` — categorizes patch/minor/major |
| security | `pipelinekit health security` | `pip-audit` — known CVEs |
| blueprints | `pipelinekit health blueprints` | Validates all installed blueprints |
| specs | `pipelinekit health specs` | Detects SPEC status header drift |
| tests | `pipelinekit health tests` | Reports last test run coverage |

Default: exits 0 even with warnings (non-blocking).
`--strict`: exits 1 on any warning.

**Run schedule (from Sustainability Policy v2):**
- Monthly: `pipelinekit health deps`, `pipelinekit health security`
- After every phase: `pipelinekit health specs`
- Before design partner demos: `pipelinekit health` (full)

---

## 13. The Test Strategy

**The iron rule:** No real API calls in tests. All external services are mocked.

**Coverage requirements:**
- Overall: ≥ 80%
- `src/pipelinekit/ai/`: ≥ 85%

**The READ ONLY guard:**
Existing test files are READ ONLY. When new tests are needed for new code alongside existing test files — create sibling files (`test_loader_interpolation.py` alongside `test_loader.py`). Never modify an existing test to accommodate new code.

**Exception:** When an existing test mocks a method that no longer exists in the real SDK (Soda API lesson) — updating the test is not just permitted, it is required. A test that mocks a dead API is false confidence, which is worse than no test.

**The mock pattern for AI providers:**

```python
from unittest.mock import patch, MagicMock

def test_diagnose_returns_valid_result(tmp_path):
    mock_provider = MagicMock()
    mock_provider.diagnose.return_value = DiagnosticResult(
        status="diagnosed",
        finding_type="contract_violation",
        confidence=0.91,
        evidence=[],
        recommended_actions=[],
    )
    engine = DiagnosticsEngine(config=mock_config, provider=mock_provider)
    result = engine.diagnose("run-123")
    assert result.status == "diagnosed"
    assert result.can_auto_fix is False
```

---

## 14. The Error System

Every error has a PK code. No bare exceptions. No free-form error strings.

Format: `PK-[AREA]-[NUMBER]`

Areas: CONFIG · CONTRACT · RUNTIME · ADAPTER · AI · STATE · BLUEPRINT · NOTIFY · HEALTH · ARCH · DIAG

**Key codes:**

| Code | Meaning | When you see it |
|---|---|---|
| PK-ADAPTER-001 | Source unreachable | Host not found, connection refused |
| PK-ADAPTER-002 | Adapter execution failed | dlt/dbt/Soda runtime error |
| PK-AI-001 | AI provider unavailable | Missing API key |
| PK-AI-002 | AI response failed schema validation | Hallucinated or malformed AI output |
| PK-CONFIG-006 | Credential field empty after interpolation | Env var not set |
| PK-CONTRACT-008 | Contract file invalid | Wrong YAML structure or wrong directory |

**Error class hierarchy:**

```python
PipelineKitError
├── ConfigurationError   PK-CONFIG-*
├── StateError           PK-STATE-*
├── RuntimeError         PK-RUNTIME-*
├── ContractError        PK-CONTRACT-*
├── BlueprintError       PK-BLUEPRINT-*
├── DiagnosticsError     PK-DIAG-*
├── LLMError             PK-AI-*
├── ArchitectureError    PK-ARCH-*
└── HealthError          PK-HEALTH-*
```

---

## 15. Architectural Smells — All 16

These are the pre-flight checks before every sprint. All must pass.

| # | Smell | Signal | Direction |
|---|---|---|---|
| 1 | Untraceable Feature | "Why does this exist?" has no answer | Trace to Constitution → ADR → SPEC or remove |
| 2 | Provider Leak | Provider SDK import outside adapter | Move to adapter file immediately |
| 3 | Agent Boundary Erosion | Agent modifies files it doesn't own | Strict READ ONLY enforcement |
| 4 | Spec Drift | Code and SPEC disagree | Update SPEC in same PR as code |
| 5 | Contract Version Gap | Contract changed without version bump | Version every breaking contract change |
| 6 | Prompt-Driven Architecture | Architecture from a prompt, not an ADR | Write the ADR first |
| 7 | MCP Without ADR | MCP added without governance decision | ADR before every MCP |
| 8 | Single-Implementation Abstraction | Interface with only one concrete implementation | Two implementations minimum |
| 9 | Placeholder Inflation | SPEC status "Draft" when phase is complete | Update status after every phase |
| 10 | Customer Capability Gap | Feature exists but customer can't use it | CLI command or it doesn't exist |
| 11 | Capability Creep | Feature doesn't improve TTTD | Reject it |
| 12 | Trust Regression | New feature reduces determinism | Never trade trust for convenience |
| 13 | Observer Becomes Actor | AI executes, not just recommends | `can_auto_fix/apply` always False |
| 14 | State Orphan | State written but never read | Read it or don't write it |
| 15 | Blueprint Shortcut | Blueprint missing one of 8 assets | All 8 required, no exceptions |
| 16 | Control Plane Inversion | Tool dictates to PipelineKit | PipelineKit coordinates, never defers |

---

## 16. The Decision Log

Key decisions and their reasoning — in the order they were made:

**typer `>=0.16,<1.0`** — click 8.4 broke `make_metavar()` in typer <0.16. Pin conservatively.

**`cwd: Path | None = None` pattern** — `Path.cwd()` as a default argument binds at import time, not at call time. Always use `None` and resolve inside the function.

**Feature branch per sprint** — fast-forward merge only after local verification. Never merge unverified code to main.

**mypy overrides for provider SDKs** — numpy PEP 695 syntax in newer numpy causes mypy to crash on Python 3.13 when processing type stubs. Override with `ignore_errors = True` for `dlt.*`, `soda.*`, `openai.*`, `anthropic.*`, `ollama.*`, `deepseek.*`, `mistralai.*`.

**AcceptedValuesRule as plain dict** — Pydantic v2 removed `__root__` model. Use plain dict for simple value wrappers.

**Intelligence layer not control plane** — after the dbt/Fivetran merger, "control plane" puts PipelineKit in the same mental bucket as Dagster, Kestra, and Prefect. "Intelligence layer" and "operating system" are broader and more accurate.

**TTTD dimensions as design principles** — five dimensions of Time-to-Trusted-Data are intent, not promised benchmarks. Numbers are earned from real usage, not asserted in documentation.

**Provider factory in `ai/providers/`** — when `adapters/factory.py` was READ ONLY during Phase 4, Claude Code correctly moved the provider factory to `ai/providers/__init__.py`. Documents win over prompts.

**ADR-017: PipelineKit owns credentials** — dlt's own config system (`DESTINATION__SNOWFLAKE__CREDENTIALS__*` env vars, `.dlt/secrets.toml`) creates two credential systems. Position A (PipelineKit owns config, dlt reads from PipelineConfig) is correct — one operating model, one config file.

**Blueprint #001 diagnostic run before design partners** — running against real infrastructure before any customer sees the product found: dlt scaffold returning `[]`, missing Soda API, wrong dbt source paths, column name mismatches. All fixed before any customer interaction.

---

## 17. Lessons Learned

### On scaffolding

Never ship a scaffold as production code. The dlt adapter was marked "Phase 2 placeholder" in its own docstring and shipped for 3 phases before the verification run caught it. Every piece of code that says "placeholder" or "TODO" is a landmine.

**Rule:** If it is a scaffold, it fails loudly. Return `NotImplementedError`, not `[]`.

### On mocking

Tests that mock removed methods are false confidence — worse than no test. When an SDK breaks its API, the tests still pass because they mock the old API. The first real run shows the breakage.

**Rule:** When upgrading a major SDK version, delete existing mocks and rebuild them against the new API.

### On dbt

dbt has strict file location requirements. `sources.yml` must be inside the model paths directory. `profiles.yml` default target must be env-driven for multi-target support. `accepted_values` tests changed syntax in dbt 1.12. Always run `dbt parse` after any schema or config change — it is faster than a full `dbt build`.

### On verification

The correct local testing sequence is:
1. Docker Postgres + DuckDB (no cloud credentials)
2. Cloud source (real Salesforce/Stripe) + DuckDB (no destination credentials)
3. Real source + real destination (full production path)

Never skip to step 3. Steps 1 and 2 find 90% of the issues.

### On schema/model alignment

When a JSON schema defines a field as `"type": "object"` but the Pydantic model uses `list[SomeModel]` — the schema is wrong. A list of structured items should be `"type": "array"`. The `adr_compliance` field in `architecture.schema.json` had this mismatch for one sprint before being caught.

### On the document chain

Documents that contradict each other are more dangerous than no documents. When SPEC-005 said `confidence_threshold` comes from config but the implementation used a module default — both were "correct" in different ways. Specification drift is a trust problem. Fix it in the same sprint it is found.

### On row counts

dlt reports "rows loaded" as the number of completed load jobs, not the number of data rows. Use `pipeline.last_trace.last_normalize_info.row_counts` and sum values for non-`_dlt_*` keys to get the actual data row count.

---

## 18. What Breaks and Why

**`pipelinekit validate` passes but `pipelinekit run` fails:**
The config is structurally valid but credentials are wrong or missing. `pipelinekit validate` only checks schema — it does not test connectivity. Use `pipelinekit run --dry-run` for connectivity validation.

**dbt parse fails with "source not found":**
Usually one of: `sources.yml` is not inside `models/`, the source name in the SQL doesn't match the name in `sources.yml`, or the database/schema env vars are not set.

**dlt loads 2 rows instead of 1000:**
dlt is in incremental mode and found 2 new rows since last run. Delete `.dlt/` directory and `*.duckdb` files, then re-run. Or set `write_disposition="replace"` in the pipeline run call.

**Soda scan crashes:**
The installed soda-core version changed its API. Check if `get_scan_results()` is available. If the test mocks `get_checks_pass_count()` — that method no longer exists.

**mypy fails on provider imports:**
The provider SDK uses Python 3.13 PEP 695 type syntax in its stubs. Add `[[tool.mypy.overrides]]` with `ignore_errors = true` for that package.

**`pipelinekit health specs` shows drift:**
A SPEC status header still shows "Approved" for an implemented SPEC. Run `pipelinekit health specs --fix` to auto-update, or manually update the `**Status:**` line.

**DuckDB and dbt see different files:**
dlt writes to its default DuckDB file (named after the pipeline). dbt reads from `DUCKDB_PATH`. If they don't point to the same file, dbt sees an empty database. The `_destination()` method in the dlt adapter must honor `destination.path` from config.

---

## 19. The Sprint Pattern

Every sprint follows this exact sequence:

```
Pre-sprint:
  1. Read current repo state (git log, pipelinekit health)
  2. Verify all 16 smells pass
  3. Write SPEC (if not already written)
  4. Write ADR (if architectural decision needed)
  5. Commit SPEC and ADR to main before sprint fires

Sprint execution:
  6. Write session opener (Message 1 for Claude Code)
  7. Write implementation prompt (Message 2 for Claude Code)
  8. Commit prompts to strategy-archive/
  9. Fire Message 1 to Claude Code — wait for N-point confirmation
  10. Fire Message 2 to Claude Code — let it build
  11. Receive output — run 8-step trio loop

Post-sprint:
  12. Confirm push hash
  13. Produce PROJECT-STATUS
  14. Commit PROJECT-STATUS
  15. State next action
```

**The confirmation gate (step 9):**

Claude Code must confirm understanding of the sprint before Message 2 is sent. The confirmation must be specific — not "I understand." It must name the exact files, the exact boundary, and the exact constraint that matters most for this sprint.

If the confirmation is vague — make it re-read the relevant document before proceeding.

---

## 20. Design Partner Readiness

**What must be true before the first design partner conversation:**

```
✅ Blueprint #001 verified locally (1,000 rows, 0.7 min)
✅ pipelinekit health runs green
✅ All 4 quality gates pass (pytest, ruff, black, mypy)
✅ CI green on GitHub
✅ Runbook has at least one verified deployment row

⏳ Blueprint #001 production Snowflake verification
⏳ Blueprint #002 (Salesforce → Snowflake) — expands ICP coverage
⏳ PK-CONFIG-006 wired into validate/run
```

**What a design partner demo looks like:**

```powershell
# 1. Initialize
pipelinekit init
pipelinekit validate

# 2. Deploy Blueprint #001
pipelinekit blueprint info postgres-to-snowflake
.\scripts\verify-blueprint-001.ps1 -Local

# 3. Show AI diagnostics
pipelinekit diagnose

# 4. Show architecture reasoning
pipelinekit architect analyze --type tool_selection

# 5. Show health
pipelinekit health
```

Total demo time: under 10 minutes. Every command works. Every output is structured and readable.

**The ICP model:**

| ICP | Who | Primary need | Blueprint |
|---|---|---|---|
| ICP-001 | Solo Founder | Fast, simple stack | Blueprint #003 (Stripe → Snowflake) |
| ICP-002 | Analytics Consultancy | Repeatability | Blueprint #001 or #002 |
| ICP-003 | Internal Data Team | Reliability at scale | Blueprint #001 |
| ICP-004 | Mixed-Stack Enterprise | Coherence above 3+ tools | Architecture Intelligence |

**The TTTD pitch:**

Every PipelineKit feature reduces Time-to-Trusted-Data on at least one dimension:
- Design speed → Blueprints
- Validation speed → `pipelinekit validate`
- Deployment safety → Contracts
- Diagnostic speed → `pipelinekit diagnose`
- Pipeline confidence → Quality checks

These are design principles backed by the Blueprint #001 verified run: 0.7 minutes from config to trusted data.

---

## Appendix A: Environment Setup

```powershell
# Prerequisites
# Python 3.13+, Poetry 2.4+, Docker Desktop, Git

# Clone and install
git clone https://github.com/emkwambe/pipelinekit
cd pipelinekit
poetry install

# Verify
poetry run pipelinekit --help
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80

# Local Blueprint #001 test
docker run --name pk-test -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=testdb -p 5432:5432 -d postgres:15
Start-Sleep 5
docker exec pk-test psql -U test -d testdb -c "
CREATE TABLE orders (order_id SERIAL PRIMARY KEY, customer_id INT, amount NUMERIC, status VARCHAR, created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW());
INSERT INTO orders (customer_id, amount, status) SELECT (random()*1000)::int, (random()*500)::numeric, (ARRAY['pending','processing','shipped','delivered','cancelled'])[floor(random()*5+1)] FROM generate_series(1,1000);"

$env:PG_HOST="localhost"; $env:PG_PORT="5432"; $env:PG_DATABASE="testdb"
$env:PG_USER="test"; $env:PG_PASSWORD="test"
$env:POSTGRES_CONN_STR="postgresql://test:test@localhost:5432/testdb"

.\scripts\verify-blueprint-001.ps1 -Local
```

---

## Appendix B: Adding a New Blueprint

1. Copy `blueprints/postgres-to-snowflake/` as a template
2. Write SPEC-0XX for the new blueprint
3. Create all 8 assets — verify with Smell 15 checklist
4. Add source type handling to `dlt/adapter.py`
5. Add SourceConfig fields for new source credentials
6. Add verification script `scripts/verify-blueprint-0XX.ps1`
7. Run `pipelinekit blueprint validate` — must exit 0
8. Write tests in `tests/blueprints/test_blueprint_0XX.py`
9. Run locally with `-Local` flag before any cloud verification
10. Record verified deployment in runbook before design partner outreach

---

## Appendix C: Key File Locations

| Artifact | Path |
|---|---|
| Governing principle | `docs/constitution/Product-Constitution.md` |
| All ADRs | `docs/decisions/` |
| All SPECs | `docs/specifications/` |
| Current state | `docs/reference/PROJECT-STATUS.md` |
| 16 Smells | `docs/reference/Architectural-Smells.md` |
| Sustainability Policy | `docs/reference/Sustainability-Policy.md` |
| Error codes | `docs/reference/Error-Codes.md` |
| Master Architecture | `docs/institutional-memory/strategy-archive/PIPELINEKIT-MASTER-ARCHITECTURE.md` |
| Phase 6 Sprint Plan | `docs/institutional-memory/strategy-archive/PHASE-6-SPRINT-PLAN.md` |
| New chat briefing | `docs/institutional-memory/strategy-archive/NEW-CHAT-PHASE-6-BRIEFING.md` |
| Diagnostic schema | `schemas/diagnostic.schema.json` |
| Architecture schema | `schemas/architecture.schema.json` |
| Blueprint schema | `schemas/blueprint.schema.json` |
