# SPEC-011-Architecture-Intelligence.md

**Status:** Approved  
**Owner:** diagnostics-engineer  
**Phase:** 5 — Architecture Layer  
**Date:** June 25, 2026  
**ADRs:** ADR-007 (AI is Operator not Owner), ADR-014 (AI Provider MCP Layer), ADR-015 (Architecture Intelligence Scope), ADR-005 (BYOK)  
**Schemas:** schemas/diagnostic.schema.json, schemas/blueprint.schema.json  
**Depends on:** SPEC-005 (AI Diagnostics), SPEC-006 (Blueprint Engine), SPEC-003 (Runtime)  
**Extends:** LLMProvider Protocol (provider.py), DiagnosticsEngine (diagnostics.py)

---

## Purpose

Define Architecture Intelligence — the Phase 5 capability that answers the question Phase 4 cannot:

> **Phase 4:** "Why did this pipeline fail?"  
> **Phase 5:** "What architecture should this pipeline use?"

Architecture Intelligence is not pipeline generation. It is architectural reasoning — helping teams make better decisions about tool selection, stack design, cost tradeoffs, and ADR compliance before pipelines are built or changed.

No one currently owns this decision layer. PipelineKit is positioned to own it because it already sits above every provider, already has contracts and schemas that define truth, and already has structured diagnostic evidence from Phase 4.

---

## Governing Rules

All Phase 4 AI rules apply and are extended:

- Architecture recommendations are advisory — never auto-applied
- Every recommendation traces to evidence (cost data, ADR constraints, blueprint patterns)
- AI interprets — AI never defines architectural truth
- Provider-specific code stays in `ai/providers/`
- All AI output validates against `schemas/architecture.schema.json` (new schema)
- Human approval required before any architectural change is executed
- `can_auto_fix` remains False — Phase 5 introduces `can_auto_apply` which is also False

---

## What Architecture Intelligence Covers

### Five Reasoning Capabilities

**1. Tool Selection Reasoning**
> "Should this pipeline use dbt or SQLMesh for transformation?"
> "Should this use Fivetran or dlt given licensing and operational constraints?"
> "Should this workload run in DuckDB or Snowflake given cost and volume?"

**2. Cost Architecture Comparison**
> "What is the cheapest reliable architecture for 500M rows/day?"
> "What would switching from Snowflake to DuckDB save per month?"

**3. ADR Compliance Checking**
> "Will this proposed change violate any of our existing ADRs?"
> "Does this blueprint satisfy the deterministic-before-AI principle?"

**4. Stack Evolution Recommendations**
> "What changed in our data landscape since last month that affects our architecture?"
> "We're growing from 10M to 100M rows/day — what needs to change?"

**5. Blueprint Selection and Comparison**
> "Which blueprint best fits our source/destination combination?"
> "What would we need to change to use the Stripe→Snowflake blueprint?"

---

## New Schema — architecture.schema.json

Phase 5 requires a new schema alongside the existing `diagnostic.schema.json`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PipelineKit Architecture Recommendation",
  "type": "object",
  "required": ["reasoning_type", "confidence", "current_state", "recommendation", "tradeoffs", "evidence", "adr_compliance"],
  "properties": {
    "reasoning_type": {
      "type": "string",
      "enum": ["tool_selection", "cost_optimization", "adr_compliance", "stack_evolution", "blueprint_selection"]
    },
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "current_state": {"type": "object"},
    "recommendation": {"type": "object"},
    "tradeoffs": {"type": "array"},
    "evidence": {"type": "array"},
    "adr_compliance": {"type": "object"},
    "can_auto_apply": {"type": "boolean", "default": false},
    "estimated_impact": {"type": "object"}
  }
}
```

---

## ArchitectureResult Model

Extends the Phase 4 pattern. New model alongside `DiagnosticResult`.

```python
# src/pipelinekit/ai/arch_models.py

from pydantic import BaseModel, Field
from typing import Optional

class ArchitectureTradeoff(BaseModel):
    dimension: str          # "cost" | "reliability" | "complexity" | "vendor_lock"
    current: str
    proposed: str
    direction: str          # "better" | "worse" | "neutral"
    evidence: str

class ADRComplianceCheck(BaseModel):
    adr_id: str             # "ADR-004", "ADR-007" etc.
    compliant: bool
    note: str

class ArchitectureRecommendation(BaseModel):
    action: str
    tool_from: Optional[str] = None
    tool_to: Optional[str] = None
    rationale: str
    effort: str = "medium"   # low | medium | high
    reversible: bool = True
    requires_approval: bool = True  # always True in Phase 5

