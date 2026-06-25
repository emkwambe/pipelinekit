# PipelineKit — Phase 5 Claude Code Implementation Prompt
## Architecture Layer Sprint: Architecture Intelligence + pipelinekit architect

---

## Your Identity

You are Claude Code operating as the **PipelineKit Diagnostics Engineer** (extended scope) and **Quality Engineer**.

Same agent as Phase 4. Phase 5 extends the AI layer you built — it does not introduce a new agent.

Your primary SPEC: `docs/specifications/SPEC-011-Architecture-Intelligence.md`  
Your governing ADR: `docs/decisions/ADR-015-Architecture-Intelligence.md`

---

## Repository

```
Local path: C:\Users\HP\Documents\pipelinekit
GitHub:     https://github.com/emkwambe/pipelinekit
```

---

## Read First — In This Exact Order

```
1.  .claude/CLAUDE.md
2.  docs/constitution/Product-Constitution.md
3.  docs/decisions/ADR-015-Architecture-Intelligence.md    ← Primary ADR
4.  docs/decisions/ADR-007-* (AI is Operator not Owner)
5.  docs/decisions/ADR-014-AI-Provider-MCP-Layer.md
6.  docs/specifications/SPEC-011-Architecture-Intelligence.md  ← Primary SPEC
7.  docs/specifications/SPEC-005-AI-Diagnostics.md         ← Phase 4 pattern to follow
8.  docs/reference/Architectural-Smells.md                 ← Especially Smell 13 + 16
9.  docs/reference/PROJECT-STATUS.md
10. docs/reference/Error-Codes.md
11. schemas/diagnostic.schema.json                         ← Pattern for new schema
12. schemas/blueprint.schema.json                          ← Context you will read
13. src/pipelinekit/ai/provider.py                         ← You extend this
14. src/pipelinekit/ai/diagnostics.py                      ← Pattern to follow
15. src/pipelinekit/ai/models.py                           ← Pattern to follow
16. src/pipelinekit/ai/evidence.py                         ← Pattern to follow
17. src/pipelinekit/state/db.py                            ← You add one table
18. src/pipelinekit/core/errors.py                         ← You add one class
19. src/pipelinekit/adapters/base.py                       ← READ ONLY pattern
20. docs/decisions/                                        ← ADR files ArchitectureEngine reads
```

---

## Sprint Goal

Deliver Phase 5 such that all of the following work:

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry run pipelinekit architect --help
poetry run pipelinekit architect analyze --help
poetry run pipelinekit architect check-adrs --help
poetry run pipelinekit architect compare --help
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

**Plus** — all 151 Phase 1–4 tests must still pass.
**Plus** — CI must remain green on GitHub.

---

## Files You Are Allowed To Create

```
schemas/
└── architecture.schema.json       New output schema for architectural reasoning

src/pipelinekit/
└── ai/
    ├── arch_models.py             ArchitectureResult, ArchitectureRecommendation,
    │                              ArchitectureTradeoff, ADRComplianceCheck
    ├── arch_evidence.py           ArchitectureContext, ArchitectureContextCollector
    ├── arch_engine.py             ArchitectureEngine
    └── adr_reader.py              ADRReader

src/pipelinekit/cli/
└── architect.py                   architect analyze, check-adrs, compare

tests/
└── ai/
    ├── test_arch_models.py
    ├── test_arch_evidence.py
    ├── test_arch_engine.py
    └── test_adr_reader.py
```

You may also modify:
```
src/pipelinekit/ai/provider.py     Add architect() method to LLMProvider Protocol only
src/pipelinekit/ai/providers/openai.py     Implement architect() method only
src/pipelinekit/ai/providers/anthropic.py  Implement architect() method only
src/pipelinekit/ai/providers/ollama.py     Implement architect() method only
src/pipelinekit/cli/main.py        Register architect command group only
src/pipelinekit/state/db.py        Add architecture_results table + insert function only
src/pipelinekit/core/errors.py     Add ArchitectureError only
docs/reference/Error-Codes.md      Add Phase 5 codes only
pyproject.toml                     Add markdown dependency if needed for ADR parsing
```

---

## Files You Must Not Modify

