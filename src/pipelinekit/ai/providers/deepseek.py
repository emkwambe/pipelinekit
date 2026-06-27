"""DeepSeek provider — non-US cloud provider for provider diversity (ADR-016).

DeepSeek exposes an OpenAI-compatible API, so this provider drives the ``openai``
SDK pointed at DeepSeek's ``base_url``. The SDK is loaded via
``importlib.import_module`` (not a literal ``import openai``) so it stays
physically contained in this file: the OpenAI SDK remains isolated to
``openai.py`` and this module per the package's import-isolation rule, without
either file importing the other's symbols.

API key from ``DEEPSEEK_API_KEY`` (BYOK, ADR-005). Missing key or transport
failure → ``LLMError(PK-AI-001)``; malformed output → ``LLMError(PK-AI-002)``.
"""

from __future__ import annotations

import importlib
import os
from typing import TYPE_CHECKING, Any

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

_ENV_KEY = "DEEPSEEK_API_KEY"
_BASE_URL = "https://api.deepseek.com"
# Cap only the blueprint-proposal response. deepseek-chat's hard output limit is
# 8192 tokens; diagnose/architect pass no cap (SDK default).
_PROPOSAL_MAX_TOKENS = 8192


class DeepSeekProvider:
    """DeepSeek AI provider.

    Data residency: China (DeepSeek AI servers).
    Suitable for: cost-sensitive deployments, Asian market customers.
    Not suitable for: EU GDPR or US FedRAMP requirements.
    API key: DEEPSEEK_API_KEY environment variable.
    Model default: deepseek-chat (maps to DeepSeek-V3)

    ADR-016: Non-US cloud provider requirement.
    """

    name = "deepseek"

    def __init__(self, model: str = "deepseek-chat") -> None:
        self.model = model

    def _complete(self, system: str, user: str, max_tokens: int | None = None) -> str:
        """Call the DeepSeek API (OpenAI-compatible) and return the raw text.

        ``max_tokens`` caps the response when set; ``None`` (diagnose/architect)
        uses the SDK default.
        """
        api_key = os.environ.get(_ENV_KEY)
        if not api_key:
            raise LLMError(
                "PK-AI-001",
                f"Set {_ENV_KEY} to use the DeepSeek provider.",
                {"provider": self.name},
            )
        try:
            # OpenAI-compatible SDK loaded by name to keep it contained here.
            sdk: Any = importlib.import_module("openai")
            client = sdk.OpenAI(api_key=api_key, base_url=_BASE_URL)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(
                "PK-AI-001",
                f"DeepSeek provider unavailable: {exc}",
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
        """Propose a blueprint from context (SPEC-015). Never writes files."""
        raw = self._complete(
            PROPOSAL_SYSTEM_PROMPT,
            build_proposal_user_prompt(context),
            max_tokens=_PROPOSAL_MAX_TOKENS,
        )
        return parse_proposal_response(raw, context, self.name, self.model)

    def analyze_migration(self, context: dict) -> "MigrationProposal":
        """Analyse an existing config and propose a migration (SPEC-017)."""
        raw = self._complete(
            MIGRATION_SYSTEM_PROMPT, build_migration_user_prompt(context)
        )
        return parse_migration_response(raw, context)
