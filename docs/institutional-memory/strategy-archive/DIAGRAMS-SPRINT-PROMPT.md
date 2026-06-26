# PipelineKit — Diagrams Sprint
## Visual Documentation for All Audiences

---

## Your Identity

You are Claude Code operating as **documentation-engineer**.

This sprint produces diagrams only. No source files modified. No tests required.

---

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First

```
1. docs/reference/PROJECT-STATUS.md
2. docs/reference/ARCHITECTURE.md
3. docs/guides/CLI-REFERENCE.md
4. src/pipelinekit/cli/main.py              ← actual command surface
5. src/pipelinekit/ai/provider.py           ← AI layer
6. src/pipelinekit/blueprints/registry.py   ← blueprint system
7. src/pipelinekit/state/db.py              ← state tables
8. src/pipelinekit/core/errors.py           ← error taxonomy
```

---

## Output Location

All diagrams go in: `docs/diagrams/`  
Create the directory if it does not exist.  
Format: **Mermaid** (`.mmd` files) — renders natively in GitHub, Obsidian, and most docs platforms.  
Also produce one `README.md` in `docs/diagrams/` that describes each diagram and its audience.

---

## The 12 Diagrams Required

---

### DIAGRAM 1: System Overview (Investor / Executive)
**File:** `docs/diagrams/01-system-overview.mmd`  
**Audience:** Investors, executives, first-time evaluators  
**Purpose:** What is PipelineKit in one picture  
**Style:** High-level, no implementation detail, shows value not code

Must show:
- The three product layers: RealityDB (data) → PipelineKit (pipeline OS) → Analytics (output)
- The five AI capabilities (Diagnose, Architect, Propose, Migrate, Health)
- The three blueprint sources (hand-crafted, AI-proposed, registry-installed)
- The five AI providers (Anthropic, OpenAI, Ollama, DeepSeek, Mistral)
- The trust model in one phrase: "AI Proposes — Human Approves — Apply Writes"

---

### DIAGRAM 2: Five-Layer Architecture (Engineering)
**File:** `docs/diagrams/02-five-layer-architecture.mmd`  
**Audience:** Engineers evaluating PipelineKit, contributors  
**Purpose:** The complete technical architecture layer by layer

Must show all 5 layers with their key components:
```
Layer 5: Architecture Intelligence  → ArchitectureEngine, ADRReader
Layer 4: Intelligence Layer         → DiagnosticsEngine, EvidenceCollector, LLMProvider
Layer 3: Trust Layer                → BlueprintRegistry, NotificationDispatcher, CI
Layer 2: Data Layer                 → PipelineRunner, dlt adapter, dbt adapter, Soda adapter
Layer 1: Foundation                 → CLI, PipelineConfig, StateStore, ErrorHierarchy
```

Also show the cross-cutting concerns:
- State store (SQLite) accessed from all layers
- ADR document chain (Constitution → ADR → SPEC → Code)

---

### DIAGRAM 3: CLI Command Map (Engineering / Maintenance)
**File:** `docs/diagrams/03-cli-command-map.mmd`  
**Audience:** Engineers, maintainers, on-call engineers  
**Purpose:** Complete map of every CLI command, its flags, and what it calls internally

Must show every command from `src/pipelinekit/cli/main.py`:
```
pipelinekit
├── init
├── validate [--contracts]
├── run [--dry-run]
├── status
├── blueprint
│   ├── list
│   ├── validate
│   ├── info <name>
│   ├── search <query>
│   └── install <name> [--version] [--force]
├── generate
│   ├── blueprint --source --destination --tables [--plan|--interactive]
│   └── show <plan-id>
├── apply
│   └── plan <plan-id> [--interactive]
├── diagnose [run-id] [--provider] [--approve]
├── architect
│   ├── analyze [--type]
│   ├── check-adrs
│   └── compare
├── health [--strict]
│   ├── deps
│   ├── security
│   ├── blueprints
│   ├── specs
│   └── tests
└── migrate
    └── analyze <config> [--apply] [--write-draft]
```

For each command show: what it reads from state.db, what it writes to state.db, what external system it calls.

---

### DIAGRAM 4: Pipeline Execution Flow (Engineering)
**File:** `docs/diagrams/04-pipeline-execution-flow.mmd`  
**Audience:** Engineers debugging pipeline runs  
**Purpose:** Exact sequence of what happens during `pipelinekit run`