class ArchitectureResult(BaseModel):
    reasoning_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    current_state: dict
    recommendation: ArchitectureRecommendation
    tradeoffs: list[ArchitectureTradeoff] = []
    evidence: list[dict] = []
    adr_compliance: list[ADRComplianceCheck] = []
    can_auto_apply: bool = False    # always False in Phase 5
    estimated_impact: dict = {}
    explanation: str = ""
```

---

## ArchitectureContext — Evidence for Architecture Reasoning

Architecture reasoning needs different evidence than pipeline diagnostics.

```python
# src/pipelinekit/ai/arch_evidence.py

@dataclass
class ArchitectureContext:
    config: dict                   # full pipelinekit.yaml
    blueprint_metadata: dict       # installed blueprints from registry
    adr_summaries: list[dict]      # parsed from docs/decisions/
    run_history: list[dict]        # last 30 runs — pattern data
    contract_violations: list[dict] # last 30 days
    current_tools: dict            # source, destination, transform, quality
    volume_profile: dict           # rows/day, growth rate from state.db
    diagnostic_history: list[dict] # Phase 4 results — what keeps failing
```

---

## ArchitectureEngine

Extends the DiagnosticsEngine pattern for architectural reasoning.

```python
# src/pipelinekit/ai/arch_engine.py

class ArchitectureEngine:
    """Orchestrates context collection → AI architectural reasoning → validation.

    Same trust boundary as DiagnosticsEngine:
    - Context is read-only
    - Output validated against architecture.schema.json
    - can_auto_apply always False
    - Recommendations presented to human — never executed
    """

    def __init__(self, config: PipelineConfig, provider: LLMProvider):
        self.config = config
        self.provider = provider

    def analyze(
        self,
        reasoning_type: str,
        question: str | None = None,
        cwd: Path | None = None,
    ) -> ArchitectureResult:
        """
        Full architectural reasoning cycle:
        1. Collect ArchitectureContext
        2. Call provider.architect(context, reasoning_type, question)
        3. Validate against architecture.schema.json
        4. Store result in state.db
        5. Return ArchitectureResult
        Never applies recommendations.
        """
        ...
```

---

## LLMProvider Extension

Add `architect` method to the `LLMProvider` Protocol:

```python
# src/pipelinekit/ai/provider.py — extend existing Protocol

class LLMProvider(Protocol):
    # ... existing methods ...

    def architect(
        self,
        context: "ArchitectureContext",
        reasoning_type: str,
        question: str | None = None,
    ) -> "ArchitectureResult":
        """
        Perform architectural reasoning from context.
        Output must validate against schemas/architecture.schema.json.
        Raises LLMError(PK-AI-001) if provider unavailable.
        Raises LLMError(PK-AI-002) if response fails schema validation.
        """
        ...
```

---

## pipelinekit architect Command

New top-level command — the entry point for Architecture Intelligence.

```python
# src/pipelinekit/cli/architect.py

architect_app = typer.Typer(
    name="architect",
    help="AI-native architecture reasoning for your analytics stack.",
    no_args_is_help=True,
)

@architect_app.command("analyze")
def analyze_command(
    question: str = typer.Argument(
        None,
        help="Natural language architecture question."
    ),
    type_: str = typer.Option(
        "tool_selection", "--type", "-t",
        help="Reasoning type: tool_selection | cost_optimization | adr_compliance | stack_evolution | blueprint_selection"
    ),
    provider: str = typer.Option(None, "--provider", "-p"),
    approve: bool = typer.Option(False, "--approve"),
):
    """Analyze your analytics architecture and get AI-powered recommendations."""

@architect_app.command("check-adrs")
def check_adrs_command(
    change: str = typer.Argument(..., help="Proposed change to check."),
):
    """Check whether a proposed change complies with your ADRs."""

@architect_app.command("compare")
def compare_command(
    tool_a: str = typer.Argument(...),
    tool_b: str = typer.Argument(...),
):
    """Compare two tools for your specific stack and data profile."""
```

### Output format — analyze:

```
Analyzing architecture...

✓ Context collected — 30 runs, 2 blueprints, 12 ADRs

Reasoning type:  tool_selection
Confidence:      0.87
Status:          recommendation

Recommendation:
  Switch transformation layer from dbt to SQLMesh

Rationale:
  Your pipeline runs 400M rows/day with 3 failed dbt incremental runs
  in the past 2 weeks (PK-ADAPTER-002). SQLMesh's native incremental
  model handling and built-in column-level lineage would reduce these
  failures and improve debugging time by an estimated 40%.

