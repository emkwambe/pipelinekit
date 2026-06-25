# SPEC-005-AI-Diagnostics.md

**Status:** Approved  
**Owner:** diagnostics-engineer  
**Phase:** 4 — Intelligence Layer  
**Date:** June 25, 2026  
**ADRs:** ADR-007 (AI is Operator not Owner), ADR-014 (AI Provider MCP Layer), ADR-005 (BYOK)  
**Schemas:** schemas/diagnostic.schema.json  
**Depends on:** SPEC-003 (Runtime), SPEC-004 (Contracts), SPEC-007 (State), SPEC-009 (Adapters)  
**AI Strategy:** docs/ai/PIPELINEKIT-AI & Model Strategy Standard.md

---

## Purpose

Define the AI diagnostics subsystem — the intelligence layer that explains why pipelines fail, what caused contract violations, and what a team should do next.

Phase 4 is where PipelineKit becomes an operating system, not just a runner.

The AI layer does not replace contracts, quality checks, or deterministic validation.
It interprets the evidence they produce and explains it in human language.

**Deterministic first. AI second. Always.**

---

## Governing Rules

From `docs/ai/PIPELINEKIT-AI & Model Strategy Standard.md`:

- AI exists to improve diagnosis, remediation, onboarding, observability, and migration
- AI does not replace contracts, quality checks, deterministic validation, or observability
- Every AI recommendation must be grounded in observable evidence
- AI interprets — AI never defines truth
- Incorrect automation is worse than no automation
- Trust Before Intelligence: correctness, explainability, reproducibility before intelligence
- AI may diagnose and recommend — never silently modify production (ADR-007)
- Every AI recommendation requires explicit human approval before execution

---

## The Diagnostic Schema — Authoritative Contract

All AI output must validate against `schemas/diagnostic.schema.json`.

Required fields:

```json
{
  "status": "string",
  "finding_type": "string",
  "confidence": "number (0.0–1.0)",
  "evidence": "array",
  "recommended_actions": "array",
  "can_auto_fix": "boolean (default: false)"
}
```

The `DiagnosticsEngine` must reject any AI response that fails this schema.
No diagnostic output reaches the CLI without passing schema validation.
This is not optional — it is the trust boundary between AI and the user.

---

## Required Capabilities — Phase 4

| Capability | Description |
|---|---|
| `EvidenceCollector` | Assembles structured evidence from state.db, contract results, step results |
| `LLMProvider` Protocol | Stable interface — all AI providers implement it |
| `DiagnosticsEngine` | Coordinates evidence → LLM → schema validation → DiagnosticResult |
| `pipelinekit diagnose` | CLI command — triggers full diagnostic cycle |
| Three AI providers | OpenAI, Anthropic, Ollama (BYOK — ADR-005) |
| Schema validation | Every AI output validated against diagnostic.schema.json |
| Human approval gate | Recommended actions presented for human approval — never auto-executed |

---

## Evidence Architecture

Evidence is the input to every AI diagnosis. Without structured evidence, AI produces guesses. With structured evidence, AI produces explanations.

### Evidence Sources (all from state.db)

```python
@dataclass
class EvidencePackage:
    run_id: str
    pipeline_name: str
    pipeline_result: dict          # from pipeline_runs table
    step_results: list[dict]       # per-step outcomes from executor
    contract_results: list[dict]   # from contract_results table
    validation_results: list[dict] # from validation_runs table
    recent_runs: list[dict]        # last 5 runs for pattern detection
    config_snapshot: dict          # pipelinekit.yaml at time of run
    error_codes: list[str]         # all PK-* codes from this run
```

### Evidence Collection Rules

- Evidence is read-only — EvidenceCollector never writes to state.db
- Evidence is assembled before any AI call — never fetched mid-diagnosis
- Evidence must be serializable to JSON — no Python objects in the package
- If a run_id does not exist in state.db → raise `DiagnosticsError(PK-DIAG-001)`
- If evidence is incomplete (missing required fields) → diagnose with available evidence, flag gaps

---

## LLMProvider Protocol

The stable interface all AI providers implement.
Provider-specific code never leaves `src/pipelinekit/ai/providers/`.

```python
# src/pipelinekit/ai/provider.py

from typing import Protocol
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction

class LLMProvider(Protocol):
    """Stable interface for all AI providers.

    Provider-specific code stays in providers/<name>.py.
    The DiagnosticsEngine calls this interface only.
    ADR-007: AI observes and recommends — never acts.
    ADR-005: BYOK — customer provides API key.
    """

    def diagnose(self, evidence: EvidencePackage) -> DiagnosticResult:
        """
        Analyze evidence and return a structured DiagnosticResult.
        Output must validate against schemas/diagnostic.schema.json.
        Raises LLMError(PK-AI-001) if provider unavailable.
        Raises LLMError(PK-AI-002) if response fails schema validation.
        """
        ...

    def summarize(self, logs: list[str]) -> str:
        """Summarize log entries in plain English. Never invents facts."""
        ...

    def recommend(
        self, diagnosis: DiagnosticResult
    ) -> list[RecommendedAction]:
        """
        Generate recommended actions from a diagnosis.
        Actions are suggestions — never executed without human approval.
        """
        ...
```

