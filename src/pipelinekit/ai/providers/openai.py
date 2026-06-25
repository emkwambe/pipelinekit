"""OpenAI provider.

All ``openai`` imports stay inside this file (lazily, in ``_complete``).
API key from ``OPENAI_API_KEY`` (BYOK, ADR-005). Missing key or transport
failure → ``LLMError(PK-AI-001)``; malformed output → ``LLMError(PK-AI-002)``.
"""

from __future__ import annotations

import os

from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers import (
    SYSTEM_PROMPT,
    build_user_prompt,
    parse_diagnostic_response,
)
from pipelinekit.core.errors import LLMError

_ENV_KEY = "OPENAI_API_KEY"


class OpenAIProvider:
    """OpenAI provider implementing the ``LLMProvider`` protocol."""

    name = "openai"

    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model

    def _complete(self, system: str, user: str) -> str:
        """Call the OpenAI API and return the raw text response."""
        api_key = os.environ.get(_ENV_KEY)
        if not api_key:
            raise LLMError(
                "PK-AI-001",
                f"Set {_ENV_KEY} to use the OpenAI provider.",
                {"provider": self.name},
            )
        try:
            import openai  # noqa: PLC0415 — provider import isolated here

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(
                "PK-AI-001",
                f"OpenAI provider unavailable: {exc}",
                {"provider": self.name},
            ) from exc

    def diagnose(self, evidence: EvidencePackage) -> DiagnosticResult:
        """Diagnose a run from structured evidence."""
        raw = self._complete(SYSTEM_PROMPT, build_user_prompt(evidence))
        return parse_diagnostic_response(raw, evidence)

    def summarize(self, logs: list[str]) -> str:
        """Summarize log lines in plain English."""
        prompt = "Summarize these log lines factually:\n" + "\n".join(logs)
        return self._complete("You are a concise log summarizer.", prompt)

    def recommend(self, diagnosis: DiagnosticResult) -> list[RecommendedAction]:
        """Return the diagnosis's recommended actions (never executed)."""
        return list(diagnosis.recommended_actions)