Must show the complete sequence:
1. Config loaded → PipelineConfig validated
2. State: run record created in pipeline_runs
3. Ingestion adapter (dlt) → source connection → rows loaded
4. State: rows_loaded updated
5. Transformation adapter (dbt) → dbt build
6. State: transformation result recorded
7. Quality adapter (Soda) → checks evaluated
8. State: quality result recorded
9. Contract validator → contract checks
10. State: contract results recorded
11. Notification dispatcher → alert if failure
12. State: final status updated
13. CLI renders result table

Show error paths: what happens when each step fails, which error code fires, which state tables are updated.

---

### DIAGRAM 5: AI Blueprint Proposal Flow (Engineering / Product)
**File:** `docs/diagrams/05-blueprint-proposal-flow.mmd`  
**Audience:** Engineers, product managers, design partners  
**Purpose:** The complete proposal lifecycle from command to applied blueprint

Must show:
```
User: pipelinekit generate blueprint --source stripe --destination snowflake --plan
  ↓
AdapterCapabilityRegistry.is_source_supported() → check
  ↓ (if unsupported: PK-GEN-006)
BlueprintProposer._build_context()
  → read existing blueprints (patterns)
  → read blueprint.schema.json
  → read SourceConfig fields
  ↓
LLMProvider.propose_blueprint(context)
  → PROPOSAL_SYSTEM_PROMPT
  → provider API call
  → parse_proposal_response() → strip fences, extract JSON
  ↓
Validate each asset (blueprint.json against schema)
  ↓
Attach provenance (9 fields) to each asset
Force can_auto_apply = False
Store in state.db (blueprint_proposals table)
  ↓
CLI renders: Plan ID, confidence, assumptions, required decisions
  ↓
User: pipelinekit generate blueprint --interactive OR pipelinekit apply plan <id>
  ↓
Per-asset review: [a]ccept [r]eject [e]dit [x]explain [y-all]
  ↓
pipelinekit apply plan <id>
  → Only APPROVED assets written
  → _strip_provenance() before write
  → AssetState: approved → written
  ↓
pipelinekit blueprint validate
  → AssetState: written → validated
```

Show the state machine: proposed → approved → written → validated  
Show what PK-GEN-001 through PK-GEN-007 mean at which step

---

### DIAGRAM 6: Migration Intelligence Flow (Engineering / Sales)
**File:** `docs/diagrams/06-migration-intelligence-flow.mmd`  
**Audience:** Engineers evaluating migration, sales conversations with Airbyte/Fivetran users  
**Purpose:** Show exactly how an existing pipeline config becomes a PipelineKit pipeline

Must show:
```
Existing config (airbyte-connection.json / fivetran-connector.json / pipeline.py)
  ↓
MigrationConfigParser.parse() → detect format
  → AirbyteParser / FivetranParser / PythonParser (ast.parse only — never exec)
  ↓
MigrationAnalyzer.analyze()
  → build migration context
  → LLMProvider.analyze_migration()
  → MigrationProposal: mappings + gaps + confidence + draft_yaml
  ↓
CLI renders: clean / partial / unsupported mappings + blocking gaps
  ↓
pipelinekit migrate analyze --apply
  → blocking_gaps > 0? → PK-MIGRATE-003 (use --write-draft)
  → pipelinekit.proposed.yaml written (NOT pipelinekit.yaml)
  ↓
Human fills FIXME markers
  ↓
pipelinekit validate → pipelinekit run
```

Show mapping status icons: ✓ clean / ⚠ partial / ✗ unsupported  
Show what each tool replaces: Airbyte → dlt, Fivetran → dlt, custom Python → dlt

---

### DIAGRAM 7: State Store Schema (Maintenance / Engineering)
**File:** `docs/diagrams/07-state-store-schema.mmd`  
**Audience:** Maintainers, engineers debugging state issues  
**Purpose:** Complete SQLite state store — all 8 tables, all columns, all relationships

Must show all 8 tables:
```
pipeline_runs          (id, status, started_at, completed_at, rows_loaded, ...)
validation_runs        (id, status, contracts_valid, dbt_valid, ...)
contract_results       (id, run_id FK, table_name, check_type, passed, ...)
diagnostic_results     (id, run_id FK, finding_type, confidence, ...)
architecture_results   (id, query_type, recommendation, confidence, ...)
health_runs            (id, check_type, status, details, ...)
blueprint_proposals    (plan_id, blueprint_name, source_type, assets JSON, ...)
installed_blueprints   (name PK, version, source, destination, verified, ...)
```

Show FK relationships between tables.  
Show which CLI commands read/write which tables.

---

