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
from typing import TYPE_CHECKING

from pipelinekit.ai.arch_models import ArchitectureResult
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult
from pipelinekit.ai.provider import LLMProvider
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError

if TYPE_CHECKING:
    from pipelinekit.ai.arch_evidence import ArchitectureContext

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


ARCH_SYSTEM_PROMPT = """You are a senior data architecture advisor for PipelineKit.
Analyze the provided architecture context and return a JSON recommendation.
Your response must be valid JSON matching this schema:
{
  "reasoning_type": "tool_selection|cost_optimization|adr_compliance|\
stack_evolution|blueprint_selection",
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
  "tradeoffs": [{"dimension": "...", "current": "...", "proposed": "...", \
"direction": "better|worse|neutral", "evidence": "..."}],
  "evidence": [{"type": "...", "detail": "..."}],
  "adr_compliance": {"checked": [], "violations": [], "compliant": []},
  "can_auto_apply": false,
  "estimated_impact": {},
  "explanation": "Human-readable reasoning"
}
Never invent evidence. Only use what is provided.
can_auto_apply must always be false.
Base recommendations on the specific data profile, not generic best practices."""


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


def build_arch_user_prompt(
    context: "ArchitectureContext",
    reasoning_type: str,
    question: str | None = None,
) -> str:
    """Render architecture context as the user prompt (structured, never raw)."""
    payload = {
        "reasoning_type": reasoning_type,
        "question": question,
        "context": context.to_dict(),
    }
    return (
        "Reason about this analytics architecture using only the context below.\n\n"
        + json.dumps(payload, indent=2, default=str)
    )


def parse_architecture_response(
    raw: str,
    context: "ArchitectureContext",
    reasoning_type: str,
) -> ArchitectureResult:
    """Parse a provider's raw text response into an ``ArchitectureResult``.

    The model's ``adr_compliance`` object form (``{checked, violations,
    compliant}``) is normalized into the list[ADRComplianceCheck] the model
    expects. ``can_auto_apply`` is forced False at this boundary (the engine
    re-forces it as well).

    Raises:
        LLMError: ``PK-AI-002`` if the text is not valid JSON or does not
            satisfy the ``ArchitectureResult`` model.
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

    data.setdefault("reasoning_type", reasoning_type)
    data["adr_compliance"] = _normalize_adr_compliance(data.get("adr_compliance"))
    data["can_auto_apply"] = False  # Phase 5 invariant (ADR-015)
    try:
        return ArchitectureResult(**data)
    except Exception as exc:
        raise LLMError(
            "PK-AI-002",
            f"AI response did not match the architecture model: {exc}",
            {"detail": str(exc)},
        ) from exc


def _normalize_adr_compliance(raw: object) -> list[dict]:
    """Normalize provider ``adr_compliance`` into a list of check dicts.

    Accepts either the prompt's object form ``{checked, violations, compliant}``
    or a direct list of check objects.
    """
    if isinstance(raw, list):
        return [_coerce_check(item, True) for item in raw]
    if isinstance(raw, dict):
        checks: list[dict] = []
        for item in raw.get("compliant") or []:
            checks.append(_coerce_check(item, True))
        for item in raw.get("violations") or []:
            checks.append(_coerce_check(item, False))
        return checks
    return []


def _coerce_check(item: object, default_compliant: bool) -> dict:
    """Coerce one ADR compliance entry into a check dict."""
    if isinstance(item, dict):
        return {
            "adr_id": str(item.get("adr_id") or item.get("id") or "ADR-unknown"),
            "compliant": bool(item.get("compliant", default_compliant)),
            "note": str(item.get("note", "")),
        }
    return {"adr_id": str(item), "compliant": default_compliant, "note": ""}


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
