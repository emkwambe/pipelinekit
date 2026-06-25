"""The stable ``LLMProvider`` Protocol.

No concrete provider code lives here. Provider-specific imports stay inside
``src/pipelinekit/ai/providers/`` (ADR-014, Smell 2). The ``DiagnosticsEngine``
calls this interface only and never knows which provider is active.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction


@runtime_checkable
class LLMProvider(Protocol):
    """Stable interface every AI provider implements (ADR-007, ADR-005)."""

    name: str

    def diagnose(self, evidence: EvidencePackage) -> DiagnosticResult:
        """Analyze evidence and return a structured ``DiagnosticResult``.

        Raises ``LLMError(PK-AI-001)`` if the provider is unavailable and
        ``LLMError(PK-AI-002)`` if the response fails schema validation.
        """
        ...

    def summarize(self, logs: list[str]) -> str:
        """Summarize log entries in plain English. Never invents facts."""
        ...

    def recommend(self, diagnosis: DiagnosticResult) -> list[RecommendedAction]:
        """Return recommended actions for a diagnosis (never executed)."""
        ...
