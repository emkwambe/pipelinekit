"""Tests for the provider factory and shared parsing helpers (SPEC-005)."""

from __future__ import annotations

import json

import pytest
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult
from pipelinekit.ai.providers import (
    build_user_prompt,
    create_provider,
    parse_diagnostic_response,
)
from pipelinekit.ai.providers.anthropic import AnthropicProvider
from pipelinekit.ai.providers.ollama import OllamaProvider
from pipelinekit.ai.providers.openai import OpenAIProvider
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError


def _config(provider: str) -> PipelineConfig:
    return PipelineConfig(
        **{
            "pipeline": {"name": "demo"},
            "runtime": {},
            "ingestion": {
                "source": {"type": "postgres"},
                "destination": {"type": "duckdb"},
            },
            "transformation": {},
            "contracts": {},
            "quality": {},
            "diagnostics": {"enabled": True, "provider": provider},
            "notifications": {},
        }
    )


def _evidence() -> EvidencePackage:
    return EvidencePackage(
        run_id="run-9", pipeline_name="demo", pipeline_result={"status": "failed"}
    )


def test_factory_creates_each_provider():
    """create_provider returns the right type for each configured provider."""
    assert isinstance(create_provider(_config("anthropic")), AnthropicProvider)
    assert isinstance(create_provider(_config("openai")), OpenAIProvider)
    assert isinstance(create_provider(_config("ollama")), OllamaProvider)


def test_factory_override_wins():
    """An explicit override takes precedence over config."""
    provider = create_provider(_config("anthropic"), override="openai")
    assert isinstance(provider, OpenAIProvider)


def test_factory_unknown_provider_raises_ai_001():
    """An unknown/unconfigured provider raises LLMError(PK-AI-001)."""
    with pytest.raises(LLMError) as exc_info:
        create_provider(_config("none"))
    assert exc_info.value.code == "PK-AI-001"


def test_parse_valid_response():
    """parse_diagnostic_response builds a DiagnosticResult from valid JSON."""
    raw = json.dumps(
        {
            "status": "diagnosed",
            "finding_type": "unknown",
            "confidence": 0.5,
            "evidence": [],
            "recommended_actions": [],
        }
    )
    result = parse_diagnostic_response(raw, _evidence())
    assert isinstance(result, DiagnosticResult)
    assert result.run_id == "run-9"


def test_parse_strips_code_fences():
    """parse_diagnostic_response tolerates a Markdown-fenced JSON body."""
    raw = (
        "```json\n"
        '{"status": "diagnosed", "finding_type": "unknown", "confidence": 0.6, '
        '"evidence": [], "recommended_actions": []}\n'
        "```"
    )
    result = parse_diagnostic_response(raw, _evidence())
    assert result.confidence == 0.6


def test_parse_invalid_json_raises_ai_002():
    """parse_diagnostic_response raises PK-AI-002 on non-JSON text."""
    with pytest.raises(LLMError) as exc_info:
        parse_diagnostic_response("not json at all", _evidence())
    assert exc_info.value.code == "PK-AI-002"


def test_parse_invalid_model_raises_ai_002():
    """parse_diagnostic_response raises PK-AI-002 when fields violate the model."""
    raw = json.dumps({"status": "diagnosed", "finding_type": "x", "confidence": 5.0})
    with pytest.raises(LLMError) as exc_info:
        parse_diagnostic_response(raw, _evidence())
    assert exc_info.value.code == "PK-AI-002"


def test_build_user_prompt_includes_run_id():
    """build_user_prompt embeds the serialized evidence."""
    prompt = build_user_prompt(_evidence())
    assert "run-9" in prompt