### DIAGRAM 8: Error Code Taxonomy (Maintenance / On-Call)
**File:** `docs/diagrams/08-error-taxonomy.mmd`  
**Audience:** On-call engineers, support  
**Purpose:** Complete error hierarchy — where each error fires and what to do

Must show the error class hierarchy:
```
PipelineKitError
├── ConfigurationError   PK-CONFIG-001 to 006
├── StateError           PK-STATE-001 to 003
├── RuntimeError         PK-RUNTIME-001 to 004
├── ContractError        PK-CONTRACT-001 to 008
├── BlueprintError       PK-BLUEPRINT-001 to 005
├── DiagnosticsError     PK-DIAG-001 to 003
├── LLMError             PK-AI-001 to 002
├── ArchitectureError    PK-ARCH-001 to 003
├── HealthError          PK-HEALTH-001 to 003
├── RegistryError        PK-REGISTRY-001 to 005
├── ProposalError        PK-GEN-001 to 007
└── MigrationError       PK-MIGRATE-001 to 005
```

For each error area show: which command triggers it, what the user sees, what the fix is.

---

### DIAGRAM 9: Blueprint Catalog and Registry (Product / Engineering)
**File:** `docs/diagrams/09-blueprint-catalog-registry.mmd`  
**Audience:** Product, engineers, design partners  
**Purpose:** The blueprint ecosystem — local, registry, AI-proposed

Must show:
```
Blueprint Sources:
├── Hand-crafted (local)
│   ├── postgres-to-snowflake v1.0.0 ✅ locally verified
│   └── salesforce-to-snowflake v1.0.0 ✅ locally verified
├── AI-Proposed (BlueprintProposer)
│   └── stripe-to-snowflake v1.0.0 ✅ AI-proposed, human-approved
└── Registry (registry.pipelinekit.dev — pending deploy)
    ├── pipelinekit blueprint search <query>
    └── pipelinekit blueprint install <name>

Blueprint Structure (8 required assets):
├── blueprint.json
├── pipelinekit.example.yaml
├── ingestion/pipeline.py (dlt)
├── transform/ (dbt project)
├── contracts/*.yaml
├── quality/checks.yaml
├── alerts/config.yaml
└── docs/runbook.md

Verification states:
proposed → approved → written → validated → locally verified → production verified
```

---

### DIAGRAM 10: AI Provider Architecture (Engineering / Investor)
**File:** `docs/diagrams/10-ai-provider-architecture.mmd`  
**Audience:** Engineers, investors evaluating AI strategy  
**Purpose:** How PipelineKit's AI layer works — provider diversity, trust model, evidence architecture

Must show:
```
PipelineKit AI Layer
        ↓
LLMProvider Protocol (interface)
        ↓
┌─────────────────────────────────────────┐
│ Provider implementations                │
├──────────────┬──────────────────────────┤
│ Anthropic    │ US Cloud                 │
│ OpenAI       │ US Cloud                 │
│ Ollama       │ Local / Air-gapped       │
│ DeepSeek     │ China / Cost-sensitive   │
│ Mistral      │ EU / GDPR-compliant      │
└──────────────┴──────────────────────────┘
        ↓
Three AI capabilities:
├── diagnose() → DiagnosticResult (can_auto_fix: always False)
├── architect() → ArchitectureResult (can_auto_apply: always False)
└── propose_blueprint() → BlueprintProposal (can_auto_apply: always False)

Evidence flow:
StateDB → EvidenceCollector → EvidencePackage → LLMProvider → validated against schema
                                                              → CLI renders

Trust boundary (immutable):
AI proposes — human approves — apply() writes
can_auto_fix / can_auto_apply / can_auto_execute = always False
```

---

### DIAGRAM 11: The Product Ecosystem (Investor / Strategic)
**File:** `docs/diagrams/11-product-ecosystem.mmd`  
**Audience:** Investors, strategic partners, Mpingo Systems overview  
**Purpose:** How PipelineKit fits in the broader Mpingo Systems product portfolio

Must show:
```
Mpingo Systems Product Ecosystem

RealityDB Platform
├── RealityDB Core (CLI v2.38.0)
├── SimLab (interactive simulation)
├── Sandbox (9 templates, 32K-50K rows each)
└── SafeSQL Pro (SQL validation, safesqlpro.dev)

PipelineKit (this product)
├── Blueprint Catalog (3 blueprints)
├── AI Layer (5 providers, 3 capabilities)
├── Registry (registry.pipelinekit.dev)
└── Migration Intelligence (Airbyte/Fivetran/Python)

Education Products
├── MathAthlone (competitive math, Chess.com for math)
├── MathPivot (AI math tutoring)
├── SQL Learn (SQL education platform)
└── Atelier (Decision Intelligence Measurement System)

The integration:
RealityDB → generates synthetic enterprise data
PipelineKit → runs trusted pipelines on that data
PipelineKit Academy → trains engineers using both
```

