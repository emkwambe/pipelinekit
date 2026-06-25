# PipelineKit — Phase 4 Claude Code Implementation Prompt
## Intelligence Layer Sprint: AI Diagnostics + LLMProvider + pipelinekit diagnose

---

## Your Identity

You are Claude Code operating as the **PipelineKit Diagnostics Engineer** and **Quality Engineer**.

Your agent roles:
- `agents/diagnostics-engineer/AGENT.md` + `SYSTEM.md` — primary
- `agents/quality-engineer/AGENT.md` — tests

You are not the CLI Engineer. You are not the Runtime Engineer.
You build the AI layer. You call the runtime's existing interfaces.
You never modify what Phase 1, 2, or 3 built — you build on top of it.

---

## Repository

```
Local path: C:\Users\HP\Documents\pipelinekit
GitHub:     https://github.com/emkwambe/pipelinekit
```

---

## Read First — In This Exact Order

```
1.  .claude/CLAUDE.md                                          ← Your operating rules (v3)
2.  docs/constitution/Product-Constitution.md
3.  docs/decisions/ADR-000-Foundational-Architecture-Decisions.md
4.  docs/decisions/ADR-007-* (AI is Operator not Owner)        ← Load-bearing ADR
5.  docs/decisions/ADR-014-AI-Provider-MCP-Layer.md            ← Phase 4 AI governance
6.  docs/decisions/ADR-005-* (BYOK)
7.  agents/diagnostics-engineer/AGENT.md
8.  agents/diagnostics-engineer/SYSTEM.md
9.  docs/specifications/SPEC-005-AI-Diagnostics.md             ← Your primary spec
10. docs/specifications/SPEC-007-State-Store.md                ← Evidence lives here
11. docs/specifications/SPEC-003-Pipeline-Runtime.md           ← PipelineResult you read
12. docs/specifications/SPEC-010-Testing-and-Quality-Gates.md
13. docs/reference/Error-Codes.md
14. docs/reference/Architectural-Smells.md                     ← All 16 — especially 13
15. docs/reference/PROJECT-STATUS.md
16. docs/ai/PIPELINEKIT-AI & Model Strategy Standard.md        ← Read every word
17. schemas/diagnostic.schema.json                             ← Authoritative AI contract
18. src/pipelinekit/core/errors.py                             ← Add 2 classes only
19. src/pipelinekit/state/db.py                                ← Evidence source
20. src/pipelinekit/runtime/result.py                          ← PipelineResult you read
21. src/pipelinekit/adapters/base.py                           ← Pattern you follow
22. contracts/provider.yaml                                    ← Adapter contract
```

Do not skip items 16 and 17. The AI strategy document and diagnostic schema
are the authoritative contracts for everything you build in Phase 4.

---

## Sprint Goal

Deliver Phase 4 such that all of the following work:

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry run pipelinekit diagnose --help
poetry run pipelinekit diagnose <run_id>
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

**Plus** — all 112 Phase 1 + 2 + 3 tests must still pass.
**Plus** — CI must remain green on GitHub.

---

## Files You Are Allowed To Create

```
src/pipelinekit/
└── ai/
    ├── __init__.py
    ├── provider.py          LLMProvider Protocol
    ├── evidence.py          EvidenceCollector, EvidencePackage
    ├── models.py            DiagnosticResult, RecommendedAction
    ├── diagnostics.py       DiagnosticsEngine
    └── providers/
        ├── __init__.py
        ├── openai.py        OpenAIProvider
        ├── anthropic.py     AnthropicProvider
        └── ollama.py        OllamaProvider

src/pipelinekit/cli/
└── diagnose.py              pipelinekit diagnose command

tests/
└── ai/
    ├── __init__.py
    ├── test_evidence.py
    ├── test_models.py
    ├── test_diagnostics.py
    └── providers/
        ├── __init__.py
        ├── test_openai.py
        ├── test_anthropic.py
        └── test_ollama.py
```

You may also modify:
```
src/pipelinekit/core/errors.py    Add DiagnosticsError + LLMError only
src/pipelinekit/cli/main.py       Register diagnose command only
src/pipelinekit/state/db.py       Add diagnostic_results table + insert_diagnostic_result() only
docs/reference/Error-Codes.md    Add Phase 4 codes only
pyproject.toml                    Add openai, anthropic, ollama dependencies only
```

---

## Files You Must Not Modify