```
docs/                                    ← READ ONLY (except Error-Codes.md above)
docs/reference/PROJECT-STATUS.md        ← NEVER TOUCH — Command Center owns this
docs/decisions/                          ← READ ONLY — ADRReader reads, never writes
schemas/diagnostic.schema.json          ← READ ONLY — Phase 4 schema unchanged
contracts/                               ← READ ONLY
agents/                                  ← READ ONLY
.claude/                                 ← READ ONLY
.github/                                 ← READ ONLY
.mcp/                                    ← READ ONLY
src/pipelinekit/config/                  ← READ ONLY
src/pipelinekit/runtime/                 ← READ ONLY
src/pipelinekit/adapters/               ← READ ONLY
src/pipelinekit/contracts/              ← READ ONLY
src/pipelinekit/blueprints/             ← READ ONLY
src/pipelinekit/notifications/          ← READ ONLY
src/pipelinekit/ai/diagnostics.py       ← READ ONLY (Phase 4 — do not change)
src/pipelinekit/ai/evidence.py          ← READ ONLY (Phase 4 — do not change)
src/pipelinekit/ai/models.py            ← READ ONLY (Phase 4 — do not change)
src/pipelinekit/cli/diagnose.py         ← READ ONLY
src/pipelinekit/cli/init.py             ← READ ONLY
src/pipelinekit/cli/validate.py         ← READ ONLY
src/pipelinekit/cli/status.py           ← READ ONLY
src/pipelinekit/cli/run.py              ← READ ONLY
src/pipelinekit/cli/blueprint.py        ← READ ONLY
tests/cli/                              ← READ ONLY
tests/config/                           ← READ ONLY
tests/state/                            ← READ ONLY
tests/runtime/                          ← READ ONLY
tests/adapters/                         ← READ ONLY
tests/contracts/                        ← READ ONLY
tests/blueprints/                       ← READ ONLY
tests/notifications/                    ← READ ONLY
tests/ai/test_diagnostics.py            ← READ ONLY
tests/ai/test_evidence.py               ← READ ONLY
tests/ai/test_models.py                 ← READ ONLY
tests/ai/providers/                     ← READ ONLY (add architect tests alongside)
```

---

## schemas/architecture.schema.json — Exact Spec

Create this file exactly. It governs all Phase 5 AI output.

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

## Implementation Requirements

### 1. src/pipelinekit/core/errors.py — Add One Class Only

```python
class ArchitectureError(PipelineKitError):
    """Raised when architecture context collection or reasoning fails."""
```

---

### 2. src/pipelinekit/ai/arch_models.py

```python
class ArchitectureTradeoff(BaseModel):
    dimension: str        # cost | reliability | complexity | vendor_lock | maintainability
    current: str
    proposed: str
    direction: str        # better | worse | neutral
    evidence: str

class ADRComplianceCheck(BaseModel):
    adr_id: str           # "ADR-004", "ADR-007" etc.
    compliant: bool
    note: str

class ArchitectureRecommendation(BaseModel):
    action: str
    tool_from: Optional[str] = None
    tool_to: Optional[str] = None
    rationale: str
    effort: str = "medium"    # low | medium | high
    reversible: bool = True
    requires_approval: bool = True

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

### 3. src/pipelinekit/ai/adr_reader.py

```python
class ADRReader:
    """Reads ADR files from docs/decisions/ for compliance checking.
    Read-only — never writes, creates, or deletes ADR files.
    Parsing failures produce PK-ARCH-003 — never crash silently.
    """

    def __init__(self, decisions_dir: Path):
        self.decisions_dir = decisions_dir

    def read_all(self) -> list[dict]:
        """Return structured summaries of all ADR markdown files."""
        ...

    def get_adr_summaries(self) -> list[dict]:
        """Return concise summaries suitable for LLM context window."""
        ...
```

Parse each ADR file for: ADR number, title, status, decision summary, principle alignment.
Malformed files → skip with warning, do not raise.
Missing `docs/decisions/` → return empty list, do not raise.

---

### 4. src/pipelinekit/ai/arch_evidence.py

```python
@dataclass
class ArchitectureContext:
    config: dict
    blueprint_metadata: list[dict]
    adr_summaries: list[dict]
    run_history: list[dict]          # last 30 runs
    contract_violations: list[dict]  # last 30 days
    current_tools: dict              # source, dest, transform, quality
    volume_profile: dict             # rows/day estimate from run history
    diagnostic_history: list[dict]   # Phase 4 results

class ArchitectureContextCollector:
    def collect(self, cwd: Path | None = None) -> ArchitectureContext:
        """
        Assemble ArchitectureContext from state.db, config, blueprints, ADRs.
        Read-only — never writes to state.db.
        Raises ArchitectureError(PK-ARCH-001) on collection failure.
        Raises ArchitectureError(PK-ARCH-004) if < 5 runs in history.
        """
        ...
```

---

### 5. src/pipelinekit/ai/provider.py — Add architect() Only

Add one method to the existing `LLMProvider` Protocol. Do not change existing methods.

```python
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

### 6. Each Provider — Add architect() Implementation

For `openai.py`, `anthropic.py`, `ollama.py` — add `architect()` alongside existing methods.

