"""Tests for the shared proposal parser (SPEC-015).

``parse_proposal_response`` is used by all five providers, so robust handling of
markdown fences and preamble/trailing prose belongs here — one place, every
provider. A response with no JSON object raises ``ProposalError(PK-GEN-001)``.
"""

from __future__ import annotations

import json

import pytest
from pipelinekit.ai.proposal_models import BlueprintProposal, ProposalContext
from pipelinekit.ai.providers import parse_proposal_response
from pipelinekit.core.errors import ProposalError

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


def _ctx() -> ProposalContext:
    return ProposalContext(
        source_type="stripe", destination_type="snowflake", tables=["charges"]
    )


def test_parser_accepts_plain_json():
    """A bare JSON object parses into a BlueprintProposal."""
    result = parse_proposal_response(_VALID, _ctx(), "mistral", "")
    assert isinstance(result, BlueprintProposal)
    assert result.source_type == "stripe"
    assert len(result.assets) == 1


def test_parser_strips_markdown_fences():
    """A ```json fenced response parses (every provider, via shared parser)."""
    fenced = f"```json\n{_VALID}\n```"
    result = parse_proposal_response(fenced, _ctx(), "anthropic", "claude")
    assert isinstance(result, BlueprintProposal)
    assert len(result.assets) == 1


def test_parser_handles_preamble_and_trailing_prose():
    """Preamble and trailing prose around the JSON object are dropped."""
    noisy = f"Here is the proposal you asked for:\n```json\n{_VALID}\n```\nLet me know!"
    result = parse_proposal_response(noisy, _ctx(), "openai", "")
    assert result.confidence == 0.9


def test_parser_non_json_raises_pk_gen_001():
    """A response with no JSON object raises ProposalError(PK-GEN-001)."""
    with pytest.raises(ProposalError) as exc_info:
        parse_proposal_response("I cannot do that.", _ctx(), "ollama", "")
    assert exc_info.value.code == "PK-GEN-001"
