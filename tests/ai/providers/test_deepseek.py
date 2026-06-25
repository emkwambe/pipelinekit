"""Tests for DeepSeekProvider (ADR-016). The OpenAI-compatible SDK is mocked."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers.deepseek import DeepSeekProvider
from pipelinekit.core.errors import LLMError

_RESPONSE = json.dumps(
    {
        "status": "diagnosed",
        "finding_type": "adapter_failure",
        "confidence": 0.88,
        "evidence": [{"type": "error_code", "detail": "PK-ADAPTER-001"}],
        "recommended_actions": [
            {"action": "retry connection", "risk_level": "low", "reversible": True}
        ],
        "can_auto_fix": False,
        "explanation": "Transient connection failure.",
    }
)


def _evidence() -> EvidencePackage:
    return EvidencePackage(
        run_id="run-ds", pipeline_name="demo", pipeline_result={"status": "failed"}
    )


def test_diagnose_returns_result():
    """diagnose() parses a mocked API response into a DiagnosticResult."""
    provider = DeepSeekProvider()
    with patch.object(provider, "_complete", return_value=_RESPONSE):
        result = provider.diagnose(_evidence())
    assert isinstance(result, DiagnosticResult)
    assert result.finding_type == "adapter_failure"
    assert result.run_id == "run-ds"


def test_diagnose_missing_key_raises_ai_001(monkeypatch):
    """diagnose() raises LLMError(PK-AI-001) when DEEPSEEK_API_KEY is missing."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(LLMError) as exc_info:
        DeepSeekProvider().diagnose(_evidence())
    assert exc_info.value.code == "PK-AI-001"


def test_complete_uses_deepseek_base_url(monkeypatch):
    """_complete drives the OpenAI-compatible SDK against DeepSeek's base_url."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-test")
    fake_sdk = MagicMock()
    choice = SimpleNamespace(message=SimpleNamespace(content=_RESPONSE))
    completion = SimpleNamespace(choices=[choice])
    fake_sdk.OpenAI.return_value.chat.completions.create.return_value = completion
    with patch.dict(sys.modules, {"openai": fake_sdk}):
        result = DeepSeekProvider().diagnose(_evidence())
    assert result.finding_type == "adapter_failure"
    _, kwargs = fake_sdk.OpenAI.call_args
    assert kwargs["base_url"] == "https://api.deepseek.com"


def test_summarize_and_recommend():
    """summarize() returns text and recommend() echoes the diagnosis actions."""
    provider = DeepSeekProvider()
    with patch.object(provider, "_complete", return_value="a summary"):
        assert provider.summarize(["line 1"]) == "a summary"
    result = DiagnosticResult(
        status="diagnosed",
        finding_type="adapter_failure",
        confidence=0.9,
        recommended_actions=[RecommendedAction(action="retry connection")],
    )
    assert provider.recommend(result) == result.recommended_actions


def test_deepseek_isolated():
    """DeepSeek specifics (base URL) live only in the deepseek provider file."""
    src_root = Path(__file__).resolve().parents[3] / "src" / "pipelinekit"
    allowed = src_root / "ai" / "providers" / "deepseek.py"
    offenders = []
    for path in src_root.rglob("*.py"):
        if path == allowed:
            continue
        if "api.deepseek.com" in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == [], f"DeepSeek base URL leaked outside provider: {offenders}"
