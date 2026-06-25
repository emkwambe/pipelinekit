"""AI providers and the provider factory.

All provider SDK imports (openai, anthropic, ollama) are isolated inside the
individual provider modules. This package also hosts:

- ``SYSTEM_PROMPT`` — the shared structured-output instruction
- ``parse_diagnostic_response`` — shared raw-text → ``DiagnosticResult`` parser
- ``create_provider`` — the provider factory (selection logic in one place)

The factory lives here rather than in ``adapters/factory.py``: that module is
owned by the runtime-engineer and is read-only for the diagnostics-engineer
(CLAUDE.md Agent Boundary Rule, Smell 3). Keeping AI provider selection in the
AI package respects the boundary. (Flagged deviation from the brief's
"Provider Factory" section, which named adapters/factory.py.)
"""

from __future__ import annotations

import json

from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult
from pipelinekit.ai.provider import LLMProvider
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError

SYSTEM_PROMPT = """You are a data pipeline diagnostics assistant.
Analyze the provided pipeline evidence and return a JSON diagnostic result.
Your response must be valid JSON matching this schema:
{
  "status": "diagnosed|inconclusive|error",
  "finding_type": "contract_violation|adapter_failure|configuration_error|\
data_quality|freshness_violation|unknown",
  "confidence": 0.0-1.0,
  "evidence": [{"type": "...", "detail": "..."}],
  "recommended_actions": [{"action": "...", "risk_level": "low|medium|high", \
"reversible": true}],
  "can_auto_fix": false,
  "explanation": "Human-readable root cause explanation"
}
Never invent evidence. Only use what is provided.
can_auto_fix must always be false."""


def build_user_prompt(evidence: EvidencePackage) -> str:
    """Render the evidence package as the user prompt (structured, never raw)."""
    return "Diagnose this pipeline run using only the evidence below.\n\n" + json.dumps(
        evidence.to_dict(), indent=2, default=str
    )


def parse_diagnostic_response(raw: str, evidence: EvidencePackage) -> DiagnosticResult:
    """Parse a provider's raw text response into a ``DiagnosticResult``.

    Raises:
        LLMError: ``PK-AI-002`` if the text is not valid JSON or does not
            satisfy the ``DiagnosticResult`` model.
    """
    text = _strip_code_fences(raw)
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise LLMError(
            "PK-AI-002",
            "AI response was not valid JSON",
            {"detail": str(exc)},
        ) from exc

    data.setdefault("run_id", evidence.run_id)
    data.setdefault("pipeline_name", evidence.pipeline_name)
    try:
        return DiagnosticResult(**data)
    except Exception as exc:
        raise LLMError(
            "PK-AI-002",
            f"AI response did not match the diagnostic model: {exc}",
            {"detail": str(exc)},
        ) from exc


def _strip_code_fences(text: str) -> str:
    """Remove Markdown code fences a model may wrap JSON in."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:] if lines else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped.strip()


def create_provider(config: PipelineConfig, override: str | None = None) -> LLMProvider:
    """Create an ``LLMProvider`` from config, or an explicit override string.

    Raises:
        LLMError: ``PK-AI-001`` if the provider name is missing or unknown.
    """
    name = (override or config.diagnostics.provider or "").strip().lower()

    if name == "anthropic":
        from pipelinekit.ai.providers.anthropic import AnthropicProvider

        return AnthropicProvider()
    if name == "openai":
        from pipelinekit.ai.providers.openai import OpenAIProvider

        return OpenAIProvider()
    if name == "ollama":
        from pipelinekit.ai.providers.ollama import OllamaProvider

        return OllamaProvider()

    raise LLMError(
        "PK-AI-001",
        f"Unknown or unconfigured AI provider: '{name or 'none'}'. "
        "Set diagnostics.provider to openai, anthropic, or ollama.",
        {"provider": name},
    )