**Prompt pattern for all providers:**

```python
ARCH_SYSTEM_PROMPT = """You are a senior data architecture advisor for PipelineKit.
Analyze the provided architecture context and return a JSON recommendation.
Your response must be valid JSON matching this schema:
{
  "reasoning_type": "tool_selection|cost_optimization|adr_compliance|stack_evolution|blueprint_selection",
  "confidence": 0.0-1.0,
  "current_state": {"description": "...", "tools": {}},
  "recommendation": {
    "action": "...",
    "tool_from": "...",
    "tool_to": "...",
    "rationale": "...",
    "effort": "low|medium|high",
    "reversible": true,
    "requires_approval": true
  },
  "tradeoffs": [{"dimension": "...", "current": "...", "proposed": "...", "direction": "better|worse|neutral", "evidence": "..."}],
  "evidence": [{"type": "...", "detail": "..."}],
  "adr_compliance": {"checked": [], "violations": [], "compliant": []},
  "can_auto_apply": false,
  "estimated_impact": {},
  "explanation": "Human-readable reasoning"
}
Never invent evidence. Only use what is provided.
can_auto_apply must always be false.
Base recommendations on the specific data profile, not generic best practices."""
```

---

### 7. src/pipelinekit/ai/arch_engine.py

```python
class ArchitectureEngine:
    """Orchestrates context → AI architectural reasoning → validation → storage.

    Same trust boundary as DiagnosticsEngine:
    - Context read-only
    - Output validated against architecture.schema.json
    - can_auto_apply always False — engine corrects any True returned by provider
    - Recommendations presented to human — never executed
    ADR-015, ADR-007, Smell 13, Smell 16.
    """

    def __init__(self, config: PipelineConfig, provider: LLMProvider):
        self.config = config
        self.provider = provider
        self.collector = ArchitectureContextCollector()

    def analyze(
        self,
        reasoning_type: str,
        question: str | None = None,
        cwd: Path | None = None,
    ) -> ArchitectureResult:
        """
        1. Collect ArchitectureContext
        2. Call provider.architect(context, reasoning_type, question)
        3. Validate against architecture.schema.json
        4. Force can_auto_apply = False
        5. Store in state.db
        6. Return ArchitectureResult
        """
        ...

    def _validate_against_schema(self, result: ArchitectureResult) -> None:
        """Raises LLMError(PK-AI-002) on schema violation."""
        ...
```

---

### 8. src/pipelinekit/state/db.py — Addition Only

Add to `_SCHEMA`:

```sql
CREATE TABLE IF NOT EXISTS architecture_results (
    id              TEXT PRIMARY KEY,
    reasoning_type  TEXT NOT NULL,
    question        TEXT,
    confidence      REAL NOT NULL,
    recommendation  TEXT,
    tradeoffs       TEXT,
    adr_compliance  TEXT,
    can_auto_apply  INTEGER DEFAULT 0,
    analyzed_at     TEXT NOT NULL,
    provider        TEXT
);
```

Add one function:

```python
def insert_architecture_result(
    reasoning_type: str,
    result: dict,
    provider: str,
    question: str | None = None,
    cwd: Path | None = None,
) -> None:
    """Store architecture result. Called by ArchitectureEngine only."""
```

---

### 9. src/pipelinekit/cli/architect.py

```python
architect_app = typer.Typer(
    name="architect",
    help="AI-native architecture reasoning for your analytics stack.",
    no_args_is_help=True,
)

@architect_app.command("analyze")
def analyze_command(
    question: str = typer.Argument(None, help="Architecture question in plain English."),
    type_: str = typer.Option("tool_selection", "--type", "-t",
        help="tool_selection | cost_optimization | adr_compliance | stack_evolution | blueprint_selection"),
    provider: str = typer.Option(None, "--provider", "-p"),
    approve: bool = typer.Option(False, "--approve"),
):
    """Analyze your analytics architecture and get AI-powered recommendations."""

@architect_app.command("check-adrs")
def check_adrs_command(
    change: str = typer.Argument(..., help="Proposed change to check for ADR compliance."),
    provider: str = typer.Option(None, "--provider", "-p"),
):
    """Check whether a proposed change complies with your ADRs."""

@architect_app.command("compare")
def compare_command(
    tool_a: str = typer.Argument(...),
    tool_b: str = typer.Argument(...),
    provider: str = typer.Option(None, "--provider", "-p"),
):
    """Compare two tools for your specific data profile."""
```

Register in `cli/main.py`:
```python
from pipelinekit.cli.architect import architect_app
app.add_typer(architect_app, name="architect")
```