---

### DIAGRAM 12: Future Architecture — MCP Integration (Future Engineering)
**File:** `docs/diagrams/12-future-mcp-architecture.mmd`  
**Audience:** Future engineers, strategic planning  
**Purpose:** What PipelineKit looks like with MCP integrated (ADR-021, not yet built)

Must show:
```
Current:
User → CLI → PipelineKit

Future Role 1: PipelineKit AS MCP Server
Claude Desktop / Cursor / Any MCP client
        ↓ MCP protocol
PipelineKit MCP Server
  tools: [validate, diagnose, health, blueprint_info, migrate_analyze, propose]
        ↓
Same PipelineKit internals

Future Role 2: MCP for Schema Discovery
BlueprintProposer
        ↓ MCP call
Source MCP Server (Salesforce MCP, Stripe MCP, etc.)
  → actual schema, real column names
        ↓
Confidence: 0.82 → 0.95+

Future Role 3: MCP for Alerts
NotificationDispatcher
        ↓ MCP call
Slack MCP / PagerDuty MCP / Teams MCP

Trust model unchanged:
MCP tools are read/propose only
Write/execute requires human confirmation
ADR-007 boundary holds regardless of interface
```

Label clearly: CURRENT STATE vs FUTURE STATE (ADR-021, not yet built)

---

## Diagram README

**File:** `docs/diagrams/README.md`

```markdown
# PipelineKit Diagrams

All diagrams are Mermaid format (.mmd). They render automatically in GitHub.

| File | Title | Audience | Use case |
|---|---|---|---|
| 01-system-overview | System Overview | Investors, Executives | First conversation |
| 02-five-layer-architecture | Five-Layer Architecture | Engineers | Technical evaluation |
| 03-cli-command-map | CLI Command Map | Maintainers | Day-to-day operations |
| 04-pipeline-execution-flow | Pipeline Execution Flow | Engineers | Debugging runs |
| 05-blueprint-proposal-flow | Blueprint Proposal Flow | Engineers, Product | AI feature explanation |
| 06-migration-intelligence-flow | Migration Intelligence | Engineers, Sales | ICP-004 conversations |
| 07-state-store-schema | State Store Schema | Maintainers | Database debugging |
| 08-error-taxonomy | Error Code Taxonomy | On-call Engineers | Incident response |
| 09-blueprint-catalog-registry | Blueprint Catalog | Product, Partners | Catalog overview |
| 10-ai-provider-architecture | AI Provider Architecture | Engineers, Investors | AI strategy |
| 11-product-ecosystem | Product Ecosystem | Investors | Portfolio overview |
| 12-future-mcp-architecture | Future MCP Architecture | Future Engineers | Roadmap planning |
```

---

## Quality Requirements

- Every diagram must be valid Mermaid syntax — verify it renders before committing
- Every diagram must accurately reflect the current codebase — no invented features
- Diagram 12 must clearly label what is CURRENT vs FUTURE
- No placeholder nodes — every box must represent something real
- Error codes must match `docs/reference/Error-Codes.md` exactly
- CLI commands must match `src/pipelinekit/cli/main.py` exactly
- State tables must match `src/pipelinekit/state/db.py` exactly

---

## Files You Must Not Modify

```
src/                              ← READ ONLY
docs/reference/PROJECT-STATUS.md  ← READ ONLY
All existing docs/                ← READ ONLY (you only CREATE new files in docs/diagrams/)
```

---

## Commit Message

```
docs: 12 Mermaid diagrams covering all audiences and use cases

- 01: System overview (investor/executive)
- 02: Five-layer architecture (engineering)
- 03: CLI command map (maintenance)
- 04: Pipeline execution flow (debugging)
- 05: Blueprint proposal flow (AI feature)
- 06: Migration intelligence flow (sales/ICP-004)
- 07: State store schema (database maintenance)
- 08: Error code taxonomy (on-call)
- 09: Blueprint catalog and registry (product)
- 10: AI provider architecture (engineering/investor)
- 11: Product ecosystem (investor/strategic)
- 12: Future MCP architecture (roadmap)

All verified against src/ — no invented features.
Diagram 12 clearly labeled CURRENT vs FUTURE.
```
