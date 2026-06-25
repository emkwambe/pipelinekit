"""Ollama local provider — for air-gapped / privacy-first deployments.

All ``ollama`` imports stay inside this file (lazily, in ``_complete``). Host
from ``OLLAMA_HOST`` (default ``http://localhost:11434``) — no API key needed
(local). Transport failure → ``LLMError(PK-AI-001)``; malformed output →
``LLMError(PK-AI-002)``.
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

_ENV_HOST = "OLLAMA_HOST"
_DEFAULT_HOST = "http://localhost:11434"


class OllamaProvider:
    """Ollama local provider implementing the ``LLMProvider`` protocol."""

    name = "ollama"

    def __init__(self, model: str = "llama3") -> None:
        self.model = model
        # Gracefully default the host when OLLAMA_HOST is not set.
        self.host = os.environ.get(_ENV_HOST, _DEFAULT_HOST)

    def _complete(self, system: str, user: str) -> str:
        """Call the local Ollama server and return the raw text response."""
        try:
            import ollama  # noqa: PLC0415 — provider import isolated here

            client = ollama.Client(host=self.host)
            response = client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                format="json",
            )
            return str(response["message"]["content"])
        except Exception as exc:
            raise LLMError(
                "PK-AI-001",
                f"Ollama provider unavailable at {self.host}: {exc}",
                {"provider": self.name, "host": self.host},
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
