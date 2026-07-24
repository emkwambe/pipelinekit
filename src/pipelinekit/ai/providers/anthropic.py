"""Anthropic Claude provider — the default recommended provider.

All ``anthropic`` imports stay inside this file (lazily, in ``_complete``).
API key from ``ANTHROPIC_API_KEY`` (BYOK, ADR-005). Missing key or transport
failure → ``LLMError(PK-AI-001)``; malformed output → ``LLMError(PK-AI-002)``.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers import (
    ARCH_SYSTEM_PROMPT,
    MIGRATION_SYSTEM_PROMPT,
    PROPOSAL_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_arch_user_prompt,
    build_migration_user_prompt,
    build_proposal_user_prompt,
    build_user_prompt,
    parse_architecture_response,
    parse_diagnostic_response,
    parse_migration_response,
    parse_proposal_response,
)
from pipelinekit.core.errors import LLMError

if TYPE_CHECKING:
    from pipelinekit.ai.arch_evidence import ArchitectureContext
    from pipelinekit.ai.arch_models import ArchitectureResult
    from pipelinekit.ai.migration_models import MigrationProposal
    from pipelinekit.ai.proposal_models import BlueprintProposal, ProposalContext

_ENV_KEY = "ANTHROPIC_API_KEY"
# Blueprint proposals return ~13 full files; 8192 — and even 16000 — truncated a
# full proposal mid-JSON (surfacing as PK-GEN-001), so the ceiling is raised to
# 32000. claude-sonnet-4-6 supports well above this. It is only a ceiling —
# short diagnostic/architecture responses are unaffected.
_MAX_TOKENS = 32000


class AnthropicProvider:
    """Anthropic Claude provider implementing the ``LLMProvider`` protocol."""

    name = "anthropic"
    MAX_CONTEXT_TOKENS = 200_000

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        self.model = model

    def _complete(self, system: str, user: str) -> str:
        """Call the Anthropic API and return the raw text response."""
        api_key = os.environ.get(_ENV_KEY)
        if not api_key:
            raise LLMError(
                "PK-AI-001",
                f"Set {_ENV_KEY} to use the Anthropic provider.",
                {"provider": self.name},
            )
        try:
            import anthropic  # noqa: PLC0415 — provider import isolated here

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=_MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(
                block.text for block in message.content if hasattr(block, "text")
            )
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(
                "PK-AI-001",
                f"Anthropic provider unavailable: {exc}",
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

    def architect(
        self,
        context: "ArchitectureContext",
        reasoning_type: str,
        question: str | None = None,
    ) -> "ArchitectureResult":
        """Reason about architecture from structured context (SPEC-011)."""
        raw = self._complete(
            ARCH_SYSTEM_PROMPT,
            build_arch_user_prompt(context, reasoning_type, question),
        )
        return parse_architecture_response(raw, context, reasoning_type)

    def propose_blueprint(self, context: "ProposalContext") -> "BlueprintProposal":
        """Propose a blueprint from context (SPEC-015). Never writes files.

        Fence/preamble handling lives in the shared ``parse_proposal_response``
        so every provider benefits from it.
        """
        raw = self._complete(
            PROPOSAL_SYSTEM_PROMPT, build_proposal_user_prompt(context)
        )
        return parse_proposal_response(raw, context, self.name, self.model)

    def analyze_migration(self, context: dict) -> "MigrationProposal":
        """Analyse an existing config and propose a migration (SPEC-017)."""
        raw = self._complete(
            MIGRATION_SYSTEM_PROMPT, build_migration_user_prompt(context)
        )
        return parse_migration_response(raw, context)
