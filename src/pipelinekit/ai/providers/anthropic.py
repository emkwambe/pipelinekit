"""Anthropic Claude provider — the default recommended provider.

All ``anthropic`` imports stay inside this file (lazily, in ``_complete``).
API key from ``ANTHROPIC_API_KEY`` (BYOK, ADR-005). Missing key or transport
failure → ``LLMError(PK-AI-001)``; malformed output → ``LLMError(PK-AI-002)``.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import TYPE_CHECKING

from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers import (
    ARCH_SYSTEM_PROMPT,
    PROPOSAL_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_arch_user_prompt,
    build_proposal_user_prompt,
    build_user_prompt,
    parse_architecture_response,
    parse_diagnostic_response,
    parse_proposal_response,
)
from pipelinekit.core.errors import LLMError

if TYPE_CHECKING:
    from pipelinekit.ai.arch_evidence import ArchitectureContext
    from pipelinekit.ai.arch_models import ArchitectureResult
    from pipelinekit.ai.proposal_models import BlueprintProposal, ProposalContext

_ENV_KEY = "ANTHROPIC_API_KEY"
# Blueprint proposals return many full files, so the ceiling is generous; short
# diagnostic/architecture responses are unaffected.
_MAX_TOKENS = 8192


class AnthropicProvider:
    """Anthropic Claude provider implementing the ``LLMProvider`` protocol."""

    name = "anthropic"

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

        Anthropic sometimes wraps the JSON object in markdown fences or adds a
        short preamble. Strip fences and extract the outermost ``{...}`` object
        before parsing. A response that is still not valid JSON is logged to
        stderr and raised as ``LLMError(PK-AI-002)``.
        """
        raw = self._complete(
            PROPOSAL_SYSTEM_PROMPT, build_proposal_user_prompt(context)
        )
        content = _extract_json_object(raw)
        try:
            json.loads(content)
        except ValueError as exc:
            print(
                f"[anthropic] proposal response was not valid JSON:\n{raw}",
                file=sys.stderr,
            )
            raise LLMError(
                "PK-AI-002",
                "Anthropic proposal response was not valid JSON",
                {"provider": self.name},
            ) from exc
        return parse_proposal_response(content, context, self.name, self.model)


def _extract_json_object(raw: str) -> str:
    """Return the JSON object from a model response.

    Strips `````json`` / ``````` fences, then — if the result is not
    already valid JSON — extracts the substring from the first ``{`` to the last
    ``}`` (handling preamble or trailing prose). Returns the cleaned string; the
    caller validates.
    """
    content = re.sub(r"```json\s*|\s*```", "", raw).strip()
    try:
        json.loads(content)
        return content
    except ValueError:
        start, end = content.find("{"), content.rfind("}")
        if start != -1 and end > start:
            return content[start : end + 1]
        return content