---

## DiagnosticResult Model

```python
# src/pipelinekit/ai/models.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional

class RecommendedAction(BaseModel):
    action: str                      # human-readable description
    command: Optional[str] = None    # pipelinekit command if applicable
    risk_level: str = "low"          # low | medium | high
    reversible: bool = True
    requires_approval: bool = True   # always True in Phase 4

class DiagnosticResult(BaseModel):
    """Validated against schemas/diagnostic.schema.json.

    Every field maps directly to a required schema field.
    No additional fields without schema update.
    """
    status: str                      # "diagnosed" | "inconclusive" | "error"
    finding_type: str                # "contract_violation" | "adapter_failure" |
                                     # "configuration_error" | "data_quality" |
                                     # "freshness_violation" | "unknown"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[dict]             # structured evidence items used
    recommended_actions: list[RecommendedAction]
    can_auto_fix: bool = False       # Phase 4: always False — human approval required
    explanation: str = ""            # human-readable root cause explanation
    run_id: str = ""
    pipeline_name: str = ""

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_valid(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
```

---

## DiagnosticsEngine

```python
# src/pipelinekit/ai/diagnostics.py

from pipelinekit.ai.evidence import EvidenceCollector
from pipelinekit.ai.provider import LLMProvider
from pipelinekit.ai.models import DiagnosticResult
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import DiagnosticsError

class DiagnosticsEngine:
    """Orchestrates evidence collection → AI diagnosis → schema validation.

    The engine is the trust boundary between structured evidence and AI output.
    It never passes raw logs or unstructured text to the AI provider.
    It never returns AI output that fails schema validation.

    ADR-007: AI observes and recommends. Never acts.
    """

    def __init__(self, config: PipelineConfig, provider: LLMProvider):
        self.config = config
        self.provider = provider
        self.collector = EvidenceCollector()

    def diagnose(self, run_id: str) -> DiagnosticResult:
        """
        Full diagnostic cycle:
        1. Collect evidence from state.db for run_id
        2. Call provider.diagnose(evidence)
        3. Validate result against diagnostic.schema.json
        4. Return DiagnosticResult — never execute recommendations
        """
        ...

    def _validate_against_schema(self, result: DiagnosticResult) -> None:
        """
        Validate DiagnosticResult against schemas/diagnostic.schema.json.
        Raises DiagnosticsError(PK-AI-002) on validation failure.
        This is the trust boundary — no invalid AI output reaches the CLI.
        """
        ...
```

---

## AI Provider Adapters

### Phase 4 — Three providers

```
src/pipelinekit/ai/providers/
├── __init__.py
├── openai.py      OpenAIProvider — implements LLMProvider
├── anthropic.py   AnthropicProvider — implements LLMProvider
└── ollama.py      OllamaProvider — implements LLMProvider (local, air-gapped)
```

### BYOK Rule (ADR-005)