```
docs/                                    ← READ ONLY
docs/reference/PROJECT-STATUS.md        ← NEVER TOUCH — Command Center owns this
schemas/                                 ← READ ONLY — diagnostic.schema.json is authoritative
contracts/                               ← READ ONLY
agents/                                  ← READ ONLY
.claude/                                 ← READ ONLY
.github/                                 ← READ ONLY
.mcp/                                    ← READ ONLY (no AI MCPs in Phase 4)
src/pipelinekit/config/                  ← READ ONLY
src/pipelinekit/runtime/                 ← READ ONLY
src/pipelinekit/adapters/ (existing)     ← READ ONLY
src/pipelinekit/contracts/               ← READ ONLY
src/pipelinekit/blueprints/              ← READ ONLY
src/pipelinekit/notifications/           ← READ ONLY
src/pipelinekit/cli/init.py              ← READ ONLY
src/pipelinekit/cli/validate.py          ← READ ONLY
src/pipelinekit/cli/status.py            ← READ ONLY
src/pipelinekit/cli/run.py               ← READ ONLY
src/pipelinekit/cli/blueprint.py         ← READ ONLY
tests/cli/                               ← READ ONLY
tests/config/                            ← READ ONLY
tests/state/                             ← READ ONLY
tests/runtime/                           ← READ ONLY
tests/adapters/                          ← READ ONLY
tests/contracts/                         ← READ ONLY
tests/blueprints/                        ← READ ONLY
tests/notifications/                     ← READ ONLY
```

---

## pyproject.toml — Phase 4 Additions Only

```toml
[tool.poetry.dependencies]
openai = "^1.0"
anthropic = "^0.25"
ollama = "^0.2"
```

All provider imports stay inside `src/pipelinekit/ai/providers/`.
Zero openai/anthropic/ollama imports anywhere else.

---

## The AI Boundary — Non-Negotiable

From ADR-007 and the AI Strategy Standard. This boundary is enforced by design.

```
AI MAY:
  ✓ Read evidence from state.db (via EvidenceCollector — read only)
  ✓ Analyze evidence and return DiagnosticResult
  ✓ Recommend actions (in DiagnosticResult.recommended_actions)
  ✓ Summarize logs and contract violations in plain English
  ✓ Classify failure types

AI MAY NOT:
  ✗ Write to state.db (except via insert_diagnostic_result — see below)
  ✗ Execute any pipeline command
  ✗ Modify pipelinekit.yaml
  ✗ Access credentials other than its own provider API key
  ✗ Make network calls outside its own provider API
  ✗ Set can_auto_fix = True (Phase 4: always False)
  ✗ Auto-execute any recommended action
```

`can_auto_fix` in `DiagnosticResult` is `False` in Phase 4.
No code path exists that auto-executes a `RecommendedAction`.
If you find yourself writing execution logic — stop and ask.

---

## The Diagnostic Schema — Authoritative Contract

`schemas/diagnostic.schema.json` requires exactly 5 fields:

```json
{
  "status":              "string",
  "finding_type":        "string",
  "confidence":          "number (0.0–1.0)",
  "evidence":            "array",
  "recommended_actions": "array",
  "can_auto_fix":        "boolean (default: false)"
}
```

Every `DiagnosticResult` must validate against this schema.
The `DiagnosticsEngine._validate_against_schema()` method enforces it.
If validation fails → raise `LLMError("PK-AI-002", ...)`.
This is the trust boundary. It is not optional.

---

## Implementation Requirements

### 1. src/pipelinekit/core/errors.py — Add Two Classes Only

```python
class DiagnosticsError(PipelineKitError):
    """Raised when evidence collection or diagnostics engine fails."""

class LLMError(PipelineKitError):
    """Raised when an AI provider is unavailable or returns invalid output."""
```

Do not change any existing class.

---

### 2. src/pipelinekit/ai/evidence.py

`EvidencePackage` is the structured input to every AI diagnosis.
`EvidenceCollector` assembles it from state.db — read only, never writes.

```python
@dataclass
class EvidencePackage:
    run_id: str
    pipeline_name: str
    pipeline_result: dict          # from pipeline_runs table
    step_results: list[dict]       # per-step data from executor
    contract_results: list[dict]   # from contract_results table
    validation_results: list[dict] # from validation_runs table
    recent_runs: list[dict]        # last 5 runs for pattern detection
    config_snapshot: dict          # pipelinekit.yaml sections relevant to this run
    error_codes: list[str]         # all PK-* codes from this run

class EvidenceCollector:
    def collect(self, run_id: str, cwd: Path | None = None) -> EvidencePackage:
        """
        Assemble evidence from state.db for a given run_id.
        Raises DiagnosticsError(PK-DIAG-001) if run_id not found.
        Raises DiagnosticsError(PK-DIAG-002) if evidence incomplete.
        Never writes to state.db.
        Returns EvidencePackage — fully JSON-serializable.
        """
        ...

    def get_most_recent_run_id(self, cwd: Path | None = None) -> str:
        """
        Return the run_id of the most recent pipeline run.
        Raises DiagnosticsError(PK-DIAG-001) if no runs exist.
        """
        ...
```

