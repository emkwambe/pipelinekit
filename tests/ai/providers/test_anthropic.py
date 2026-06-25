"""Tests for AnthropicProvider (SPEC-005). Anthropic SDK is never called."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers.anthropic import AnthropicProvider
from pipelinekit.core.errors import LLMError

_RESPONSE = json.dumps(
    {
        "status": "diagnosed",
        "finding_type": "adapter_failure",
        "confidence": 0.9,
        "evidence": [{"type": "error_code", "detail": "PK-ADAPTER-001"}],
        "recommended_actions": [
            {"action": "check connectivity", "risk_level": "low", "reversible": True}
        ],
        "can_auto_fix": False,
        "explanation": "Connection refused.",
    }
)


def _evidence() -> EvidencePackage:
    return EvidencePackage(
        run_id="run-1", pipeline_name="demo", pipeline_result={"status": "failed"}
    )


def test_diagnose_returns_result():
    """diagnose() parses a mocked API response into a DiagnosticResult."""
    provider = AnthropicProvider()
    with patch.object(provider, "_complete", return_value=_RESPONSE):
        result = provider.diagnose(_evidence())
    assert isinstance(result, DiagnosticResult)
    assert result.finding_type == "adapter_failure"
    assert result.run_id == "run-1"


def test_diagnose_missing_key_raises_ai_001(monkeypatch):
    """diagnose() raises LLMError(PK-AI-001) when the API key is missing."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(LLMError) as exc_info:
        AnthropicProvider().diagnose(_evidence())
    assert exc_info.value.code == "PK-AI-001"


def test_complete_calls_sdk(monkeypatch):
    """_complete imports the SDK, calls the API, and returns the text (mocked)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "re_test")
    fake_sdk = MagicMock()
    message = SimpleNamespace(content=[SimpleNamespace(text=_RESPONSE)])
    fake_sdk.Anthropic.return_value.messages.create.return_value = message
    with patch.dict(sys.modules, {"anthropic": fake_sdk}):
        result = AnthropicProvider().diagnose(_evidence())
    assert result.finding_type == "adapter_failure"
    fake_sdk.Anthropic.assert_called_once()


def test_summarize_and_recommend():
    """summarize() returns text and recommend() echoes the diagnosis actions."""
    provider = AnthropicProvider()
    with patch.object(provider, "_complete", return_value="a summary"):
        assert provider.summarize(["line 1", "line 2"]) == "a summary"
    result = DiagnosticResult(
        status="diagnosed",
        finding_type="adapter_failure",
        confidence=0.9,
        recommended_actions=[RecommendedAction(action="check connectivity")],
    )
    assert provider.recommend(result) == result.recommended_actions


def test_anthropic_imports_isolated():
    """No source file outside the anthropic provider imports anthropic."""
    src_root = Path(__file__).resolve().parents[3] / "src" / "pipelinekit"
    allowed = src_root / "ai" / "providers" / "anthropic.py"
    offenders = []
    for path in src_root.rglob("*.py"):
        if path == allowed:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import anthropic", "from anthropic")):
                offenders.append(str(path))
                break
    assert offenders == [], f"anthropic imported outside provider: {offenders}"