| Provider | Environment Variable |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Ollama | `OLLAMA_HOST` (default: http://localhost:11434) |

API keys are never hardcoded. Never logged. Never stored in state.db.

### Provider Selection

```yaml
# pipelinekit.yaml
diagnostics:
  enabled: true
  provider: anthropic    # openai | anthropic | ollama
```

`AdapterFactory` creates the correct provider from config.
The `DiagnosticsEngine` never knows which provider is active.

### Confidence Threshold

```yaml
diagnostics:
  enabled: true
  provider: anthropic
  confidence_threshold: 0.7    # default — results below this flagged as inconclusive
```

Results below threshold are returned as `status: "inconclusive"` — not suppressed.
The user always sees the diagnosis, even low-confidence ones.

---

## pipelinekit diagnose Command

```python
# src/pipelinekit/cli/diagnose.py

def diagnose_command(
    run_id: str = typer.Argument(
        None,
        help="Run ID to diagnose. Defaults to most recent run."
    ),
    provider: str = typer.Option(
        None, "--provider",
        help="Override provider from config (openai|anthropic|ollama)."
    ),
    approve: bool = typer.Option(
        False, "--approve",
        help="Interactively approve recommended actions."
    ),
):
    """Diagnose a pipeline run using AI-assisted root cause analysis."""
```

### Output format

```
Diagnosing run run-a3f2c1b8...

✓ Evidence collected — 3 contract violations, 1 adapter failure

Finding:    contract_violation
Confidence: 0.91
Explanation:

  The orders table failed freshness validation (18h old, max 12h). This
  is consistent with the ingestion step timing out at 09:14 UTC. The
  root cause appears to be a connection pool exhaustion on the Postgres
  source — 3 of the last 5 runs show similar patterns between 09:00-10:00.

Evidence used:
  · run-a3f2c1b8: PK-ADAPTER-001 (connection refused)
  · orders contract: PK-CONTRACT-002 (freshness violation)
  · 3 prior runs: similar failure window

Recommended actions:

  1. [low risk] Increase Postgres connection pool size
     Command: (manual — edit Postgres config)

  2. [low risk] Reschedule pipeline to 08:00 UTC
     Command: (manual — edit your scheduler)

  3. [medium risk] Add connection retry logic to ingestion adapter
     Command: (manual — open issue in your repo)

Run 'pipelinekit diagnose --approve' to review and approve actions.
```

### Approval flow (--approve flag)

```
Action 1 of 3: Increase Postgres connection pool size
Risk: low | Reversible: yes
Approve? [y/N]:
```

Approved actions are recorded in state.db — never auto-executed.
The user receives a summary of approved actions to execute manually.

---

## File Structure

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
        ├── test_openai.py
        ├── test_anthropic.py
        └── test_ollama.py
```

---

## Error Codes — Phase 4

| Code | Meaning |
|---|---|
| `PK-AI-001` | AI provider unavailable |
| `PK-AI-002` | AI response failed schema validation |
| `PK-AI-003` | AI confidence below threshold |
| `PK-DIAG-001` | Run ID not found in state.db |
| `PK-DIAG-002` | Evidence collection failed |
| `PK-DIAG-003` | Diagnosis engine initialization failed |

Add `DiagnosticsError` to `src/pipelinekit/core/errors.py`:

```python
class DiagnosticsError(PipelineKitError):
    """Raised when evidence collection or AI diagnosis fails."""

class LLMError(PipelineKitError):
    """Raised when an AI provider is unavailable or returns invalid output."""
```

---

## pyproject.toml — Phase 4 Additions

```toml
[tool.poetry.dependencies]
openai = "^1.0"
anthropic = "^0.25"
ollama = "^0.2"
jsonschema = "^4.0"    # already added in Phase 3
```

All provider imports isolated inside their adapter files.
Zero openai/anthropic/ollama imports outside `src/pipelinekit/ai/providers/`.

---

## Test Strategy

All AI provider tests mock the provider — no real API calls in tests.

```python
# tests/ai/test_diagnostics.py

def test_diagnose_returns_valid_result(mock_evidence, mock_provider):
    """DiagnosticsEngine returns DiagnosticResult on valid evidence."""
    ...

def test_invalid_schema_raises_error(mock_evidence, bad_provider):
    """DiagnosticsEngine raises LLMError(PK-AI-002) on schema violation."""
    ...

def test_low_confidence_marked_inconclusive(mock_evidence, low_conf_provider):
    """Results below threshold return status=inconclusive, not suppressed."""
    ...

def test_evidence_collector_reads_state(tmp_path):
    """EvidenceCollector assembles correct package from state.db."""
    ...

def test_recommended_actions_never_auto_execute():
    """No code path exists that executes a RecommendedAction without approval."""
    ...
```

---

## Constraints

- AI providers imported only inside `src/pipelinekit/ai/providers/`
- DiagnosticsEngine never executes recommendations — returns them only
- Schema validation is mandatory — not skippable
- Confidence threshold respected — inconclusive is a valid result
- Evidence is read-only — EvidenceCollector never writes
- `can_auto_fix` is always False in Phase 4
- No AI calls in tests — mock at the LLMProvider protocol level
- API keys via environment variables only — never hardcoded

---

## AI Guardrails Summary

```
AI may:      inspect, diagnose, recommend, summarize, classify
AI may not:  deploy, delete, modify production, rotate secrets, auto-execute

Evidence:    read from state.db — never invented
Output:      must validate against diagnostic.schema.json
Approval:    every recommended action requires human confirmation
Execution:   always manual — PipelineKit records approval, never runs it
```

---

## Acceptance Criteria

```
✓ pipelinekit diagnose <run_id> exits 0 with DiagnosticResult
✓ pipelinekit diagnose defaults to most recent run when no run_id given
✓ All DiagnosticResult output validates against diagnostic.schema.json
✓ Invalid AI response raises LLMError(PK-AI-002) — never reaches CLI
✓ confidence < threshold returns status=inconclusive
✓ pipelinekit diagnose --approve presents actions for human review
✓ No recommended action is ever auto-executed
✓ OpenAI, Anthropic, Ollama all implement LLMProvider correctly
✓ Zero provider imports outside src/pipelinekit/ai/providers/
✓ EvidenceCollector never writes to state.db
✓ poetry run pytest tests/ai/ → all tests pass
✓ coverage >= 85% on src/pipelinekit/ai/
✓ No API keys in any file
✓ PROJECT-STATUS.md untouched
```

---

## Out of Scope

- `can_auto_fix = True` — Phase 5 only, requires ADR-016
- `pipelinekit fix` auto-remediation command — Phase 5
- Architecture Intelligence ("what architecture should I use?") — Phase 5, SPEC-011
- Real-time streaming diagnostics — Phase 5+
- Diagnostic history UI — Phase 5+
- Model fine-tuning on customer pipeline data — Phase 5+