---

### 3. src/pipelinekit/ai/models.py

Implement exactly as specified in SPEC-005.
Every field maps to a required field in `schemas/diagnostic.schema.json`.

```python
class RecommendedAction(BaseModel):
    action: str
    command: Optional[str] = None
    risk_level: str = "low"       # low | medium | high
    reversible: bool = True
    requires_approval: bool = True  # always True in Phase 4

class DiagnosticResult(BaseModel):
    status: str                    # diagnosed | inconclusive | error
    finding_type: str              # contract_violation | adapter_failure |
                                   # configuration_error | data_quality |
                                   # freshness_violation | unknown
    confidence: float              # 0.0–1.0, validated
    evidence: list[dict]           # structured items used in diagnosis
    recommended_actions: list[RecommendedAction]
    can_auto_fix: bool = False     # always False in Phase 4
    explanation: str = ""
    run_id: str = ""
    pipeline_name: str = ""
```

---

### 4. src/pipelinekit/ai/provider.py

The stable `LLMProvider` Protocol. No concrete provider code here.

```python
from typing import Protocol
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult

class LLMProvider(Protocol):
    def diagnose(self, evidence: EvidencePackage) -> DiagnosticResult: ...
    def summarize(self, logs: list[str]) -> str: ...
    def recommend(self, diagnosis: DiagnosticResult) -> list[dict]: ...
```

---

### 5. src/pipelinekit/ai/diagnostics.py

`DiagnosticsEngine` is the trust boundary between evidence and AI output.

```python
class DiagnosticsEngine:
    def __init__(self, config: PipelineConfig, provider: LLMProvider):
        self.config = config
        self.provider = provider
        self.collector = EvidenceCollector()

    def diagnose(self, run_id: str, cwd: Path | None = None) -> DiagnosticResult:
        """
        1. Collect evidence via EvidenceCollector
        2. Call provider.diagnose(evidence)
        3. Validate result against diagnostic.schema.json
        4. Store result in state.db via insert_diagnostic_result()
        5. Return DiagnosticResult
        Never executes recommendations.
        """
        ...

    def _validate_against_schema(self, result: DiagnosticResult) -> None:
        """
        Validate against schemas/diagnostic.schema.json.
        Raises LLMError(PK-AI-002) on failure.
        This is the trust boundary — no invalid output reaches CLI.
        """
        ...
```

---

### 6. src/pipelinekit/ai/providers/anthropic.py

```python
class AnthropicProvider:
    """Anthropic Claude provider. Default recommended provider.

    All anthropic imports stay inside this file.
    API key from ANTHROPIC_API_KEY environment variable.
    Raises LLMError(PK-AI-001) if key missing or provider unavailable.
    Raises LLMError(PK-AI-002) if response fails schema validation.
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        ...
```

### 7. src/pipelinekit/ai/providers/openai.py

```python
class OpenAIProvider:
    """OpenAI provider. All openai imports stay inside this file.
    API key from OPENAI_API_KEY environment variable.
    """
    def __init__(self, model: str = "gpt-4o"):
        ...
```

### 8. src/pipelinekit/ai/providers/ollama.py

```python
class OllamaProvider:
    """Ollama local provider. For air-gapped enterprise deployments.
    All ollama imports stay inside this file.
    Host from OLLAMA_HOST env var (default: http://localhost:11434).
    """
    def __init__(self, model: str = "llama3"):
        ...
```

Each provider implements `LLMProvider` protocol completely.
Each provider prompts the AI with structured evidence — never raw logs.
Each provider parses the response and returns a `DiagnosticResult`.

**Prompt pattern for all providers:**

```python
SYSTEM_PROMPT = """You are a data pipeline diagnostics assistant.
Analyze the provided pipeline evidence and return a JSON diagnostic result.
Your response must be valid JSON matching this schema:
{
  "status": "diagnosed|inconclusive|error",
  "finding_type": "contract_violation|adapter_failure|configuration_error|data_quality|freshness_violation|unknown",
  "confidence": 0.0-1.0,
  "evidence": [{"type": "...", "detail": "..."}],
  "recommended_actions": [{"action": "...", "risk_level": "low|medium|high", "reversible": true}],
  "can_auto_fix": false,
  "explanation": "Human-readable root cause explanation"
}
Never invent evidence. Only use what is provided.
can_auto_fix must always be false."""
```

