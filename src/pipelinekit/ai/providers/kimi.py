"""Kimi (Moonshot AI) provider — OpenAI-compatible, 128k context (ADR-041).

Kimi exposes an OpenAI-compatible API, so this provider drives the ``openai``
SDK pointed at Moonshot's ``base_url``. Like ``deepseek.py``, the SDK is loaded
via ``importlib.import_module`` (not a literal ``import openai``) so it stays
physically contained: the OpenAI SDK remains isolated to ``openai.py`` and the
OpenAI-compatible providers per the package's import-isolation rule, without any
file importing another provider's symbols.

The ``moonshot-v1-128k`` model's 131,072-token context window is the reason for
adding Kimi — it holds EMS-enriched diagnosis prompts (quality scores, SLO
violations, anomalies, drift, contract history, full log) without truncation.

API key from ``MOONSHOT_API_KEY`` (BYOK, ADR-005). Missing key or transport
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

_ENV_KEY = "MOONSHOT_API_KEY"
DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "moonshot-v1-32k"
# The 128k model is the primary reason for adding Kimi (AI-7 EMS injection).
KIMI_MODELS = [
    "moonshot-v1-8k",
    "moonshot-v1-32k",
    "moonshot-v1-128k",
]
# Cap only the blueprint-proposal response; diagnose/architect pass no cap.
_PROPOSAL_MAX_TOKENS = 8192


class KimiProvider:
    """Kimi (Moonshot AI) provider.

    Data residency: China (Moonshot AI servers).
    Suitable for: large-context EMS-enriched diagnosis (128k), Asia-Pacific
    latency, structured data analysis.
    Not suitable for: EU GDPR or US FedRAMP requirements.
    API key: MOONSHOT_API_KEY environment variable.
    Model default: moonshot-v1-32k (balance of context and speed);
    moonshot-v1-128k for EMS-enriched prompts.

    ADR-041: sixth provider, OpenAI-compatible.
    """

    name = "kimi"
    MAX_CONTEXT_TOKENS = 131_072

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model

    def _complete(self, system: str, user: str, max_tokens: int | None = None) -> str:
        """Call the Kimi API (OpenAI-compatible) and return the raw text.

        ``max_tokens`` caps the response when set; ``None`` (diagnose/architect)
        uses the SDK default.
        """
        api_key = os.environ.get(_ENV_KEY)
        if not api_key:
            raise LLMError(
                "PK-AI-001",
                f"{_ENV_KEY} environment variable not set. "
                "Get your API key at https://platform.moonshot.cn",
                {"provider": self.name},
            )
        try:
            # OpenAI-compatible SDK loaded by name to keep it contained here.
            sdk: Any = importlib.import_module("openai")
            client = sdk.OpenAI(api_key=api_key, base_url=DEFAULT_BASE_URL)
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
                f"Kimi provider unavailable: {exc}",
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
