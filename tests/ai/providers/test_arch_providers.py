"""Tests for provider architect() methods (SPEC-011). SDKs are never called."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from pipelinekit.ai.arch_evidence import ArchitectureContext
from pipelinekit.ai.arch_models import ArchitectureResult
from pipelinekit.ai.providers import parse_architecture_response
from pipelinekit.ai.providers.anthropic import AnthropicProvider
from pipelinekit.ai.providers.ollama import OllamaProvider
from pipelinekit.ai.providers.openai import OpenAIProvider
from pipelinekit.core.errors import LLMError

_RESPONSE = json.dumps(
    {
        "reasoning_type": "tool_selection",
        "confidence": 0.82,
        "current_state": {"description": "dbt on duckdb", "tools": {}},
        "recommendation": {
            "action": "switch dbt to sqlmesh",
            "tool_from": "dbt",
            "tool_to": "sqlmesh",
            "rationale": "native incremental handling",
            "effort": "medium",
            "reversible": True,
            "requires_approval": True,
        },
        "tradeoffs": [
            {
                "dimension": "reliability",
                "current": "dbt",
                "proposed": "sqlmesh",
                "direction": "better",
                "evidence": "fewer timeouts",
            }
        ],
        "evidence": [{"type": "run", "detail": "PK-ADAPTER-002"}],
        "adr_compliance": {
            "checked": ["ADR-005"],
            "violations": [],
            "compliant": [{"adr_id": "ADR-005", "note": "Apache 2.0"}],
        },
        "can_auto_apply": True,
        "estimated_impact": {},
        "explanation": "SQLMesh reduces incremental failures.",
    }
)


def _context() -> ArchitectureContext:
    return ArchitectureContext(
        config={"pipeline": {"name": "demo"}},
        run_history=[{"id": "run-1", "status": "failed"}],
        volume_profile={"runs_observed": 6},
    )


@pytest.mark.parametrize(
    "provider_cls", [AnthropicProvider, OpenAIProvider, OllamaProvider]
)
def test_architect_returns_result(provider_cls):
    """architect() parses a mocked response into an ArchitectureResult."""
    provider = provider_cls()
    with patch.object(provider, "_complete", return_value=_RESPONSE):
        result = provider.architect(_context(), "tool_selection", "dbt or sqlmesh?")
    assert isinstance(result, ArchitectureResult)
    assert result.reasoning_type == "tool_selection"
    assert result.recommendation.tool_to == "sqlmesh"


def test_architect_forces_can_auto_apply_false():
    """A response with can_auto_apply=True is forced False at the parse boundary."""
    provider = AnthropicProvider()
    with patch.object(provider, "_complete", return_value=_RESPONSE):
        result = provider.architect(_context(), "tool_selection")
    assert result.can_auto_apply is False


def test_architect_normalizes_adr_compliance_object():
    """The object form {checked, violations, compliant} becomes a check list."""
    result = parse_architecture_response(_RESPONSE, _context(), "tool_selection")
    assert len(result.adr_compliance) == 1
    assert result.adr_compliance[0].adr_id == "ADR-005"
    assert result.adr_compliance[0].compliant is True


def test_architect_invalid_json_raises_ai_002():
    """A non-JSON response raises LLMError(PK-AI-002)."""
    with pytest.raises(LLMError) as exc_info:
        parse_architecture_response("not json", _context(), "tool_selection")
    assert exc_info.value.code == "PK-AI-002"


def test_architect_missing_key_raises_ai_001(monkeypatch):
    """architect() raises LLMError(PK-AI-001) when the API key is missing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LLMError) as exc_info:
        AnthropicProvider().architect(_context(), "tool_selection")
    assert exc_info.value.code == "PK-AI-001"