---

### 9. src/pipelinekit/state/db.py — Addition Only

Add to the `_SCHEMA` string:

```sql
CREATE TABLE IF NOT EXISTS diagnostic_results (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    status          TEXT NOT NULL,
    finding_type    TEXT NOT NULL,
    confidence      REAL NOT NULL,
    explanation     TEXT,
    evidence        TEXT,        -- JSON array
    actions         TEXT,        -- JSON array
    can_auto_fix    INTEGER DEFAULT 0,
    diagnosed_at    TEXT NOT NULL,
    provider        TEXT
);
```

Add one new function:

```python
def insert_diagnostic_result(
    run_id: str,
    result: dict,
    provider: str,
    cwd: Path | None = None,
) -> None:
    """Store diagnostic result. Called by DiagnosticsEngine only."""
```

Do not change any existing function.

---

### 10. src/pipelinekit/cli/diagnose.py

```python
def diagnose_command(
    run_id: str = typer.Argument(
        None,
        help="Run ID to diagnose. Defaults to most recent run."
    ),
    provider: str = typer.Option(
        None, "--provider", "-p",
        help="AI provider override: openai | anthropic | ollama"
    ),
    approve: bool = typer.Option(
        False, "--approve",
        help="Interactively review recommended actions."
    ),
):
    """Diagnose a pipeline run using AI-assisted root cause analysis."""
```

**Behavior:**
1. Load config via `load_config()`
2. If `diagnostics.enabled` is False → print guidance, exit 0
3. Resolve run_id — if None, use `EvidenceCollector.get_most_recent_run_id()`
4. Create provider from config (or --provider override)
5. Call `DiagnosticsEngine.diagnose(run_id)`
6. Render `DiagnosticResult` with Rich
7. If `--approve` → present actions interactively
8. Exit 0 on success, exit 1 on `LLMError` or `DiagnosticsError`

**Output format — success:**
```
Diagnosing run-a3f2c1b8...

✓ Evidence collected

Finding:     contract_violation
Confidence:  0.91
Status:      diagnosed

Explanation:
  The orders table failed freshness validation (18h old, max 12h).
  Root cause appears to be Postgres connection pool exhaustion —
  3 of the last 5 runs show similar failures between 09:00-10:00 UTC.

Evidence used:
  · PK-ADAPTER-001 — connection refused at 09:14 UTC
  · PK-CONTRACT-002 — orders freshness violation
  · 3 prior runs with similar timing pattern

Recommended actions:
  1. [low risk] Increase Postgres connection pool size
  2. [low risk] Reschedule pipeline to 08:00 UTC

Run with --approve to review actions interactively.
```

**Output format — inconclusive:**
```
⚠ Diagnosis inconclusive (confidence: 0.42)

Insufficient evidence to determine root cause.
Run 'pipelinekit status' to check recent run history.
```

Register in `src/pipelinekit/cli/main.py`:
```python
from pipelinekit.cli.diagnose import diagnose_command
app.command("diagnose")(diagnose_command)
```

---

## Provider Factory

Add to `src/pipelinekit/adapters/factory.py`:

```python
@staticmethod
def create_ai_provider(config: PipelineConfig, override: str | None = None) -> "LLMProvider":
    """Create AI provider from config or override string."""
```

The factory keeps provider selection in one place.
The CLI calls the factory. The DiagnosticsEngine receives a provider.

---

## Test Requirements

**All 112 prior tests must continue to pass.**

All AI provider tests mock the provider — **zero real API calls in tests**.
Use `unittest.mock.patch` or `pytest-mock` to mock at the `LLMProvider` protocol level.

### Minimum tests required:

**tests/ai/test_evidence.py** — 4 tests:
- `collect()` returns `EvidencePackage` from valid state.db
- `collect()` raises `DiagnosticsError(PK-DIAG-001)` on unknown run_id
- `get_most_recent_run_id()` returns correct id
- `EvidencePackage` is fully JSON-serializable

**tests/ai/test_models.py** — 4 tests:
- Valid `DiagnosticResult` with all 5 required schema fields
- `confidence` outside 0.0–1.0 raises `ValidationError`
- `can_auto_fix` defaults to `False`
- `RecommendedAction.requires_approval` defaults to `True`

**tests/ai/test_diagnostics.py** — 5 tests:
- `diagnose()` returns `DiagnosticResult` on valid evidence (mocked provider)
- `diagnose()` raises `LLMError(PK-AI-002)` when provider returns invalid schema
- `diagnose()` stores result in state.db via `insert_diagnostic_result()`
- Low confidence result returns `status=inconclusive`
- `can_auto_fix=True` in provider response is corrected to `False`

