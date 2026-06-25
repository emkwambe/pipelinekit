"""The stable ``LLMProvider`` Protocol.

No concrete provider code lives here. Provider-specific imports stay inside
``src/pipelinekit/ai/providers/`` (ADR-014, Smell 2). The ``DiagnosticsEngine``
calls this interface only and never knows which provider is active.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction

if TYPE_CHECKING:
    from pipelinekit.ai.arch_evidence import ArchitectureContext
    from pipelinekit.ai.arch_models import ArchitectureResult


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

    def architect(
        self,
        context: "ArchitectureContext",
        reasoning_type: str,
        question: str | None = None,
    ) -> "ArchitectureResult":
        """Perform architectural reasoning from context (SPEC-011, ADR-015).

        Output must validate against ``schemas/architecture.schema.json``.
        Raises ``LLMError(PK-AI-001)`` if the provider is unavailable and
        ``LLMError(PK-AI-002)`` if the response fails schema validation. The
        result never auto-applies — ``can_auto_apply`` is always False.
        """
        ...
