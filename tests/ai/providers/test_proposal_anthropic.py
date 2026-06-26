"""Tests for AnthropicProvider.propose_blueprint() JSON handling (SPEC-015).

Anthropic may wrap JSON in markdown fences or add preamble; the provider strips
fences and extracts the JSON object before parsing, and raises PK-AI-002 (after
logging the raw response) when the result is still not valid JSON.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from pipelinekit.ai.proposal_models import BlueprintProposal, ProposalContext
from pipelinekit.ai.providers.anthropic import AnthropicProvider
from pipelinekit.core.errors import LLMError

_VALID = json.dumps(
    {
        "confidence": 0.9,
        "assumptions": ["charges has id, amount"],
        "unsupported_areas": [],
        "requires_human_decisions": [],
        "assets": [
            {
                "asset_type": "blueprint_json",
                "filename": "blueprint.json",
                "content": "{}",
                "confidence_note": "strong pattern match",
            }
        ],
    }
)


def _context() -> ProposalContext:
    return ProposalContext(
        source_type="stripe", destination_type="snowflake", tables=["charges"]
    )


def test_propose_parses_markdown_fenced_json():
    """A ```json fenced response parses into a BlueprintProposal."""
    fenced = f"```json\n{_VALID}\n```"
    provider = AnthropicProvider()
    with patch.object(provider, "_complete", return_value=fenced):
        proposal = provider.propose_blueprint(_context())
    assert isinstance(proposal, BlueprintProposal)
    assert proposal.source_type == "stripe"
    assert len(proposal.assets) == 1


def test_propose_parses_json_with_preamble():
    """Preamble/trailing prose around the JSON object is stripped."""
    noisy = f"Here is the proposal you asked for:\n```json\n{_VALID}\n```\nDone."
    provider = AnthropicProvider()
    with patch.object(provider, "_complete", return_value=noisy):
        proposal = provider.propose_blueprint(_context())
    assert isinstance(proposal, BlueprintProposal)
    assert proposal.confidence == 0.9


def test_propose_non_json_raises_pk_ai_002():
    """A response with no JSON object raises LLMError(PK-AI-002)."""
    provider = AnthropicProvider()
    with patch.object(provider, "_complete", return_value="I cannot do that."):
        with pytest.raises(LLMError) as exc_info:
            provider.propose_blueprint(_context())
    assert exc_info.value.code == "PK-AI-002"
