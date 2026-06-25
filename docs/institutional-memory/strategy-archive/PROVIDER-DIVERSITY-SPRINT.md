# PipelineKit — Provider Diversity Sprint Prompt
## Add DeepSeek and Mistral Providers (ADR-016)

---

## Context

Phase 5 shipped with three AI providers: OpenAI, Anthropic, Ollama.

ADR-016 (Provider Diversity Policy) was committed during Phase 5 and requires
at least one non-US-headquartered cloud provider. DeepSeek (China) and
Mistral (EU/France) fulfill this requirement.

This is a small, focused sprint — two files only. All infrastructure exists.
You are following the exact same pattern as the existing providers.

---

## Read First

```
docs/decisions/ADR-016-Provider-Diversity.md    ← Why these providers
src/pipelinekit/ai/providers/anthropic.py       ← Pattern to follow exactly
src/pipelinekit/ai/providers/openai.py          ← Pattern to follow exactly
src/pipelinekit/ai/providers/__init__.py        ← Shared prompts you extend
```

---

## Files You Are Allowed To Create

```
src/pipelinekit/ai/providers/deepseek.py    DeepSeekProvider
src/pipelinekit/ai/providers/mistral.py     MistralProvider

tests/ai/providers/test_deepseek.py
tests/ai/providers/test_mistral.py
```

You may also modify:
```
src/pipelinekit/ai/providers/__init__.py    Register new providers in factory
docs/reference/Error-Codes.md              No new codes needed — reuse PK-AI-*
```

---

## Files You Must Not Modify

Everything not listed above. Especially:
- `docs/reference/PROJECT-STATUS.md` — Command Center owns it
- All Phase 4 and 5 AI files except providers/__init__.py
- Any existing test file

---

## Implementation — DeepSeek

```python
# src/pipelinekit/ai/providers/deepseek.py

class DeepSeekProvider:
    """DeepSeek AI provider.

    Data residency: China (DeepSeek AI servers).
    Suitable for: cost-sensitive deployments, Asian market customers.
    Not suitable for: EU GDPR or US FedRAMP requirements.
    API key: DEEPSEEK_API_KEY environment variable.
    Model default: deepseek-chat (maps to DeepSeek-V3)

    ADR-016: Non-US cloud provider requirement.
    """
```

DeepSeek uses an OpenAI-compatible API. Use the `openai` SDK with a custom base_url:

```python
from openai import OpenAI  # already a dependency — no new SDK needed

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
)
```

Implement: `diagnose()`, `summarize()`, `recommend()`, `architect()`  
Same system prompts as OpenAI (from providers/__init__.py)  
Same schema validation pattern  
Raises `LLMError(PK-AI-001)` if `DEEPSEEK_API_KEY` not set  
Raises `LLMError(PK-AI-002)` if response fails schema validation

---

## Implementation — Mistral

```python
# src/pipelinekit/ai/providers/mistral.py

class MistralProvider:
    """Mistral AI provider.

    Data residency: France, European Union (GDPR compliant).
    Suitable for: EU customers with GDPR data residency requirements.
    API key: MISTRAL_API_KEY environment variable.
    Model default: mistral-large-latest

    ADR-016: EU-based provider for GDPR compliance.
    """
```

Mistral has its own SDK: `mistralai` — add to pyproject.toml:

```toml
mistralai = "^1.0"
```

Implement: `diagnose()`, `summarize()`, `recommend()`, `architect()`  
Same system prompts from providers/__init__.py  
Same schema validation pattern  
Raises `LLMError(PK-AI-001)` if `MISTRAL_API_KEY` not set  
Raises `LLMError(PK-AI-002)` if response fails schema validation

---

## Register in providers/__init__.py

Add to the provider factory:

```python
"deepseek": lambda: DeepSeekProvider(),
"mistral":  lambda: MistralProvider(),
```

Update the provider list docstring to include deepseek and mistral.

---

## Tests (minimum)

**tests/ai/providers/test_deepseek.py** — 3 tests:
- `diagnose()` returns valid DiagnosticResult (mocked)
- Raises `LLMError(PK-AI-001)` when key missing
- All deepseek/openai imports isolated — none outside provider file

**tests/ai/providers/test_mistral.py** — 3 tests:
- `diagnose()` returns valid DiagnosticResult (mocked)
- Raises `LLMError(PK-AI-001)` when key missing
- All mistralai imports isolated — none outside provider file

No real API calls in tests.

---

## Validation Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit
poetry install
poetry run pytest tests/ai/providers/ --cov=src/pipelinekit/ai/providers --cov-report=term
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

```
✓ DeepSeekProvider implements LLMProvider (4 methods)
✓ MistralProvider implements LLMProvider (4 methods)
✓ Both registered in providers/__init__.py factory
✓ DEEPSEEK_API_KEY and MISTRAL_API_KEY documented in provider docstrings
✓ Data residency documented in each provider docstring
✓ No provider imports outside their respective files
✓ All tests pass (including all 174 prior tests)
✓ ruff, black, mypy all clean
✓ PROJECT-STATUS.md untouched
```

---

## Commit Message

```
feat: add DeepSeek and Mistral providers (ADR-016 provider diversity)

- src/pipelinekit/ai/providers/deepseek.py — DeepSeek-V3 via OpenAI-compatible API
- src/pipelinekit/ai/providers/mistral.py — Mistral Large (GDPR/EU)
- Both implement full LLMProvider Protocol (diagnose, summarize, recommend, architect)
- Data residency documented per ADR-016
- BYOK: DEEPSEEK_API_KEY, MISTRAL_API_KEY
```

---

## Stop and Ask Before

- Adding any dependency beyond `mistralai`
- Touching any file not in the allowed list
- Touching PROJECT-STATUS.md
- Modifying any existing provider file