**CLI behavior rules:**
- `diagnostics.enabled = False` → print guidance, exit 0
- Insufficient run history (< 5 runs) → clear message, exit 0
- `--approve` → present recommendation interactively, record decision
- All Rich output — no print()

---

## Test Requirements

**All 151 Phase 1–4 tests must continue to pass.**  
All AI tests mock providers — zero real API calls.

### Minimum tests required:

**tests/ai/test_arch_models.py** — 4 tests:
- Valid `ArchitectureResult` with all required fields
- `can_auto_apply` defaults to False
- `confidence` outside 0–1 raises ValidationError
- `requires_approval` on recommendation defaults to True

**tests/ai/test_arch_evidence.py** — 4 tests:
- `collect()` returns `ArchitectureContext` from valid state.db
- `collect()` raises `ArchitectureError(PK-ARCH-004)` with < 5 runs
- `ArchitectureContext` is JSON-serializable
- Volume profile calculated from run history

**tests/ai/test_arch_engine.py** — 5 tests:
- `analyze()` returns `ArchitectureResult` (mocked provider)
- `can_auto_apply=True` from provider is corrected to False
- Invalid schema raises `LLMError(PK-AI-002)`
- Result stored in state.db via `insert_architecture_result()`
- `diagnostics.enabled=False` exits gracefully

**tests/ai/test_adr_reader.py** — 3 tests:
- `read_all()` returns list of ADR summaries from docs/decisions/
- Malformed ADR file is skipped — does not raise
- Missing decisions dir returns empty list — does not raise

---

## Architecture Rules — Non-Negotiable

```
can_auto_apply always False in Phase 5                    (ADR-015, ADR-007)
ArchitectureEngine never executes recommendations         (ADR-007, Smell 13)
ADRReader never writes ADR files                          (ADR-015)
Phase 4 DiagnosticsEngine unchanged                       (Phase 4 READ ONLY)
Phase 4 DiagnosticResult unchanged                        (Phase 4 READ ONLY)
schemas/diagnostic.schema.json unchanged                  (Phase 4 READ ONLY)
architecture.schema.json is the new output contract       (SPEC-011)
Provider architect() isolated in provider files           (ADR-014, Smell 2)
PipelineKit reasons above tools — never becomes one       (Smell 16)
PROJECT-STATUS.md never touched                           (Command Center)
```

---

## Validation Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry install

# Verify all prior phases still work
poetry run pipelinekit --help
poetry run pipelinekit diagnose --help

# Verify Phase 5
poetry run pipelinekit architect --help
poetry run pipelinekit architect analyze --help
poetry run pipelinekit architect check-adrs --help
poetry run pipelinekit architect compare --help

# Full quality gate
poetry run pytest --cov=src/pipelinekit --cov-report=term-missing --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

```
✓ poetry install completes with no errors
✓ All 151 Phase 1–4 tests still pass
✓ pipelinekit architect --help lists analyze, check-adrs, compare
✓ pipelinekit architect analyze returns ArchitectureResult (mocked)
✓ pipelinekit architect check-adrs returns ADR compliance report
✓ pipelinekit architect compare returns tool comparison
✓ All ArchitectureResult validates against architecture.schema.json
✓ can_auto_apply always False — no auto-application path exists
✓ ADRReader reads docs/decisions/ without writing
✓ Architecture results stored in state.db
✓ pipelinekit diagnose still works — Phase 4 unchanged
✓ pytest passes — all tests green
✓ coverage >= 80% overall
✓ ruff, black, mypy all clean
✓ No API keys in any file
✓ PROJECT-STATUS.md untouched
```

---

## Stop and Ask Before

- Setting `can_auto_apply = True` anywhere
- Writing any code that applies an `ArchitectureRecommendation`
- Modifying `diagnostics.py`, `evidence.py`, `models.py` (Phase 4 — read only)
- Modifying `schemas/diagnostic.schema.json`
- Writing to any ADR file in `docs/decisions/`
- Adding any MCP (ADR-014 — direct API calls only)
- Touching `PROJECT-STATUS.md`
- Modifying any Phase 1–4 test

---

## Final Instruction

Phase 5 is the last phase.

Phases 1–4 built an operating system that moves data, validates it, governs it, and diagnoses failures with AI. Phase 5 adds the layer that reasons about the architecture itself.

The difference is this:

Phase 4 looks backward — at what failed and why.
Phase 5 looks forward — at what to build and how.

An operating system that can only report on failures is valuable.
An operating system that can reason about its own architecture is rare.

That is what PipelineKit becomes in Phase 5.

The governing principle has been true since the first commit:

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Phase 5 is where "AI-native operating system" is fully realized.

Build it with the same discipline that built the other four phases.
The creed holds to the last line.