Tradeoffs:
  Cost:        neutral (SQLMesh is Apache 2.0, same as dbt-core)
  Reliability: better (native incremental, fewer timeout patterns)
  Complexity:  medium (migration effort ~2 weeks)
  Vendor lock: better (SQLMesh has no cloud platform dependency)

ADR compliance:
  ADR-001 (Apache 2.0 preference):  ✓ compliant
  ADR-008 (Deterministic first):    ✓ compliant
  ADR-004 (Local-first):            ✓ compliant

Run 'pipelinekit architect analyze --approve' to review and record decision.
```

---

## ADR Parsing

Phase 5 reads ADRs from `docs/decisions/` to power compliance checking.

```python
# src/pipelinekit/ai/adr_reader.py

class ADRReader:
    """Reads and parses ADR files for architectural compliance checking.

    Reads from docs/decisions/ — never modifies ADR files.
    Returns structured summaries suitable for LLM context.
    """

    def __init__(self, decisions_dir: Path):
        self.decisions_dir = decisions_dir

    def read_all(self) -> list[dict]:
        """Return structured summaries of all ADRs."""
        ...

    def check_compliance(
        self,
        proposed_change: str,
        adrs: list[dict]
    ) -> list[ADRComplianceCheck]:
        """Check a proposed change against ADR constraints."""
        ...
```

---

## State Extension

Add `architecture_results` table:

```sql
CREATE TABLE IF NOT EXISTS architecture_results (
    id              TEXT PRIMARY KEY,
    reasoning_type  TEXT NOT NULL,
    question        TEXT,
    confidence      REAL NOT NULL,
    recommendation  TEXT,     -- JSON
    tradeoffs       TEXT,     -- JSON array
    adr_compliance  TEXT,     -- JSON array
    can_auto_apply  INTEGER DEFAULT 0,
    analyzed_at     TEXT NOT NULL,
    provider        TEXT
);
```

---

## Error Codes — Phase 5

| Code | Meaning |
|---|---|
| `PK-ARCH-001` | Architecture context collection failed |
| `PK-ARCH-002` | Architecture result failed schema validation |
| `PK-ARCH-003` | ADR parsing failed |
| `PK-ARCH-004` | Insufficient run history for analysis (< 5 runs) |

Add `ArchitectureError` to `core/errors.py`.

---

## File Structure

```
src/pipelinekit/
└── ai/
    ├── (existing Phase 4 files — unchanged)
    ├── arch_models.py      ArchitectureResult, ArchitectureRecommendation,
    │                       ArchitectureTradeoff, ADRComplianceCheck
    ├── arch_evidence.py    ArchitectureContext, ArchitectureContextCollector
    ├── arch_engine.py      ArchitectureEngine
    └── adr_reader.py       ADRReader

src/pipelinekit/cli/
└── architect.py            architect analyze, check-adrs, compare

schemas/
└── architecture.schema.json   New schema

tests/
└── ai/
    ├── test_arch_models.py
    ├── test_arch_evidence.py
    ├── test_arch_engine.py
    └── test_adr_reader.py
```

---

## pyproject.toml — Phase 5 Additions

No new provider dependencies. All three providers (OpenAI, Anthropic, Ollama) already implement the extended `LLMProvider` Protocol by adding the `architect` method.

Potential addition:
```toml
markdown = "^3.5"   # for ADR parsing if needed
```

---

## Constraints

- `can_auto_apply` always False in Phase 5
- ADR files are read-only — `ADRReader` never writes
- Architecture context is read-only — never modifies state except to record results
- All output validates against `schemas/architecture.schema.json`
- Phase 4 `DiagnosticResult` and `DiagnosticsEngine` unchanged
- No new providers — extend existing three
- `pipelinekit diagnose` unchanged — Phase 4 command intact

---

## Acceptance Criteria

```
✓ pipelinekit architect analyze exits 0 with ArchitectureResult
✓ pipelinekit architect check-adrs exits 0 with compliance report
✓ pipelinekit architect compare exits 0 with comparison result
✓ All ArchitectureResult validates against architecture.schema.json
✓ can_auto_apply always False — no auto-application path exists
✓ ADRReader reads and parses all docs/decisions/ files
✓ Architecture results stored in state.db
✓ All Phase 1-4 tests still pass
✓ coverage >= 80% overall, >= 85% on src/pipelinekit/ai/
✓ ruff, black, mypy all clean
✓ No API keys in any file
✓ PROJECT-STATUS.md untouched
```

---

## Out of Scope

- `can_auto_apply = True` — requires ADR-016 and reversibility mechanism
- `pipelinekit apply` auto-application command — future phase
- Blueprint generation from scratch — future phase
- Model fine-tuning on customer data — future phase
- Remote blueprint registry — future phase