**tests/ai/providers/test_anthropic.py** — 3 tests:
- `diagnose()` returns valid `DiagnosticResult` (mocked Anthropic API)
- `diagnose()` raises `LLMError(PK-AI-001)` when key missing
- All `anthropic` imports isolated — none detectable outside this file

**tests/ai/providers/test_openai.py** — 3 tests:
- `diagnose()` returns valid `DiagnosticResult` (mocked OpenAI API)
- `diagnose()` raises `LLMError(PK-AI-001)` when key missing
- All `openai` imports isolated

**tests/ai/providers/test_ollama.py** — 3 tests:
- `diagnose()` returns valid `DiagnosticResult` (mocked Ollama)
- Falls back gracefully when `OLLAMA_HOST` not set
- All `ollama` imports isolated

---

## Architecture Rules — Non-Negotiable

```
AI imports only inside src/pipelinekit/ai/providers/      (ADR-014, SPEC-005)
DiagnosticsEngine never executes recommendations           (ADR-007, Smell 13)
can_auto_fix always False in Phase 4                       (ADR-007)
Schema validation mandatory — not skippable               (SPEC-005)
EvidenceCollector is read-only                            (SPEC-005)
No real API calls in tests                                (SPEC-010)
All provider errors map to PK-AI-* or PK-DIAG-* codes    (Error-Codes.md)
Runtime never imports from ai/                            (CLI→Runtime→Adapter boundary)
PROJECT-STATUS.md never touched                           (Command Center owns it)
```

---

## Validation Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry install

# Verify Phase 1-3 still works
poetry run pipelinekit --help
poetry run pipelinekit init
poetry run pipelinekit validate
poetry run pipelinekit run --dry-run
poetry run pipelinekit blueprint list

# Verify Phase 4 works
poetry run pipelinekit diagnose --help

# Full quality gate
poetry run pytest --cov=src/pipelinekit --cov-report=term-missing --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

Phase 4 is complete when ALL of the following are true:

```
✓ poetry install completes with no errors
✓ All 112 Phase 1-3 tests still pass
✓ pipelinekit diagnose --help shows the command
✓ pipelinekit diagnose <run_id> returns DiagnosticResult
✓ pipelinekit diagnose defaults to most recent run when no run_id given
✓ All DiagnosticResult output validates against diagnostic.schema.json
✓ Invalid AI response raises LLMError(PK-AI-002) — never reaches CLI
✓ confidence < threshold returns status=inconclusive
✓ can_auto_fix is always False — no auto-execution path exists
✓ OpenAI, Anthropic, Ollama all implement LLMProvider correctly
✓ Zero provider imports outside src/pipelinekit/ai/providers/
✓ EvidenceCollector never writes to state.db
✓ DiagnosticResult stored in state.db after every diagnosis
✓ pytest passes — all tests green (Phase 1-4)
✓ coverage >= 80% across src/pipelinekit/
✓ coverage >= 85% on src/pipelinekit/ai/
✓ ruff check passes — zero errors
✓ black --check passes — zero errors
✓ mypy passes — zero errors
✓ No API keys in any file
✓ PROJECT-STATUS.md untouched
```

---

## Stop and Ask Before

- Adding any dependency not listed (openai, anthropic, ollama)
- Creating any file not in the allowed list
- Setting `can_auto_fix = True` anywhere
- Writing any code that executes a `RecommendedAction`
- Importing openai/anthropic/ollama outside `ai/providers/`
- Touching PROJECT-STATUS.md for any reason
- Modifying any Phase 1, 2, or 3 file beyond the allowed additions
- Making any real AI API call in tests
- Adding an MCP for AI providers (Phase 4 uses direct API calls — ADR-014)

---

## Final Instruction

Phase 4 is where PipelineKit becomes an operating system.

Phases 1-3 built the engine that moves, validates, and governs data.
Phase 4 adds the intelligence that explains what goes wrong and what to do next.

The difference between a pipeline tool and an operating system is this:
a tool runs. An operating system understands.

PipelineKit understands through evidence — structured, deterministic,
grounded in contracts and quality checks — not through guesswork.
The AI layer interprets that evidence. It never invents it.

Every diagnosis must be traceable to real evidence in state.db.
Every recommendation must be presented to a human before any action is taken.
Every AI output must validate against the diagnostic schema.

That discipline is what makes the intelligence trustworthy.

The product is the AI-native operating system for trusted analytics pipelines.
Phase 4 is where "AI-native" becomes true.
